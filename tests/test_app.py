"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    yield
    # Restore after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "testuser@mergington.edu" in data["message"]
        assert "testuser@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup",
            params={"email": "testuser@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email_fails(self, client, reset_activities):
        """Test that duplicate signup is rejected"""
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_adds_to_participants_list(self, client, reset_activities):
        """Test that signup properly adds email to participants"""
        email = "newstudent@mergington.edu"
        initial_count = len(activities["Programming Class"]["participants"])
        
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        assert len(activities["Programming Class"]["participants"]) == initial_count + 1
        assert email in activities["Programming Class"]["participants"]
    
    def test_signup_multiple_different_emails(self, client, reset_activities):
        """Test that multiple different emails can signup for same activity"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": email1}
        )
        response2 = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": email2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in activities["Tennis Club"]["participants"]
        assert email2 in activities["Tennis Club"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivityData:
    """Tests for activity data structure and validity"""
    
    def test_all_activities_have_valid_structure(self, client, reset_activities):
        """Test that all activities have valid structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert isinstance(activity_name, str)
            assert len(activity_name) > 0
            
            assert isinstance(activity_info["description"], str)
            assert len(activity_info["description"]) > 0
            
            assert isinstance(activity_info["schedule"], str)
            assert len(activity_info["schedule"]) > 0
            
            assert isinstance(activity_info["max_participants"], int)
            assert activity_info["max_participants"] > 0
            
            assert isinstance(activity_info["participants"], list)
            assert len(activity_info["participants"]) <= activity_info["max_participants"]
    
    def test_participants_are_valid_emails(self, client, reset_activities):
        """Test that all participants have valid email format"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            for email in activity_info["participants"]:
                assert isinstance(email, str)
                assert "@" in email
                assert "." in email


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
