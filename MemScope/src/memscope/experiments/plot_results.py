"""Generate plots only from result JSON produced by an experiment runner."""

from __future__ import annotations

import json
from pathlib import Path


def plot_metrics(input_path: Path, output_path: Path) -> Path:
    with input_path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    if "metrics" not in result or "notice" not in result:
        raise ValueError("input is not a MemScope result file")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(result["metrics"])
    recalls = [result["metrics"][name]["entitled_recall_at_k"] for name in names]
    violations = [result["metrics"][name]["authorization_violations"] for name in names]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    axes[0].bar(names, recalls, color="#2f6f9f")
    axes[0].set_ylim(0, 1.05)
    axes[0].set_title("Entitled Recall@k")
    axes[1].bar(names, violations, color="#b3533d")
    axes[1].set_title("Authorization violations")
    for axis in axes:
        axis.tick_params(axis="x", rotation=30)
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle(str(result["notice"]))
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path
