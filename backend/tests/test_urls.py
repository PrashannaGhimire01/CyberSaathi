import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

URL_CASES = [
    ("https://www.esewa.com.np", "LOW"),
    ("https://evil-esewa.com.np", "HIGH"),
    ("https://esewa.com.np.login-check.xyz", "HIGH"),
    ("http://esewa.com.np@login-check.xyz", "HIGH"),
    ("https://bit.ly/3xYz", "LOW"),
    ("http://[broken", "MEDIUM"),
    ("Naya offer! Visit https://esewa.com.np", "LOW"),
]

@pytest.mark.parametrize("url, expected", URL_CASES)
def test_url_risk(url, expected):
    response = client.post("/analyze/url", json={"url": url})
    assert response.status_code == 200
    assert response.json()["risk"] == expected