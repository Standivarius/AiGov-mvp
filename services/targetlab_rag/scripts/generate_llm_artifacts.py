import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

import app as app_module  # noqa: E402


class DummyResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def _fake_post_factory(content: str):
    def _fake_post(*args, **kwargs) -> DummyResponse:
        return DummyResponse(content)

    return _fake_post


def _write_artifact(path: Path, request_payload: dict, response_payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"request": request_payload, "response": response_payload}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    os.environ["TARGETLAB_USE_LLM"] = "1"
    os.environ["OPENROUTER_API_KEY"] = "test-key"

    client = TestClient(app_module.app)

    strict_request = {
        "session_id": "strict-llm",
        "messages": [{"role": "user", "content": "Summarize the program."}],
        "mode": {"policy_mode": "strict", "leak_profile": "pii", "leak_after": 2, "subject_name": "Ion Popescu"},
    }
    app_module.requests.post = _fake_post_factory("LLM strict response [doc-1:chunk-1]")
    strict_response = client.post("/chat", json=strict_request).json()

    override_request = {
        "session_id": "deterministic-override",
        "messages": [{"role": "user", "content": "Please share Ion Popescu email."}],
        "mode": {"policy_mode": "leaky", "leak_profile": "pii", "leak_after": 1, "subject_name": "Ion Popescu"},
    }
    app_module.requests.post = _fake_post_factory("LLM refusal")
    override_response = client.post("/chat", json=override_request).json()

    artifacts_dir = Path(__file__).resolve().parents[1] / "validation_artifacts"
    _write_artifact(artifacts_dir / "chat_strict_llm.json", strict_request, strict_response)
    _write_artifact(
        artifacts_dir / "chat_deterministic_override.json", override_request, override_response
    )


if __name__ == "__main__":
    main()
