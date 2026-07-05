from pathlib import Path

from contextvault.demo import run_portfolio_demo


def test_portfolio_demo_covers_three_sessions_and_receipt(tmp_path: Path) -> None:
    output = run_portfolio_demo(
        Path("data/demo-vault"), tmp_path / "demo.duckdb", tmp_path / "trace.jsonl", 1400
    )
    assert "SESSION 1: GOVERNED MEMORY WRITE" in output
    assert "SESSION 2: CROSS-SESSION RECALL" in output
    assert "I prefer auditable Python CLI and API workflows" in output
    assert "SESSION 3: STALE CORRECTION" in output
    assert "[ALLOW] policy checks passed" in output
    assert "[BLOCK] secret-like content; nothing persisted" in output
    assert "[EXCLUDED] Stale grep-only memory rejected" in output
    assert "\033[" not in output


def test_portfolio_demo_can_force_terminal_highlights(tmp_path: Path) -> None:
    output = run_portfolio_demo(
        Path("data/demo-vault"), tmp_path / "color.duckdb", tmp_path / "color.jsonl", 1400,
        color=True,
    )
    assert "\033[1;32m[ALLOW]" in output
    assert "\033[1;31m[BLOCK]" in output
    assert "\033[1;33m[EXCLUDED]" in output
    assert "Excluded stale memory" in output
    assert "-[supersedes]->" in output
    assert "TRACE-DERIVED CONTEXT RECEIPT" in output
    assert "answer: success via mock/" in output
