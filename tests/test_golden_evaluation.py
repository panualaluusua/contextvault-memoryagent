import json
from pathlib import Path

from contextvault.service import MemoryService


def test_versioned_golden_memory_cases(tmp_path: Path) -> None:
    fixture = json.loads(Path("data/evaluation/golden_cases.json").read_text(encoding="utf-8"))
    assert fixture["version"] == 1
    service = MemoryService(tmp_path / "memory.duckdb")
    service.ingest(Path("data/demo-vault"))
    for case in fixture["cases"]:
        pack = service.get_memory_pack(case["task"], case["budget"])
        assert len(pack) <= case["budget"], case["id"]
        for expected in case["must_contain"]:
            assert expected in pack, f"{case['id']}: missing {expected!r}"
