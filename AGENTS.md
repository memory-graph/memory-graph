# AGENTS.md - CLI Reference

## Install
```bash
cd ts && bun install && bun link  # global `memorygraph` command
```

## Commands

| Command | Args |
|---------|------|
| `store` | `--type --title --content --tags --importance --summary` |
| `get` | `<id>` |
| `update` | `<id> --title --content --tags --importance` |
| `delete` | `<id>` |
| `search` | `--query --tags --types --limit --offset --min-importance` |
| `recall` | `--query --limit` |
| `link` | `<from-id> <to-id> <TYPE> --strength --confidence` |
| `related` | `<id> --types --max-depth` |
| `context-search` | `<id> --types --min-strength --context-query` |
| `contextual-search` | `<id> --query --max-depth` |
| `entities` | `<id> [--link]` |
| `patterns` | `--query` |
| `context` | `--query --project` |
| `stats` | |
| `activity` | `--days` |
| `visualize` | `--center --depth --max-nodes --json` |
| `similarity` | `<id> --top-k --min-similarity` |
| `learning` | `--topic --max-paths` |
| `gaps` | `--project` |
| `briefing` | `--path --verbosity` |
| `predict` | `--query` |
| `warn` | `--context` |
| `outcome` | `<id> --description --success` |
| `capture` | `--task --goals` |
| `analyze-project` | `--path` |
| `workflow` | `--action track\|suggest --type --data` |
| `as-of` | `<id> <timestamp> --types` |
| `history` | `<id> --types` |
| `changes` | `<timestamp>` |
| `export` | `--format json\|markdown --output` |
| `import` | `--input --skip-duplicates` |
| `migrate` | `--to --to-path --to-uri --dry-run --no-verify` |
| `health` | `--timeout --json` |
| `config` | |

## Types
`task` `code_pattern` `problem` `solution` `project` `technology` `error` `fix` `command` `file_context` `workflow` `general` `conversation`

## Relationships
`SOLVES` `CAUSES` `BUILDS_ON` `REPLACES` `IMPROVES` `REQUIRES` `CONTRADICTS` `CONFIRMS` `RELATED_TO` `DEPENDS_ON`

## Backend
`MEMORY_BACKEND=falkordblite` (default) | `sqlite` | `falkordb` | `memgraph` | `cloud`
