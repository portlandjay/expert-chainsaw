"""
Tests for the Mergington High School Activities API
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_valid_activity_and_email(self):
        """Test successful signup for a valid activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds the participant to the activity"""
        # Sign up a new participant
        client.post("/activities/Art%20Studio/signup?email=newstudent@mergington.edu")

        # Verify the participant was added
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Art Studio"]["participants"]

    def test_signup_invalid_activity(self):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email(self):
        """Test that signing up with a duplicate email returns error"""
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""

    def test_unregister_valid_participant(self):
        """Test successful unregistration of a participant"""
        # First, sign up
        client.post("/activities/Drama%20Club/signup?email=unregister_test@mergington.edu")

        # Then unregister
        response = client.post(
            "/activities/Drama%20Club/unregister?email=unregister_test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "unregister_test@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove_me@mergington.edu"
        # Sign up
        client.post(f"/activities/Gym%20Class/signup?email={email}")

        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Gym Class"]["participants"]

        # Unregister
        client.post(f"/activities/Gym%20Class/unregister?email={email}")

        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Gym Class"]["participants"]

    def test_unregister_invalid_activity(self):
        """Test unregister for a non-existent activity"""
        response = client.post(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_participant_not_signed_up(self):
        """Test unregister for a participant who is not signed up"""
        response = client.post(
            "/activities/Basketball%20Team/unregister?email=not_signed_up@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that the root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivityCapacity:
    """Tests related to activity capacity"""

    def test_activity_tracks_correct_spot_count(self):
        """Test that activities report correct remaining spots"""
        response = client.get("/activities")
        activities = response.json()

        chess_club = activities["Chess Club"]
        spots_used = len(chess_club["participants"])
        max_spots = chess_club["max_participants"]
        assert spots_used <= max_spots


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_signup_and_unregister_workflow(self):
        """Test complete signup and unregister workflow"""
        email = "workflow_test@mergington.edu"
        activity = "Swimming Club"

        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200

        # Verify signup
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity]["participants"]

        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200

        # Verify unregister
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities[activity]["participants"]
