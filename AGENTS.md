# AGENTS.md

MemoryGraph is a TypeScript/Bun CLI for graph-based memory storage.

## Master Plan

See `master-plan.md` (repo root) for the full task list, priorities, and port completeness gaps.

## Setup

```bash
cd ts && bun install
```

## Development

```bash
bun test             # 97 tests
npx tsc --noEmit     # typecheck
bun run src/cli.ts <command>  # run CLI directly
```

## Project Layout

```
ts/src/
  cli.ts              # CLI entry point, 35+ commands
  index.ts            # library barrel exports
  config.ts           # env-based config (static getters)
  database.ts         # IMemoryDatabase interface + wrappers
  models.ts           # Zod schemas: Memory, Relationship, SearchQuery
  errors.ts           # error types
  backends/           # GraphBackend implementations + factory
  tools/              # CLI tool handlers (handleToolErrors wrapper)
  intelligence/       # entity extraction, pattern recognition, context retrieval
  analytics/          # graph visualization, similarity, learning paths
  proactive/          # session briefing, predictions, outcome tracking
  integration/        # context capture, project analysis, workflow tracking
  migration/          # backend-to-backend migration
  sdk/                # cloud API client
  utils/              # export/import, validation, helpers
ts/tests/             # test files
```

## Dependencies

- `falkordblite` - embedded graph DB (default backend)
- `falkordb` - client-server FalkorDB driver
- `neo4j-driver` - Bolt protocol driver (Memgraph)
- `zod` - schema validation

## Adding a New Backend

1. Create `ts/src/backends/<name>.ts`
2. Extend `BaseFalkorDBBackend` (Cypher) or `BaseBoltBackend` (Bolt) or implement `GraphBackend` directly
3. Add to `factory.ts` dispatch and `backends/index.ts` exports
4. Add config getters to `config.ts` if needed
