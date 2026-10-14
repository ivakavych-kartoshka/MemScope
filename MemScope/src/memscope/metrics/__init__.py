"""Paper-defined metrics and statistical helpers."""

from .core import (
    authorization_violations,
    entitled_misses,
    entitled_recall_at_k,
    entitled_recall_eligible_queries,
)
from .scorers import (
    ScoringExample,
    abstention_metrics,
    answer_metrics,
    fama_metrics,
    is_abstention,
    score_benchmark,
)

__all__ = [
    "ScoringExample",
    "abstention_metrics",
    "answer_metrics",
    "authorization_violations",
    "entitled_misses",
    "entitled_recall_at_k",
    "entitled_recall_eligible_queries",
    "fama_metrics",
    "is_abstention",
    "score_benchmark",
]
