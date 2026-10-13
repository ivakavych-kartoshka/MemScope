"""Content and label integrity helpers for the reference model."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..data.schemas import MemoryItem, MemoryLabel, Provenance


def content_digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def item_integrity_digest(
    item_id: str, payload: str, label: MemoryLabel, provenance: Provenance, version: int
) -> str:
    value: dict[str, Any] = {
        "item_id": item_id,
        "payload_digest": content_digest(payload),
        "label": label.to_mapping(),
        "provenance": {
            "source_app": provenance.source_app,
            "source_certificate_digest": provenance.source_certificate_digest,
            "source_tool": provenance.source_tool,
            "source_channel": provenance.source_channel,
            "acquisition_token_digest": provenance.acquisition_token_digest,
            "created_at": provenance.created_at,
            "parent_ids": list(provenance.parent_ids),
            "parent_digests": list(provenance.parent_digests),
            "transformation": provenance.transformation,
            "content_digest": provenance.content_digest,
            "valid": provenance.valid,
        },
        "version": version,
    }
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def integrity_ok(item: MemoryItem) -> bool:
    expected = item_integrity_digest(
        item.item_id, item.payload, item.label, item.provenance, item.version
    )
    return expected == item.integrity_digest and item.provenance.content_digest == content_digest(
        item.payload
    )
