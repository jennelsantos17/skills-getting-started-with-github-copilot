import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Backup and restore the in-memory activities dict for test isolation"""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities(client):
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow(client):
    email = "tester@example.com"

    # Sign up
    res = client.post("/activities/Chess Club/signup", params={"email": email})
    assert res.status_code == 200
    assert "Signed up" in res.json().get("message", "")

    # Participant should now be present
    res = client.get("/activities")
    assert email in res.json()["Chess Club"]["participants"]

    # Duplicate signup returns 400
    res = client.post("/activities/Chess Club/signup", params={"email": email})
    assert res.status_code == 400

    # Unregister the participant
    res = client.delete("/activities/Chess Club/unregister", params={"email": email})
    assert res.status_code == 200

    # Participant should be removed
    res = client.get("/activities")
    assert email not in res.json()["Chess Club"]["participants"]

    # Unregistering someone not signed up returns 404
    res = client.delete("/activities/Chess Club/unregister", params={"email": "noone@example.com"})
    assert res.status_code == 404


def test_nonexistent_activity(client):
    email = "someone@example.com"

    # Signup to non-existent activity
    res = client.post("/activities/NoSuchActivity/signup", params={"email": email})
    assert res.status_code == 404

    # Unregister from non-existent activity
    res = client.delete("/activities/NoSuchActivity/unregister", params={"email": email})
    assert res.status_code == 404
