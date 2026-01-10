"""Shared scoring helpers."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def extract_mock_audit(transcript: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for entry in transcript:
        if entry.get("role") != "assistant":
            continue
        content = entry.get("content", "")
        for line in content.splitlines():
            if line.startswith("<<MOCK_AUDIT>>"):
                raw = line.replace("<<MOCK_AUDIT>>", "", 1).strip()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    return None
                if isinstance(payload, dict):
                    return payload
    return None


def run_scorers(
    scenario: Dict[str, Any],
    transcript: List[Dict[str, Any]],
    mock_audit: Optional[Dict[str, Any]],
    mock_judge: bool = False,
) -> List[Dict[str, Any]]:
    from ..scorers import score_gdpr_compliance, score_pii_disclosure, score_special_category_leak

    category = (scenario.get("category") or "").upper()
    if category == "PII_DISCLOSURE":
        return [score_pii_disclosure(transcript, scenario=scenario)]
    if category == "SPECIAL_CATEGORY_LEAK":
        return [score_special_category_leak(transcript, scenario=scenario, mock_audit=mock_audit)]
    if category == "GDPR_COMPLIANCE":
        return [score_gdpr_compliance(transcript, scenario=scenario, evidence={}, mock_judge=mock_judge)]
    raise ValueError(
        f"Unknown scenario.category '{scenario.get('category')}'. "
        "Expected PII_DISCLOSURE, SPECIAL_CATEGORY_LEAK, or GDPR_COMPLIANCE."
    )
