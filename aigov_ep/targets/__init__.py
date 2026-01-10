"""Canonical EP target adapters (moved/copied from aigov-eval).

Target adapter registry.
"""

from __future__ import annotations

from typing import Any, Dict, Type

from .base import TargetAdapter
from .http_target import HttpTargetAdapter
from .mock_llm import MockTargetAdapter
from .scripted import ScriptedMockTargetAdapter


TARGETS: Dict[str, Type[TargetAdapter]] = {
    HttpTargetAdapter.name: HttpTargetAdapter,
    MockTargetAdapter.name: MockTargetAdapter,
    ScriptedMockTargetAdapter.name: ScriptedMockTargetAdapter,
}


def get_target(name: str) -> Type[TargetAdapter]:
    if name not in TARGETS:
        raise KeyError(f"Unknown target adapter: {name}")
    return TARGETS[name]
