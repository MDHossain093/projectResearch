"""
team_builder.py
---------------
Divides a list of Codeforces handles (length must be divisible by 3) into
teams of 3 that maximise tag-coverage diversity across each team.

Algorithm
---------
1. Fetch each user's solved-tags profile via fetch_team.get_user_solved_tags().
2. Score every possible 3-person combination:
       score = |union of tags covered by the 3 members|
       (a wider union means more diverse / complementary skills)
3. Use a greedy assignment:
       - Sort all combos by score descending.
       - Pick the highest-scoring combo whose members are all still available.
       - Repeat until all handles are assigned to teams.
4. Compute per-team metrics:
       - coverage:       fraction of ALL distinct tags covered by the team
       - compatibility:  average pairwise Jaccard similarity of member tag-sets
                         (higher Jaccard → more compatible / overlapping skills,
                          which is a softer "can work together" signal)

Public API
----------
    build_teams(handles: list[str]) -> list[dict]

Returns
-------
[
    {
        "team_no": 1,
        "members": ["tourist", "Benq", "Petr"],
        "compatibility": 0.42,
        "coverage": 0.68,
    },
    …
]
"""

import itertools
from collections import defaultdict

import fetch_team as ft


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _jaccard(set_a: set, set_b: set) -> float:
    """Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _team_diversity_score(tag_sets: list[set]) -> int:
    """Union size of all tags across team members — higher is more diverse."""
    union = set()
    for s in tag_sets:
        union |= s
    return len(union)


def _team_compatibility(tag_sets: list[set]) -> float:
    """
    Average pairwise Jaccard similarity among all team member pairs.
    A higher value means members have overlapping strengths (compatible).
    """
    if len(tag_sets) < 2:
        return 1.0
    pairs = list(itertools.combinations(tag_sets, 2))
    if not pairs:
        return 0.0
    return round(sum(_jaccard(a, b) for a, b in pairs) / len(pairs), 4)


def _team_coverage(tag_union: set, all_tags: set) -> float:
    """
    Fraction of all known tags covered by this team's union.
    """
    if not all_tags:
        return 0.0
    return round(len(tag_union & all_tags) / len(all_tags), 4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_teams(handles: list[str]) -> list[dict]:
    """
    Build balanced teams of 3 from `handles`, maximising tag-coverage diversity.

    Parameters
    ----------
    handles : list[str]
        Codeforces handles.  Length must be divisible by 3.

    Returns
    -------
    list of team dicts:
        {team_no, members, compatibility, coverage}

    Raises
    ------
    ValueError — if len(handles) is not divisible by 3, or < 3.
    """
    if len(handles) < 3:
        raise ValueError("At least 3 handles are required to form a team.")
    if len(handles) % 3 != 0:
        raise ValueError(
            f"Number of handles ({len(handles)}) must be divisible by 3."
        )

    # 1. Fetch tag profiles for all users
    tag_sets: dict[str, set] = {}
    for handle in handles:
        tag_sets[handle] = ft.get_user_solved_tags(handle)

    # 2. Compute the universe of all tags across all users
    all_tags: set = set()
    for s in tag_sets.values():
        all_tags |= s

    # 3. Score every possible team-of-3 combination
    all_combos = list(itertools.combinations(handles, 3))
    scored = []
    for combo in all_combos:
        team_tag_sets = [tag_sets[h] for h in combo]
        score = _team_diversity_score(team_tag_sets)
        scored.append((score, combo))

    # Sort by diversity score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # 4. Greedy assignment: pick best available combo at each step
    assigned: set[str] = set()
    teams = []
    team_no = 1

    for score, combo in scored:
        # Skip if any member already assigned
        if any(h in assigned for h in combo):
            continue

        team_tag_sets = [tag_sets[h] for h in combo]
        tag_union = set()
        for s in team_tag_sets:
            tag_union |= s

        compat = _team_compatibility(team_tag_sets)
        cov = _team_coverage(tag_union, all_tags)

        teams.append({
            "team_no": team_no,
            "members": list(combo),
            "compatibility": compat,
            "coverage": cov,
        })

        for h in combo:
            assigned.add(h)
        team_no += 1

        # Stop when all handles are assigned
        if len(assigned) == len(handles):
            break

    return teams