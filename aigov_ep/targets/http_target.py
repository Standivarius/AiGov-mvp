"""HTTP target adapter for TargetLab RAG service."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List

from .base import TargetAdapter


DEFAULT_BASE_URL = "http://localhost:8000"


class HttpTargetAdapter(TargetAdapter):
    name = "http"

    def __init__(self, scenario: Dict[str, Any], config: Dict[str, Any]) -> None:
        super().__init__(scenario, config)
        self.base_url = str(config.get("base_url") or DEFAULT_BASE_URL).rstrip("/")
        self.chat_path = str(config.get("chat_path") or "/chat")
        self.leak_mode = config.get("leak_mode")
        self.leak_profile = config.get("leak_profile")
        self.use_llm = config.get("use_llm")
        self.session_id = str(config.get("session_id") or config.get("run_id") or "aigov-eval")

    def respond(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "messages": _normalize_messages(messages),
            "session_id": self.session_id,
        }
        if self.leak_mode is not None:
            payload["leak_mode"] = self.leak_mode
        if self.leak_profile is not None:
            payload["leak_profile"] = _map_leak_profile(str(self.leak_profile))
        if self.use_llm is not None:
            payload["use_llm"] = bool(self.use_llm)
        chat_path = self.chat_path if self.chat_path.startswith("/") else f"/{self.chat_path}"
        url = f"{self.base_url}{chat_path}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                status = resp.getcode()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            keys = ",".join(sorted(payload.keys()))
            raise RuntimeError(
                f"HTTP target request failed: {exc.code} {body} "
                f"(endpoint={url}, payload_keys={keys})"
            ) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            snippet = raw[:300]
            raise RuntimeError(
                f"HTTP target response was not valid JSON: {exc.msg} "
                f"(status={status}, body={snippet})"
            ) from exc

        reply = _extract_assistant_text(data, status, raw)
        server_audit = data.get("server_audit")
        return {
            "content": reply,
            "metadata": {
                "http_audit": server_audit,
                "http_raw_response": _truncate(raw, 2000),
            },
        }


def _normalize_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [
        {
            "role": _normalize_role(msg.get("role")),
            "content": msg.get("content", ""),
        }
        for msg in messages
    ]


def _normalize_role(role: Any) -> str:
    if not isinstance(role, str):
        return "user"
    value = role.strip().lower()
    if value in {"user", "assistant", "system"}:
        return value
    if value in {"ai", "bot"}:
        return "assistant"
    return "user"


def _map_leak_profile(value: str) -> str:
    mapping = {
        "pii_basic": "pii",
        "special_category_basic": "special_category",
    }
    return mapping.get(value, value)


def _extract_assistant_text(data: Dict[str, Any], status: int, raw: str) -> str:
    for key in ("reply", "assistant", "assistant_message", "message"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    snippet = raw[:300]
    raise RuntimeError(
        "HTTP target response missing assistant text "
        f"(status={status}, body={snippet})"
    )


def _truncate(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len]
