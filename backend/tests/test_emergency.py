from fastapi.testclient import TestClient
from app.main import app
from app.services.emergency import GUIDE

client = TestClient(app)

def get_steps(shared, language="en"):
    response = client.post("/emergency", json={"shared": shared, "language": language})
    assert response.status_code == 200
    return response.json()["steps"]

def test_general_steps_when_nothing_selected():
    steps = get_steps([])
    assert steps[0] == GUIDE["steps"]["stay_calm"]["en"]
    assert len(steps) == 5

def test_money_comes_before_password():
    steps = get_steps(["password", "money"])
    contact = steps.index(GUIDE["steps"]["contact_provider"]["en"])
    change = steps.index(GUIDE["steps"]["change_password"]["en"])
    assert contact < change

def test_no_duplicate_steps():
    steps = get_steps(["otp", "money", "card"])
    assert len(steps) == len(set(steps))

def test_rejects_unknown_situation():
    response = client.post("/emergency", json={"shared": ["hacked_by_aliens"]})
    assert response.status_code == 422

def test_all_steps_have_both_languages():
    for step in GUIDE["steps"].values():
        assert step["en"] and step["ne"]

def test_every_planned_step_exists():
    for key, step_ids in GUIDE["plan"].items():
        if key != "priority":
            for step_id in step_ids:
                assert step_id in GUIDE["steps"]