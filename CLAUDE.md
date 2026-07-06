# CLAUDE.md - Memory Graph Directives

`memorygraph` CLI is installed globally. Use it for persistent memory across sessions.

## Session Workflow
1. **Start**: `memorygraph recall --query "<task>" --limit 10` and `memorygraph briefing`
2. **During**: Store on decisions, fixes, patterns. Link related memories.
3. **End**: `memorygraph store --type conversation --title "Session: <topic>" --content "<summary>" --tags "<tags>"`

## Commands
```bash
memorygraph store --type <type> --title "<title>" --content "<content>" --tags "<tags>" --importance <0-1>
memorygraph recall --query "<keywords>" --limit 10
memorygraph search --query "<text>" --tags <tags> --limit 10
memorygraph get <id>
memorygraph link <from-id> <to-id> <RELATIONSHIP_TYPE> --strength <0-1>
memorygraph related <id> --max-depth 2
memorygraph briefing
memorygraph stats
memorygraph export --output backup.json
```

## When to Store
- Architectural decision → type: `solution`, tags: `architecture`
- Bug fix → type: `problem` + `solution`, link with `SOLVES`
- Project pattern → type: `code_pattern`
- Error encountered → type: `error`
- End of session → type: `conversation`

Do NOT store: trivial changes, info already in code/docs, transient debugging state.

## Types
`task` `code_pattern` `problem` `solution` `project` `technology` `error` `fix` `command` `file_context` `workflow` `general` `conversation`

## Relationships (uppercase)
`SOLVES` `CAUSES` `BUILDS_ON` `REPLACES` `IMPROVES` `REQUIRES` `CONTRADICTS` `CONFIRMS` `RELATED_TO` `DEPENDS_ON`

## Tags
Lowercase, hyphenated, 2-5 per memory. Include component: `auth`, `database`, `cli`.

## Backend
`MEMORY_BACKEND=falkordblite` (default) | `sqlite` | `falkordb` | `memgraph` | `cloud`
