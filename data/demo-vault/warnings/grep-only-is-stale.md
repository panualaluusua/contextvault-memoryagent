---
slug: grep-only-search-is-stale
type: warning
title: Grep-only search is a stale architecture description
reliability: 3
valid_from: 2026-06-20
valid_until: 2026-06-24
recorded_at: 2026-06-20T12:00:00Z
tier: cold
relations:
  supersedes: []
  related_to: [adr-001-memory-service]
---

Older notes may describe the memory layer as grep-only text search. That is now stale as a final architecture statement.

The current plan starts with deterministic search for MVP speed but presents the architecture as a structured memory service that can add DuckDB indexing, embeddings and graph expansion.
