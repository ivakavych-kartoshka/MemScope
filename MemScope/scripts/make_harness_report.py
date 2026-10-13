#!/usr/bin/env python3
"""Render tables and figures from a synthetic RQ harness summary."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from memscope.cli import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(
        main(["harness-report", "--summary", str(args.summary), "--output-dir", str(args.output_dir)])
    )
