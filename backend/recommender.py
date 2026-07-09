"""
recommender.py
--------------
The single recommendation engine for the competitive programming recommender.

Architecture
------------
ALL recommendations — for both existing users and newly fetched Codeforces
users — are produced by the same TruncatedSVD model operating on the same
latent space.

Startup (load_data)
  1. Load cf_predictions.csv → the pre-computed SVD score matrix R (999 × 10863)
  2. Fit TruncatedSVD on R to extract the item latent factors (Vt)
  3. Load problems.csv, user_features.csv, user_tag_weakness.csv

Known users  (in cf_predictions.csv)
  → Direct row look-up from R
  → Difficulty filter: max_rating ± 200
  → Return top-N unseen problems

New / unknown users  (not in cf_predictions.csv)
  → Fetch submissions via new_user.get_user_data()
  → Build binary solved-problem vector r_new
  → Project into SVD latent space: u_latent = r_new @ Vt.T
  → Reconstruct scores: scores = u_latent @ Vt
  → Same difficulty filter + top-N logic as known users

Both paths use the SAME:
  - SVD item latent factors (Vt)
  - Difficulty window (max_rating ± 200)
  - Ranking strategy (nlargest on score)

No disk reads occur after startup. No model retraining on any request.
"""

import os
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD

import new_user as nu

# ---------------------------------------------------------------------------
# Module-level data store — populated once by load_data()
# ---------------------------------------------------------------------------

_predictions: pd.DataFrame | None = None  # R matrix (n_users × n_problems)
_problems: pd.DataFrame | None = None     # problem_id → {rating, tags}
_user_features: pd.DataFrame | None = None
_user_tag_weakness: pd.DataFrame | None = None

# Exact solved sets loaded from processed_data.csv at startup
# handle → frozenset of problem_id strings the user actually solved
_solved_lookup: dict | None = None

# SVD item latent factors — shared by both recommendation paths
_Vt: np.ndarray | None = None             # shape: (n_components, n_problems)
_problem_cols: list | None = None         # ordered list of problem_id strings
_problem_col_index: dict | None = None    # problem_id → column position (int)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_SVD_N_COMPONENTS = 100   # latent dimensions — matches research methodology

# ---------------------------------------------------------------------------
# Startup loader
# ---------------------------------------------------------------------------

def load_data() -> None:
    """
    Load all CSVs and fit the SVD decomposition.
    Called once from app.py at startup.  Idempotent (safe to call multiple times).
    """
    global _predictions, _problems, _user_features, _user_tag_weakness
    global _Vt, _problem_cols, _problem_col_index, _solved_lookup

    if _predictions is not None:
        return  # already loaded

    # 1. Pre-computed SVD score matrix
    print("[recommender] Loading cf_predictions.csv …", flush=True)
    _predictions = pd.read_csv(
        os.path.join(_DATA_DIR, "cf_predictions.csv"), index_col="user"
    )
    _problem_cols = list(_predictions.columns)
    _problem_col_index = {pid: i for i, pid in enumerate(_problem_cols)}

    # 2. Extract item latent factors from the pre-computed predictions.
    #    We decompose R (the reconstructed score matrix) to recover Vt so that
    #    any new user's binary interaction vector can be projected into the
    #    same SVD latent space — enabling consistent recommendations without
    #    retraining the model.
    print(
        f"[recommender] Fitting TruncatedSVD "
        f"(n_components={_SVD_N_COMPONENTS}) on predictions matrix …",
        flush=True,
    )
    svd = TruncatedSVD(n_components=_SVD_N_COMPONENTS, random_state=42)
    svd.fit(_predictions.values)
    _Vt = svd.components_  # (n_components, n_problems)
    print(f"[recommender] Vt extracted — shape: {_Vt.shape}", flush=True)

    # 3. Problem metadata
    print("[recommender] Loading problems.csv …", flush=True)
    _problems = pd.read_csv(os.path.join(_DATA_DIR, "problems.csv"))
    _problems["problem_id"] = _problems["problem_id"].astype(str)
    _problems = _problems.set_index("problem_id")

    # 4. User features (for display + difficulty look-up for known users)
    print("[recommender] Loading user_features.csv …", flush=True)
    _user_features = pd.read_csv(os.path.join(_DATA_DIR, "user_features.csv"))

    # 5. Tag weakness (for weakness analysis endpoint)
    print("[recommender] Loading user_tag_weakness.csv …", flush=True)
    _user_tag_weakness = pd.read_csv(os.path.join(_DATA_DIR, "user_tag_weakness.csv"))

    # 6. Exact solved sets from training data — used to exclude already-solved
    #    problems for known users instead of approximating via score threshold.
    print("[recommender] Loading processed_data.csv (solved sets) …", flush=True)
    _proc = pd.read_csv(
        os.path.join(_DATA_DIR, "processed_data.csv"),
        usecols=["user", "problem_id", "solved"],
        dtype={"user": str, "problem_id": str, "solved": int},
    )
    _solved_lookup = (
        _proc[_proc["solved"] == 1]
        .groupby("user")["problem_id"]
        .apply(set)
        .to_dict()
    )
    print(
        f"[recommender] Solved lookup built — {len(_solved_lookup)} users.",
        flush=True,
    )

    print("[recommender] All data loaded and model ready.", flush=True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assert_loaded() -> None:
    if _predictions is None or _Vt is None:
        raise RuntimeError(
            "Data not loaded. Call recommender.load_data() before making requests."
        )


def _problem_to_dict(problem_id: str, score: float) -> dict:
    """Convert a problem_id (e.g. '1915-D') to the API response dict."""
    parts = problem_id.split("-", 1)
    contest_id = int(parts[0]) if parts[0].isdigit() else parts[0]
    index = parts[1] if len(parts) > 1 else ""

    if problem_id in _problems.index:
        row = _problems.loc[problem_id]
        rating = int(row["rating"]) if not pd.isna(row["rating"]) else 0
        tags = [t.strip() for t in str(row["tags"]).split(",") if t.strip()]
    else:
        rating = 0
        tags = []

    url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"

    return {
        "contestId": contest_id,
        "index": index,
        "name": problem_id,
        "rating": rating,
        "tags": tags,
        "score": round(float(score), 6),
        "url": url,
    }


def _apply_difficulty_filter(scores: pd.Series, user_max_rating: int) -> pd.Series:
    """
    Keep only problems whose difficulty is within [user_max_rating − 200,
    user_max_rating + 200].

    Problems not present in _problems (unknown difficulty) are excluded.
    """
    lo = user_max_rating - 200
    hi = user_max_rating + 200

    valid_pids = [
        pid for pid in scores.index
        if pid in _problems.index
        and lo <= int(_problems.loc[pid, "rating"]) <= hi
    ]
    return scores[valid_pids]


def _get_user_max_rating(handle: str) -> int:
    """
    Look up the known user's max_rating from user_features.csv.
    Falls back to their current rating, then 1200 if neither is available.
    """
    row = _user_features[_user_features["user"] == handle]
    if row.empty:
        return 1200
    r = row.iloc[0]
    return int(r.get("max_rating", r.get("rating", 1200)))


def _rank_and_slice(scores: pd.Series, solved_set: set, user_max_rating: int, n: int) -> list:
    """
    Shared final step for both recommendation paths:
      1. Remove problems the user already solved.
      2. Apply difficulty filter (max_rating ± 200).
      3. Return the top-N as a list of problem dicts.

    If the difficulty filter leaves fewer than `n` results, the window is
    progressively relaxed by ±200 until at least `n` results are found or
    the window reaches ±800.
    """
    # Exclude already-solved problems
    unseen = scores.drop(
        index=[p for p in solved_set if p in scores.index], errors="ignore"
    )

    # Attempt progressively wider difficulty windows
    window = 200
    while window <= 800:
        filtered = _apply_difficulty_filter(unseen, user_max_rating)
        if len(filtered) >= n or window == 800:
            break
        window += 200

    # If still empty after widest window, fall back to unfiltered top-N
    if filtered.empty:
        filtered = unseen

    top_n = filtered.nlargest(n)
    return [_problem_to_dict(pid, score) for pid, score in top_n.items()]


# ---------------------------------------------------------------------------
# SVD-based recommendation for new users
# ---------------------------------------------------------------------------

def recommend_new_user(
    solved_problem_ids: set,
    user_max_rating: int,
    top_k: int = 10,
) -> list:
    """
    Generate recommendations for a user NOT in the pre-computed SVD matrix.

    Algorithm
    ---------
    1. Build a binary interaction vector r_new  (len = n_problems)
       where r_new[i] = 1 if problem i was solved by the user.
    2. Project into SVD latent space:  u_latent = r_new @ Vt.T
    3. Reconstruct scores:             scores   = u_latent @ Vt
    4. Apply the same difficulty filter and ranking as the known-user path.

    This reuses the SAME Vt extracted from the pre-trained SVD model —
    no retraining occurs.

    Parameters
    ----------
    solved_problem_ids : set[str]
        Problem IDs the user has already solved (will be excluded).
    user_max_rating    : int
        User's maximum Codeforces rating — used for difficulty filtering.
    top_k              : int
        Number of recommendations to return.

    Returns
    -------
    list of problem dicts:
        [{contestId, index, name, rating, tags, score, url}, …]
    """
    _assert_loaded()

    # 1. Build binary interaction vector
    r_new = np.zeros(len(_problem_cols), dtype=np.float32)
    for pid in solved_problem_ids:
        if pid in _problem_col_index:
            r_new[_problem_col_index[pid]] = 1.0

    # 2. Project into latent space (Vt shape: n_components × n_problems)
    u_latent = r_new @ _Vt.T  # → (n_components,)

    # 3. Reconstruct predicted scores for all problems
    scores_arr = u_latent @ _Vt  # → (n_problems,)
    scores = pd.Series(scores_arr, index=_problem_cols)

    # 4. Rank, filter difficulty, exclude solved → return top-K
    return _rank_and_slice(scores, solved_problem_ids, user_max_rating, top_k)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_known_user(handle: str) -> bool:
    """Return True if handle is in the pre-computed predictions matrix."""
    _assert_loaded()
    return handle in _predictions.index


def get_user_profile_from_features(handle: str) -> dict | None:
    """Return display profile for a known user (from user_features.csv)."""
    _assert_loaded()
    row = _user_features[_user_features["user"] == handle]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "handle": handle,
        "rating": int(r.get("rating", 0)),
        "max_rating": int(r.get("max_rating", r.get("rating", 0))),
        "solved": int(r.get("solved", 0)),
        "solve_rate": round(float(r.get("solve_rate", 0)), 4),
    }


def recommend(handle: str, n: int = 10) -> dict:
    """
    Generate top-N recommendations for any Codeforces handle.

    Both known and new users follow the same SVD-based pipeline:
      - Known users:  look up pre-computed scores from R (cf_predictions.csv)
      - New users:    project binary solved-vector into SVD latent space

    Both paths apply:
      - The same Vt (item latent factors)
      - The same difficulty filter: user_max_rating ± 200
      - The same ranking strategy: nlargest on SVD score

    Returns
    -------
    {
        "user": {handle, rating, max_rating, solved, solve_rate},
        "recommendations": [{contestId, index, name, rating, tags, score, url}, …]
    }

    Raises
    ------
    ValueError       — handle not found on Codeforces (new user path)
    RuntimeError     — data not loaded
    TimeoutError     — Codeforces API timed out (new user path)
    ConnectionError  — network failure (new user path)
    """
    _assert_loaded()

    if is_known_user(handle):
        # ── Known user path ────────────────────────────────────────────────
        # Direct look-up of the pre-computed SVD score row
        scores = _predictions.loc[handle].copy()

        # Exact solved set from training data (loaded at startup from
        # processed_data.csv).  Falls back to an empty set if the handle
        # is somehow absent from the lookup (should not happen in practice).
        solved_set = _solved_lookup.get(handle, set())

        # Look up max_rating for difficulty filter
        user_max_rating = _get_user_max_rating(handle)

        recs = _rank_and_slice(scores, solved_set, user_max_rating, n)

        user_profile = get_user_profile_from_features(handle) or {
            "handle": handle, "rating": 0, "max_rating": user_max_rating,
            "solved": 0, "solve_rate": 0.0,
        }

    else:
        # ── New / unknown user path ────────────────────────────────────────
        # Fetch from Codeforces API; build solved set; project into SVD space
        data = nu.get_user_data(handle)   # raises ValueError if handle unknown

        solved_set      = data["solved_set"]
        user_info       = data["user_info"]
        user_max_rating = user_info["max_rating"] or user_info["rating"] or 1200

        recs = recommend_new_user(
            solved_problem_ids=solved_set,
            user_max_rating=user_max_rating,
            top_k=n,
        )
        user_profile = user_info

    return {
        "user": user_profile,
        "recommendations": recs,
    }


# ---------------------------------------------------------------------------
# Weakness analysis  (unchanged — not part of recommendation pipeline)
# ---------------------------------------------------------------------------

def get_weakness(handle: str) -> dict:
    """
    Return tag-weakness analysis for a Codeforces handle.

    Known users: query _user_tag_weakness (pre-computed).
    New users:   fetch live data via new_user.get_full_profile().

    Returns
    -------
    {"weak_tags": [...], "strong_tags": [...], "coverage": float}
    """
    _assert_loaded()

    if is_known_user(handle):
        user_rows = _user_tag_weakness[_user_tag_weakness["user"] == handle]

        if user_rows.empty:
            return {"weak_tags": [], "strong_tags": [], "coverage": 0.0}

        weak_rows   = user_rows[user_rows["is_weak"] == 1].sort_values(
            "weakness_score", ascending=False
        )
        strong_rows = user_rows[user_rows["is_weak"] == 0].sort_values(
            "weakness_score", ascending=True
        )

        all_tags    = user_rows["tag"].tolist()
        weak_tags   = weak_rows["tag"].tolist()
        strong_tags = strong_rows["tag"].tolist()
        coverage    = round(len(strong_tags) / len(all_tags), 4) if all_tags else 0.0

        return {"weak_tags": weak_tags, "strong_tags": strong_tags, "coverage": coverage}

    else:
        profile      = nu.get_full_profile(handle)
        tag_weakness = profile["tag_weakness"]

        if not tag_weakness:
            return {"weak_tags": [], "strong_tags": [], "coverage": 0.0}

        scores = list(tag_weakness.values())
        median = sorted(scores)[len(scores) // 2]

        weak_tags   = [t for t, s in sorted(tag_weakness.items(), key=lambda x: -x[1]) if s >= median]
        strong_tags = [t for t, s in sorted(tag_weakness.items(), key=lambda x:  x[1]) if s <  median]
        coverage    = round(len(strong_tags) / len(tag_weakness), 4) if tag_weakness else 0.0

        return {"weak_tags": weak_tags, "strong_tags": strong_tags, "coverage": coverage}
