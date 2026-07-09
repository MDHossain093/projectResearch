import requests
import pandas as pd
from pathlib import Path
import time

BASE_URL = "https://codeforces.com/api"

_BASE = Path(__file__).parent.parent
DATA_DIR = _BASE / "data"

DATA_DIR.mkdir(exist_ok=True)

SUB_PATH = DATA_DIR / "temp_submissions.csv"
FEATURE_PATH = DATA_DIR / "temp_user_features.csv"
WEAK_PATH = DATA_DIR / "temp_user_tag_weakness.csv"


# ==============================
# FETCH USER SUBMISSIONS
# ==============================

def fetch_user(user):
    url = f"{BASE_URL}/user.status?handle={user}&count=1000"

    res = requests.get(url).json()

    if res["status"] != "OK":
        print(f"❌ Failed: {user}")
        return []

    rows = []

    for s in res["result"]:
        p = s.get("problem", {})

        if p.get("rating") is None:
            continue

        rows.append({
            "user": user,
            "problem_id": f"{p.get('contestId')}-{p.get('index')}",
            "rating": p.get("rating"),
            "tags": ",".join(p.get("tags", [])),
            "verdict": s.get("verdict")
        })

    return rows


# ==============================
# FETCH USER RATING
# ==============================

def fetch_user_rating(user):
    url = f"{BASE_URL}/user.info?handles={user}"

    try:
        res = requests.get(url).json()

        if res["status"] != "OK":
            return None

        info = res["result"][0]

        return info.get("maxRating", info.get("rating", None))

    except:
        return None


# ==============================
# BUILD RAW DATASET
# ==============================

def build_submission_csv(users):

    all_rows = []

    for u in users:
        print(f"Fetching {u}...")
        rows = fetch_user(u)
        all_rows.extend(rows)
        time.sleep(0.3)

    df = pd.DataFrame(all_rows)
    df.to_csv(SUB_PATH, index=False)

    print("✅ temp_submissions.csv created")


# ==============================
# PREPROCESS DATA
# ==============================

def preprocess_data():

    print("🧹 Preprocessing data...")

    df = pd.read_csv(SUB_PATH)

    # clean tags
    df["tags"] = df["tags"].fillna("").astype(str)
    df["tags"] = df["tags"].apply(
        lambda x: ",".join([t.strip() for t in x.split(",") if t.strip()])
    )

    # solved flag
    df["solved"] = df["verdict"].apply(lambda x: 1 if x == "OK" else 0)

    # group by user-problem
    grouped = df.groupby(["user", "problem_id"]).agg({
        "solved": "max",
        "rating": "first",
        "tags": "first",
        "verdict": "count"
    }).reset_index()

    grouped.rename(columns={"verdict": "attempts"}, inplace=True)

    grouped.to_csv(SUB_PATH, index=False)

    print("✅ Preprocessing done")


# ==============================
# BUILD USER FEATURES
# ==============================

def build_user_features():

    df = pd.read_csv(SUB_PATH)

    result = []

    for user, group in df.groupby("user"):

        attempts = group["attempts"].sum()
        solved = group["solved"].sum()

        solve_rate = solved / attempts if attempts > 0 else 0
        avg_attempts = attempts / max(solved, 1)

        rating = fetch_user_rating(user)

        print(f"User: {user}, Rating: {rating}")

        result.append([user, solve_rate, avg_attempts, rating])

        time.sleep(0.2)

    pd.DataFrame(
        result,
        columns=["user", "solve_rate", "avg_attempts", "rating"]
    ).to_csv(FEATURE_PATH, index=False)

    print("✅ temp_user_features.csv created")


# ==============================
# BUILD TAG WEAKNESS
# ==============================

def build_tag_weakness():

    df = pd.read_csv(SUB_PATH)

    df["tags"] = df["tags"].fillna("").astype(str)
    df["tags"] = df["tags"].apply(
        lambda x: [t.strip() for t in x.split(",") if t.strip()]
    )

    df = df.explode("tags")
    df = df[df["tags"].notna() & (df["tags"] != "")]

    result = []

    for (user, tag), group in df.groupby(["user", "tags"]):

        solve_rate = group["solved"].mean()
        attempts = group["attempts"].sum()
        avg_rating = group["rating"].mean()

        # 🔥 improved weakness (difficulty-aware)
        weakness = (
            (1 - solve_rate)
            + (attempts / df["attempts"].sum())
            + (avg_rating / 3000) * (1 - solve_rate)
        )

        result.append([user, tag, weakness])

    pd.DataFrame(result, columns=["user", "tag", "weakness"]) \
        .to_csv(WEAK_PATH, index=False)

    print("✅ temp_user_tag_weakness.csv created")


# ==============================
# MAIN PIPELINE
# ==============================

if __name__ == "__main__":

    users = []

    n = int(input("Enter number of team members: "))

    print()

    for i in range(n):

        handle = input(f"Enter Codeforces handle {i+1}: ").strip()

        users.append(handle)

    print("\nSelected Users:")

    for u in users:
        print("-", u)

    print()

    build_submission_csv(users)
    preprocess_data()
    build_user_features()
    build_tag_weakness()

    print("\n✅ Team data generated successfully.")


# ==============================================================
# API HELPER LAYER
# (Used by team_builder.py and app.py at request-time)
# All functions below operate on in-memory data injected via
# set_weakness_df(), so they do NOT perform any disk I/O.
# ==============================================================

import new_user as _nu

# Injected by app.py after recommender.load_data()
_weakness_df: pd.DataFrame | None = None

# Per-request tag profile cache (handle → {tag: score})
_tag_profile_cache: dict[str, dict[str, float]] = {}


def set_weakness_df(df: pd.DataFrame) -> None:
    """Inject the pre-loaded user_tag_weakness DataFrame from recommender.py."""
    global _weakness_df
    _weakness_df = df


def get_user_tag_profile(handle: str) -> dict[str, float]:
    """
    Return a dict mapping tag → weakness_score for `handle`.

    Source priority:
    1. In-memory cache (fastest)
    2. Pre-computed user_tag_weakness.csv (known users)
    3. Live Codeforces API fetch (new users) — result is cached

    Returns an empty dict if the handle cannot be found.
    """
    if handle in _tag_profile_cache:
        return _tag_profile_cache[handle]

    # Try pre-computed DataFrame first
    if _weakness_df is not None:
        rows = _weakness_df[_weakness_df["user"] == handle]
        if not rows.empty:
            profile = dict(zip(rows["tag"], rows["weakness_score"]))
            _tag_profile_cache[handle] = profile
            return profile

    # Fall back to live API
    try:
        profile_data = _nu.get_full_profile(handle)
        profile = profile_data["tag_weakness"]
    except Exception:
        profile = {}

    _tag_profile_cache[handle] = profile
    return profile


def get_user_solved_tags(handle: str) -> set[str]:
    """
    Return the set of all tags the user has encountered.
    Used as the tag-coverage set in team_builder.py.
    """
    return set(get_user_tag_profile(handle).keys())


def get_user_strength_tags(handle: str, top_n: int = 15) -> list[str]:
    """Return the `top_n` tags with the LOWEST weakness score (strongest topics)."""
    profile = get_user_tag_profile(handle)
    return [tag for tag, _ in sorted(profile.items(), key=lambda x: x[1])[:top_n]]


def get_user_weak_tags(handle: str, top_n: int = 15) -> list[str]:
    """Return the `top_n` tags with the HIGHEST weakness score (weakest topics)."""
    profile = get_user_tag_profile(handle)
    return [tag for tag, _ in sorted(profile.items(), key=lambda x: -x[1])[:top_n]]


def clear_cache() -> None:
    """Clear the in-memory tag profile cache (useful for testing)."""
    _tag_profile_cache.clear()
