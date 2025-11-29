# Claude Code Memory Server v1.0.0 - Production Release

**Release Date**: November 28, 2025

## TL;DR

```bash
pip install memorygraphMCP
memorygraph
```

That's it. Zero configuration needed. Memory stored locally in SQLite.

---

## What is Claude Code Memory?

A Model Context Protocol (MCP) server that gives Claude Code persistent memory across sessions and projects. Store development patterns, track relationships, and retrieve contextual knowledge automatically.

**The Problem**: Claude Code forgets everything between sessions. You repeat yourself. Patterns get lost.

**The Solution**: Graph-based memory with three complexity tiers. Start simple, scale when needed.

---

## v1.0.0 Highlights

### Zero-Config Default
- **SQLite backend** with no setup required
- Automatic database creation at `~/.memorygraph/memory.db`
- No external dependencies for basic usage
- Works out of the box on macOS, Linux, Windows (WSL)

### Three-Tier Complexity Model

| Mode | Tools | Setup | Use Case |
|------|-------|-------|----------|
| **Lite** | 8 | 30 sec | Getting started, basic memory |
| **Standard** | 15 | 30 sec | Pattern recognition, intelligence |
| **Full** | 44 | 5 min | Graph analytics, workflows, AI |

Start with lite, upgrade when you need more power.

### Multi-Backend Support
- **SQLite** (default): Zero config, perfect for <10k memories
- **Neo4j**: Production-grade graph database, best for teams
- **Memgraph**: Fastest analytics, best for large-scale graphs

All backends support all 44 tools.

### Simple CLI
```bash
# Default (lite mode, SQLite)
memorygraph

# Standard mode
memorygraph --profile standard

# Full power with Neo4j
memorygraph --backend neo4j --profile full

# Show configuration
memorygraph --show-config

# Version
memorygraph --version
```

### Docker Support
```bash
# SQLite mode
docker compose up -d

# Neo4j mode (full power)
docker compose -f docker-compose.neo4j.yml up -d

# Memgraph mode (fastest)
docker compose -f docker-compose.full.yml up -d
```

### Complete Documentation
- **README.md**: Quick start in 30 seconds
- **FULL_MODE.md**: Advanced features guide
- **DEPLOYMENT.md**: Complete deployment guide
- **CLAUDE_CODE_SETUP.md**: Step-by-step integration
- **TOOL_PROFILES.md**: All 44 tools documented

---

## Installation

### Option 1: pip (Recommended)

**Lite Mode (Default)**:
```bash
pip install memorygraphMCP
```

**Standard Mode (with intelligence)**:
```bash
pip install "memorygraph[intelligence]"
```

**Full Mode (with Neo4j)**:
```bash
pip install "memorygraph[neo4j,intelligence]"
```

### Option 2: Docker

```bash
git clone https://github.com/gregorydickson/memorygraph.git
cd memorygraph
docker compose up -d
```

---

## Claude Code Integration

Add to `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

Restart Claude Code and start using memory:
- "Store this authentication pattern for later"
- "What similar problems have we solved?"
- "Find all memories about database optimization"

---

## Key Features

### Core Memory Operations (All Modes)
- Store, retrieve, search, update, delete memories
- Create relationships between concepts
- Track project context and technology stacks
- Full-text search and filtering

### Intelligence Features (Standard & Full)
- Pattern recognition
- Similar solution suggestions
- Context-aware retrieval
- Session briefings
- Memory history tracking

### Advanced Analytics (Full Mode)
- Graph cluster analysis
- Bridge node detection
- Path finding between memories
- Workflow optimization
- Project integration
- Proactive AI suggestions

---

## Architecture

### Memory Types
- **Task**: Development tasks and execution patterns
- **CodePattern**: Reusable code solutions
- **Problem**: Issues encountered
- **Solution**: Problem resolutions
- **Project**: Codebase context
- **Technology**: Framework/language knowledge

### Relationships (7 categories, 35+ types)
- **Causal**: CAUSES, TRIGGERS, PREVENTS
- **Solution**: SOLVES, IMPROVES, REPLACES
- **Context**: APPLIES_TO, REQUIRES, USED_IN
- **Learning**: BUILDS_ON, CONFIRMS, CONTRADICTS
- **Similarity**: SIMILAR_TO, VARIANT_OF
- **Workflow**: FOLLOWS, DEPENDS_ON, ENABLES
- **Quality**: EFFECTIVE_FOR, PREFERRED_OVER

---

## What's New in v1.0.0

### Major Changes
- **Default backend changed**: Neo4j → SQLite (zero-config)
- **Tool profiling system**: Choose complexity (lite/standard/full)
- **CLI implementation**: `memorygraph` command with flags
- **Docker support**: Complete compose files for all backends
- **Documentation overhaul**: Beginner-friendly guides

### Breaking Changes
- Default backend is now SQLite (was Neo4j)
- Tool profile filtering may hide tools in lite/standard modes
- To use old setup: Set `MEMORY_BACKEND=neo4j` environment variable

### Migration Guide
**Existing users (was using Neo4j)**:
```bash
export MEMORY_BACKEND=neo4j
export MEMORY_TOOL_PROFILE=full
```

**New users**:
Nothing needed! Just `pip install memorygraphMCP`.

---

## Performance

### SQLite (Default)
- 1,000 memories: <50ms query time
- 10,000 memories: <100ms query time
- 100,000 memories: <500ms query time

### Neo4j (Recommended for >10k memories)
- 10x faster graph traversals
- 100x faster complex analytics
- Millions of memories supported

### Memgraph (Fastest)
- Fastest graph analytics
- In-memory processing
- Best for real-time queries

---

## Test Status

- **Tests**: 401/409 passing (98%)
- **Coverage**: 93%
- **Backends tested**: SQLite, Neo4j, Memgraph
- **Platforms**: macOS (primary), Linux (compatible), Windows WSL (compatible)

---

## Roadmap

### v1.0 (Current) ✅
- SQLite default
- Three-tier complexity
- 44 MCP tools
- CLI interface
- Docker support

### v1.1 (Planned)
- Data export/import
- Web visualization dashboard
- PostgreSQL backend (pg_graph)
- Enhanced embeddings
- Workflow templates

### v2.0 (Future)
- Multi-user support
- Team memory sharing
- Cloud-hosted options
- Advanced AI features

---

## Getting Help

- **Documentation**: [docs/](https://github.com/gregorydickson/memorygraph/tree/main/docs)
- **Issues**: [GitHub Issues](https://github.com/gregorydickson/memorygraph/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gregorydickson/memorygraph/discussions)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/gregorydickson/memorygraph/blob/main/CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/gregorydickson/memorygraph.git
cd memorygraph
pip install -e ".[dev]"
pytest tests/
```

---

## Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) - Protocol specification
- [Neo4j](https://neo4j.com/) - Graph database platform
- [Memgraph](https://memgraph.com/) - High-performance graph platform
- [Claude Code](https://claude.ai/code) - AI-powered development environment

---

## License

MIT License - See [LICENSE](https://github.com/gregorydickson/memorygraph/blob/main/LICENSE) file for details.

---

**Made with ❤️ for the Claude Code community**

*Start simple. Upgrade when needed. Never lose context again.*

---

## Quick Links

- [PyPI Package](https://pypi.org/project/memorygraph/)
- [GitHub Repository](https://github.com/gregorydickson/memorygraph)
- [Documentation](https://github.com/gregorydickson/memorygraph/blob/main/docs/)
- [Quick Start Guide](https://github.com/gregorydickson/memorygraph/blob/main/docs/CLAUDE_CODE_SETUP.md)
- [Full Mode Guide](https://github.com/gregorydickson/memorygraph/blob/main/docs/FULL_MODE.md)

---

**Install now**: `pip install memorygraphMCP`
