"""MemScope Algorithm 2: conservative source-cited derived-memory admission.

The derivation path supports *multi-token composition* under a single trusted
composition principal. A composition context is the tuple
``(app_id, consumer_id, purpose)`` that every presented token must share. Each
cited parent need only be authorized by *some* token in the set, but the derived
label is still the meet of every cited parent, so composition can never widen
policy (see Theorem 2). When ``len(tokens) == 1`` this reduces to single-token
admission.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from ..data.schemas import (
    AdmissionResult,
    DerivationProposal,
    ItemState,
    MemoryItem,
    Provenance,
    RetrievalToken,
    TaskContext,
)
from ..models.attribution import AttributionVerifier, ExtractiveAttributionVerifier
from .integrity import content_digest
from .policy import authorize, empty_required_scope, label_no_more_permissive, meet_labels
from .store import InMemoryStore
from .tokens import TokenError, TokenIssuer
from .writes import build_item


def _composition_context(
    contexts: Sequence[TaskContext],
) -> TaskContext:
    """Return the shared composition principal or raise ``TokenError``.

    All tokens in a composition must name the same caller app, consumer, and
    purpose. This prevents an agent from stitching together views that belong to
    unrelated tasks or principals.
    """

    first = contexts[0]
    for context in contexts[1:]:
        if (
            context.app_id != first.app_id
            or context.consumer_id != first.consumer_id
            or context.purpose != first.purpose
        ):
            raise TokenError("composition context mismatch across tokens")
    return first


def admit_derivation(
    store: InMemoryStore,
    issuer: TokenIssuer,
    tokens: Sequence[RetrievalToken],
    proposal: DerivationProposal,
    binder_caller: str,
    now: float,
    verifier: AttributionVerifier | None = None,
) -> AdmissionResult:
    """Implement Algorithm 2 and Equation (9) with multi-token composition.

    Deterministic label checks establish non-widening. Attribution only decides
    admission versus quarantine and is never permitted to modify policy.
    """

    verifier = verifier or ExtractiveAttributionVerifier()
    if not tokens:
        return AdmissionResult("REJECT", None, "empty composition token set")
    if not proposal.parent_ids:
        return AdmissionResult("REJECT", None, "empty parent set")

    try:
        verified = [
            issuer.verify(
                token,
                binder_caller,
                (token.context.tool_id,),
                now,
                store.policy_epoch,
                consume=True,
            )
            for token in tokens
        ]
        composition = _composition_context(verified)
    except TokenError:
        return AdmissionResult("REJECT", None, "invalid token or composition context")

    epoch, parents = store.read_parents(proposal.parent_ids)
    if len(parents) != len(proposal.parent_ids):
        return AdmissionResult("REJECT", None, "one or more parents are missing")
    for parent in parents:
        visible = any(
            authorize(parent, context, now, token.expires_at)
            for context, token in zip(verified, tokens)
        )
        if not visible:
            return AdmissionResult(
                "REJECT", None, "parent is not visible to any composition token"
            )
        expected_version = proposal.expected_versions.get(parent.item_id, parent.version)
        expected_digest = proposal.expected_digests.get(parent.item_id, parent.integrity_digest)
        if parent.version != expected_version or parent.integrity_digest != expected_digest:
            return AdmissionResult("REJECT", None, "stale parent version or digest")

    try:
        meet = meet_labels([parent.label for parent in parents])
    except ValueError:
        return _commit_quarantine(
            store, issuer, tokens, composition, proposal, parents, now,
            "empty temporal intersection",
        )
    if not label_no_more_permissive(proposal.proposed_label, meet):
        return AdmissionResult("REJECT", None, "proposed label is broader than parent meet")
    if empty_required_scope(meet):
        return _commit_quarantine(
            store, issuer, tokens, composition, proposal, parents, now,
            "empty required scope intersection",
        )
    decision = verifier.verify(proposal.payload, parents, proposal.transformation)
    if decision.status != "supported":
        return _commit_quarantine(
            store, issuer, tokens, composition, proposal, parents, now,
            f"attribution {decision.status}: {decision.reason}",
        )
    if epoch != store.policy_epoch:
        return AdmissionResult("REJECT", None, "policy epoch changed during derivation")
    item = _derived_item(
        issuer, tokens, composition, proposal, parents, now, ItemState.ADMITTED
    )
    store.commit(item)
    return AdmissionResult("ADMITTED", item, "deterministic and attribution checks passed")


def _acquisition_digest(issuer: TokenIssuer, tokens: Sequence[RetrievalToken]) -> str:
    joined = "".join(sorted(issuer.digest(token) for token in tokens))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _derived_item(
    issuer: TokenIssuer,
    tokens: Sequence[RetrievalToken],
    composition: TaskContext,
    proposal: DerivationProposal,
    parents: Sequence[MemoryItem],
    now: float,
    state: ItemState,
) -> MemoryItem:
    provenance = Provenance(
        source_app=composition.app_id,
        source_certificate_digest="reference-model",
        source_tool=None,
        source_channel="derived",
        acquisition_token_digest=_acquisition_digest(issuer, tokens),
        created_at=now,
        parent_ids=tuple(parent.item_id for parent in parents),
        parent_digests=tuple(parent.integrity_digest for parent in parents),
        transformation=proposal.transformation,
        content_digest=content_digest(proposal.payload),
    )
    return build_item(
        proposal.item_id,
        proposal.payload,
        proposal.proposed_label,
        provenance,
        state=state,
    )


def _commit_quarantine(
    store: InMemoryStore,
    issuer: TokenIssuer,
    tokens: Sequence[RetrievalToken],
    composition: TaskContext,
    proposal: DerivationProposal,
    parents: Sequence[MemoryItem],
    now: float,
    reason: str,
) -> AdmissionResult:
    item = _derived_item(
        issuer, tokens, composition, proposal, parents, now, ItemState.QUARANTINED
    )
    store.commit(item)
    return AdmissionResult("QUARANTINED", item, reason)
