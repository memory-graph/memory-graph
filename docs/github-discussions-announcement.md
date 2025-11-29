# 🚀 MemoryGraph v0.5.2 - Graph-Based MCP Memory Server Now on PyPI!

I'm excited to announce the initial release of **MemoryGraph**, a production-ready MCP memory server that gives AI coding agents persistent, intelligent memory with relationship tracking.

## 🎯 What is MemoryGraph?

MemoryGraph is an implementation of a persistent memory system for AI coding agents using the Model Context Protocol (MCP). Think of it as giving Claude (or any MCP-compatible AI agent) a long-term memory that understands relationships between concepts, patterns, and solutions.

## ✨ Key Features

- **🗄️ Multi-Backend Support**: SQLite (zero-config), Neo4j, or Memgraph
- **🧠 Intelligent Memory**: Pattern recognition, entity extraction, temporal tracking
- **📊 Graph Analytics**: Relationship tracking, cluster analysis, path finding
- **🔌 MCP Compatible**: Works with Claude Code, Cursor, and other MCP-enabled clients
- **🛠️ Three Tool Profiles**:
  - Lite (8 tools) - Perfect for getting started
  - Standard (15 tools) - Adds intelligence features
  - Full (44 tools) - Complete feature set with analytics

## 🚀 Quick Start

### Installation

```bash
pip install memorygraphMCP
```

### Configuration

Add to your `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

Restart Claude Code, and you're ready to go! MemoryGraph uses SQLite by default - zero configuration needed.

## 📖 What Can You Do With It?

- **Remember coding patterns**: "I always use bcrypt for password hashing in Python"
- **Track relationships**: Link solutions to problems, patterns to technologies
- **Build knowledge graphs**: Connect related memories across projects
- **Search intelligently**: Find memories by content, tags, or relationships
- **Analyze patterns**: Discover recurring workflows and common approaches
- **Project context**: Maintain context across coding sessions

## 🎓 Example Usage

Store a memory:
```
Claude, remember: "Use FastAPI's dependency injection for database connections.
Create a get_db() function that yields a session."
Tag it as: fastapi, database, sqlalchemy, dependency-injection
Memory type: CodePattern
```

Search later:
```
Claude, find all memories about database patterns in FastAPI
```

Create relationships:
```
Claude, link the dependency injection pattern to the database connection problem.
This pattern SOLVES that problem.
```

## 📊 Production Ready

- ✅ **508 tests passing** across Python 3.10, 3.11, 3.12
- ✅ **72% code coverage** with comprehensive integration tests
- ✅ **Type-safe** with full mypy compliance
- ✅ **Docker support** for Neo4j and Memgraph backends
- ✅ **Comprehensive documentation** with setup guides and deployment options

## 🔗 Resources

- **PyPI**: https://pypi.org/project/memorygraphMCP/
- **GitHub**: https://github.com/gregorydickson/memory-graph
- **Documentation**: [Setup Guide](https://github.com/gregorydickson/memory-graph/blob/main/docs/CLAUDE_CODE_SETUP.md)
- **Full Mode Guide**: [Advanced Features](https://github.com/gregorydickson/memory-graph/blob/main/docs/FULL_MODE.md)
- **Issues & Support**: https://github.com/gregorydickson/memory-graph/issues

## 🌟 Why I Built This

Working with AI coding agents is powerful, but they forget everything between sessions. I wanted to give Claude a memory that:
- Persists across sessions
- Understands relationships between concepts
- Gets smarter over time as you use it
- Works with any MCP-compatible agent

MemoryGraph makes that possible.

## 🤝 Try It Out!

I'd love feedback from the community:
- What memory features would be most useful for your workflow?
- What backends are you interested in (SQLite, Neo4j, Memgraph)?
- What integrations would you like to see?

Install it, try it out, and let me know what you think! Issues, PRs, and feature requests are all welcome.

## 📝 Next Steps

Coming in future versions:
- Import/export functionality
- Workflow automation
- Enhanced analytics
- Proactive memory suggestions
- Multi-user support

---

**Install**: `pip install memorygraphMCP`

**Star the repo** if you find this useful! ⭐

Happy remembering! 🧠
