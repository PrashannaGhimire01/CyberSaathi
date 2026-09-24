def calculate_risk(signals):
    score = min(sum(s["weight"] for s in signals), 100)
    if score >= 60:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"
    return score, level
    