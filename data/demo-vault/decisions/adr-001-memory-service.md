---
slug: adr-001-memory-service
type: architecture_decision
title: Use a structured memory service instead of prompt-only memory
reliability: 5
valid_from: 2026-06-25
valid_until:
recorded_at: 2026-06-25T12:00:00Z
tier: hot
relations:
  supports: [contextvault-memoryagent]
  supersedes: [grep-only-search-is-stale]
---

ContextVault should expose memory through a structured service instead of hiding all context inside a prompt.

The first implementation should use deterministic search and typed memory records. DuckDB, embeddings and graph expansion can be added incrementally after the cross-session memory behavior works.
