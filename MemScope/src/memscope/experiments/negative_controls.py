"""Negative controls from paper Section 11.6 (``experiments.tex``).

Each control deliberately breaks one assumption and shows that the corresponding
guarantee fails, making the guarantee's boundary visible. For every control we
also run the MemScope-mediated path and check the guarantee holds there. Output
is controlled synthetic evidence only; it is never a paper result.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..data.schemas import (
    DerivationProposal,
    MemoryItem,
    MemoryLabel,
    Provenance,
    RetrievalToken,
    Sensitivity,
    TaskContext,
)
from ..data.synthetic import (
    MutableClock,
    SyntheticScenario,
    WorkloadConfig,
    generate_scaled_scenario,
)
from ..methods.derivation import admit_derivation
from ..methods.integrity import content_digest
from ..methods.retrieval import MemScopeService, RetrievalDenied
from ..methods.store import InMemoryStore
from ..methods.tokens import TokenError, TokenIssuer
from ..methods.writes import build_item
from ..models.attribution import (
    AlwaysAcceptVerifier,
    AttributionVerifier,
    ExtractiveAttributionVerifier,
)
from ..models.ranking import LexicalRanker

_SIGNING_KEY = b"memscope-synthetic-key-material"
_CONTROL_NAMES = (
    "shadow_cache",
    "stale_token_replay",
    "always_accept_verifier",
    "authorized_copy_after_release",
)


def _scenario(seed: int, apps: int, topics_per_app: int, decoys_per_topic: int) -> SyntheticScenario:
    return generate_scaled_scenario(
        WorkloadConfig(seed=seed, apps=apps, topics_per_app=topics_per_app, decoys_per_topic=decoys_per_topic)
    )


def _prepare(scenario: SyntheticScenario) -> tuple[MutableClock, InMemoryStore, TokenIssuer, MemScopeService]:
    clock = MutableClock(scenario.now)
    store = InMemoryStore()
    for item in scenario.items:
        store.commit(item)
    issuer = TokenIssuer(_SIGNING_KEY)
    service = MemScopeService(store, issuer, clock=clock)
    return clock, store, issuer, service


def _issue(issuer: TokenIssuer, store: InMemoryStore, context: TaskContext, expires_at: float) -> RetrievalToken:
    return issuer.issue(
        context,
        expires_at=expires_at,
        policy_epoch=store.policy_epoch,
        permitted_tools=frozenset({context.tool_id}),
    )


def _shadow_cache(seeds: Sequence[int], apps: int, topics_per_app: int, decoys_per_topic: int) -> dict[str, Any]:
    mediated_returned = 0
    control_returned = 0
    for seed in seeds:
        scenario = _scenario(seed, apps, topics_per_app, decoys_per_topic)
        _, store, issuer, service = _prepare(scenario)
        ranker = LexicalRanker()
        for query in scenario.queries:
            token = _issue(issuer, store, query.context, scenario.now + 50.0)
            retrieval = service.retrieve(
                token, query.text, query.k, query.context.app_id, (query.context.tool_id,)
            )
            unauthorized = set(query.unauthorized_ids)
            mediated_returned += len({item.item_id for item in retrieval.items} & unauthorized)
            cached = ranker.rank(query.text, list(scenario.items), query.k)
            control_returned += len({item.item_id for item in cached} & unauthorized)
    return {
        "assumption_broken": "all memory access is mediated by MemScope",
        "guarantee": "purpose/tool isolation",
        "mediated_unauthorized_returned": mediated_returned,
        "control_unauthorized_returned": control_returned,
        "control_defeats_guarantee": control_returned > mediated_returned,
        "mediated_guarantee_holds": mediated_returned == 0,
    }


def _stale_token_replay(seeds: Sequence[int], apps: int, topics_per_app: int, decoys_per_topic: int) -> dict[str, Any]:
    mediated_denied = True
    mediated_expired_denied = True
    mediated_replay_denied = True
    control_stale_epoch_accepted = False
    control_expired_accepted = False
    control_replay_accepted = False
    for seed in seeds:
        scenario = _scenario(seed, apps, topics_per_app, decoys_per_topic)
        _, store, issuer, service = _prepare(scenario)
        context = scenario.queries[0].context
        tool_chain = (context.tool_id,)

        stale = _issue(issuer, store, context, scenario.now + 50.0)
        store.increment_epoch()
        try:
            service.retrieve(stale, scenario.queries[0].text, scenario.queries[0].k, context.app_id, tool_chain)
            mediated_denied = False
        except RetrievalDenied:
            pass
        try:
            issuer.verify(stale, context.app_id, tool_chain, scenario.now, current_epoch=stale.policy_epoch)
            control_stale_epoch_accepted = True
        except TokenError:
            pass

        expired = _issue(issuer, store, context, scenario.now + 10.0)
        try:
            issuer.verify(
                expired, context.app_id, tool_chain, scenario.now + 20.0, current_epoch=expired.policy_epoch
            )
        except TokenError:
            pass
        else:
            mediated_expired_denied = False
        try:
            issuer.verify(
                expired, context.app_id, tool_chain, expired.issued_at, current_epoch=expired.policy_epoch
            )
            control_expired_accepted = True
        except TokenError:
            pass

        one_shot = issuer.issue(
            context, expires_at=scenario.now + 50.0, policy_epoch=store.policy_epoch, one_shot=True
        )
        issuer.verify(one_shot, context.app_id, tool_chain, scenario.now, current_epoch=store.policy_epoch)
        try:
            issuer.verify(
                one_shot, context.app_id, tool_chain, scenario.now, current_epoch=store.policy_epoch
            )
        except TokenError:
            pass
        else:
            mediated_replay_denied = False
        fresh_issuer = TokenIssuer(_SIGNING_KEY)
        try:
            fresh_issuer.verify(one_shot, context.app_id, tool_chain, scenario.now, current_epoch=one_shot.policy_epoch)
            control_replay_accepted = True
        except TokenError:
            pass
    return {
        "assumption_broken": "clients never replay stale, expired, or already-used tokens",
        "guarantee": "epoch/expiry freshness and single-use tokens",
        "mediated_stale_denied": mediated_denied,
        "mediated_expired_denied": mediated_expired_denied,
        "mediated_replay_denied": mediated_replay_denied,
        "control_stale_epoch_accepted": control_stale_epoch_accepted,
        "control_expired_accepted": control_expired_accepted,
        "control_replay_accepted": control_replay_accepted,
        "control_defeats_guarantee": (
            control_stale_epoch_accepted and control_expired_accepted and control_replay_accepted
        ),
        "mediated_guarantee_holds": (
            mediated_denied and mediated_expired_denied and mediated_replay_denied
        ),
    }


def _derivation_parents(now: float) -> tuple[MemoryLabel, MemoryItem, MemoryItem]:
    app, consumer, purpose, tool = "app0.pkg", "consumer0", "scheduling", "calendar.read"
    label = MemoryLabel(
        purposes=frozenset({purpose}),
        apps=frozenset({app}),
        tools=frozenset({tool}),
        consumers=frozenset({consumer}),
        sensitivity=Sensitivity.PERSONAL,
        not_before=now - 50.0,
        expires_at=now + 500.0,
    )

    def make(item_id: str, payload: str) -> MemoryItem:
        provenance = Provenance(
            source_app=app,
            source_certificate_digest="reference-model",
            source_tool=tool,
            source_channel="synthetic_generator",
            acquisition_token_digest="synthetic-token-digest",
            created_at=now,
            content_digest=content_digest(payload),
        )
        return build_item(item_id, payload, label, provenance, namespace=consumer)

    return label, make("parent_alpha", "alpha beta gamma"), make("parent_beta", "delta beta gamma")


def _attack_cases(label: MemoryLabel) -> list[tuple[str, str, MemoryLabel]]:
    broader = MemoryLabel(
        purposes=label.purposes | {"personalized_ads"},
        apps=label.apps,
        tools=label.tools,
        consumers=label.consumers,
        sensitivity=label.sensitivity,
        not_before=label.not_before,
        expires_at=label.expires_at,
    )
    return [
        ("unsupported_epsilon", "epsilon", label),
        ("laundering_alpha", "alpha beta", broader),
    ]


def _admit_attack_cases(verifier: AttributionVerifier, label: MemoryLabel) -> int:
    now = 1000.0
    _, parent_a, parent_b = _derivation_parents(now)
    context = TaskContext("app0.pkg", "calendar.read", "consumer0", "scheduling", now, "n_neg")
    store = InMemoryStore()
    store.commit(parent_a)
    store.commit(parent_b)
    issuer = TokenIssuer(_SIGNING_KEY)
    admitted = 0
    for item_id, payload, proposed in _attack_cases(label):
        token = _issue(issuer, store, context, now + 100.0)
        proposal = DerivationProposal(
            item_id=f"derived_{item_id}",
            payload=payload,
            parent_ids=(parent_a.item_id, parent_b.item_id),
            proposed_label=proposed,
            transformation="extractive",
        )
        result = admit_derivation(store, issuer, [token], proposal, "app0.pkg", now, verifier=verifier)
        if result.status == "ADMITTED":
            admitted += 1
    return admitted


def _always_accept_verifier() -> dict[str, Any]:
    now = 1000.0
    label, _, _ = _derivation_parents(now)
    cases = len(_attack_cases(label))
    mediated_admitted = _admit_attack_cases(ExtractiveAttributionVerifier(), label)
    control_admitted = _admit_attack_cases(AlwaysAcceptVerifier(), label)
    mediated_far = mediated_admitted / cases if cases else 0.0
    control_far = control_admitted / cases if cases else 0.0
    return {
        "assumption_broken": "the attribution verifier is correct",
        "guarantee": "derivation soundness (no unsupported or laundering admission)",
        "attack_cases": cases,
        "mediated_admitted": mediated_admitted,
        "control_admitted": control_admitted,
        "mediated_false_acceptance_rate": mediated_far,
        "control_false_acceptance_rate": control_far,
        "control_defeats_guarantee": control_far > mediated_far,
        "mediated_guarantee_holds": mediated_far == 0.0,
    }


def _authorized_copy_after_release(
    seeds: Sequence[int], apps: int, topics_per_app: int, decoys_per_topic: int
) -> dict[str, Any]:
    seed = seeds[0]
    scenario = _scenario(seed, apps, topics_per_app, decoys_per_topic)
    _, store, issuer, service = _prepare(scenario)
    query = scenario.queries[0]
    token = _issue(issuer, store, query.context, scenario.now + 50.0)
    retrieval = service.retrieve(
        token, query.text, query.k, query.context.app_id, (query.context.tool_id,)
    )
    readable = len(retrieval.items) > 0 and all(
        isinstance(item.payload, str) and item.payload for item in retrieval.items
    )
    return {
        "assumption_broken": "an authorized tool does not copy plaintext after receipt",
        "guarantee": "confidentiality after authorized release (explicitly out of scope)",
        "authorized_items_released": len(retrieval.items),
        "plaintext_readable_after_release": readable,
        "post_release_exfiltration_possible": readable,
        "post_release_dlp_enforced": False,
        "control_defeats_guarantee": readable,
        "mediated_guarantee_holds": False,
        "boundary": (
            "MemScope enforces policy at release time; it does not and cannot prevent an "
            "authorized recipient from copying plaintext afterwards."
        ),
    }


def run_negative_controls(
    *,
    seeds: Sequence[int],
    apps: int,
    topics_per_app: int,
    decoys_per_topic: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run the four Section 11.6 negative controls and report the boundaries."""

    controls = {
        "shadow_cache": _shadow_cache(seeds, apps, topics_per_app, decoys_per_topic),
        "stale_token_replay": _stale_token_replay(seeds, apps, topics_per_app, decoys_per_topic),
        "always_accept_verifier": _always_accept_verifier(),
        "authorized_copy_after_release": _authorized_copy_after_release(
            seeds, apps, topics_per_app, decoys_per_topic
        ),
    }
    summary = {
        "controls": len(controls),
        "controls_defeating_their_guarantee": sum(
            1 for control in controls.values() if control["control_defeats_guarantee"]
        ),
        "mediated_guarantees_held": sum(
            1 for control in controls.values() if control["mediated_guarantee_holds"]
        ),
        "out_of_scope_by_design": ["authorized_copy_after_release"],
    }
    aggregate: dict[str, Any] = {
        "source": "paper Section 11.6 negative controls",
        "interpretation": (
            "Each control breaks one assumption; control_defeats_guarantee=True makes the "
            "guarantee's boundary visible, and mediated_guarantee_holds records whether the "
            "MemScope-mediated path maintains the guarantee."
        ),
        "summary": summary,
        **controls,
    }
    rows = [
        {
            "rq": "negative_controls",
            "control": name,
            "control_defeats_guarantee": aggregate[name]["control_defeats_guarantee"],
            "mediated_guarantee_holds": aggregate[name]["mediated_guarantee_holds"],
            "guarantee": aggregate[name]["guarantee"],
        }
        for name in _CONTROL_NAMES
    ]
    return aggregate, rows
