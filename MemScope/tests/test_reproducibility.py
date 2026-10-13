import json
from pathlib import Path

from memscope.experiments.run_evaluation import run_evaluation
from memscope.utils.io import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def test_fixed_seed_reproduces_metrics_and_queries(tmp_path: Path) -> None:
    config = load_yaml(ROOT / "configs" / "synthetic_demo.yaml")
    first = run_evaluation(config, tmp_path / "a")
    second = run_evaluation(config, tmp_path / "b")
    assert first["metrics"] == second["metrics"]
    assert (tmp_path / "a" / "query_results.jsonl").read_text() == (
        tmp_path / "b" / "query_results.jsonl"
    ).read_text()


def test_no_result_claimed_as_paper_measurement(tmp_path: Path) -> None:
    config = load_yaml(ROOT / "configs" / "synthetic_demo.yaml")
    run_evaluation(config, tmp_path)
    result = json.loads((tmp_path / "metrics.json").read_text())
    assert result["paper_result_claimed"] is False
    assert result["metadata"]["result_class"] == "synthetic_smoke_test"
