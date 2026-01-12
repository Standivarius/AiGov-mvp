"""Judge output mapper for behaviour_json_v0_phase0 schema compliance."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _behaviour_schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "contracts" / "behaviour_json_v0_phase0.schema.json"


def _generate_deterministic_id(prefix: str, *components: str) -> str:
    hasher = hashlib.sha256()
    for component in components:
        hasher.update(str(component).encode("utf-8"))
    hash_suffix = hasher.hexdigest()[:12]
    return f"{prefix}_{hash_suffix}"


def _map_verdict_to_rating(verdict: str) -> str:
    mapping = {
        "VIOLATION": "VIOLATED",
        "NO_VIOLATION": "COMPLIANT",
        "UNCLEAR": "UNDECIDED",
    }
    if verdict not in mapping:
        raise ValueError(
            f"Unknown verdict '{verdict}'. Expected one of: {list(mapping.keys())}"
        )
    return mapping[verdict]


def _infer_severity_from_rating(rating: str) -> str:
    mapping = {
        "VIOLATED": "HIGH",
        "COMPLIANT": "INFO",
        "UNDECIDED": "LOW",
    }
    return mapping.get(rating, "MEDIUM")


def map_judge_output_to_behaviour_json(
    internal_output: dict[str, Any],
    scenario_id: str | None = None,
) -> dict[str, Any]:
    if scenario_id is None:
        scenario_id = internal_output.get("judge_meta", {}).get("scenario_id", "unknown")

    timestamp = internal_output.get("judge_meta", {}).get(
        "timestamp_utc", datetime.utcnow().isoformat()
    )

    verdict = internal_output.get("verdict", "UNCLEAR")
    rating = _map_verdict_to_rating(verdict)

    audit_id = _generate_deterministic_id("audit", scenario_id, timestamp[:10])
    run_id = _generate_deterministic_id("run", scenario_id, timestamp)
    finding_id = _generate_deterministic_id("finding", scenario_id, run_id)

    judge_meta = internal_output.get("judge_meta", {})
    framework = judge_meta.get("framework", "GDPR")

    severity = _infer_severity_from_rating(rating)

    inspect_provenance = {
        "model": judge_meta.get("model", "unknown"),
        "timestamp_utc": judge_meta.get("timestamp_utc", timestamp),
    }

    if "temperature" in judge_meta:
        inspect_provenance["temperature"] = judge_meta["temperature"]
    if "mock" in judge_meta:
        inspect_provenance["mock"] = judge_meta["mock"]
    if "source_fixture" in judge_meta:
        inspect_provenance["source_fixture"] = judge_meta["source_fixture"]

    return {
        "audit_id": audit_id,
        "run_id": run_id,
        "finding_id": finding_id,
        "scenario_id": scenario_id,
        "framework": framework,
        "rating": rating,
        "reasoning": internal_output.get("rationale", []),
        "legal_references": internal_output.get("citations", []),
        "signals": internal_output.get("signals", []),
        "severity": severity,
        "inspect_provenance": inspect_provenance,
    }


def validate_against_schema(
    output: dict[str, Any], schema_path: Path | None = None
) -> tuple[bool, str | None]:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required for behaviour_json validation") from exc

    if schema_path is None:
        schema_path = _behaviour_schema_path()

    if not schema_path.exists():
        return (False, f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)

    try:
        jsonschema.validate(instance=output, schema=schema)
        return (True, None)
    except jsonschema.ValidationError as exc:
        error_msg = (
            f"Validation error: {exc.message}\n"
            f"Path: {list(exc.path)}\n"
            f"Failed value: {exc.instance}"
        )
        return (False, error_msg)
    except jsonschema.SchemaError as exc:
        return (False, f"Schema error: {exc.message}")


def map_and_validate(
    internal_output: dict[str, Any],
    scenario_id: str | None = None,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    behaviour_json = map_judge_output_to_behaviour_json(internal_output, scenario_id)
    is_valid, error_msg = validate_against_schema(behaviour_json, schema_path=schema_path)
    if not is_valid:
        raise ValueError(f"Schema validation failed: {error_msg}")
    return behaviour_json
