# Migrating from claude-code-memory to MemoryGraph

## Overview

Version 2.0.0 represents a major rebranding from `claude-code-memory` to `MemoryGraph` to better reflect the project's universal MCP compatibility. While originally built for Claude Code, MemoryGraph works with any MCP-enabled coding agent (Cursor, Continue, etc.).

This is a **breaking change** that requires migration steps for existing users.

---

## What Changed

### Package & CLI Changes

| Old | New |
|-----|-----|
| **Package Name** | `claude-code-memory` | `memorygraph` |
| **CLI Command** | `claude-memory` | `memorygraph` |
| **Python Module** | `claude_memory` | `memorygraph` |
| **Default DB Path** | `~/.claude-memory/memory.db` | `~/.memorygraph/memory.db` |

### Why the Change?

- **Better Branding**: MemoryGraph is more descriptive and not Claude-specific
- **Universal Compatibility**: Emphasizes MCP standard compatibility
- **Broader Audience**: Works with any MCP-enabled coding agent

### What Stayed the Same?

- All features and functionality
- Environment variables (`MEMORY_*` prefix)
- Database schema and compatibility
- All 44 MCP tools
- Backend support (SQLite, Neo4j, Memgraph)

---

## Migration Steps

### For Existing Users

If you're upgrading from `claude-code-memory` v1.x to `memorygraph` v2.0:

#### 1. Uninstall Old Package

```bash
pip uninstall claude-code-memory
```

Or with `uv`:
```bash
uv pip uninstall claude-code-memory
```

#### 2. Install New Package

```bash
pip install memorygraphMCP
```

Or with `uv`:
```bash
uv pip install memorygraphMCP
```

#### 3. Update MCP Configuration

Edit your MCP client configuration:

**For Claude Code** (`.claude/mcp.json` or `~/.config/claude/mcp_settings.json`):

**Before:**
```json
{
  "mcpServers": {
    "claude-memory": {
      "command": "claude-memory"
    }
  }
}
```

**After:**
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

**For other MCP clients**: Update your server configuration following the same pattern.

#### 4. Migrate Database (Choose One Option)

You have two options for handling your existing data:

**Option A: Move Database to New Location (Recommended)**

```bash
# Create new directory
mkdir -p ~/.memorygraph

# Move your existing database
mv ~/.claude-memory/memory.db ~/.memorygraph/memory.db

# Verify
ls -lh ~/.memorygraph/memory.db
```

**Option B: Keep Database at Old Location**

Use the `MEMORY_SQLITE_PATH` environment variable to point to your old database:

Update your MCP configuration:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "env": {
        "MEMORY_SQLITE_PATH": "/Users/yourname/.claude-memory/memory.db"
      }
    }
  }
}
```

#### 5. Restart Your Coding Agent

- **Claude Code**: Restart the application
- **Other clients**: Follow their restart procedure

#### 6. Verify Migration

Test that your memories are accessible:

```bash
# Check configuration
memorygraph --show-config

# Verify version
memorygraph --version
# Should show: memorygraph 2.0.0
```

In your coding agent, try:
- "Show me all my memories"
- "What patterns have we stored?"

---

## Docker Users

### Update Docker Compose

**Before:**
```yaml
services:
  claude-memory:
    build:
      context: .
    container_name: claude-memory-sqlite
```

**After:**
```yaml
services:
  memorygraph:
    build:
      context: .
    container_name: memorygraph-sqlite
```

### Volume Migration

```bash
# Stop containers
docker-compose down

# Update docker-compose.yml (see above)

# Rebuild
docker-compose build

# Start with new configuration
docker-compose up -d
```

Your volume data will persist through the rename if you keep the same volume name or copy data between volumes.

---

## Environment Variables

No changes needed! All environment variables retain the `MEMORY_*` prefix:

- `MEMORY_BACKEND` (sqlite|neo4j|memgraph|auto)
- `MEMORY_TOOL_PROFILE` (lite|standard|full)
- `MEMORY_SQLITE_PATH` (SQLite database path)
- `MEMORY_LOG_LEVEL` (DEBUG|INFO|WARNING|ERROR)
- `MEMORY_NEO4J_URI`, `MEMORY_NEO4J_USER`, `MEMORY_NEO4J_PASSWORD`
- `MEMORY_MEMGRAPH_URI`

---

## Troubleshooting

### "command not found: memorygraph"

**Cause**: Old package still installed or PATH not updated

**Fix**:
```bash
# Verify old package is uninstalled
pip list | grep claude-code-memory

# If found, uninstall
pip uninstall claude-code-memory

# Reinstall new package
pip install memorygraphMCP

# Verify
which memorygraph
memorygraph --version
```

### "Database not found" or Empty Memories

**Cause**: Database not migrated to new location

**Fix**:
```bash
# Check old location
ls -lh ~/.claude-memory/memory.db

# If exists, move it
mkdir -p ~/.memorygraph
mv ~/.claude-memory/memory.db ~/.memorygraph/memory.db

# Or use MEMORY_SQLITE_PATH env var (see Option B above)
```

### MCP Server Not Loading

**Cause**: MCP configuration not updated

**Fix**:
1. Check `.claude/mcp.json` uses `"memorygraph"` as command
2. Restart Claude Code completely
3. Check server status: `memorygraph --show-config`

---

## For Developers

### Import Changes

If you were importing the library in custom code:

**Before:**
```python
from claude_memory.database import MemoryDatabase
from claude_memory.models import Memory
```

**After:**
```python
from memorygraph.database import MemoryDatabase
from memorygraph.models import Memory
```

### Module Changes

**Before:**
```bash
python -m claude_memory
```

**After:**
```bash
python -m memorygraph
```

---

## Getting Help

### Still Having Issues?

1. **Check Configuration**: Run `memorygraph --show-config`
2. **Check Logs**: Set `MEMORY_LOG_LEVEL=DEBUG` for verbose output
3. **GitHub Issues**: [github.com/gregorydickson/memory-graph/issues](https://github.com/gregorydickson/memory-graph/issues)
4. **Documentation**: See [README.md](README.md) and [docs/](docs/)

### Report Migration Problems

If you encounter migration issues, please report them with:
- Old version number (check `pip show claude-code-memory`)
- New version number (check `memorygraph --version`)
- Your MCP client (Claude Code, Cursor, etc.)
- Steps that failed
- Error messages

---

## Why This Change?

The rename from `claude-code-memory` to `MemoryGraph` better reflects the project's goals:

1. **Universal Compatibility**: Works with any MCP client, not just Claude Code
2. **Better Naming**: "MemoryGraph" describes what it does (graph-based memory)
3. **Professional Branding**: More suitable for broader adoption
4. **MCP Standard**: Emphasizes adherence to the Model Context Protocol

**Note**: The project was originally built for Claude Code and is optimized for that workflow, but the MCP standard enables it to work with any compatible client.

---

## Timeline

- **v1.0.0** (Nov 2024): Released as `claude-code-memory`
- **v2.0.0** (Nov 2024): Rebranded to `memorygraph`

The old `claude-code-memory` package on PyPI will remain available but deprecated. All future development happens under `memorygraph`.

---

## Questions?

See the main [README.md](README.md) for updated documentation, or join the discussion on GitHub.
