"""
new_user.py
-----------
Data collection and preprocessing wrapper for Codeforces users.

Responsibilities (ONLY):
  - Fetch user info and submissions from the Codeforces public API
  - Preprocess submissions into a normalised DataFrame
  - Compute the solved-problem set (used by recommender.py to exclude problems)
  - Compute tag-weakness scores (used by weakness analysis)
  - Compute display statistics (solved count, solve_rate, etc.)

This module does NOT implement any recommendation logic.
All recommendation is handled exclusively by recommender.py via TruncatedSVD.
"""

import math
import requests
import pandas as pd

CF_API_BASE = "https://codeforces.com/api"

# ---------------------------------------------------------------------------
# Codeforces API helpers
# ---------------------------------------------------------------------------

def _cf_get(endpoint: str, params: dict) -> dict:
    """Raw GET to the Codeforces API. Raises typed exceptions on failure."""
    url = f"{CF_API_BASE}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        raise TimeoutError("Codeforces API request timed out.")
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Network error contacting Codeforces API: {exc}")

    if data.get("status") != "OK":
        comment = data.get("comment", "Unknown error")
        raise ValueError(f"Codeforces API error: {comment}")

    return data["result"]


def fetch_user_info(handle: str) -> dict:
    """
    Fetch basic profile info from the CF API.

    Returns
    -------
    {"handle": str, "rating": int, "max_rating": int}

    Raises ValueError if the handle does not exist.
    """
    result = _cf_get("user.info", {"handles": handle})
    info = result[0]
    return {
        "handle": info.get("handle", handle),
        "rating": info.get("rating", 0),
        "max_rating": info.get("maxRating", 0),
    }


def fetch_submissions(handle: str) -> pd.DataFrame:
    """
    Fetch all rated submissions for `handle`.

    Returns a DataFrame with columns:
        user, problem_id, rating, tags, verdict, timestamp

    Unrated problems are excluded.
    """
    result = _cf_get("user.status", {"handle": handle})

    rows = []
    for sub in result:
        problem = sub.get("problem", {})
        rating = problem.get("rating")
        if rating is None:
            continue

        contest_id = problem.get("contestId", "")
        index = problem.get("index", "")
        problem_id = f"{contest_id}-{index}" if contest_id and index else ""
        if not problem_id:
            continue

        tags = ",".join(problem.get("tags", []))
        verdict = sub.get("verdict", "UNKNOWN")
        timestamp = sub.get("creationTimeSeconds", 0)

        rows.append({
            "user": handle,
            "problem_id": problem_id,
            "rating": int(rating),
            "tags": tags,
            "verdict": verdict,
            "timestamp": timestamp,
        })

    if not rows:
        return pd.DataFrame(
            columns=["user", "problem_id", "rating", "tags", "verdict", "timestamp"]
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Preprocessing helpers
# ---------------------------------------------------------------------------

def get_solved_problems(submissions_df: pd.DataFrame) -> set:
    """
    Return the set of problem_id strings the user has solved (verdict == 'OK').
    """
    if submissions_df.empty:
        return set()
    solved = submissions_df[submissions_df["verdict"] == "OK"]["problem_id"]
    return set(solved.unique())


def compute_user_features(handle: str, submissions_df: pd.DataFrame, user_info: dict) -> dict:
    """
    Compute display statistics from raw submissions.

    Parameters
    ----------
    handle        : Codeforces handle string
    submissions_df: DataFrame returned by fetch_submissions()
    user_info     : dict from fetch_user_info() — provides rating & max_rating

    Returns
    -------
    {
        "handle": str,
        "rating": int,
        "max_rating": int,
        "solved": int,
        "solve_rate": float,
    }
    """
    if submissions_df.empty:
        return {
            "handle": handle,
            "rating": user_info.get("rating", 0),
            "max_rating": user_info.get("max_rating", 0),
            "solved": 0,
            "solve_rate": 0.0,
        }

    solved_set = get_solved_problems(submissions_df)
    grouped = submissions_df.groupby("problem_id")

    total_solved = 0
    total_attempts = 0

    for pid, group in grouped:
        total_attempts += len(group)
        if pid in solved_set:
            total_solved += 1

    solve_rate = total_solved / total_attempts if total_attempts > 0 else 0.0

    return {
        "handle": handle,
        "rating": user_info.get("rating", 0),
        "max_rating": user_info.get("max_rating", 0),
        "solved": total_solved,
        "solve_rate": round(solve_rate, 4),
    }


def compute_tag_weakness(submissions_df: pd.DataFrame) -> dict:
    """
    Compute weakness score per tag from raw submissions.

    Returns a dict mapping tag_name → weakness_score (0.0–1.0, higher = weaker).
    Used exclusively by the weakness analysis endpoint — NOT by the recommender.
    """
    if submissions_df.empty:
        return {}

    rows = []
    for _, sub in submissions_df.iterrows():
        tags = [t.strip() for t in str(sub["tags"]).split(",") if t.strip()]
        is_ok = sub["verdict"] == "OK"
        for tag in tags:
            rows.append({"tag": tag, "verdict": "OK" if is_ok else "FAIL"})

    if not rows:
        return {}

    tag_df = pd.DataFrame(rows)
    tag_stats = (
        tag_df.groupby("tag")
        .apply(
            lambda g: pd.Series({
                "attempts": len(g),
                "solved": (g["verdict"] == "OK").sum(),
            }),
            include_groups=False,
        )
        .reset_index()
    )

    weakness_map = {}
    for _, row in tag_stats.iterrows():
        tag = row["tag"]
        attempts = int(row["attempts"])
        solved = int(row["solved"])
        if attempts == 0:
            continue
        solve_rate = solved / attempts
        mastery = math.log1p(solved)
        skill = solve_rate * mastery
        weakness = max(0.0, min(1.0, 1.0 - (skill / (skill + 1.0 + 1e-9))))
        weakness_map[tag] = round(weakness, 4)

    return weakness_map


# ---------------------------------------------------------------------------
# Public composite helpers
# ---------------------------------------------------------------------------

def get_user_data(handle: str) -> dict:
    """
    Fetch and preprocess all data needed by recommender.recommend() for a
    new (unknown) user.

    Returns
    -------
    {
        "user_info":        dict  — handle, rating, max_rating, solved, solve_rate
        "solved_set":       set   — problem_id strings the user has already solved
        "submissions_df":   pd.DataFrame — raw normalised submissions
    }

    Raises
    ------
    ValueError       — handle not found on Codeforces
    TimeoutError     — Codeforces API timed out
    ConnectionError  — network failure
    """
    user_info_raw  = fetch_user_info(handle)
    submissions_df = fetch_submissions(handle)
    solved_set     = get_solved_problems(submissions_df)
    user_info      = compute_user_features(handle, submissions_df, user_info_raw)

    return {
        "user_info":       user_info,
        "solved_set":      solved_set,
        "submissions_df":  submissions_df,
    }


def get_full_profile(handle: str) -> dict:
    """
    Extended profile that also includes tag-weakness data.
    Used by the weakness analysis endpoint and fetch_team.py.

    Returns
    -------
    {
        "user_info":      dict
        "solved_set":     set
        "submissions_df": pd.DataFrame
        "tag_weakness":   dict[str, float]
    }
    """
    data = get_user_data(handle)
    tag_weakness = compute_tag_weakness(data["submissions_df"])

    return {
        **data,
        "tag_weakness": tag_weakness,
    }
