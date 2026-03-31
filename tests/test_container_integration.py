import os

import pytest
import requests


RUN_CONTAINER_TESTS = os.getenv("RUN_CONTAINER_TESTS") == "true"
AUTH_URL = os.getenv("AUTH_URL", "http://auth:8001")
API_URL = os.getenv("API_URL", "http://main:8000")


pytestmark = pytest.mark.skipif(
    not RUN_CONTAINER_TESTS,
    reason="Ces tests sont destinés au conteneur de test Docker.",
)


def _signup_and_login(username: str):
    requests.post(
        f"{AUTH_URL}/signup",
        json={"username": username, "password": "secret"},
        timeout=30,
    )
    response = requests.post(
        f"{AUTH_URL}/login",
        json={"username": username, "password": "secret"},
        timeout=30,
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_container_auth_and_history_flow():
    headers = _signup_and_login("docker_alice")
    history = requests.get(f"{API_URL}/history", headers=headers, timeout=30)
    history.raise_for_status()
    assert history.json() == {"history": []}


def test_container_analyze_returns_expected_shape():
    headers = _signup_and_login("docker_analyze")
    response = requests.post(
        f"{API_URL}/analyze",
        headers=headers,
        json={"code": "def add(a, b):\n    return a + b"},
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    assert set(body.keys()) == {"is_optimal", "issues", "suggestions"}
    assert isinstance(body["is_optimal"], bool)
    assert isinstance(body["issues"], list)
    assert isinstance(body["suggestions"], list)


def test_container_chat_and_history():
    headers = _signup_and_login("docker_chat")
    chat = requests.post(
        f"{API_URL}/chat",
        headers=headers,
        json={"input": "Bonjour depuis Docker"},
        timeout=60,
    )
    chat.raise_for_status()
    body = chat.json()
    assert isinstance(body["response"], str)
    assert body["response"].strip() != ""

    history = requests.get(f"{API_URL}/history", headers=headers, timeout=30)
    history.raise_for_status()
    payload = history.json()["history"]
    assert len(payload) >= 2
    assert payload[0]["content"] == "Bonjour depuis Docker"
