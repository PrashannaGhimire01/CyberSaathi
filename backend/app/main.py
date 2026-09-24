from fastapi import FastAPI 
from pydantic import BaseModel

app = FastAPI(title="CyberSaathi")

class MessageIn(BaseModel):
    message: str

@app.post("/analyze/message")
def analyze_message(data:MessageIn):
    return{"risk": "UNKNOWN", "score":0, "reasons": [], "length": len(data.message)}
    