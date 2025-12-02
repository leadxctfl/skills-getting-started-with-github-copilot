"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    yield
    # Cleanup after test
    activities.clear()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_has_correct_structure(self, client):
        """Test that activities have the correct data structure"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_participants_count(self, client):
        """Test that participant counts are correct"""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Gym Class"]["participants"]) == 2


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alice@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alice@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_email(self, client):
        """Test that duplicate signup is rejected"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_activity_full(self, client):
        """Test signup when activity is at max capacity"""
        # Fill up Gym Class (max 3 participants for testing)
        activities["Gym Class"]["max_participants"] = 2
        
        response = client.post(
            "/activities/Gym%20Class/signup?email=new@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()
    
    def test_signup_email_normalization(self, client):
        """Test that emails are normalized (lowercased)"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=ALICE@MERGINGTON.EDU"
        )
        assert response.status_code == 200
        
        # Verify email is stored in lowercase
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Chess Club"]["participants"]
        assert "alice@mergington.edu" in participants


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/signup/{email} endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/signup/michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant who isn't signed up"""
        response = client.delete(
            "/activities/Chess%20Club/signup/notreal@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/signup/someone@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_email_normalization(self, client):
        """Test that unregister also normalizes emails"""
        response = client.delete(
            "/activities/Chess%20Club/signup/MICHAEL@MERGINGTON.EDU"
        )
        assert response.status_code == 200
        
        # Verify participant was actually removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests for combined operations"""
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering from an activity"""
        # Sign up
        signup_response = client.post(
            "/activities/Programming%20Class/signup?email=bob@mergington.edu"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "bob@mergington.edu" in activities_data["Programming Class"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            "/activities/Programming%20Class/signup/bob@mergington.edu"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "bob@mergington.edu" not in activities_data["Programming Class"]["participants"]
    
    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple participants signing up and unregistering"""
        # Add multiple participants
        for i in range(3):
            client.post(
                f"/activities/Chess%20Club/signup?email=user{i}@mergington.edu"
            )
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        chess_club_participants = activities_data["Chess Club"]["participants"]
        assert len(chess_club_participants) == 5  # 2 original + 3 new
        
        # Remove one
        client.delete(
            "/activities/Chess%20Club/signup/user0@mergington.edu"
        )
        
        # Verify count decreased
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        chess_club_participants = activities_data["Chess Club"]["participants"]
        assert len(chess_club_participants) == 4
