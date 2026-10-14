"""Offline-only benchmark adapter with a shared, documented JSONL schema.

The adapter never downloads, authenticates, calls a model, or reaches the
network. It validates a *manually prepared* benchmark directory against
``docs/data_format.md`` and returns typed, cross-checked records. Real benchmark
files are provisioned and licensed by a human operator; this module only rejects
malformed or unlicensed inputs early.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from ..data.schemas import MemoryLabel, TaskContext
from ..utils.io import read_jsonl
from ..utils.validation import require_keys

_REQUIRED_FILES = (
    "items.jsonl",
    "queries.jsonl",
    "splits.json",
    "LICENSE_OR_TERMS.txt",
    "PREPARATION_MANIFEST.json",
)
_SPLIT_KEYS = ("train", "development", "pilot", "test")


@dataclass(frozen=True)
class BenchmarkRecord:
    record_type: str
    record_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class BenchmarkData:
    """Validated, cross-checked benchmark contents (never a paper result)."""

    name: str
    items: tuple[dict[str, Any], ...]
    queries: tuple[dict[str, Any], ...]
    splits: dict[str, Any]
    manifest: dict[str, Any]


def _require_finite(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"benchmark {field} must be a number")
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"benchmark {field} must be finite")
    return number


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"benchmark {field} must be a list")
    return value


class JsonlBenchmarkAdapter:
    """Load a manually prepared policy-augmented benchmark directory.

    Required files are documented in ``docs/data_format.md``. A directory missing
    its license/terms or preparation manifest is refused, because provenance and
    licensing are prerequisites for any real evaluation cell.
    """

    NAMES = frozenset({"locomo", "longmemeval", "memora", "pa_bench", "multi_app"})

    def __init__(self, name: str, root: Path, *, require_provenance: bool = True) -> None:
        if name not in self.NAMES:
            raise ValueError(f"unsupported benchmark adapter: {name}")
        self.name = name
        self.root = root
        self.require_provenance = require_provenance

    def _required_files(self) -> tuple[str, ...]:
        if self.require_provenance:
            return _REQUIRED_FILES
        return _REQUIRED_FILES[:3]

    def validate(self) -> None:
        for filename in self._required_files():
            path = self.root / filename
            if not path.is_file():
                raise FileNotFoundError(f"missing manually prepared benchmark file: {path}")

    def load_items(self) -> list[dict[str, Any]]:
        self.validate()
        rows = list(read_jsonl(self.root / "items.jsonl"))
        seen: set[str] = set()
        for row in rows:
            require_keys(
                row,
                ["item_id", "text", "source", "label", "created_at", "expires_at"],
                "benchmark item",
            )
            item_id = row["item_id"]
            if not isinstance(item_id, str) or not item_id:
                raise ValueError("benchmark item_id must be a non-empty string")
            if item_id in seen:
                raise ValueError(f"duplicate benchmark item id: {item_id}")
            seen.add(item_id)
            if not isinstance(row["text"], str):
                raise TypeError(f"benchmark item {item_id} text must be a string")
            if not isinstance(row["label"], Mapping):
                raise TypeError(f"benchmark item {item_id} label must be an object")
            try:
                MemoryLabel.from_mapping(row["label"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"benchmark item {item_id} has an invalid label: {exc}") from exc
            if not isinstance(row["source"], Mapping):
                raise TypeError(f"benchmark item {item_id} source must be an object")
            require_keys(
                row["source"], ["app", "tool", "channel", "timestamp"], "benchmark item source"
            )
            _require_finite(row["created_at"], "item created_at")
            _require_finite(row["expires_at"], "item expires_at")
        return rows

    def load_queries(self) -> list[dict[str, Any]]:
        self.validate()
        rows = list(read_jsonl(self.root / "queries.jsonl"))
        seen: set[str] = set()
        for row in rows:
            require_keys(
                row,
                ["query_id", "text", "context", "entitled_item_ids", "split"],
                "benchmark query",
            )
            query_id = row["query_id"]
            if not isinstance(query_id, str) or not query_id:
                raise ValueError("benchmark query_id must be a non-empty string")
            if query_id in seen:
                raise ValueError(f"duplicate benchmark query id: {query_id}")
            seen.add(query_id)
            if not isinstance(row["context"], Mapping):
                raise TypeError(f"benchmark query {query_id} context must be an object")
            require_keys(
                row["context"],
                ["app", "tool", "consumer", "purpose", "task_time", "nonce"],
                "benchmark query context",
            )
            try:
                TaskContext(
                    app_id=str(row["context"]["app"]),
                    tool_id=row["context"]["tool"],
                    consumer_id=str(row["context"]["consumer"]),
                    purpose=str(row["context"]["purpose"]),
                    task_time=_require_finite(row["context"]["task_time"], "context task_time"),
                    nonce=str(row["context"]["nonce"]),
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"benchmark query {query_id} has an invalid context: {exc}") from exc
            entries = _require_list(row["entitled_item_ids"], "query entitled_item_ids")
            if any(not isinstance(entry, str) for entry in entries):
                raise ValueError(f"benchmark query {query_id} entitled_item_ids must be strings")
            if not isinstance(row["split"], str) or not row["split"]:
                raise ValueError(f"benchmark query {query_id} split must be a non-empty string")
        return rows

    def load_splits(self) -> dict[str, Any]:
        self.validate()
        path = self.root / "splits.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError("splits.json must contain a JSON object")
        for key in _SPLIT_KEYS:
            entries = _require_list(value.get(key), f"splits.{key}")
            if any(not isinstance(entry, str) for entry in entries):
                raise ValueError(f"splits.{key} must be a list of query IDs")
        hash_value = value.get("preparation_hash")
        if not isinstance(hash_value, str) or not hash_value:
            raise ValueError("splits.json requires a non-empty preparation_hash")
        return value

    def load_manifest(self) -> dict[str, Any]:
        self.validate()
        path = self.root / "PREPARATION_MANIFEST.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError("PREPARATION_MANIFEST.json must contain a JSON object")
        return value

    def load(self) -> BenchmarkData:
        items = self.load_items()
        queries = self.load_queries()
        splits = self.load_splits()
        item_ids = {row["item_id"] for row in items}
        split_names = set(_SPLIT_KEYS)
        for row in queries:
            unknown = set(row["entitled_item_ids"]) - item_ids
            if unknown:
                raise ValueError(
                    f"benchmark query {row['query_id']} references unknown entitled items: "
                    f"{sorted(unknown)}"
                )
            if row["split"] not in split_names:
                raise ValueError(
                    f"benchmark query {row['query_id']} split {row['split']!r} is not one of "
                    f"{sorted(split_names)}"
                )
        self._validate_split_membership(queries, splits)
        return BenchmarkData(
            name=self.name,
            items=tuple(items),
            queries=tuple(queries),
            splits=dict(splits),
            manifest=self.load_manifest(),
        )

    @staticmethod
    def _validate_split_membership(
        queries: Sequence[Mapping[str, Any]], splits: Mapping[str, Any]
    ) -> None:
        query_ids = {row["query_id"] for row in queries}
        assigned: set[str] = set()
        for key in _SPLIT_KEYS:
            members = set(splits[key])
            unknown = members - query_ids
            if unknown:
                raise ValueError(f"splits.{key} references unknown query IDs: {sorted(unknown)}")
            overlap = members & assigned
            if overlap:
                raise ValueError(f"query IDs appear in multiple splits: {sorted(overlap)}")
            assigned |= members
