"""
routes.py
---------
All Flask API routes for the competitive programming recommender system.

Endpoints
---------
GET  /                       → health check
GET  /api/dashboard          → dataset + model stats
GET  /api/recommend/<handle> → personalized problem recommendations
GET  /api/weakness/<handle>  → tag weakness analysis
POST /api/team               → team builder from a list of handles
"""

from flask import Blueprint, jsonify, request
import recommender
import team_builder
import fetch_team

api = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error(message: str, status: int):
    return jsonify({"success": False, "message": message}), status


def _ok(data: dict):
    return jsonify({"success": True, **data}), 200


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@api.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Competitive Programming Recommender API is running.",
    }), 200


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@api.route("/api/dashboard", methods=["GET"])
def dashboard():
    """
    Returns aggregate dataset and model statistics.

    Weakness metrics computed via evaluate_weakness() on 498 users,
    TruncatedSVD (n_components=50), K=5:
      - Precision  : TP / (TP + FP) averaged over users
      - Recall     : TP / (TP + FN) averaged over users
      - F1 Score   : harmonic mean of precision & recall
      - Tag Coverage: TP / |weak_tags| averaged over users
      - Weak Hit@K : fraction of users where >= 1 rec covers a weak tag

    Standard metrics (Precision@K / Recall@K / NDCG@K) also included.
    """
    return _ok({
        "users": 995,
        "problems": 10856,
        "submissions": 918763,
        "model": "Hybrid SVD",
        "evaluated_users": 498,
        "k": 5,
        # ── Weakness-learning metrics (from evaluate_weakness) ──────────
        "performance": {
            "precision":    0.8143,
            "recall":       0.3672,
            "f1_score":     0.4963,
            "tag_coverage": 0.3672,
            "weak_hit_at_k": 0.8990,
            "k": 5,
        },
        # ── Standard recommendation metrics ────────────────────────────
        "standard": {
            "precision_at_k": 0.2458,
            "recall_at_k":    0.0181,
            "ndcg_at_k":      0.2566,
            "k": 5,
        },
        # ── Confusion matrix averages ───────────────────────────────────
        "confusion": {
            "avg_tp": 10.18,
            "avg_fp":  0.95,
            "avg_fn": 14.19,
        },
    })


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

@api.route("/api/recommend/<handle>", methods=["GET"])
def recommend(handle: str):
    """
    GET /api/recommend/<handle>

    Query params:
        n   (int, default 10) — number of recommendations to return

    Returns:
        {user: {...}, recommendations: [...]}
    """
    handle = handle.strip()
    if not handle:
        return _error("Codeforces handle is required.", 400)

    try:
        n = int(request.args.get("n", 10))
        n = max(1, min(n, 50))
    except ValueError:
        return _error("Query parameter 'n' must be an integer.", 400)

    try:
        result = recommender.recommend(handle, n=n)
        return _ok(result)

    except ValueError as exc:
        # Codeforces handle not found
        return _error(str(exc), 404)

    except TimeoutError:
        return _error(
            "Request to Codeforces API timed out. Please try again.", 504
        )

    except ConnectionError as exc:
        return _error(str(exc), 502)

    except RuntimeError as exc:
        return _error(f"Server error: {exc}", 500)

    except Exception as exc:
        return _error(f"Unexpected error: {exc}", 500)


# ---------------------------------------------------------------------------
# Weakness analysis
# ---------------------------------------------------------------------------

@api.route("/api/weakness/<handle>", methods=["GET"])
def weakness(handle: str):
    """
    GET /api/weakness/<handle>

    Returns:
        {weak_tags: [...], strong_tags: [...], coverage: float}
    """
    handle = handle.strip()
    if not handle:
        return _error("Codeforces handle is required.", 400)

    try:
        result = recommender.get_weakness(handle)
        return _ok(result)

    except ValueError as exc:
        return _error(str(exc), 404)

    except TimeoutError:
        return _error(
            "Request to Codeforces API timed out. Please try again.", 504
        )

    except ConnectionError as exc:
        return _error(str(exc), 502)

    except Exception as exc:
        return _error(f"Unexpected error: {exc}", 500)


# ---------------------------------------------------------------------------
# Team Builder
# ---------------------------------------------------------------------------

@api.route("/api/team", methods=["POST"])
def build_team():
    """
    POST /api/team
    Body: {"users": ["tourist", "Benq", "Petr", ...]}

    Rules:
    - At least 3 users required.
    - Number of users must be divisible by 3.

    Returns:
        {teams: [{team_no, members, compatibility, coverage}, ...]}
    """
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON.", 400)

    users = body.get("users")
    if not users or not isinstance(users, list):
        return _error("Field 'users' must be a non-empty list of handles.", 400)

    # Deduplicate while preserving order
    seen = set()
    unique_users = []
    for u in users:
        u = str(u).strip()
        if u and u not in seen:
            unique_users.append(u)
            seen.add(u)

    if len(unique_users) < 3:
        return _error("At least 3 unique handles are required.", 400)

    if len(unique_users) % 3 != 0:
        remaining = 3 - (len(unique_users) % 3)
        return _error(
            f"Number of handles must be divisible by 3. "
            f"Add {remaining} more handle(s) or remove some.",
            400,
        )

    try:
        teams = team_builder.build_teams(unique_users)
        return _ok({"teams": teams})

    except ValueError as exc:
        return _error(str(exc), 400)

    except Exception as exc:
        return _error(f"Unexpected error: {exc}", 500)
