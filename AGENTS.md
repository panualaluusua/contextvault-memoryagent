# Agent instructions

## Project

This repository implements a local, governed memory prototype for AI agents.
The current release surface includes CLI, HTTP, Docker, and a read-only FastMCP
adapter for Codex and Claude Code.

## Sources of truth

Use these in order:

1. explicit user instructions;
2. this file and any more specific nested `AGENTS.md`;
3. `README.md`, `docs/CURRENT_STATUS.md`, `architecture.md`, and `docs/MCP.md`;
4. source code and executable tests;
5. historical planning files only as dated background.

When documentation and tests disagree, verify the implementation and update the
active documentation in the same change.

## Shared memory MCP

If the `agent-memory` MCP server is available, use it before cross-project
architecture, technology, security, or engineering-practice decisions.

- Prefer repository-local instructions, source code, and tests for local facts.
- Cite the memory source when shared memory affects a decision.
- Inspect exclusions or the receipt when stale or conflicting guidance matters.
- Do not call shared memory for routine edits fully specified by this repository.
- Treat MCP as read-only. Do not add a write tool or automatic curation without
  an explicit human-approval design and new evaluation rubric.
- Explicit user instructions always override recalled preferences or practices.

## Development workflow

Before implementation, add or identify measurable pass conditions in
`EVALUATION.md`. Work in one RALP iteration at a time: implement, run focused
tests, evaluate against the rubric, repair gaps, then run the full suite.

Primary commands:

```powershell
python -m pytest -q
contextvault demo --color always
python -m contextvault.mcp_server --help
```

MCP-focused verification:

```powershell
python -m pytest tests\test_mcp_server.py -q
```

## Engineering boundaries

- Preserve typed/temporal memory, deterministic truth resolution, source
  citations, structural budgets, governance outcomes, and metadata-only traces.
- Keep FastMCP stdout protocol-clean; diagnostics belong on stderr.
- Keep MCP database access read-only and process-isolated on Windows.
- Never commit credentials, identity documents, private PKM content, generated
  DuckDB files, traces, or `.env` secrets.
- DuckDB supports this local single-user prototype; do not imply multi-writer or
  horizontally scaled production readiness.
- Qwen, public hosting, and live Ollama remain optional until verified.

## Documentation completion

When behavior changes, reconcile at minimum:

- `README.md`
- `docs/CURRENT_STATUS.md`
- `docs/NEXT_STEPS.md`
- `architecture.md`
- `EVALUATION.md`

Report synthetic evaluation separately from answer quality or business impact.
