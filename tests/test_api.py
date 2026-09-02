import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_create_and_get_task():
    payload = {
        "user_request": "Analyze the impact of AI on medicine.",
        "provider": "mock"
    }

    res = client.post("/api/tasks", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "task_id" in data
    assert data["status"] == "completed"
    assert data["final_output"] != ""

    task_id = data["task_id"]
    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["task_id"] == task_id
