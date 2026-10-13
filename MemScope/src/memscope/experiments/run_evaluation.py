"""Matched synthetic evaluation and real-data preflight."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..baselines.simple import NamespaceBaseline, PromptOnlyBaseline, UnscopedBaseline
from ..data.adapters import JsonlBenchmarkAdapter
from ..data.schemas import QueryEvaluation, as_jsonable
from ..data.synthetic import SYNTHETIC_NOTICE, MutableClock, generate_synthetic_scenario
from ..methods.retrieval import MemScopeService
from ..methods.store import InMemoryStore
from ..methods.tokens import TokenIssuer
from ..metrics.core import evaluate_queries
from ..utils.io import write_json, write_jsonl
from .common import run_metadata, validate_config


def run_evaluation(config: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    validate_config(config)
    if config["run"]["mode"] != "synthetic":
        adapter = JsonlBenchmarkAdapter(
            str(config["data"]["name"]), Path(str(config["data"]["root"]))
        )
        adapter.validate()
        raise NotImplementedError(
            "real benchmark files passed schema preflight, but benchmark-specific policy annotations "
            "and output scorer must be author-verified before execution"
        )
    seed = int(config["run"]["seed"])
    scenario = generate_synthetic_scenario(seed)
    clock = MutableClock(scenario.now)
    store = InMemoryStore()
    for item in scenario.items:
        store.commit(item)
    issuer = TokenIssuer(b"memscope-synthetic-key-material")
    service = MemScopeService(store, issuer, clock=clock)

    rows: list[dict[str, Any]] = []
    by_method: dict[str, list[QueryEvaluation]] = {
        "memscope": [],
        "unscoped": [],
        "namespace": [],
        "prompt_only": [],
    }
    baselines = [UnscopedBaseline(), NamespaceBaseline(), PromptOnlyBaseline()]
    for query in scenario.queries:
        token = issuer.issue(
            query.context,
            expires_at=scenario.now + 50.0,
            policy_epoch=store.policy_epoch,
            permitted_tools=frozenset({query.context.tool_id}),
        )
        retrieval = service.retrieve(
            token,
            query.text,
            int(config["retrieval"]["k"]),
            query.context.app_id,
            (query.context.tool_id,),
        )
        returned = tuple(item.item_id for item in retrieval.items)
        evaluation = QueryEvaluation(
            query.query_id, returned, query.entitled_ids, query.unauthorized_ids, 0.0
        )
        by_method["memscope"].append(evaluation)
        rows.append(
            {
                "notice": SYNTHETIC_NOTICE,
                "method": "memscope",
                "query_id": query.query_id,
                "returned_ids": list(returned),
                "entitled_ids": sorted(query.entitled_ids),
                "unauthorized_ids": sorted(query.unauthorized_ids),
                "candidate_count": retrieval.candidate_count,
                "authorized_count": retrieval.authorized_count,
            }
        )
        for baseline in baselines:
            selected = baseline.retrieve(
                query.text, scenario.items, query.context, int(config["retrieval"]["k"])
            )
            baseline_returned = tuple(item.item_id for item in selected)
            by_method[baseline.name].append(
                QueryEvaluation(
                    query.query_id,
                    baseline_returned,
                    query.entitled_ids,
                    query.unauthorized_ids,
                    0.0,
                )
            )
            rows.append(
                {
                    "notice": SYNTHETIC_NOTICE,
                    "method": baseline.name,
                    "query_id": query.query_id,
                    "returned_ids": list(baseline_returned),
                    "entitled_ids": sorted(query.entitled_ids),
                    "unauthorized_ids": sorted(query.unauthorized_ids),
                }
            )

    metrics = {name: evaluate_queries(records) for name, records in by_method.items()}
    result = {
        "notice": SYNTHETIC_NOTICE,
        "paper_result_claimed": False,
        "metadata": run_metadata(config, "evaluate"),
        "metrics": metrics,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "resolved_config.json", dict(config))
    write_jsonl(output_dir / "query_results.jsonl", rows)
    write_json(output_dir / "metrics.json", result)
    write_json(
        output_dir / "audit_events.json",
        {"notice": SYNTHETIC_NOTICE, "events": [as_jsonable(x) for x in store.audit_events()]},
    )
    return result
