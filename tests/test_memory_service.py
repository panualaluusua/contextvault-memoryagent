from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from contextvault.service import MemoryService


def test_ingest_persists_and_recalls_preference(tmp_path: Path) -> None:
    database = tmp_path / "memory.db"
    first = MemoryService(database)
    assert first.ingest(Path("data/demo-vault")) == 5
    first.connection.close()
    second = MemoryService(database)
    results = second.search("agentic infrastructure preferences")
    assert results[0]["memory_type"] == "preference"
    assert results[0]["source"] == "preferences/user-preferences.md"


def test_written_preference_survives_new_service(tmp_path: Path) -> None:
    database = tmp_path / "memory.db"
    first = MemoryService(database)
    decision, slug = first.remember_preference("session-1", "I prefer compact CLI tools")
    assert decision.outcome == "allow"
    assert slug
    first.connection.close()
    second = MemoryService(database)
    pack = second.get_memory_pack("What are my preferences for CLI tools?", 700)
    assert "I prefer compact CLI tools" in pack
    assert "source: session:session-1" in pack


def test_relation_expansion_returns_incoming_and_outgoing_edges(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.db")
    service.ingest(Path("data/demo-vault"))
    edges = service.expand_relations("contextvault-memoryagent")
    assert any(edge["direction"] == "incoming" and edge["relation_type"] == "supports" for edge in edges)
    edges = service.expand_relations("adr-001-memory-service")
    assert any(edge["direction"] == "outgoing" and edge["relation_type"] == "supersedes" for edge in edges)


def test_redacted_preference_is_persisted_without_original_email(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.duckdb")
    decision, slug = service.remember_preference("redact", "Email me at private@example.com about tests")
    assert decision.outcome == "redact" and slug
    pack = service.get_memory_pack("email tests preference", 800)
    assert "[REDACTED_EMAIL]" in pack
    assert "private@example.com" not in pack


def test_search_ranking_and_limit_execute_in_duckdb_sql(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "sql-ranking.duckdb")
    service.ingest(Path("data/demo-vault"))
    queries: list[str] = []
    original = service._fetch_dicts

    def recording_fetch(query: str, parameters=None):
        queries.append(query)
        return original(query, parameters)

    service._fetch_dicts = recording_fetch  # type: ignore[method-assign]
    results = service.search("structured architecture memory", limit=2)
    assert len(results) <= 2
    ranking_query = queries[-1]
    assert "WITH corpus" in ranking_query
    assert "ORDER BY score DESC" in ranking_query
    assert "LIMIT ?" in ranking_query
    assert "SELECT * FROM memories" not in ranking_query


def test_process_local_concurrent_writes_are_serialized(tmp_path: Path) -> None:
    database = tmp_path / "concurrent.duckdb"
    services = [MemoryService(database) for _ in range(8)]

    def write(index: int) -> str | None:
        _, slug = services[index].remember_preference(
            f"concurrent-{index}", f"I prefer workflow number {index}"
        )
        return slug

    with ThreadPoolExecutor(max_workers=8) as executor:
        slugs = list(executor.map(write, range(8)))
    assert all(slugs)
    verifier = MemoryService(database)
    assert verifier.memory_count() == 8
    for service in services:
        service.connection.close()
