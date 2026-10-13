"""Direct observation writes and versioned correction helpers."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ..data.schemas import ItemState, MemoryItem, MemoryLabel, Provenance, RetrievalToken
from .integrity import content_digest, item_integrity_digest
from .store import InMemoryStore
from .tokens import TokenIssuer


def build_item(
    item_id: str,
    payload: str,
    label: MemoryLabel,
    provenance: Provenance,
    state: ItemState = ItemState.ADMITTED,
    **metadata: Any,
) -> MemoryItem:
    """Construct an integrity-bound reference item.

    Encryption is intentionally delegated to the Android adapter; this function
    must not be mistaken for a production ciphertext implementation.
    """

    provenance = replace(provenance, content_digest=content_digest(payload))
    digest = item_integrity_digest(item_id, payload, label, provenance, 1)
    return MemoryItem(
        item_id=item_id,
        payload=payload,
        label=label,
        provenance=provenance,
        integrity_digest=digest,
        state=state,
        **metadata,
    )


def put_observation(
    store: InMemoryStore,
    issuer: TokenIssuer,
    token: RetrievalToken,
    item_id: str,
    payload: str,
    label: MemoryLabel,
    source_certificate_digest: str,
    source_channel: str,
    now: float,
    namespace: str = "default",
    safety_critical: bool = False,
    hard_pinned: bool = False,
) -> MemoryItem:
    """Paper Section 7.3 direct write using an already policy-capped label."""

    context = issuer.verify(
        token,
        token.context.app_id,
        (token.context.tool_id,),
        now,
        store.policy_epoch,
        consume=False,
    )
    if context.app_id not in label.apps or context.purpose not in label.purposes:
        raise PermissionError("direct-write label does not include the active task scope")
    provenance = Provenance(
        source_app=context.app_id,
        source_certificate_digest=source_certificate_digest,
        source_tool=context.tool_id,
        source_channel=source_channel,
        acquisition_token_digest=issuer.digest(token),
        created_at=now,
        transformation="observation",
    )
    item = build_item(
        item_id,
        payload,
        label,
        provenance,
        namespace=namespace,
        safety_critical=safety_critical,
        hard_pinned=hard_pinned,
    )
    store.commit(item)
    return item
