#!/usr/bin/env python3
"""Run the offline synthetic RQ1-RQ6 harness from a YAML config."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from memscope.cli import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(["harness", "--config", str(args.config)]))
