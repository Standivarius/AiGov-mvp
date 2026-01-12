"""Vendored contract helpers."""

from __future__ import annotations

from pathlib import Path

_CONTRACTS_DIR = Path(__file__).parent
_EVIDENCE_PACK_DIR = _CONTRACTS_DIR / "evidence_pack"


def get_evidence_pack_schema_path() -> Path:
    """Return absolute path to the evidence pack schema."""
    return (_EVIDENCE_PACK_DIR / "evidence_pack_v0.schema.json").resolve()


def get_evidence_pack_manifest_schema_path() -> Path:
    """Return absolute path to the evidence pack manifest schema."""
    return (_EVIDENCE_PACK_DIR / "evidence_pack_manifest_v1.json").resolve()
