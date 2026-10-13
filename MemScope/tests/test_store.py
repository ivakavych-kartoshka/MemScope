import pytest
from conftest import make_context, make_item

from memscope.data.schemas import AuditEvent
from memscope.methods.retrieval import MemScopeService
from memscope.methods.store import AuditPartitionFull, InMemoryStore
from memscope.methods.tokens import TokenIssuer


def _event(token_id: str = "t") -> AuditEvent:
    return AuditEvent(
        timestamp=20.0,
        token_id=token_id,
        app_id="assistant.pkg",
        purpose="scheduling",
        tool_id="calendar.read",
        item_ids=(),
        decision="ALLOW",
        bytes_returned=0,
        policy_epoch=1,
    )


def test_audit_partition_full_fails_explicitly() -> None:
    store = InMemoryStore(audit_capacity=2)
    store.append_audit(_event("a"))
    store.append_audit(_event("b"))
    with pytest.raises(AuditPartitionFull, match="full"):
        store.append_audit(_event("c"))
    assert len(store.audit_events()) == 2


def test_audit_partition_full_blocks_release(issuer: TokenIssuer) -> None:
    """A full audit partition must fail closed before any plaintext is released."""

    store = InMemoryStore(audit_capacity=0)
    store.commit(make_item("m1", "calendar meeting"))
    token = issuer.issue(make_context(), 30.0, store.policy_epoch)
    service = MemScopeService(store, issuer, clock=lambda: 20.0)
    with pytest.raises(AuditPartitionFull):
        service.retrieve(token, "calendar", 5, "assistant.pkg", ("calendar.read",))
    assert store.audit_events() == ()
