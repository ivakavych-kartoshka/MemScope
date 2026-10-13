"""Configuration validation and run provenance."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections.abc import Mapping
from typing import Any

from ..utils.validation import require_keys


def validate_config(config: Mapping[str, Any]) -> None:
    require_keys(config, ["run", "data", "retrieval", "output"], "configuration")
    require_keys(config["run"], ["seed", "mode"], "run")
    require_keys(config["data"], ["name", "root"], "data")
    require_keys(config["retrieval"], ["k"], "retrieval")
    require_keys(config["output"], ["root"], "output")
    if int(config["run"]["seed"]) < 0:
        raise ValueError("run.seed must be non-negative")
    if int(config["retrieval"]["k"]) < 1:
        raise ValueError("retrieval.k must be positive")


def config_hash(config: Mapping[str, Any]) -> str:
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_metadata(config: Mapping[str, Any], stage: str) -> dict[str, Any]:
    return {
        "stage": stage,
        "config_sha256": config_hash(config),
        "seed": int(config["run"]["seed"]),
        "mode": str(config["run"]["mode"]),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "result_class": "synthetic_smoke_test" if config["run"]["mode"] == "synthetic" else "real",
        "paper_result_claimed": False,
    }
