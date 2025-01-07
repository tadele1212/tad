import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..models import ServiceInput, NearestStopInput

client = TestClient(app)

def test_show_stop():
    response = client.post(
        "/api/show_stop",
        json={"service_no": "163-1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "stops" in data
    assert isinstance(data["stops"], list)

def test_nearest_stop():
    response = client.post(
        "/api/nearest_stop",
        json={
            "service_no": "163-1",
            "gx": 1.3521,
            "gy": 103.8198,
            "last_stop": 0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "sequence" in data
    assert "road_name" in data
    assert "km" in data 