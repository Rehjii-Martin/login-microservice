from fastapi.testclient import TestClient
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app
from models import init_db, seed_demo_user

init_db()
seed_demo_user()

client = TestClient(app)

def test_login_refresh_logout_flow():
    # login
    r = client.post("/auth/login", json={"user_name":"M.Koike", "password":"pass0000"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data and "refresh_token" in data
    refresh = data["refresh_token"]

    # refresh
    r2 = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert "access_token" in r2.json()

    # logout
    r3 = client.post("/auth/logout", json={"refresh_token": refresh})
    assert r3.status_code == 200
    assert r3.json()["message"] == "successfully logout"

    # refresh again should fail (revoked)
    r4 = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r4.status_code == 401
    assert r4.json()["error"] == "Invalid user"

def test_invalid_login():
    r = client.post("/auth/login", json={"user_name":"nope", "password":"bad"})
    assert r.status_code == 401
    assert r.json()["error"] == "Invalid user"
