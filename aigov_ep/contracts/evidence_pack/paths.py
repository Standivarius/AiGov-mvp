"""Paths to vendored evidence pack contracts."""

from __future__ import annotations

from pathlib import Path


def evidence_pack_schema_path() -> Path:
    return Path(__file__).resolve().parent / "evidence_pack_v0.schema.json"


def evidence_pack_manifest_path() -> Path:
    return Path(__file__).resolve().parent / "evidence_pack_manifest_v1.json"
