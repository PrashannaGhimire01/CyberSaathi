from typing import Literal
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.services.url_analyzer import analyze_url
from app.services.risk_engine import calculate_risk
from app.services.explanation import build_explanation
from app.services.emergency import build_emergency_plan
from app.services.hybrid import assess
from app.services.lessons import get_lessons

Language = Literal["en", "ne"]
Shared = Literal["otp", "password", "card", "money", "app_installed", "personal_info"]

ML_REASON = {
    "en": "Its overall wording is similar to known scam messages (flagged by our AI model).",
    "ne": "यसको समग्र लेखन ज्ञात ठगी सन्देशहरूसँग मिल्दोजुल्दो छ (हाम्रो AI मोडेलले चिन्ह लगायो)।",
}

app = FastAPI(title="CyberSaathi")

class MessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    language: Language = "en"

class UrlIn(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    language: Language = "en"

class EmergencyIn(BaseModel):
    shared: list[Shared] = Field(default_factory=list, max_length=6)
    language: Language = "en"

@app.get("/")
def home():
    return {"service": "CyberSaathi", "status": "running"}

@app.post("/analyze/message")
def check_message(data: MessageIn):
    result = assess(data.message)
    explanation = build_explanation(result["level"], result["signals"], data.language)
    if result["ml_flagged"]:
        reason = ML_REASON[data.language]
        if reason not in explanation["reasons"]:
            explanation["reasons"].append(reason)
    return {
        "risk": result["level"],
        "score": result["score"],
        "explanation": explanation,
        "ml": {
            "available": result["ml_available"],
            "probability": result["ml_probability"],
            "flagged": result["ml_flagged"],
            "override_applied": result["override_applied"],
        },
        "signals": result["signals"],
    }

@app.post("/analyze/url")
def check_url(data: UrlIn):
    signals = analyze_url(data.url)
    score, level = calculate_risk(signals)
    return {
        "risk": level,
        "score": score,
        "explanation": build_explanation(level, signals, data.language),
        "signals": signals,
    }

@app.post("/emergency")
def emergency(data: EmergencyIn):
    return {"steps": build_emergency_plan(set(data.shared), data.language)}

STATIC_DIR = Path(__file__).parent / "static"

@app.get("/lessons")
def lessons(language: Language = "en"):
    return {"lessons": get_lessons(language)}

app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")