from collections.abc import Callable, Sequence

import pytest
from conftest import make_context, make_item, make_label

from memscope.data.schemas import MemoryItem
from memscope.methods.retrieval import MemScopeService, PolicyChurnError, RetrievalDenied
from memscope.methods.store import InMemoryStore
from memscope.methods.tokens import TokenIssuer
from memscope.models.ranking import Ranker


def _scripted_clock(ticks: list[float]) -> Callable[[], float]:
    """Deterministic clock that returns one scripted tick per call."""

    remaining = list(ticks)

    def now() -> float:
        return remaining.pop(0)

    return now


def test_filtering_precedes_ranking(store: InMemoryStore, issuer: TokenIssuer) -> None:
    allowed = make_item("allowed", "shopping preference blue", label=make_label(purposes=("ads",), tools=("ads",)))
    secret = make_item("secret", "allergy allergy allergy", label=make_label(purposes=("health",), tools=("health",)))
    store.commit(allowed)
    store.commit(secret)
    context = make_context(purpose="ads", tool="ads")
    token = issuer.issue(context, 30.0, store.policy_epoch)
    service = MemScopeService(store, issuer, clock=lambda: 20.0)
    result = service.retrieve(token, "allergy blue", 1, "assistant.pkg", ("ads",))
    assert [item.item_id for item in result.items] == ["allowed"]
    assert result.candidate_count == 1


def test_expired_item_never_returned(store: InMemoryStore, issuer: TokenIssuer) -> None:
    store.commit(make_item(label=make_label(expires_at=19.0)))
    context = make_context()
    token = issuer.issue(context, 30.0, store.policy_epoch)
    result = MemScopeService(store, issuer, clock=lambda: 20.0).retrieve(
        token, "calendar", 5, "assistant.pkg", ("calendar.read",)
    )
    assert result.items == ()


def test_integrity_tampering_excludes_item(store: InMemoryStore, issuer: TokenIssuer) -> None:
    item = make_item()
    item.payload = "tampered"
    store.commit(item)
    token = issuer.issue(make_context(), 30.0, store.policy_epoch)
    result = MemScopeService(store, issuer, clock=lambda: 20.0).retrieve(
        token, "tampered", 5, "assistant.pkg", ("calendar.read",)
    )
    assert result.items == ()


def test_stale_epoch_denied(store: InMemoryStore, issuer: TokenIssuer) -> None:
    token = issuer.issue(make_context(), 30.0, store.policy_epoch)
    store.increment_epoch()
    with pytest.raises(RetrievalDenied):
        MemScopeService(store, issuer, clock=lambda: 20.0).retrieve(
            token, "calendar", 1, "assistant.pkg", ("calendar.read",)
        )


def test_item_expiring_before_release_is_not_returned(
    store: InMemoryStore, issuer: TokenIssuer
) -> None:
    """Final-check freshness: an item live at filtering but expired at release is dropped."""

    store.commit(make_item("racy", "calendar meeting", label=make_label(expires_at=25.0)))
    token = issuer.issue(make_context(), 30.0, store.policy_epoch)
    # verify=20, filter=22 (live), release=26 (expired) -> restart; then filter=27 sees expiry.
    service = MemScopeService(
        store, issuer, clock=_scripted_clock([20.0, 22.0, 26.0, 27.0, 28.0])
    )
    result = service.retrieve(token, "calendar", 5, "assistant.pkg", ("calendar.read",))
    assert result.items == ()
    assert result.decision == "ALLOW"


def test_release_time_expiry_race_fails_closed(store: InMemoryStore, issuer: TokenIssuer) -> None:
    """If the release recheck keeps observing expiry, retrieval fails closed, never leaks."""

    store.commit(make_item("racy", "calendar meeting", label=make_label(expires_at=25.0)))
    token = issuer.issue(make_context(), 30.0, store.policy_epoch)
    # Filtering is always live (<25) but the release recheck always observes expiry (>=25).
    service = MemScopeService(
        store, issuer, clock=_scripted_clock([20.0, 22.0, 26.0, 22.0, 26.0, 22.0, 26.0])
    )
    with pytest.raises(PolicyChurnError):
        service.retrieve(token, "calendar", 5, "assistant.pkg", ("calendar.read",))


class _ExplodingRanker(Ranker):
    def rank(self, query: str, items: Sequence[MemoryItem], k: int) -> list[MemoryItem]:
        raise RuntimeError("ranker failure")


def test_ranker_exception_fails_explicitly(store: InMemoryStore, issuer: TokenIssuer) -> None:
    """A ranker exception must surface as an explicit failure, never a silent release."""

    store.commit(make_item("m1", "calendar meeting"))
    token = issuer.issue(make_context(), 30.0, store.policy_epoch)
    service = MemScopeService(store, issuer, ranker=_ExplodingRanker(), clock=lambda: 20.0)
    with pytest.raises(RuntimeError, match="ranker failure"):
        service.retrieve(token, "calendar", 5, "assistant.pkg", ("calendar.read",))
    assert store.audit_events() == ()
