# CLAUDE.md

MemoryGraph is a graph-based memory CLI for AI coding agents, written in TypeScript/Bun.

## Master Plan

See `master-plan.md` (repo root) for the full task list, priorities, and port completeness gaps.

## Build & Test

```bash
cd ts
bun install          # install deps
bun test             # run tests (97 tests)
npx tsc --noEmit     # typecheck
bun build src/cli.ts --compile --outfile memorygraph  # compile binary
```

## Architecture

All source is in `ts/src/`. Entry point is `cli.ts`, library exports from `index.ts`.

- **backends/**: Graph database backends. `BaseFalkorDBBackend` (shared Cypher logic for FalkorDB/FalkorDBLite), `BaseBoltBackend` (shared Bolt protocol for Memgraph/Neo4j). Factory dispatch in `factory.ts`.
- **tools/**: CLI tool handlers wrapped with `handleToolErrors`. Each returns `{ isError, text }`.
- **models.ts**: Zod schemas and types for Memory, Relationship, SearchQuery.
- **config.ts**: Env-based config, all getters read `process.env` at call time.
- **database.ts**: `IMemoryDatabase` interface, `MemoryDatabase` (local) and `CloudMemoryDatabase` (cloud).
- **intelligence/**: Entity extraction (regex-based), pattern recognition, context retrieval. All require Cypher-capable backend.
- **analytics/**: Graph visualization, solution similarity, learning paths, knowledge gaps.
- **proactive/**: Session briefing, predictive suggestions, outcome learning.
- **integration/**: Context capture, project analysis, workflow tracking.
- **migration/**: Backend-to-backend migration with verification.
- **sdk/**: Cloud API client for external use.

## Key Patterns

- Backends implement `GraphBackend` interface (`base.ts`). Cypher backends share query logic via base classes; SQLite has its own implementation.
- Tool handlers use `handleToolErrors` decorator for consistent error handling.
- CLI uses `parseSimpleArgs` for arg parsing (not `parseArgs` from `node:util`).
- Config is read-only via static getters; CLI overrides by setting `process.env`.
- Intelligence/analytics/proactive/integration modules take `GraphBackend` as first arg, not `IMemoryDatabase`.

## Backends

| Backend | Status | Base class |
|---------|--------|------------|
| falkordblite | Working | `BaseFalkorDBBackend` |
| sqlite | Working | own impl |
| falkordb | Working | `BaseFalkorDBBackend` |
| memgraph | Working | `BaseBoltBackend` |
| cloud | Working | own impl |
| neo4j | Stub (throws) | would use `BaseBoltBackend` |
| turso | Stub (throws) | - |
| ladybugdb | Stub (throws) | - |
