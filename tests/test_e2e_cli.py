import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "contextvault", *arguments],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_separate_processes_ingest_remember_and_recall(tmp_path: Path) -> None:
    database = tmp_path / "e2e-memory.db"
    trace = tmp_path / "e2e-trace.jsonl"

    ingest = run_cli("--trace", str(trace), "ingest", "data/demo-vault", "--database", str(database))
    assert ingest.returncode == 0, ingest.stderr
    assert "Indexed 5 memories" in ingest.stdout

    remember = run_cli(
        "--trace", str(trace), "remember", "I prefer concise auditable CLI output",
        "--session", "e2e-session-1", "--database", str(database),
    )
    assert remember.returncode == 0, remember.stderr
    assert remember.stdout.startswith("ALLOW:")

    recall = run_cli(
        "--trace", str(trace), "recall", "What output preferences should this project follow?",
        "--database", str(database), "--budget", "900",
    )
    assert recall.returncode == 0, recall.stderr
    assert "I prefer concise auditable CLI output" in recall.stdout
    assert "source: session:e2e-session-1" in recall.stdout
    assert len(recall.stdout.strip()) <= 900

    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == ["memory_write", "memory_pack"]


def test_separate_processes_remember_and_ask_with_receipt(tmp_path: Path) -> None:
    database = tmp_path / "agent-e2e.db"
    trace = tmp_path / "agent-e2e.jsonl"
    preference = "I prefer source-grounded terminal workflows"

    remember = run_cli(
        "--trace", str(trace), "remember", preference,
        "--session", "agent-e2e-session", "--database", str(database),
    )
    assert remember.returncode == 0, remember.stderr

    ask = run_cli(
        "--trace", str(trace), "ask", "What workflow should I use? preferences",
        "--provider", "mock", "--database", str(database), "--budget", "900",
    )
    assert ask.returncode == 0, ask.stderr
    assert "ANSWER [mock/deterministic-memory-mock-v1]" in ask.stdout
    assert "Memory-grounded recommendation" in ask.stdout
    assert "CONTEXT RECEIPT" in ask.stdout
    assert preference in ask.stdout
    assert "source: session:agent-e2e-session" in ask.stdout

    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == ["memory_write", "memory_pack", "agent_answer"]
    assert records[-1]["outcome"] == "success"
    assert records[-1]["provider"] == "mock"


def test_governed_truthiness_flow_renders_trace_receipt(tmp_path: Path) -> None:
    database = tmp_path / "m2-e2e.duckdb"
    trace = tmp_path / "m2-e2e.jsonl"
    assert run_cli("ingest", "data/demo-vault", "--database", str(database)).returncode == 0
    write = run_cli(
        "--trace", str(trace), "remember", "Email owner@example.com about architecture preferences",
        "--session", "m2-session", "--database", str(database),
    )
    assert write.returncode == 0
    assert write.stdout.startswith("REDACT:")

    answer = run_cli(
        "--trace", str(trace), "ask", "Is grep-only search the current structured memory architecture?",
        "--provider", "mock", "--database", str(database), "--budget", "1400",
    )
    assert answer.returncode == 0, answer.stderr
    assert "Excluded stale memory" in answer.stdout
    assert "-[supersedes]->" in answer.stdout

    receipt = run_cli("receipt", str(trace))
    assert receipt.returncode == 0, receipt.stderr
    assert "write: redact" in receipt.stdout
    assert "excluded: grep-only-search-is-stale (stale" in receipt.stdout
    assert "answer: success via mock/" in receipt.stdout
    assert "owner@example.com" not in trace.read_text(encoding="utf-8")
