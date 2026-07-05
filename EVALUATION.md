# ContextVault RALP Evaluation Rubric

This is the implementation-time definition of done. Run `python -m pytest` and
`python -m contextvault demo` after every meaningful iteration. A claim only
passes when the linked automated check or reproducible evidence exists.

## RALP loop

1. **Rubric**: select the lowest failing gate that unlocks an end-to-end path.
2. **Act**: make the smallest coherent implementation change.
3. **Loop**: run tests and the demo, then record observed evidence.
4. **Prove**: mark a gate passed only from executable or externally verifiable evidence.

## Local MVP gates

| Gate | Pass condition | Evidence |
|---|---|---|
| L1 Install | Package imports and CLI help runs | `python -m contextvault --help` |
| L2 Validate | Invalid records fail with actionable errors | `tests/test_ingest.py` |
| L3 Persist | Ingested memory survives a new service instance | `tests/test_memory_service.py` |
| L4 Recall | A preference is retrieved with a source citation | `tests/test_memory_service.py` |
| L5 Truthiness | Superseded/stale memory is excluded and explained | `tests/test_memory_pack.py` |
| L6 Budget | Rendered memory pack never exceeds its character budget | `tests/test_memory_pack.py` |

All L1-L6 must pass before Qwen or deployment work starts.

## Submission gates

| Gate | Pass condition | Required evidence |
|---|---|---|
| S1 Track | README explicitly identifies Track 1: MemoryAgent | README |
| S2 Qwen | Real Qwen Cloud model participates in the working decision path | integration test + trace |
| S3 Cross-session | A separately started session recalls persisted memory | test + demo |
| S4 Memory tools | Retrieval uses an explicit service/tool boundary | source + test |
| S5 Staleness | Current memory wins over stale/conflicting memory | test + demo |
| S6 Limited context | Selection respects a configured context budget | test + trace |
| S7 Judge runnable | Clean checkout instructions reproduce demo and tests | clean-checkout log |
| S8 Public ready | License, source, assets and English instructions exist | repository audit |
| S9 Alibaba | Working backend and code-level Alibaba Cloud proof exist | endpoint + proof doc |
| S10 Architecture | Diagram matches the shipped implementation | reviewed asset |
| S11 Video | Public video is under 3 minutes and shows real behavior | URL + duration |
| S12 Evaluation | With-memory baseline wins deterministic scenarios | evaluation report |
| S13 Safety | Secrets and unsafe memory writes are blocked or quarantined | tests + scan |

Stage One is PASS only when S1-S13 pass. The original hackathon rubric remains
historical planning context and is not part of the public release surface.

## Current iteration

- Iteration 1 result: L2, L3, L5 and L6 pass; L1 needs clean install proof;
  L4 search passes but the first demo pack omitted the preference under budget.
- Iteration 2 target: prove install and ensure preference recall survives packing.
- Iteration 2 observation: packaging is blocked by the environment's missing
  `wheel`; preference type-priority was too weak against repeated text terms.
- Iteration 3 result: L2-L6 pass (`5 passed`); the scripted demo visibly recalls
  the preference and excludes the expired grep-only record. L1 remains AT RISK:
  source execution works, but editable-install evidence is still missing.
- Next target after local gates: S2 real Qwen path, then S9 Alibaba deployment.

## Iteration 4 rubric: cross-session memory tool path

This rubric is frozen before implementation. All gates must pass before the
iteration is complete, followed by the separate black-box E2E test.

| Gate | Pass condition | Evidence |
|---|---|---|
| R4.1 Governed write | CLI writes a safe preference and rejects secret-like input | governance tests |
| R4.2 Persistence | A new service/process retrieves the written preference | integration test |
| R4.3 Relations | One-hop expansion returns typed incoming and outgoing edges | service test |
| R4.4 Receipt | Recall output lists selected sources and stale exclusions | pack test |
| R4.5 Trace | Writes and retrievals append parseable JSONL events without memory bodies | trace test |
| R4.6 Compatibility | Existing validation, budget and stale tests still pass | full test suite |
| R4.E2E | Separate CLI processes ingest, remember and recall the same database | `tests/test_e2e_cli.py` |

The E2E test is intentionally excluded from the first rubric run. It is run
only after R4.1-R4.6 pass, as an independent final verification.

### Iteration 4 result

- R4.1-R4.6: **PASS**, 11 tests passed before E2E execution.
- R4.E2E: **PASS**, 1 black-box subprocess test passed.
- Full regression after E2E: **PASS**, 12 tests passed.
- Submission gates advanced: S3, S4, S5 and S6 have local executable evidence;
  S2 (real Qwen) and S9 (Alibaba deployment) remain failing.

## Iteration 5 rubric: provider-neutral agent loop

This rubric is frozen before implementation. R5.1-R5.7 are evaluated first;
the black-box R5.E2E test runs only after they all pass.

| Gate | Pass condition | Evidence |
|---|---|---|
| R5.1 Tool order | Agent retrieves a memory pack before every memory-enabled provider call | agent unit test |
| R5.2 Provider boundary | Mock and Qwen-compatible providers implement the same interface | provider tests |
| R5.3 Decision value | Deterministic mock produces a source-grounded answer that differs from the no-memory baseline | agent test |
| R5.4 Configuration | Missing Qwen key, base URL, or model fails before network access with actionable names | provider test |
| R5.5 Failure safety | Provider errors return a controlled CLI failure and do not mutate memories | integration test |
| R5.6 Observability | Answer trace records provider/model/outcome/latency and no prompt or memory body | trace test |
| R5.7 Compatibility | Iteration-4 governance, recall, relations, budget, and stale behavior still pass | full non-E2E suite |
| R5.E2E | Separate CLI processes remember and ask through the mock provider, showing answer plus receipt | subprocess E2E test |

Passing R5 does not pass submission gate S2. S2 requires a successful live Qwen
Cloud call with externally verifiable trace evidence.

### Iteration 5 result

- R5.1-R5.7: **PASS**, 16 tests passed before E2E execution.
- R5.E2E: **PASS**, 2 subprocess E2E tests passed (legacy memory path and agent path).
- Full regression after E2E: **PASS**, 18 tests passed.
- The live Qwen submission gate S2 remains **FAIL** pending credentials,
  endpoint/model confirmation, and a successful external call.

## Architecture audit: 2026-07-01

The implementation was re-tested against `architecture.md`, including a clean
manual CLI path in addition to the automated suite.

- Full automated regression: **PASS**, 20 tests.
- Cross-process governed preference write and recall: **PASS**.
- Source-grounded mock answer and context receipt: **PASS**.
- Stale architecture exclusion: **PASS**.
- Selected-memory one-hop relation expansion, including `supersedes`: **PASS**.
- Context-budget enforcement: **PASS**.
- Trace privacy (no raw task or memory body): **PASS**.
- Missing-Qwen-configuration fail-safe: **PASS**, controlled exit code 3.

Audit fixes: query tokenization now handles punctuation, trace stores a task
hash instead of task text, and memory packs include budgeted relation expansion
with truth-changing edges prioritized over generic relations.

Target-architecture gaps remain explicit: live Qwen verification, HTTP/MCP,
and Alibaba Cloud deployment.

## DuckDB migration evidence: 2026-07-01

- DuckDB dependency: **PASS**, v1.5.4 installed and constrained to `<2`.
- Unchanged `MemoryService` contract: **PASS**.
- Full regression: **PASS**, 20 tests.
- Cross-process ingest/write/ask persistence: **PASS**.
- Direct engine verification: **PASS**, DuckDB reported v1.5.4 and six persisted memories.

The SQLite adapter has been removed. Remaining storage work is schema-version
metadata and persistent single-writer volume configuration on Alibaba Cloud.

## Iteration 6 rubric: original-plan milestone M2

This rubric was frozen before implementation from the original Phase 2
acceptance criteria. M2 passes only when every gate has executable evidence.

| Gate | Pass condition | Evidence |
|---|---|---|
| M2.1 Truthiness | Active `supersedes` edges remove older targets; contradictions resolve by reliability, then recency, then slug | resolver tests |
| M2.2 Explanation | Every stale, superseded, or contradicted exclusion has a deterministic reason in the memory pack | pack tests |
| M2.3 Governance | Every write returns `allow`, `redact`, `quarantine`, or `block`; redacted content can be safely persisted | governance tests |
| M2.4 Trace | Write, pack, conflict, and answer events remain parseable JSONL without raw task or unredacted content | trace tests |
| M2.5 Receipt | A human-readable receipt is rendered from JSONL events, not reconstructed from hidden state | receipt tests |
| M2.6 Golden fixtures | Versioned demo cases assert recall, stale correction, citations, and budget | golden evaluation test |
| M2.7 Compatibility | All M0/M1, DuckDB, provider, and architecture tests still pass | non-E2E suite |
| M2.E2E | Separate processes write, resolve, answer, and render a receipt from the generated trace | subprocess E2E |

Rollback and replay UI remain cuttable polish under the original July 3 scope
checkpoint. They are not required for M2 passage.

### Iteration 6 / M2 result

- M2.1-M2.7: **PASS**, 24 tests passed before E2E.
- M2.E2E: **PASS**, 3 subprocess scenarios passed.
- Full regression: **PASS**, 27 tests.
- Original Phase 2 exit gate: **PASS**. Tests prove stale/conflict resolution,
  all four policy outcomes, safe trace contents, trace-derived receipt rendering,
  and versioned golden regression cases.

## Iteration 7 rubric: portable HTTP delivery

This rubric is frozen before implementation. Cloud hosting is explicitly out of
scope for this iteration; the artifact must be deployable anywhere Docker runs.

| Gate | Pass condition | Evidence |
|---|---|---|
| P7.1 API contract | Health, governed write, memory pack, and agent answer endpoints return stable JSON | API tests |
| P7.2 Service reuse | HTTP handlers call existing `MemoryService` and `MemoryAgent`; no duplicate retrieval logic | integration tests/source review |
| P7.3 Safety | Request-size limit, JSON validation, optional bearer token, and controlled errors work | negative API tests |
| P7.4 Persistence | A write made over HTTP is recalled by a later HTTP request through DuckDB | API integration test |
| P7.5 Observability | HTTP agent requests preserve JSONL trace and context receipt behavior | trace test |
| P7.6 Portability | Dockerfile has a non-root runtime, health check, persistent data path, and no embedded secrets | Docker inspection/build |
| P7.7 Compatibility | Existing 27 tests still pass | full non-Docker suite |
| P7.E2E | A real local HTTP server handles health, write, and ask across separate requests | socket-level E2E |

### Iteration 7 result

- P7.1-P7.7: **PASS**, full suite 29 tests.
- Docker image build: **PASS**, Python 3.11 + DuckDB 1.5.4.
- P7.E2E: **PASS**, real container health/write/ask flow.
- Non-root runtime: **PASS**, user `contextvault` (UID 10001).
- Persistent `/data` volume and container health check: **PASS**.
- Hosting provider and public deployment: intentionally deferred for later cost review.

## Iteration 8 rubric: portfolio release candidate

| Gate | Pass condition | Evidence |
|---|---|---|
| P8.1 README | English README explains value, architecture, setup, demo, API, tests, privacy, and limitations | documentation audit |
| P8.2 Architecture | Editable diagram matches the shipped Markdown/DuckDB/service/agent/API flow | SVG + source review |
| P8.3 Baseline | Versioned scenarios compare memory-enabled and memory-disabled answers with deterministic metrics | evaluation tests/report |
| P8.4 Demo | One command shows governed write, cross-session recall, stale correction, relations, answer, and receipt | demo E2E |
| P8.5 Reproducibility | README commands run from repository root without cloud credentials | clean command audit |
| P8.6 Honesty | Qwen, public hosting, multi-writer scaling, and production security are explicitly marked optional/pending | documentation audit |
| P8.7 Compatibility | Full API/Docker-era regression remains green | full test suite |

### Iteration 8 result

- P8.1 README: **PASS**, English portfolio documentation replaces the planning README.
- P8.2 Architecture: **PASS**, editable SVG matches shipped components and optional boundaries.
- P8.3 Baseline: **PASS at the time**, 3/3 golden cases. Its former “grounded answers” label was corrected by P9 to citation-contract coverage.
- P8.4 Demo: **PASS**, one command covers all three sessions and trace-derived receipt.
- P8.5 Reproducibility: **PASS**, editable install and documented commands verified.
- P8.6 Honesty: **PASS**, optional Qwen, deferred hosting, security, and single-writer limits documented.
- P8.7 Compatibility: **PASS**, 31 tests at that iteration.

## Documentation audit: 2026-07-01

- Active status, roadmap, architecture and task board reconciled with shipped code.
- Provider-neutral portfolio direction separated from historical Qwen hackathon plans.
- Historical plans carry explicit status banners and are indexed separately.
- Local Markdown link audit: **PASS**, no missing relative targets.
- README/API command and endpoint claims checked against CLI and implementation.
- Stale active claims for SQLite, planned HTTP, and mandatory cloud dependencies: none found.
- Full regression after those documentation changes: **PASS**, 31 tests at that iteration.

## Iteration 9 rubric: evidence and scalability corrections

This rubric is frozen before implementation in response to the technical roast.
The release is not complete until every applicable gate has executable evidence.

| Gate | Pass condition | Evidence |
|---|---|---|
| P9.1 Honest evaluation | The mock metric is named citation-contract coverage, never answer quality or model accuracy | report/docs tests |
| P9.2 Structural budget | Memory packs never use final string slicing, never exceed budget, and end with complete Markdown blocks | boundary/property tests |
| P9.3 SQL retrieval | Candidate scoring, filtering, ordering and limiting execute in DuckDB SQL; Python does not fetch the full table to rank it | source review + retrieval tests |
| P9.4 Retrieval metrics | Evaluation reports recall@k, MRR and latency separately from citation-contract coverage | evaluator tests/report |
| P9.5 Larger corpus | A deterministic, versioned synthetic corpus contains 50–100 varied memories with distractors and conflicts | corpus test |
| P9.6 Concurrency boundary | Process-local writes are serialized explicitly and concurrent writes survive; cross-process/multi-replica limits remain documented | concurrency tests/docs |
| P9.7 Real-provider path | A local Ollama-compatible provider exists with fake-transport tests; live smoke is run only if a local endpoint is available | provider tests/smoke status |
| P9.8 Compatibility | Existing CLI, HTTP, Docker, governance, truthiness and demo behavior remains green | full suite |
| P9.E2E | Evaluation and demo commands run end-to-end and regenerate honest reports | command audit |

### Iteration 9 result

- P9.1: **PASS**; the generated report calls the mock result citation-contract coverage and states its limits.
- P9.2: **PASS**; boundary tests cover 300â€“1400 character budgets without final-output slicing.
- P9.3: **PASS**; DuckDB SQL performs scoring, filtering, ordering and limiting.
- P9.4â€“P9.5: **PASS**; 60 versioned synthetic memories, recall@3 1.000, MRR 0.833, and separately reported latency.
- P9.6: **PASS**; eight concurrent process-local writes persist. Cross-process and multi-replica writes remain unsupported.
- P9.7: **PASS** for the Ollama provider contract and controlled configuration errors. Live smoke: **NOT RUN**, Ollama executable unavailable.
- P9.8: **PASS**, full regression 43 tests.
- P9.E2E: **PASS**, `contextvault demo` and `contextvault evaluate` completed and regenerated the report.

The local retrieval latency observed in this run was 12.038 ms mean. It is
environment-specific evidence, not a production benchmark.

## Presentation demo audit: 2026-07-02

- Added explicit `[ALLOW]`, `[BLOCK]`, `[SELECTED]`, and `[EXCLUDED]` events.
- Added `demo --color auto|always|never`; redirected and test output remains plain by default.
- Added a visible blocked secret-like write without echoing the secret.
- Focused demo/CLI tests: **PASS**, 5 tests.
- Full Windows regression: **PASS**, 44 tests.

## Iteration 10 rubric: shared FastMCP memory adapter

This rubric is frozen before implementation. The iteration passes only when
all applicable gates have executable evidence.

| Gate | Pass condition | Evidence |
|---|---|---|
| M10.1 Official FastMCP | The server uses `mcp.server.fastmcp.FastMCP` from a pinned stable MCP Python SDK series | dependency/source audit |
| M10.2 Read-only boundary | Exactly four public tools exist: context, memory, relations, and receipt; none can mutate memory | MCP tool-list test + source review |
| M10.3 Existing service reuse | MCP delegates retrieval, truth resolution, budgeting, and receipts to existing ContextVault services | unit/integration tests |
| M10.4 Structured contracts | Tool inputs are typed and bounded; outputs expose sources, selections, exclusions, and controlled not-found states | schema and call tests |
| M10.5 Stdio safety | Protocol output is not polluted by application logging or secrets | subprocess MCP E2E |
| M10.6 Client compatibility | A real MCP client initializes, lists tools, and calls the server over stdio | protocol E2E |
| M10.7 Agent setup | Exact current commands for Codex and Claude Code user-level setup, verification, and removal are documented | local CLI audit + docs |
| M10.8 Compatibility | Existing CLI, HTTP, demo, evaluation, Docker-era behavior and full regression remain green | full test suite |
| M10.E2E | A seeded memory is retrieved, a stale memory is excluded, and a receipt is returned through MCP | end-to-end scenario |

Deferred by design: write tools, automatic curation, remote HTTP hosting,
authentication, and MCP SDK v2 migration.

### Iteration 10 RALP result

- M10.1: **PASS**; official `mcp.server.fastmcp.FastMCP`, dependency `mcp>=1.26,<2`.
- M10.2: **PASS**; tool-list test exposes exactly `get_context`, `get_memory`, `get_relations`, and `get_receipt`.
- M10.3–M10.4: **PASS**; tools delegate to `MemoryService`, enforce typed bounds, and return structured source/truth metadata.
- M10.5–M10.6: **PASS**; a real MCP client initializes and calls the server over stdio without protocol pollution.
- M10.7: **PASS**; current local Codex and Claude CLI syntax, verification, removal, and guidance are documented in `docs/MCP.md`.
- M10.8: **PASS** after RALP repair; full Windows regression 47 tests.
- M10.E2E: **PASS**; selected `adr-001-memory-service`, excluded `grep-only-search-is-stale`, and returned the trace receipt.

RALP repair notes:

1. Persistent/thread-crossing DuckDB connections hung under FastMCP on Windows.
2. The final adapter isolates each read-only database operation in a short-lived backend process; task content is passed through JSON stdin, not command-line arguments.
3. The full suite exposed the pre-existing Windows unauthorized-POST reset. The server now consumes bounded rejected bodies and flushes its JSON response; ten consecutive unauthorized requests are covered by the regression test.
4. User-level Codex/Claude configuration was not mutated because the external home-directory write approval did not complete. The server and exact commands are ready for that separate activation step.

### Codex activation: 2026-07-03

- Created `~/.agent-memory/memory.duckdb` and seeded five synthetic demo memories.
- Added global Codex stdio server `agent-memory` with an absolute Python command and explicit source `PYTHONPATH`.
- `codex mcp get agent-memory`: **enabled**.
- `codex mcp list`: **enabled**.
- Fresh-session in-agent tool invocation remains the next smoke test because MCP capabilities are discovered when a Codex session starts.

## Iteration 11 rubric: portfolio repository hygiene

This rubric is frozen before cleanup. Historical evidence may be relocated but
must not be silently destroyed.

| Gate | Pass condition | Evidence |
|---|---|---|
| P11.1 Root clarity | The repository root contains only runtime/build entry points and active source-of-truth documents required by repository guidance | root inventory |
| P11.2 Documentation structure | Active architecture, operations, portfolio material, and dated historical plans have explicit homes and an updated index | link and index audit |
| P11.3 Runtime hygiene | Regenerable caches, local databases, traces, and temporary outputs are absent and ignored | filesystem and ignore audit |
| P11.4 Publication safety | No committed `.env`, database, trace, credential, video, archive, or obvious secret-bearing artifact is present | filename/content scan |
| P11.5 Reproducibility | Package metadata and JSON artifacts validate; full tests and the deterministic demo remain green | command audit |
| P11.6 Repository boundary | The project is an independent valid Git work tree ready for a later remote and clean-clone verification | `git status` |

Public GitHub creation, CI execution, release tagging, and clean-clone proof
remain separate publication gates; cleanup must not claim those external steps
as complete.

### Iteration 11 result

- P11.1: **PASS**; the root now contains only project entry points and active
  repository-level sources required by `AGENTS.md`.
- P11.2: **PASS**; current product docs, architecture decisions, evaluation
  artifacts, and public release boundaries have explicit indexed homes.
- P11.3: **PASS**; runtime caches and the 61 MB local `.tmp` tree were removed;
  ignore rules cover databases, traces, logs, build outputs, videos and env files.
- P11.4: **PASS for the working tree**; filename/content scans found no real
  credentials or generated databases, and the private Alibaba support reference
  was removed. Git-history audit awaits the first canonical repository history.
- P11.5: **PASS locally**; Ruff, baseline MyPy, 47 tests, package build,
  isolated dependency audit, deterministic demo, JSON validation, and Docker
  build/CLI smoke pass.
- P11.6: **PASS**; this directory is now an independent Git work tree on
  `main`. Initial commit, remote creation, hosted CI and clean-clone proof remain
  pending user-controlled publication steps.

## Iteration 12 rubric: public v0.1.0 release

This rubric is frozen before release-state documentation, clean-clone
verification, tagging, or GitHub Release creation. ContextVault v0.1.0 is
complete only when every required gate is PASS against the same release commit.

| Gate | Pass condition | Required evidence |
|---|---|---|
| R12.1 Canonical source | Public canonical repository exists on `main`, has a configured `origin`, and the local branch tracks `origin/main` | GitHub repository metadata and `git status --branch` |
| R12.2 Hosted CI | GitHub Actions quality and container jobs pass for the exact commit tagged `v0.1.0` | successful workflow run and matching commit SHA |
| R12.3 Clean install | A fresh GitHub clone installs successfully with development dependencies outside the source work tree | clone and install command log |
| R12.4 Quality gates | Ruff, MyPy and the complete 47-test suite pass in the fresh clone | command output from the clean clone |
| R12.5 Behavioral evidence | `contextvault demo` shows governed allow/block, cross-session recall, stale exclusion, selected source and a trace-derived receipt; evaluation reports 3/3, recall@3 1.000 and MRR 0.833 | clean-clone demo and evaluation assertions |
| R12.6 Container evidence | The fresh clone builds the non-root image; the container health endpoint returns `ok`; runtime UID is `10001` | Docker build, health response and `id -u` output |
| R12.7 Documentation integrity | README links the canonical repository and CI badge; current status and next steps distinguish completed release gates from optional follow-up work; local Markdown links resolve | documentation and link audit |
| R12.8 Publication safety | Git history contains no raw videos, `.env`, databases, traces, private planning archive, handoff material or obvious real credentials | tracked-file and content scan |
| R12.9 Immutable release | Annotated `v0.1.0` tag and public GitHub Release point to the exact commit that passed R12.2–R12.8 | tag SHA and GitHub Release metadata |

Public cloud hosting, live Qwen/Ollama calls, multi-user identity, hybrid
retrieval, a full 118-second video, and LinkedIn publication are explicitly
outside the v0.1.0 completion gate.

### Iteration 12 result before tagging

Verified against public commit `8435716d47b93a470a4a79eb65aa99de38e7034d`
on 2026-07-05.

- R12.1: **PASS**; the public canonical repository is
  `panualaluusua/contextvault-memoryagent`, and local `main` tracks
  `origin/main`.
- R12.2: **PASS**; hosted GitHub Actions run `28740600253` completed
  successfully for the verified commit.
- R12.3: **PASS**; a new clone from the public GitHub URL installed in a new
  Python 3.11 virtual environment with `pip install -e ".[dev]"`.
- R12.4: **PASS**; Ruff, MyPy over 17 source files, and 47/47 tests passed in
  the clean clone.
- R12.5: **PASS after one RALP repair**; the demo proved governed allow/block,
  cross-session recall, stale exclusion, selected source and receipt. The first
  evaluation check exposed an ambiguous summary, so the report and regression
  test were repaired to state `Golden cases: 3/3 passed` explicitly. Recall@3
  remained 1.000 and MRR 0.833.
- R12.6: **PASS**; the clean clone built `contextvault:v0.1.0-verify`, ran as
  UID `10001`, and returned `status: ok` from the health endpoint.
- R12.7: **PASS**; the README contains the canonical URL and CI badge, active
  Markdown links resolve, and status/roadmap documents match the release state.
- R12.8: **PASS**; tracked-file and full Git-patch scans found no raw videos,
  `.env`, databases, traces, private planning directories, personal paths,
  private keys, AWS keys, or plausible live API keys.
- R12.9: **PENDING** until the evidence commit passes hosted CI and the
  annotated tag plus GitHub Release are created for that exact commit.
