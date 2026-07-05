from pathlib import Path

from .agent import MemoryAgent
from .providers import MockProvider
from .service import MemoryService
from .trace import load_trace, render_receipt


RESET = "\033[0m"
STYLES = {
    "blue": "\033[1;36m",
    "green": "\033[1;32m",
    "yellow": "\033[1;33m",
    "red": "\033[1;31m",
}


def _paint(text: str, style: str, color: bool) -> str:
    return f"{STYLES[style]}{text}{RESET}" if color else text


def _highlight_receipt(receipt: str, color: bool) -> str:
    if not color:
        return receipt
    lines = []
    for line in receipt.splitlines():
        lowered = line.lower()
        if "excluded" in lowered:
            lines.append(_paint(line, "yellow", True))
        elif "write: block" in lowered:
            lines.append(_paint(line, "red", True))
        elif "write: allow" in lowered or "selected=" in lowered:
            lines.append(_paint(line, "green", True))
        elif "answer: success" in lowered:
            lines.append(_paint(line, "blue", True))
        else:
            lines.append(line)
    return "\n".join(lines)


def run_portfolio_demo(
    vault: Path, database: Path, trace: Path, budget: int, color: bool = False
) -> str:
    database.parent.mkdir(parents=True, exist_ok=True)
    trace.parent.mkdir(parents=True, exist_ok=True)
    for artifact in (database, trace):
        if artifact.exists():
            artifact.unlink()

    lines = [_paint("=== SESSION 1: GOVERNED MEMORY WRITE ===", "blue", color)]
    first = MemoryService(database, trace)
    first.ingest(vault)
    decision, slug = first.remember_preference(
        "portfolio-session-1", "I prefer auditable Python CLI and API workflows"
    )
    lines.append(_paint(f"[ALLOW] {decision.reason} ({slug})", "green", color))
    blocked, _ = first.remember_preference(
        "portfolio-session-1", "api_key=sk-abcdefghijklmnop"
    )
    lines.append(_paint(f"[BLOCK] {blocked.reason}; nothing persisted", "red", color))
    first.connection.close()

    lines.extend(["", _paint("=== SESSION 2: CROSS-SESSION RECALL ===", "blue", color)])
    second = MemoryService(database, trace)
    recall = MemoryAgent(second, MockProvider()).answer(
        "What workflow matches my project preferences?", budget
    )
    lines.extend([
        _paint("[SELECTED] Preference recalled from an earlier session", "green", color),
        recall.answer,
        "",
        _highlight_receipt(recall.receipt or "", color),
    ])
    second.connection.close()

    lines.extend(["", _paint("=== SESSION 3: STALE CORRECTION ===", "blue", color)])
    third = MemoryService(database, trace)
    correction = MemoryAgent(third, MockProvider()).answer(
        "Is grep-only search the current structured memory architecture?", budget
    )
    lines.extend([
        _paint("[EXCLUDED] Stale grep-only memory rejected", "yellow", color),
        _paint("[SELECTED] Current DuckDB architecture decision", "green", color),
        correction.answer,
        "",
        _highlight_receipt(correction.receipt or "", color),
    ])
    third.connection.close()

    lines.extend([
        "",
        _paint("=== TRACE-DERIVED CONTEXT RECEIPT ===", "blue", color),
        _highlight_receipt(render_receipt(load_trace(trace)), color),
    ])
    return "\n".join(lines)
