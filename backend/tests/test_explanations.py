from fastapi.testclient import TestClient
from app.main import app
from app.services.message_analyzer import RULES as MESSAGE_RULES
from app.services.url_analyzer import RULES as URL_RULES

client = TestClient(app)

def test_nepali_explanation():
    response = client.post("/analyze/message", json={
        "message": "Badhai cha! Lottery jitnubhayo. OTP pathaunuhos.", "language": "ne"})
    body = response.json()
    assert body["risk"] == "HIGH"
    assert "ठगी" in body["explanation"]["headline"]
    assert len(body["explanation"]["actions"]) > 0

def test_rejects_unknown_language():
    response = client.post("/analyze/message", json={"message": "hello", "language": "fr"})
    assert response.status_code == 422

def test_all_rules_have_both_languages():
    message_rules = list(MESSAGE_RULES["categories"].values()) + [MESSAGE_RULES["link"]]
    url_rules = [rule for name, rule in URL_RULES.items() if name != "version"]
    for rule in message_rules + url_rules:
        assert rule["reason_en"] and rule["reason_ne"]

def test_web_page_is_served():
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "CyberSaathi" in response.text