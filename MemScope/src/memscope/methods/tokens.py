"""Task-rooted signed-token reference protocol (paper Section 7.1)."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections.abc import Sequence

from ..data.schemas import RetrievalToken, TaskContext


class TokenError(ValueError):
    pass


def _token_payload(
    context: TaskContext,
    issued_at: float,
    expires_at: float,
    policy_epoch: int,
    permitted_tools: frozenset[str | None],
    max_queries: int,
    one_shot: bool,
    parent_token_digest: str | None,
    token_id: str,
) -> bytes:
    value = {
        "context": {
            "app_id": context.app_id,
            "tool_id": context.tool_id,
            "consumer_id": context.consumer_id,
            "purpose": context.purpose,
            "task_time": context.task_time,
            "nonce": context.nonce,
        },
        "issued_at": issued_at,
        "expires_at": expires_at,
        "policy_epoch": policy_epoch,
        "permitted_tools": sorted(permitted_tools, key=lambda x: "" if x is None else x),
        "max_queries": max_queries,
        "one_shot": one_shot,
        "parent_token_digest": parent_token_digest,
        "token_id": token_id,
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class TokenIssuer:
    """HMAC-based reference issuer.

    Production must replace this with OS/Keystore-backed signatures and Binder identity.
    """

    def __init__(self, signing_key: bytes) -> None:
        if len(signing_key) < 16:
            raise ValueError("reference signing key must contain at least 16 bytes")
        self._key = signing_key
        self._uses: dict[str, int] = {}

    def issue(
        self,
        context: TaskContext,
        expires_at: float,
        policy_epoch: int,
        permitted_tools: frozenset[str | None] | None = None,
        max_queries: int = 16,
        one_shot: bool = False,
        parent_token_digest: str | None = None,
    ) -> RetrievalToken:
        tools = permitted_tools or frozenset({context.tool_id})
        token_id = secrets.token_hex(16)
        payload = _token_payload(
            context,
            context.task_time,
            expires_at,
            policy_epoch,
            tools,
            max_queries,
            one_shot,
            parent_token_digest,
            token_id,
        )
        signature = hmac.new(self._key, payload, hashlib.sha256).hexdigest()
        return RetrievalToken(
            context=context,
            issued_at=context.task_time,
            expires_at=expires_at,
            policy_epoch=policy_epoch,
            permitted_tools=tools,
            max_queries=max_queries,
            one_shot=one_shot,
            parent_token_digest=parent_token_digest,
            token_id=token_id,
            signature=signature,
        )

    def digest(self, token: RetrievalToken) -> str:
        return hashlib.sha256((token.token_id + token.signature).encode("utf-8")).hexdigest()

    def verify(
        self,
        token: RetrievalToken,
        binder_caller: str,
        tool_chain: Sequence[str | None],
        now: float,
        current_epoch: int,
        consume: bool = True,
    ) -> TaskContext:
        payload = _token_payload(
            token.context,
            token.issued_at,
            token.expires_at,
            token.policy_epoch,
            token.permitted_tools,
            token.max_queries,
            token.one_shot,
            token.parent_token_digest,
            token.token_id,
        )
        expected = hmac.new(self._key, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, token.signature):
            raise TokenError("invalid token signature")
        if binder_caller != token.context.app_id:
            raise TokenError("Binder caller does not match token app")
        if not tool_chain or tool_chain[-1] != token.context.tool_id:
            raise TokenError("active tool chain does not match token")
        if any(tool not in token.permitted_tools for tool in tool_chain):
            raise TokenError("tool chain contains an unpermitted tool")
        if now < token.issued_at or now >= token.expires_at:
            raise TokenError("token is not currently valid")
        if token.policy_epoch != current_epoch:
            raise TokenError("stale policy epoch")
        uses = self._uses.get(token.token_id, 0)
        limit = 1 if token.one_shot else token.max_queries
        if uses >= limit:
            raise TokenError("token replay/query budget exhausted")
        if consume:
            self._uses[token.token_id] = uses + 1
        return token.context

    def attenuate(
        self,
        parent: RetrievalToken,
        child_context: TaskContext,
        expires_at: float,
        policy_epoch: int,
        max_queries: int,
    ) -> RetrievalToken:
        """Equation (12): issue a fail-closed child whose scope is no broader."""

        if child_context.app_id != parent.context.app_id:
            raise TokenError("child app cannot differ from parent app")
        if child_context.consumer_id != parent.context.consumer_id:
            raise TokenError("child consumer cannot differ from parent consumer")
        if child_context.purpose != parent.context.purpose:
            raise TokenError("child purpose cannot differ from parent purpose")
        if child_context.tool_id not in parent.permitted_tools:
            raise TokenError("child tool is outside parent permitted tools")
        if expires_at > parent.expires_at:
            raise TokenError("child expiry cannot exceed parent expiry")
        if max_queries > parent.max_queries:
            raise TokenError("child query budget cannot exceed parent budget")
        if policy_epoch != parent.policy_epoch:
            raise TokenError("child and parent epochs must match")
        return self.issue(
            child_context,
            expires_at=expires_at,
            policy_epoch=policy_epoch,
            permitted_tools=frozenset({child_context.tool_id}),
            max_queries=max_queries,
            one_shot=parent.one_shot,
            parent_token_digest=self.digest(parent),
        )
