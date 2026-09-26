"""Train CyberSaathi's first ML scam classifier and evaluate it honestly."""
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data" / "dataset.csv"
MODEL_OUT = ROOT / "ai" / "models" / "scam_model.joblib"
RANDOM_STATE = 42

def main():
    df = pd.read_csv(DATA, encoding="utf-8")
    df = df.dropna(subset=["text", "label"])
    df = df[df["text"].str.strip() != ""]
    print(f"Loaded {len(df)} messages")
    print("Labels:", df["label"].value_counts().to_dict())

    X = df["text"].tolist()
    y = (df["label"] == "scam").astype(int).tolist()  # 1 = scam, 0 = legit

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"\nTrain: {len(X_train)}  Test: {len(X_test)}")

    model = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n=== Evaluation on held-out test set ===")
    print(classification_report(y_test, y_pred, target_names=["legit", "scam"], digits=3))
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    print("Confusion matrix:")
    print(f"  True legit kept legit (TN): {tn}")
    print(f"  Legit flagged as scam (FP): {fp}   <- false alarms")
    print(f"  Scam missed as legit  (FN): {fn}   <- dangerous misses")
    print(f"  Scam caught as scam   (TP): {tp}")

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    print(f"\nModel saved to {MODEL_OUT}")

    # quick smoke test on two obvious messages
    for msg in ["Badhai cha! Lottery jitnubhayo. OTP pathaunuhos.",
                "Your eSewa OTP is 482913. Do not share this code with anyone."]:
        proba = model.predict_proba([msg])[0][1]
        print(f"  scam-prob {proba:.2f}: {msg[:50]}")

if __name__ == "__main__":
    main()