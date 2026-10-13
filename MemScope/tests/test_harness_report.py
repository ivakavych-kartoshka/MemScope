import csv
import json
from pathlib import Path
from typing import Any

import pytest

from memscope.experiments.harness_report import write_harness_report
from memscope.experiments.run_harness import run_harness
from memscope.utils.io import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path) -> dict[str, Any]:
    config = load_yaml(ROOT / "configs" / "synthetic_harness.yaml")
    config["output"]["root"] = str(tmp_path / "out")
    config["harness"]["seeds"] = [7, 11]
    return config


def _summary(tmp_path: Path) -> Path:
    run_harness(_config(tmp_path), tmp_path / "out")
    return tmp_path / "out" / "harness_summary.json"


def test_report_writes_tables_and_figures(tmp_path: Path) -> None:
    summary = _summary(tmp_path)
    result = write_harness_report(summary, tmp_path / "report")
    assert "not a paper result" in result["notice"]
    for name in ("tables/rq1_enforcement.csv", "tables/harness_tables.md"):
        assert (tmp_path / "report" / name).exists()
    for name in result["figures"]:
        assert (tmp_path / "report" / name).exists()


def test_rq1_table_reflects_summary(tmp_path: Path) -> None:
    summary_path = _summary(tmp_path)
    summary = json.loads(summary_path.read_text())
    write_harness_report(summary_path, tmp_path / "report")
    rows = {row["method"]: row for row in csv.DictReader(
        (tmp_path / "report" / "tables" / "rq1_enforcement.csv").open(encoding="utf-8")
    )}
    assert rows["memscope"]["authorization_violations_total"] == "0"
    assert rows["memscope"]["queries_with_violation"] == "0"
    for baseline in ("unscoped", "namespace", "prompt_only"):
        expected = summary["rq1_enforcement"][baseline]["authorization_violations_total"]
        assert int(rows[baseline]["authorization_violations_total"]) == expected


def test_markdown_carries_synthetic_notice(tmp_path: Path) -> None:
    summary_path = _summary(tmp_path)
    summary = json.loads(summary_path.read_text())
    write_harness_report(summary_path, tmp_path / "report")
    text = (tmp_path / "report" / "tables" / "harness_tables.md").read_text()
    assert summary["notice"] in text
    assert "not_measured_offline" in text


def test_negative_controls_table_and_boundary(tmp_path: Path) -> None:
    summary_path = _summary(tmp_path)
    write_harness_report(summary_path, tmp_path / "report")
    rows = {row["control"]: row for row in csv.DictReader(
        (tmp_path / "report" / "tables" / "negative_controls.csv").open(encoding="utf-8")
    )}
    assert set(rows) == {
        "shadow_cache",
        "stale_token_replay",
        "always_accept_verifier",
        "authorized_copy_after_release",
    }
    assert rows["shadow_cache"]["mediated_guarantee_holds"] == "True"
    assert rows["authorized_copy_after_release"]["mediated_guarantee_holds"] == "False"
    text = (tmp_path / "report" / "tables" / "harness_tables.md").read_text()
    assert "negative-control boundaries" in text


def test_report_rejects_non_summary_input(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"foo": "bar"}))
    with pytest.raises(ValueError):
        write_harness_report(bad, tmp_path / "report")
