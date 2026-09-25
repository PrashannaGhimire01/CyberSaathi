import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

CASES = [
    ("Your eSewa OTP is 482913. Do not share this code with anyone.", "LOW"),
    ("Badhai cha! Tapai lottery ma Rs 50000 jitnubhayo. OTP pathaunuhos.", "HIGH"),
    ("Tapai ko account block hunecha. Turuntai verify garnuhos: http://esewa-verify.xyz", "HIGH"),
    ("Badhai cha! Lottery jitnubhayo. OTP pathaunuhos. Do not share with anyone.", "HIGH"),
    ("I am going shopping, see you at 5", "LOW"),
    ("Naya offer! Visit https://esewa.com.np", "LOW"),
]

@pytest.mark.parametrize("message, expected", CASES)
def test_risk_level(message, expected):
    response = client.post("/analyze/message", json={"message": message})
    assert response.status_code == 200
    assert response.json()["risk"] == expected

def test_rejects_wrong_field():
    response = client.post("/analyze/message", json={"text": "hello"})
    assert response.status_code == 422

def test_rejects_empty_message():
    response = client.post("/analyze/message", json={"message": ""})
    assert response.status_code == 422

def test_rejects_huge_message():
    response = client.post("/analyze/message", json={"message": "a" * 5001})
    assert response.status_code == 422