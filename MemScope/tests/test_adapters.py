from pathlib import Path

import pytest

from memscope.adapters.android import UnavailableAndroidAdapter
from memscope.adapters.attacks import ExternalAttackAdapter
from memscope.baselines.external import ExternalBaseline
from memscope.data.adapters import JsonlBenchmarkAdapter


def test_external_adapters_fail_explicitly(tmp_path: Path) -> None:
    with pytest.raises(NotImplementedError, match="manually provisioned"):
        ExternalBaseline("GAAP", tmp_path).retrieve("q", [], None, 1)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError, match="external artifact"):
        ExternalAttackAdapter("MEXTRA", tmp_path, "unconfigured").run({})
    with pytest.raises(RuntimeError, match="Android adapter unavailable"):
        UnavailableAndroidAdapter().query_memory({})


def test_benchmark_adapter_requires_manual_files(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="manually prepared"):
        JsonlBenchmarkAdapter("locomo", tmp_path).validate()


def test_unknown_attack_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ExternalAttackAdapter("invented", tmp_path, "x")
