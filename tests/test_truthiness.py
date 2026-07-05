from contextvault.truthiness import resolve_truthiness


def memory(slug: str, reliability: int, recorded_at: str, stale: bool = False) -> dict:
    return {
        "slug": slug, "reliability": reliability,
        "recorded_at": recorded_at, "stale": stale, "valid_until": None,
    }


def test_supersedes_removes_active_older_target_with_reason() -> None:
    old = memory("old", 5, "2026-06-01T00:00:00+00:00")
    new = memory("new", 4, "2026-07-01T00:00:00+00:00")
    selected, excluded = resolve_truthiness(
        [old, new], [{"source_slug": "new", "relation_type": "supersedes", "target_slug": "old"}]
    )
    assert [item["slug"] for item in selected] == ["new"]
    assert excluded[0].kind == "superseded"
    assert excluded[0].winner_slug == "new"


def test_contradiction_uses_reliability_then_recency_then_slug() -> None:
    low = memory("low", 3, "2026-07-01T00:00:00+00:00")
    high_old = memory("high-old", 5, "2026-06-01T00:00:00+00:00")
    selected, excluded = resolve_truthiness(
        [low, high_old], [{"source_slug": "low", "relation_type": "contradicts", "target_slug": "high-old"}]
    )
    assert [item["slug"] for item in selected] == ["high-old"]
    assert excluded[0].winner_slug == "high-old"

    alpha = memory("alpha", 5, "2026-07-01T00:00:00+00:00")
    beta = memory("beta", 5, "2026-07-01T00:00:00+00:00")
    selected, _ = resolve_truthiness(
        [beta, alpha], [{"source_slug": "beta", "relation_type": "contradicts", "target_slug": "alpha"}]
    )
    assert [item["slug"] for item in selected] == ["alpha"]
