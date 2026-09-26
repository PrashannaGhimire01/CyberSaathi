"""Honest evaluation: train on the AI-assisted dataset, test on the RAW
collected messages. Removes any training row that overlaps the test set."""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).parent.parent
TRAIN = ROOT / "data" / "dataset.csv"
TEST = ROOT / "data" / "testset.csv"
MODEL_OUT = ROOT / "ai" / "models" / "scam_model.joblib"
LEAK_THRESHOLD = 0.80

def load(path):
    df = pd.read_csv(path, encoding="utf-8").dropna(subset=["text", "label"])
    return df[df["text"].str.strip() != ""]

train_df = load(TRAIN)
test_df = load(TEST)
print(f"Train: {len(train_df)}  Test: {len(test_df)}")
print(f"Test balance: {test_df['label'].value_counts().to_dict()}")

# --- leakage guard: drop training rows too similar to ANY test message ---
vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))
vec.fit(train_df["text"].tolist() + test_df["text"].tolist())
sims = cosine_similarity(vec.transform(train_df["text"].tolist()),
                         vec.transform(test_df["text"].tolist()))
keep = sims.max(axis=1) < LEAK_THRESHOLD
removed = int((~keep).sum())
print(f"Removed {removed} training rows overlapping the test set (>= {LEAK_THRESHOLD} similar)")
train_df = train_df[keep]

X_train = train_df["text"].tolist()
y_train = (train_df["label"] == "scam").astype(int).tolist()
X_test = test_df["text"].tolist()
y_test = (test_df["label"] == "scam").astype(int).tolist()

model = Pipeline([
    ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2)),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
])
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print("\n=== HONEST: trained on AI-assisted data, tested on RAW collected messages ===")
print(classification_report(y_test, y_pred, target_names=["legit", "scam"], digits=3))
tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
print("Confusion matrix:")
print(f"  legit kept legit (TN): {tn}")
print(f"  legit flagged scam (FP): {fp}   <- false alarms")
print(f"  scam missed       (FN): {fn}   <- dangerous misses")
print(f"  scam caught       (TP): {tp}")

MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_OUT)
print(f"\nModel saved to {MODEL_OUT}")