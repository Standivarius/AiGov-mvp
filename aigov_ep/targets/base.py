"""Target adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class TargetAdapter(ABC):
    name = "base"

    def __init__(self, scenario: Dict[str, Any], config: Dict[str, Any]) -> None:
        self.scenario = scenario
        self.config = config

    @abstractmethod
    def respond(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Return a dict with at least a 'content' field."""
        raise NotImplementedError
