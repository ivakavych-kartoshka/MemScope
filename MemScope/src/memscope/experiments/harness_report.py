"""Render tables and figures from a synthetic RQ harness summary.

Everything produced here is derived only from ``harness_summary.json`` (which
carries the synthetic notice); no value is hard-coded. Outputs are labeled
controlled-synthetic artifacts, never paper results.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

_METHOD_ORDER = ("memscope", "unscoped", "namespace", "prompt_only")


def _load_summary(summary_path: Path) -> dict[str, Any]:
    with summary_path.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    if not isinstance(summary, dict) or "notice" not in summary or "rq1_enforcement" not in summary:
        raise ValueError("input is not a MemScope harness summary")
    return summary


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _format_cell(cell: Any) -> str:
    if isinstance(cell, float):
        return f"{cell:.4f}"
    return str(cell)


def _md_table(header: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_format_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def _rq1_table(summary: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    enforce = summary["rq1_enforcement"]
    order = [m for m in _METHOD_ORDER if m in enforce] + [m for m in enforce if m not in _METHOD_ORDER]
    header = [
        "method",
        "out_of_scope_retrieval_rate_mean",
        "authorization_violations_total",
        "unique_record_extraction_yield_total",
        "queries_with_violation",
        "queries_with_violation_rate",
        "ci95_low",
        "ci95_high",
    ]
    rows: list[list[Any]] = []
    for name in order:
        entry = enforce[name]
        low, high = entry["queries_with_violation_rate_ci95"]
        rows.append(
            [
                name,
                entry["out_of_scope_retrieval_rate_mean"],
                entry["authorization_violations_total"],
                entry["unique_record_extraction_yield_total"],
                entry["queries_with_violation"],
                entry["queries_with_violation_rate"],
                low,
                high,
            ]
        )
    return header, rows


def _rq2_table(summary: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    utility = summary["rq2_utility"]
    header = ["scope_width", "k", "entitled_recall_at_k_mean", "ci95_low", "ci95_high"]
    rows: list[list[Any]] = []
    for width in utility["scope_widths"]:
        for k in utility["k_sweep"]:
            entry = utility["entitled_recall_at_k"][f"w{width}_k{k}"]
            low, high = entry["entitled_recall_at_k_ci95"]
            rows.append([width, k, entry["entitled_recall_at_k_mean"], low, high])
    return header, rows


def _rq3_table(summary: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    derivation = summary["rq3_derivation"]
    header = ["kind", "cases", "admitted", "accept_rate"]
    rows: list[list[Any]] = []
    for kind in derivation["kinds"]:
        cases = derivation["cases"][kind]
        admitted = derivation["admitted"][kind]
        rows.append([kind, cases, admitted, admitted / cases if cases else 0.0])
    rows.append(["false_acceptance_rate", "", "", derivation["false_acceptance_rate"]])
    rows.append(["false_rejection_rate", "", "", derivation["false_rejection_rate"]])
    return header, rows


def _rq4_table(summary: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    lifecycle = summary["rq4_lifecycle"]
    header = ["metric", "value"]
    rows = [[key, lifecycle[key]] for key in sorted(lifecycle)]
    return header, rows


def _rq6_table(summary: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    retention = summary["rq6_retention"]
    header = ["metric", "value"]
    rows = [[key, retention[key]] for key in sorted(retention)]
    return header, rows


_NEGATIVE_CONTROL_ORDER = (
    "shadow_cache",
    "stale_token_replay",
    "always_accept_verifier",
    "authorized_copy_after_release",
)


def _negative_controls_table(summary: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
    controls = summary["negative_controls"]
    header = [
        "control",
        "assumption_broken",
        "guarantee",
        "control_defeats_guarantee",
        "mediated_guarantee_holds",
    ]
    names = [name for name in _NEGATIVE_CONTROL_ORDER if name in controls]
    rows = [
        [
            name,
            controls[name]["assumption_broken"],
            controls[name]["guarantee"],
            controls[name]["control_defeats_guarantee"],
            controls[name]["mediated_guarantee_holds"],
        ]
        for name in names
    ]
    return header, rows


def _plot_rq1(summary: dict[str, Any], figures_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    enforce = summary["rq1_enforcement"]
    names = [m for m in _METHOD_ORDER if m in enforce]
    produced: list[Path] = []

    fig, axis = plt.subplots(figsize=(6, 4))
    axis.bar(names, [enforce[name]["authorization_violations_total"] for name in names], color="#b3533d")
    axis.set_ylabel("authorization violations (total)")
    axis.set_title("RQ1 authorization violations by method")
    axis.grid(axis="y", alpha=0.25)
    fig.suptitle(str(summary["notice"]), fontsize=8)
    fig.tight_layout()
    violations_path = figures_dir / "rq1_authorization_violations.png"
    fig.savefig(violations_path, dpi=160)
    plt.close(fig)
    produced.append(violations_path)

    rates = [enforce[name]["queries_with_violation_rate"] for name in names]
    lows = [enforce[name]["queries_with_violation_rate_ci95"][0] for name in names]
    highs = [enforce[name]["queries_with_violation_rate_ci95"][1] for name in names]
    lower = [max(0.0, rate - low) for rate, low in zip(rates, lows)]
    upper = [max(0.0, high - rate) for rate, high in zip(rates, highs)]
    fig, axis = plt.subplots(figsize=(6, 4))
    axis.bar(names, rates, yerr=[lower, upper], capsize=4, color="#2f6f9f")
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("queries with violation rate (95% Wilson)")
    axis.set_title("RQ1 out-of-scope leakage rate by method")
    axis.grid(axis="y", alpha=0.25)
    fig.suptitle(str(summary["notice"]), fontsize=8)
    fig.tight_layout()
    rate_path = figures_dir / "rq1_query_violation_rate.png"
    fig.savefig(rate_path, dpi=160)
    plt.close(fig)
    produced.append(rate_path)
    return produced


def _plot_rq2(summary: dict[str, Any], figures_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    utility = summary["rq2_utility"]
    ks = utility["k_sweep"]
    fig, axis = plt.subplots(figsize=(6, 4))
    for width in utility["scope_widths"]:
        recalls = [
            utility["entitled_recall_at_k"][f"w{width}_k{k}"]["entitled_recall_at_k_mean"]
            for k in ks
        ]
        axis.plot(ks, recalls, marker="o", label=f"scope width {width}")
    axis.set_ylim(0, 1.05)
    axis.set_xlabel("k")
    axis.set_ylabel("entitled Recall@k")
    axis.set_title("RQ2 entitled recall vs k by scope width")
    axis.legend()
    axis.grid(alpha=0.25)
    fig.suptitle(str(summary["notice"]), fontsize=8)
    fig.tight_layout()
    path = figures_dir / "rq2_recall_vs_k.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return [path]


def _plot_rq6(summary: dict[str, Any], figures_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    retention = summary["rq6_retention"]
    labels = ["policy-aware", "policy-blind"]
    values = [
        retention["policy_aware_safety_survival_mean"],
        retention["policy_blind_safety_survival_mean"],
    ]
    fig, axis = plt.subplots(figsize=(6, 4))
    axis.bar(labels, values, color=["#3d7d54", "#b3533d"])
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("safety-critical survival")
    axis.set_title("RQ6 safety retention under byte budget")
    axis.grid(axis="y", alpha=0.25)
    fig.suptitle(str(summary["notice"]), fontsize=8)
    fig.tight_layout()
    path = figures_dir / "rq6_safety_survival.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return [path]


def write_harness_report(summary_path: Path, output_dir: Path) -> dict[str, Any]:
    """Write CSV/Markdown tables and PNG figures derived from the summary."""

    summary = _load_summary(summary_path)
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"

    rq1_header, rq1_rows = _rq1_table(summary)
    rq2_header, rq2_rows = _rq2_table(summary)
    rq3_header, rq3_rows = _rq3_table(summary)
    rq4_header, rq4_rows = _rq4_table(summary)
    rq6_header, rq6_rows = _rq6_table(summary)

    tables: dict[str, tuple[list[str], list[list[Any]]]] = {
        "rq1_enforcement": (rq1_header, rq1_rows),
        "rq2_utility": (rq2_header, rq2_rows),
        "rq3_derivation": (rq3_header, rq3_rows),
        "rq4_lifecycle": (rq4_header, rq4_rows),
        "rq6_retention": (rq6_header, rq6_rows),
    }
    if "negative_controls" in summary:
        tables["negative_controls"] = _negative_controls_table(summary)
    produced_tables: list[str] = []
    markdown = [f"> {summary['notice']}", ""]
    for name, (header, rows) in tables.items():
        _write_csv(tables_dir / f"{name}.csv", header, rows)
        produced_tables.append(f"tables/{name}.csv")
        markdown.append(f"## {name}")
        markdown.append("")
        markdown.append(_md_table(header, rows))
        markdown.append("")
    markdown.append(
        f"RQ5 mobile cost: {summary['rq5_mobile_cost']['status']} "
        f"({summary['rq5_mobile_cost']['detail']})"
    )
    if "negative_controls" in summary:
        controls = summary["negative_controls"]
        markdown.append("")
        markdown.append("## negative-control boundaries")
        markdown.append("")
        for name in _NEGATIVE_CONTROL_ORDER:
            boundary = controls.get(name, {}).get("boundary")
            if boundary:
                markdown.append(f"- **{name}**: {boundary}")
        counts = controls["summary"]
        markdown.append("")
        markdown.append(
            f"Controls: {counts['controls']}; "
            f"defeating their guarantee: {counts['controls_defeating_their_guarantee']}; "
            f"mediated guarantee held: {counts['mediated_guarantees_held']}."
        )
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / "harness_tables.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    produced_tables.append("tables/harness_tables.md")

    figures_dir.mkdir(parents=True, exist_ok=True)
    figures = [
        *_plot_rq1(summary, figures_dir),
        *_plot_rq2(summary, figures_dir),
        *_plot_rq6(summary, figures_dir),
    ]

    return {
        "notice": summary["notice"],
        "tables": produced_tables,
        "figures": [str(path.relative_to(output_dir)) for path in figures],
    }
