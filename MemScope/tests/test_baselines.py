from conftest import make_context, make_item

from memscope.baselines.simple import NamespaceBaseline, PromptOnlyBaseline, UnscopedBaseline


def test_unscoped_and_prompt_baselines_do_not_enforce_policy() -> None:
    items = [make_item("a", "allergy"), make_item("b", "calendar")]
    context = make_context(purpose="ads", tool="ads")
    assert UnscopedBaseline().retrieve("allergy", items, context, 1)[0].item_id == "a"
    assert PromptOnlyBaseline().retrieve("allergy", items, context, 1)[0].item_id == "a"


def test_namespace_baseline_filters_only_identity_namespace() -> None:
    a = make_item("a", "allergy", namespace="primary_assistant")
    b = make_item("b", "allergy", namespace="other")
    result = NamespaceBaseline().retrieve("allergy", [a, b], make_context(), 5)
    assert [item.item_id for item in result] == ["a"]
