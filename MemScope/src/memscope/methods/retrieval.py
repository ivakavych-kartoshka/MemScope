"""MemScope Algorithm 1: filter before rank, then revalidate before release."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence

from ..data.schemas import AuditEvent, MemoryItem, RetrievalResult, RetrievalToken, TaskContext
from ..models.ranking import LexicalRanker, Ranker
from .integrity import integrity_ok
from .policy import authorize
from .store import InMemoryStore
from .tokens import TokenError, TokenIssuer


class RetrievalDenied(PermissionError):
    pass


class PolicyChurnError(RuntimeError):
    pass


def _projection_candidate(item: MemoryItem, context: TaskContext, now: float) -> bool:
    """Indexable over-approximation; never a trusted authorization decision."""

    label = item.label
    return (
        context.purpose in label.purposes
        and context.app_id in label.apps
        and context.tool_id in label.tools
        and context.consumer_id in label.consumers
        and label.not_before <= now < label.expires_at
    )


def authorized_view(
    items: Sequence[MemoryItem], context: TaskContext, now: float, token_expiry: float
) -> list[MemoryItem]:
    """Equation (5), including integrity validation before a ranker sees payloads."""

    return [
        item
        for item in items
        if integrity_ok(item) and authorize(item, context, now, token_expiry)
    ]


class MemScopeService:
    def __init__(
        self,
        store: InMemoryStore,
        issuer: TokenIssuer,
        ranker: Ranker | None = None,
        clock: Callable[[], float] = time.monotonic,
        max_restarts: int = 2,
    ) -> None:
        self.store = store
        self.issuer = issuer
        self.ranker = ranker or LexicalRanker()
        self.clock = clock
        self.max_restarts = max_restarts

    def retrieve(
        self,
        token: RetrievalToken,
        query: str,
        k: int,
        binder_caller: str,
        tool_chain: Sequence[str | None],
    ) -> RetrievalResult:
        """Algorithm 1 with bounded restart and appendix-required final recheck."""

        if k < 0:
            raise ValueError("k must be non-negative")
        now = self.clock()
        try:
            context = self.issuer.verify(
                token,
                binder_caller,
                tool_chain,
                now,
                self.store.policy_epoch,
                consume=True,
            )
        except TokenError as exc:
            self._audit(token, (), "DENY", str(exc), now)
            raise RetrievalDenied("request denied") from exc

        for restart in range(self.max_restarts + 1):
            epoch, items = self.store.snapshot()
            now = self.clock()
            candidates = [item for item in items if _projection_candidate(item, context, now)]
            authorized = authorized_view(candidates, context, now, token.expires_at)
            ranked = self.ranker.rank(query, authorized, k)
            input_ids = {item.item_id for item in authorized}
            if any(item.item_id not in input_ids for item in ranked):
                raise RuntimeError("ranker violated confinement contract")

            release_now = self.clock()
            if epoch != self.store.policy_epoch or release_now >= token.expires_at:
                if restart == self.max_restarts:
                    self._audit(token, (), "TRANSIENT_DENY", "policy churn or expiry", release_now)
                    raise PolicyChurnError("bounded retrieval restart exhausted")
                try:
                    context = self.issuer.verify(
                        token,
                        binder_caller,
                        tool_chain,
                        release_now,
                        self.store.policy_epoch,
                        consume=False,
                    )
                except TokenError as exc:
                    self._audit(token, (), "DENY", str(exc), release_now)
                    raise RetrievalDenied("request denied") from exc
                continue

            # Conservative implementation of the appendix final-check-freshness lemma.
            final_items = tuple(
                item
                for item in ranked
                if integrity_ok(item)
                and authorize(item, context, release_now, token.expires_at)
                and self.store.get(item.item_id) is item
            )
            if len(final_items) != len(ranked):
                if restart == self.max_restarts:
                    raise PolicyChurnError("item changed during final authorization")
                continue
            self._audit(token, final_items, "ALLOW", "", release_now)
            return RetrievalResult(
                items=final_items,
                decision="ALLOW",
                restarts=restart,
                candidate_count=len(candidates),
                authorized_count=len(authorized),
            )
        raise AssertionError("unreachable")

    def _audit(
        self,
        token: RetrievalToken,
        items: Sequence[MemoryItem],
        decision: str,
        detail: str,
        now: float,
    ) -> None:
        self.store.append_audit(
            AuditEvent(
                timestamp=now,
                token_id=token.token_id,
                app_id=token.context.app_id,
                purpose=token.context.purpose,
                tool_id=token.context.tool_id,
                item_ids=tuple(item.item_id for item in items),
                decision=decision,
                bytes_returned=sum(item.size_bytes for item in items),
                policy_epoch=self.store.policy_epoch,
                detail=detail,
            )
        )
