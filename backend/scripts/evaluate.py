import pandas as pd
import numpy as np
from pathlib import Path

from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

# ==============================
# PATHS
# ==============================

_BASE = Path(__file__).parent.parent

DATA_PATH = _BASE / "data" / "processed_data.csv"
TAG_WEAK_PATH = _BASE / "data" / "evaluation_data.csv"
PROBLEM_PATH = _BASE / "data" / "problems.csv"
USER_FEATURE_PATH = _BASE / "data" / "user_features.csv"

# ==============================
# LOAD DATA
# ==============================

print("📥 Loading data...")

df = pd.read_csv(DATA_PATH)
tag_weak_df = pd.read_csv(TAG_WEAK_PATH)
problem_df = pd.read_csv(PROBLEM_PATH)
user_features = pd.read_csv(USER_FEATURE_PATH)

# ==============================
# PREPROCESSING
# ==============================

print("🧹 Preprocessing data...")

# clean tags
problem_df["tags"] = (
    problem_df["tags"]
    .fillna("")
    .astype(str)
)

# remove invalid users
df = df[
    df["user"]
    .astype(str)
    .str.contains("[a-zA-Z]")
]

# remove missing ratings
df = df.dropna(subset=["rating"])

# remove duplicates
df = df.drop_duplicates(
    subset=["user", "problem_id"]
)

# correct types
df["rating"] = df["rating"].astype(int)
df["solved"] = df["solved"].astype(int)

print("Total rows:", len(df))

# ==============================
# TRAIN TEST SPLIT
# ==============================

print("⏳ Splitting train/test...")

train_list = []
test_list = []

for user, group in df.groupby("user"):

    # minimum interactions
    if len(group) < 5:
        continue

    # shuffle
    group = group.sample(frac=1, random_state=42)

    split_idx = int(0.8 * len(group))

    train_list.append(group.iloc[:split_idx])
    test_list.append(group.iloc[split_idx:])

train = pd.concat(train_list)
test = pd.concat(test_list)

print("Train size:", len(train))
print("Test size:", len(test))

# ==============================
# BUILD USER-PROBLEM MATRIX
# ==============================

print("⚙️ Building matrix...")

pivot = train.pivot_table(
    index="user",
    columns="problem_id",
    values="solved",
    fill_value=0
)

users = pivot.index.tolist()

# ==============================
# TRAIN SVD MODEL
# ==============================

print("🧠 Training SVD model...")

sparse_matrix = csr_matrix(
    pivot.values
)

svd = TruncatedSVD(
    n_components=50,
    random_state=42
)

latent_matrix = svd.fit_transform(
    sparse_matrix
)

reconstructed_matrix = np.dot(
    latent_matrix,
    svd.components_
)

svd_scores_df = pd.DataFrame(
    reconstructed_matrix,
    index=users,
    columns=pivot.columns
)

# ==============================
# HELPERS
# ==============================

def get_user_max_rating(user):

    row = user_features[
        user_features["user"] == user
    ]

    if not row.empty:

        max_rating = row["max_rating"].iloc[0]

        if not pd.isna(max_rating):
            return int(max_rating)

    # Fallback: highest solved problem rating
    solved_data = train[
        (train["user"] == user) &
        (train["solved"] == 1)
    ]

    if solved_data.empty:
        return None

    return int(
        solved_data["rating"].max()
    )

def get_weak_tags(user):

    return set(
        tag_weak_df[
            (tag_weak_df["user"] == user) &
            (tag_weak_df["is_weak"] == 1)
        ]["tag"]
    )


def get_problem_info(pid):

    row = problem_df[
        problem_df["problem_id"] == pid
    ]

    if row.empty:
        return set()

    tags_value = row["tags"].iloc[0]

    if pd.isna(tags_value):
        return set()

    return set(
        str(tags_value).split(",")
    )

# ==============================
# SVD RECOMMENDER
# ==============================

def recommend(user, top_k=5):

    # user not found
    if user not in svd_scores_df.index:
        return []

    # =====================================
    # GET SVD SCORES
    # =====================================

    scores = svd_scores_df.loc[user]

    # =====================================
    # REMOVE ALREADY SOLVED
    # =====================================

    user_solved = set(
        train[
            (train["user"] == user) &
            (train["solved"] == 1)
        ]["problem_id"]
    )

    scores = scores.drop(
        labels=list(user_solved),
        errors="ignore"
    )

    # =====================================
    # USER MAX CF RATING
    # =====================================

    user_max_rating = get_user_max_rating(user)

    if user_max_rating is None:
        return []

    min_rating = user_max_rating - 200
    max_rating = user_max_rating + 200

    # =====================================
    # DIFFICULTY FILTER
    # =====================================

    valid_problems = train[
        (train["rating"] >= min_rating) &
        (train["rating"] <= max_rating)
    ]["problem_id"].unique()

    scores = scores[
        scores.index.isin(valid_problems)
    ]

    # =====================================
    # SORT SCORES
    # =====================================

    scores = scores.sort_values(
        ascending=False
    )

    return scores.head(top_k).index.tolist()

# ==============================
# STANDARD METRICS
# ==============================

def precision_at_k(rec, actual, k):

    if not rec:
        return 0

    return len(
        set(rec[:k]) & set(actual)
    ) / k


def recall_at_k(rec, actual, k):

    if not actual:
        return 0

    return len(
        set(rec[:k]) & set(actual)
    ) / len(actual)


def ndcg_at_k(rec, actual, k):

    dcg = 0

    for i, p in enumerate(rec[:k]):

        if p in actual:
            dcg += 1 / np.log2(i + 2)

    idcg = sum([
        1 / np.log2(i + 2)
        for i in range(
            min(len(actual), k)
        )
    ])

    return (
        dcg / idcg
        if idcg > 0
        else 0
    )

# ==============================
# WEAKNESS METRICS
# ==============================

def evaluate_weakness(user, recs):
    weak_tags = get_weak_tags(user)

    if not weak_tags:
        return None

    covered_tags = set()
    FP = 0

    for pid in recs:

        tags = get_problem_info(pid)

        tag_match = len(tags & weak_tags) > 0

        if tag_match:
            covered_tags.update(tags & weak_tags)
        else:
            FP += 1

    # =====================================
    # CONFUSION MATRIX
    # =====================================

    TP = len(covered_tags)
    FN = len(weak_tags - covered_tags)

    precision = (
        TP / (TP + FP)
        if (TP + FP) > 0
        else 0
    )

    recall = (
        TP / (TP + FN)
        if (TP + FN) > 0
        else 0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    accuracy = (
        TP / (TP + FP + FN)
        if (TP + FP + FN) > 0
        else 0
    )

    tag_coverage = (
        TP / len(weak_tags)
        if len(weak_tags) > 0
        else 0
    )

    weak_hit = 1 if TP > 0 else 0

    return (
        precision,
        recall,
        f1,
        accuracy,
        tag_coverage,
        weak_hit,
        TP,
        FP,
        FN
    )

# ==============================
# EVALUATION LOOP
# ==============================

print("📊 Evaluating recommender...")

K = 5

# standard metrics
precisions = []
recalls = []
ndcgs = []

# weakness metrics
precision_w_list = []
recall_w_list = []
f1_w_list = []
accuracy_w_list = []

tag_coverages = []
weak_hits = []

TP_list = []
FP_list = []
FN_list = []

evaluated_users = 0

for user in users[:500]:

    actual = test[
        (test["user"] == user) &
        (test["solved"] == 1)
    ]["problem_id"].tolist()

    if not actual:
        continue

    recs = recommend(user, K)

    if not recs:
        continue

    evaluated_users += 1

    # ==========================
    # STANDARD METRICS
    # ==========================

    precisions.append(
        precision_at_k(recs, actual, K)
    )

    recalls.append(
        recall_at_k(recs, actual, K)
    )

    ndcgs.append(
        ndcg_at_k(recs, actual, K)
    )

    # ==========================
    # WEAKNESS METRICS
    # ==========================

    res = evaluate_weakness(user, recs)

    if res:
        prec, rec, f1, acc, tc, wh, TP, FP, FN = res

        precision_w_list.append(prec)
        recall_w_list.append(rec)
        f1_w_list.append(f1)
        accuracy_w_list.append(acc)

        tag_coverages.append(tc)
        weak_hits.append(wh)

        TP_list.append(TP)
        FP_list.append(FP)
        FN_list.append(FN)

# ==============================
# FINAL RESULTS
# ==============================

print("\n" + "=" * 70)
print("📈 STANDARD RECOMMENDATION METRICS")
print("=" * 70)

print(f"Users Evaluated: {evaluated_users}")

print(f"\nPrecision@{K}: {np.mean(precisions):.4f}")
print(f"Recall@{K}:    {np.mean(recalls):.4f}")
print(f"NDCG@{K}:      {np.mean(ndcgs):.4f}")

print("\n" + "=" * 70)
print("📊 WEAKNESS CONFUSION MATRIX")
print("=" * 70)

print(f"Average TP: {np.mean(TP_list):.2f}")
print(f"Average FP: {np.mean(FP_list):.2f}")
print(f"Average FN: {np.mean(FN_list):.2f}")

print("\n" + "=" * 70)
print("🎯 WEAKNESS LEARNING METRICS")
print("=" * 70)

print(f"Precision: {np.mean(precision_w_list):.4f}")
print(f"Recall:    {np.mean(recall_w_list):.4f}")
print(f"F1 Score:  {np.mean(f1_w_list):.4f}")
print(f"Accuracy:  {np.mean(accuracy_w_list):.4f}")

print(f"Tag Coverage: {np.mean(tag_coverages):.4f}")
print(f"Weak Hit@{K}: {np.mean(weak_hits):.4f}")

print("\n✅ Evaluation Complete")
