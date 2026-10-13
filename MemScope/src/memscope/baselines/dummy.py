"""Deterministic test-only baseline."""

from collections.abc import Sequence

from ..data.schemas import MemoryItem, TaskContext
from .base import Baseline


class DummyFirstBaseline(Baseline):
    name = "dummy_test_only"

    def retrieve(
        self, query: str, items: Sequence[MemoryItem], context: TaskContext, k: int
    ) -> Sequence[MemoryItem]:
        return sorted(items, key=lambda item: item.item_id)[:k]
