"""
app.py
------
Flask application entry point.

Responsibilities:
- Create the Flask app and enable CORS.
- Load all pre-computed data into memory ONCE at startup.
- Register the API blueprint from routes.py.
- Inject the loaded weakness DataFrame into fetch_team.py.
"""

from flask import Flask
from flask_cors import CORS

import recommender
import fetch_team
from routes import api

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Allow all origins (Next.js dev server typically runs on localhost:3000)
CORS(app, resources={r"/*": {"origins": "*"}})

# Register all routes from routes.py
app.register_blueprint(api)

# ---------------------------------------------------------------------------
# Startup — load all data once before the first request
# ---------------------------------------------------------------------------

print("[app] Starting up — loading data into memory …", flush=True)
recommender.load_data()

# Share the pre-loaded weakness DataFrame with fetch_team
# to avoid a redundant disk read
from recommender import _user_tag_weakness as _wtf
fetch_team.set_weakness_df(_wtf)

print("[app] Ready. Listening on http://127.0.0.1:5000", flush=True)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,   # keep False to prevent double data-load in reloader
    )
