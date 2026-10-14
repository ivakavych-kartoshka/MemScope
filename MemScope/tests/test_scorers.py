import pytest

from memscope.metrics.scorers import (
    ScoringExample,
    abstention_metrics,
    accuracy_metrics,
    answer_metrics,
    fama_metrics,
    is_abstention,
    score_benchmark,
)


def test_is_abstention_detects_markers_and_normalizes() -> None:
    assert is_abstention("  I don't know ")
    assert is_abstention("")
    assert not is_abstention("Tuesday at 10 AM")


def test_answer_metrics_exact_and_f1() -> None:
    examples = [
        ScoringExample("q1", "Tuesday 10 AM", target="Tuesday 10 AM"),
        ScoringExample("q2", "Tuesday 11 AM", target="Tuesday 10 AM"),
    ]
    metrics = answer_metrics(examples)
    assert metrics["exact_match"] == pytest.approx(0.5)
    assert 0.0 < metrics["token_f1"] < 1.0


def test_answer_metrics_ignores_abstain_only_examples() -> None:
    examples = [ScoringExample("q1", "I don't know", should_abstain=True)]
    assert answer_metrics(examples) == {"exact_match": 0.0, "token_f1": 0.0}


def test_abstention_accuracy() -> None:
    examples = [
        ScoringExample("q1", "I don't know", should_abstain=True),
        ScoringExample("q2", "Tuesday", target="Tuesday", should_abstain=False),
        ScoringExample("q3", "Tuesday", target="Tuesday", should_abstain=True),
    ]
    assert abstention_metrics(examples)["abstention_accuracy"] == pytest.approx(2 / 3)


def test_accuracy_combines_answers_and_abstentions() -> None:
    examples = [
        ScoringExample("q1", "Tuesday", target="Tuesday"),
        ScoringExample("q2", "unknown", should_abstain=True),
        ScoringExample("q3", "wrong", target="Tuesday"),
    ]
    assert accuracy_metrics(examples)["accuracy"] == pytest.approx(2 / 3)


def test_fama_penalizes_invalidated_evidence() -> None:
    examples = [
        ScoringExample("q1", "Riverside", target="Riverside", used_item_ids=("valid",)),
        ScoringExample(
            "q2",
            "Riverside",
            target="Riverside",
            used_item_ids=("stale",),
            invalidated_item_ids=frozenset({"stale"}),
        ),
    ]
    metrics = fama_metrics(examples)
    assert metrics["fama"] == pytest.approx(0.5)
    assert metrics["invalidated_use_rate"] == pytest.approx(0.5)


def test_score_benchmark_dispatch_and_unknown() -> None:
    examples = [ScoringExample("q1", "Tuesday", target="Tuesday")]
    assert "fama" in score_benchmark("memora", examples)
    assert "abstention_accuracy" in score_benchmark("longmemeval", examples)
    assert score_benchmark("locomo", examples) == {"exact_match": 1.0, "token_f1": 1.0}
    with pytest.raises(ValueError, match="unsupported benchmark scorer"):
        score_benchmark("invented", examples)


def test_score_benchmark_empty_is_well_defined() -> None:
    for name in ("locomo", "longmemeval", "memora", "pa_bench", "multi_app"):
        metrics = score_benchmark(name, [])
        assert all(value == 0.0 for value in metrics.values())
