from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


INITIAL_ACTIVITIES = deepcopy(activities)


def restore_activities():
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client():
    restore_activities()
    with TestClient(app) as test_client:
        yield test_client
    restore_activities()


def test_root_redirects_to_static_index(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_activities = response.json()
    assert response_activities["Chess Club"]["description"] == (
        "Learn strategies and compete in chess tournaments"
    )
    assert response_activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_student_to_activity(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email=student@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_returns_400_for_duplicate_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_returns_400_for_full_activity(client):
    # Arrange
    activity_name = "Basketball Team"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student{number}@mergington.edu"
        for number in range(activity["max_participants"])
    ]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email=new@mergington.edu"
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Basketball Team"

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_student_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup?email=student@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_for_unregistered_student(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup?email=student@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}


def test_unregister_requires_email(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422