import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Annotated, TypedDict, cast

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .trace import load_trace, render_receipt


class ContextResult(TypedDict):
    memory_pack: str
    selected: list[str]
    excluded: list[str]
    characters: int
    budget: int


class MemoryResult(TypedDict):
    found: bool
    slug: str
    memory_type: str
    title: str
    body: str
    source: str
    recorded_at: str
    valid_from: str
    valid_until: str
    tier: str


class RelationsResult(TypedDict):
    slug: str
    relations: list[dict[str, str]]


class ReceiptResult(TypedDict):
    receipt: str
    event_count: int


def _trace_records(trace: Path) -> list[dict]:
    return load_trace(trace) if trace.exists() else []


def create_mcp_server(database: Path, trace: Path) -> FastMCP:
    mcp = FastMCP(
        "Shared Agent Memory",
        instructions=(
            "Read-only access to governed shared decisions and practices. "
            "Use get_context before cross-project architecture or technology decisions. "
            "Project-local instructions and source code remain authoritative for local details."
        ),
        log_level="ERROR",
    )

    def run_backend(operation: str, payload: dict) -> dict:
        completed = subprocess.run(
            [
                sys.executable, "-m", "contextvault.mcp_backend", operation,
                "--database", str(database), "--trace", str(trace),
            ],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("memory backend failed; inspect the local MCP server logs")
        return json.loads(completed.stdout)

    @mcp.tool()
    def get_context(
        task: Annotated[str, Field(min_length=3, max_length=2000)],
        budget: Annotated[int, Field(ge=300, le=8000)] = 1400,
    ) -> ContextResult:
        """Return a bounded, cited memory pack for a task without changing memory."""
        return cast(ContextResult, run_backend("get_context", {"task": task, "budget": budget}))

    @mcp.tool()
    def get_memory(
        slug: Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[a-zA-Z0-9._-]+$")],
    ) -> MemoryResult:
        """Return one memory by stable slug, including its source and validity metadata."""
        return cast(MemoryResult, run_backend("get_memory", {"slug": slug}))

    @mcp.tool()
    def get_relations(
        slug: Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[a-zA-Z0-9._-]+$")],
    ) -> RelationsResult:
        """Return typed incoming and outgoing relations for one memory."""
        return cast(RelationsResult, run_backend("get_relations", {"slug": slug}))

    @mcp.tool()
    def get_receipt(
        max_events: Annotated[int, Field(ge=1, le=100)] = 20,
    ) -> ReceiptResult:
        """Return a bounded human-readable receipt of recent memory selections and exclusions."""
        records = _trace_records(trace)[-max_events:]
        return {"receipt": render_receipt(records), "event_count": len(records)}

    return mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="contextvault-mcp")
    parser.add_argument(
        "--database", type=Path,
        default=Path(os.getenv("CONTEXTVAULT_MCP_DATABASE", ".contextvault/memory.duckdb")),
    )
    parser.add_argument(
        "--trace", type=Path,
        default=Path(os.getenv("CONTEXTVAULT_MCP_TRACE", ".contextvault/mcp-trace.jsonl")),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.trace.parent.mkdir(parents=True, exist_ok=True)
    create_mcp_server(args.database, args.trace).run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
