"""Security, utility, lifecycle, and label metrics from paper Section 11.7."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Sequence

from ..data.schemas import MemoryLabel, QueryEvaluation


def authorization_violations(evaluations: Sequence[QueryEvaluation]) -> int:
    """Equation (6): count unique returned items known to be unauthorized per query."""

    return sum(len(set(row.returned_ids) & set(row.unauthorized_ids)) for row in evaluations)


def out_of_scope_retrieval_rate(evaluations: Sequence[QueryEvaluation]) -> float:
    returned = sum(len(set(row.returned_ids)) for row in evaluations)
    return authorization_violations(evaluations) / returned if returned else 0.0


def entitled_misses(evaluations: Sequence[QueryEvaluation]) -> int:
    """Equation (7): total entitled ground-truth records not returned."""

    return sum(len(set(row.entitled_ids) - set(row.returned_ids)) for row in evaluations)


def entitled_recall_eligible_queries(evaluations: Sequence[QueryEvaluation]) -> int:
    """Frozen convention (author decision): queries with empty ground truth are excluded."""

    return sum(1 for row in evaluations if row.entitled_ids)


def entitled_recall_at_k(
    evaluations: Sequence[QueryEvaluation], empty_ground_truth: str = "exclude"
) -> float:
    """Equation (8): mean per-query entitled recall.

    Frozen convention: queries with empty entitled ground truth contribute to no
    denominator and are excluded by default. The set of excluded queries depends
    only on the method-independent ground truth ``G(q)``, so ER@k stays comparable
    across methods evaluated on the identical query set ``Q``. ``'zero'`` remains
    available only as a diagnostic that charges an empty query a zero score; it is
    not the reported headline metric.
    """

    if empty_ground_truth not in {"exclude", "zero"}:
        raise ValueError("empty_ground_truth must be 'exclude' or 'zero'")
    scores: list[float] = []
    for row in evaluations:
        if not row.entitled_ids:
            if empty_ground_truth == "zero":
                scores.append(0.0)
            continue
        scores.append(len(set(row.returned_ids) & set(row.entitled_ids)) / len(row.entitled_ids))
    return sum(scores) / len(scores) if scores else 0.0


def unique_record_extraction_yield(evaluations: Sequence[QueryEvaluation]) -> int:
    leaked: set[str] = set()
    for row in evaluations:
        leaked.update(set(row.returned_ids) & set(row.unauthorized_ids))
    return len(leaked)


def exact_match(prediction: str, target: str) -> float:
    return float(prediction.strip().casefold() == target.strip().casefold())


def token_f1(prediction: str, target: str) -> float:
    pred = prediction.casefold().split()
    gold = target.casefold().split()
    if not pred and not gold:
        return 1.0
    if not pred or not gold:
        return 0.0
    pred_counts: dict[str, int] = defaultdict(int)
    gold_counts: dict[str, int] = defaultdict(int)
    for token in pred:
        pred_counts[token] += 1
    for token in gold:
        gold_counts[token] += 1
    overlap = sum(min(count, gold_counts[token]) for token, count in pred_counts.items())
    precision = overlap / len(pred)
    recall = overlap / len(gold)
    return 2 * precision * recall / (precision + recall) if overlap else 0.0


def safety_critical_survival(retained: Iterable[str], safety_critical: Iterable[str]) -> float:
    critical = set(safety_critical)
    if not critical:
        return 0.0
    return len(set(retained) & critical) / len(critical)


def latency_summary(latencies_ms: Sequence[float]) -> dict[str, float]:
    if not latencies_ms:
        return {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0}
    if any((not math.isfinite(x) or x < 0) for x in latencies_ms):
        raise ValueError("latencies must be finite and non-negative")
    values = sorted(latencies_ms)

    def nearest(percentile: float) -> float:
        index = min(len(values) - 1, max(0, math.ceil(percentile * len(values)) - 1))
        return values[index]

    return {"p50_ms": nearest(0.50), "p95_ms": nearest(0.95), "p99_ms": nearest(0.99)}


def label_metrics(predicted: Sequence[MemoryLabel], gold: Sequence[MemoryLabel]) -> dict[str, float]:
    if len(predicted) != len(gold):
        raise ValueError("predicted and gold label counts differ")
    if not gold:
        return {"exact_match": 0.0, "false_widening": 0.0, "false_narrowing": 0.0}
    exact = widening = narrowing = 0
    for pred, target in zip(predicted, gold):
        if pred == target:
            exact += 1
        if (
            not pred.purposes <= target.purposes
            or not pred.apps <= target.apps
            or not pred.tools <= target.tools
            or not pred.consumers <= target.consumers
            or pred.expires_at > target.expires_at
            or pred.not_before < target.not_before
            or pred.sensitivity < target.sensitivity
        ):
            widening += 1
        elif pred != target:
            narrowing += 1
    n = len(gold)
    return {
        "exact_match": exact / n,
        "false_widening": widening / n,
        "false_narrowing": narrowing / n,
    }


def binary_error_rates(
    decisions_supported: Sequence[bool], gold_supported: Sequence[bool]
) -> dict[str, float]:
    if len(decisions_supported) != len(gold_supported):
        raise ValueError("decision and gold counts differ")
    positives = sum(gold_supported)
    negatives = len(gold_supported) - positives
    false_rejects = sum(g and not d for d, g in zip(decisions_supported, gold_supported))
    false_accepts = sum((not g) and d for d, g in zip(decisions_supported, gold_supported))
    return {
        "false_acceptance_rate": false_accepts / negatives if negatives else 0.0,
        "false_rejection_rate": false_rejects / positives if positives else 0.0,
    }


def evaluate_queries(evaluations: Sequence[QueryEvaluation]) -> dict[str, float]:
    eligible = entitled_recall_eligible_queries(evaluations)
    summary = {
        "authorization_violations": float(authorization_violations(evaluations)),
        "out_of_scope_retrieval_rate": out_of_scope_retrieval_rate(evaluations),
        "entitled_misses": float(entitled_misses(evaluations)),
        "entitled_recall_at_k": entitled_recall_at_k(evaluations),
        "entitled_recall_eligible_queries": float(eligible),
        "entitled_recall_excluded_queries": float(len(evaluations) - eligible),
        "unique_record_extraction_yield": float(unique_record_extraction_yield(evaluations)),
    }
    summary.update(latency_summary([row.latency_ms for row in evaluations]))
    return summary
