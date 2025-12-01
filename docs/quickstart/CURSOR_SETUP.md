# MemoryGraph Setup for Cursor AI

Get persistent memory working in Cursor in under 2 minutes.

## Prerequisites

- Cursor IDE (latest version)
- Python 3.10+
- pipx installed (`pip install --user pipx && pipx ensurepath`)

## Quick Start

### 1. Install MemoryGraph

```bash
pipx install memorygraphMCP
```

Verify installation:
```bash
memorygraph --version
```

### 2. Configure Cursor

**Option A: Via Settings UI**

1. Open Cursor Settings (`Cmd/Ctrl + ,`)
2. Navigate to **Features > MCP**
3. Click **Add Server**
4. Enter:
   - Name: `memorygraph`
   - Command: `memorygraph`

**Option B: Via Configuration File**

Create or edit `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": [],
      "env": {}
    }
  }
}
```

For global configuration (all projects), create `~/.cursor/mcp.json`.

### 3. Enable Agent Mode

MCP servers require Cursor's Agent mode:

1. Open Cursor Chat (`Cmd/Ctrl + L`)
2. Click the mode selector (bottom of chat)
3. Select **Agent** mode

### 4. Restart Cursor

Close and reopen Cursor to load the MCP server.

### 5. Verify Connection

In Cursor chat (Agent mode), ask:

```
What memory tools do you have available?
```

You should see MemoryGraph tools like `store_memory`, `search_memories`, etc.

## First Memory

Try storing your first memory:

```
Store this for later: This project uses TypeScript with strict mode enabled
```

Then retrieve it:

```
What do you know about this project's TypeScript setup?
```

## Configuration Options

### Extended Mode (More Tools)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended"]
    }
  }
}
```

### Custom Database Location

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "env": {
        "MEMORY_SQLITE_PATH": "/path/to/your/memory.db"
      }
    }
  }
}
```

### Extended Mode with Neo4j

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended", "--backend", "neo4j"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://localhost:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
```

## Troubleshooting

### Server Not Appearing

1. Ensure memorygraph is in your PATH:
   ```bash
   which memorygraph
   ```
2. If not found, run `pipx ensurepath` and restart your terminal
3. Try using the full path in config:
   ```json
   {
     "command": "/Users/yourname/.local/bin/memorygraph"
   }
   ```

### Agent Mode Required

MCP tools only work in Agent mode. If you don't see the tools:
- Switch from "Chat" or "Composer" to "Agent" mode
- The mode selector is at the bottom of the chat panel

### Tools Not Working

1. Check Cursor's MCP server status in Settings > Features > MCP
2. Look for error messages in the server status
3. Test the server manually:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph
   ```

### Permission Errors

On macOS, you may need to allow terminal access:
- System Preferences > Security & Privacy > Privacy > Full Disk Access
- Add Cursor to the list

## Tips for Cursor Users

1. **Use Agent mode for memory operations** - Regular chat mode doesn't have MCP access
2. **Store patterns as you discover them** - Ask Cursor to remember useful patterns
3. **Query before implementing** - Check if you've solved similar problems before
4. **Use project-scoped config** - Keep `.cursor/mcp.json` in your repo for team sharing

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**Works with**: Cursor AI (all versions with MCP support)
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
