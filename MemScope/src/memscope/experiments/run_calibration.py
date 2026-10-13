"""Policy/configuration preflight; MemScope has no conformal calibration stage."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..data.synthetic import SYNTHETIC_NOTICE
from ..utils.io import write_json
from .common import run_metadata, validate_config


def run_calibration(config: Mapping[str, Any], output_dir: Path) -> dict[str, Any]:
    validate_config(config)
    result = {
        "notice": SYNTHETIC_NOTICE if config["run"]["mode"] == "synthetic" else "preflight only",
        "status": "not_applicable",
        "reason": "The MemScope paper defines deterministic policy enforcement, not a calibrated predictor.",
        "metadata": run_metadata(config, "calibrate"),
    }
    write_json(output_dir / "resolved_config.json", dict(config))
    write_json(output_dir / "calibration_preflight.json", result)
    return result
