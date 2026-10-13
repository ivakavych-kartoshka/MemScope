"""Directly specified paper baselines."""

from collections.abc import Sequence

from ..data.schemas import MemoryItem, TaskContext
from ..models.ranking import LexicalRanker, Ranker
from .base import Baseline


class UnscopedBaseline(Baseline):
    name = "unscoped"

    def __init__(self, ranker: Ranker | None = None) -> None:
        self.ranker = ranker or LexicalRanker()

    def retrieve(
        self, query: str, items: Sequence[MemoryItem], context: TaskContext, k: int
    ) -> Sequence[MemoryItem]:
        return self.ranker.rank(query, items, k)


class NamespaceBaseline(Baseline):
    name = "namespace"

    def __init__(self, ranker: Ranker | None = None) -> None:
        self.ranker = ranker or LexicalRanker()

    def retrieve(
        self, query: str, items: Sequence[MemoryItem], context: TaskContext, k: int
    ) -> Sequence[MemoryItem]:
        scoped = [item for item in items if item.namespace == context.consumer_id]
        return self.ranker.rank(query, scoped, k)


class PromptOnlyBaseline(UnscopedBaseline):
    """Store remains unscoped; the textual instruction is intentionally non-enforcing."""

    name = "prompt_only"
