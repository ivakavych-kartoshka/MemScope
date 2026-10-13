"""Version-pinned external attack adapter schema."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AttackRecord:
    attack_name: str
    artifact_version: str
    reproduction_status: str
    original_threat_model: str
    attack_budget: int
    success_definition: str


class ExternalAttackAdapter:
    SUPPORTED_NAMES = frozenset({"MEXTRA", "ADAM", "SPORE", "MINJA", "MemPoison"})

    def __init__(self, name: str, artifact_root: Path, version: str) -> None:
        if name not in self.SUPPORTED_NAMES:
            raise ValueError(f"unknown paper attack: {name}")
        self.name = name
        self.artifact_root = artifact_root
        self.version = version

    def run(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError(
            f"{self.name} is an external artifact adapter. Manually provision and validate "
            "the version-pinned implementation before enabling it."
        )
