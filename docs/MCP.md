# ContextVault MCP for Codex and Claude Code

ContextVault exposes one local, read-only FastMCP server for both coding agents.
It uses the official MCP Python SDK and the `stdio` transport. The server never
adds, edits, or deletes memories.

## Tools

| Tool | Purpose |
|---|---|
| `get_context(task, budget)` | Return a bounded, cited memory pack for a task. |
| `get_memory(slug)` | Read one memory and its validity/source metadata. |
| `get_relations(slug)` | Read typed incoming and outgoing relations. |
| `get_receipt(max_events)` | Show recent selections and exclusions. |

## Prepare a local database

Install the package and create a user-level data directory:

```powershell
python -m pip install -e .
$memoryHome = Join-Path $HOME ".agent-memory"
New-Item -ItemType Directory -Force $memoryHome | Out-Null
$database = Join-Path $memoryHome "memory.duckdb"
$trace = Join-Path $memoryHome "trace.jsonl"
contextvault ingest data\demo-vault --database $database
$mcpCommand = (Get-Command contextvault-mcp).Source
```

The demo vault is synthetic. Replace it later with a curated, typed shared vault;
do not point the indexer at arbitrary Markdown and assume it becomes trustworthy.

## Add to Codex

```powershell
codex mcp add agent-memory -- $mcpCommand --database $database --trace $trace
codex mcp list
codex mcp get agent-memory
```

Remove it with:

```powershell
codex mcp remove agent-memory
```

## Add to Claude Code

Use user scope so the same memory is available across projects:

```powershell
claude mcp add --scope user --transport stdio `
  agent-memory -- $mcpCommand --database $database --trace $trace
claude mcp list
claude mcp get agent-memory
```

Inside Claude Code, `/mcp` shows the connection and discovered tools. Remove it
with:

```powershell
claude mcp remove --scope user agent-memory
```

## Durable agent guidance

Put the following policy in the relevant global or repository agent guidance:

```text
Use the agent-memory MCP tools before cross-project architecture, technology,
security, or engineering-practice decisions. Prefer project-local AGENTS.md,
CLAUDE.md, source code, and tests for local facts. Cite memory sources used.
Do not call shared memory for routine edits that are fully specified locally.
```

For Codex, durable repository guidance belongs in `AGENTS.md`. For Claude Code,
use the corresponding `CLAUDE.md` guidance. MCP supplies live data; these files
define when the agent should request it.

## Smoke test prompts

Run the same prompt in both agents:

```text
Use agent-memory to check the current structured-memory architecture. Show the
selected source and any stale or superseded memory that was excluded.
```

Expected evidence:

- `adr-001-memory-service` is selected;
- `grep-only-search-is-stale` is excluded;
- the source path appears;
- `get_receipt` shows selected and excluded slugs.

## Boundaries

- The MCP server is read-only, but its receipt trace is writable.
- DuckDB access is isolated in short-lived read-only backend processes on
  Windows so the long-running stdio server does not retain database locks.
- The current server is local and single-user; it has no remote authentication.
- Shared memory does not override explicit prompts or project-local evidence.
- Write proposals, automatic curation, remote HTTP and MCP SDK v2 are deferred.
