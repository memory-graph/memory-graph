# MemoryGraph Setup for VS Code with GitHub Copilot

Get persistent memory working with GitHub Copilot in VS Code.

## Prerequisites

- **VS Code 1.102+** (MCP support is GA as of this version)
- **GitHub Copilot subscription** (Individual, Business, or Enterprise)
- **GitHub Copilot Chat extension** installed
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

### 2. Configure VS Code

Create `.vscode/mcp.json` in your workspace root:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": []
    }
  }
}
```

For user-level configuration (all workspaces), create the file at:
- **macOS/Linux**: `~/.vscode/mcp.json`
- **Windows**: `%USERPROFILE%\.vscode\mcp.json`

### 3. Start the MCP Server

1. Open VS Code
2. Open the Command Palette (`Cmd/Ctrl + Shift + P`)
3. Run: **MCP: List Servers**
4. Find `memorygraph` and click **Start**

Alternatively, MCP servers auto-start when you open Copilot Chat in agent mode.

### 4. Use Agent Mode

MCP tools are available in Copilot's **Agent mode**:

1. Open Copilot Chat (`Cmd/Ctrl + Shift + I` or click the Copilot icon)
2. Click **Agent** at the top of the chat panel
3. Or type `@workspace` to use agent capabilities

### 5. Verify Connection

In Copilot Chat (Agent mode), ask:

```
What MCP tools do you have available?
```

You should see MemoryGraph tools like `store_memory`, `search_memories`.

## First Memory

Store a memory:

```
@workspace Store this for later: The API rate limit is 100 requests per minute
```

Retrieve it later:

```
@workspace What's the API rate limit for this project?
```

## Configuration Options

### Extended Mode

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

### With Environment Variables

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended"],
      "env": {
        "MEMORY_SQLITE_PATH": "${workspaceFolder}/.vscode/memory.db"
      }
    }
  }
}
```

### Full Path (Recommended for Reliability)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/yourname/.local/bin/memorygraph",
      "args": []
    }
  }
}
```

Find your path with: `which memorygraph`

## Enterprise Considerations

### Policy Requirements

GitHub Copilot Enterprise admins can control MCP access via policies:

- **Organization policies** may restrict which MCP servers can be used
- **Allowed servers list** may need to include `memorygraph`
- Check with your admin if MCP servers aren't working

### Security Notes

- MemoryGraph stores data locally by default (`~/.memorygraph/memory.db`)
- No data is sent to external servers in default configuration
- For enterprise, consider project-scoped databases to isolate data

### Audit and Compliance

- MCP tool calls are logged by VS Code
- View logs: **Help > Toggle Developer Tools > Console**
- Memory data can be exported for compliance review

## Troubleshooting

### MCP Servers Not Available

1. **Check VS Code version**: Must be 1.102 or later
   ```
   Help > About > Version
   ```

2. **Verify Copilot Chat extension**: Ensure it's installed and enabled

3. **Check MCP configuration**:
   - Command Palette > **MCP: List Servers**
   - Verify memorygraph is listed

### Server Won't Start

1. **Test memorygraph manually**:
   ```bash
   memorygraph --version
   memorygraph --show-config
   ```

2. **Check PATH**:
   ```bash
   which memorygraph
   ```

3. **Use full path** in configuration if command isn't found

### Tools Not Appearing in Chat

1. **Must use Agent mode** - Regular chat doesn't have MCP access
2. **Restart the MCP server**: Command Palette > **MCP: Restart Server**
3. **Reload VS Code window**: Command Palette > **Developer: Reload Window**

### Permission Errors

On macOS:
- System Preferences > Security & Privacy > Privacy > Full Disk Access
- Add VS Code to the list

### View Server Logs

1. Command Palette > **MCP: Show Server Logs**
2. Select `memorygraph`
3. Check for error messages

## Tips for VS Code + Copilot Users

1. **Use `@workspace` prefix** for memory operations in chat
2. **Store coding conventions** - Remember project-specific patterns
3. **Track debugging solutions** - Store what fixed tricky bugs
4. **Project-scoped memory** - Use `.vscode/mcp.json` per repository

## Limitations

- **128 tools max** per chat request (MemoryGraph core mode has 9, extended has 11)
- **Agent mode required** for MCP access
- **Workspace trust** must be enabled for MCP servers to run

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [VS Code MCP Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

---

**Works with**: VS Code 1.102+ with GitHub Copilot
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
**Requirements**: GitHub Copilot subscription, Agent mode
