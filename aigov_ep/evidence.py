"""Evidence pack builder."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List


LIMITATIONS = [
    "Heuristic detection only; results may include false positives or miss context.",
    "Transcript-only evaluation; no backend controls or logs are assessed.",
]


def build_evidence_pack(
    scenario: Dict[str, Any],
    transcript: List[Dict[str, Any]],
    scores: List[Dict[str, Any]],
    runner_config: Dict[str, Any],
    mock_audit: Any = None,
    http_audit: Any = None,
    http_raw_response: Any = None,
) -> Dict[str, Any]:
    return {
        "generated_at": _utc_now(),
        "scenario": {
            "scenario_id": scenario.get("scenario_id"),
            "title": scenario.get("title"),
            "category": scenario.get("category"),
            "framework": scenario.get("framework"),
            "role": scenario.get("role"),
            "failure_criteria": scenario.get("failure_criteria"),
            "source_path": scenario.get("source_path"),
        },
        "transcript": transcript,
        "scores": scores,
        "runner_config": runner_config,
        "mock_audit": mock_audit,
        "http_audit": http_audit,
        "http_raw_response": http_raw_response,
        "limitations": LIMITATIONS,
    }


def write_evidence_pack(path: str, evidence_pack: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(evidence_pack, handle, indent=2, sort_keys=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
