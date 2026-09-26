"""Measure near-duplicate overlap between the train and test splits.
High overlap = the 'exam' contains rewordings of the 'study notes' = leakage."""
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "dataset.csv"

df = pd.read_csv(DATA, encoding="utf-8").dropna(subset=["text", "label"])
X = df["text"].tolist()
y = (df["label"] == "scam").astype(int).tolist()
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))
train_vecs = vec.fit_transform(X_train)
test_vecs = vec.transform(X_test)

sims = cosine_similarity(test_vecs, train_vecs)
nearest = sims.max(axis=1)

for thresh in (0.95, 0.90, 0.80, 0.70):
    n = (nearest >= thresh).sum()
    print(f"  test messages with a train twin >= {thresh:.2f} similar: {n}/{len(X_test)} ({100*n/len(X_test):.0f}%)")
print(f"\n  average nearest-train similarity: {nearest.mean():.2f}")
print("  (near 1.0 = heavy leakage; near 0.3 = genuinely new test messages)")

# show the 3 most-leaked test messages next to their train twin
import numpy as np
order = np.argsort(-nearest)
print("\n  Most similar test/train pairs:")
for i in order[:3]:
    j = sims[i].argmax()
    print(f"   sim={nearest[i]:.2f}")
    print(f"     TEST : {X_test[i][:70]}")
    print(f"     TRAIN: {X_train[j][:70]}")