"""Paper-defined metrics and statistical helpers."""

from .core import (
    authorization_violations,
    entitled_misses,
    entitled_recall_at_k,
    entitled_recall_eligible_queries,
)

__all__ = [
    "authorization_violations",
    "entitled_misses",
    "entitled_recall_at_k",
    "entitled_recall_eligible_queries",
]
