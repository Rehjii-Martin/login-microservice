# tests/test_auth.py
from fastapi.testclient import TestClient
import os, sys, json

# Make app importable when running pytest from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app
from models import init_db, seed_demo_user 

# --- pytest setup ---
init_db()
seed_demo_user()
client = TestClient(app)

def test_login_refresh_logout_flow():
    # login
    r = client.post("/auth/login", json={"user_name": "M.Koike", "password": "pass0000"})
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
    r = client.post("/auth/login", json={"user_name": "nope", "password": "bad"})
    assert r.status_code == 401
    assert r.json()["error"] == "Invalid user"


# --- standalone demo client ---

def _pretty(title, obj):
    print(f"\n=== {title} ===")
    print(json.dumps(obj, indent=2))

def _must_ok(resp):
    try:
        data = resp.json()
    except Exception:
        print("Non-JSON response:", resp.text)
        raise SystemExit(1)
    if not resp.ok:
        print(f"HTTP {resp.status_code}")
        _pretty("Error", data)
        raise SystemExit(1)
    return data

def demo_run():
    import requests 

    base = os.environ.get("AUTH_BASE_URL", "http://127.0.0.1:8000")
    headers = {"Content-Type": "application/json"}

    # 1) LOGIN
    r = requests.post(f"{base}/auth/login",
                      json={"user_name": "M.Koike", "password": "pass0000"},
                      headers=headers, timeout=5)
    data = _must_ok(r)
    _pretty("Login response", data)
    refresh = data["refresh_token"]

    # 2) REFRESH
    r2 = requests.post(f"{base}/auth/refresh",
                       json={"refresh_token": refresh},
                       headers=headers, timeout=5)
    data2 = _must_ok(r2)
    _pretty("Refresh response", data2)

    # 3) LOGOUT
    r3 = requests.post(f"{base}/auth/logout",
                       json={"refresh_token": refresh},
                       headers=headers, timeout=5)
    data3 = _must_ok(r3)
    _pretty("Logout response", data3)

    # 4) NEGATIVE CHECK (should be 401)
    r4 = requests.post(f"{base}/auth/refresh",
                       json={"refresh_token": refresh},
                       headers=headers, timeout=5)
    print("\n=== Refresh again after logout (expected 401) ===")
    print("HTTP", r4.status_code)
    try:
        print(json.dumps(r4.json(), indent=2))
    except Exception:
        print(r4.text)

if __name__ == "__main__":
    # Demo mode prints JSON from a live uvicorn server.
    demo_run()
