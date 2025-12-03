# MemoryGraph Setup for Windsurf

Get persistent memory working in Windsurf in under 2 minutes.

## Prerequisites

- Windsurf IDE (latest version)
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

### 2. Configure Windsurf

**Option A: Via Settings UI**

1. Open Windsurf Settings (`Cmd/Ctrl + ,`)
2. Search for "MCP" or navigate to **Extensions > MCP Servers**
3. Click **Add MCP Server**
4. Configure:
   - Name: `memorygraph`
   - Command: `memorygraph`
   - Transport: `stdio`

**Option B: Via Configuration File**

Windsurf uses a similar configuration format to other MCP clients. Create or edit your MCP configuration:

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

Location varies by OS:
- **macOS**: `~/Library/Application Support/Windsurf/mcp.json`
- **Linux**: `~/.config/Windsurf/mcp.json`
- **Windows**: `%APPDATA%\Windsurf\mcp.json`

### 3. Restart Windsurf

Close and reopen Windsurf to load the MCP server.

### 4. Verify Connection

In Windsurf's AI chat, ask:

```
What memory tools do you have available?
```

You should see MemoryGraph tools listed.

## First Memory

Store your first memory:

```
Store this for later: Use pnpm instead of npm for this monorepo
```

Retrieve it later:

```
What package manager should I use for this project?
```

## Configuration Options

### Extended Mode (Pattern Recognition)

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

### Project-Specific Memory

Create `.windsurf/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "env": {
        "MEMORY_SQLITE_PATH": "./.windsurf/memory.db"
      }
    }
  }
}
```

## Troubleshooting

### Server Not Connecting

1. Check that memorygraph is installed and in PATH:
   ```bash
   which memorygraph
   memorygraph --version
   ```

2. If not found, ensure pipx bin is in your PATH:
   ```bash
   pipx ensurepath
   # Restart terminal
   ```

3. Use full path in configuration:
   ```json
   {
     "command": "/Users/yourname/.local/bin/memorygraph"
   }
   ```

### MCP Tools Not Appearing

1. Verify MCP server status in Windsurf settings
2. Check for error messages in the server logs
3. Restart Windsurf completely (not just reload)

### Test Server Manually

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph
```

You should see a JSON response with capabilities.

### SSE Transport (If Required)

If Windsurf requires SSE transport instead of stdio, you may need to run MemoryGraph with an SSE wrapper. Check Windsurf documentation for current requirements.

## Tips for Windsurf Users

1. **Leverage Windsurf's features** - Combine MemoryGraph with Windsurf's code understanding
2. **Store architectural decisions** - Remember why you made certain choices
3. **Track what works** - Store successful patterns for future reference
4. **Query before coding** - Check if you've solved similar problems

## Recommended: Memory Protocol

Add this to `.windsurfrules` or your project's rules file for automatic memory usage:

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
- **Project-specific**: `.windsurfrules` in project root
- **Global**: Windsurf Settings > AI Rules

## Windsurf-Specific Features

Windsurf has a rich feature set. MemoryGraph complements these by:

- **Persisting context** - Remember discussions across sessions
- **Tracking solutions** - Know what worked in past projects
- **Building relationships** - Connect problems to their solutions

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**Works with**: Windsurf (all versions with MCP support)
**Transport**: stdio (SSE may be supported)
**Profiles**: core (9 tools), extended (11 tools)
