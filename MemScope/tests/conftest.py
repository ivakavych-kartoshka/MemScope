from collections.abc import Sequence
from typing import Any

import pytest

from memscope.data.schemas import MemoryItem, MemoryLabel, Provenance, Sensitivity, TaskContext
from memscope.methods.integrity import content_digest
from memscope.methods.store import InMemoryStore
from memscope.methods.tokens import TokenIssuer
from memscope.methods.writes import build_item


@pytest.fixture
def signing_key() -> bytes:
    return b"0123456789abcdef-test-key"


@pytest.fixture
def issuer(signing_key: bytes) -> TokenIssuer:
    return TokenIssuer(signing_key)


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


def make_label(
    purposes: Sequence[str] = ("scheduling",),
    apps: Sequence[str] = ("assistant.pkg",),
    tools: Sequence[str | None] = ("calendar.read",),
    consumers: Sequence[str] = ("primary_assistant",),
    sensitivity: Sensitivity = Sensitivity.PERSONAL,
    not_before: float = 10.0,
    expires_at: float = 100.0,
) -> MemoryLabel:
    return MemoryLabel(
        frozenset(purposes),
        frozenset(apps),
        frozenset(tools),
        frozenset(consumers),
        sensitivity,
        not_before,
        expires_at,
    )


def make_context(
    purpose: str = "scheduling", tool: str | None = "calendar.read", now: float = 20.0
) -> TaskContext:
    return TaskContext("assistant.pkg", tool, "primary_assistant", purpose, now, "nonce")


def make_item(
    item_id: str = "m1", payload: str = "calendar free Tuesday", **kwargs: Any
) -> MemoryItem:
    label = kwargs.pop("label", make_label())
    provenance = Provenance(
        source_app="assistant.pkg",
        source_certificate_digest="cert",
        source_tool="calendar.read",
        source_channel="test",
        acquisition_token_digest="token",
        created_at=10.0,
        transformation="observation",
        content_digest=content_digest(payload),
    )
    return build_item(item_id, payload, label, provenance, **kwargs)
