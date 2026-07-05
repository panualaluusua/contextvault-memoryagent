from pathlib import Path

import pytest

from contextvault.ingest import MemoryValidationError, parse_memory


def test_invalid_memory_reports_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text("---\ntype: preference\n---\nbody\n", encoding="utf-8")
    with pytest.raises(MemoryValidationError, match="missing fields"):
        parse_memory(path)


def test_demo_memory_has_typed_relations() -> None:
    memory = parse_memory(Path("data/demo-vault/preferences/user-preferences.md"), Path("data/demo-vault"))
    assert memory.memory_type == "preference"
    assert memory.relations["constrains"] == ["hackathon-selection"]
