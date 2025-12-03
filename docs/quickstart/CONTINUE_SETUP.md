# MemoryGraph Setup for Continue.dev

Get persistent memory working with Continue in VS Code or JetBrains IDEs.

## Prerequisites

- **Continue extension** installed ([VS Code](https://marketplace.visualstudio.com/items?itemName=Continue.continue) or [JetBrains](https://plugins.jetbrains.com/plugin/22707-continue))
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

### 2. Configure Continue

Continue supports MCP configuration in multiple formats.

**Option A: YAML Configuration (Recommended)**

Create `.continue/config.yaml` in your home directory or project:

```yaml
mcpServers:
  - name: memorygraph
    command: memorygraph
    args: []
```

**Option B: JSON Configuration**

Create `.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "memorygraph",
      "command": "memorygraph",
      "args": []
    }
  ]
}
```

**Option C: Copy from Other Clients**

Continue can use JSON configs from Claude Code, Cursor, or Cline. Copy your existing `mcp.json` to `.continue/mcpServers/memorygraph.json`:

```json
{
  "command": "memorygraph",
  "args": []
}
```

### 3. Enable Agent Mode

MCP servers only work in Continue's Agent mode:

1. Open Continue sidebar
2. Look for the mode selector
3. Switch to **Agent** mode (not Chat or Edit)

### 4. Restart Continue

Reload your IDE or restart the Continue extension to load MCP servers.

### 5. Verify Connection

In Continue (Agent mode), type:

```
@MCP What memory tools are available?
```

Or simply ask:

```
What tools do you have for storing memories?
```

## First Memory

Store a memory:

```
Store this for later: Always run tests before committing in this repo
```

Retrieve it:

```
What should I do before committing code?
```

## Configuration Options

### Extended Mode with More Tools

```yaml
mcpServers:
  - name: memorygraph
    command: memorygraph
    args:
      - "--profile"
      - "extended"
```

### Custom Database Path

```yaml
mcpServers:
  - name: memorygraph
    command: memorygraph
    env:
      MEMORY_SQLITE_PATH: "/path/to/memory.db"
```

### Full Path (Recommended)

```yaml
mcpServers:
  - name: memorygraph
    command: /Users/yourname/.local/bin/memorygraph
    args: []
```

Find your path: `which memorygraph`

### Project-Specific Configuration

Create `.continue/config.yaml` in your project root:

```yaml
mcpServers:
  - name: memorygraph
    command: memorygraph
    env:
      MEMORY_SQLITE_PATH: "./.continue/memory.db"
```

## Configuration Locations

Continue looks for configuration in this order:

1. **Project**: `.continue/config.yaml` in workspace
2. **User**: `~/.continue/config.yaml`
3. **MCP Servers Directory**: `~/.continue/mcpServers/*.json`

## Troubleshooting

### MCP Tools Not Available

1. **Verify Agent mode** - MCP only works in Agent mode, not Chat or Edit
2. **Check configuration syntax** - YAML is indent-sensitive
3. **Reload Continue** - Use the reload button or restart IDE

### Server Not Starting

1. **Test memorygraph directly**:
   ```bash
   memorygraph --version
   ```

2. **Check PATH**:
   ```bash
   which memorygraph
   ```

3. **Use full path** in configuration if needed

### View Logs

- **VS Code**: View > Output > Select "Continue" from dropdown
- **JetBrains**: View > Tool Windows > Continue > Logs tab

### Common Errors

**"Command not found"**
```yaml
# Use full path instead
mcpServers:
  - name: memorygraph
    command: /Users/yourname/.local/bin/memorygraph
```

**"Connection refused"**
- Ensure no other process is using the server
- Check if memorygraph is installed correctly

**"MCP protocol error"**
- Update Continue to latest version
- Verify memorygraph version: `memorygraph --version`

## Tips for Continue Users

1. **Use `@MCP` mention** to explicitly invoke MCP tools
2. **Agent mode is key** - Regular chat doesn't have MCP access
3. **Combine with Continue's context** - Use `@file` and `@folder` with memory
4. **Share configs** - Continue configs work across VS Code and JetBrains

## Recommended: Memory Protocol

Add this to `.continuerules` or your Continue config for automatic memory usage:

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
- **Project-specific**: `.continuerules` in project root
- **User-level**: `~/.continue/config.yaml` under `systemMessage`

## Continue-Specific Features

Continue's MCP integration works well for:

- **Storing code patterns** you discover during reviews
- **Remembering debugging solutions** across projects
- **Tracking API behaviors** and quirks
- **Building project knowledge** over time

## JetBrains-Specific Notes

For JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.):

1. Install Continue plugin from JetBrains Marketplace
2. Configuration is the same as VS Code
3. Config location: `~/.continue/config.yaml`
4. Access via Tools > Continue or the sidebar

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [Continue MCP Documentation](https://docs.continue.dev/customize/deep-dives/mcp)

---

**Works with**: Continue.dev (VS Code and JetBrains)
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
**Config formats**: YAML, JSON
