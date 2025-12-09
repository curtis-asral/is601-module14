import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# User Endpoints


def test_register_user():
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "Password1",
    }
    r = client.post("/users/register", json=data)
    assert r.status_code == 200
    assert r.json()["username"] == "testuser"


def test_login_user():
    data = {"username": "testuser", "password": "Password1"}
    r = client.post("/users/login", json=data)
    assert r.status_code == 200
    assert "access_token" in r.json()


# Calculation Endpoints


def test_add_calculation():
    user_data = {
        "first_name": "Calc",
        "last_name": "User",
        "email": "calcuser@example.com",
        "username": "calcuser",
        "password": "Password1",
    }
    user_resp = client.post("/users/register", json=user_data)
    user_id = user_resp.json()["id"]
    calc_data = {"type": "addition", "inputs": [1, 2, 3], "user_id": user_id}
    r = client.post("/calculations", json=calc_data)
    assert r.status_code == 200
    assert r.json()["result"] == 6


def test_browse_calculations():
    r = client.get("/calculations")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_read_calculation():
    r = client.get("/calculations/1")
    assert r.status_code == 200
    assert "result" in r.json()


def test_delete_calculation():
    r = client.delete("/calculations/1")
    assert r.status_code == 200
    assert r.json()["ok"] is True
