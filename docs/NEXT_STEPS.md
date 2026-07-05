# Next steps

Last updated: 2026-07-05.

ContextVault is a provider-neutral public release candidate. The canonical
repository, implementation, tests, architecture diagram, raw proof recordings
and first successful hosted CI run exist. The remaining v0.1.0 work is
clean-clone verification and immutable release publication.

## Public release

1. Clone the public repository into a separate directory and verify install,
   tests, `contextvault demo`, evaluation and Docker Compose.
2. Confirm that GitHub Actions passes for the exact clean-clone-verified commit.
3. Tag the verified commit as `v0.1.0` and create a GitHub release.
4. Cut a 15–25 second stale-memory proof from the existing CLI capture.
5. Publish the proof, infographic and LinkedIn case study, then add their public
   links to the README and portfolio hub.

## Engineering follow-ups

- Validate retrieval on a representative, human-labeled corpus; the current 60
  memories are deterministic synthetic distractors.
- Replace DuckDB or introduce a single-writer service before running multiple
  API processes or replicas.
- Add semantic or hybrid retrieval only after measuring an improvement over the
  current lexical recall and MRR baseline.
- Compare MCP retrieval against direct Markdown reading in two real projects.
- Design memory writes through MCP only if read-only usage demonstrates value;
  require explicit human approval before changing shared memory.

## Deferred decisions

- Select a public hosting target only if a hosted demo adds value beyond the
  local Docker and MCP evidence.
- Add hosting-specific TLS, secret storage, rate limits and backups before any
  public endpoint.
- Live-verify Qwen or Ollama only when credentials, cost and reproducibility are
  acceptable.

Never place API keys, cloud credentials, identity documents, payment data,
private knowledge-base content or customer data in the repository, traces or
demo footage.
