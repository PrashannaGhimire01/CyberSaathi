import json
import re
from pathlib import Path

RULES_PATH = Path(__file__).parent.parent / "rules" / "message_rules.json"
URL_PATTERN = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)

with open(RULES_PATH, encoding="utf-8") as f:
    RULES = json.load(f)

def keyword_found(keyword, text):
    if keyword.isascii():
        return re.search(r"\b" + re.escape(keyword) + r"\b", text) is not None
    return keyword in text

def analyze_message(text):
    lowered = text.lower()
    signals = []
    for name, category in RULES["categories"].items():
        matched = [k for k in category["keywords"] if keyword_found(k, lowered)]
        if matched:
            signals.append({"signal": name, "weight": category["weight"],
                            "reason": category["reason_en"], "matched": matched})
    urls = URL_PATTERN.findall(text)
    if urls:
        signals.append({"signal": "contains_link", "weight": RULES["link"]["weight"],
                        "reason": RULES["link"]["reason_en"], "matched": urls})
    return signals