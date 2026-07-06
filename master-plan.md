# MemoryGraph Master Plan

**Current Version**: v0.13.0 (TypeScript/Bun CLI)
**Last Updated**: July 2026
**Test Status**: 97 tests passing, typecheck clean

This is the single source of truth for all pending work on MemoryGraph.
Completed items are marked with ~~strikethrough~~. Priorities: P0 (blockers),
P1 (should fix soon), P2 (nice to have), P3 (future/strategic).

---

## Current State

MemoryGraph was rewritten from Python MCP server to TypeScript/Bun CLI in v0.13.0.
The port is ~90% complete. An adversarial review (3 agents: red-team, security,
port-completeness) identified 41 findings; 23 were fixed in the v0.13.0 release commit.

- **Runtime**: TypeScript/Bun (was Python)
- **Interface**: CLI (was MCP server)
- **Backends**: 5 working (falkordblite, sqlite, falkordb, memgraph, cloud), 3 stubs
- **Commands**: 35+ CLI commands across 8 categories
- **Tests**: 97 tests, 12 files

---

## P0 - Adversarial Review: High Priority

These are functional bugs that make features silently non-functional.

- [ ] **H7: Temporal intelligence non-functional** — `intelligence/temporal.ts` traverses `[:PREVIOUS]` chains and reads `is_current`/`superseded_by` properties that backends never create. `updateMemory` does in-place `SET` with no versioning. Fix: implement versioning in `updateMemory` (create new node + `PREVIOUS` relationship, set `is_current`/`superseded_by`), or remove/disable the temporal module until infrastructure exists.
- [ ] **M7: Intelligence/analytics/proactive commands throw on SQLite and Cloud** — `cmdEntities --link`, `cmdPatterns`, `cmdContext`, `cmdVisualize`, `cmdSimilarity`, `cmdLearning`, `cmdGaps`, `cmdBriefing`, `cmdPredict`, `cmdWarn`, `cmdOutcome` all call `executeQuery` which throws on non-Cypher backends. Fix: guard with `backend.isCypherCapable()` and return a clear message, or implement via backend CRUD methods.
- [ ] **M1: `recall` is identical to `search`** — `handleRecallMemories` calls `db.searchMemories` instead of `backend.recallMemories`. SQLite and Cloud both implement `recallMemories` with fuzzy/recall semantics but it's never invoked. Fix: have `handleRecallMemories` call `db.backend?.recallMemories?.()` when available, falling back to `searchMemories`.

## P1 - Adversarial Review: Medium Priority

Correctness issues that degrade quality but don't break features entirely.

- [ ] **M8: SDK and internal cloud adapter target different APIs** — SDK uses `https://api.memorygraph.dev` with `Authorization: Bearer` and paths `/api/v1/memories`. Internal `CloudRESTAdapter` uses `https://graph-api.memorygraph.dev` with `X-API-Key` and paths `/memories`. Fix: align base URL, auth header, and path scheme.
- [ ] **M6: `getRelatedMemories` may reverse relationship direction** — Undirected traversal `(start)-[r...]-(related)` means `r[0]` could be incoming or outgoing, but reconstructed `Relationship` always sets `from_memory_id: memoryId`. Fix: determine direction from `startNode(rel)` vs `endNode(rel)`.
- [ ] **M3: `parseSimpleArgs` cannot pass values starting with `--`** — `--query --foo` misparses. Fix: use `--` as end-of-options sentinel, or accept `--key=--value`.
- [ ] **M12: `handleWhatChanged` does N+1 `getRelatedMemories` calls** — Fetches up to 1000 memories then calls `getRelatedMemories` per memory. Fix: single Cypher query filtering relationships by `recorded_at >= $since`.

## P1 - Adversarial Review: Security

- [ ] **SEC-4: Secret exposure in `config` command** — URIs with embedded credentials (e.g. `bolt://user:pass@host`) printed verbatim. Fix: redact userinfo from URIs before printing.
- [ ] **SEC-5: Sensitive data in error messages** — Backend errors include raw query text and parameter values. Fix: log full error at debug level, surface generic message.
- [ ] **SEC-9: Weak sensitive-data filter in context capture** — Regex filter misses multi-word leaks, non-standard TLDs, base64/hex blobs, AWS keys without labels, SSH keys.
- [ ] **SEC-10: LIKE wildcard injection in SQLite** — Tag and project_path values with `%` or `_` are interpreted as LIKE wildcards. Fix: escape LIKE wildcards.
- [ ] **SEC-11: Relationship type not validated by SQLite backend** — Import path bypasses `isRelationshipType` check. Fix: validate in SQLite `createRelationship` and `importFromJson`.

## P2 - Adversarial Review: Low Priority

- [ ] **L1**: Dead code in `context-extractor.ts` — redundant type cast after null guard
- [ ] **L2**: Dead confidence branch in `entity-extraction.ts` — FUNCTION regex captures name without `()` so `endsWith("()")` check is dead
- [ ] **L3**: Brittle JSON `LIKE` matching in SQLite `project_path` filter — use `json_extract` instead
- [ ] **L4**: Integration modules use relationship types (`PART_OF`, `MODIFIES`, `CREATES`, etc.) not in `RelationshipType` enum
- [ ] **L5**: `findAllCycles` throws "not yet implemented" — implement or remove
- [ ] **L6**: `getProjectFromMemories` is a stub returning `null` — implement or remove
- [ ] **M10: CLI test is vacuous** — `cli-commands.test.ts` tests a local reimplementation of `parseSimpleArgs` and only asserts source contains `case` strings. Fix: test actual command execution.

---

## P1 - Port Completeness Gaps

Features that existed in the Python codebase (v0.12.4) but are missing from the TypeScript port.

### Missing Modules

- [ ] **`relationships.py` not ported** — RelationshipManager (metadata, validation, strength calc, inverse handling, contradiction detection, type suggestion) and `RELATIONSHIP_TYPE_METADATA` mapping. No TS equivalent.
- [ ] **`graph_analytics.py` not ported** — GraphAnalyzer (path finding, clustering, bridge detection, metrics) and `GraphPath`/`MemoryCluster`/`BridgeNode` classes. No TS equivalent.
- [ ] **`advanced_tools.py` not ported** — 7 MCP tools have no CLI equivalent: `find-memory-path`, `analyze-clusters`, `bridge-memories`, `suggest-relationship`, `reinforce-relationship`, `relationship-categories`, `graph-metrics`.

### Missing Backends

- [ ] **neo4j backend** — Was a full 215-line implementation in Python. TS port is a throwing stub. Would use `BaseBoltBackend`.
- [ ] **turso backend** — Was a full 451-line implementation in Python (libSQL). TS port is a throwing stub.
- [ ] **ladybugdb backend** — Was a full 238-line implementation in Python. TS port is a throwing stub.

### Missing Functionality

- [ ] **Migration scripts** — `bitemporal_migration.py` and `multitenancy_migration.py` plus `migrate-to-multitenant` CLI command not ported. Backend-to-backend migration IS ported.
- [ ] **`update_relationship_properties`** — No TS backend implements post-creation relationship property updates.
- [ ] **`findAllCycles`** — Throws "not yet implemented". Only `hasCycle` is ported.
- [ ] **`predictSolutionEffectiveness` and `trackMemoryROI`** — Exported from `analytics/advanced-queries.ts` but not wired to any CLI command.
- [ ] **SDK framework integrations** — 4 Python adapters (autogen, crewai, langchain, llamaindex) not ported. TS SDK is framework-agnostic by design.

### Missing Test Coverage

- [ ] **proactive/** — No tests for session-briefing, predictive, outcome-learning
- [ ] **integration/** — No tests for context-capture, project-analysis, workflow-tracking
- [ ] **analytics/** — No tests for advanced-queries (visualization, similarity, learning paths, gaps)
- [ ] **sdk/** — No TS SDK tests
- [ ] **backends/cloud.ts** — No tests for cloud backend
- [ ] Python had ~100 test files; TS has 12

---

## P3 - Planned Features (v0.14+)

- [ ] **Web visualization dashboard** — Browser-based graph visualization at app.memorygraph.dev
- [ ] **PostgreSQL backend** — `pg_graph` backend for PostgreSQL users
- [ ] **Enhanced embedding support** — Optional semantic search beyond keyword/entity matching
- [ ] **Workflow automation templates** — Pre-built workflow patterns for common dev tasks

## P3 - Strategic (Future)

- [ ] **VS Code extension** — Cloud-only, subscription required. Coding memory where you code.
- [ ] **GitHub Action** — CI/CD memory automation for automated context capture
- [ ] **Multi-tenancy** — Schema enhancement for multi-tenant support (tenant_id, team_id, visibility fields)
- [ ] **Insights/analytics dashboard** — Knowledge gap detection, pattern discovery, expertise mapping, stale knowledge alerts
- [ ] **Framework integrations** — LlamaIndex, LangChain/LangGraph, CrewAI, AutoGen adapters (TypeScript ecosystem equivalents)

---

## Completed in v0.13.0

~~23 adversarial review findings fixed~~ (5 Critical, 7 High, 11 Medium/Low) — see CHANGELOG.md for details.

~~TypeScript port from Python~~ — 303 files changed, net -63,818 lines. 35+ CLI commands, 5 working backends, 97 tests.

~~Adversarial review completed~~ — 3-agent review (red-team, security, port-completeness). Reports in `REDTEAM_FINDINGS.md` and `SECURITY_REVIEW.md`.

---

## Archived Workplans

Historical workplans from the Python era are in `docs/planning/` and `docs/archive/`.
These are reference-only and mostly outdated (reference Python, MCP server, PyPI).
The `PRODUCT_ROADMAP.md` contains competitive analysis and marketing strategy.
