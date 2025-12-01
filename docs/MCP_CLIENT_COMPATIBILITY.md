# MCP Client Compatibility Guide

MemoryGraph works with any MCP-compliant AI coding tool. This guide covers supported clients, configuration formats, and compatibility details.

## Supported MCP Clients

| Client | Type | MCP Support | Transport | Quick Start |
|--------|------|-------------|-----------|-------------|
| **Claude Code** | CLI/IDE | Full | stdio | [Setup Guide](CLAUDE_CODE_SETUP.md) |
| **Cursor AI** | IDE | Full | stdio, SSE | [Setup Guide](quickstart/CURSOR_SETUP.md) |
| **Windsurf** | IDE | Full | stdio, SSE | [Setup Guide](quickstart/WINDSURF_SETUP.md) |
| **VS Code + Copilot** | IDE Extension | Full (1.102+) | stdio | [Setup Guide](quickstart/VSCODE_COPILOT_SETUP.md) |
| **Continue.dev** | IDE Extension | Full | stdio | [Setup Guide](quickstart/CONTINUE_SETUP.md) |
| **Cline** | IDE Extension | Full | stdio | [Setup Guide](quickstart/CLINE_SETUP.md) |
| **Gemini CLI** | CLI | Varies | stdio | [Setup Guide](quickstart/GEMINI_CLI_SETUP.md) |

## MCP Protocol Overview

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard that allows AI assistants to connect to external tools and data sources. MemoryGraph implements the MCP server specification, making it compatible with any MCP client.

### How It Works

```
┌─────────────┐         ┌─────────────────┐         ┌──────────────┐
│  AI Client  │ ──MCP── │   MemoryGraph   │ ──────▶ │   SQLite/    │
│  (Cursor,   │         │   MCP Server    │         │   Neo4j/     │
│   VS Code)  │         │                 │         │   Memgraph   │
└─────────────┘         └─────────────────┘         └──────────────┘
```

1. **Client** sends MCP tool calls (e.g., `store_memory`, `search_memories`)
2. **MemoryGraph** processes requests and manages data
3. **Database** stores memories and relationships persistently

## Transport Protocols

MCP supports multiple transport protocols:

### stdio (Standard I/O)

**Most common.** Communication via stdin/stdout.

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

**Supported by**: All clients

### SSE (Server-Sent Events)

HTTP-based transport for web environments.

```json
{
  "mcpServers": {
    "memorygraph": {
      "url": "http://localhost:8080/sse",
      "transport": "sse"
    }
  }
}
```

**Supported by**: Cursor, Windsurf, some web-based clients

**Note**: MemoryGraph currently supports stdio. SSE support may require additional configuration.

## Configuration Formats

Different clients use different configuration formats:

### JSON (Most Common)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "standard"],
      "env": {
        "MEMORY_SQLITE_PATH": "~/.memorygraph/memory.db"
      }
    }
  }
}
```

**Used by**: Claude Code, Cursor, VS Code, Cline

### YAML

```yaml
mcpServers:
  - name: memorygraph
    command: memorygraph
    args:
      - "--profile"
      - "standard"
    env:
      MEMORY_SQLITE_PATH: "~/.memorygraph/memory.db"
```

**Used by**: Continue.dev

## Configuration File Locations

| Client | Location |
|--------|----------|
| **Claude Code** | `~/.claude.json` (user) or `.mcp.json` (project) |
| **Cursor** | `.cursor/mcp.json` (project) or Settings UI |
| **VS Code + Copilot** | `.vscode/mcp.json` (workspace) |
| **Continue** | `~/.continue/config.yaml` or `~/.continue/mcpServers/` |
| **Cline** | Via Settings UI → MCP Settings |
| **Windsurf** | Settings UI or config file |

## Feature Comparison

| Feature | Claude Code | Cursor | VS Code | Continue | Cline |
|---------|-------------|--------|---------|----------|-------|
| **MCP Support** | Native | Full | Full (1.102+) | Full | Full |
| **Agent Mode** | Default | Required | Required | Required | Default |
| **Max Tools** | Unlimited | Unlimited | 128 | Unlimited | Unlimited |
| **Config UI** | CLI | Yes | No | Yes | Yes |
| **Project Scope** | Yes | Yes | Yes | Yes | Limited |

## Tool Profiles

MemoryGraph offers three tool profiles:

| Profile | Tools | Best For |
|---------|-------|----------|
| **lite** | 8 | Quick start, simple workflows |
| **standard** | 15 | Pattern recognition, most users |
| **full** | 44 | Advanced analytics, power users |

Configure via command line argument:

```json
{
  "args": ["--profile", "standard"]
}
```

## Migration Between Clients

Moving from one client to another is straightforward:

### 1. Export Configuration

Most configurations are similar. Copy your `mcp.json` content.

### 2. Adapt Format

**From Claude Code to Cursor**: Direct copy works

```json
// Both use the same format
{
  "mcpServers": {
    "memorygraph": { "command": "memorygraph" }
  }
}
```

**From JSON to YAML (Continue)**:

```yaml
# Convert JSON structure to YAML
mcpServers:
  - name: memorygraph
    command: memorygraph
```

### 3. Memory Data Persists

Your memory database (`~/.memorygraph/memory.db`) is independent of the client. Switch clients without losing data.

## Troubleshooting by Client

### Claude Code
- Use `claude mcp list` to check server status
- See [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md)

### Cursor
- Check Settings > Features > MCP for server status
- Requires Agent mode for MCP tools
- See [CURSOR_SETUP.md](quickstart/CURSOR_SETUP.md)

### VS Code + Copilot
- Requires VS Code 1.102+
- Use Command Palette: "MCP: List Servers"
- See [VSCODE_COPILOT_SETUP.md](quickstart/VSCODE_COPILOT_SETUP.md)

### Continue
- Use Agent mode (not Chat or Edit)
- Check `~/.continue/config.yaml` syntax
- See [CONTINUE_SETUP.md](quickstart/CONTINUE_SETUP.md)

### Cline
- Access MCP Settings via gear icon
- Check for "disabled: false"
- See [CLINE_SETUP.md](quickstart/CLINE_SETUP.md)

## Common Issues

### "Command not found"

```bash
# Check installation
which memorygraph

# If not found, add pipx bin to PATH
pipx ensurepath
# Restart terminal
```

### "Server not connecting"

1. Test manually:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph
   ```

2. Use full path in config:
   ```json
   { "command": "/full/path/to/memorygraph" }
   ```

### "Tools not appearing"

- Ensure Agent mode is enabled (most clients)
- Restart the client after configuration changes
- Check for typos in configuration

## Security Considerations

### Data Location

By default, MemoryGraph stores data locally:
- **Default path**: `~/.memorygraph/memory.db`
- **No external transmission** in default configuration
- **Project-scoped** databases possible for isolation

### Per-Client Security

| Client | Security Features |
|--------|-------------------|
| Claude Code | User-scoped by default |
| Cursor | Workspace trust |
| VS Code | Workspace trust, enterprise policies |
| Continue | Open-source, auditable |
| Cline | Local API keys |

### Enterprise Deployment

For enterprise use:
- Configure project-scoped databases
- Use Neo4j/Memgraph for team sharing
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for advanced options

## Getting Help

- **Documentation**: [README](../README.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues**: [Report bugs](https://github.com/gregorydickson/memory-graph/issues)
- **Discussions**: [Ask questions](https://github.com/gregorydickson/memory-graph/discussions)

---

**MemoryGraph**: Universal memory for AI coding agents

*Works with any MCP-compliant client. Your data, your choice of tools.*
