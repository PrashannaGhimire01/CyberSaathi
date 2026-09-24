SAFETY_DISCOUNT = 30
DISCOUNTABLE = {"credential_request", "safety_advice"}

def calculate_risk(signals):
    names = {s["signal"] for s in signals}
    score = sum(s["weight"] for s in signals)
    other_warnings = names - DISCOUNTABLE
    if "safety_advice" in names and not other_warnings:
        score -= SAFETY_DISCOUNT
    score = max(0, min(score, 100))
    if score >= 60:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"
    return score, level


