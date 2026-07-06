<p align="center">
  <img src="docs/html/logo-220.png" alt="MemoryGraph Logo" width="220">
</p>

<h1 align="center">MemoryGraph</h1>

<p align="center">
  <strong>Graph-based Memory CLI for AI Coding Agents</strong>
</p>

<p align="center">
  <a href="https://bun.sh/"><img src="https://img.shields.io/badge/runtime-Bun-000000" alt="Bun"></a>
  <a href="https://www.typescriptlang.org/"><img src="https://img.shields.io/badge/language-TypeScript-3178C6" alt="TypeScript"></a>
  <img src="https://img.shields.io/badge/setup-zero--config-green" alt="Zero Config">
  <img src="https://img.shields.io/badge/backends-5%20options-purple" alt="5 Backends">
</p>

<p align="center">
  A graph-based memory system that gives AI coding agents persistent memory.<br>
  Store patterns, track relationships, retrieve knowledge across sessions.
</p>

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/gregorydickson/memory-graph.git
cd memory-graph/ts
bun install

# 2. Store a memory
bun run src/cli.ts store \
  --type solution \
  --title "Use Zod for validation" \
  --content "All runtime validation uses Zod schemas" \
  --tags "architecture,validation"

# 3. Recall memories by natural language query
bun run src/cli.ts recall --query "validation" --limit 10

# 4. View stats
bun run src/cli.ts stats
```

No database server required. FalkorDBLite (embedded graph DB) is used by default with zero configuration.

**Important:** MemoryGraph provides memory tools, but your coding agent won't use them automatically. You need to prompt or configure it to store memories. See [Memory Best Practices](#memory-best-practices) below.

---

## Why MemoryGraph?

### Graph Relationships Make the Difference

Flat storage (CLAUDE.md, vector stores) keeps memories as isolated entries. Graph storage connects them:

```
[timeout_fix] --CAUSES--> [memory_leak] --SOLVED_BY--> [connection_pooling]
     |                                                        |
     +------------------SUPERSEDED_BY------------------------+
```

Query: "What happened with retry logic?" returns the full causal chain, not just individual memories.

### When to Use What

| Use CLAUDE.md / AGENTS.md For | Use MemoryGraph For |
|-------------------------------|---------------------|
| "Always use 2-space indentation" | "Last time we used 4-space, it broke the linter" |
| "Run tests before committing" | "The auth tests failed because of X, fixed by Y" |
| Static rules, prime directives | Dynamic learnings with relationships |

---

## CLI Commands

### Memory Operations

| Command | Purpose | Example |
|---------|---------|---------|
| `store` | Store a new memory | `store --type solution --title "Fix" --content "..." --tags redis,fix` |
| `get` | Get a memory by ID | `get <memory-id>` |
| `update` | Update an existing memory | `update <id> --title "New title"` |
| `delete` | Delete a memory | `delete <memory-id>` |
| `search` | Search with filters | `search --query "timeout" --tags redis --limit 10` |
| `recall` | Natural language recall | `recall --query "authentication security"` |
| `related` | Get related memories | `related <id> --types SOLVES,CAUSES --max-depth 2` |
| `link` | Create a relationship | `link <from-id> <to-id> SOLVES --strength 0.8` |

### Context Search

| Command | Purpose |
|---------|---------|
| `context-search` | Search relationships by type, strength, or context text |
| `contextual-search` | Search within a memory's related items |

### Intelligence

| Command | Purpose |
|---------|---------|
| `entities` | Extract entities (files, functions, classes, technologies) from a memory |
| `patterns` | Find similar problems and suggest patterns |
| `context` | Get intelligent context retrieval with entity and keyword matching |

### Analytics

| Command | Purpose |
|---------|---------|
| `stats` | Database statistics (memory count, types, relationships) |
| `activity` | Recent activity summary with unresolved problems |
| `visualize` | Graph visualization data (nodes and edges) |
| `similarity` | Analyze solution similarity for a given memory |
| `learning` | Recommend learning paths for a topic |
| `gaps` | Identify knowledge gaps (unsolved problems, missing connections) |

### Proactive

| Command | Purpose |
|---------|---------|
| `briefing` | Generate a session briefing with recent activity and open issues |
| `predict` | Predict what might be needed based on current context |
| `warn` | Warn about potential issues (deprecated approaches, known errors) |
| `outcome` | Record an outcome for a memory (success/failure tracking) |

### Integration

| Command | Purpose |
|---------|---------|
| `capture` | Capture task context from current environment |
| `analyze-project` | Analyze the current project codebase |
| `workflow` | Track or suggest workflow improvements |

### Temporal

| Command | Purpose |
|---------|---------|
| `as-of` | Query relationships as they existed at a specific time |
| `history` | Get full relationship history for a memory |
| `changes` | Show relationship changes since a timestamp |

### Data Management

| Command | Purpose |
|---------|---------|
| `export` | Export to JSON or Markdown |
| `import` | Import from JSON |
| `migrate` | Migrate between backends |
| `health` | Run a health check |
| `config` | Show current configuration |

---

## Backends

| Backend | Type | Config | Native Graph | Zero-Config | Best For |
|---------|------|--------|--------------|-------------|----------|
| **falkordblite** (default) | Embedded | File path | Cypher | Yes | Default, graph queries without server |
| **sqlite** | Embedded | File path | Simulated | Yes | Zero-dependency fallback |
| **falkordb** | Client-server | Host:port | Cypher | No | High-performance production |
| **memgraph** | Client-server | Bolt URI | Cypher | No | Real-time analytics |
| **cloud** | Cloud | API Key | Cypher | No | Multi-device sync, team sharing |

### Backend Configuration

```bash
# Use FalkorDBLite (default, zero-config)
bun run src/cli.ts stats

# Use SQLite
MEMORY_BACKEND=sqlite bun run src/cli.ts stats

# Use FalkorDB (client-server)
MEMORY_BACKEND=falkordb MEMORY_FALKORDB_HOST=localhost MEMORY_FALKORDB_PORT=6379 bun run src/cli.ts stats

# Use Memgraph
MEMORY_BACKEND=memgraph MEMORY_MEMGRAPH_URI=bolt://localhost:7687 bun run src/cli.ts stats

# Use Cloud
MEMORY_BACKEND=cloud MEMORYGRAPH_API_KEY=mg_your_key bun run src/cli.ts stats
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MEMORY_BACKEND` | Backend type | `falkordblite` |
| `MEMORY_FALKORDBLITE_PATH` | FalkorDBLite database path | `~/.memorygraph/falkordblite.db` |
| `MEMORY_SQLITE_PATH` | SQLite database path | `~/.memorygraph/memory.db` |
| `MEMORY_FALKORDB_HOST` | FalkorDB server host | `localhost` |
| `MEMORY_FALKORDB_PORT` | FalkorDB server port | `6379` |
| `MEMORY_MEMGRAPH_URI` | Memgraph Bolt URI | `bolt://localhost:7687` |
| `MEMORYGRAPH_API_KEY` | Cloud API key | - |
| `MEMORYGRAPH_API_URL` | Cloud API URL | `https://graph-api.memorygraph.dev` |
| `MEMORY_TOOL_PROFILE` | Tool profile (core or extended) | `core` |
| `MEMORY_LOG_LEVEL` | Log level | `INFO` |

---

## Memory Types

| Type | Use Case |
|------|----------|
| `task` | Tasks and action items |
| `code_pattern` | Recurring code patterns or conventions |
| `problem` | Problems or challenges encountered |
| `solution` | Solutions, decisions, or approaches chosen |
| `project` | Project context, environment, setup info |
| `technology` | Technology choices and evaluations |
| `error` | Errors discovered |
| `fix` | Fixes applied to errors |
| `command` | Useful commands or CLI snippets |
| `file_context` | Context about specific files |
| `workflow` | Workflow or process descriptions |
| `general` | General purpose memories |
| `conversation` | Conversation summaries |

## Relationship Types

| Type | Meaning |
|------|---------|
| `RELATED_TO` | General connection |
| `BUILDS_ON` | New memory extends an older one |
| `CONTRADICTS` | New memory supersedes or invalidates an older one |
| `CONFIRMS` | New memory provides evidence for an older one |
| `SOLVES` | A solution solves a problem |
| `CAUSES` | One memory causes another |
| `REQUIRES` | One memory depends on another |
| `IMPROVES` | An improvement over an existing approach |
| `REPLACES` | Replaces an older approach |
| `DEPENDS_ON` | Workflow dependency |

---

## Memory Best Practices

### Session Workflow

```bash
# Start of session: recall recent context
bun run src/cli.ts recall --query "recent work" --limit 10

# During work: store decisions and patterns
bun run src/cli.ts store \
  --type solution \
  --title "Use JWT for auth" \
  --content "JWT tokens with 24h expiry, refresh token rotation" \
  --tags "auth,security,api" \
  --importance 0.8

# Link it to a prior decision
bun run src/cli.ts link <new-id> <prior-id> BUILDS_ON --strength 0.9

# End of session: store summary
bun run src/cli.ts store \
  --type conversation \
  --title "Session: auth refactor" \
  --content "Refactored auth middleware, added JWT, fixed token refresh bug" \
  --tags "auth,session-summary"

# Export backup
bun run src/cli.ts export --format json --output session-backup.json
```

### Add to CLAUDE.md or AGENTS.md

```markdown
## Memory Protocol

### REQUIRED: Before Starting Work
You MUST use `recall` before any task. Query by project, tech, or task type.

### REQUIRED: Automatic Storage Triggers
Store memories on ANY of:
- Git commit: what was fixed/added
- Bug fix: problem + solution
- Architecture decision: choice + rationale
- Pattern discovered: reusable approach

### Memory Fields
- Type: solution | problem | code_pattern | fix | error | workflow
- Title: Specific, searchable
- Content: Accomplishment, decisions, patterns
- Tags: project, tech, category (required)
- Importance: 0.8+ critical, 0.5-0.7 standard, 0.3-0.4 minor
- Relationships: Link related memories when they exist
```

---

## Architecture

### Project Structure
```
memory-graph/
├── ts/
│   ├── src/
│   │   ├── cli.ts              # CLI entry point (35+ commands)
│   │   ├── index.ts            # Library exports
│   │   ├── config.ts           # Configuration management
│   │   ├── database.ts         # Database interface
│   │   ├── models.ts           # Data models and schemas
│   │   ├── backends/           # Backend implementations
│   │   │   ├── falkordb-shared.ts  # Shared FalkorDB base class
│   │   │   ├── falkordblite.ts     # Embedded FalkorDBLite
│   │   │   ├── falkordb.ts         # Client-server FalkorDB
│   │   │   ├── bolt-shared.ts      # Shared Bolt protocol base
│   │   │   ├── memgraph.ts         # Memgraph (Bolt protocol)
│   │   │   ├── sqlite.ts           # SQLite fallback
│   │   │   ├── cloud.ts            # Cloud REST API
│   │   │   └── factory.ts          # Backend factory
│   │   ├── tools/              # CLI tool handlers
│   │   ├── intelligence/       # Entity extraction, pattern recognition, context retrieval
│   │   ├── analytics/          # Graph visualization, similarity, learning paths
│   │   ├── proactive/          # Session briefing, predictions, outcome learning
│   │   ├── integration/        # Context capture, project analysis, workflow tracking
│   │   ├── migration/          # Backend-to-backend migration
│   │   ├── sdk/                # Cloud API client SDK
│   │   └── utils/              # Export/import, validation, helpers
│   ├── tests/                  # 97 tests
│   └── package.json
├── docs/                       # Documentation
└── CLAUDE.md                   # Agent instructions
```

### Building

```bash
cd ts
bun install
bun test                    # Run tests
npx tsc --noEmit            # Type check
bun build src/cli.ts --compile --outfile memorygraph  # Compile binary
```

---

## Import / Migration

```bash
# Import from JSON export
bun run src/cli.ts import --input backup.json --skip-duplicates

# Migrate between backends
bun run src/cli.ts migrate --to sqlite --to-path ./local.db
bun run src/cli.ts migrate --to falkordblite --to-path ./graph.falkor --no-verify
bun run src/cli.ts migrate --to memgraph --to-uri bolt://localhost:7687
```

---

## SDK

The TypeScript SDK provides a client for the MemoryGraph Cloud API:

```typescript
import { MemoryGraphClient } from "memorygraph/sdk";

const client = new MemoryGraphClient({ apiKey: "mg_..." });

const memory = await client.createMemory({
  type: "solution",
  title: "Fixed timeout issue",
  content: "Used exponential backoff with retries",
  tags: ["redis", "timeout"],
});
```

---

## License

MIT License - see [LICENSE](LICENSE).

---

**Start simple. Upgrade when needed. Never lose context again.**
