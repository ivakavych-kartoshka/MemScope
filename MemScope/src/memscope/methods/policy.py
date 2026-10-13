"""Authorization and label lattice operations (Equations 3-5)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from ..data.schemas import ItemState, MemoryItem, MemoryLabel, TaskContext


def authorize(
    item: MemoryItem,
    context: TaskContext,
    now: float,
    token_expires_at: float,
) -> bool:
    """Equation (3): authorize an item for an authenticated context and release time."""

    label = item.label
    return (
        item.state == ItemState.ADMITTED
        and context.purpose in label.purposes
        and context.app_id in label.apps
        and context.tool_id in label.tools
        and context.consumer_id in label.consumers
        and label.not_before <= now < label.expires_at
        and now < token_expires_at
        and item.provenance.valid
    )


def label_no_more_permissive(candidate: MemoryLabel, bound: MemoryLabel) -> bool:
    """Return `candidate <= bound` in the paper's coordinate order."""

    return (
        candidate.purposes <= bound.purposes
        and candidate.apps <= bound.apps
        and candidate.tools <= bound.tools
        and candidate.consumers <= bound.consumers
        and candidate.sensitivity >= bound.sensitivity
        and candidate.not_before >= bound.not_before
        and candidate.expires_at <= bound.expires_at
    )


def meet_labels(labels: Sequence[MemoryLabel]) -> MemoryLabel:
    """Equation (4): conservative meet of a nonempty parent-label set."""

    if not labels:
        raise ValueError("cannot compute meet of an empty parent set")
    purposes = set(labels[0].purposes)
    apps = set(labels[0].apps)
    tools = set(labels[0].tools)
    consumers = set(labels[0].consumers)
    for label in labels[1:]:
        purposes.intersection_update(label.purposes)
        apps.intersection_update(label.apps)
        tools.intersection_update(label.tools)
        consumers.intersection_update(label.consumers)
    not_before = max(label.not_before for label in labels)
    expires_at = min(label.expires_at for label in labels)
    if not_before >= expires_at:
        raise ValueError("parent labels have an empty temporal intersection")
    return MemoryLabel(
        purposes=frozenset(purposes),
        apps=frozenset(apps),
        tools=frozenset(tools),
        consumers=frozenset(consumers),
        sensitivity=max(label.sensitivity for label in labels),
        not_before=not_before,
        expires_at=expires_at,
    )


def empty_required_scope(label: MemoryLabel) -> bool:
    return not label.purposes or not label.apps or not label.tools or not label.consumers


def authorized_view(
    items: Iterable[MemoryItem], context: TaskContext, now: float, token_expires_at: float
) -> list[MemoryItem]:
    """Equation (5): construct the authorized candidate view before ranking."""

    return [item for item in items if authorize(item, context, now, token_expires_at)]
