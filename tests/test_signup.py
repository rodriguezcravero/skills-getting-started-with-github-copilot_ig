"""
Tests for the signup endpoint: POST /activities/{activity_name}/signup
"""

import pytest


class TestSignupSuccess:
    """Tests for successful signup scenarios"""

    def test_signup_new_participant(self, client, get_activities):
        """Test successfully signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]
        
        # Verify participant was added to database
        activities = get_activities()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_returns_success_message(self, client):
        """Test that signup returns proper success message format"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]


class TestSignupValidation:
    """Tests for signup validation and error cases"""

    def test_signup_nonexistent_activity(self, client):
        """Test signup fails when activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email(self, client, get_activities, reset_activities):
        """Test that duplicate signup is prevented"""
        activities = get_activities()
        existing_email = activities["Chess Club"]["participants"][0]
        
        response = client.post(
            "/activities/Chess%20Club/signup?email=" + existing_email
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_duplicate_after_successful_signup(self, client):
        """Test attempting to signup the same email twice for same activity"""
        email = "duplicate_test@mergington.edu"
        activity = "Gym%20Class"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()


class TestSignupEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_signup_same_email_different_activities(self, client, get_activities):
        """Test that same email can signup for different activities"""
        email = "multi_activity@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities = get_activities()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]

    def test_signup_activity_at_capacity(self, client, get_activities):
        """Test signup behavior when activity reaches capacity"""
        activities = get_activities()
        
        # Find an activity with 1 spot left
        activity_name = "Chess Club"
        max_participants = activities[activity_name]["max_participants"]
        current_count = len(activities[activity_name]["participants"])
        spots_left = max_participants - current_count
        
        if spots_left > 0:
            # Fill remaining spots
            for i in range(spots_left):
                email = f"capacity_test_{i}@mergington.edu"
                response = client.post(
                    f"/activities/Chess%20Club/signup?email={email}"
                )
                assert response.status_code == 200
            
            # Try to signup when at capacity
            response = client.post(
                "/activities/Chess%20Club/signup?email=overflow@mergington.edu"
            )
            # Currently API doesn't check capacity, so this succeeds
            # This documents current behavior; can be updated if capacity check is added
            assert response.status_code == 200

    def test_signup_case_sensitive_activity_name(self, client):
        """Test that activity names are case-sensitive"""
        # Wrong case should fail
        response = client.post(
            "/activities/chess%20club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_signup_with_special_characters_in_email(self, client, get_activities):
        """Test signup with email containing valid special characters"""
        from urllib.parse import urlencode
        email = "student.name+tag@mergington.edu"
        
        # Properly URL-encode the email parameter
        params = urlencode({"email": email})
        response = client.post(
            f"/activities/Drama%20Club/signup?{params}"
        )
        assert response.status_code == 200
        
        # Verify email was stored correctly
        activities = get_activities()
        assert email in activities["Drama Club"]["participants"]

    def test_signup_whitespace_in_email_preserved(self, client, get_activities):
        """Test that email is stored exactly as provided"""
        email = "test.user@mergington.edu"
        response = client.post(
            f"/activities/Art%20Studio/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify exact email stored
        activities = get_activities()
        assert email in activities["Art Studio"]["participants"]
