"""RQ2 centrepiece: rule-based vs ML, head-to-head on the SAME raw test set."""
import sys
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import (classification_report, precision_score,
                             recall_score, f1_score)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))   # so `import app...` works

try:
    from app.services.message_analyzer import analyze_message, URL_PATTERN
    from app.services.url_analyzer import analyze_url
    from app.services.risk_engine import calculate_risk
except Exception as e:
    print("Could not import the rule-based system from backend/.")
    print("Run this from the CyberSaathi root, and check backend/app/services/ exists.")
    print("Error:", e)
    sys.exit(1)

MODEL = ROOT / "ai" / "models" / "scam_model.joblib"
TEST = ROOT / "data" / "testset.csv"
MAX_URLS = 5

def rule_predict(text):
    signals = analyze_message(text)
    for url in URL_PATTERN.findall(text)[:MAX_URLS]:
        signals.extend(analyze_url(url))
    _, level = calculate_risk(signals)
    return 1 if level in ("HIGH", "MEDIUM") else 0, level

model = joblib.load(MODEL)
df = pd.read_csv(TEST, encoding="utf-8").dropna(subset=["text", "label"])
df = df[df["text"].str.strip() != ""]
texts = df["text"].tolist()
y_true = (df["label"] == "scam").astype(int).tolist()

y_ml = model.predict(texts).tolist()
y_rule, levels = [], []
for t in texts:
    p, lvl = rule_predict(t)
    y_rule.append(p); levels.append(lvl)

print("=== RULE-BASED (HIGH or MEDIUM counted as scam) ===")
print(classification_report(y_true, y_rule, target_names=["legit", "scam"], digits=3))
print("=== MACHINE LEARNING (TF-IDF char n-grams + LogReg) ===")
print(classification_report(y_true, y_ml, target_names=["legit", "scam"], digits=3))

def line(name, yp):
    P = precision_score(y_true, yp, pos_label=1, zero_division=0)
    R = recall_score(y_true, yp, pos_label=1, zero_division=0)
    F = f1_score(y_true, yp, pos_label=1, zero_division=0)
    return f"  {name:12} scam precision={P:.2f}  recall={R:.2f}  F1={F:.2f}"

print("Side by side (scam class):")
print(line("Rule-based", y_rule))
print(line("ML", y_ml))

print("\nWhere they disagree:")
any_dis = False
for t, yt, yr, ym in zip(texts, y_true, y_rule, y_ml):
    if yr != ym:
        any_dis = True
        lab = "scam" if yt == 1 else "legit"
        rp = "scam" if yr == 1 else "legit"
        mp = "scam" if ym == 1 else "legit"
        who = "rule right" if rp == lab else "ML right"
        print(f"  true={lab:5} | rule={rp:5} ml={mp:5} ({who}) | {t[:55]}")
if not any_dis:
    print("  (they agreed on every message)")