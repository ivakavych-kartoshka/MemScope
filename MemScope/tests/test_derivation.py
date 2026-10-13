from conftest import make_context, make_item, make_label

from memscope.data.schemas import (
    DerivationProposal,
    ItemState,
    MemoryItem,
    MemoryLabel,
    RetrievalToken,
    Sensitivity,
)
from memscope.methods.derivation import admit_derivation
from memscope.methods.store import InMemoryStore
from memscope.methods.tokens import TokenIssuer


def _setup(
    store: InMemoryStore, issuer: TokenIssuer
) -> tuple[MemoryItem, MemoryItem, RetrievalToken, MemoryLabel]:
    label1 = make_label(
        purposes=("scheduling", "health"),
        tools=("shared",),
        sensitivity=Sensitivity.SENSITIVE,
        expires_at=80,
    )
    label2 = make_label(
        purposes=("scheduling",), tools=("shared",), sensitivity=Sensitivity.HEALTH_SENSITIVE, expires_at=70
    )
    p1 = make_item("p1", "Riverside Clinic", label=label1)
    p2 = make_item("p2", "Tuesday 10 AM", label=label2)
    store.commit(p1)
    store.commit(p2)
    context = make_context(tool="shared")
    token = issuer.issue(context, 50.0, store.policy_epoch)
    return p1, p2, token, label2


def test_admitted_derivation_is_no_broader(store: InMemoryStore, issuer: TokenIssuer) -> None:
    p1, p2, token, meet_label = _setup(store, issuer)
    proposal = DerivationProposal(
        "d1",
        "Tuesday 10 AM",
        ("p1", "p2"),
        meet_label,
        "extractive",
        {"p1": 1, "p2": 1},
        {"p1": p1.integrity_digest, "p2": p2.integrity_digest},
    )
    result = admit_derivation(store, issuer, [token], proposal, "assistant.pkg", 20.0)
    assert result.status == "ADMITTED"
    assert result.item is not None and result.item.state == ItemState.ADMITTED
    assert result.item.label.sensitivity == Sensitivity.HEALTH_SENSITIVE


def test_broadened_derivation_rejected(store: InMemoryStore, issuer: TokenIssuer) -> None:
    _p1, _p2, token, _meet_label = _setup(store, issuer)
    broad = make_label(purposes=("scheduling", "ads"), tools=("shared",), expires_at=70)
    proposal = DerivationProposal("d2", "Tuesday 10 AM", ("p1", "p2"), broad, "extractive")
    result = admit_derivation(store, issuer, [token], proposal, "assistant.pkg", 20.0)
    assert result.status == "REJECT"
    assert "broader" in result.reason


def test_unsupported_abstraction_quarantined(store: InMemoryStore, issuer: TokenIssuer) -> None:
    _p1, _p2, token, meet_label = _setup(store, issuer)
    proposal = DerivationProposal("d3", "invented diagnosis", ("p1", "p2"), meet_label, "abstractive")
    result = admit_derivation(store, issuer, [token], proposal, "assistant.pkg", 20.0)
    assert result.status == "QUARANTINED"
    assert result.item is not None and result.item.state == ItemState.QUARANTINED


def test_empty_composition_rejected(store: InMemoryStore, issuer: TokenIssuer) -> None:
    _, _, _, meet_label = _setup(store, issuer)
    proposal = DerivationProposal("d4", "Tuesday 10 AM", ("p1", "p2"), meet_label, "extractive")
    result = admit_derivation(store, issuer, [], proposal, "assistant.pkg", 20.0)
    assert result.status == "REJECT"
    assert "composition" in result.reason


def test_composition_context_mismatch_rejected(store: InMemoryStore, issuer: TokenIssuer) -> None:
    _, _, _, meet_label = _setup(store, issuer)
    scheduling = issuer.issue(make_context(tool="shared", purpose="scheduling"), 50.0, store.policy_epoch)
    health = issuer.issue(make_context(tool="shared", purpose="health"), 50.0, store.policy_epoch)
    proposal = DerivationProposal("d5", "Tuesday 10 AM", ("p1", "p2"), meet_label, "extractive")
    result = admit_derivation(store, issuer, [scheduling, health], proposal, "assistant.pkg", 20.0)
    assert result.status == "REJECT"
    assert "composition" in result.reason


def test_missing_parent_rejected(store: InMemoryStore, issuer: TokenIssuer) -> None:
    _, _, token, meet_label = _setup(store, issuer)
    proposal = DerivationProposal("d7", "Tuesday 10 AM", ("p1", "ghost"), meet_label, "extractive")
    result = admit_derivation(store, issuer, [token], proposal, "assistant.pkg", 20.0)
    assert result.status == "REJECT"
    assert "missing" in result.reason


def test_stale_parent_version_rejected(store: InMemoryStore, issuer: TokenIssuer) -> None:
    p1, p2, token, meet_label = _setup(store, issuer)
    proposal = DerivationProposal(
        "d8",
        "Tuesday 10 AM",
        ("p1", "p2"),
        meet_label,
        "extractive",
        {"p1": p1.version + 1, "p2": p2.version},
        {"p1": p1.integrity_digest, "p2": p2.integrity_digest},
    )
    result = admit_derivation(store, issuer, [token], proposal, "assistant.pkg", 20.0)
    assert result.status == "REJECT"
    assert "stale" in result.reason


def test_disjoint_tool_composition_quarantines(store: InMemoryStore, issuer: TokenIssuer) -> None:
    """Appendix scheduling example: two tokens, disjoint tools, empty required scope."""

    calendar = make_item(
        "calendar",
        "free Tuesday 10 AM",
        label=make_label(purposes=("scheduling",), apps=("assistant.pkg", "calendar.pkg"), tools=("calendar.read",), expires_at=80),
    )
    health = make_item(
        "clinic",
        "prefers Riverside Clinic",
        label=make_label(purposes=("health", "scheduling"), apps=("assistant.pkg", "health.pkg"), tools=("health.preference.read",), expires_at=70),
    )
    store.commit(calendar)
    store.commit(health)
    token_cal = issuer.issue(make_context(tool="calendar.read", purpose="scheduling"), 50.0, store.policy_epoch)
    token_health = issuer.issue(
        make_context(tool="health.preference.read", purpose="scheduling"), 50.0, store.policy_epoch
    )
    meet = make_label(
        purposes=("scheduling",),
        apps=("assistant.pkg",),
        tools=(),
        consumers=("primary_assistant",),
        expires_at=70,
    )
    proposal = DerivationProposal("d6", "Tuesday 10 AM", ("calendar", "clinic"), meet, "extractive")
    result = admit_derivation(
        store, issuer, [token_cal, token_health], proposal, "assistant.pkg", 20.0
    )
    assert result.status == "QUARANTINED"
    assert "empty required scope" in result.reason
