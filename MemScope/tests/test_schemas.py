import pytest
from conftest import make_item, make_label

from memscope.data.schemas import MemoryLabel, Sensitivity, TaskContext


def test_label_rejects_empty_time_interval() -> None:
    with pytest.raises(ValueError, match="not_before"):
        make_label(not_before=5.0, expires_at=5.0)


def test_context_rejects_empty_identity() -> None:
    with pytest.raises(ValueError):
        TaskContext("", None, "consumer", "purpose", 1.0, "n")


def test_item_computes_positive_size() -> None:
    item = make_item(payload="hello")
    assert item.size_bytes == 5


def test_label_mapping_roundtrip() -> None:
    label = make_label(sensitivity=Sensitivity.SENSITIVE)
    assert MemoryLabel.from_mapping(label.to_mapping()) == label
