"""Hybrid assessment: rule-based signals + ML, with a rule-based legit-override.
Keeps CyberSaathi explainable (rules give the reasons) while ML adds recall."""
from urllib.parse import urlparse
from app.services.message_analyzer import analyze_message, URL_PATTERN
from app.services.url_analyzer import analyze_url
from app.services.risk_engine import calculate_risk
from app.services.ml_classifier import scam_probability, MODEL_AVAILABLE

MAX_URLS = 5
ML_THRESHOLD = 0.5

# Recognised legitimate Nepali domains — VERIFY/EXTEND against official sources.
OFFICIAL_DOMAINS = [
    "esewa.com.np", "khalti.com", "nabilbank.com", "nepalbank.com.np",
    "ntc.net.np", "ncell.axiata.com", "daraz.com.np", "nepalpost.gov.np",
    "imepay.com.np", "connectips.com", "fonepay.com", "worldlink.com.np",
    "nea.org.np",
]
REQUEST_WORDS = ["pay ", "send", "fee", "processing", "deposit", "registration",
                 "otp", "pin", "password", "transfer", "pathaunuhos", "pathaunu",
                 "dinuhos"]

def _links_all_official(text):
    urls = URL_PATTERN.findall(text)
    if not urls:
        return False
    for u in urls:
        host = (urlparse(u if u.lower().startswith("http") else "http://" + u).hostname or "").lower()
        if not any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS):
            return False
    return True

def _has_request_words(text):
    low = text.lower()
    return any(w in low for w in REQUEST_WORDS)

def assess(text):
    signals = analyze_message(text)
    for url in URL_PATTERN.findall(text)[:MAX_URLS]:
        signals.extend(analyze_url(url))
    rule_score, rule_level = calculate_risk(signals)

    ml_prob = scam_probability(text)
    ml_flag = ml_prob is not None and ml_prob >= ML_THRESHOLD

    override = False
    if ml_flag and rule_level == "LOW" and _links_all_official(text) and not _has_request_words(text):
        ml_flag = False
        override = True

    level = rule_level
    if ml_flag:
        level = {"LOW": "MEDIUM", "MEDIUM": "HIGH", "HIGH": "HIGH"}[rule_level]

    ml_pct = int(round((ml_prob or 0) * 100))
    score = max(rule_score, ml_pct if ml_flag else 0)

    return {
        "level": level,
        "score": score,
        "signals": signals,
        "ml_available": MODEL_AVAILABLE,
        "ml_probability": round(ml_prob, 3) if ml_prob is not None else None,
        "ml_flagged": ml_flag,
        "override_applied": override,
    }