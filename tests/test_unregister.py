"""
Tests for the unregister endpoint: POST /activities/{activity_name}/unregister
"""

import pytest


class TestUnregisterSuccess:
    """Tests for successful unregister scenarios"""

    def test_unregister_existing_participant(self, client, get_activities):
        """Test successfully unregistering an existing participant"""
        activities = get_activities()
        activity_name = "Chess Club"
        participant = activities[activity_name]["participants"][0]
        initial_count = len(activities[activity_name]["participants"])
        
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={participant}"
        )
        assert response.status_code == 200
        assert participant in response.json()["message"]
        
        # Verify participant was removed
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert participant not in activities[activity_name]["participants"]

    def test_unregister_returns_success_message(self, client, get_activities):
        """Test that unregister returns proper success message format"""
        activities = get_activities()
        participant = activities["Programming Class"]["participants"][0]
        
        response = client.post(
            f"/activities/Programming%20Class/unregister?email={participant}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]


class TestUnregisterValidation:
    """Tests for unregister validation and error cases"""

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister fails when activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self, client):
        """Test unregister fails when participant is not signed up"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notsignedup@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_already_unregistered(self, client, get_activities):
        """Test attempting to unregister the same email twice"""
        # First, get a participant and unregister them
        activities = get_activities()
        participant = activities["Gym Class"]["participants"][0]
        
        # First unregister should succeed
        response1 = client.post(
            f"/activities/Gym%20Class/unregister?email={participant}"
        )
        assert response1.status_code == 200
        
        # Second unregister attempt should fail
        response2 = client.post(
            f"/activities/Gym%20Class/unregister?email={participant}"
        )
        assert response2.status_code == 400
        assert "not signed up" in response2.json()["detail"].lower()


class TestUnregisterEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_unregister_case_sensitive_activity_name(self, client):
        """Test that activity names are case-sensitive"""
        response = client.post(
            "/activities/chess%20club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_then_signup_same_email(self, client, get_activities):
        """Test that unregistered email can sign up again"""
        activities = get_activities()
        activity_name = "Drama Club"
        participant = activities[activity_name]["participants"][0]
        
        # Unregister
        response1 = client.post(
            f"/activities/Drama%20Club/unregister?email={participant}"
        )
        assert response1.status_code == 200
        
        # Sign up again
        response2 = client.post(
            f"/activities/Drama%20Club/signup?email={participant}"
        )
        assert response2.status_code == 200
        
        # Verify back in participants list
        assert participant in activities[activity_name]["participants"]

    def test_unregister_from_one_activity_leaves_others_intact(self, client, get_activities):
        """Test that unregistering from one activity doesn't affect other activities"""
        email = "multi_activity_test@mergington.edu"
        
        # Sign up for multiple activities
        client.post("/activities/Chess%20Club/signup?email=" + email)
        client.post("/activities/Programming%20Class/signup?email=" + email)
        
        activities = get_activities()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]
        
        # Unregister from one
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify removed from one, still in other
        assert email not in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_unregister_with_special_characters_in_email(self, client, get_activities):
        """Test unregister with email containing valid special characters"""
        email = "student.name+test@mergington.edu"
        activity = "Art%20Studio"
        
        # Sign up first
        response_signup = client.post(f"/activities/{activity}/signup?email={email}")
        assert response_signup.status_code == 200
        
        # Then unregister
        response_unregister = client.post(
            f"/activities/Art%20Studio/unregister?email={email}"
        )
        assert response_unregister.status_code == 200
        
        # Verify removed
        activities = get_activities()
        assert email not in activities["Art Studio"]["participants"]

    def test_unregister_only_removes_one_instance(self, client, get_activities):
        """
        Test that unregister only removes one instance if somehow duplicated.
        (Documents behavior if duplicate entries were to exist)
        """
        activities = get_activities()
        activity_name = "Science Club"
        
        # Manually add duplicate (simulating edge case)
        email = "duplicate_instance@mergington.edu"
        activities[activity_name]["participants"].append(email)
        activities[activity_name]["participants"].append(email)
        
        initial_count = len(activities[activity_name]["participants"])
        
        # Unregister
        response = client.post(
            f"/activities/Science%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Should remove only one instance
        assert len(activities[activity_name]["participants"]) == initial_count - 1


class TestUnregisterIntegration:
    """Integration tests combining signup and unregister"""

    def test_signup_unregister_cycle(self, client, get_activities):
        """Test complete signup -> unregister -> signup cycle"""
        email = "cycle_test@mergington.edu"
        activity = "Debate%20Team"
        
        activities = get_activities()
        initial_count = len(activities["Debate Team"]["participants"])
        
        # Signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        assert len(activities["Debate Team"]["participants"]) == initial_count + 1
        
        # Unregister
        response2 = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        assert len(activities["Debate Team"]["participants"]) == initial_count
        
        # Signup again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200
        assert len(activities["Debate Team"]["participants"]) == initial_count + 1
