import pytest
import json
import time
import threading
from app.api import app, latest_data, system_status

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_status_structure(client):
    """Verify that /api/status returns the correct JSON structure."""
    response = client.get('/api/status')
    assert response.status_code == 200
    
    data = response.get_json()
    assert "status" in data
    assert "sensors" in data
    assert isinstance(data["sensors"], dict)

def test_api_status_data(client):
    """Verify that the API returns data consistent with the internal state."""
    # Seed some data
    system_status = "ALARM"
    latest_data["Temperature"] = {
        "value": 25.5,
        "timestamp": "2026-01-01T12:00:00",
        "status": "OK",
        "alarm": None
    }
    
    # We need to ensure the shared state in api.py is updated.
    # Note: In a real test we might want to mock the 'api' module if state is global.
    from app import api
    api.system_status = "ALARM"
    api.latest_data["Temperature"] = latest_data["Temperature"]

    response = client.get('/api/status')
    data = response.get_json()
    
    assert data["status"] == "ALARM"
    assert data["sensors"]["Temperature"]["value"] == 25.5
    assert data["sensors"]["Temperature"]["status"] == "OK"
