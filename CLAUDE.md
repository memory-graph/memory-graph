# CLAUDE.md - Memory Graph Directives for Coding Agents

## Overview

Memory Graph is a CLI-based memory system for coding agents. It stores, retrieves,
and links memories (decisions, patterns, bugs, context) in a local graph database
so that knowledge persists across sessions.

## Quick Start

```bash
# Store a memory
bun run ts/src/index.ts store \
  --type solution \
  --title "Use Zod for validation" \
  --content "All runtime validation uses Zod schemas" \
  --tags "architecture,validation"

# Recall memories by natural language query
bun run ts/src/index.ts recall --query "validation" --limit 10

# Search by keyword
bun run ts/src/index.ts search --query "validation" --limit 5

# Get a specific memory
bun run ts/src/index.ts get --id <memory-id>

# Link two memories
bun run ts/src/index.ts link \
  --from <memory-id-1> \
  --to <memory-id-2> \
  --type BUILDS_ON \
  --strength 0.8

# Find related memories
bun run ts/src/index.ts related --id <memory-id> --max-depth 2

# View stats
bun run ts/src/index.ts stats

# Export all memories
bun run ts/src/index.ts export --output backup.json
```

## When to Store Memories

Store a memory when you:

1. **Make an architectural decision** - type `solution`, tags: `architecture`
2. **Discover a bug or fix** - type `error` or `fix`, tags: `bugfix`
3. **Learn a project pattern** - type `code_pattern`, tags: `convention`
4. **Record important context** - type `project` or `file_context`, tags: `project`
5. **Record a workflow** - type `workflow`, tags: `process`

Do NOT store a memory for:
- Trivial changes (typo fixes, formatting)
- Information already in the code or docs
- Transient debugging state

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

All relationship types are uppercase. Key ones:

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

## Tagging Conventions

- Use lowercase, hyphenated tags: `api-design`, `error-handling`
- 2-5 tags per memory is ideal
- Include the module/area: `auth`, `database`, `cli`

## Session Workflow

1. **Start of session**: Run `recall --query "recent work" --limit 5` to load recent context
2. **During work**: Store memories as you make decisions or learn patterns
3. **End of session**: Store a summary memory with type `conversation`

## Backend Configuration

Set `MEMORY_BACKEND` environment variable:
- `falkordblite` (default) - embedded graph DB, no server needed
- `sqlite` - zero-dependency fallback using Bun's built-in SQLite
- `cloud` - remote API (requires `MEMORYGRAPH_API_KEY`)

Additional env vars:
- `MEMORY_SQLITE_PATH` - SQLite database path
- `MEMORY_FALKORDBLITE_PATH` - FalkorDBLite database path
- `MEMORYGRAPH_API_KEY` - Cloud API key
- `MEMORYGRAPH_API_URL` - Cloud API URL

## Import / Migration

```bash
# Import from JSON export
bun run ts/src/index.ts import --input backup.json --skip-duplicates

# Migrate between backends
bun run ts/src/index.ts migrate \
  --source sqlite --source-path ./local.db \
  --target falkordblite --target-path ./graph.falkor \
  --verify --rollback-on-failure
```
