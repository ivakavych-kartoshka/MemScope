import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return env


def test_module_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "memscope.cli", "--help"],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "synthetic-demo" in result.stdout


def test_cli_synthetic_demo_and_plot(tmp_path: Path) -> None:
    config = yaml.safe_load((ROOT / "configs" / "synthetic_demo.yaml").read_text())
    config["output"]["root"] = str(tmp_path / "out")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    subprocess.run(
        [sys.executable, "scripts/run_synthetic_demo.py", "--config", str(config_path)],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    metrics = json.loads((tmp_path / "out" / "metrics.json").read_text())
    assert metrics["paper_result_claimed"] is False
    assert "synthetic" in metrics["notice"]
    subprocess.run(
        [
            sys.executable,
            "scripts/make_plots.py",
            "--input",
            str(tmp_path / "out" / "metrics.json"),
            "--output",
            str(tmp_path / "out" / "metrics.png"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    assert (tmp_path / "out" / "metrics.png").stat().st_size > 0
