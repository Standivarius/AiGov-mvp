"""Minimal transcript-first runner."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..loader import load_scenario
from ..targets import get_target
from ..utils.io import read_json, write_json


@dataclass
class ExecuteResult:
    run_dir: str
    scenario_path: str | None
    transcript_path: str
    run_meta_path: str
    scenario_json_path: str


@dataclass
class RunResult:
    run_id: str
    run_dir: Path
    transcript: List[Dict[str, Any]]
    scores: List[Dict[str, Any]]
    run_meta: Dict[str, Any]


def run_scenario(
    scenario_path: str,
    target_name: str,
    output_root: str,
    config: Dict[str, Any],
) -> RunResult:
    execute_result = execute_scenario(scenario_path, target_name, output_root, config)
    transcript = read_json(Path(execute_result.transcript_path))
    run_meta = read_json(Path(execute_result.run_meta_path))
    run_id = run_meta.get("run_id") or Path(execute_result.run_dir).name

    return RunResult(
        run_id=run_id,
        run_dir=Path(execute_result.run_dir),
        transcript=transcript,
        scores=[],
        run_meta=run_meta,
    )


def execute_scenario(
    scenario_path: str,
    target_name: str,
    out_dir: str,
    config: Dict[str, Any],
) -> ExecuteResult:
    scenario = load_scenario(scenario_path)
    scenario["source_path"] = scenario_path

    output_root_path = Path(out_dir)
    output_root_path.mkdir(parents=True, exist_ok=True)

    run_id = _build_run_id()
    run_dir = output_root_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    target_cls = get_target(target_name)
    target_config = dict(config)
    target_config["run_id"] = run_id
    target = target_cls(scenario, target_config)

    runner_config = {
        "target": target_name,
        "model": getattr(target, "model", None),
        "base_url": getattr(target, "base_url", None),
        "temperature": config.get("temperature"),
        "max_tokens": config.get("max_tokens"),
        "seed": config.get("seed"),
        "leaky": bool(config.get("leaky")),
        "leak_mode": config.get("leak_mode"),
        "leak_profile": config.get("leak_profile"),
        "leak_after": config.get("leak_after"),
        "use_llm": config.get("use_llm"),
        "mock_judge": config.get("mock_judge"),
    }

    transcript: List[Dict[str, Any]] = []
    messages: List[Dict[str, str]] = []
    http_audit: Optional[List[Any]] = [] if target_name == "http" else None
    http_raw_response: Optional[List[Any]] = [] if target_name == "http" else None

    auditor_seed = scenario.get("auditor_seed")
    if auditor_seed:
        messages.append({"role": "system", "content": auditor_seed})

    turn_index = 0
    started_at = _utc_now()

    for turn in scenario.get("turns", []):
        role = turn.get("role", "user")
        content = turn.get("content", "")
        messages.append({"role": role, "content": content})
        transcript.append(_entry(turn_index, role, content))
        turn_index += 1

        if role != "user":
            continue

        response = target.respond(messages)
        assistant_content = response.get("content", "")
        metadata = response.get("metadata") or {}

        if metadata.get("mock_audit"):
            audit_payload = metadata.get("mock_audit")
            if isinstance(audit_payload, dict):
                leaked_fields = audit_payload.get("leaked_fields") or []
                audit_payload = {
                    "leaked_fields": leaked_fields,
                    "turn_index": turn_index,
                }
                assistant_content = _append_mock_audit(assistant_content, audit_payload)
                metadata["mock_audit"] = audit_payload
        if http_audit is not None:
            http_audit.append(metadata.get("http_audit"))
        if http_raw_response is not None:
            http_raw_response.append(metadata.get("http_raw_response"))

        messages.append({"role": "assistant", "content": assistant_content})
        transcript.append(_entry(turn_index, "assistant", assistant_content, metadata or None))
        turn_index += 1

    finished_at = _utc_now()
    run_meta = {
        "run_id": run_id,
        "scenario_path": scenario_path,
        "scenario_id": scenario.get("scenario_id"),
        "target": target_name,
        "runner_config": runner_config,
        "started_at": started_at,
        "finished_at": finished_at,
        "http_audit": http_audit,
        "http_raw_response": http_raw_response,
    }

    transcript_path = run_dir / "transcript.json"
    run_meta_path = run_dir / "run_meta.json"
    scenario_json_path = run_dir / "scenario.json"

    write_json(transcript_path, transcript)
    write_json(run_meta_path, run_meta)
    write_json(scenario_json_path, scenario)

    return ExecuteResult(
        run_dir=str(run_dir),
        scenario_path=scenario_path,
        transcript_path=str(transcript_path),
        run_meta_path=str(run_meta_path),
        scenario_json_path=str(scenario_json_path),
    )


def _entry(
    turn_index: int,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    entry = {
        "turn_index": turn_index,
        "role": role,
        "content": content,
        "timestamp": _utc_now(),
    }
    if metadata:
        entry["metadata"] = metadata
    return entry


def _append_mock_audit(content: str, payload: Dict[str, Any]) -> str:
    return f"{content}\n{_format_mock_audit(payload)}"


def _format_mock_audit(payload: Dict[str, Any]) -> str:
    audit_json = json.dumps(
        {"leaked_fields": payload.get("leaked_fields", []), "turn_index": payload.get("turn_index")},
        separators=(",", ":"),
    )
    return f"<<MOCK_AUDIT>> {audit_json}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    return f"{stamp}_{suffix}"
