"""External baseline contracts; no third-party API is fabricated."""

from collections.abc import Sequence
from pathlib import Path

from ..data.schemas import MemoryItem, TaskContext
from .base import Baseline


class ExternalBaseline(Baseline):
    def __init__(self, name: str, artifact_root: Path) -> None:
        self.name = name
        self.artifact_root = artifact_root

    def retrieve(
        self, query: str, items: Sequence[MemoryItem], context: TaskContext, k: int
    ) -> Sequence[MemoryItem]:
        raise NotImplementedError(
            f"{self.name} requires a manually provisioned, version-pinned external artifact; "
            "implement the connector described in docs/baseline_adapters.md"
        )


class AppSearchVisibilityBaseline(ExternalBaseline):
    def __init__(self, artifact_root: Path) -> None:
        super().__init__("appsearch_visibility", artifact_root)
