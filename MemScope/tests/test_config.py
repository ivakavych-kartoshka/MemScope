from pathlib import Path

from memscope.experiments.common import validate_config
from memscope.utils.io import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def test_all_configs_parse_and_validate() -> None:
    for name in ("default.yaml", "synthetic_demo.yaml", "experiment_template.yaml"):
        validate_config(load_yaml(ROOT / "configs" / name))


def test_policy_example_uses_safe_yaml() -> None:
    policy = load_yaml(ROOT / "configs" / "policies.example.yaml")
    assert policy["rules"][0]["id"] == "food_safety_allergy"
