import pytest
from conftest import make_context, make_item, make_label

from memscope.data.schemas import Sensitivity
from memscope.methods.policy import authorize, label_no_more_permissive, meet_labels


def test_authorization_exact_dimensions_and_time() -> None:
    item = make_item()
    context = make_context()
    assert authorize(item, context, 20.0, 30.0)
    assert not authorize(item, make_context(purpose="shopping"), 20.0, 30.0)
    assert not authorize(item, context, 100.0, 200.0)
    assert not authorize(item, context, 20.0, 20.0)


def test_meet_intersects_and_restricts() -> None:
    a = make_label(
        purposes=("health", "scheduling"),
        tools=("shared", "health.read"),
        sensitivity=Sensitivity.SENSITIVE,
        not_before=10,
        expires_at=90,
    )
    b = make_label(
        purposes=("scheduling",),
        tools=("shared", "calendar.read"),
        sensitivity=Sensitivity.HEALTH_SENSITIVE,
        not_before=20,
        expires_at=80,
    )
    result = meet_labels([a, b])
    assert result.purposes == frozenset({"scheduling"})
    assert result.tools == frozenset({"shared"})
    assert result.sensitivity == Sensitivity.HEALTH_SENSITIVE
    assert result.not_before == 20 and result.expires_at == 80
    assert label_no_more_permissive(result, a)
    assert label_no_more_permissive(result, b)


def test_meet_rejects_empty_parent_set() -> None:
    with pytest.raises(ValueError, match="empty parent"):
        meet_labels([])


def test_meet_rejects_disjoint_time() -> None:
    with pytest.raises(ValueError, match="temporal"):
        meet_labels([make_label(not_before=0, expires_at=10), make_label(not_before=20, expires_at=30)])
