"""Benchmark-specific answer/abstention/FAMA scorers (paper Section 11.7).

These scorers are declared in advance and exercised on synthetic examples so the
real-benchmark path is ready before licensed data is provisioned. They never run
a model, never reach the network, and never claim a paper result on their own.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from .core import exact_match, token_f1

_ABSTENTION_MARKERS = frozenset(
    {
        "",
        "unknown",
        "not sure",
        "no answer",
        "cannot answer",
        "can't answer",
        "no information",
        "i don't know",
        "i do not know",
    }
)


@dataclass(frozen=True)
class ScoringExample:
    """One scored prediction against its policy-aware ground truth."""

    query_id: str
    prediction: str
    target: str | None = None
    should_abstain: bool = False
    used_item_ids: tuple[str, ...] = ()
    invalidated_item_ids: frozenset[str] = field(default_factory=frozenset)


def is_abstention(prediction: str, markers: Iterable[str] = _ABSTENTION_MARKERS) -> bool:
    normalized = " ".join(prediction.strip().casefold().split())
    return normalized in markers


def _scorable(example: ScoringExample) -> bool:
    return example.target is not None or example.should_abstain


def _default_correct(example: ScoringExample) -> bool:
    return bool(exact_match(example.prediction, example.target or ""))


def _answer_correct(example: ScoringExample, correct: Callable[[ScoringExample], bool]) -> bool:
    if example.should_abstain:
        return is_abstention(example.prediction)
    return correct(example)


def answer_metrics(
    examples: Iterable[ScoringExample],
    *,
    correct: Callable[[ScoringExample], bool] | None = None,
) -> dict[str, float]:
    """Exact-match and token-F1 means over examples with an answer target."""

    correct = correct or _default_correct
    scored = [example for example in examples if example.target is not None]
    if not scored:
        return {"exact_match": 0.0, "token_f1": 0.0}
    exact = sum(float(correct(example)) for example in scored) / len(scored)
    f1 = sum(token_f1(example.prediction, example.target or "") for example in scored) / len(scored)
    return {"exact_match": exact, "token_f1": f1}


def abstention_metrics(examples: Iterable[ScoringExample]) -> dict[str, float]:
    """Accuracy of the abstain/answer decision over answerable or abstain examples."""

    scored = [example for example in examples if _scorable(example)]
    if not scored:
        return {"abstention_accuracy": 0.0}
    correct = sum(is_abstention(example.prediction) == example.should_abstain for example in scored)
    return {"abstention_accuracy": correct / len(scored)}


def accuracy_metrics(
    examples: Iterable[ScoringExample],
    *,
    correct: Callable[[ScoringExample], bool] | None = None,
) -> dict[str, float]:
    """Combined answer-or-abstain accuracy over every scorable example."""

    if correct is None:
        correct = _default_correct
    scored = [example for example in examples if _scorable(example)]
    if not scored:
        return {"accuracy": 0.0}
    total = sum(float(_answer_correct(example, correct)) for example in scored)
    return {"accuracy": total / len(scored)}


def fama_metrics(
    examples: Iterable[ScoringExample],
    *,
    correct: Callable[[ScoringExample], bool] | None = None,
) -> dict[str, float]:
    """Forgetting-aware memory accuracy: correct answers that reuse no invalidated item."""

    if correct is None:
        correct = _default_correct
    scored = [example for example in examples if _scorable(example)]
    if not scored:
        return {"fama": 0.0, "invalidated_use_rate": 0.0}
    hits = 0
    invalidated = 0
    for example in scored:
        used_invalidated = bool(set(example.used_item_ids) & example.invalidated_item_ids)
        if used_invalidated:
            invalidated += 1
        if _answer_correct(example, correct) and not used_invalidated:
            hits += 1
    return {
        "fama": hits / len(scored),
        "invalidated_use_rate": invalidated / len(scored),
    }


def score_benchmark(name: str, examples: Iterable[ScoringExample]) -> dict[str, float]:
    """Dispatch to the preregistered scorer set for a named benchmark."""

    materialized = list(examples)
    if name == "locomo":
        return answer_metrics(materialized)
    if name == "longmemeval":
        return {
            **answer_metrics(materialized),
            **abstention_metrics(materialized),
            **accuracy_metrics(materialized),
        }
    if name == "memora":
        return {**answer_metrics(materialized), **fama_metrics(materialized)}
    if name == "pa_bench":
        return {**accuracy_metrics(materialized), **abstention_metrics(materialized)}
    if name == "multi_app":
        return {
            **answer_metrics(materialized),
            **abstention_metrics(materialized),
            **accuracy_metrics(materialized),
        }
    raise ValueError(f"unsupported benchmark scorer: {name}")
