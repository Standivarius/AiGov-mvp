"""Scenario loader for YAML/JSON scenario cards."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None


class ScenarioLoadError(RuntimeError):
    pass


def _normalize_turns(raw_turns: List[Any]) -> List[Dict[str, str]]:
    turns: List[Dict[str, str]] = []
    for item in raw_turns:
        if isinstance(item, str):
            turns.append({"role": "user", "content": item})
            continue
        if isinstance(item, dict):
            content = item.get("content") or item.get("text")
            role = item.get("role", "user")
            if not content:
                raise ScenarioLoadError("Turn is missing content")
            turns.append({"role": role, "content": content})
            continue
        raise ScenarioLoadError("Turn must be a string or object")
    return turns


def load_scenario(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise ScenarioLoadError(f"Scenario file not found: {path}")

    _, ext = os.path.splitext(path)
    ext = ext.lower()

    with open(path, "r", encoding="utf-8") as handle:
        if ext in (".yaml", ".yml"):
            if yaml is None:
                raise ScenarioLoadError("PyYAML is required for YAML scenarios")
            data = yaml.safe_load(handle)
        elif ext == ".json":
            data = json.load(handle)
        else:
            raise ScenarioLoadError(f"Unsupported scenario format: {ext}")

    if not isinstance(data, dict):
        raise ScenarioLoadError("Scenario root must be an object")

    raw_turns = data.get("turns") or data.get("dialogue") or data.get("messages")
    if not raw_turns:
        raise ScenarioLoadError("Scenario must include turns")

    data["turns"] = _normalize_turns(raw_turns)
    return data
