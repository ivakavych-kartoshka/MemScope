"""Deterministic, clearly synthetic multi-app smoke-test data."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

from ..data.schemas import (
    ItemState,
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


@dataclass(frozen=True)
class WorkloadConfig:
    """Dimensions of the scaled synthetic multi-app harness workload.

    The generator is fully deterministic: identical configs (including ``seed``)
    produce byte-for-byte identical scenarios, and every item/query carries the
    synthetic notice through the surrounding run metadata.
    """

    seed: int = 7
    apps: int = 3
    topics_per_app: int = 4
    decoys_per_topic: int = 2
    now: float = 1000.0

    def __post_init__(self) -> None:
        if self.apps < 1 or self.topics_per_app < 1 or self.decoys_per_topic < 1:
            raise ValueError("workload dimensions must be positive")
        if not isfinite(self.now):
            raise ValueError("workload clock must be finite")

    @property
    def group_size(self) -> int:
        """Relevant items per topic: one entitled item plus its decoys."""

        return 1 + self.decoys_per_topic


_TOPIC_PURPOSES: tuple[str, ...] = (
    "scheduling",
    "health",
    "shopping",
    "travel",
    "finance",
    "socializing",
)
_TOPIC_TOOLS: tuple[str, ...] = (
    "calendar.read",
    "health.read",
    "shopping.search",
    "travel.plan",
    "finance.read",
    "social.post",
)
_TOPIC_SENSITIVITY: tuple[Sensitivity, ...] = (
    Sensitivity.PERSONAL,
    Sensitivity.HEALTH_SENSITIVE,
    Sensitivity.PERSONAL,
    Sensitivity.SENSITIVE,
)


def oracle_authorized(item: MemoryItem, context: TaskContext, now: float) -> bool:
    """Independent policy oracle: label semantics only, no enforcement code path.

    This deliberately re-derives Equation (3) from ``MemoryLabel`` fields instead
    of calling ``memscope.methods.policy.authorize`` so the harness ground truth
    is computed separately from the implementation under test. The token-expiry
    coordinate is excluded here because the oracle scores policy entitlement, not
    token liveness.
    """

    label = item.label
    return (
        item.state == ItemState.ADMITTED
        and context.purpose in label.purposes
        and context.app_id in label.apps
        and context.tool_id in label.tools
        and context.consumer_id in label.consumers
        and label.not_before <= now < label.expires_at
        and item.provenance.valid
    )


def _workload_item(
    item_id: str,
    text: str,
    *,
    app: str,
    consumer: str,
    namespace: str,
    purposes: Sequence[str],
    tools: Sequence[str],
    sensitivity: Sensitivity,
    not_before: float,
    expires_at: float,
    safety: bool = False,
    utility: float = 0.5,
) -> MemoryItem:
    label = MemoryLabel(
        purposes=frozenset(purposes),
        apps=frozenset({app}),
        tools=frozenset(tools),
        consumers=frozenset({consumer}),
        sensitivity=sensitivity,
        not_before=not_before,
        expires_at=expires_at,
    )
    provenance = Provenance(
        source_app=app,
        source_certificate_digest="synthetic-certificate-digest",
        source_tool=tools[0],
        source_channel="synthetic_generator",
        acquisition_token_digest="synthetic-token-digest",
        created_at=not_before,
        transformation="observation",
        content_digest=content_digest(text),
    )
    return build_item(
        item_id,
        text,
        label,
        provenance,
        namespace=namespace,
        safety_critical=safety,
        hard_pinned=safety,
        future_utility=utility,
        safety_value=1.0 if safety else 0.1,
        sensitivity_cost=float(sensitivity) / 3.0,
        staleness=0.1,
        recomputation_cost=0.8 if safety else 0.2,
    )


def _relevance_tokens(text: str) -> frozenset[str]:
    return frozenset(part for part in text.lower().split() if part)


def generate_scaled_scenario(config: WorkloadConfig | None = None) -> SyntheticScenario:
    """Build a deterministic multi-app workload with a per-query policy oracle.

    Every topic contributes one entitled item (authorized and relevant) and
    ``decoys_per_topic`` relevant-but-unauthorized items spanning four failure
    modes: wrong purpose, wrong tool, expired, and not-yet-valid. ``k`` is set to
    the topic group size so an unscoped ranker surfaces the full group, letting
    the harness measure out-of-scope retrieval deterministically.
    """

    cfg = config or WorkloadConfig()
    now = cfg.now
    suffix = "A" if cfg.seed % 2 else "B"
    items: list[MemoryItem] = []
    queries: list[SyntheticQuery] = []

    for app_index in range(cfg.apps):
        app = f"app{app_index}.pkg"
        consumer = f"consumer{app_index}"
        namespace = consumer
        for topic_index in range(cfg.topics_per_app):
            purpose = _TOPIC_PURPOSES[topic_index % len(_TOPIC_PURPOSES)]
            tool = _TOPIC_TOOLS[topic_index % len(_TOPIC_TOOLS)]
            sensitivity = _TOPIC_SENSITIVITY[topic_index % len(_TOPIC_SENSITIVITY)]
            token = f"topic{app_index}x{topic_index}"
            group: list[MemoryItem] = []

            entitled_id = f"entitled_a{app_index}_t{topic_index}"
            group.append(
                _workload_item(
                    entitled_id,
                    f"{token} {purpose} synthetic reference note {suffix}",
                    app=app,
                    consumer=consumer,
                    namespace=namespace,
                    purposes=[purpose],
                    tools=[tool],
                    sensitivity=sensitivity,
                    not_before=now - 50.0,
                    expires_at=now + 200.0,
                    safety=sensitivity >= Sensitivity.SENSITIVE,
                    utility=1.0,
                )
            )

            for decoy_index in range(cfg.decoys_per_topic):
                decoy_id = f"decoy_a{app_index}_t{topic_index}_d{decoy_index}"
                decoy_purposes = [purpose]
                decoy_tools = [tool]
                not_before = now - 50.0
                expires_at = now + 200.0
                mode = decoy_index % 4
                if mode == 0:
                    decoy_purposes = [f"{purpose}_unrelated"]
                elif mode == 1:
                    decoy_tools = [f"{tool}.other"]
                elif mode == 2:
                    expires_at = now - 10.0
                else:
                    not_before = now + 10.0
                group.append(
                    _workload_item(
                        decoy_id,
                        f"{token} {purpose} synthetic decoy {mode} {suffix}",
                        app=app,
                        consumer=consumer,
                        namespace=namespace,
                        purposes=decoy_purposes,
                        tools=decoy_tools,
                        sensitivity=Sensitivity.SENSITIVE,
                        not_before=not_before,
                        expires_at=expires_at,
                    )
                )

            items.extend(group)
            relevant = [
                item for item in group if token in _relevance_tokens(item.payload)
            ]
            context = TaskContext(
                app, tool, consumer, purpose, now, f"n{app_index}_{topic_index}"
            )
            queries.append(
                SyntheticQuery(
                    f"q_a{app_index}_t{topic_index}",
                    f"{token} {purpose}",
                    context,
                    frozenset(
                        item.item_id
                        for item in relevant
                        if oracle_authorized(item, context, now)
                    ),
                    frozenset(
                        item.item_id
                        for item in relevant
                        if not oracle_authorized(item, context, now)
                    ),
                    k=cfg.group_size,
                )
            )

    return SyntheticScenario(now=now, items=tuple(items), queries=tuple(queries))


class MutableClock:
    def __init__(self, now: float) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now
