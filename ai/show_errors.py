from pathlib import Path
import joblib, pandas as pd

ROOT = Path(__file__).parent.parent
model = joblib.load(ROOT / "ai" / "models" / "scam_model.joblib")
df = pd.read_csv(ROOT / "data" / "testset.csv", encoding="utf-8").dropna(subset=["text", "label"])
df = df[df["text"].str.strip() != ""]

for _, r in df.iterrows():
    prob = model.predict_proba([r["text"]])[0][1]
    pred = "scam" if prob >= 0.5 else "legit"
    if pred != r["label"]:
        print(f"  prob={prob:.2f}  true={r['label']:5}  pred={pred:5}  {r['text'][:70]}")