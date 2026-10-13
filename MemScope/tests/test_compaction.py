import pytest
from conftest import make_item, make_label

from memscope.methods.compaction import (
    EvictionWeights,
    ResourceConflict,
    exact_knapsack_oracle,
    policy_aware_compact,
)
from memscope.methods.store import InMemoryStore


def test_expired_removed_before_budget_eviction(store: InMemoryStore) -> None:
    expired = make_item("expired", "old", label=make_label(expires_at=19.0))
    live = make_item("live", "new", size_bytes=10)
    store.commit(expired)
    store.commit(live)
    report = policy_aware_compact(store, 20, 20.0)
    assert report.expired_or_revoked == ("expired",)
    assert store.tombstone_digest("expired") == expired.integrity_digest


def test_hard_pin_conflict_is_explicit(store: InMemoryStore) -> None:
    store.commit(make_item("critical", "x", hard_pinned=True, size_bytes=50))
    with pytest.raises(ResourceConflict):
        policy_aware_compact(store, 10, 20.0)


def test_policy_value_preserves_safety_item(store: InMemoryStore) -> None:
    safety = make_item("safety", "s", safety_value=10.0, size_bytes=10)
    ordinary = make_item("ordinary", "o", future_utility=0.1, size_bytes=10)
    store.commit(safety)
    store.commit(ordinary)
    report = policy_aware_compact(store, 10, 20.0)
    assert report.retained == ("safety",)


def test_exact_oracle_respects_budget() -> None:
    items = [
        make_item("a", "a", future_utility=2.0, size_bytes=5),
        make_item("b", "b", future_utility=1.0, size_bytes=5),
    ]
    assert exact_knapsack_oracle(items, 5, EvictionWeights()) == {"a"}
