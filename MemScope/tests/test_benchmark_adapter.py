import json
from pathlib import Path
from typing import Any

import pytest

from memscope.data.adapters import BenchmarkData, JsonlBenchmarkAdapter


def _label(**overrides: Any) -> dict[str, Any]:
    label: dict[str, Any] = {
        "purposes": ["scheduling"],
        "apps": ["assistant.pkg"],
        "tools": ["calendar.read"],
        "consumers": ["primary_assistant"],
        "sensitivity": "PERSONAL",
        "not_before": 0.0,
        "expires_at": 100.0,
    }
    label.update(overrides)
    return label


def _write_benchmark(
    root: Path, *, items: list[dict[str, Any]], queries: list[dict[str, Any]], splits: dict[str, Any]
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "items.jsonl").write_text(
        "\n".join(json.dumps(row) for row in items) + "\n", encoding="utf-8"
    )
    (root / "queries.jsonl").write_text(
        "\n".join(json.dumps(row) for row in queries) + "\n", encoding="utf-8"
    )
    (root / "splits.json").write_text(json.dumps(splits), encoding="utf-8")
    (root / "LICENSE_OR_TERMS.txt").write_text("manual terms\n", encoding="utf-8")
    (root / "PREPARATION_MANIFEST.json").write_text(
        json.dumps({"origin": "manual", "version": "1"}), encoding="utf-8"
    )


def _valid_items() -> list[dict[str, Any]]:
    return [
        {
            "item_id": "m1",
            "text": "calendar free Tuesday",
            "source": {"app": "calendar.pkg", "tool": "calendar.read", "channel": "calendar", "timestamp": 0.0},
            "label": _label(),
            "created_at": 0.0,
            "expires_at": 100.0,
        }
    ]


def _valid_queries() -> list[dict[str, Any]]:
    return [
        {
            "query_id": "q1",
            "text": "when am I free?",
            "context": {
                "app": "assistant.pkg",
                "tool": "calendar.read",
                "consumer": "primary_assistant",
                "purpose": "scheduling",
                "task_time": 10.0,
                "nonce": "n1",
            },
            "entitled_item_ids": ["m1"],
            "split": "test",
        }
    ]


def _valid_splits() -> dict[str, Any]:
    return {
        "train": [],
        "development": [],
        "pilot": [],
        "test": ["q1"],
        "preparation_hash": "sha256:deadbeef",
    }


def test_missing_provenance_files_rejected(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    root.mkdir()
    (root / "items.jsonl").write_text("", encoding="utf-8")
    (root / "queries.jsonl").write_text("", encoding="utf-8")
    (root / "splits.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="manually prepared"):
        JsonlBenchmarkAdapter("locomo", root).validate()


def test_partial_load_without_provenance_allowed(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    _write_benchmark(root, items=_valid_items(), queries=_valid_queries(), splits=_valid_splits())
    (root / "LICENSE_OR_TERMS.txt").unlink()
    (root / "PREPARATION_MANIFEST.json").unlink()
    adapter = JsonlBenchmarkAdapter("locomo", root, require_provenance=False)
    assert adapter.load_items()[0]["item_id"] == "m1"


def test_valid_benchmark_loads(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    _write_benchmark(root, items=_valid_items(), queries=_valid_queries(), splits=_valid_splits())
    data = JsonlBenchmarkAdapter("locomo", root).load()
    assert isinstance(data, BenchmarkData)
    assert data.name == "locomo"
    assert data.manifest == {"origin": "manual", "version": "1"}
    assert len(data.items) == 1 and len(data.queries) == 1


def test_duplicate_item_id_rejected(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    items = _valid_items() + _valid_items()
    _write_benchmark(root, items=items, queries=_valid_queries(), splits=_valid_splits())
    with pytest.raises(ValueError, match="duplicate benchmark item id"):
        JsonlBenchmarkAdapter("locomo", root).load_items()


def test_invalid_label_rejected(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    items = _valid_items()
    items[0]["label"] = _label(not_before=200.0, expires_at=100.0)
    _write_benchmark(root, items=items, queries=_valid_queries(), splits=_valid_splits())
    with pytest.raises(ValueError, match="invalid label"):
        JsonlBenchmarkAdapter("locomo", root).load_items()


def test_query_referencing_unknown_item_rejected(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    queries = _valid_queries()
    queries[0]["entitled_item_ids"] = ["ghost"]
    _write_benchmark(root, items=_valid_items(), queries=queries, splits=_valid_splits())
    with pytest.raises(ValueError, match="unknown entitled items"):
        JsonlBenchmarkAdapter("locomo", root).load()


def test_query_split_not_declared_rejected(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    queries = _valid_queries()
    queries[0]["split"] = "holdout"
    _write_benchmark(root, items=_valid_items(), queries=queries, splits=_valid_splits())
    with pytest.raises(ValueError, match="split 'holdout' is not one of"):
        JsonlBenchmarkAdapter("locomo", root).load()


def test_overlapping_splits_rejected(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    splits = _valid_splits()
    splits["train"] = ["q1"]
    _write_benchmark(root, items=_valid_items(), queries=_valid_queries(), splits=splits)
    with pytest.raises(ValueError, match="multiple splits"):
        JsonlBenchmarkAdapter("locomo", root).load()


def test_splits_require_preparation_hash(tmp_path: Path) -> None:
    root = tmp_path / "locomo"
    splits = _valid_splits()
    del splits["preparation_hash"]
    _write_benchmark(root, items=_valid_items(), queries=_valid_queries(), splits=splits)
    with pytest.raises(ValueError, match="preparation_hash"):
        JsonlBenchmarkAdapter("locomo", root).load_splits()
