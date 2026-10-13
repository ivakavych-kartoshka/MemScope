"""Command-line interface for MemScope's reference model and experiment harness."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .data.adapters import JsonlBenchmarkAdapter
from .experiments.harness_report import write_harness_report
from .experiments.plot_results import plot_metrics
from .experiments.run_ablation import run_ablation
from .experiments.run_calibration import run_calibration
from .experiments.run_evaluation import run_evaluation
from .experiments.run_harness import run_harness
from .utils.io import load_yaml
from .utils.logging import configure_logging


def _output_dir(config: dict[str, Any], config_path: Path) -> Path:
    root = Path(str(config["output"]["root"]))
    return root if root.is_absolute() else (Path.cwd() / root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memscope", description="Purpose-bound memory reference implementation"
    )
    parser.add_argument("--log-level", default="INFO")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("synthetic-demo", help="run labeled synthetic smoke test")
    demo.add_argument("--config", type=Path, required=True)

    experiment = sub.add_parser("experiment", help="run a configured experiment stage")
    experiment.add_argument("--config", type=Path, required=True)
    experiment.add_argument("--stage", choices=("calibrate", "evaluate", "ablate"), required=True)

    harness = sub.add_parser("harness", help="run the synthetic RQ1-RQ6 harness")
    harness.add_argument("--config", type=Path, required=True)

    harness_report = sub.add_parser(
        "harness-report", help="render tables and figures from a harness summary"
    )
    harness_report.add_argument("--summary", type=Path, required=True)
    harness_report.add_argument("--output-dir", type=Path, required=True)

    plot = sub.add_parser("plot", help="plot a generated metrics JSON file")
    plot.add_argument("--input", type=Path, required=True)
    plot.add_argument("--output", type=Path, required=True)

    validate = sub.add_parser("validate-data", help="validate a manually prepared benchmark")
    validate.add_argument("--name", required=True)
    validate.add_argument("--root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    if args.command in {"synthetic-demo", "experiment"}:
        config = load_yaml(args.config)
        output_dir = _output_dir(config, args.config)
        stage = "evaluate" if args.command == "synthetic-demo" else args.stage
        if stage == "evaluate":
            result = run_evaluation(config, output_dir)
        elif stage == "calibrate":
            result = run_calibration(config, output_dir)
        else:
            result = run_ablation(config, output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "harness":
        config = load_yaml(args.config)
        result = run_harness(config, _output_dir(config, args.config))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "plot":
        path = plot_metrics(args.input, args.output)
        print(path)
        return 0
    if args.command == "harness-report":
        result = write_harness_report(args.summary, args.output_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "validate-data":
        JsonlBenchmarkAdapter(args.name, args.root).validate()
        print(f"valid benchmark layout: {args.root}")
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
