# MemoryGraph Setup for ChatGPT Desktop

Get persistent memory working in ChatGPT Desktop in under 2 minutes.

## Prerequisites

- ChatGPT Desktop app (latest version with MCP support)
- Python 3.10+
- pipx installed (`pip install --user pipx && pipx ensurepath`)

## MCP Support Status

As of 2025, OpenAI has officially adopted the Model Context Protocol (MCP) and integrated it across their products:

- **ChatGPT Desktop**: Full MCP client support (March 2025+)
- **Developer Mode**: Beta feature with complete MCP tool support
- **OpenAI Agents SDK**: Native MCP integration
- **Responses API**: MCP-compatible

ChatGPT Desktop now includes built-in MCP client capabilities for seamless integration with external tools, real-time data sources, and specialized workflows.

## Quick Start

### 1. Install MemoryGraph

```bash
pipx install memorygraphMCP
```

Verify installation:
```bash
memorygraph --version
```

### 2. Configure ChatGPT Desktop

The exact configuration method depends on your ChatGPT Desktop version:

#### Option A: Via Developer Mode (Beta)

1. Open ChatGPT Desktop
2. Enable Developer Mode in Settings
3. Navigate to **Settings > MCP Servers**
4. Click **Add Server**
5. Enter:
   - Name: `memorygraph`
   - Command: `memorygraph`
   - Args: (leave empty or add `--profile extended` for more tools)

#### Option B: Via Configuration File

ChatGPT Desktop may use a configuration file similar to Claude Desktop. Check for:

**macOS**:
```bash
~/Library/Application\ Support/ChatGPT/chatgpt_config.json
```

**Windows**:
```
%APPDATA%\ChatGPT\chatgpt_config.json
```

Add the MCP server configuration:

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

**Note**: Configuration file location may vary by version. Check ChatGPT Desktop documentation for your specific version.

### 3. Handle PATH Issues (if needed)

If ChatGPT Desktop cannot find the `memorygraph` command:

**Option A: Use full path** (recommended)
```bash
# Find your installation path
which memorygraph

# Use full path in config
{
  "command": "/Users/yourname/.local/bin/memorygraph"
}
```

**Option B: Create symlink**
```bash
# Create symlink to system directory
sudo ln -s ~/.local/bin/memorygraph /usr/local/bin/memorygraph

# Then use simple command
{
  "command": "memorygraph"
}
```

### 4. Restart ChatGPT Desktop

Completely quit and restart ChatGPT Desktop to load the MCP server.

### 5. Verify Connection

In a new conversation, ask:

```
What memory tools do you have available?
```

You should see MemoryGraph tools like `store_memory`, `recall_memories`, `search_memories`, etc.

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

Adds statistics and complex query tools (11 total tools).

### Custom Database Location

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": [],
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

### Server Not Connecting

1. **Verify memorygraph is installed**:
   ```bash
   which memorygraph
   memorygraph --version
   ```

2. **Check Developer Mode is enabled** (if using beta):
   - Settings > Developer Mode > ON
   - MCP Servers section should be visible

3. **Test server manually**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph
   ```

4. **Use full path in config**:
   ```json
   {
     "command": "/Users/yourname/.local/bin/memorygraph"
   }
   ```

### Tools Not Appearing

1. **Restart completely**: Quit ChatGPT Desktop (not just close window) and reopen
2. **Check MCP server status**: Look for server status indicator in Settings
3. **Verify JSON syntax**: Validate your config file at https://jsonlint.com
4. **Check logs**: Look for ChatGPT Desktop logs in:
   - macOS: `~/Library/Logs/ChatGPT/`
   - Windows: `%APPDATA%\ChatGPT\logs\`

### Command Not Found Error

Similar to Claude Desktop, ChatGPT Desktop may have restricted PATH:

```bash
# Solution 1: Use full path
which memorygraph  # Copy this path
# Add to config: "/Users/yourname/.local/bin/memorygraph"

# Solution 2: Create symlink
sudo ln -s ~/.local/bin/memorygraph /usr/local/bin/memorygraph
```

### Permission Issues

On macOS, you may need to grant ChatGPT Desktop permissions:

1. System Settings > Privacy & Security > Full Disk Access
2. Add ChatGPT Desktop to the list
3. Restart ChatGPT Desktop

## Tips for ChatGPT Desktop Users

1. **Use Developer Mode for full MCP access** - Regular mode may have limited tool support
2. **Store context between sessions** - Build up project knowledge over time
3. **Query before starting** - Check if you've solved similar problems
4. **Save successful patterns** - Remember what works for future reference
5. **Link related memories** - Create relationships between problems and solutions

## Recommended: Memory Protocol

For consistent memory usage, configure ChatGPT with memory guidelines. If ChatGPT Desktop supports custom instructions, add:

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

## OpenAI Apps SDK Integration

ChatGPT Desktop uses the OpenAI Apps SDK, which has MCP as its backbone. This enables:

- **Rich interactive applications** inside ChatGPT
- **Standardized tool integration** via MCP protocol
- **Bidirectional communication** between tools and ChatGPT
- **Resource discovery** through MCP servers

MemoryGraph leverages this SDK integration to provide persistent memory capabilities.

## Features Available via MCP

ChatGPT Desktop MCP integration provides:

- **Extended capabilities**: Access specialized tools directly in conversations
- **Real-time information**: Retrieve data beyond ChatGPT's training cutoff
- **Workflow automation**: Connect ChatGPT to existing tools and systems
- **Tool chaining**: Combine multiple MCP tools for complex workflows
- **Persistent context**: Store and recall information across sessions

## Version Compatibility

- **MCP Protocol**: 2024-11-05 specification
- **ChatGPT Desktop**: Version with MCP support (March 2025+)
- **MemoryGraph**: v0.9.0+ recommended for full compatibility

Check for updates regularly as OpenAI continues to enhance MCP integration.

## Example Full Configuration

Here's a complete working example (macOS):

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/john/.local/bin/memorygraph",
      "args": ["--profile", "extended"],
      "env": {
        "MEMORY_SQLITE_PATH": "/Users/john/.memorygraph/memory.db",
        "MEMORY_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Remember to:
1. Replace `/Users/john` with your actual home directory path
2. Use the path from `which memorygraph`
3. Ensure valid JSON syntax (commas, quotes, braces)

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [OpenAI Documentation](https://platform.openai.com/)

## Resources

- [OpenAI MCP Announcement](https://platform.openai.com/docs/guides/mcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [ChatGPT Desktop Download](https://openai.com/chatgpt/desktop)

---

**Works with**: ChatGPT Desktop (macOS, Windows) with MCP support
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
**Status**: Official MCP support as of March 2025

**Note**: ChatGPT Desktop's MCP implementation is evolving. Check OpenAI's documentation for the latest configuration details specific to your version.
