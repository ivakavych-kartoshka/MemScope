"""Offline synthetic RQ1-RQ6 harness over the scaled multi-app workload.

Every number produced here is a *controlled synthetic* measurement used to
exercise the reference pipeline; it is never a paper result. RQ5 (on-device
latency/energy/thermal cost) is explicitly reported as ``not_measured_offline``
because it requires the provisioned AOSP devices described in
``docs/ec2_experiment_guide.md``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..baselines.simple import NamespaceBaseline, PromptOnlyBaseline, UnscopedBaseline
from ..data.schemas import (
    DerivationProposal,
    MemoryItem,
    MemoryLabel,
    Provenance,
    QueryEvaluation,
    RetrievalToken,
    Sensitivity,
    TaskContext,
)
from ..data.synthetic import (
    SYNTHETIC_NOTICE,
    MutableClock,
    SyntheticScenario,
    WorkloadConfig,
    generate_scaled_scenario,
)
from ..methods.compaction import policy_aware_compact
from ..methods.derivation import admit_derivation
from ..methods.integrity import content_digest
from ..methods.retrieval import MemScopeService, RetrievalDenied
from ..methods.store import InMemoryStore
from ..methods.tokens import TokenIssuer
from ..methods.writes import build_item
from ..metrics.core import (
    evaluate_queries,
    safety_critical_survival,
)
from ..metrics.statistics import bootstrap_median_ci, wilson_interval
from ..models.attribution import ExtractiveAttributionVerifier
from ..utils.io import write_json, write_jsonl
from .common import run_metadata, validate_config, write_run_manifest

_SIGNING_KEY = b"memscope-synthetic-key-material"
RQ5_STATUS = "not_measured_offline"
RQ5_DETAIL = (
    "on-device latency/energy/thermal cost requires the provisioned AOSP devices; "
    "see docs/ec2_experiment_guide.md"
)
_ENFORCEMENT_METHODS = ("memscope", "unscoped", "namespace", "prompt_only")
_INTERPRETATION = (
    "Controlled synthetic harness output for pipeline validation; not an empirical paper result."
)


@dataclass(frozen=True)
class HarnessConfig:
    seeds: tuple[int, ...]
    apps: int
    topics_per_app: int
    decoys_per_topic: int
    k: int
    k_sweep: tuple[int, ...]
    byte_budget: int


def _harness_config(config: Mapping[str, Any]) -> HarnessConfig:
    section = dict(config.get("harness", {}))
    k = int(config["retrieval"]["k"])
    run_section = config.get("run", {})
    raw_seeds = section.get("seeds", run_section.get("seeds", [config["run"]["seed"]]))
    seeds = tuple(int(seed) for seed in raw_seeds)
    if not seeds or any(seed < 0 for seed in seeds):
        raise ValueError("harness.seeds must be non-empty non-negative integers")
    apps = int(section.get("apps", 3))
    topics_per_app = int(section.get("topics_per_app", 4))
    decoys_per_topic = int(section.get("decoys_per_topic", 2))
    k_sweep = tuple(int(value) for value in section.get("k_sweep", [k]))
    if any(value < 1 for value in k_sweep):
        raise ValueError("harness.k_sweep values must be positive")
    byte_budget = int(section.get("byte_budget", 2048))
    if byte_budget < 1:
        raise ValueError("harness.byte_budget must be positive")
    WorkloadConfig(
        seed=seeds[0],
        apps=apps,
        topics_per_app=topics_per_app,
        decoys_per_topic=decoys_per_topic,
    )
    return HarnessConfig(
        seeds=seeds,
        apps=apps,
        topics_per_app=topics_per_app,
        decoys_per_topic=decoys_per_topic,
        k=k,
        k_sweep=k_sweep,
        byte_budget=byte_budget,
    )


def _workload(seed: int, cfg: HarnessConfig) -> SyntheticScenario:
    return generate_scaled_scenario(
        WorkloadConfig(
            seed=seed,
            apps=cfg.apps,
            topics_per_app=cfg.topics_per_app,
            decoys_per_topic=cfg.decoys_per_topic,
        )
    )


def _prepare(
    scenario: SyntheticScenario,
) -> tuple[MutableClock, InMemoryStore, TokenIssuer, MemScopeService]:
    clock = MutableClock(scenario.now)
    store = InMemoryStore()
    for item in scenario.items:
        store.commit(item)
    issuer = TokenIssuer(_SIGNING_KEY)
    service = MemScopeService(store, issuer, clock=clock)
    return clock, store, issuer, service


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _issue(
    issuer: TokenIssuer, store: InMemoryStore, context: TaskContext, expires_at: float
) -> RetrievalToken:
    return issuer.issue(
        context,
        expires_at=expires_at,
        policy_epoch=store.policy_epoch,
        permitted_tools=frozenset({context.tool_id}),
    )


def _rq1_enforcement(
    cfg: HarnessConfig,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    oosr: dict[str, list[float]] = {name: [] for name in _ENFORCEMENT_METHODS}
    violations = dict.fromkeys(_ENFORCEMENT_METHODS, 0)
    yield_total = dict.fromkeys(_ENFORCEMENT_METHODS, 0)
    queries_with_violation = dict.fromkeys(_ENFORCEMENT_METHODS, 0)
    rows: list[dict[str, Any]] = []
    total_queries = 0

    for seed in cfg.seeds:
        scenario = _workload(seed, cfg)
        _, store, issuer, service = _prepare(scenario)
        baselines = {
            "unscoped": UnscopedBaseline(),
            "namespace": NamespaceBaseline(),
            "prompt_only": PromptOnlyBaseline(),
        }
        evaluations: dict[str, list[QueryEvaluation]] = {name: [] for name in _ENFORCEMENT_METHODS}
        for query in scenario.queries:
            token = _issue(issuer, store, query.context, scenario.now + 50.0)
            retrieval = service.retrieve(
                token, query.text, query.k, query.context.app_id, (query.context.tool_id,)
            )
            evaluations["memscope"].append(
                QueryEvaluation(
                    query.query_id,
                    tuple(item.item_id for item in retrieval.items),
                    query.entitled_ids,
                    query.unauthorized_ids,
                )
            )
            for name, baseline in baselines.items():
                selected = baseline.retrieve(query.text, scenario.items, query.context, query.k)
                evaluations[name].append(
                    QueryEvaluation(
                        query.query_id,
                        tuple(item.item_id for item in selected),
                        query.entitled_ids,
                        query.unauthorized_ids,
                    )
                )
        total_queries += len(scenario.queries)
        for name in _ENFORCEMENT_METHODS:
            summary = evaluate_queries(evaluations[name])
            oosr[name].append(summary["out_of_scope_retrieval_rate"])
            leaked = sum(
                1
                for row in evaluations[name]
                if set(row.returned_ids) & set(row.unauthorized_ids)
            )
            queries_with_violation[name] += leaked
            violations[name] += int(summary["authorization_violations"])
            yield_total[name] += int(summary["unique_record_extraction_yield"])
            rows.append(
                {
                    "rq": "RQ1",
                    "seed": seed,
                    "method": name,
                    "out_of_scope_retrieval_rate": summary["out_of_scope_retrieval_rate"],
                    "authorization_violations": summary["authorization_violations"],
                    "unique_record_extraction_yield": summary["unique_record_extraction_yield"],
                    "entitled_recall_at_k": summary["entitled_recall_at_k"],
                }
            )

    aggregate = {
        name: {
            "out_of_scope_retrieval_rate_mean": _mean(oosr[name]),
            "authorization_violations_total": violations[name],
            "unique_record_extraction_yield_total": yield_total[name],
            "queries_with_violation": queries_with_violation[name],
            "queries_with_violation_rate": (
                queries_with_violation[name] / total_queries if total_queries else 0.0
            ),
            "queries_with_violation_rate_ci95": list(
                wilson_interval(queries_with_violation[name], total_queries)
            )
            if total_queries
            else [0.0, 0.0],
        }
        for name in _ENFORCEMENT_METHODS
    }
    return aggregate, rows, total_queries


def _rq2_utility(cfg: HarnessConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    recalls: dict[int, list[float]] = {k: [] for k in cfg.k_sweep}
    rows: list[dict[str, Any]] = []
    for seed in cfg.seeds:
        scenario = _workload(seed, cfg)
        _, store, issuer, service = _prepare(scenario)
        for k in cfg.k_sweep:
            evaluations: list[QueryEvaluation] = []
            for query in scenario.queries:
                token = _issue(issuer, store, query.context, scenario.now + 50.0)
                retrieval = service.retrieve(
                    token, query.text, k, query.context.app_id, (query.context.tool_id,)
                )
                evaluations.append(
                    QueryEvaluation(
                        query.query_id,
                        tuple(item.item_id for item in retrieval.items),
                        query.entitled_ids,
                        query.unauthorized_ids,
                    )
                )
            recall = evaluate_queries(evaluations)["entitled_recall_at_k"]
            recalls[k].append(recall)
            rows.append({"rq": "RQ2", "seed": seed, "k": k, "entitled_recall_at_k": recall})
    aggregate = {
        str(k): {
            "entitled_recall_at_k_mean": _mean(values),
            "entitled_recall_at_k_ci95": list(bootstrap_median_ci(values, seed=cfg.seeds[0] + k)),
        }
        for k, values in recalls.items()
    }
    return aggregate, rows


def _derivation_parents(
    app: str, consumer: str, purpose: str, tool: str, now: float
) -> tuple[MemoryLabel, MemoryItem, MemoryItem]:
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


def _rq3_derivation() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    now = 1000.0
    app, consumer, purpose, tool = "app0.pkg", "consumer0", "scheduling", "calendar.read"
    label, parent_a, parent_b = _derivation_parents(app, consumer, purpose, tool, now)
    context = TaskContext(app, tool, consumer, purpose, now, "n_deriv")
    verifier = ExtractiveAttributionVerifier()

    broader = MemoryLabel(
        purposes=frozenset({purpose, "personalized_ads"}),
        apps=label.apps,
        tools=label.tools,
        consumers=label.consumers,
        sensitivity=label.sensitivity,
        not_before=label.not_before,
        expires_at=label.expires_at,
    )

    cases = [
        ("faithful_alpha", "alpha beta", "extractive", label, "faithful"),
        ("faithful_gamma", "gamma", "extractive", label, "faithful"),
        ("unsupported_epsilon", "epsilon", "extractive", label, "unsupported"),
        ("unsupported_zeta", "zeta", "extractive", label, "unsupported"),
        ("laundering_alpha", "alpha beta", "extractive", broader, "laundering"),
        ("laundering_gamma", "gamma", "extractive", broader, "laundering"),
    ]

    store = InMemoryStore()
    store.commit(parent_a)
    store.commit(parent_b)
    issuer = TokenIssuer(_SIGNING_KEY)

    counts = {"faithful": 0, "unsupported": 0, "laundering": 0}
    admitted = {"faithful": 0, "unsupported": 0, "laundering": 0}
    rows: list[dict[str, Any]] = []
    for item_id, payload, transformation, proposed_label, kind in cases:
        token = _issue(issuer, store, context, now + 100.0)
        proposal = DerivationProposal(
            item_id=f"derived_{item_id}",
            payload=payload,
            parent_ids=(parent_a.item_id, parent_b.item_id),
            proposed_label=proposed_label,
            transformation=transformation,
        )
        result = admit_derivation(
            store, issuer, [token], proposal, app, now, verifier=verifier
        )
        counts[kind] += 1
        if result.status == "ADMITTED":
            admitted[kind] += 1
        rows.append(
            {
                "rq": "RQ3",
                "case": item_id,
                "kind": kind,
                "status": result.status,
                "reason": result.reason,
            }
        )

    attack_cases = counts["unsupported"] + counts["laundering"]
    attack_admitted = admitted["unsupported"] + admitted["laundering"]
    aggregate = {
        "cases": {kind: counts[kind] for kind in counts},
        "admitted": {kind: admitted[kind] for kind in admitted},
        "false_acceptance_rate": attack_admitted / attack_cases if attack_cases else 0.0,
        "false_rejection_rate": (
            (counts["faithful"] - admitted["faithful"]) / counts["faithful"]
            if counts["faithful"]
            else 0.0
        ),
    }
    return aggregate, rows


def _rq4_lifecycle(cfg: HarnessConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    post_expiry_releases = 0
    epoch_change_denials = 0
    rows: list[dict[str, Any]] = []
    for seed in cfg.seeds:
        scenario = _workload(seed, cfg)
        clock, store, issuer, service = _prepare(scenario)

        release_now = scenario.now + 1_000.0
        clock.now = release_now
        released = 0
        for query in scenario.queries:
            token = _issue(issuer, store, query.context, release_now + 1_000_000.0)
            retrieval = service.retrieve(
                token, query.text, query.k, query.context.app_id, (query.context.tool_id,)
            )
            released += sum(
                1 for item in retrieval.items if item.label.expires_at <= release_now
            )
        post_expiry_releases += released

        clock.now = scenario.now
        first = scenario.queries[0]
        token = _issue(issuer, store, first.context, scenario.now + 50.0)
        store.increment_epoch()
        denied = 0
        try:
            service.retrieve(
                token, first.text, first.k, first.context.app_id, (first.context.tool_id,)
            )
        except RetrievalDenied:
            denied = 1
        epoch_change_denials += denied
        rows.append(
            {
                "rq": "RQ4",
                "seed": seed,
                "post_expiry_releases": released,
                "epoch_change_denials": denied,
            }
        )
    return {
        "post_expiry_releases_total": post_expiry_releases,
        "epoch_change_denials": epoch_change_denials,
        "epoch_change_trials": len(cfg.seeds),
    }, rows


def _policy_blind_retain(items: Sequence[MemoryItem], budget: int, now: float) -> list[str]:
    """Policy-blind control eviction (descending ID); not a paper baseline."""

    live = [item for item in items if item.label.expires_at > now]
    live.sort(key=lambda item: item.item_id, reverse=True)
    used = sum(item.size_bytes for item in live)
    removed: set[str] = set()
    for item in live:
        if used <= budget:
            break
        removed.add(item.item_id)
        used -= item.size_bytes
    return [item.item_id for item in live if item.item_id not in removed]


def _rq6_retention(cfg: HarnessConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    policy_survival: list[float] = []
    control_survival: list[float] = []
    rows: list[dict[str, Any]] = []
    for seed in cfg.seeds:
        scenario = _workload(seed, cfg)
        items = list(scenario.items)
        safety = [item.item_id for item in items if item.safety_critical]
        total_bytes = sum(item.size_bytes for item in items)
        pinned_bytes = sum(item.size_bytes for item in items if item.hard_pinned)
        budget = max(cfg.byte_budget, pinned_bytes)
        if budget >= total_bytes:
            budget = max(pinned_bytes, total_bytes // 2)

        store = InMemoryStore()
        for item in items:
            store.commit(item)
        report = policy_aware_compact(store, budget, scenario.now)
        policy_value = safety_critical_survival(report.retained, safety)

        control_ids = _policy_blind_retain(items, budget, scenario.now)
        control_value = safety_critical_survival(control_ids, safety)

        policy_survival.append(policy_value)
        control_survival.append(control_value)
        rows.append(
            {
                "rq": "RQ6",
                "seed": seed,
                "byte_budget": budget,
                "safety_items": len(safety),
                "policy_aware_safety_survival": policy_value,
                "policy_blind_safety_survival": control_value,
            }
        )
    return {
        "policy_aware_safety_survival_mean": _mean(policy_survival),
        "policy_blind_safety_survival_mean": _mean(control_survival),
    }, rows


def run_harness(config: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    """Run RQ1-RQ6 over the synthetic workload; RQ5 is a labeled non-measurement."""

    validate_config(config)
    if config["run"]["mode"] != "synthetic":
        raise NotImplementedError(
            "the RQ harness runs on synthetic workloads; real RQs require the "
            "manually provisioned benchmarks and AOSP devices"
        )
    cfg = _harness_config(config)

    rq1, rows1, _ = _rq1_enforcement(cfg)
    rq2, rows2 = _rq2_utility(cfg)
    rq3, rows3 = _rq3_derivation()
    rq4, rows4 = _rq4_lifecycle(cfg)
    rq6, rows6 = _rq6_retention(cfg)

    result: dict[str, Any] = {
        "notice": SYNTHETIC_NOTICE,
        "paper_result_claimed": False,
        "metadata": run_metadata(config, "harness"),
        "harness_config": asdict(cfg),
        "rq1_enforcement": rq1,
        "rq2_utility": rq2,
        "rq3_derivation": rq3,
        "rq4_lifecycle": rq4,
        "rq5_mobile_cost": {"status": RQ5_STATUS, "detail": RQ5_DETAIL},
        "rq6_retention": rq6,
        "interpretation": _INTERPRETATION,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "resolved_config.json", dict(config))
    write_json(output_dir / "harness_summary.json", result)
    write_jsonl(output_dir / "harness_runs.jsonl", [*rows1, *rows2, *rows3, *rows4, *rows6])
    write_run_manifest(
        output_dir,
        config,
        "harness",
        ["resolved_config.json", "harness_summary.json", "harness_runs.jsonl", "run_manifest.json"],
    )
    return result
