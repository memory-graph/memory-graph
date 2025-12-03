# MemoryGraph Hooks for Claude Code Web

This directory contains hook files to auto-install MemoryGraph
in Claude Code Web (remote) environments.

## Quick Setup

Copy the `.claude` directory to your project root:

```bash
cp -r examples/claude-code-hooks/.claude /path/to/your/project/
```

Or use the helper script:

```bash
./examples/claude-code-hooks/copy-to-project.sh /path/to/your/project
```

## How It Works

1. When Claude Code Web starts, it runs SessionStart hooks
2. The hook detects it's in a remote environment (`CLAUDE_CODE_REMOTE=true`)
3. MemoryGraph is installed via pip and added as an MCP server
4. Your AI assistant now has memory!

## Cloud Persistence (Optional)

By default, memories in remote environments are ephemeral (lost when session ends).

For persistent storage, add these environment variables in Claude Code Web settings:

```env
MEMORYGRAPH_API_KEY=your-api-key    # Get from memorygraph.dev (coming soon)
```

Or use your own Turso database:

```env
MEMORYGRAPH_TURSO_URL=libsql://your-db.turso.io
MEMORYGRAPH_TURSO_TOKEN=your-token
```

## Local vs Remote Behavior

| Environment | Behavior |
|-------------|----------|
| Local CLI | Hook exits early. Install manually with `pip install memorygraphMCP` |
| Remote (no cloud key) | Auto-installs. Ephemeral SQLite storage. |
| Remote (with cloud key) | Auto-installs. Persistent cloud storage. |

## Files

- `.claude/settings.json` - Hook configuration
- `.claude/hooks/install-memorygraph.sh` - Installation script
- `.claude/hooks/install-memorygraph-minimal.sh` - Minimal variant

## Troubleshooting

**Hook not running:**
- Ensure `.claude/` is in your project root (not a subdirectory)
- Check that `install-memorygraph.sh` is executable

**MCP server not available:**
- Restart Claude Code after hook runs
- Check hook output in session logs

**Memories not persisting:**
- Set `MEMORYGRAPH_API_KEY` or `MEMORYGRAPH_TURSO_URL` for persistence
- Without cloud config, remote memories are lost on session end

## See Also

- [Full Documentation](../../docs/claude-code-web.md)
- [Main README](../../README.md)
