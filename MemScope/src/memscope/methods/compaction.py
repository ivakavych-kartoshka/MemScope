"""Equation (10-11) and Algorithm 3 policy-aware compaction."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..data.schemas import ItemState, MemoryItem
from .store import InMemoryStore


class ResourceConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class EvictionWeights:
    alpha: float = 1.0
    beta: float = 2.0
    gamma: float = 0.5
    delta: float = 0.5
    eta: float = 0.5


@dataclass(frozen=True)
class CompactionReport:
    expired_or_revoked: tuple[str, ...]
    evicted: tuple[str, ...]
    retained: tuple[str, ...]
    bytes_after: int


def item_value(item: MemoryItem, weights: EvictionWeights) -> float:
    """Equation (10) per-item value before the binary retention decision."""

    return (
        weights.alpha * item.future_utility
        + weights.beta * item.safety_value
        + weights.gamma * item.recomputation_cost
        - weights.delta * item.sensitivity_cost
        - weights.eta * item.staleness
    )


def policy_aware_compact(
    store: InMemoryStore,
    byte_budget: int,
    now: float,
    weights: EvictionWeights | None = None,
) -> CompactionReport:
    """Algorithm 3 greedy approximation; no approximation ratio is claimed."""

    if weights is None:
        weights = EvictionWeights()
    if byte_budget < 0:
        raise ValueError("byte budget must be non-negative")
    _, snapshot = store.snapshot()
    expired = []
    for item in snapshot:
        if now >= item.label.expires_at or item.state in {ItemState.EXPIRED, ItemState.TOMBSTONED}:
            store.remove(item.item_id)
            expired.append(item.item_id)

    _, live = store.snapshot()
    pinned_bytes = sum(item.size_bytes for item in live if item.hard_pinned)
    if pinned_bytes > byte_budget:
        raise ResourceConflict(
            f"hard-pinned items require {pinned_bytes} bytes but budget is {byte_budget}"
        )
    evicted: list[str] = []
    if store.bytes_used() > byte_budget:
        candidates = [item for item in live if not item.hard_pinned]
        candidates.sort(key=lambda item: (item_value(item, weights) / item.size_bytes, item.item_id))
        for item in candidates:
            store.remove(item.item_id)
            evicted.append(item.item_id)
            if store.bytes_used() <= byte_budget:
                break
    _, retained = store.snapshot()
    return CompactionReport(
        expired_or_revoked=tuple(expired),
        evicted=tuple(evicted),
        retained=tuple(item.item_id for item in retained),
        bytes_after=store.bytes_used(),
    )


def exact_knapsack_oracle(items: Sequence[MemoryItem], byte_budget: int, weights: EvictionWeights) -> set[str]:
    """Small-instance exact oracle for Eq. (10-11), not the online algorithm."""

    if byte_budget < 0:
        raise ValueError("byte budget must be non-negative")
    pinned = [item for item in items if item.hard_pinned]
    pinned_bytes = sum(item.size_bytes for item in pinned)
    if pinned_bytes > byte_budget:
        raise ResourceConflict("hard-pinned items exceed exact-oracle budget")
    capacity = byte_budget - pinned_bytes
    optional = [item for item in items if not item.hard_pinned]
    dp: list[tuple[float, set[str]]] = [(0.0, set()) for _ in range(capacity + 1)]
    for item in optional:
        value = item_value(item, weights)
        for budget in range(capacity, item.size_bytes - 1, -1):
            prior_value, prior_ids = dp[budget - item.size_bytes]
            candidate_value = prior_value + value
            if candidate_value > dp[budget][0]:
                dp[budget] = (candidate_value, set(prior_ids) | {item.item_id})
    best = max(dp, key=lambda pair: pair[0])[1]
    return {item.item_id for item in pinned} | best
