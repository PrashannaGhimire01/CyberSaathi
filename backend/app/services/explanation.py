import json
from pathlib import Path

TEXT_PATH = Path(__file__).parent.parent / "rules" / "explanations.json"

with open(TEXT_PATH, encoding="utf-8") as f:
    TEXT = json.load(f)

def build_explanation(level, signals, language):
    reasons = list(dict.fromkeys(s["reasons"][language] for s in signals))
    return {
        "headline": TEXT["headlines"][level][language],
        "reasons": reasons,
        "actions": TEXT["actions"][level][language],
        "disclaimer": TEXT["disclaimer"][language],
    }