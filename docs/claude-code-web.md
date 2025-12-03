# Using MemoryGraph with Claude Code Web

Claude Code Web runs in ephemeral cloud containers. This guide explains
how to use MemoryGraph in these environments.

## How It Works

Claude Code supports [project hooks](https://code.claude.com/docs/en/hooks)
that run on session start. MemoryGraph provides hook files that:

1. Detect remote environment via `CLAUDE_CODE_REMOTE` env var
2. Install MemoryGraph via pip
3. Register the MCP server
4. Configure cloud backend if API key is present

## Installation

### Option 1: Copy Hook Files (Recommended)

Copy the provided hooks to your project:

```bash
# Clone or download memorygraph
git clone https://github.com/gregorydickson/memory-graph.git

# Copy hooks to your project
cp -r memory-graph/examples/claude-code-hooks/.claude /path/to/your/project/

# Commit to version control
cd /path/to/your/project
git add .claude/
git commit -m "Add MemoryGraph hooks for Claude Code Web"
git push
```

### Option 2: Manual Setup

Create these files in your project:

**`.claude/settings.json`:**
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/install-memorygraph.sh"
          }
        ]
      }
    ]
  }
}
```

**`.claude/hooks/install-memorygraph.sh`:**
```bash
#!/bin/bash
[ "$CLAUDE_CODE_REMOTE" != "true" ] && exit 0
pip install --quiet memorygraphMCP
claude mcp add memorygraph 2>/dev/null || true
echo "[memorygraph] Ready"
```

Make the script executable:
```bash
chmod +x .claude/hooks/install-memorygraph.sh
```

## Persistent Storage

By default, memories in Claude Code Web are **ephemeral**—they're lost when
the session ends. For persistent storage, configure a cloud backend.

### Option A: MemoryGraph Cloud (Coming Soon)

1. Sign up at [memorygraph.dev](https://memorygraph.dev)
2. Get your API key
3. Add to Claude Code Web environment variables:
   - `MEMORYGRAPH_API_KEY`: Your API key

### Option B: Bring Your Own Turso Database

[Turso](https://turso.tech) offers free SQLite-compatible cloud databases.

1. Create a Turso account and database
2. Get your database URL and auth token
3. Add to Claude Code Web environment variables:
   - `MEMORYGRAPH_TURSO_URL`: `libsql://your-db-name.turso.io`
   - `MEMORYGRAPH_TURSO_TOKEN`: Your auth token

### Setting Environment Variables

In Claude Code Web:
1. Click the environment dropdown (shows "Default")
2. Click "New cloud environment" or edit existing
3. Add variables in the "Environment variables" section
4. Click "Create environment" or "Save"

## Behavior Summary

| Environment | Detection | Storage | Persistence |
|-------------|-----------|---------|-------------|
| Local CLI | `CLAUDE_CODE_REMOTE` not set | Local SQLite | ✅ Persistent |
| Remote (no config) | `CLAUDE_CODE_REMOTE=true` | Local SQLite | ❌ Ephemeral |
| Remote + API key | `CLAUDE_CODE_REMOTE=true` | Cloud API | ✅ Persistent |
| Remote + Turso | `CLAUDE_CODE_REMOTE=true` | Turso DB | ✅ Persistent |

## Troubleshooting

### Hook not executing

- Verify `.claude/settings.json` is valid JSON
- Check that `.claude/hooks/install-memorygraph.sh` is executable
- Ensure files are committed and pushed to your repository

### MCP server not available after install

- The MCP server registers after the hook runs
- Try sending a message to trigger Claude to reload tools
- Check session logs for hook output

### Memories not persisting between sessions

- This is expected without cloud configuration
- Set `MEMORYGRAPH_API_KEY` or Turso credentials for persistence
- Verify environment variables are set in the correct cloud environment

### Permission denied errors

- Ensure the hook script has execute permissions: `chmod +x .claude/hooks/install-memorygraph.sh`
- Commit the executable bit: `git update-index --chmod=+x .claude/hooks/install-memorygraph.sh`

## Local Development

The hooks are designed to be safe for local use:

- On local CLI, hooks exit immediately (no-op)
- Local installation uses the normal flow: `pip install memorygraphMCP && claude mcp add memorygraph`
- You can test hooks locally by setting `CLAUDE_CODE_REMOTE=true`

## Security Considerations

- Hook scripts run with the same permissions as Claude Code
- The installation script only installs from PyPI (trusted source)
- Cloud credentials are stored in Claude Code's secure environment variable storage
- No credentials are logged or exposed in hook output

## Advanced: Using Turso for Multi-Device Sync

Turso supports embedded replicas, allowing you to sync memories across multiple devices:

1. Create a Turso database (one per user/team)
2. Configure all devices with the same Turso credentials
3. Each device maintains a local copy that syncs automatically

**Benefits:**
- Fast local access (reads from local replica)
- Automatic background sync
- Works offline, syncs when connected
- Share memories across your laptop, desktop, and cloud environments

**Setup:**
```env
# Set on all devices
MEMORY_BACKEND=turso
MEMORYGRAPH_TURSO_URL=libsql://shared-memory.turso.io
MEMORYGRAPH_TURSO_TOKEN=your-token
```

## See Also

- [Turso Quickstart](https://docs.turso.tech/quickstart)
- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [MemoryGraph Main README](../README.md)
