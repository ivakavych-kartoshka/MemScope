"""Synthetic label-dimension ablation harness."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..data.schemas import ItemState, MemoryItem, QueryEvaluation, TaskContext
from ..data.synthetic import SYNTHETIC_NOTICE, generate_synthetic_scenario
from ..metrics.core import evaluate_queries
from ..models.ranking import LexicalRanker
from ..utils.io import write_json
from .common import run_metadata, validate_config, write_run_manifest


def run_ablation(config: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    """Execute controlled synthetic removal of each set-valued label coordinate."""

    validate_config(config)
    if config["run"]["mode"] != "synthetic":
        raise NotImplementedError("real ablations require the manually provisioned matched harness")
    scenario = generate_synthetic_scenario(int(config["run"]["seed"]))
    ranker = LexicalRanker()
    variants = ("full", "remove_purpose", "remove_app", "remove_tool", "remove_consumer")
    metrics: dict[str, dict[str, float]] = {}
    for variant in variants:
        ignored = None if variant == "full" else variant.removeprefix("remove_")
        rows: list[QueryEvaluation] = []
        for query in scenario.queries:
            eligible = [
                item
                for item in scenario.items
                if _authorized_with_ablation(item, query.context, scenario.now, ignored)
            ]
            selected = ranker.rank(query.text, eligible, int(config["retrieval"]["k"]))
            rows.append(
                QueryEvaluation(
                    query.query_id,
                    tuple(item.item_id for item in selected),
                    query.entitled_ids,
                    query.unauthorized_ids,
                    0.0,
                )
            )
        metrics[variant] = evaluate_queries(rows)
    result = {
        "notice": SYNTHETIC_NOTICE,
        "paper_result_claimed": False,
        "metadata": run_metadata(config, "ablate"),
        "metrics": metrics,
        "interpretation": "Controlled synthetic label-removal smoke test; not an empirical paper ablation.",
    }
    write_json(output_dir / "resolved_config.json", dict(config))
    write_json(output_dir / "ablation.json", result)
    write_run_manifest(
        output_dir, config, "ablate", ["resolved_config.json", "ablation.json", "run_manifest.json"]
    )
    return result


def _authorized_with_ablation(
    item: MemoryItem, context: TaskContext, now: float, ignored: str | None
) -> bool:
    label = item.label
    checks = {
        "purpose": context.purpose in label.purposes,
        "app": context.app_id in label.apps,
        "tool": context.tool_id in label.tools,
        "consumer": context.consumer_id in label.consumers,
    }
    return (
        item.state == ItemState.ADMITTED
        and item.provenance.valid
        and label.not_before <= now < label.expires_at
        and all(value for name, value in checks.items() if name != ignored)
    )
