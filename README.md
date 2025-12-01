# MemoryGraph

## MCP Memory Server for AI Coding Agents

[![Tests](https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml/badge.svg)](https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/memorygraph)](https://pypi.org/project/memorygraph/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Zero Config](https://img.shields.io/badge/setup-zero--config-green)](docs/DEPLOYMENT.md)
[![3 Backends](https://img.shields.io/badge/backends-SQLite%20%7C%20Neo4j%20%7C%20Memgraph-purple)](docs/FULL_MODE.md)

A graph-based [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI coding agents persistent memory. Store patterns, track relationships, retrieve knowledge across sessions.

---

## Quick Start

### Claude Code CLI (30 seconds)

```bash
# 1. Install
pipx install memorygraphMCP

# 2. Add to Claude Code
claude mcp add --scope user memorygraph -- memorygraph

# 3. Restart Claude Code (exit and run 'claude' again)
```

**Verify it works:**
```bash
claude mcp list  # Should show memorygraph with "Connected"
```

Then in Claude Code: *"Store this for later: Use pytest for Python testing"*

![Memory Creation](docs/images/memory-creation.jpg)

> **Other MCP clients?** See [Supported Clients](#supported-mcp-clients) below.
>
> **Need pipx?** `pip install --user pipx && pipx ensurepath`
>
> **Command not found?** Run `pipx ensurepath` and restart your terminal.

---

## Supported MCP Clients

MemoryGraph works with any MCP-compliant AI coding tool:

| Client | Type | Quick Start |
|--------|------|-------------|
| **Claude Code** | CLI/IDE | [Setup Guide](docs/CLAUDE_CODE_SETUP.md) |
| **Cursor AI** | IDE | [Setup Guide](docs/quickstart/CURSOR_SETUP.md) |
| **Windsurf** | IDE | [Setup Guide](docs/quickstart/WINDSURF_SETUP.md) |
| **VS Code + Copilot** | IDE (1.102+) | [Setup Guide](docs/quickstart/VSCODE_COPILOT_SETUP.md) |
| **Continue.dev** | VS Code/JetBrains | [Setup Guide](docs/quickstart/CONTINUE_SETUP.md) |
| **Cline** | VS Code | [Setup Guide](docs/quickstart/CLINE_SETUP.md) |
| **Gemini CLI** | CLI | [Setup Guide](docs/quickstart/GEMINI_CLI_SETUP.md) |

See [MCP_CLIENT_COMPATIBILITY.md](docs/MCP_CLIENT_COMPATIBILITY.md) for detailed compatibility info.

---

## Why MemoryGraph?

### Graph Relationships Make the Difference

**Flat storage** (CLAUDE.md, vector stores):
```
Memory 1: "Fixed timeout by adding retry logic"
Memory 2: "Retry logic caused memory leak"
Memory 3: "Fixed memory leak with connection pooling"
```
No connection between these - search finds them separately.

**Graph storage** (MemoryGraph):
```
[timeout_fix] --CAUSES--> [memory_leak] --SOLVED_BY--> [connection_pooling]
     |                                                        |
     +------------------SUPERSEDED_BY------------------------+
```
Query: "What happened with retry logic?" → Returns the full causal chain.

### When to Use What

| Use CLAUDE.md For | Use MemoryGraph For |
|-------------------|---------------------|
| "Always use 2-space indentation" | "Last time we used 4-space, it broke the linter" |
| "Run tests before committing" | "The auth tests failed because of X, fixed by Y" |
| Static instructions | Dynamic learnings with relationships |

### Relationship Types

MemoryGraph tracks 7 categories of relationships:
- **Causal**: CAUSES, TRIGGERS, LEADS_TO, PREVENTS
- **Solution**: SOLVES, ADDRESSES, ALTERNATIVE_TO, IMPROVES
- **Context**: OCCURS_IN, APPLIES_TO, WORKS_WITH, REQUIRES
- **Learning**: BUILDS_ON, CONTRADICTS, CONFIRMS
- **Similarity**: SIMILAR_TO, VARIANT_OF, RELATED_TO
- **Workflow**: FOLLOWS, DEPENDS_ON, ENABLES, BLOCKS
- **Quality**: EFFECTIVE_FOR, PREFERRED_OVER, DEPRECATED_BY

---

## Choose Your Mode

| Feature | Lite (Default) | Standard | Full |
|---------|----------------|----------|------|
| Memory Storage | 8 tools | 15 tools | 44 tools |
| Relationships | Basic | Basic | Advanced |
| Pattern Recognition | - | Yes | Yes |
| Session Briefings | - | Yes | Yes |
| Graph Analytics | - | - | Yes |
| Backend | SQLite | SQLite | SQLite/Neo4j/Memgraph |
| Setup Time | 30 sec | 30 sec | 5 min |

```bash
memorygraph                      # Lite (default)
memorygraph --profile standard   # Pattern recognition
memorygraph --profile full       # All features
```

See [TOOL_PROFILES.md](docs/TOOL_PROFILES.md) for complete tool list.

---

## Installation Options

### pipx (Recommended)

```bash
pipx install memorygraphMCP                      # Lite mode
pipx install "memorygraphMCP[intelligence]"      # Standard mode
pipx install "memorygraphMCP[neo4j,intelligence]" # Full mode + Neo4j
```

### pip

```bash
pip install --user memorygraphMCP
```

### Docker

```bash
docker compose up -d                           # SQLite
docker compose -f docker-compose.neo4j.yml up -d  # Neo4j
```

### uvx (Quick Test)

```bash
uvx memorygraph --version  # No install needed
```

| Method | Best For | Persistence |
|--------|----------|-------------|
| pipx | Most users | Yes |
| pip | PATH already configured | Yes |
| Docker | Teams, production | Yes |
| uvx | Quick testing | No |

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed options.

---

## Configuration

### Claude Code CLI

```bash
# Lite mode (default)
claude mcp add --scope user memorygraph -- memorygraph

# Standard mode
claude mcp add --scope user memorygraph -- memorygraph --profile standard

# Full mode with Neo4j
claude mcp add --scope user memorygraph \
  --env MEMORY_NEO4J_URI=bolt://localhost:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=password \
  -- memorygraph --profile full --backend neo4j
```

### Other MCP Clients

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "standard"]
    }
  }
}
```

See [CONFIGURATION.md](docs/CONFIGURATION.md) for all options.

---

## Usage

### Store Memories

```json
{
  "tool": "store_memory",
  "content": "Use bcrypt for password hashing",
  "memory_type": "CodePattern",
  "tags": ["security", "authentication"]
}
```

### Search Memories

```json
{
  "tool": "search_memories",
  "query": "authentication",
  "limit": 5
}
```

### Create Relationships

```json
{
  "tool": "create_relationship",
  "from_memory_id": "mem_123",
  "to_memory_id": "mem_456",
  "relationship_type": "SOLVES"
}
```

![Memory Report](docs/images/memory-report.jpg)

See [docs/examples/](docs/examples/) for more use cases.

---

## Backends

| Backend | Best For | Setup |
|---------|----------|-------|
| **SQLite** (default) | Personal use, <10k memories | Zero config |
| **Neo4j** | Teams, complex analytics | [Setup guide](docs/FULL_MODE.md) |
| **Memgraph** | High-performance analytics | [Setup guide](docs/FULL_MODE.md) |

---

## Architecture

### Memory Types
- **Task** - Development tasks and patterns
- **CodePattern** - Reusable solutions
- **Problem** - Issues encountered
- **Solution** - How problems were resolved
- **Project** - Codebase context
- **Technology** - Framework/tool knowledge

### Project Structure
```
memorygraph/
├── src/memorygraph/     # Main source
│   ├── server.py        # MCP server (44 tools)
│   ├── backends/        # SQLite, Neo4j, Memgraph
│   └── tools/           # Tool implementations
├── tests/               # 409 tests, 93% coverage
└── docs/                # Documentation
```

See [schema.md](docs/schema.md) for complete data model.

---

## Troubleshooting

**Command not found?**
```bash
pipx ensurepath && source ~/.bashrc  # or ~/.zshrc
```

**MCP connection failed?**
```bash
memorygraph --version    # Check installation
claude mcp list          # Check connection status
```

**Multiple version conflict?**
```bash
# Use full path to avoid venv conflicts
claude mcp add memorygraph -- ~/.local/bin/memorygraph
```

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

---

## Development

```bash
git clone https://github.com/gregorydickson/memorygraph.git
cd memorygraph
pip install -e ".[dev]"
pytest tests/ -v --cov=memorygraph
```

---

## Roadmap

### Current (v1.0)
- SQLite default backend
- Three-tier complexity (lite/standard/full)
- 44 MCP tools
- PyPI + Docker

### Planned (v1.1)
- Web visualization dashboard
- PostgreSQL backend
- Enhanced embeddings

See [PRODUCT_ROADMAP.md](docs/PRODUCT_ROADMAP.md) for details.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](LICENSE).

---

## Links

- [Documentation](docs/)
- [GitHub Issues](https://github.com/gregorydickson/memorygraph/issues)
- [Discussions](https://github.com/gregorydickson/memorygraph/discussions)

---

**Made for the Claude Code community**

*Start simple. Upgrade when needed. Never lose context again.*
