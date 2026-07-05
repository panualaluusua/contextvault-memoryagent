from pathlib import Path

from contextvault.service import MemoryService
import pytest


def test_pack_has_citations_and_respects_budget(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.db")
    service.ingest(Path("data/demo-vault"))
    pack = service.get_memory_pack("project preferences architecture memory service", budget=700)
    assert "source:" in pack
    assert "[preference]" in pack
    assert len(pack) <= 700


def test_preference_priority_handles_query_punctuation(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.db")
    service.remember_preference("punctuation", "I prefer auditable Python CLI systems")
    pack = service.get_memory_pack("What architecture matches my preferences?", budget=900)
    assert "I prefer auditable Python CLI systems" in pack
    assert "source: session:punctuation" in pack


def test_stale_memory_is_excluded_and_explained(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.db")
    service.ingest(Path("data/demo-vault"))
    pack = service.get_memory_pack("grep search stale architecture", budget=1200)
    assert "Excluded stale memory" in pack
    assert "Grep-only search" not in pack.split("## Warnings")[0]


def test_pack_expands_typed_relations_for_selected_memory(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.db")
    service.ingest(Path("data/demo-vault"))
    pack = service.get_memory_pack("structured architecture memory service", budget=1400)
    assert "## Related Memory Edges" in pack
    assert "adr-001-memory-service -[supersedes]-> grep-only-search-is-stale" in pack


@pytest.mark.parametrize("budget", [300, 350, 500, 700, 900, 1400])
def test_pack_budget_keeps_complete_markdown_blocks(tmp_path: Path, budget: int) -> None:
    service = MemoryService(tmp_path / f"budget-{budget}.duckdb")
    service.ingest(Path("data/demo-vault"))
    task = "architecture preferences " + "very long context " * 100
    pack = service.get_memory_pack(task, budget)
    assert len(pack) <= budget
    assert not pack.endswith(("(", "[", "-", "source:", "##"))
    assert pack.count("[") == pack.count("]")
    assert pack.count("(") == pack.count(")")


def test_pack_rejects_unusable_budget(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "tiny.duckdb")
    with pytest.raises(ValueError, match="at least 300"):
        service.get_memory_pack("task", 299)
