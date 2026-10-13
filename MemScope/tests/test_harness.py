import json
from pathlib import Path
from typing import Any

import pytest

from memscope.experiments.run_harness import run_harness
from memscope.utils.io import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path, **harness_overrides: object) -> dict[str, Any]:
    config = load_yaml(ROOT / "configs" / "synthetic_harness.yaml")
    config["output"]["root"] = str(tmp_path / "out")
    config["harness"].update(harness_overrides)
    return config


def test_harness_is_deterministic(tmp_path: Path) -> None:
    config = _config(tmp_path, seeds=[7, 11])
    run_harness(config, tmp_path / "a")
    run_harness(config, tmp_path / "b")
    assert (tmp_path / "a" / "harness_summary.json").read_text() == (
        tmp_path / "b" / "harness_summary.json"
    ).read_text()
    assert (tmp_path / "a" / "harness_runs.jsonl").read_text() == (
        tmp_path / "b" / "harness_runs.jsonl"
    ).read_text()


def test_harness_reports_rq5_as_not_measured(tmp_path: Path) -> None:
    result = run_harness(_config(tmp_path, seeds=[7]), tmp_path / "out")
    assert result["rq5_mobile_cost"]["status"] == "not_measured_offline"
    assert result["paper_result_claimed"] is False
    assert "not a paper result" in result["notice"]


def test_harness_enforcement_matches_policy_oracle(tmp_path: Path) -> None:
    result = run_harness(_config(tmp_path, seeds=[7, 11, 13]), tmp_path / "out")
    rq1 = result["rq1_enforcement"]
    assert rq1["memscope"]["authorization_violations_total"] == 0
    assert rq1["memscope"]["queries_with_violation"] == 0
    for baseline in ("unscoped", "namespace", "prompt_only"):
        assert rq1[baseline]["authorization_violations_total"] > 0
        assert rq1[baseline]["queries_with_violation"] > 0


def test_harness_utility_recall_tracks_scope_and_k(tmp_path: Path) -> None:
    result = run_harness(_config(tmp_path, seeds=[7]), tmp_path / "out")
    utility = result["rq2_utility"]
    recalls = utility["entitled_recall_at_k"]
    assert recalls["w1_k1"]["entitled_recall_at_k_mean"] == 1.0
    assert recalls["w2_k1"]["entitled_recall_at_k_mean"] < 1.0
    assert recalls["w3_k1"]["entitled_recall_at_k_mean"] < recalls["w2_k1"]["entitled_recall_at_k_mean"]
    for width in utility["scope_widths"]:
        assert recalls[f"w{width}_k5"]["entitled_recall_at_k_mean"] == 1.0


def test_harness_lifecycle_fails_closed(tmp_path: Path) -> None:
    result = run_harness(_config(tmp_path, seeds=[7, 11, 13]), tmp_path / "out")
    lifecycle = result["rq4_lifecycle"]
    assert lifecycle["post_expiry_releases_total"] == 0
    assert lifecycle["epoch_change_denials"] == lifecycle["epoch_change_trials"] == 3
    assert lifecycle["revoked_items_returned_total"] == 0
    assert lifecycle["revocation_trials"] == 3
    assert lifecycle["ttl_allowed_before_expiry"] == lifecycle["ttl_trials"] == 3
    assert lifecycle["ttl_returned_at_expiry"] == 0


def test_harness_derivation_blocks_laundering(tmp_path: Path) -> None:
    result = run_harness(_config(tmp_path, seeds=[7]), tmp_path / "out")
    derivation = result["rq3_derivation"]
    assert derivation["admitted"]["faithful"] == derivation["cases"]["faithful"]
    for kind in (
        "unsupported",
        "laundering",
        "cross_scope",
        "stale_parent",
        "expired_parent",
        "composition_mismatch",
        "composition_disjoint_tools",
    ):
        assert kind in derivation["cases"]
        assert derivation["admitted"][kind] == 0
    assert derivation["false_acceptance_rate"] == 0.0
    assert derivation["false_rejection_rate"] == 0.0


def test_harness_retention_protects_safety_items(tmp_path: Path) -> None:
    result = run_harness(_config(tmp_path, seeds=[7, 11]), tmp_path / "out")
    retention = result["rq6_retention"]
    assert retention["policy_aware_safety_survival_mean"] == 1.0
    assert retention["policy_blind_safety_survival_mean"] < retention["policy_aware_safety_survival_mean"]


def test_harness_writes_run_manifest(tmp_path: Path) -> None:
    run_harness(_config(tmp_path, seeds=[7]), tmp_path / "out")
    manifest = json.loads((tmp_path / "out" / "run_manifest.json").read_text())
    assert manifest["metadata"]["stage"] == "harness"
    assert "harness_summary.json" in manifest["outputs"]


def test_harness_reports_negative_controls(tmp_path: Path) -> None:
    result = run_harness(_config(tmp_path, seeds=[7, 11]), tmp_path / "out")
    controls = result["negative_controls"]
    assert controls["summary"]["controls"] == 4
    assert controls["shadow_cache"]["mediated_unauthorized_returned"] == 0
    assert controls["stale_token_replay"]["mediated_guarantee_holds"] is True
    assert controls["authorized_copy_after_release"]["mediated_guarantee_holds"] is False


def test_harness_rejects_real_mode(tmp_path: Path) -> None:
    config = _config(tmp_path, seeds=[7])
    config["run"]["mode"] = "real"
    with pytest.raises(NotImplementedError):
        run_harness(config, tmp_path / "out")
