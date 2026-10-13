from memscope.data.schemas import QueryEvaluation
from memscope.metrics.core import (
    authorization_violations,
    entitled_misses,
    entitled_recall_at_k,
    entitled_recall_eligible_queries,
    evaluate_queries,
    exact_match,
    out_of_scope_retrieval_rate,
    token_f1,
)


def test_security_and_entitled_metrics() -> None:
    rows = [
        QueryEvaluation("q1", ("a", "x"), frozenset({"a", "b"}), frozenset({"x"})),
        QueryEvaluation("q2", ("c",), frozenset({"c"}), frozenset({"z"})),
    ]
    assert authorization_violations(rows) == 1
    assert entitled_misses(rows) == 1
    assert entitled_recall_at_k(rows) == 0.75
    assert out_of_scope_retrieval_rate(rows) == 1 / 3


def test_empty_ground_truth_policy() -> None:
    rows = [
        QueryEvaluation("empty", (), frozenset(), frozenset()),
        QueryEvaluation("hit", ("a",), frozenset({"a"}), frozenset()),
    ]
    assert entitled_recall_at_k(rows) == 1.0
    assert entitled_recall_at_k(rows, "zero") == 0.5
    assert entitled_recall_eligible_queries(rows) == 1
    summary = evaluate_queries(rows)
    assert summary["entitled_recall_eligible_queries"] == 1.0
    assert summary["entitled_recall_excluded_queries"] == 1.0
    assert summary["entitled_recall_at_k"] == 1.0


def test_text_metrics() -> None:
    assert exact_match(" Blue ", "blue") == 1.0
    assert token_f1("a b", "a c") == 0.5
