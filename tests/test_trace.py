import json
from pathlib import Path

from contextvault.service import MemoryService


def test_trace_is_jsonl_metadata_without_memory_body(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    service = MemoryService(tmp_path / "memory.db", trace)
    secret_phrase = "I prefer a very specific private phrase"
    service.remember_preference("trace-session", secret_phrase)
    task = "specific preferences containing private task details"
    service.get_memory_pack(task, 700)
    records = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    assert [record["event"] for record in records] == ["memory_write", "memory_pack"]
    assert secret_phrase not in trace.read_text(encoding="utf-8")
    assert task not in trace.read_text(encoding="utf-8")
    assert "task_sha256" in records[1]
    assert "task" not in records[1]
    assert records[1]["characters"] <= records[1]["budget"]
