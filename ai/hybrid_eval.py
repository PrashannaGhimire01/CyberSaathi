"""Hybrid = ML for recall + rule-based legit-override for precision.
Rule:  trust ML's SCAM verdict, EXCEPT downgrade to legit when the message
       looks benign (rules see no scam signal), its only links point to
       recognised OFFICIAL domains, and it contains no scam-style request.
Evaluated on the same raw test set as rule-based and ML."""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
import joblib
import pandas as pd
from sklearn.metrics import (classification_report, precision_score,
                             recall_score, f1_score)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.services.message_analyzer import analyze_message, URL_PATTERN
from app.services.url_analyzer import analyze_url
from app.services.risk_engine import calculate_risk

MODEL = ROOT / "ai" / "models" / "scam_model.joblib"
TEST = ROOT / "data" / "testset.csv"

# Recognised legitimate Nepali domains. VERIFY/EXTEND these against official sources.
OFFICIAL_DOMAINS = [
    "esewa.com.np", "khalti.com", "nabilbank.com", "nepalbank.com.np",
    "ntc.net.np", "ncell.axiata.com", "daraz.com.np", "nepalpost.gov.np",
    "imepay.com.np", "connectips.com", "fonepay.com", "worldlink.com.np",
    "nea.org.np", "sanimabank.com", "globalimebank.com", "nicasiabank.com",
]
REQUEST_WORDS = ["pay", "send", "fee", "processing", "deposit", "registration",
                 "otp", "pin", "password", "transfer", "pathaunuhos", "pathaunu",
                 "dinuhos", "बुझाउनु", "पठाउनु"]

def links_all_official(text):
    urls = URL_PATTERN.findall(text)
    if not urls:
        return False
    for u in urls:
        host = (urlparse(u if u.lower().startswith("http") else "http://" + u).hostname or "").lower()
        if not any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS):
            return False
    return True

def has_request_words(text):
    low = text.lower()
    return any(w in low for w in REQUEST_WORDS)

def rule_level(text):
    signals = analyze_message(text)
    for url in URL_PATTERN.findall(text)[:5]:
        signals.extend(analyze_url(url))
    return calculate_risk(signals)[1]

def hybrid_predict(text, ml_pred):
    if ml_pred == 1:  # ML says scam
        if rule_level(text) == "LOW" and links_all_official(text) and not has_request_words(text):
            return 0  # legit override
    return ml_pred

model = joblib.load(MODEL)
df = pd.read_csv(TEST, encoding="utf-8").dropna(subset=["text", "label"])
df = df[df["text"].str.strip() != ""]
texts = df["text"].tolist()
y_true = (df["label"] == "scam").astype(int).tolist()
y_ml = model.predict(texts).tolist()
y_rule = [1 if rule_level(t) in ("HIGH", "MEDIUM") else 0 for t in texts]
y_hyb = [hybrid_predict(t, m) for t, m in zip(texts, y_ml)]

print("=== HYBRID (ML + rule-based legit override) ===")
print(classification_report(y_true, y_hyb, target_names=["legit", "scam"], digits=3))

def line(name, yp):
    return (f"  {name:12} scam  P={precision_score(y_true,yp,pos_label=1,zero_division=0):.2f}"
            f"  R={recall_score(y_true,yp,pos_label=1,zero_division=0):.2f}"
            f"  F1={f1_score(y_true,yp,pos_label=1,zero_division=0):.2f}")
print("Three-way comparison (scam class):")
print(line("Rule-based", y_rule))
print(line("ML", y_ml))
print(line("Hybrid", y_hyb))

print("\nRemaining hybrid errors:")
errs = 0
for t, yt, yh in zip(texts, y_true, y_hyb):
    if yt != yh:
        errs += 1
        print(f"  true={'scam' if yt else 'legit':5} pred={'scam' if yh else 'legit':5} | {t[:60]}")
if not errs:
    print("  none — hybrid classified every test message correctly")