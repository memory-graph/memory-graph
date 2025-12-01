# MemoryGraph Setup for Gemini CLI

Get persistent memory working with Google's Gemini CLI.

## Prerequisites

- **Gemini CLI** installed ([Installation Guide](https://github.com/google-gemini/gemini-cli))
- **Google AI API key** or Google Cloud credentials
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

### 2. Configure Gemini CLI

Gemini CLI supports MCP servers via configuration file.

**Create or edit** `~/.gemini/config.json`:

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

### 3. Verify Setup

Start Gemini CLI and check for MCP tools:

```bash
gemini
```

Then ask:

```
What MCP tools do you have available?
```

## First Memory

Store a memory:

```
Store this for later: The main database is PostgreSQL on port 5432
```

Retrieve it:

```
What database does this project use?
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

### Custom Database Path

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "env": {
        "MEMORY_SQLITE_PATH": "/path/to/memory.db"
      }
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
      "args": []
    }
  }
}
```

Find your path: `which memorygraph`

## Troubleshooting

### MCP Server Not Loading

1. **Check Gemini CLI version** - Ensure you have MCP support
2. **Verify config location**: `~/.gemini/config.json`
3. **Check JSON syntax** - Use a JSON validator

### Command Not Found

```bash
# Check if memorygraph is installed
which memorygraph

# If not found
pipx ensurepath
# Restart terminal
```

### Test Server Manually

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph
```

### View Logs

Check Gemini CLI output for MCP-related errors:

```bash
gemini --verbose
```

## Tips for Gemini CLI Users

1. **Leverage the 1M context window** - Gemini can process large codebases
2. **Store key insights** - Remember important findings from large file analysis
3. **Track patterns** - Use memory to build up project knowledge
4. **Query before analysis** - Check what you already know about a topic

## Gemini-Specific Use Cases

Gemini CLI's large context window pairs well with MemoryGraph:

### Large Codebase Analysis

```
Analyze all the files in src/ and store key architectural patterns you find
```

### Cross-File Patterns

```
Search the codebase for authentication patterns and remember what you find
```

### Incremental Learning

```
What have we learned about this codebase so far?
```

## Combining with Gemini's Strengths

| Gemini Strength | MemoryGraph Enhancement |
|-----------------|------------------------|
| 1M token context | Store insights from large analyses |
| Fast inference | Quick memory queries |
| Code understanding | Persist code patterns |
| Multi-modal | Store context about diagrams/images discussed |

## Configuration File Location

Default location: `~/.gemini/config.json`

Alternative locations may be supported - check Gemini CLI documentation for your version.

## Limitations

- MCP support in Gemini CLI may vary by version
- Check Google's documentation for current MCP capabilities
- Some features may require specific Gemini API tiers

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [Gemini CLI Documentation](https://github.com/google-gemini/gemini-cli)

---

**Works with**: Gemini CLI (with MCP support)
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
**Note**: MCP support may vary by Gemini CLI version
