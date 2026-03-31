from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.assistant import main
from api.authentification.auth import User
from memory import memory


class StubChain:
    def __init__(self, result):
        self.result = result

    def invoke(self, payload):
        return self.result


class StubChatAgent:
    def __init__(self):
        self.calls = []

    def invoke(self, payload, config=None):
        self.calls.append((payload, config))
        user_text = payload["messages"][-1]["content"]
        thread_id = config["configurable"]["thread_id"]
        return {
            "messages": [SimpleNamespace(content=f"Réponse à {thread_id}: {user_text}")]
        }


def setup_function():
    memory.clear_history()
    main.app.dependency_overrides.clear()


def _client_for(username="alice"):
    main.app.dependency_overrides[main.get_current_user] = lambda: User(
        username=username
    )
    return TestClient(main.app)


def _set_user(username):
    main.app.dependency_overrides[main.get_current_user] = lambda: User(
        username=username
    )


def test_analyze_endpoint_returns_structured_output(monkeypatch):
    client = _client_for()
    monkeypatch.setattr(
        main,
        "get_analysis_chain",
        lambda: StubChain(
            SimpleNamespace(
                model_dump=lambda: {"is_optimal": True, "issues": [], "suggestions": []}
            )
        ),
    )

    response = client.post("/analyze", json={"code": "def add(a, b): return a + b"})
    assert response.status_code == 200
    assert response.json() == {"is_optimal": True, "issues": [], "suggestions": []}


def test_full_pipeline_stops_when_analysis_is_not_optimal(monkeypatch):
    client = _client_for()
    analysis_result = SimpleNamespace(
        is_optimal=False,
        issues=["Pas de docstring"],
        suggestions=["Ajouter une docstring"],
        model_dump=lambda: {
            "is_optimal": False,
            "issues": ["Pas de docstring"],
            "suggestions": ["Ajouter une docstring"],
        },
    )
    monkeypatch.setattr(main, "get_analysis_chain", lambda: StubChain(analysis_result))

    response = client.post(
        "/full_pipeline", json={"code": "def add(a, b): return a + b"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["error"] == "Code non optimal"
    assert body["analysis"]["is_optimal"] is False


def test_full_pipeline_continues_when_code_is_optimal(monkeypatch):
    client = _client_for()
    monkeypatch.setattr(
        main,
        "get_analysis_chain",
        lambda: StubChain(
            SimpleNamespace(
                is_optimal=True,
                issues=[],
                suggestions=[],
                model_dump=lambda: {
                    "is_optimal": True,
                    "issues": [],
                    "suggestions": [],
                },
            )
        ),
    )
    monkeypatch.setattr(
        main,
        "get_test_chain",
        lambda: StubChain(
            SimpleNamespace(
                unit_test="def test_add(): assert add(1, 2) == 3",
                model_dump=lambda: {
                    "unit_test": "def test_add(): assert add(1, 2) == 3"
                },
            )
        ),
    )
    monkeypatch.setattr(
        main,
        "get_explain_test_chain",
        lambda: StubChain(
            SimpleNamespace(
                explanation="Ce test vérifie l'addition.",
                model_dump=lambda: {"explanation": "Ce test vérifie l'addition."},
            )
        ),
    )

    response = client.post(
        "/full_pipeline", json={"code": "def add(a, b): return a + b"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["is_optimal"] is True
    assert "unit_test" in body["test"]
    assert "explanation" in body["explanation"]


def test_chat_and_history_are_scoped_by_user(monkeypatch):
    stub_agent = StubChatAgent()
    monkeypatch.setattr(main, "get_chat_agent", lambda: stub_agent)

    client = TestClient(main.app)

    _set_user("alice")
    alice_chat = client.post("/chat", json={"input": "Bonjour, je m'appelle Alice."})
    assert alice_chat.status_code == 200
    assert "alice" in alice_chat.json()["response"]

    _set_user("bob")
    bob_chat = client.post("/chat", json={"input": "Bonjour, je m'appelle Bob."})
    assert bob_chat.status_code == 200
    assert "bob" in bob_chat.json()["response"]

    _set_user("alice")
    alice_history = client.get("/history")
    _set_user("bob")
    bob_history = client.get("/history")

    assert len(alice_history.json()["history"]) == 2
    assert len(bob_history.json()["history"]) == 2
    assert (
        alice_history.json()["history"][0]["content"] == "Bonjour, je m'appelle Alice."
    )
    assert bob_history.json()["history"][0]["content"] == "Bonjour, je m'appelle Bob."
