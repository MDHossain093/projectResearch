<div align="center">

# 🧠 CodeRecommend AI

### A Hybrid Recommendation & Team‑Formation System for Competitive Programmers

**Personalized problem suggestions, tag-level weakness analysis, and automatic team balancing — all powered by an SVD recommendation engine that works for both known and cold‑start Codeforces users.**

---

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Tailwind](https://img.shields.io/badge/TailwindCSS-4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-22c55e?style=for-the-badge)]()

</div>

---

## ✨ What is this?

**CodeRecommend AI** is a full‑stack ML application that helps competitive programmers on **Codeforces** practice more effectively and form better teams.

It does **three** things, all from a single Codeforces handle:

| 🎯 Feature | What it does |
|---|---|
| **Problem Recommendations** | Hybrid SVD model (collaborative + content + cold-start) that recommends unseen problems at the right difficulty. |
| **Weakness Analyzer** | Tag‑level strength/weakness profile computed live from your submissions — shows exactly which topics to grind. |
| **Team Builder** | Greedy combinatorial algorithm that splits a roster of handles into balanced teams of 3 maximizing tag‑coverage diversity. |

Works for **any** Codeforces handle — known users get pre‑computed SVD scores, completely new users get a hybrid cold‑start score computed in real time.

---

## 🖼️ Preview

> Add screenshots later by dropping them in a `screenshots/` folder and replacing the paths below.

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard    │  Recommend │  Weakness  │  Team Builder     │
│  ─────────────┼────────────┼────────────┼────────────────  │
│  📊 1,000 users · 10,856 problems · 918,763 submissions   │
│  Precision@10: 21.08%  ·  Recall@10: 2.68%  ·  NDCG@10: 22.95% │
│  Weak Hit@10: 92.12%   ·  Tag F1: 56.51%                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Why it matters

- **Models cold‑start properly.** A user with zero overlap to the training matrix still gets meaningful recommendations via content + difficulty + neighbor‑based collaborative filtering.
- **Explainable scoring.** Every recommendation is the weighted sum of three interpretable components — content (tag profile), difficulty (rating distance), and CF (neighbor SVD average).
- **Single source of truth engine.** The same `_rank_and_slice()` pipeline serves both known and new users — no model retraining on requests.
- **Real Codeforces integration.** All new‑user data is fetched live from the Codeforces public API and pre‑processed in milliseconds.

---

## 🏗️ Architecture

```
┌──────────────────────────┐         ┌────────────────────────────┐
│  Next.js 16 (Frontend)   │  HTTP   │  Flask (Backend API)        │
│  ─────────────────────   │ ───────►│  ─────────────────────────  │
│  • Dashboard stats        │         │  • /api/recommend/<handle>  │
│  • Recommendation list    │         │  • /api/weakness/<handle>   │
│  • Weakness analyzer      │         │  • /api/analytics/<handle>  │
│  • Team builder UI        │         │  • /api/team                │
│  • Tailwind 4 + shadcn/ui │         │  • /api/dashboard           │
└──────────────────────────┘         └─────────────┬──────────────┘
                                                    │
                                          ┌─────────▼──────────┐
                                          │  recommendation    │
                                          │  engine (SVD)      │
                                          │  ─────────────     │
                                          │  • cf_predictions  │
                                          │  • problems        │
                                          │  • user_features   │
                                          │  • user_weakness   │
                                          └─────────┬──────────┘
                                                    │
                                          ┌─────────▼──────────┐
                                          │  Codeforces API    │
                                          │  (live for new     │
                                          │   users)           │
                                          └────────────────────┘
```

---

## 🧬 How the Recommendation Engine Works

The core algorithm lives in [`backend/recommender.py`](backend/recommender.py) and serves **both** known and unknown users through the same final pipeline.

### Known users (in `cf_predictions.csv`)
1. Look up pre‑computed SVD row `R[user]`.
2. Exclude problems already solved (from `processed_data.csv`).
3. Apply a difficulty filter: `max_rating ± 200` (progressively widens to ±800 if needed).
4. Return top‑N via `nlargest` on the score.

### New users (cold‑start hybrid)
A user **not** in the pre‑computed matrix is projected into the same latent space using:

```
final_score = 0.5 · content  +  0.2 · difficulty  +  0.3 · cf
```

| Component | Formula |
|---|---|
| **content** | max over the problem's tags of (mean solved rating per tag) |
| **difficulty** | `exp(−|user_max_rating − problem_rating| / 600)` |
| **cf** | similarity‑weighted average of the top‑10 cosine‑similar training users' SVD scores |

The result then flows through the **same** ranking/exclusion/difficulty filter as known users.

---

## 📊 Dataset & Model Performance

Trained on **995 users**, **10,856 problems**, and **918,763 submissions** scraped from Codeforces.

### Standard recommendation metrics (K=10)

| Metric | Value |
|---|---:|
| Precision@10 | **21.08%** |
| Recall@10 | **2.68%** |
| NDCG@10 | **22.95%** |

### Weakness‑alignment metrics (K=10)

| Metric | Value |
|---|---:|
| Weak Precision@10 | **80.48%** |
| Weak Hit@10 | **92.12%** |
| Avg Aligned Problems | 8.05 / 10 |

### Tag‑level weakness metrics (per‑user average)

| Metric | Value |
|---|---:|
| Precision | 70.19% |
| Recall | 49.90% |
| F1 Score | **56.51%** |
| Accuracy | 57.05% |
| Tag Coverage | 49.90% |

> Evaluated on **498** held‑out users with a Truncated SVD (`n_components=50`).

---

## 🧰 Tech Stack

**Backend**
- 🐍 Python 3.11 · Flask · Flask‑CORS
- 📊 pandas · NumPy
- 🌐 `requests` for the Codeforces public API
- 🤖 Truncated SVD over a binary user×problem interaction matrix

**Frontend**
- ⚛️ Next.js 16 (App Router) · React 19
- 🎨 Tailwind CSS 4 · shadcn/ui · lucide-react
- 🧩 Custom hooks & clean component architecture

**Data**
- 📁 14+ pre‑computed CSVs in `backend/data/`
- 🧪 `scripts/evaluate.py` for offline evaluation

---

## 📂 Project Structure

```
projectResearch/
├── backend/
│   ├── app.py                 # Flask entry point
│   ├── recommender.py         # Hybrid SVD recommender engine
│   ├── team_builder.py        # Greedy 3-person team-formation
│   ├── fetch_team.py          # Tag profile fetcher + cache
│   ├── new_user.py            # Cold-start path (CF API + preprocessing)
│   ├── routes.py              # All REST endpoints
│   ├── data/                  # Pre-computed CSVs (10K+ problems, 1M subs)
│   └── scripts/evaluate.py    # Offline evaluation pipeline
│
├── frontend/
│   ├── app/
│   │   ├── dashboard/         # Metrics dashboard
│   │   ├── recommendation/    # Problem recommendation page
│   │   ├── weakness/          # Weakness analyzer
│   │   └── team/              # Team builder page
│   ├── components/            # UI components (Card, Sidebar, Navbar, ...)
│   ├── hooks/                 # useRecentHandles
│   └── services/api.js        # Typed API client
│
└── data/                      # Raw research datasets
```

---

## ⚡ Quick Start

### 1. Clone

```bash
git clone https://github.com/MDHossain093/code-recommend-ai.git
cd code-recommend-ai
```

### 2. Backend (Flask)

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5000
```

On startup it loads all CSVs into memory and prints:
```
[app] Starting up — loading data into memory …
[recommender] Loading cf_predictions.csv …
[recommender] All data loaded and model ready.
[app] Ready. Listening on http://127.0.0.1:5000
```

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Open <http://localhost:3000> — the app redirects to `/dashboard`.

### 4. Try it out

Paste any Codeforces handle into the recommendation page:

- **Known handle** (e.g. `tourist`, `Petr`) → instant SVD lookup.
- **Unknown handle** → live CF fetch + cold-start hybrid in ~1s.

---

## 🔌 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/api/dashboard` | GET | Dataset + model stats |
| `/api/recommend/<handle>?n=10` | GET | Top‑N problem recommendations |
| `/api/weakness/<handle>` | GET | Tag weakness (known users) |
| `/api/weakness/v2/<handle>` | GET | Rich weakness profile (new users) |
| `/api/analytics/<handle>` | GET | Full per‑tag analytics |
| `/api/team` | POST | Build teams from `{"users": [...]}` |

**Example**

```bash
curl http://127.0.0.1:5000/api/recommend/tourist?n=5
```

```json
{
  "success": true,
  "user": { "handle": "tourist", "rating": 3900, "max_rating": 3900, "solved": 1820, "solve_rate": 0.7826 },
  "recommendations": [
    { "contestId": 1915, "index": "D", "name": "1915-D", "rating": 2400, "tags": ["binary search"], "score": 0.984312, "url": "https://codeforces.com/problemset/problem/1915/D" }
  ]
}
```

---

## 🧠 Team Builder Algorithm

[`backend/team_builder.py`](backend/team_builder.py) forms **teams of 3** from a list of handles, maximizing tag‑coverage diversity.

1. Fetch each user's solved‑tags set.
2. Score every possible 3‑person combo by the **union size** of their tags.
3. Greedy assignment: pick the best combo whose members are still available, repeat.
4. Compute per‑team **compatibility** (avg pairwise Jaccard) and **coverage** (fraction of the global tag universe covered).

> Constraints: at least 3 handles, count must be divisible by 3.

---

## 🧪 Reproduce the Evaluation

```bash
cd backend
python scripts/evaluate.py
```

Re‑runs Precision@K, Recall@K, NDCG@K, weak‑alignment, and tag‑level confusion matrices on the held‑out split.

---

## 🗺️ Roadmap

- [ ] Add a **learning‑to‑rank** layer (LambdaMART) on top of the SVD scores
- [ ] Replace the linear hybrid weights with a learned reranker
- [ ] Add **user embeddings** (Word2Vec‑style) on submission sequences
- [ ] Cache Codeforces fetches in Redis to make the cold‑start path sub‑200ms
- [ ] Deploy a public demo on Vercel + Render

---

## 📜 License

Released under the **MIT License**. See [`LICENSE`](LICENSE).

---

## 👤 Author

**MD Hossain**
GitHub: [@MDHossain093](https://github.com/MDHossain093)

> Interested in ML systems, recommendation engines, and competitive programming. This project was built end‑to‑end as a research artifact — data pipeline, model, API, and UI.

---

<div align="center">

⭐ **If you find this useful, drop a star on the repo — it helps a lot.** ⭐

</div>
