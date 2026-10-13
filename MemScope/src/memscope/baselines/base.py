"""Baseline interface with a common input/output schema."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..data.schemas import MemoryItem, TaskContext


class Baseline(ABC):
    name: str

    @abstractmethod
    def retrieve(
        self, query: str, items: Sequence[MemoryItem], context: TaskContext, k: int
    ) -> Sequence[MemoryItem]:
        """Return items from the supplied matched-harness store."""
