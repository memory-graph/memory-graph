# MemoryGraph Setup for OpenCode

Get persistent memory working in OpenCode in under 2 minutes.

## Prerequisites

- OpenCode installed (latest version)
- Python 3.10+
- pipx installed (`pip install --user pipx && pipx ensurepath`)

## Choose Your Backend

| Feature | Local (SQLite) | Cloud |
|---------|---------------|-------|
| Setup | Zero-config | API key required |
| Multi-device | No | Yes |
| Offline | Yes | No |
| Cost | Free | Free tier |

**New users**: Start with Local for simplicity, Cloud for sync.

## Quick Start (Local Backend)

1. Install: `pipx install memorygraphMCP`

2. Config: Add to `~/.opencode/opencode.json`:
```json
{
  "mcp": {
    "memorygraph": {
      "type": "local",
      "command": ["memorygraph"],
      "enabled": true
    }
  }
}
```

3. Restart OpenCode

4. Verify: Ask "What MCP tools do you have available?"

## Quick Start (Cloud Backend)

1. Get API key from [app.memorygraph.dev](https://app.memorygraph.dev)

2. Install: `pipx install memorygraphMCP`

3. Config:
```json
{
  "mcp": {
    "memorygraph": {
      "type": "local",
      "command": ["memorygraph", "--backend", "cloud"],
      "enabled": true,
      "environment": {
        "MEMORYGRAPH_API_KEY": "mg_your_key"
      }
    }
  }
}
```

4. Restart and verify

## Troubleshooting

- **Command not found**: Use full path from `which memorygraph`
- **Tools not appearing**: Restart OpenCode, check JSON syntax
- **Connection issues**: Run `memorygraph --show-config`

For advanced config, see [CONFIGURATION.md](../CONFIGURATION.md)