"""Transactional in-memory reference store; Android storage is an adapter."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from dataclasses import replace

from ..data.schemas import AuditEvent, ItemState, MemoryItem


class InMemoryStore:
    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}
        self._audit: list[AuditEvent] = []
        self._tombstones: dict[str, str] = {}
        self._epoch = 1
        self._lock = threading.RLock()

    @property
    def policy_epoch(self) -> int:
        with self._lock:
            return self._epoch

    def increment_epoch(self) -> int:
        with self._lock:
            self._epoch += 1
            return self._epoch

    def commit(self, item: MemoryItem, increment_epoch: bool = False) -> None:
        with self._lock:
            if item.item_id in self._items:
                raise ValueError(f"duplicate item ID: {item.item_id}")
            self._items[item.item_id] = item
            if increment_epoch:
                self._epoch += 1

    def replace(self, item: MemoryItem, increment_epoch: bool = True) -> None:
        with self._lock:
            if item.item_id not in self._items:
                raise KeyError(item.item_id)
            self._items[item.item_id] = item
            if increment_epoch:
                self._epoch += 1

    def get(self, item_id: str) -> MemoryItem | None:
        with self._lock:
            return self._items.get(item_id)

    def snapshot(self) -> tuple[int, tuple[MemoryItem, ...]]:
        with self._lock:
            return self._epoch, tuple(self._items.values())

    def read_parents(self, parent_ids: Sequence[str]) -> tuple[int, tuple[MemoryItem, ...]]:
        with self._lock:
            parents = tuple(self._items[item_id] for item_id in parent_ids if item_id in self._items)
            return self._epoch, parents

    def set_state(self, item_id: str, state: ItemState) -> None:
        with self._lock:
            item = self._items[item_id]
            self._items[item_id] = replace(item, state=state)
            self._epoch += 1

    def remove(self, item_id: str) -> MemoryItem:
        with self._lock:
            item = self._items.pop(item_id)
            self._tombstones[item_id] = item.integrity_digest
            self._epoch += 1
            return item

    def tombstone_digest(self, item_id: str) -> str | None:
        with self._lock:
            return self._tombstones.get(item_id)

    def bytes_used(self) -> int:
        with self._lock:
            return sum(item.size_bytes for item in self._items.values())

    def append_audit(self, event: AuditEvent) -> None:
        with self._lock:
            self._audit.append(event)

    def audit_events(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._audit)
