"""Offline-only benchmark adapter with a shared, documented JSONL schema."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.io import read_jsonl
from ..utils.validation import require_keys


@dataclass(frozen=True)
class BenchmarkRecord:
    record_type: str
    record_id: str
    payload: dict[str, Any]


class JsonlBenchmarkAdapter:
    """Load a manually prepared policy-augmented benchmark directory.

    Required files are documented in docs/data_format.md. The adapter never
    downloads, authenticates, or calls a model.
    """

    NAMES = frozenset({"locomo", "longmemeval", "memora", "pa_bench", "multi_app"})

    def __init__(self, name: str, root: Path) -> None:
        if name not in self.NAMES:
            raise ValueError(f"unsupported benchmark adapter: {name}")
        self.name = name
        self.root = root

    def validate(self) -> None:
        for filename in ("items.jsonl", "queries.jsonl", "splits.json"):
            path = self.root / filename
            if not path.is_file():
                raise FileNotFoundError(f"missing manually prepared benchmark file: {path}")

    def load_items(self) -> list[dict[str, Any]]:
        self.validate()
        rows = list(read_jsonl(self.root / "items.jsonl"))
        for row in rows:
            require_keys(
                row,
                ["item_id", "text", "source", "label", "created_at", "expires_at"],
                "benchmark item",
            )
        return rows

    def load_queries(self) -> list[dict[str, Any]]:
        self.validate()
        rows = list(read_jsonl(self.root / "queries.jsonl"))
        for row in rows:
            require_keys(
                row,
                ["query_id", "text", "context", "entitled_item_ids", "split"],
                "benchmark query",
            )
        return rows
