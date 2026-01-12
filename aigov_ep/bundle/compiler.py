"""Bundle compiler for single-scenario EP bundles."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from ..loader import load_scenario


class BundleCompileError(RuntimeError):
    pass


def compile_single_scenario_bundle(
    scenario_path: str,
    out_dir: str,
    client_id: str | None = None,
) -> Dict[str, str]:
    scenario = load_scenario(scenario_path)
    _validate_scenario(scenario)

    scenario_id = str(scenario.get("scenario_id"))
    original_path = Path(scenario_path)
    ext = original_path.suffix or ".yaml"

    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    scenario_checksum = _sha256_file(original_path)
    bundle_hash = _bundle_hash(client_id or "default", scenario_id, scenario_checksum)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = out_root / f"bundle_{client_id or 'default'}_{stamp}_{bundle_hash[:8]}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    scenarios_dir = bundle_dir / "scenarios"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    scenario_filename = f"{scenario_id}{ext}"
    scenario_target = scenarios_dir / scenario_filename
    shutil.copyfile(original_path, scenario_target)

    manifest = _build_manifest(
        scenario_id=scenario_id,
        scenario_checksum=scenario_checksum,
        scenario_rel_path=str(Path("scenarios") / scenario_filename),
        client_id=client_id or "default",
        bundle_hash=bundle_hash,
    )

    manifest_path = bundle_dir / "bundle_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)

    build_meta_path = bundle_dir / "build_meta.json"
    _write_build_meta(build_meta_path)

    manifest_checksum = _sha256_file(manifest_path)

    checksums_path = bundle_dir / "checksums.sha256"
    _write_checksums(
        checksums_path,
        [
            (scenario_checksum, str(Path("scenarios") / scenario_filename)),
            (manifest_checksum, "bundle_manifest.json"),
        ],
    )

    return {
        "bundle_dir": str(bundle_dir),
        "manifest_path": str(manifest_path),
    }


def _validate_scenario(scenario: Dict[str, Any]) -> None:
    required = {
        "scenario_id": str,
        "title": str,
        "category": str,
        "turns": list,
    }
    for key, expected_type in required.items():
        value = scenario.get(key)
        if not isinstance(value, expected_type):
            raise BundleCompileError(f"Scenario missing or invalid '{key}'")


def _build_manifest(
    scenario_id: str,
    scenario_checksum: str,
    scenario_rel_path: str,
    client_id: str,
    bundle_hash: str,
) -> Dict[str, Any]:
    return {
        "manifest_version": "0.1",
        "bundle_hash": bundle_hash,
        "client": {"client_id": client_id},
        "scenarios": [
            {
                "scenario_id": scenario_id,
                "source": "single",
                "file_path": scenario_rel_path,
                "checksum": scenario_checksum,
            }
        ],
        "compiler": {
            "version": "ep-bundle-compiler-0.1.0",
            "rules": {"validation": "minimal"},
        },
        "checksums": {"file": "checksums.sha256", "algorithm": "SHA-256"},
    }


def _bundle_hash(client_id: str, scenario_id: str, scenario_checksum: str) -> str:
    stable_fields = {
        "client_id": client_id,
        "scenario_id": scenario_id,
        "scenario_checksum": scenario_checksum,
    }
    payload = json.dumps(stable_fields, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_checksums(path: Path, entries: list[tuple[str, str]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for checksum, rel_path in entries:
            handle.write(f"{checksum}  {rel_path}\n")


def _write_build_meta(path: Path) -> None:
    payload = {"created_at": _utc_now()}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
