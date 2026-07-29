<div align="center">

# 🧠 CodeRecommend AI

### A Hybrid Recommendation & Team-Formation System for Competitive Programmers

**Give it a Codeforces handle. Get back the problems you should solve next, the topics you're actually weak at, and the most balanced 3-person teams — from a hybrid SVD engine that works even for users the model has never seen.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Tailwind](https://img.shields.io/badge/Tailwind-4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Dataset](https://img.shields.io/badge/Dataset-Kaggle-20BEFF?style=for-the-badge&logo=kaggle&logoColor=white)](https://www.kaggle.com/datasets/fardin35/codeforces-user-dataset)

</div>

---

## 📌 TL;DR

> Competitive programmers plateau because they practise the wrong problems — too easy, too hard, or on topics they're already good at.
> **CodeRecommend AI** mines **2.04M Codeforces submissions** to build a per-user latent profile, then recommends problems that are *simultaneously* at the right difficulty **and** aimed at that user's measured weak topics.

**The headline result:** **8.05 of every 10** recommended problems hit a topic the user is provably weak at, and **92.1%** of users get at least one weakness-targeted problem in their top 10.

| | |
|---|---|
| 🧩 **Problem** | Generic "recommended problems" lists ignore *why* a user is stuck. |
| 💡 **Approach** | Truncated SVD over a 995 × 10,864 interaction matrix + an explainable cold-start hybrid + a tag-level weakness model. |
| 📈 **Outcome** | 80.5% weakness-alignment precision @ K=10, with a working full-stack app on top. |
| 🛠️ **Scope** | Data pipeline → model → evaluation harness → REST API → production UI. Built end-to-end. |

---

## 🖼️ Preview

<table align="center">
  <tr>
    <td align="center"><b>📊 Dashboard</b></td>
    <td align="center"><b>🎯 Recommendations</b></td>
  </tr>
  <tr>
    <td><img src="screenshots/dashboard.png" alt="Model evaluation dashboard" width="470" /></td>
    <td><img src="screenshots/recommend.png" alt="Personalized problem recommendations" width="470" /></td>
  </tr>
  <tr>
    <td align="center"><b>🧪 Weakness Analyzer</b></td>
    <td align="center"><b>👥 Team Builder</b></td>
  </tr>
  <tr>
    <td><img src="screenshots/weakness.png" alt="Per-tag weakness analysis" width="470" /></td>
    <td><img src="screenshots/team.png" alt="Balanced team generation" width="470" /></td>
  </tr>
</table>

<div align="center"><i>Full light &amp; dark theme, driven by a single design-token system.</i></div>

---

## ✨ What it does

| Feature | What happens under the hood |
|---|---|
| **🎯 Problem Recommendation** | Known users get a pre-computed SVD score row. Unknown users are projected into the same latent space in real time via a 3-component hybrid. Both paths then flow through one shared ranking + difficulty-filter pipeline. |
| **🧪 Weakness Analysis** | Per-tag `solve_rate` and `coverage` are combined into a strength score, classifying all 38 Codeforces tags into weak / neutral / strong — computed live from the user's submission history. |
| **👥 Team Builder** | Scores every 3-person combination by the union size of their solved-tag sets, then greedily assigns teams to maximise tag-coverage diversity. |

Works for **any** Codeforces handle — no retraining, no sign-up.

---

## 📊 Results

Evaluated with an 80/20 per-user split, `TruncatedSVD(n_components=50)`, **K = 10**.

### Standard recommendation metrics

| Metric | Value | Users |
|---|---:|---:|
| Precision@10 | **21.08%** | 498 |
| Recall@10 | 2.68% | 498 |
| NDCG@10 | **22.95%** | 498 |

> Recall is low **by design** — a user's held-out set contains hundreds of problems while we recommend only 10. Precision and NDCG are the meaningful signals here.

### Weakness-alignment (the metric this project actually optimises for)

| Metric | Value | Users |
|---|---:|---:|
| **Weak Hit@10** | **92.12%** | 495 |
| Weak Precision@10 | **80.48%** | 495 |
| Avg aligned problems | **8.05 / 10** | 495 |
| Avg non-aligned problems | 1.95 / 10 | 495 |

### Tag-level weakness classification

| Metric | Value |
|---|---:|
| Precision | 70.19% |
| Recall | 49.90% |
| **F1 Score** | **56.51%** |
| Accuracy | 57.05% |
| Tag Coverage | 49.90% |

**Confusion matrix** (per-user averages, 495 users): TP `13.76` · FP `5.71` · FN `10.61` · TN `7.92`

<details>
<summary><b>ℹ️ A note on which numbers are which</b></summary>

Three places report metrics, and they are **not** all from the same run:

| Source | Run |
|---|---|
| The dashboard UI + this README | Latest run, **K = 10** |
| `backend/scripts/evaluate.py` | Ships with `K = 5` — edit line 391 to `K = 10` to reproduce the numbers above |
| `GET /api/dashboard` | Returns an **older K = 5** snapshot, hardcoded in `routes.py` |

The frontend dashboard renders its figures from a local constant rather than calling `/api/dashboard`, which is why it can show the newer run. Unifying these is on the roadmap.

</details>

---

## 📦 The Dataset

All model inputs come from the companion Kaggle dataset:

<div align="center">

### 👉 **[Codeforces User Dataset on Kaggle](https://www.kaggle.com/datasets/fardin35/codeforces-user-dataset)** 👈

</div>

**This step is not optional.** Three CSVs exceed GitHub's 100 MB limit and are therefore `.gitignore`d — a fresh clone **will not start** without them:

| File | Size | Status in repo | Needed by |
|---|---:|---|---|
| `cf_predictions.csv` | 215 MB | ❌ **Kaggle only** | Backend startup (the pre-computed SVD score matrix) |
| `raw_submissions.csv` | 159 MB | ❌ **Kaggle only** | Data pipeline / re-derivation |
| `processed_data.csv` | 56 MB | ❌ **Kaggle only** | Backend startup + `evaluate.py` |
| `problems.csv` | 483 KB | ✅ in repo | Tags & difficulty lookup |
| `user_features.csv` | 75 KB | ✅ in repo | Ratings, solve rates |
| `user_tag_weakness.csv` | 2.2 MB | ✅ in repo | Per-tag weakness (known users) |
| `evaluation_data.csv` | 2.0 MB | ✅ in repo | Ground-truth weak tags for evaluation |

Download the dataset and drop every file into **`backend/data/`**.

### Scale

```
2,040,756  raw submissions          (raw_submissions.csv)
  921,797  user × problem rows      (processed_data.csv)
  918,763  after cleaning           → the matrix that gets factorised
   10,864  unique problems          (problems.csv)
      995  users with full features (user_features.csv)
   34,138  user × tag weakness rows (evaluation_data.csv)
```

### Schema of the key tables

```
processed_data.csv    user, problem_id, solved, attempts, rating, tags
problems.csv          problem_id, rating, tags
user_features.csv     user, solved, attempts, solve_rate, avg_attempts,
                      avg_problem_rating, max_problem_rating, rating, max_rating
evaluation_data.csv   user, tag, attempts, solved, corpus_count, solve_rate,
                      coverage, strength_score, weakness_score, is_weak
```

---

## 🧬 How the engine works

The core lives in [`backend/recommender.py`](backend/recommender.py). Both user types converge on **one** ranking pipeline — there is no retraining at request time.

### Path A — known users

```
1.  Look up the pre-computed SVD row  R[user]        # cf_predictions.csv
2.  Drop problems the user already solved            # processed_data.csv
3.  Difficulty gate: max_rating ± 200                # widens to ±800 if too few survive
4.  nlargest(n) on the score
```

### Path B — cold start (handle unseen by the model)

The user is projected into the same latent space with an **explainable linear hybrid**:

```
final_score  =  0.50 · content  +  0.20 · difficulty  +  0.30 · cf
```

| Component | Definition | Intuition |
|---|---|---|
| `content` | max over the problem's tags of the user's mean solved-rating in that tag | *Have you shown skill in this topic?* |
| `difficulty` | `exp( −\|user_max_rating − problem_rating\| / 600 )` | *Is this in your challenge zone?* |
| `cf` | similarity-weighted mean of the top-10 cosine-nearest training users' SVD scores | *What worked for people like you?* |

The result then flows through **the exact same** exclusion → difficulty-filter → rank steps as Path A. Every score decomposes into three human-readable terms, so any recommendation can be explained.

### The weakness model

```
solve_rate  =  solved_in_tag / attempted_in_tag
coverage    =  solved_in_tag / total_solved_by_user
strength    =  0.40 · solve_rate  +  0.60 · coverage
weakness    =  1 − strength
```

| Strength | Class |
|---|---|
| `< 0.45` | 🔴 weak |
| `0.45 – 0.60` | ⚪ neutral |
| `> 0.60` | 🟢 strong |

Weighting `coverage` above `solve_rate` is deliberate: a 100% solve rate across two problems is not mastery.

### The team builder

[`backend/team_builder.py`](backend/team_builder.py) forms teams of 3:

1. Fetch each handle's solved-tag set (live CF API, cached).
2. Score every 3-combination by the **union size** of their tags.
3. Greedily assign the best combo whose members are all still free; repeat.
4. Report **compatibility** (mean pairwise Jaccard) and **coverage** (share of the global tag universe).

> Constraints: ≥ 3 handles, and the count must be divisible by 3.

---

## 🏗️ Architecture

```
┌───────────────────────────────┐                ┌──────────────────────────────┐
│   Next.js 16 · React 19       │                │   Flask REST API             │
│   ─────────────────────────   │   HTTP/JSON    │   ────────────────────────   │
│   • /dashboard   metrics      │ ─────────────► │   GET  /api/recommend/<h>    │
│   • /recommendation           │                │   GET  /api/weakness/v2/<h>  │
│   • /weakness    tag profile  │ ◄───────────── │   GET  /api/analytics/<h>    │
│   • /team        builder      │                │   POST /api/team             │
│   Tailwind 4 · design tokens  │                │   GET  /api/dashboard        │
└───────────────────────────────┘                └───────────────┬──────────────┘
                                                                 │ loaded once at boot
                                                 ┌───────────────▼──────────────┐
                                                 │  Recommender  (in memory)    │
                                                 │  • cf_predictions  215 MB    │
                                                 │  • processed_data   56 MB    │
                                                 │  • problems / features       │
                                                 └───────────────┬──────────────┘
                                                                 │ cold-start only
                                                 ┌───────────────▼──────────────┐
                                                 │  Codeforces public API       │
                                                 │  live fetch + preprocess     │
                                                 └──────────────────────────────┘
```

**Design decision:** every CSV is loaded **once at startup**, not per request. Boot costs a few seconds and ~1 GB RAM; in exchange, known-user recommendations are a pure in-memory lookup.

---

## ⚡ Quick Start

### Prerequisites

- Python **3.10+**
- Node.js **18+**
- ~500 MB free disk for the dataset

### 1 · Clone

```bash
git clone https://github.com/MDHossain093/code-recommend-ai.git
cd code-recommend-ai
```

### 2 · Get the data ⚠️ *required*

Download **[the Kaggle dataset](https://www.kaggle.com/datasets/fardin35/codeforces-user-dataset)** and place every CSV in `backend/data/`.

```bash
# Or via the Kaggle CLI:
pip install kaggle
kaggle datasets download -d fardin35/codeforces-user-dataset -p backend/data --unzip
```

Verify the three large files landed:

```bash
ls -lh backend/data/cf_predictions.csv backend/data/processed_data.csv backend/data/raw_submissions.csv
```

### 3 · Backend

```bash
cd backend
python -m venv .venv

source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

pip install -r requirements.txt
python app.py
```

Expect:

```
[app] Starting up — loading data into memory …
[recommender] Loading cf_predictions.csv …
[recommender] Loading processed_data.csv (solved sets) …
[recommender] All data loaded and model ready.
[app] Ready. Listening on http://127.0.0.1:5000
```

> ⏳ First boot takes ~20–60 s while the 215 MB score matrix is parsed. This is expected.

### 4 · Frontend

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

The root route redirects to `/dashboard`. To point the UI at a non-default API:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000/api
```

### 5 · Try it

| Handle type | Example | Path |
|---|---|---|
| In the training matrix | `tourist`, `Petr` | Instant SVD lookup |
| Anything else | your own handle | Live CF fetch + cold-start hybrid (~1 s) |

---

## 🔌 API Reference

| Endpoint | Method | Returns |
|---|---|---|
| `/` | GET | Health check |
| `/api/dashboard` | GET | Dataset + model statistics |
| `/api/recommend/<handle>?n=10` | GET | `{user, recommendations[]}` — `n` clamped to 1–50 |
| `/api/weakness/<handle>` | GET | Tag weakness for known users |
| `/api/weakness/v2/<handle>` | GET | Rich profile: `{user, summary, weak_tags, strong_tags, all_tags, coverage}` |
| `/api/analytics/<handle>` | GET | Full per-tag analytics |
| `/api/team` | POST | `{teams[]}` from body `{"users": [...]}` |

Every response is enveloped: `{"success": true, ...}` or `{"success": false, "message": "..."}`.

<details>
<summary><b>Example request &amp; response</b></summary>

```bash
curl "http://127.0.0.1:5000/api/recommend/tourist?n=2"
```

```json
{
  "success": true,
  "user": {
    "handle": "tourist",
    "rating": 3900,
    "max_rating": 3900,
    "solved": 1820,
    "solve_rate": 0.7826
  },
  "recommendations": [
    {
      "contestId": 1915,
      "index": "D",
      "name": "1915-D",
      "rating": 2400,
      "tags": ["binary search", "dp"],
      "score": 0.984312,
      "url": "https://codeforces.com/problemset/problem/1915/D"
    }
  ]
}
```

**Status codes:** `400` bad input · `404` handle not found · `502` CF API unreachable · `504` CF API timeout · `500` server error.

</details>

---

## 🧪 Reproduce the evaluation

```bash
cd backend
pip install scikit-learn scipy      # not in requirements.txt — evaluation-only deps
python scripts/evaluate.py
```

Re-runs the full harness: the 80/20 split, SVD training, Precision/Recall/NDCG@K, weakness alignment, and the tag-level confusion matrix.

> To match the K = 10 figures in this README, change `K = 5` to `K = 10` at [`scripts/evaluate.py:391`](backend/scripts/evaluate.py#L391).

---

## 📂 Project Structure

```
projectResearch/
├── backend/
│   ├── app.py                  # Flask entry — loads all data once at boot
│   ├── routes.py               # REST endpoints + error envelope
│   ├── recommender.py          # ⭐ Hybrid SVD engine (known + cold-start)
│   ├── new_user.py             # Cold-start: CF API fetch → tag strength profile
│   ├── team_builder.py         # Greedy 3-person team formation
│   ├── fetch_team.py           # Tag-profile fetcher + on-disk cache
│   ├── data/                   # ⚠️ CSVs — 3 large ones come from Kaggle
│   └── scripts/evaluate.py     # Offline evaluation harness
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.jsx      # Shell + no-flash theme script
│       │   ├── globals.css     # ⭐ Design tokens (light + dark)
│       │   ├── dashboard/      # Model metrics
│       │   ├── recommendation/ # Problem recommendations
│       │   ├── weakness/       # Tag weakness analyzer
│       │   └── team/           # Team builder
│       ├── components/         # Sidebar, Navbar, ThemeToggle, PageHeader, …
│       ├── hooks/              # useRecentHandles (localStorage)
│       ├── lib/                # ui.js (style primitives) · utils.js (helpers)
│       └── services/api.js     # Fetch wrapper + error normalisation
│
└── screenshots/
```

---

## 🎨 Frontend design system

The UI is built on **semantic design tokens**, not hardcoded palette classes.

- **One token set, two themes.** `globals.css` defines every surface, border and accent as an OKLCH custom property under `:root` and `.dark`. Components reference `bg-card`, `text-muted-foreground`, `bg-ok/12` — never `bg-slate-900`.
- **Six semantic accents** (`ok · info · warn · bad · iris · aqua`), each with a saturated fill tone and a contrast-tuned text tone, so every chart bar and status chip stays legible in both themes.
- **Zero-flash theme switching.** An inline script in the document `<head>` applies the saved/system theme before first paint, so there is no white flash and no hydration mismatch — per the [Next.js preventing-flash guide](https://nextjs.org/docs/app/guides/preventing-flash-before-hydration).
- **Shared primitives** in `lib/ui.js` (`card`, `input`, `btnPrimary`, `tonePill`, …) keep all four routes visually identical instead of each re-declaring its own class strings.
- Codeforces rating tiers map onto the same tokens, so `tourist`'s red stays readable on a white background.

---

## 🧰 Tech Stack

**Backend** — Python 3.10 · Flask · Flask-CORS · pandas · NumPy · `requests`
**Model** — Truncated SVD (50 components) over a binary user × problem matrix · cosine-similarity neighbour blending · scikit-learn + SciPy *(evaluation only)*
**Frontend** — Next.js 16 (App Router, Turbopack) · React 19 · Tailwind CSS 4 · lucide-react
**Data** — 2.04M submissions · 10,864 problems · 995 users

---

## 🗺️ Roadmap

- [ ] Unify the three metric sources behind a single generated `metrics.json`
- [ ] Learning-to-rank layer (LambdaMART) on top of the SVD scores
- [ ] Learn the hybrid weights `(0.5 / 0.2 / 0.3)` instead of hand-setting them
- [ ] Sequence-aware user embeddings over submission history
- [ ] Redis cache for CF fetches → sub-200 ms cold start
- [ ] Swap the 215 MB dense CSV for a sparse `.npz` + memory-mapped load
- [ ] Public demo on Vercel + Render

---

## 📜 License

MIT — see [`LICENSE`](LICENSE).

## 👤 Author

**MD Hossain** · [@MDHossain093](https://github.com/MDHossain093)

> Built end-to-end as a research artifact: data collection, feature engineering, model, evaluation harness, REST API, and production UI. Interested in ML systems and recommender engines.

<div align="center">

⭐ **If this was useful, a star goes a long way.** ⭐

</div>
