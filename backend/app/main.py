from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.services.message_analyzer import analyze_message, URL_PATTERN
from app.services.url_analyzer import analyze_url
from app.services.risk_engine import calculate_risk
from app.services.explanation import build_explanation
from app.services.emergency import build_emergency_plan
from pathlib import Path
from fastapi.staticfiles import StaticFiles

MAX_URLS = 5
Language = Literal["en", "ne"]
Shared = Literal["otp", "password", "card", "money", "app_installed", "personal_info"]


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

def build_response(signals, language):
    score, level = calculate_risk(signals)
    return {"risk": level, "score": score,
            "explanation": build_explanation(level, signals, language),
            "signals": signals}

@app.get("/")
def home():
    return {"service": "CyberSaathi", "status": "running"}

@app.post("/analyze/message")
def check_message(data: MessageIn):
    signals = analyze_message(data.message)
    for url in URL_PATTERN.findall(data.message)[:MAX_URLS]:
        signals.extend(analyze_url(url))
    return build_response(signals, data.language)

@app.post("/analyze/url")
def check_url(data: UrlIn):
    return build_response(analyze_url(data.url), data.language)
    
@app.post("/emergency")
def emergency(data: EmergencyIn):
    return {"steps": build_emergency_plan(set(data.shared), data.language)}

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")