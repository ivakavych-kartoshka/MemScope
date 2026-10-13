import random

from conftest import make_context, make_item, make_label

from memscope.data.schemas import DerivationProposal, Sensitivity
from memscope.methods.derivation import admit_derivation
from memscope.methods.policy import label_no_more_permissive, meet_labels
from memscope.methods.store import InMemoryStore
from memscope.methods.tokens import TokenIssuer


def test_meet_monotonicity_property() -> None:
    rng = random.Random(123)
    universe = ["a", "b", "c", "d"]
    for _ in range(100):
        labels = []
        for _parent in range(rng.randint(1, 5)):
            purposes = tuple(x for x in universe if rng.random() < 0.7) or ("a",)
            apps = tuple(x for x in universe if rng.random() < 0.7) or ("a",)
            tools = tuple(x for x in universe if rng.random() < 0.7) or ("a",)
            consumers = tuple(x for x in universe if rng.random() < 0.7) or ("a",)
            labels.append(
                make_label(
                    purposes=purposes,
                    apps=apps,
                    tools=tools,
                    consumers=consumers,
                    sensitivity=Sensitivity(rng.randrange(4)),
                    not_before=rng.uniform(0, 10),
                    expires_at=rng.uniform(20, 40),
                )
            )
        meet = meet_labels(labels)
        assert all(label_no_more_permissive(meet, parent) for parent in labels)


def test_multi_token_composition_never_widens_policy(
    store: InMemoryStore, issuer: TokenIssuer
) -> None:
    """Property (Theorem 2): any admitted multi-token derivation is no broader than every parent."""

    rng = random.Random(456)
    tools = ["calendar.read", "health.read", "travel.read"]
    admitted = 0
    for i in range(80):
        n_tokens = rng.randint(1, 3)
        token_tools = [rng.choice(tools) for _ in range(n_tokens)]
        parents = []
        labels = []
        for j in range(rng.randint(1, 3)):
            tool = rng.choice(token_tools)
            label = make_label(
                purposes=("scheduling",),
                apps=("assistant.pkg",),
                tools=(tool,),
                consumers=("primary_assistant",),
                not_before=10.0,
                expires_at=50.0,
            )
            item = make_item(f"m{i}_{j}", f"note {i} item {j}", label=label)
            store.commit(item)
            parents.append(item)
            labels.append(label)
        tokens = [
            issuer.issue(make_context(tool=tool, purpose="scheduling"), 60.0, store.policy_epoch)
            for tool in token_tools
        ]
        try:
            meet = meet_labels(labels)
        except ValueError:
            continue
        proposal = DerivationProposal(
            f"d{i}", parents[0].payload, tuple(p.item_id for p in parents), meet, "extractive"
        )
        result = admit_derivation(store, issuer, tokens, proposal, "assistant.pkg", 20.0)
        assert result.status in {"ADMITTED", "QUARANTINED", "REJECT"}
        if result.status == "ADMITTED":
            assert result.item is not None
            assert all(
                label_no_more_permissive(result.item.label, parent.label) for parent in parents
            )
            admitted += 1
    assert admitted > 0


def test_multi_token_context_mismatch_always_rejects(
    store: InMemoryStore, issuer: TokenIssuer
) -> None:
    """Composition principal: tokens with distinct (app, consumer, purpose) never compose."""

    store.commit(make_item("p", "note", label=make_label()))
    meet = make_label()
    proposal = DerivationProposal("d", "note", ("p",), meet, "extractive")
    purposes = ["scheduling", "health", "travel"]
    for i in range(len(purposes) - 1):
        left = issuer.issue(make_context(purpose=purposes[i]), 60.0, store.policy_epoch)
        right = issuer.issue(make_context(purpose=purposes[i + 1]), 60.0, store.policy_epoch)
        result = admit_derivation(store, issuer, [left, right], proposal, "assistant.pkg", 20.0)
        assert result.status == "REJECT"
        assert "composition" in result.reason
