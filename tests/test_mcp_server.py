import asyncio
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from contextvault.mcp_server import create_mcp_server
from contextvault.service import MemoryService


EXPECTED_TOOLS = {"get_context", "get_memory", "get_relations", "get_receipt"}


def test_fastmcp_exposes_exactly_four_read_only_tools(tmp_path: Path) -> None:
    server = create_mcp_server(tmp_path / "memory.duckdb", tmp_path / "trace.jsonl")
    tools = server._tool_manager.list_tools()

    assert {tool.name for tool in tools} == EXPECTED_TOOLS
    assert all(term not in tool.name for tool in tools for term in ("write", "remember", "delete", "upsert"))
    context = next(tool for tool in tools if tool.name == "get_context")
    assert context.parameters["properties"]["budget"]["minimum"] == 300
    assert context.parameters["properties"]["budget"]["maximum"] == 8000


def test_memory_service_get_memory_has_controlled_not_found(tmp_path: Path) -> None:
    service = MemoryService(tmp_path / "memory.duckdb")
    service.ingest(Path("data/demo-vault"))

    memory = service.get_memory("adr-001-memory-service")
    assert memory is not None
    assert memory["source"] == "decisions/adr-001-memory-service.md"
    assert service.get_memory("does-not-exist") is None


def test_real_stdio_mcp_client_retrieves_truth_and_receipt(tmp_path: Path) -> None:
    run_id = uuid4().hex
    database = tmp_path / f"memory-{run_id}.duckdb"
    trace = tmp_path / f"trace-{run_id}.jsonl"
    seeded = subprocess.run(
        [
            sys.executable, "-m", "contextvault", "ingest", "data/demo-vault",
            "--database", str(database),
        ],
        cwd=Path.cwd(), capture_output=True, text=True, timeout=30,
    )
    assert seeded.returncode == 0, seeded.stderr

    async def scenario() -> None:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[
                "-m", "contextvault.mcp_server",
                "--database", str(database),
                "--trace", str(trace),
            ],
            cwd=Path.cwd(),
        )
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert {tool.name for tool in listed.tools} == EXPECTED_TOOLS

                context = await session.call_tool(
                    "get_context",
                    {"task": "Is grep-only search the current structured memory architecture?", "budget": 1400},
                )
                assert not context.isError
                payload = context.structuredContent
                assert payload is not None
                assert "adr-001-memory-service" in payload["selected"]
                assert "grep-only-search-is-stale" in payload["excluded"]
                assert payload["characters"] <= payload["budget"]
                assert "source: decisions/adr-001-memory-service.md" in payload["memory_pack"]

                missing = await session.call_tool("get_memory", {"slug": "does-not-exist"})
                assert missing.structuredContent == {
                    "found": False, "slug": "does-not-exist", "memory_type": "", "title": "",
                    "body": "", "source": "", "recorded_at": "", "valid_from": "",
                    "valid_until": "", "tier": "",
                }

                relations = await session.call_tool(
                    "get_relations", {"slug": "adr-001-memory-service"}
                )
                assert any(
                    edge["relation_type"] == "supersedes"
                    for edge in relations.structuredContent["relations"]
                )

                receipt = await session.call_tool("get_receipt", {"max_events": 20})
                assert "selected=adr-001-memory-service" in receipt.structuredContent["receipt"]
                assert "excluded=grep-only-search-is-stale" in receipt.structuredContent["receipt"]

    asyncio.run(scenario())
