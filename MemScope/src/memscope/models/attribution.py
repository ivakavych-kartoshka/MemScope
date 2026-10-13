"""Attribution-checker contracts for paper Section 7.4."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from ..data.schemas import MemoryItem


@dataclass(frozen=True)
class AttributionDecision:
    status: str  # supported, unsupported, or uncertain
    reason: str


class AttributionVerifier(ABC):
    @abstractmethod
    def verify(
        self, payload: str, parents: Sequence[MemoryItem], transformation: str
    ) -> AttributionDecision:
        """Check content support; this decision can never widen a label."""


class ExtractiveAttributionVerifier(AttributionVerifier):
    """Exact/lexical verifier for extractive or structured synthetic transforms."""

    def verify(
        self, payload: str, parents: Sequence[MemoryItem], transformation: str
    ) -> AttributionDecision:
        source = " ".join(parent.payload for parent in parents).lower()
        if transformation in {"extractive", "selection"}:
            if payload.lower() in source:
                return AttributionDecision("supported", "exact extractive span found")
            return AttributionDecision("unsupported", "extractive span absent from parents")
        if transformation == "structured":
            terms = set(re.findall(r"[a-z0-9]+", payload.lower()))
            source_terms = set(re.findall(r"[a-z0-9]+", source))
            if terms <= source_terms:
                return AttributionDecision("supported", "all structured terms occur in parents")
            return AttributionDecision("unsupported", "structured output adds unsupported terms")
        return AttributionDecision("uncertain", "abstractive verification requires external model")


class AlwaysAcceptVerifier(AttributionVerifier):
    """Negative-control verifier. Never use as evidence of semantic integrity."""

    def verify(
        self, payload: str, parents: Sequence[MemoryItem], transformation: str
    ) -> AttributionDecision:
        return AttributionDecision("supported", "TEST-ONLY always-accept negative control")
