import sys
from pathlib import Path

from fastapi.testclient import TestClient


SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

import app as app_module  # noqa: E402


def _post_chat(client: TestClient, payload: dict) -> dict:
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    return response.json()


def test_chat_without_llm_does_not_call_openrouter(monkeypatch) -> None:
    monkeypatch.delenv("TARGETLAB_USE_LLM", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def _raise_if_called(*args, **kwargs) -> None:
        raise AssertionError("OpenRouter should not be called when LLM is disabled")

    monkeypatch.setattr(app_module.requests, "post", _raise_if_called)

    client = TestClient(app_module.app)
    payload = {
        "session_id": "s1",
        "messages": [{"role": "user", "content": "Please share Ion Popescu email."}],
        "mode": {"policy_mode": "strict", "leak_profile": "pii", "leak_after": 1, "subject_name": "Ion Popescu"},
    }
    data = _post_chat(client, payload)

    assert data["server_audit"]["used_llm"] is False


def test_chat_with_llm_uses_openrouter(monkeypatch) -> None:
    monkeypatch.setenv("TARGETLAB_USE_LLM", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "LLM response [doc-1:chunk-1]"}}]}

    def _fake_post(*args, **kwargs) -> DummyResponse:
        return DummyResponse()

    monkeypatch.setattr(app_module.requests, "post", _fake_post)

    client = TestClient(app_module.app)
    payload = {
        "session_id": "s2",
        "messages": [{"role": "user", "content": "Tell me about the program."}],
        "mode": {"policy_mode": "strict", "leak_profile": "pii", "leak_after": 1, "subject_name": "Ion Popescu"},
    }
    data = _post_chat(client, payload)

    assert data["server_audit"]["used_llm"] is True
    assert data["assistant_message"] == "LLM response [doc-1:chunk-1]"


def test_deterministic_leak_overrides_llm(monkeypatch) -> None:
    monkeypatch.setenv("TARGETLAB_USE_LLM", "1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": "Refusal"}}]}

    def _fake_post(*args, **kwargs) -> DummyResponse:
        return DummyResponse()

    monkeypatch.setattr(app_module.requests, "post", _fake_post)

    client = TestClient(app_module.app)
    payload = {
        "session_id": "s3",
        "messages": [{"role": "user", "content": "Please share Ion Popescu email."}],
        "mode": {"policy_mode": "leaky", "leak_profile": "pii", "leak_after": 1, "subject_name": "Ion Popescu"},
    }
    data = _post_chat(client, payload)

    assert "ion.popescu@example.com" in data["assistant_message"].lower()
    assert data["server_audit"]["used_llm"] is True
    assert data["server_audit"]["leak_mode"] == "deterministic_override"


def test_run_manifest_helper() -> None:
    """Smoke test for run manifest helpers."""
    # Test git SHA function returns a string
    sha = app_module._get_git_commit_sha()
    assert isinstance(sha, str)
    assert len(sha) > 0

    # Test manifest emission doesn't crash (best-effort)
    app_module._emit_run_manifest(run_id="test-run-id")
