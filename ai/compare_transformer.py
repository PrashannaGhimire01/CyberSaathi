"""RQ2: compare the lightweight TF-IDF + LogisticRegression model against a
multilingual transformer (sentence embeddings + LogisticRegression) on the SAME
honest held-out test set. Mirrors ai/train_eval.py's split and leakage guard,
so the two models are judged on identical data."""
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).parent.parent
TRAIN = ROOT / "data" / "dataset.csv"
TEST = ROOT / "data" / "testset.csv"
LEAK_THRESHOLD = 0.80
EMB_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def load(path):
    df = pd.read_csv(path, encoding="utf-8").dropna(subset=["text", "label"])
    return df[df["text"].str.strip() != ""]

train_df, test_df = load(TRAIN), load(TEST)

# --- leakage guard: identical to train_eval.py ---
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))
vec.fit(train_df["text"].tolist() + test_df["text"].tolist())
sims = cosine_similarity(vec.transform(train_df["text"].tolist()),
                         vec.transform(test_df["text"].tolist()))
keep = sims.max(axis=1) < LEAK_THRESHOLD
removed = int((~keep).sum())
train_df = train_df[keep]

X_train = train_df["text"].tolist()
y_train = (train_df["label"] == "scam").astype(int).tolist()
X_test = test_df["text"].tolist()
y_test = (test_df["label"] == "scam").astype(int).tolist()
print(f"Train (after removing {removed} overlaps): {len(X_train)}   Test: {len(X_test)}")

def report(name, y_pred):
    print(f"\n=== {name} ===")
    print(classification_report(y_test, y_pred, target_names=["legit", "scam"], digits=3))
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    print(f"  FP (false alarms): {fp}   FN (missed scams): {fn}   TP: {tp}   TN: {tn}")

# --- Model 1: TF-IDF + LogisticRegression (the app's on-device model) ---
tfidf = Pipeline([
    ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2)),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
])
tfidf.fit(X_train, y_train)
report("TF-IDF + LogisticRegression  (lightweight, runs on-device)", tfidf.predict(X_test))

# --- Model 2: multilingual transformer embeddings + LogisticRegression ---
from sentence_transformers import SentenceTransformer
print(f"\nLoading transformer {EMB_MODEL} (first run downloads ~0.5 GB)...")
emb = SentenceTransformer(EMB_MODEL)
Xtr = emb.encode(X_train, normalize_embeddings=True, show_progress_bar=True)
Xte = emb.encode(X_test, normalize_embeddings=True, show_progress_bar=True)
clf = LogisticRegression(max_iter=1000, class_weight="balanced")
clf.fit(Xtr, y_train)
report("Transformer embeddings + LogisticRegression  (heavier, server-only)", clf.predict(Xte))