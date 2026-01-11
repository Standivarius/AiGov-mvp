"""Run manifest + checksums helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from aigov_ep.utils.io import write_json


_REDACTED = "[redacted]"
_SENSITIVE_MARKERS = (
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "authorization",
    "auth",
    "bearer",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(path: Path, entries: list[tuple[str, str]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for checksum, rel_path in entries:
            handle.write(f"{checksum}  {rel_path}\n")


def write_run_manifest(
    *,
    run_dir: Path,
    scenario_source_path: Optional[Path],
    scenario_json_path: Path,
    transcript_path: Path,
    run_meta_path: Path,
    target_name: str,
    target_config: Dict[str, Any],
) -> Path:
    scenario_rel = _relative_path(run_dir, scenario_json_path)
    transcript_rel = _relative_path(run_dir, transcript_path)
    run_meta_rel = _relative_path(run_dir, run_meta_path)

    scenario_checksum = sha256_file(scenario_json_path)
    transcript_checksum = sha256_file(transcript_path)
    run_meta_checksum = sha256_file(run_meta_path)

    manifest: Dict[str, Any] = {
        "manifest_version": "0.1",
        "created_at_utc": _utc_now(),
        "target": {
            "name": target_name,
            "config": _sanitize_config(target_config),
        },
        "scenario": {"path": scenario_rel, "checksum": scenario_checksum},
        "transcript": {"path": transcript_rel, "checksum": transcript_checksum},
        "run_meta": {"path": run_meta_rel, "checksum": run_meta_checksum},
    }

    bundle_info = _find_bundle_info(scenario_source_path) if scenario_source_path else None
    if bundle_info:
        manifest["bundle"] = bundle_info

    manifest_path = run_dir / "run_manifest.json"
    write_json(manifest_path, manifest)

    manifest_checksum = sha256_file(manifest_path)
    checksums_path = run_dir / "checksums.sha256"
    write_checksums(
        checksums_path,
        [
            (scenario_checksum, scenario_rel),
            (transcript_checksum, transcript_rel),
            (run_meta_checksum, run_meta_rel),
            (manifest_checksum, "run_manifest.json"),
        ],
    )
    return manifest_path


def _sanitize_config(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: Dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(key):
                sanitized[key] = _REDACTED
            else:
                sanitized[key] = _sanitize_config(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_config(item) for item in value]
    return value


def _is_sensitive_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    lower = key.lower()
    return any(marker in lower for marker in _SENSITIVE_MARKERS)


def _relative_path(root: Path, path: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return str(rel)


def _find_bundle_info(scenario_source_path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if not scenario_source_path:
        return None
    current = scenario_source_path.resolve()
    for parent in current.parents:
        manifest_path = parent / "bundle_manifest.json"
        if manifest_path.exists():
            info: Dict[str, Any] = {
                "bundle_dir": str(parent),
                "bundle_manifest_checksum": sha256_file(manifest_path),
            }
            try:
                with open(manifest_path, "r", encoding="utf-8") as handle:
                    manifest = json.load(handle)
            except json.JSONDecodeError:
                manifest = {}
            bundle_hash = manifest.get("bundle_hash")
            if isinstance(bundle_hash, str) and bundle_hash:
                info["bundle_hash"] = bundle_hash
            return info
    return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
