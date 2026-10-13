import pytest

from memscope.metrics.statistics import bootstrap_median_ci, holm_adjust, wilson_interval


def test_wilson_bounds() -> None:
    low, high = wilson_interval(5, 10)
    assert 0 <= low < 0.5 < high <= 1


def test_bootstrap_is_seeded() -> None:
    assert bootstrap_median_ci([1, 2, 3, 4], repetitions=100, seed=4) == bootstrap_median_ci(
        [1, 2, 3, 4], repetitions=100, seed=4
    )


def test_holm_monotone_adjustment() -> None:
    result = holm_adjust({"a": 0.01, "b": 0.02, "c": 0.5})
    assert result["a"] <= result["b"] <= result["c"]
    with pytest.raises(ValueError):
        holm_adjust({"bad": 1.2})
