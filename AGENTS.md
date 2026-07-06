# AGENTS.md - AI Agent CLI Usage Guide

## Installation

```bash
cd ts && bun install
bun link  # Makes `memorygraph` available globally
```

## CLI Entry Point

After `bun link`, use from any directory:
```bash
memorygraph <command> [options]
```

Within this repo (without linking):
```bash
bun run ts/src/cli.ts <command> [options]
```

## Available Commands

### Memory Operations

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `store` | Create a new memory | `--type`, `--title`, `--content`, `--tags`, `--importance`, `--summary` |
| `get` | Retrieve a memory by ID | `--id` |
| `update` | Update an existing memory | `--id`, `--title`, `--content`, `--tags`, `--importance` |
| `delete` | Delete a memory | `--id` |
| `search` | Full-text search | `--query`, `--limit`, `--offset`, `--type`, `--min-importance` |
| `recall` | Get recent memories | `--limit`, `--offset` |

### Relationship Operations

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `link` | Create a relationship | `--from`, `--to`, `--type`, `--strength`, `--confidence` |
| `related` | Get related memories | `--id`, `--max-depth`, `--types` |

### Analytics

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `stats` | Database statistics | none |
| `activity` | Recent activity timeline | `--days` |

### Temporal Queries

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `as-of` | Query state at a past time | `--id`, `--timestamp` |
| `history` | Relationship history | `--id` |
| `changes` | What changed since a time | `--since` |

### Data Management

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `export` | Export to JSON or Markdown | `--output`, `--format` |
| `import` | Import from JSON | `--input`, `--skip-duplicates` |
| `migrate` | Migrate between backends | `--source`, `--target`, `--verify` |
| `health` | Health check | `--timeout` |
| `config` | Show configuration | none |

## Backend Selection

Set `MEMORY_BACKEND` env var or use defaults:
- **falkordblite** (default): Embedded graph DB, no server needed
- **sqlite**: Zero-dependency fallback
- **cloud**: Remote API (needs `MEMORYGRAPH_API_KEY` and `MEMORYGRAPH_API_URL`)

Additional env vars:
- `MEMORY_SQLITE_PATH` - SQLite database path
- `MEMORY_FALKORDBLITE_PATH` - FalkorDBLite database path

## Agent Workflow

### Starting a Task
```bash
# Recall recent memories
memorygraph recall --query "recent work" --limit 10

# Get a session briefing
memorygraph briefing

# Search for relevant context
memorygraph search --query "authentication" --limit 5
```

### During Work
```bash
# Store a decision
memorygraph store \
  --type solution \
  --title "Use JWT for auth" \
  --content "JWT tokens with 24h expiry, refresh token rotation" \
  --tags "auth,security,api" \
  --importance 0.8

# Link it to a prior decision
memorygraph link <new-id> <prior-id> BUILDS_ON --strength 0.9
```

### Ending a Session
```bash
# Store session summary
memorygraph store \
  --type conversation \
  --title "Session: auth refactor" \
  --content "Refactored auth middleware, added JWT, fixed token refresh bug" \
  --tags "auth,session-summary"

# Export backup
memorygraph export --output session-backup.json
```

## Tips

- Use `--importance` (0.0-1.0) to rank memories; higher = more important
- Use `--tags` (comma-separated) for categorization
- Link memories with `link` to create a knowledge chain
- Use `as-of` to understand past state when debugging
- Run `health` to verify backend connectivity
- Use `briefing` at the start of each session for a quick overview
- Use `entities` to extract and link entities from a memory's content
- Use `predict` to get predictions about what might be needed next
