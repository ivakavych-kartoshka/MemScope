"""Deterministic, clearly synthetic multi-app smoke-test data."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..data.schemas import (
    MemoryItem,
    MemoryLabel,
    Provenance,
    Sensitivity,
    TaskContext,
)
from ..methods.integrity import content_digest
from ..methods.writes import build_item

SYNTHETIC_NOTICE = "synthetic smoke-test output, not a paper result"


@dataclass(frozen=True)
class SyntheticQuery:
    query_id: str
    text: str
    context: TaskContext
    entitled_ids: frozenset[str]
    unauthorized_ids: frozenset[str]
    k: int = 3


@dataclass(frozen=True)
class SyntheticScenario:
    now: float
    items: tuple[MemoryItem, ...]
    queries: tuple[SyntheticQuery, ...]


def _item(
    item_id: str,
    text: str,
    purposes: Sequence[str],
    tools: Sequence[str],
    sensitivity: Sensitivity,
    expires_at: float,
    safety: bool = False,
    utility: float = 0.5,
) -> MemoryItem:
    label = MemoryLabel(
        purposes=frozenset(purposes),
        apps=frozenset({"assistant.pkg"}),
        tools=frozenset(tools),
        consumers=frozenset({"primary_assistant"}),
        sensitivity=sensitivity,
        not_before=900.0,
        expires_at=expires_at,
    )
    provenance = Provenance(
        source_app="assistant.pkg",
        source_certificate_digest="synthetic-certificate-digest",
        source_tool=tools[0],
        source_channel="synthetic_generator",
        acquisition_token_digest="synthetic-token-digest",
        created_at=900.0,
        transformation="observation",
        content_digest=content_digest(text),
    )
    return build_item(
        item_id,
        text,
        label,
        provenance,
        namespace="primary_assistant",
        safety_critical=safety,
        hard_pinned=safety,
        future_utility=utility,
        safety_value=1.0 if safety else 0.1,
        sensitivity_cost=float(sensitivity) / 3.0,
        staleness=0.1,
        recomputation_cost=0.8 if safety else 0.2,
    )


def generate_synthetic_scenario(seed: int = 7) -> SyntheticScenario:
    """Create policy-oracle records without using a real person or benchmark."""

    # Seed influences stable harmless wording only; repeated calls are byte-for-byte stable.
    suffix = "A" if seed % 2 else "B"
    items = (
        _item(
            "calendar_free",
            f"Synthetic calendar is free Tuesday at 10 AM slot {suffix}",
            ["scheduling"],
            ["calendar.read"],
            Sensitivity.PERSONAL,
            1100.0,
        ),
        _item(
            "allergy",
            "Synthetic profile has a peanut allergy",
            ["health", "food_safety"],
            ["health.read", "grocery.allergen_check"],
            Sensitivity.HEALTH_SENSITIVE,
            1400.0,
            safety=True,
            utility=1.0,
        ),
        _item(
            "shopping_color",
            "Synthetic shopping preference is blue",
            ["shopping", "personalized_ads"],
            ["shopping.search", "ads.rank"],
            Sensitivity.PERSONAL,
            1500.0,
        ),
        _item(
            "clinic",
            "Synthetic clinic preference is Riverside Clinic",
            ["health", "scheduling"],
            ["health.preference.read"],
            Sensitivity.HEALTH_SENSITIVE,
            1300.0,
            safety=True,
        ),
        _item(
            "expired_travel",
            "Synthetic expired passport reminder",
            ["travel"],
            ["travel.plan"],
            Sensitivity.SENSITIVE,
            999.0,
        ),
    )
    now = 1000.0
    queries = (
        SyntheticQuery(
            "q_schedule",
            "calendar free Tuesday",
            TaskContext(
                "assistant.pkg", "calendar.read", "primary_assistant", "scheduling", now, "n1"
            ),
            frozenset({"calendar_free"}),
            frozenset({"allergy", "shopping_color", "clinic", "expired_travel"}),
        ),
        SyntheticQuery(
            "q_food",
            "peanut allergy food",
            TaskContext(
                "assistant.pkg",
                "grocery.allergen_check",
                "primary_assistant",
                "food_safety",
                now,
                "n2",
            ),
            frozenset({"allergy"}),
            frozenset({"calendar_free", "shopping_color", "clinic", "expired_travel"}),
        ),
        SyntheticQuery(
            "q_ads",
            "preference allergy blue",
            TaskContext(
                "assistant.pkg", "ads.rank", "primary_assistant", "personalized_ads", now, "n3"
            ),
            frozenset({"shopping_color"}),
            frozenset({"allergy", "calendar_free", "clinic", "expired_travel"}),
        ),
    )
    return SyntheticScenario(now=now, items=items, queries=queries)


class MutableClock:
    def __init__(self, now: float) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now
