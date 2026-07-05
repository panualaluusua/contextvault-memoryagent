from contextvault.trace import render_receipt


def test_receipt_is_rendered_only_from_trace_records() -> None:
    receipt = render_receipt([
        {"event": "memory_write", "outcome": "redact", "slug": "preference-1"},
        {"event": "conflict_resolution", "excluded_slug": "old", "kind": "superseded", "winner_slug": "new"},
        {"event": "memory_pack", "selected_slugs": ["new"], "excluded_slugs": ["old"], "characters": 400, "budget": 800},
        {"event": "agent_answer", "outcome": "success", "provider": "mock", "model": "mock-v1", "latency_ms": 2.0},
    ])
    assert "write: redact preference-1" in receipt
    assert "excluded: old (superseded; winner=new)" in receipt
    assert "selected=new; excluded=old" in receipt
    assert "success via mock/mock-v1" in receipt
