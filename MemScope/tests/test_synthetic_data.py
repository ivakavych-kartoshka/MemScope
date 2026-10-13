from memscope.data.synthetic import SYNTHETIC_NOTICE, generate_synthetic_scenario


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
