# Decision Log

## Decisions

### 2026-06-25 - Isolate the prototype from private source material

Decision: Develop the prototype in a dedicated repository with synthetic data.

Reason: The private PKM/LLM-wiki must remain unchanged and should not become public submission data.

Impact: The public product uses only synthetic demo data and has no dependency on the private knowledge base.

### 2026-06-25 - Use demo-vault instead of private PKM

Decision: Public submission uses `data/demo-vault/`.

Reason: The demo needs to be judge-testable and safe to publish.

Impact: Real PKM informs architecture but is not shipped.

### 2026-06-26 - Target Qwen Track 1: MemoryAgent

Decision: Submit to Track 1: MemoryAgent.

Reason: The project directly demonstrates persistent memory, cross-session recall, user preferences and stale-memory handling.

Impact: Scope prioritizes memory behavior over video generation, multi-agent society, autopilot workflows or edge hardware.

### 2026-06-26 - Use OKF-style memory files

Decision: Memories are Markdown files with YAML frontmatter and mandatory `type`.

Reason: This gives both human-readable documentation and machine-readable memory records.

Impact: Ingest must include an OKF-style validation gate.

### 2026-06-26 - Add bi-temporal memory fields

Decision: Memories include `valid_from`, `valid_until`, `recorded_at` and `supersedes`.

Reason: Qwen MemoryAgent asks for timely forgetting of outdated information.

Impact: Stale handling becomes a first-class feature.

### 2026-06-26 - Use graph-ready metadata, not a graph DB in MVP

Decision: Use typed `relations.*` fields and DuckDB relation expansion now; defer Neo4j/Kuzu/Graphiti.

Reason: Graph DB adds infrastructure risk. Typed relations give the future GraphRAG path without slowing MVP.

Impact: Implement `expand_relations(memory_slug, depth=1)` in the MVP.

### 2026-07-01 - Use DuckDB as the production local memory index

Decision: Replace the temporary SQLite adapter with DuckDB behind the existing
`MemoryService` interface.

Reason: DuckDB matches the planned analytical memory-index architecture, keeps
the demo embedded and portable, and leaves room for richer ranking and
evaluation queries without adding a separate database service.

Impact: Add DuckDB as a runtime dependency, migrate schema and tests, retain a
single-writer deployment model for the MVP, and document how the database file
is persisted on Alibaba Cloud. SQLite compatibility is not a requirement.

### 2026-07-01 - Continue as a provider-neutral portfolio project

Decision: Complete ContextVault as a provider-neutral open-source portfolio
project. Keep Qwen and Alibaba integrations optional until their access,
privacy, and cost constraints are acceptable.

Reason: The implemented memory, governance, truthiness, evaluation, and receipt
layers have independent engineering value. External account verification must
not block a reproducible local product.

Impact: Prioritize HTTP API, Docker, English documentation, architecture assets,
evaluation evidence, and a short demo. Choose inexpensive hosting later without
changing the core service interface.

### 2026-07-03 - Expose shared memory through read-only FastMCP

Decision: Use the official MCP Python SDK FastMCP API and expose exactly four
read-only tools over local stdio for Codex and Claude Code.

Reason: One interoperable adapter avoids separate agent integrations. Read-only
scope lets the agents consume curated shared knowledge without silently changing
its source of truth.

Impact: `get_context`, `get_memory`, `get_relations`, and `get_receipt` reuse
the existing memory behavior. On Windows, each DuckDB read runs in a short-lived
backend process because persistent/thread-crossing connections hung under the
FastMCP runtime. Write proposals, remote HTTP, and automatic curation remain
deferred pending real usage evidence and a human-approval design.
