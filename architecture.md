# Architecture

Last updated: 2026-07-03.

The editable visual is
[`docs/architecture/contextvault-architecture.svg`](docs/architecture/contextvault-architecture.svg).

## Invariant

A memory-enabled agent request retrieves and resolves a budgeted memory pack
before invoking the selected model provider.

## Implemented flow

```text
Markdown vault + governed session writes
                  |
          schema validation / ingest
                  |
       DuckDB-backed MemoryService
          /          |          \
   lexical rank   truthiness   typed relations
          \          |          /
        budgeted memory pack + citations
                  |
            MemoryAgent
        /                         \
deterministic mock       optional Qwen-compatible provider
                  |
      CLI, single-process HTTP, read-only MCP
                  |
      metadata-only trace -> context receipt
```

## Components

| Component | Implementation and responsibility |
|---|---|
| Markdown ingest | `ingest.py` parses and validates typed, temporal YAML frontmatter and Markdown bodies. |
| Governance | `governance.py` returns allow, redact, quarantine or block before session writes. |
| Memory service | `service.py` persists memories and relations in embedded DuckDB. |
| Truthiness | `truthiness.py` excludes stale/superseded memories and resolves contradictions deterministically. |
| Retrieval | Lexical scoring, memory-type priority, two-memory selection, character budget and one-hop edges. |
| Agent | `agent.py` always obtains the memory pack before a memory-enabled provider call. |
| Providers | Deterministic mock is verified; Qwen-compatible chat completions is optional and not live-verified. |
| Trace and receipt | JSONL stores task hashes and metadata; receipt text is rendered only from trace records. |
| Delivery | `cli.py`, `api.py`, Dockerfile and Compose expose the same service and agent paths. |
| MCP adapter | `mcp_server.py` exposes four read-only FastMCP tools; short-lived `mcp_backend.py` processes isolate DuckDB reads on Windows. |

## Persistence and concurrency

The portfolio MVP uses one server process and one DuckDB writer. Docker mounts
`/data` for the database and trace. A future host must provide a persistent
writable volume. Horizontal write scaling requires a different storage design
and is explicitly out of scope.

## HTTP boundary

The implemented API exposes health, governed preference writes, memory packs
and agent answers. It reuses `MemoryService` and `MemoryAgent`; there is no
second retrieval implementation. See [`docs/API.md`](docs/API.md).

## MCP boundary

The local stdio server exposes `get_context`, `get_memory`, `get_relations`, and
`get_receipt` to Codex and Claude Code. FastMCP handles protocol framing and
typed schemas. Each database operation runs in a short-lived process with a
DuckDB read-only connection; task text is transferred through JSON stdin rather
than command-line arguments. The long-running MCP process writes only the
metadata receipt trace. See [`docs/MCP.md`](docs/MCP.md).

## Security boundary

The application supports an optional shared bearer token and a 16 KiB request
limit. Any public deployment must add TLS, secret management, rate limiting,
backups and network controls at the host or reverse proxy.

## Optional extensions

- live Qwen or another provider through the provider interface;
- human-approved proposal workflow for shared-memory writes;
- embedding or hybrid retrieval;
- graph export to a dedicated graph database;
- multi-user identity and a multi-writer database.
