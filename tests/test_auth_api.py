from fastapi.testclient import TestClient

from api.authentification.auth import app, fake_users_db


client = TestClient(app)


def setup_function():
    fake_users_db.clear()


def test_signup_login_and_me_flow():
    signup = client.post("/signup", json={"username": "alice", "password": "secret"})
    assert signup.status_code == 200
    assert signup.json() == {"username": "alice"}

    login = client.post("/login", json={"username": "alice", "password": "secret"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json() == {"username": "alice"}


def test_signup_rejects_duplicate_username():
    client.post("/signup", json={"username": "alice", "password": "secret"})
    duplicate = client.post("/signup", json={"username": "alice", "password": "secret"})
    assert duplicate.status_code == 400
