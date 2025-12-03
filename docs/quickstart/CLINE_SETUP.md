# MemoryGraph Setup for Cline

Get persistent memory working with Cline (formerly Claude Dev) in VS Code.

## Prerequisites

- **Cline extension** installed from [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev)
- API key configured (Anthropic, OpenRouter, or other provider)
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

### 2. Configure Cline

1. Open VS Code
2. Click the Cline icon in the sidebar
3. Click the **gear icon** (settings) at the top
4. Scroll to **MCP Servers** section
5. Click **Edit MCP Settings**

This opens `cline_mcp_settings.json`. Add MemoryGraph:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": [],
      "disabled": false
    }
  }
}
```

### 3. Restart Cline

Click the refresh button in Cline's sidebar or reload VS Code.

### 4. Verify Connection

In Cline's chat, ask:

```
What MCP tools do you have available for memory?
```

You should see MemoryGraph tools listed.

## First Memory

Store a memory:

```
Store this for later: The auth service uses JWT with 24-hour expiry
```

Retrieve it:

```
What token expiry does the auth service use?
```

## Configuration Options

### Extended Mode

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended"],
      "disabled": false
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
      "args": [],
      "env": {
        "MEMORY_SQLITE_PATH": "/path/to/memory.db"
      },
      "disabled": false
    }
  }
}
```

### Full Path (Recommended)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/yourname/.local/bin/memorygraph",
      "args": [],
      "disabled": false
    }
  }
}
```

Find your path: `which memorygraph`

## Configuration File Location

Cline stores MCP settings at:
- **macOS**: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Linux**: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
- **Windows**: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

Or access via Cline settings UI (recommended).

## Troubleshooting

### MCP Server Not Connecting

1. **Check the MCP Servers section** in Cline settings
2. **Look for status indicator** next to memorygraph
3. **Click the server name** to see error details

### Server Shows as Disabled

```json
{
  "memorygraph": {
    "disabled": false  // Ensure this is false
  }
}
```

### Command Not Found

1. **Verify installation**:
   ```bash
   which memorygraph
   memorygraph --version
   ```

2. **Use full path**:
   ```json
   {
     "command": "/Users/yourname/.local/bin/memorygraph"
   }
   ```

3. **Ensure pipx bin is in PATH**:
   ```bash
   pipx ensurepath
   # Restart terminal and VS Code
   ```

### View Server Logs

1. Open VS Code Output panel (`Cmd/Ctrl + Shift + U`)
2. Select "Cline" from the dropdown
3. Look for MCP-related messages

### Test Server Manually

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph
```

You should see a JSON response.

## Tips for Cline Users

1. **Leverage autonomous mode** - Cline can use memory tools automatically during tasks
2. **Store decisions** - Have Cline remember architectural decisions
3. **Track solutions** - Store what worked when fixing bugs
4. **Project context** - Build up knowledge about your codebase

## Recommended: Memory Protocol

Add this to `.clinerules` or your project's rules file for automatic memory usage:

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
- **Project-specific**: `.clinerules` in project root
- **Global**: Cline Settings > Custom Instructions

## Cline-Specific Features

Cline is an autonomous coding agent. MemoryGraph enhances this by:

- **Persisting task context** across sessions
- **Remembering past decisions** for consistency
- **Tracking what worked** in previous autonomous runs
- **Building project knowledge** over time

### Autonomous Workflow Example

```
Task: Refactor the user service

Before you start, check if we have any memories about the user service
architecture or past refactoring decisions.

[Cline searches memories, finds relevant context]

Now proceed with the refactoring, and store any important decisions
you make for future reference.
```

## Using with OpenRouter

Cline is popular with OpenRouter for free/cheap models. MemoryGraph works with any model Cline supports:

1. Configure your OpenRouter API key in Cline
2. MCP tools work the same regardless of model
3. Memory persists across model switches

## Multiple MCP Servers

Cline supports multiple MCP servers:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended"]
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["/path/to/allowed/dir"]
    }
  }
}
```

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [Cline Documentation](https://github.com/cline/cline)

---

**Works with**: Cline (VS Code extension)
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
**Model support**: Any model supported by Cline
