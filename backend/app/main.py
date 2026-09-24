from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.services.message_analyzer import analyze_message
from app.services.risk_engine import calculate_risk

app = FastAPI(title="CyberSaathi")

class MessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=5000)

@app.post("/analyze/message")
def check_message(data: MessageIn):
    signals = analyze_message(data.message)
    score, level = calculate_risk(signals)
    return {"risk": level, "score": score, "reasons": [s["reason"] for s in signals], "signals": signals}