#!/usr/bin/env python3
"""Run calibration preflight, evaluation, or ablation from a YAML config."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from memscope.cli import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", choices=("calibrate", "evaluate", "ablate"), required=True)
    args = parser.parse_args()
    raise SystemExit(
        main(["experiment", "--config", str(args.config), "--stage", args.stage])
    )
