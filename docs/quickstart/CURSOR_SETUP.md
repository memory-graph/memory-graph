# MemoryGraph Setup for Cursor AI

Get persistent memory working in Cursor in under 2 minutes.

## Prerequisites

- Cursor IDE (latest version)
- Python 3.10+
- pipx installed (`pip install --user pipx && pipx ensurepath`)

## Choose Your Backend

MemoryGraph supports two backend options:

| Feature | Local (SQLite) | Cloud |
|---------|---------------|-------|
| **Setup** | Zero-config | API key required |
| **Data Location** | `~/.memorygraph/` | memorygraph.dev |
| **Multi-device** | No | Yes |
| **Team sharing** | No | Yes |
| **Offline** | Yes | No |
| **Cost** | Free | Free tier available |

**New users**: We recommend starting with **Cloud** for multi-device sync, or **Local** for single-machine use.

---

## Quick Start (Local Backend)

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

---

## Quick Start (Cloud Backend)

Cloud backend syncs memories across all your devices and enables team collaboration.

### 1. Get Your API Key

1. Sign up at [app.memorygraph.dev](https://app.memorygraph.dev)
2. Copy your API key (starts with `mg_`)

### 2. Install MemoryGraph

```bash
pipx install memorygraphMCP
```

### 3. Configure Cursor with Cloud Backend

Create or edit `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "cloud"],
      "env": {
        "MEMORYGRAPH_API_KEY": "mg_your_api_key_here"
      }
    }
  }
}
```

For global configuration (all projects), create `~/.cursor/mcp.json`.

### 4. Restart Cursor and Verify

1. Close and reopen Cursor
2. Switch to **Agent** mode
3. Ask: "What memory tools do you have available?"

---

## Migrating from Local to Cloud

Already using local SQLite and want to switch to cloud?

### Step 1: Export Local Memories

```bash
# Export all memories to JSON
memorygraph export --output memories-backup.json
```

### Step 2: Import to Cloud

```bash
# Set your cloud API key
export MEMORYGRAPH_API_KEY=mg_your_key_here

# Import to cloud backend
memorygraph import --backend cloud --input memories-backup.json
```

### Step 3: Update Cursor Configuration

Update your `.cursor/mcp.json` to use cloud backend:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "cloud"],
      "env": {
        "MEMORYGRAPH_API_KEY": "mg_your_api_key_here"
      }
    }
  }
}
```

### Step 4: Restart Cursor

Close and reopen Cursor to apply the new configuration.

See [CLOUD_BACKEND.md](../CLOUD_BACKEND.md) for detailed migration options and troubleshooting.

---

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

## Recommended: Memory Protocol

Add this to `.cursorrules` or your project's rules file for automatic memory usage:

```markdown
## Memory Protocol

### REQUIRED: Before Starting Work
You MUST use `recall_memories` before any task. Query by project, tech, or task type.

### REQUIRED: Automatic Storage Triggers
Store memories on ANY of:
- **Git commit** → what was fixed/added
- **Bug fix** → problem + solution
- **Version release** → summarize changes
- **Architecture decision** → choice + rationale
- **Pattern discovered** → reusable approach

### Timing Mode (default: on-commit)
`memory_mode: immediate | on-commit | session-end`

### Memory Fields
- **Type**: solution | problem | code_pattern | fix | error | workflow
- **Title**: Specific, searchable (not generic)
- **Content**: Accomplishment, decisions, patterns
- **Tags**: project, tech, category (REQUIRED)
- **Importance**: 0.8+ critical, 0.5-0.7 standard, 0.3-0.4 minor
- **Relationships**: Link related memories when they exist

Do NOT wait to be asked. Memory storage is automatic.
```

**File locations:**
- **Project-specific**: `.cursorrules` in project root
- **Global**: `~/.cursor/rules` or Cursor Settings

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**Works with**: Cursor AI (all versions with MCP support)
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
