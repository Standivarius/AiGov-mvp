"""Taxonomy loader for GDPR signals.

Provides versioned signal taxonomy with validation and synonym mapping.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Default taxonomy path (packaged resource)
_DEFAULT_TAXONOMY_PATH = Path(__file__).parent / "signals.json"

# Cached taxonomy data
_taxonomy_cache: dict | None = None


def load_taxonomy(path: Path | str | None = None) -> dict:
    """Load taxonomy from JSON file.

    Args:
        path: Path to taxonomy JSON file. Defaults to packaged signals.json.

    Returns:
        Taxonomy dict with version, description, and signals.
    """
    global _taxonomy_cache

    if path is None:
        path = _DEFAULT_TAXONOMY_PATH
    else:
        path = Path(path)

    # Use cache if loading default path and already loaded
    if path == _DEFAULT_TAXONOMY_PATH and _taxonomy_cache is not None:
        return _taxonomy_cache

    with open(path, encoding="utf-8") as f:
        taxonomy = json.load(f)

    # Cache if default path
    if path == _DEFAULT_TAXONOMY_PATH:
        _taxonomy_cache = taxonomy

    return taxonomy


def get_taxonomy_version(path: Path | str | None = None) -> str:
    """Get taxonomy version string."""
    return load_taxonomy(path).get("version", "unknown")


def get_allowed_signal_ids(path: Path | str | None = None) -> set[str]:
    """Get set of valid signal IDs from taxonomy."""
    taxonomy = load_taxonomy(path)
    return {s["id"] for s in taxonomy.get("signals", [])}


def get_signal_metadata(path: Path | str | None = None) -> dict[str, dict]:
    """Get mapping of signal ID to full metadata."""
    taxonomy = load_taxonomy(path)
    return {s["id"]: s for s in taxonomy.get("signals", [])}


# Known signal synonyms: maps non-canonical -> canonical signal ID
# These are common variations seen in judge outputs or legacy cases
SIGNAL_SYNONYMS: dict[str, str] = {
    # Legacy case labels -> canonical taxonomy IDs
    "data_minimization_violation": "data_minimization_breach",
    "subject_rights_denial": "rights_violation",
    "cross_border_transfer_violation": "international_transfer_violation",
    "automated_decision_making": "profiling_without_safeguards",
    "excessive_data_retention": "retention_violation",
    "dpo_absence": "inadequate_dpo",
    # Common judge output variations
    "consent_violation": "lack_of_consent",
    "no_consent": "lack_of_consent",
    "missing_consent": "lack_of_consent",
    "transparency_violation": "inadequate_transparency",
    "lack_of_transparency": "inadequate_transparency",
    "data_breach": "breach_notification_failure",
    "security_breach": "inadequate_security",
    "cross_border_transfer": "international_transfer_violation",
    "international_transfer": "international_transfer_violation",
    "unlawful_transfer": "international_transfer_violation",
    "automated_profiling": "profiling_without_safeguards",
    "profiling_violation": "profiling_without_safeguards",
    "subject_access_denial": "rights_violation",
    "access_request_denial": "rights_violation",
    "erasure_denial": "rights_violation",
    "excessive_retention": "retention_violation",
    "data_retention_violation": "retention_violation",
    "storage_limitation_breach": "retention_violation",
    "missing_dpo": "inadequate_dpo",
    "no_dpo": "inadequate_dpo",
    "dpo_violation": "inadequate_dpo",
    "special_category_data": "special_category_violation",
    "sensitive_data_violation": "special_category_violation",
    "excessive_collection": "excessive_data_collection",
    "data_minimisation_breach": "data_minimization_breach",  # UK spelling
    "processor_violation": "processor_contract_violation",
    "controller_processor_violation": "processor_contract_violation",
}


def normalize_signal(signal: str, allowed: set[str] | None = None) -> tuple[str | None, bool]:
    """Normalize a signal to canonical taxonomy ID.

    Args:
        signal: Signal string to normalize
        allowed: Set of allowed signal IDs (loaded if None)

    Returns:
        Tuple of (normalized_signal, is_valid)
        - If signal is canonical: (signal, True)
        - If signal has synonym: (canonical_signal, True)
        - If unknown: (None, False)
    """
    if allowed is None:
        allowed = get_allowed_signal_ids()

    # Already canonical
    if signal in allowed:
        return signal, True

    # Check synonyms
    if signal in SIGNAL_SYNONYMS:
        canonical = SIGNAL_SYNONYMS[signal]
        if canonical in allowed:
            return canonical, True

    # Unknown signal
    return None, False


def validate_signals(signals: list[str], allowed: set[str] | None = None) -> dict[str, list[str]]:
    """Validate and normalize a list of signals.

    Args:
        signals: List of signal strings to validate
        allowed: Set of allowed signal IDs (loaded if None)

    Returns:
        Dict with:
            - "signals": list of valid canonical signals
            - "other_signals": list of unrecognized signals
    """
    if allowed is None:
        allowed = get_allowed_signal_ids()

    valid_signals = []
    other_signals = []
    seen = set()

    for signal in signals:
        normalized, is_valid = normalize_signal(signal, allowed)
        if is_valid and normalized not in seen:
            valid_signals.append(normalized)
            seen.add(normalized)
        elif not is_valid:
            other_signals.append(signal)

    return {
        "signals": valid_signals,
        "other_signals": other_signals,
    }
