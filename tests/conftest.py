"""
Pytest configuration and shared fixtures for API tests
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a TestClient for making requests to the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture to reset activities to a known state.
    This can be called within tests if needed to reset state.
    Note: By default, tests run with persistent state between them.
    """
    # Store original state
    original_state = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, activity in activities.items():
        activity["participants"] = original_state[name]["participants"].copy()


@pytest.fixture
def get_activities():
    """Fixture to access the in-memory activities database for assertions"""
    def _get_activities():
        return activities
    return _get_activities
