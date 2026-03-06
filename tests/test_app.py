import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as original_activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore in-memory activities to their original state after each test."""
    backup = copy.deepcopy(original_activities)
    yield
    original_activities.clear()
    original_activities.update(backup)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_get_activities_contains_expected_fields(client):
    response = client.get("/activities")
    activity = response.json()["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]


def test_signup_adds_participant(client):
    client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    response = client.get("/activities")
    assert "newstudent@mergington.edu" in response.json()["Chess Club"]["participants"]


def test_signup_duplicate_returns_400(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_unknown_activity_returns_404(client):
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]


def test_unregister_removes_participant(client):
    client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    response = client.get("/activities")
    assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]


def test_unregister_not_enrolled_returns_404(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "nobody@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
