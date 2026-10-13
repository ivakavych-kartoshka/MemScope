import pytest

from memscope.baselines.simple import UnscopedBaseline
from memscope.data.schemas import QueryEvaluation
from memscope.data.synthetic import (
    SYNTHETIC_NOTICE,
    MutableClock,
    WorkloadConfig,
    generate_scaled_scenario,
    generate_synthetic_scenario,
    oracle_authorized,
)
from memscope.methods.retrieval import MemScopeService
from memscope.methods.store import InMemoryStore
from memscope.methods.tokens import TokenIssuer
from memscope.metrics.core import authorization_violations, entitled_recall_at_k


def test_synthetic_generator_is_deterministic() -> None:
    a = generate_synthetic_scenario(7)
    b = generate_synthetic_scenario(7)
    assert [x.payload for x in a.items] == [x.payload for x in b.items]
    assert [q.query_id for q in a.queries] == [q.query_id for q in b.queries]


def test_synthetic_data_contains_policy_oracle() -> None:
    scenario = generate_synthetic_scenario()
    assert scenario.items and scenario.queries
    assert all(query.entitled_ids for query in scenario.queries)
    assert "not a paper result" in SYNTHETIC_NOTICE


def test_scaled_generator_is_deterministic() -> None:
    config = WorkloadConfig(seed=11, apps=2, topics_per_app=3, decoys_per_topic=2)
    a = generate_scaled_scenario(config)
    b = generate_scaled_scenario(config)
    assert [(i.item_id, i.payload) for i in a.items] == [(i.item_id, i.payload) for i in b.items]
    assert [(q.query_id, sorted(q.entitled_ids), sorted(q.unauthorized_ids)) for q in a.queries] == [
        (q.query_id, sorted(q.entitled_ids), sorted(q.unauthorized_ids)) for q in b.queries
    ]
    assert generate_scaled_scenario(config).now == a.now


def test_scaled_workload_dimensions() -> None:
    config = WorkloadConfig(seed=3, apps=4, topics_per_app=5, decoys_per_topic=3)
    scenario = generate_scaled_scenario(config)
    assert len(scenario.queries) == config.apps * config.topics_per_app
    assert len(scenario.items) == config.apps * config.topics_per_app * config.group_size
    assert all(query.k == config.group_size for query in scenario.queries)


def test_scaled_oracle_is_self_consistent() -> None:
    scenario = generate_scaled_scenario(WorkloadConfig(seed=5, apps=2, topics_per_app=3))
    for query in scenario.queries:
        assert query.entitled_ids
        assert query.unauthorized_ids
        assert query.entitled_ids.isdisjoint(query.unauthorized_ids)
        token = query.text.split()[0]
        relevant = [item for item in scenario.items if token in item.payload.split()]
        assert relevant
        for item in relevant:
            authorized = oracle_authorized(item, query.context, scenario.now)
            assert authorized == (item.item_id in query.entitled_ids)


def test_scaled_config_rejects_bad_dimensions() -> None:
    with pytest.raises(ValueError):
        WorkloadConfig(apps=0)
    with pytest.raises(ValueError):
        WorkloadConfig(decoys_per_topic=0)


def _evaluate_scaled(config: WorkloadConfig) -> tuple[list[QueryEvaluation], list[QueryEvaluation]]:
    scenario = generate_scaled_scenario(config)
    clock = MutableClock(scenario.now)
    store = InMemoryStore()
    for item in scenario.items:
        store.commit(item)
    issuer = TokenIssuer(b"memscope-synthetic-key-material")
    service = MemScopeService(store, issuer, clock=clock)
    baseline = UnscopedBaseline()

    memscope_rows: list[QueryEvaluation] = []
    baseline_rows: list[QueryEvaluation] = []
    for query in scenario.queries:
        token = issuer.issue(
            query.context,
            expires_at=scenario.now + 50.0,
            policy_epoch=store.policy_epoch,
            permitted_tools=frozenset({query.context.tool_id}),
        )
        retrieval = service.retrieve(
            token,
            query.text,
            query.k,
            query.context.app_id,
            (query.context.tool_id,),
        )
        memscope_rows.append(
            QueryEvaluation(
                query.query_id,
                tuple(item.item_id for item in retrieval.items),
                query.entitled_ids,
                query.unauthorized_ids,
            )
        )
        selected = baseline.retrieve(query.text, scenario.items, query.context, query.k)
        baseline_rows.append(
            QueryEvaluation(
                query.query_id,
                tuple(item.item_id for item in selected),
                query.entitled_ids,
                query.unauthorized_ids,
            )
        )
    return memscope_rows, baseline_rows


def test_memscope_enforces_oracle_on_scaled_workload() -> None:
    config = WorkloadConfig(seed=11, apps=2, topics_per_app=3, decoys_per_topic=2)
    memscope_rows, _ = _evaluate_scaled(config)
    assert authorization_violations(memscope_rows) == 0
    assert entitled_recall_at_k(memscope_rows) == 1.0


def test_unscoped_baseline_leaks_scaled_workload() -> None:
    config = WorkloadConfig(seed=11, apps=2, topics_per_app=3, decoys_per_topic=2)
    _, baseline_rows = _evaluate_scaled(config)
    n_queries = config.apps * config.topics_per_app
    assert authorization_violations(baseline_rows) == n_queries * config.decoys_per_topic
