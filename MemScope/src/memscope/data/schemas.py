"""Validated paper-level objects for MemScope (paper Sections 3-4)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum, IntEnum
from math import isfinite
from typing import Any


class Sensitivity(IntEnum):
    """Ordered sensitivity; larger values require at least as restrictive controls."""

    PUBLIC = 0
    PERSONAL = 1
    SENSITIVE = 2
    HEALTH_SENSITIVE = 3


class ItemState(str, Enum):
    PROPOSED = "proposed"
    ADMITTED = "admitted"
    QUARANTINED = "quarantined"
    EXPIRED = "expired"
    TOMBSTONED = "tombstoned"
    COMPACTED = "compacted"


@dataclass(frozen=True)
class TaskContext:
    """Equation (1): authenticated task context.

    `task_time` is the signed task-start time. Retrieval uses a fresh trusted clock
    value for the authorization and final-release checks.
    """

    app_id: str
    tool_id: str | None
    consumer_id: str
    purpose: str
    task_time: float
    nonce: str

    def __post_init__(self) -> None:
        if not self.app_id or not self.consumer_id or not self.purpose or not self.nonce:
            raise ValueError("task context identities, purpose, and nonce must be non-empty")
        if not isfinite(self.task_time):
            raise ValueError("task_time must be finite")


@dataclass(frozen=True)
class MemoryLabel:
    """Equation (2): enforceable label coordinates."""

    purposes: frozenset[str]
    apps: frozenset[str]
    tools: frozenset[str | None]
    consumers: frozenset[str]
    sensitivity: Sensitivity
    not_before: float
    expires_at: float

    def __post_init__(self) -> None:
        if not isfinite(self.not_before) or not isfinite(self.expires_at):
            raise ValueError("label times must be finite")
        if self.not_before >= self.expires_at:
            raise ValueError("label requires not_before < expires_at")
        if not isinstance(self.sensitivity, Sensitivity):
            object.__setattr__(self, "sensitivity", Sensitivity(self.sensitivity))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> MemoryLabel:
        return cls(
            purposes=frozenset(value["purposes"]),
            apps=frozenset(value["apps"]),
            tools=frozenset(value["tools"]),
            consumers=frozenset(value["consumers"]),
            sensitivity=Sensitivity[value["sensitivity"]]
            if isinstance(value["sensitivity"], str)
            else Sensitivity(value["sensitivity"]),
            not_before=float(value["not_before"]),
            expires_at=float(value["expires_at"]),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "purposes": sorted(self.purposes),
            "apps": sorted(self.apps),
            "tools": sorted(self.tools, key=lambda x: "" if x is None else x),
            "consumers": sorted(self.consumers),
            "sensitivity": self.sensitivity.name,
            "not_before": self.not_before,
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True)
class Provenance:
    source_app: str
    source_certificate_digest: str
    source_tool: str | None
    source_channel: str
    acquisition_token_digest: str
    created_at: float
    parent_ids: tuple[str, ...] = ()
    parent_digests: tuple[str, ...] = ()
    transformation: str = "observation"
    content_digest: str = ""
    valid: bool = True

    def __post_init__(self) -> None:
        if not self.source_app or not self.source_channel or not self.transformation:
            raise ValueError("provenance source and transformation must be non-empty")
        if len(self.parent_ids) != len(self.parent_digests):
            raise ValueError("parent IDs and digests must have equal length")
        if len(set(self.parent_ids)) != len(self.parent_ids):
            raise ValueError("parent IDs must be unique")
        if not isfinite(self.created_at):
            raise ValueError("provenance creation time must be finite")


@dataclass
class MemoryItem:
    """Equation (2) plus lifecycle, ranking, and compaction metadata."""

    item_id: str
    payload: str
    label: MemoryLabel
    provenance: Provenance
    integrity_digest: str
    state: ItemState = ItemState.ADMITTED
    version: int = 1
    namespace: str = "default"
    safety_critical: bool = False
    hard_pinned: bool = False
    future_utility: float = 0.0
    safety_value: float = 0.0
    sensitivity_cost: float = 0.0
    staleness: float = 0.0
    recomputation_cost: float = 0.0
    size_bytes: int = 0

    def __post_init__(self) -> None:
        if not self.item_id or not self.integrity_digest:
            raise ValueError("item ID and integrity digest must be non-empty")
        if self.version < 1:
            raise ValueError("item version must be positive")
        if self.size_bytes == 0:
            self.size_bytes = max(1, len(self.payload.encode("utf-8")))
        if self.size_bytes < 1:
            raise ValueError("item size must be positive")


@dataclass(frozen=True)
class RetrievalToken:
    context: TaskContext
    issued_at: float
    expires_at: float
    policy_epoch: int
    permitted_tools: frozenset[str | None]
    max_queries: int
    one_shot: bool
    parent_token_digest: str | None
    token_id: str
    signature: str

    def __post_init__(self) -> None:
        if self.issued_at >= self.expires_at:
            raise ValueError("token requires issued_at < expires_at")
        if self.max_queries < 1:
            raise ValueError("max_queries must be positive")
        if self.context.tool_id not in self.permitted_tools:
            raise ValueError("active tool must be in token permitted_tools")


@dataclass(frozen=True)
class AuditEvent:
    timestamp: float
    token_id: str
    app_id: str
    purpose: str
    tool_id: str | None
    item_ids: tuple[str, ...]
    decision: str
    bytes_returned: int
    policy_epoch: int
    detail: str = ""


@dataclass(frozen=True)
class RetrievalResult:
    items: tuple[MemoryItem, ...]
    decision: str
    restarts: int
    candidate_count: int
    authorized_count: int


@dataclass(frozen=True)
class DerivationProposal:
    item_id: str
    payload: str
    parent_ids: tuple[str, ...]
    proposed_label: MemoryLabel
    transformation: str
    expected_versions: Mapping[str, int] = field(default_factory=dict)
    expected_digests: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AdmissionResult:
    status: str
    item: MemoryItem | None
    reason: str


@dataclass(frozen=True)
class QueryEvaluation:
    query_id: str
    returned_ids: tuple[str, ...]
    entitled_ids: frozenset[str]
    unauthorized_ids: frozenset[str]
    latency_ms: float = 0.0


def as_jsonable(value: Any) -> Any:
    """Recursively convert dataclass/enum/set objects to JSON-compatible values."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (frozenset, set, tuple)):
        return [as_jsonable(v) for v in value]
    if hasattr(value, "__dataclass_fields__"):
        return {k: as_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [as_jsonable(v) for v in value]
    return value
