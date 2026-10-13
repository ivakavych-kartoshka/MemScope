from dataclasses import replace

import pytest
from conftest import make_context

from memscope.methods.tokens import TokenError, TokenIssuer


def test_token_authenticity_and_caller_binding(issuer: TokenIssuer) -> None:
    context = make_context()
    token = issuer.issue(context, 30.0, 1)
    assert issuer.verify(token, "assistant.pkg", ("calendar.read",), 20.0, 1) == context
    with pytest.raises(TokenError):
        issuer.verify(token, "attacker.pkg", ("calendar.read",), 20.0, 1, consume=False)


def test_token_field_mutation_fails(issuer: TokenIssuer) -> None:
    token = issuer.issue(make_context(), 30.0, 1)
    mutated = replace(token, expires_at=40.0)
    with pytest.raises(TokenError, match="signature"):
        issuer.verify(mutated, "assistant.pkg", ("calendar.read",), 20.0, 1)


def test_one_shot_replay_fails(issuer: TokenIssuer) -> None:
    token = issuer.issue(make_context(), 30.0, 1, one_shot=True)
    issuer.verify(token, "assistant.pkg", ("calendar.read",), 20.0, 1)
    with pytest.raises(TokenError, match="exhausted"):
        issuer.verify(token, "assistant.pkg", ("calendar.read",), 20.0, 1)


def test_child_token_attenuation(issuer: TokenIssuer) -> None:
    parent = issuer.issue(
        make_context(tool="calendar.read"),
        50.0,
        1,
        permitted_tools=frozenset({"calendar.read", "shared"}),
        max_queries=5,
    )
    child = issuer.attenuate(parent, make_context(tool="shared", now=21.0), 40.0, 1, 2)
    assert child.permitted_tools == frozenset({"shared"})
    with pytest.raises(TokenError, match="purpose"):
        issuer.attenuate(parent, make_context(purpose="health", now=21.0), 40.0, 1, 2)


def test_swapped_app_binding_fails(issuer: TokenIssuer) -> None:
    token = issuer.issue(make_context(), 30.0, 1)
    swapped = replace(token, context=replace(token.context, app_id="attacker.pkg"))
    with pytest.raises(TokenError, match="signature"):
        issuer.verify(swapped, "assistant.pkg", ("calendar.read",), 20.0, 1)


def test_unregistered_tool_rejected(issuer: TokenIssuer) -> None:
    token = issuer.issue(make_context(), 30.0, 1)
    with pytest.raises(TokenError, match="unpermitted tool"):
        issuer.verify(token, "assistant.pkg", ("evil.tool", "calendar.read"), 20.0, 1)


def test_rolled_back_clock_rejected(issuer: TokenIssuer) -> None:
    token = issuer.issue(make_context(now=20.0), 30.0, 1)
    with pytest.raises(TokenError, match="not currently valid"):
        issuer.verify(token, "assistant.pkg", ("calendar.read",), 15.0, 1)
