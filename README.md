# MemoryGraph

## MCP Memory Server for AI Coding Agents

[![Tests](https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml/badge.svg)](https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/memorygraph)](https://pypi.org/project/memorygraph/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Zero Config](https://img.shields.io/badge/setup-zero--config-green)](docs/DEPLOYMENT.md)
[![3 Backends](https://img.shields.io/badge/backends-SQLite%20%7C%20Neo4j%20%7C%20Memgraph-purple)](docs/FULL_MODE.md)

A graph-based Model Context Protocol (MCP) server that gives **AI coding agents** persistent memory. Originally built for Claude Code, MemoryGraph works with any MCP-enabled coding agent. Store development patterns, track relationships, and retrieve contextual knowledge across sessions and projects.

---

## Quick Start (30 seconds)

### Step 1: Install

```bash
pip install memorygraphMCP
```

### Step 2: Add to Your MCP Client

**For Claude Code**, edit `.claude/mcp.json` (or `~/.config/claude/mcp_settings.json`):

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

**For other MCP clients** (Cursor, Continue, etc.), follow their MCP server configuration docs.

### Step 3: Restart Your Coding Agent

That's it! Memory is stored in `~/.memorygraph/memory.db`. Zero additional configuration needed.

### Start Using It

Ask your AI coding agent in any conversation:
- "Store this pattern for later"
- "What similar problems have we solved?"
- "Remember this approach works well for authentication"
- "Show me all memories related to database migrations"

See [CLAUDE_CODE_SETUP.md](docs/CLAUDE_CODE_SETUP.md) for Claude Code integration guide and advanced configurations.

---

## What is This?

**MemoryGraph** is a universal MCP server implementation that provides persistent memory for AI coding agents, built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io).

### Understanding the Architecture

- **MCP** is an open specification that allows AI assistants to connect to external data sources and tools
- **MemoryGraph** is an MCP server implementation that provides memory capabilities via graph database backends
- **AI coding agents** (Claude Code, Cursor, Continue, etc.) are MCP clients that can connect to any MCP-compliant server

Think of it this way:
- **MCP Specification** = HTTP specification
- **MemoryGraph** = A web server (like nginx or Apache)
- **Coding Agents** = Web browsers that can connect to any HTTP server

This implementation is **not** the only way to provide memory to coding agents. Anyone can build their own MCP server with different memory approaches. MemoryGraph offers:
- Graph-based knowledge representation
- Multiple backend options (SQLite, Neo4j, Memgraph)
- Progressive complexity model (lite → standard → full)
- 44 specialized memory tools

**Why build on MCP?** It's an open standard. Your memory data isn't locked into proprietary formats. You can migrate to other MCP servers, build your own, or integrate multiple memory systems simultaneously.

**Originally Built For Claude Code**: While MemoryGraph works with any MCP client, it was specifically designed and optimized for Claude Code workflows.

---

## Understanding Memory Options

Most AI coding agents offer multiple ways to maintain persistent context across sessions. Here's how they compare (using Claude Code as example):

### Memory Option Comparison

| Feature | CLAUDE.md Files | Anthropic Memory Tool (API) | MCP Memory Servers |
|---------|----------------|----------------------------|-------------------|
| **Setup** | Zero config | API integration required | MCP server config |
| **Storage** | Markdown files | Your implementation | Server's backend |
| **Automatic** | ✅ Always loaded | ✅ Claude checks automatically | ⚡ On-demand via tools |
| **Relationships** | ❌ Flat text | ❌ Flat files | ✅ Depends on server |
| **Searchable** | ❌ No search | ✅ File-based | ✅ Semantic/graph search |
| **Best For** | Instructions, preferences | Long-running agents | Knowledge graphs, patterns |

### Option 1: CLAUDE.md Files (Built-in)

**What it is**: Claude Code's native memory system using hierarchical Markdown files.

**How it works**:
- Files are automatically loaded into context when Claude Code launches
- Hierarchical: Enterprise → Project → User → Local
- You manage the content manually or via `#` quick-add

**Best For**:
- Coding conventions and style guides
- Project architecture documentation
- Team-shared instructions
- Personal preferences

**Limitations**:
- Everything loads into context (token cost)
- No search or retrieval - Claude sees all or nothing
- No relationships between concepts
- Manual maintenance required

### Option 2: Anthropic Memory Tool (API Beta)

**What it is**: A beta feature in the Anthropic API for building custom memory backends.

**How it works**:
- Claude makes tool calls to read/write files in a `/memories` directory
- You implement the storage backend (file system, database, cloud)
- Uses `BetaAbstractMemoryTool` (Python) or `betaMemoryTool` (TypeScript)

**Best For**:
- Custom applications calling Anthropic API
- Long-running agentic workflows
- Workflows that need context editing

**Not For**:
- Claude Code users (different architecture)
- MCP server implementations

### Option 3: MCP Memory Servers

**What it is**: External servers that provide memory tools via Model Context Protocol.

**How it works**:
- Claude Code connects to MCP server via stdio/HTTP
- Server exposes tools like `store_memory`, `search_memories`, `get_related`
- Storage backend varies by implementation (SQLite, Neo4j, vector stores)

**Popular Implementations**:

| Server | Storage | Key Feature |
|--------|---------|-------------|
| mcp-memory-keeper | SQLite | Channels, checkpoints, git integration |
| mcp-memory-service | SQLite + Cloudflare | Hybrid sync, semantic search |
| **memorygraph** | Neo4j/Memgraph/SQLite | **Graph relationships, pattern recognition** |

---

## Why memorygraph?

### Graph Relationships Make the Difference

**memorygraph** uses **graph database relationships** to capture how concepts connect - something flat file systems and vector stores cannot do.

**Flat storage** (CLAUDE.md, vector stores):
```
Memory 1: "Fixed timeout by adding retry logic"
Memory 2: "Retry logic caused memory leak"
Memory 3: "Fixed memory leak with connection pooling"
```
No connection between these - search finds them separately.

**Graph storage** (memorygraph):
```
[timeout_fix] --CAUSES--> [memory_leak] --SOLVED_BY--> [connection_pooling]
     |                                                        |
     +------------------SUPERSEDED_BY------------------------+
```
Query: "What happened with retry logic?" → Returns the full causal chain.

### Relationship Categories

We track seven categories of relationships that CLAUDE.md files cannot represent:

1. **Causal**: CAUSES, TRIGGERS, LEADS_TO, PREVENTS
2. **Solution**: SOLVES, ADDRESSES, ALTERNATIVE_TO, IMPROVES
3. **Context**: OCCURS_IN, APPLIES_TO, WORKS_WITH, REQUIRES
4. **Learning**: BUILDS_ON, CONTRADICTS, CONFIRMS
5. **Similarity**: SIMILAR_TO, VARIANT_OF, RELATED_TO
6. **Workflow**: FOLLOWS, DEPENDS_ON, ENABLES, BLOCKS
7. **Quality**: EFFECTIVE_FOR, PREFERRED_OVER, DEPRECATED_BY

### Complementary Usage

**memorygraph complements CLAUDE.md files** - it doesn't replace them:

| Use CLAUDE.md For | Use memorygraph For |
|-------------------|---------------------------|
| "Always use 2-space indentation" | "Last time we used 4-space, it broke the linter" |
| "Run tests before committing" | "The auth tests failed because of X, fixed by Y" |
| "API uses JWT authentication" | "JWT refresh logic caused issues; switched to session tokens" |
| Static instructions | Dynamic learnings |
| What to do | What happened and why |

### Decision Guide

```
┌─────────────────────────────────────────────────────────────────┐
│                     Decision Guide                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  "I need Claude to follow project conventions"                   │
│       → Use CLAUDE.md files                                      │
│                                                                  │
│  "I need Claude to remember what we discussed"                   │
│       → Use MCP memory server (any)                              │
│                                                                  │
│  "I need Claude to understand WHY a solution worked"             │
│       → Use memorygraph (graph relationships)             │
│                                                                  │
│  "I need Claude to find similar past problems"                   │
│       → Use memorygraph (pattern recognition)             │
│                                                                  │
│  "I'm building a custom app with Anthropic API"                  │
│       → Use Anthropic Memory Tool (BetaAbstractMemoryTool)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Choose Your Mode

Start simple, upgrade when needed:

| Feature | Lite (Default) | Standard | Full |
|---------|----------------|----------|------|
| **Memory Storage** | ✅ | ✅ | ✅ |
| **Relationships** | ✅ Basic | ✅ Basic | ✅ Advanced |
| **Pattern Recognition** | ❌ | ✅ | ✅ |
| **Session Briefings** | ❌ | ✅ | ✅ |
| **Graph Analytics** | ❌ | ❌ | ✅ |
| **Project Integration** | ❌ | ❌ | ✅ |
| **Workflow Automation** | ❌ | ❌ | ✅ |
| **Backend** | SQLite | SQLite | SQLite/Neo4j/Memgraph |
| **Tools Available** | 8 | 15 | 44 |
| **Setup Time** | 30 sec | 30 sec | 5 min |

```bash
# Default (lite mode)
memorygraph

# Standard mode (pattern recognition)
memorygraph --profile standard

# Full power (all 44 tools)
memorygraph --profile full --backend neo4j
```

---

## Features

### Core Memory Operations (All Modes)
- **Store & Retrieve** - Persistent memory across sessions
- **Smart Search** - Find memories by content, context, or relationships
- **Relationship Tracking** - Link related concepts, solutions, and patterns
- **Project Context** - Organize memories by project and technology

### Intelligence Features (Standard & Full)
- **Pattern Recognition** - Automatically identify reusable patterns
- **Solution Suggestions** - Find similar solutions from past work
- **Context Awareness** - Smart context retrieval with token limiting
- **Session Briefings** - Get AI-generated summaries of your work

### Advanced Analytics (Full Mode Only)
- **Graph Analytics** - Cluster analysis, bridging nodes, path finding
- **Workflow Automation** - Track and optimize development workflows
- **Project Integration** - Codebase scanning and pattern detection
- **Proactive Suggestions** - AI-powered recommendations and issue detection

See [TOOL_PROFILES.md](docs/TOOL_PROFILES.md) for complete tool list.

---

## Installation

### Option 1: pip (Recommended)

```bash
# Basic installation (SQLite, lite mode)
pip install memorygraphMCP

# With intelligence features (standard mode)
pip install "memorygraphMCP[intelligence]"

# Full power with Neo4j
pip install "memorygraphMCP[neo4j,intelligence]"
```

### Option 2: Docker

```bash
# SQLite mode (default)
docker compose up -d

# Neo4j mode (full power)
docker compose -f docker-compose.neo4j.yml up -d
```

### Option 3: uvx (Quick Test / No Install)

Try memorygraph without installation using uvx:

```bash
# Install uv (if not already installed)
pip install uv
# or: curl -LsSf https://astral.sh/uv/install.sh | sh

# Run directly from PyPI
uvx memorygraph --version
uvx memorygraph --show-config

# Run as MCP server (ephemeral)
uvx memorygraph --backend sqlite --profile lite
```

**Note**: uvx is great for quick testing and CI/CD, but **pip install is recommended** for daily use as a persistent MCP server. See [DEPLOYMENT.md](docs/DEPLOYMENT.md#method-4-uvx-ephemeral--testing) for limitations and use cases.

### Installation Method Comparison

| Method | Setup Time | Use Case | Persistence | Recommended For |
|--------|-----------|----------|-------------|-----------------|
| **pip install** | 30 sec | Daily use, MCP server | Yes | Most users |
| **Docker** | 5 min | Team/production | Yes | Power users, teams |
| **uvx** | 10 sec* | Quick test, CI/CD | No** | Testing, automation |

\* First run slower (downloads package), subsequent runs cached
\*\* Requires explicit database path for persistent data (`MEMORY_SQLITE_PATH`)

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed installation options.

---

## Configuration Examples

### Basic Configuration (Lite Mode - Default)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

### Standard Mode (Pattern Recognition)

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

### Full Mode with SQLite

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "full"],
      "env": {
        "MEMORY_TOOL_PROFILE": "full",
        "MEMORY_SQLITE_PATH": "/Users/yourname/.memorygraph/memory.db"
      }
    }
  }
}
```

### Full Mode with Neo4j

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "full"],
      "env": {
        "MEMORY_BACKEND": "neo4j",
        "MEMORY_NEO4J_URI": "bolt://localhost:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "your-password",
        "MEMORY_TOOL_PROFILE": "full"
      }
    }
  }
}
```

### Full Mode with Memgraph

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "memgraph", "--profile", "full"],
      "env": {
        "MEMORY_BACKEND": "memgraph",
        "MEMORY_MEMGRAPH_URI": "bolt://localhost:7687",
        "MEMORY_MEMGRAPH_USER": "memgraph",
        "MEMORY_MEMGRAPH_PASSWORD": "memgraph",
        "MEMORY_TOOL_PROFILE": "full"
      }
    }
  }
}
```

### Docker-based Configuration

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "memorygraph-server",
        "python",
        "-m",
        "claude_memory.server"
      ],
      "env": {
        "MEMORY_BACKEND": "neo4j",
        "MEMORY_NEO4J_URI": "bolt://neo4j:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "your-password"
      }
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
      "args": ["--profile", "standard"],
      "env": {
        "MEMORY_SQLITE_PATH": "/path/to/your/project/.memory/memory.db",
        "MEMORY_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Multiple Memory Servers (Project-Specific)

```json
{
  "mcpServers": {
    "memory-personal": {
      "command": "memorygraph",
      "env": {
        "MEMORY_SQLITE_PATH": "/Users/yourname/.memorygraph/personal.db"
      }
    },
    "memory-work": {
      "command": "memorygraph",
      "args": ["--profile", "full", "--backend", "neo4j"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://work-server:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "work-password"
      }
    }
  }
}
```

See [CLAUDE_CODE_SETUP.md](docs/CLAUDE_CODE_SETUP.md) for more configuration examples and best practices.

---

## Usage Examples

### Basic Memory Storage

```json
{
  "tool": "store_memory",
  "content": "Use bcrypt for password hashing in this project",
  "memory_type": "CodePattern",
  "project": "my-app",
  "tags": ["security", "authentication"]
}
```

### Find Related Memories

```json
{
  "tool": "search_memories",
  "query": "authentication",
  "memory_type": "CodePattern",
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

### Pattern Recognition (Standard/Full)

```json
{
  "tool": "find_similar_solutions",
  "problem_description": "need to validate user input",
  "limit": 3
}
```

See examples in [docs/examples/](docs/examples/) for more use cases.

---

## Architecture

### Memory Types
- **Task** - Development tasks and execution patterns
- **CodePattern** - Reusable code solutions and architectural decisions
- **Problem** - Issues encountered and their context
- **Solution** - How problems were resolved and effectiveness
- **Project** - Codebase context and project-specific knowledge
- **Technology** - Framework, language, and tool-specific knowledge

### Relationship Categories (7 types, 35+ relationships)
1. **Causal** - `CAUSES`, `TRIGGERS`, `LEADS_TO`, `PREVENTS`, `BREAKS`
2. **Solution** - `SOLVES`, `ADDRESSES`, `ALTERNATIVE_TO`, `IMPROVES`, `REPLACES`
3. **Context** - `OCCURS_IN`, `APPLIES_TO`, `WORKS_WITH`, `REQUIRES`, `USED_IN`
4. **Learning** - `BUILDS_ON`, `CONTRADICTS`, `CONFIRMS`, `GENERALIZES`, `SPECIALIZES`
5. **Similarity** - `SIMILAR_TO`, `VARIANT_OF`, `RELATED_TO`, `ANALOGY_TO`, `OPPOSITE_OF`
6. **Workflow** - `FOLLOWS`, `DEPENDS_ON`, `ENABLES`, `BLOCKS`, `PARALLEL_TO`
7. **Quality** - `EFFECTIVE_FOR`, `INEFFECTIVE_FOR`, `PREFERRED_OVER`, `DEPRECATED_BY`, `VALIDATED_BY`

See [schema.md](docs/schema.md) for complete data model.

---

## Backends

### SQLite (Default)
- **Use for**: Getting started, personal projects, <10k memories
- **Pros**: Zero config, no dependencies, portable, fast for most use cases
- **Cons**: Graph queries slower at scale, no concurrent writes
- **Backend**: `--backend sqlite` (default)

### Neo4j
- **Use for**: Production, team use, complex graph analytics
- **Pros**: Industry-standard graph DB, rich query language, excellent tooling
- **Cons**: Requires setup, resource intensive
- **Backend**: `--backend neo4j`

### Memgraph
- **Use for**: High-performance analytics, real-time queries
- **Pros**: Fastest graph analytics, in-memory processing, compatible with Neo4j
- **Cons**: Requires setup, less mature ecosystem
- **Backend**: `--backend memgraph`

See [FULL_MODE.md](docs/FULL_MODE.md) for backend setup guides.

---

## Environment Variables

```bash
# Backend selection
export MEMORY_BACKEND=sqlite          # sqlite (default) | neo4j | memgraph

# Tool profile
export MEMORY_TOOL_PROFILE=lite       # lite (default) | standard | full

# SQLite configuration (default backend)
export MEMORY_SQLITE_PATH=~/.memorygraph/memory.db

# Neo4j configuration (if using neo4j backend)
export MEMORY_NEO4J_URI=bolt://localhost:7687
export MEMORY_NEO4J_USER=neo4j
export MEMORY_NEO4J_PASSWORD=your-password

# Memgraph configuration (if using memgraph backend)
export MEMORY_MEMGRAPH_URI=bolt://localhost:7687
export MEMORY_MEMGRAPH_USER=memgraph
export MEMORY_MEMGRAPH_PASSWORD=your-password

# Logging
export MEMORY_LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
```

### CLI Options

```bash
# Show help
memorygraph --help

# Show current configuration
memorygraph --show-config

# Show version
memorygraph --version

# Run with custom settings
memorygraph --backend neo4j --profile full --log-level DEBUG
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete configuration reference.

---

## Development

### Project Structure
```
memorygraph/
├── src/claude_memory/          # Main source code
│   ├── server.py               # MCP server (44 tools)
│   ├── backends/               # SQLite, Neo4j, Memgraph
│   ├── tools/                  # Tool implementations
│   ├── models.py               # Data models
│   └── cli.py                  # Command-line interface
├── tests/                      # 409 tests, 93% coverage
├── docs/                       # Documentation
└── pyproject.toml             # Package configuration
```

### Development Setup

```bash
# Clone repository
git clone https://github.com/gregorydickson/memorygraph.git
cd memorygraph

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=claude_memory

# Type checking
mypy src/

# Format code
black src/ tests/
ruff --fix src/ tests/
```

### Test Suite

```bash
# All tests
pytest

# With coverage
pytest --cov=claude_memory --cov-report=html

# Specific backend
pytest tests/backends/test_sqlite_backend.py

# Integration tests
pytest tests/integration/
```

**Current Status**: 401/409 tests passing, 93% coverage

---

## Upgrading

### From Lite to Standard
No changes needed - just add the flag:
```bash
memorygraph --profile standard
```

### From SQLite to Neo4j
1. Export SQLite data: `memorygraph --export backup.json`
2. Set up Neo4j (see [FULL_MODE.md](docs/FULL_MODE.md))
3. Import data: `memorygraph --backend neo4j --import backup.json`
4. Update MCP config to use `--backend neo4j`

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed migration guide.

---

## Troubleshooting

### Common Issues

**Server won't start**
```bash
# Check configuration
memorygraph --show-config

# Verify database connection
memorygraph --health
```

**SQLite database locked**
```bash
# Check for running processes
ps aux | grep memorygraph

# Remove lock file (if safe)
rm ~/.memorygraph/memory.db-lock
```

**Neo4j connection refused**
```bash
# Verify Neo4j is running
docker ps | grep neo4j

# Check credentials
memorygraph --backend neo4j --show-config
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md#troubleshooting) for more solutions.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Check [GitHub Issues](https://github.com/gregorydickson/memorygraph/issues)
2. Fork the repository and create a feature branch
3. Make changes following our coding standards (Black, Ruff, mypy)
4. Add tests for new functionality (maintain 90%+ coverage)
5. Submit a pull request with clear description

---

## Roadmap

### v1.0 (Current) ✅
- ✅ SQLite default backend
- ✅ Three-tier complexity (lite/standard/full)
- ✅ 44 MCP tools
- ✅ CLI with `memorygraph` command
- ✅ PyPI publication
- ✅ Docker support

### v1.1 (Planned)
- Web visualization dashboard
- Enhanced embedding support
- PostgreSQL backend (pg_graph)
- Advanced analytics UI
- Workflow automation templates

### v2.0 (Future)
- Multi-user support
- Team memory sharing
- Cloud-hosted options
- Advanced AI features

---

## Performance

### Benchmarks (SQLite)
- **1,000 memories**: <50ms query time
- **10,000 memories**: <100ms query time
- **100,000 memories**: <500ms query time
- **Relationship traversal**: <100ms for 3-hop queries

### Benchmarks (Neo4j)
- **10x faster** graph traversals at scale
- **100x faster** complex analytics queries
- Handles millions of memories efficiently

See [FULL_MODE.md](docs/FULL_MODE.md#performance) for detailed benchmarks.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- [Documentation](docs/) - Guides, references, examples
- [GitHub Issues](https://github.com/gregorydickson/memorygraph/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/gregorydickson/memorygraph/discussions) - Questions and community support

---

## Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) - Protocol specification
- [Neo4j](https://neo4j.com/) - Graph database platform
- [Memgraph](https://memgraph.com/) - High-performance graph platform
- [Claude Code](https://claude.ai/code) - AI-powered development environment

---

**Made with ❤️ for the Claude Code community**

*Start simple. Upgrade when needed. Never lose context again.*
