# Current implementation status

Last updated: 2026-07-05.

## Release state

ContextVault is published as the canonical public repository at
<https://github.com/panualaluusua/contextvault-memoryagent>. It installs as a
Python package, runs through CLI, HTTP, or read-only MCP, builds as a non-root
Docker image, and needs no cloud credentials for its demo, tests, or
deterministic evaluation.

Release `v0.1.0` was published on 2026-07-05 from commit `4c0518f` after hosted
CI and clean-clone verification:
<https://github.com/panualaluusua/contextvault-memoryagent/releases/tag/v0.1.0>.

## Working now

- Typed and temporal Markdown/YAML validation and ingestion.
- Embedded DuckDB 1.5.x persistence behind `MemoryService`.
- Cross-process recall and DuckDB SQL lexical ranking with type prioritization.
- Governed writes: allow, redact, quarantine and block.
- Stale, supersedes and contradiction truthiness resolution.
- Character-budgeted memory packs with citations and one-hop typed relations.
- Metadata-only JSONL traces and trace-derived context receipts.
- Provider-neutral `MemoryAgent` with verified mock, Ollama contract, and optional Qwen adapter.
- Read-only official FastMCP adapter for Codex and Claude Code with four tools.
- CLI commands for ingest, remember, recall, relations, ask, receipt, serve, demo and evaluate.
- HTTP API with optional bearer token, JSON validation and request-size limits.
- Non-root Docker image, health check, Compose and persistent `/data` volume.
- English README, editable SVG architecture diagram and API documentation.
- Versioned golden cases and generated with/without-memory baseline report.
- GitHub Actions definition for tests, Ruff, MyPy, package build, dependency audit and Docker smoke.
- First hosted GitHub Actions quality and container run passed on `main`.
- Release-candidate hosted CI passed for commit `8435716`.
- A new clone from the public GitHub URL passed installation, Ruff, MyPy,
  47 tests, deterministic demo, 3/3 evaluation and publication-safety checks.
- The clean-clone Docker image ran as UID 10001 and returned `status: ok` from
  its health endpoint.
- Local proof captures for the CLI stale-memory flow and live Codex MCP usage.

## Latest verified evidence

```text
Full regression: 47 passed (2026-07-05)
Golden cases: 3/3 passed
Synthetic distractor corpus: 60 memories
Mean recall@3: 1.000
MRR: 0.833
Citation-contract coverage: 100% with memory, 0% without memory
Mean retrieval latency: 12.038 ms (local run; not a benchmark)
Editable package installation: passed
One-command highlighted three-session demo: passed
Docker build: passed
Real container health/write/ask E2E: passed
Runtime user: non-root contextvault (UID 10001)
FastMCP focused protocol E2E: 3 passed
Ruff: passed
MyPy checked baseline: passed, 17 source files
Isolated dependency audit: no known vulnerabilities
Package build: wheel and source distribution passed
```

Earlier milestone evidence remains in `EVALUATION.md`.

## Publication assets

- Editable architecture diagram: `docs/architecture/contextvault-architecture.svg`.
- CLI stale-memory proof captured locally: 35.1 seconds.
- Codex `agent-memory` MCP proof captured locally: 43.0 seconds.
- Raw recordings are intentionally excluded from Git history.
- The short public proof edit and its final publication URL are pending.

## Not completed

- Public edited demo video and LinkedIn case study.
- Public hosting target and deployment; hosting is optional for the portfolio release.
- Live Qwen call and live Ollama smoke; both are optional.
- Multi-user authentication, TLS, public rate limiting and automated backups.
- Cross-process or multi-replica write serialization and horizontal scaling.
- Embedding/hybrid retrieval, graph database export and rollback UI.
- Claude Code MCP activation and a fresh-session live smoke test.
