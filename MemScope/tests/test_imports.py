def test_import_package() -> None:
    import memscope

    assert memscope.__version__ == "0.1.0"


def test_import_core_modules() -> None:
    from memscope.methods import compaction, derivation, retrieval, tokens
    from memscope.metrics import core, statistics

    assert all((compaction, derivation, retrieval, tokens, core, statistics))
