# MemoryGraph v0.13.0 Release Notes

**Release Date:** July 5, 2026

MemoryGraph has been completely rewritten from Python to TypeScript/Bun. The MCP server is now a CLI that coding agents invoke directly via shell commands. All features from the Python codebase have been ported, with 97 tests passing and a clean typecheck.

---

## Highlights

- **TypeScript/Bun rewrite** — entire codebase ported from Python (303 files changed, net -63,818 lines)
- **CLI-first architecture** — agents run `memorygraph` commands directly, no MCP protocol overhead
- **5 working backends** — FalkorDBLite (default), SQLite, FalkorDB, Memgraph, Cloud
- **35+ CLI commands** across memory ops, intelligence, analytics, proactive, integration, temporal
- **97 tests passing**, typecheck clean

---

## What Changed

### Python MCP Server → TypeScript CLI

The biggest change is the shift from an MCP server to a standalone CLI. Coding agents already execute shell commands, so MemoryGraph now provides a `memorygraph` binary they call directly. This eliminates the MCP protocol layer, simplifies deployment, and makes memory available to any agent that can run commands — Claude Code, Cursor, Windsurf, Continue, or any other.

```bash
# Install
cd memory-graph/ts && bun install && bun link

# Use
memorygraph recall --query "authentication redis" --limit 10
memorygraph store --type solution --title "Fix" --content "..." --tags redis,fix
memorygraph link <from-id> <to-id> SOLVES --strength 0.8
```

### Backends

All 5 backends from the Python version are ported and working:

| Backend | Type | Base Class | Status |
|---------|------|------------|--------|
| FalkorDBLite (default) | Embedded | `BaseFalkorDBBackend` | Working |
| SQLite | Embedded | own impl | Working |
| FalkorDB | Client-server | `BaseFalkorDBBackend` | Working |
| Memgraph | Client-server | `BaseBoltBackend` | Working |
| Cloud | Cloud REST | own impl | Working |

Shared Cypher logic lives in `BaseFalkorDBBackend` (FalkorDB + FalkorDBLite) and `BaseBoltBackend` (Memgraph, Neo4j stub). The factory dispatches via a dict lookup.

### Intelligence, Analytics, Proactive, Integration

All modules from the Python version are ported:

- **Intelligence**: Entity extraction (12 types, regex-based), pattern recognition, context retrieval with multi-factor ranking
- **Analytics**: Graph visualization, solution similarity (Jaccard), learning paths, knowledge gaps
- **Proactive**: Session briefings, predictive suggestions, issue warnings, outcome learning
- **Integration**: Context capture, project analysis, workflow tracking
- **Migration**: Backend-to-backend with verification
- **SDK**: Cloud API client for TypeScript apps

### Documentation

- README rewritten for TypeScript CLI with agent integration templates
- CLAUDE.md and AGENTS.md condensed for token efficiency (131 → 38 lines, 125 → 50 lines)
- Ready-to-paste instruction templates for Claude Code, Cursor, and generic agents

---

## Testing

| Metric | Value |
|--------|-------|
| Test files | 12 |
| Tests | 97 |
| Expectations | 242 |
| Failures | 0 |
| Typecheck | Clean |
| Runtime | ~750ms |

Test coverage: activity-tools, cli-commands, config, context-retrieval, entity-extraction, export-import, falkordb-backends, migration, models, pattern-recognition, sqlite-backend, temporal.

---

## Migration from v0.12.4

### For end users

1. **Uninstall Python version**: `pip uninstall memorygraphMCP`
2. **Install TypeScript version**: `cd memory-graph/ts && bun install && bun link`
3. **Remove MCP config**: Delete the MemoryGraph entry from your MCP server config (Claude Code, Cursor, etc.)
4. **Add agent instructions**: Paste the template from the README into your agent's instruction file
5. **Data persists**: Your `~/.memorygraph/` database is unchanged — FalkorDBLite and SQLite databases are compatible

### For developers

```bash
cd ts
bun install
bun test             # 97 tests
npx tsc --noEmit     # typecheck
bun build src/cli.ts --compile --outfile memorygraph  # compile binary
```

---

## Breaking Changes

- **Runtime**: Python → TypeScript/Bun (requires Bun 1.1+)
- **Interface**: MCP server → CLI (no longer an MCP server, agents call `memorygraph` directly)
- **Installation**: `pip install` → `bun install && bun link` or compiled binary
- **Python SDK removed**: Use the TypeScript SDK (`memorygraph/sdk`) for cloud API access

---

## What's Next (v0.14+)

- Web visualization dashboard
- PostgreSQL backend support (pg_graph)
- Enhanced embedding support
- Workflow automation templates

---

## Contributors

- Gregory Dickson

---

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for the complete history.
