from contextvault.synthetic_corpus import CORPUS_VERSION, build_synthetic_corpus


def test_versioned_synthetic_corpus_has_variety_and_conflicts() -> None:
    corpus = build_synthetic_corpus()
    assert CORPUS_VERSION == 1
    assert len(corpus) == 60
    assert len({memory.slug for memory in corpus}) == 60
    assert len({memory.memory_type for memory in corpus}) == 5
    assert len({memory.tier for memory in corpus}) == 3
    assert sum(memory.stale for memory in corpus) >= 5
    assert sum("contradicts" in memory.relations for memory in corpus) >= 4
