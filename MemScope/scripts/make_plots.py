#!/usr/bin/env python3
"""Generate a figure from a MemScope metrics JSON file."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from memscope.cli import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(["plot", "--input", str(args.input), "--output", str(args.output)]))
