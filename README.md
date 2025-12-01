# MemoryGraph

## MCP Memory Server for AI Coding Agents

[![Tests](https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml/badge.svg)](https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/memorygraph)](https://pypi.org/project/memorygraph/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Zero Config](https://img.shields.io/badge/setup-zero--config-green)](docs/DEPLOYMENT.md)
[![5 Backends](https://img.shields.io/badge/backends-5%20options-purple)](docs/DEPLOYMENT.md)

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

**Important:** MemoryGraph provides memory tools, but Claude won't use them automatically. You need to prompt Claude or configure it to store memories. See [Memory Best Practices](#memory-best-practices) below.

**Quick setup:** Add this to your `~/.claude/CLAUDE.md` to enable automatic memory storage:
```markdown
## Memory Protocol
After completing significant tasks, store a memory with:
- Type: solution, problem, code_pattern, etc.
- Title: Brief description
- Content: What was accomplished, key decisions, patterns discovered
- Tags: Relevant keywords for future recall
- Relationships: Link to related memories (problems solved, patterns used)

Before starting work, use `recall_memories` to check for relevant past learnings.
```

See [CLAUDE.md Examples](docs/examples/CLAUDE_MD_EXAMPLES.md) for more configuration templates.

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

| Feature | Core (Default) | Extended |
|---------|----------------|----------|
| Memory Storage | 9 tools | 11 tools |
| Relationships | Yes | Yes |
| Session Briefings | Yes | Yes |
| Database Stats | - | Yes |
| Complex Queries | - | Yes |
| Backend | SQLite | SQLite |
| Setup Time | 30 sec | 30 sec |

```bash
memorygraph                    # Core (default, 9 tools)
memorygraph --profile extended # Extended (11 tools)
```

**Core mode** provides all essential tools for daily use and works for 95% of users.
**Extended mode** adds database statistics and complex relationship queries for power users.

See [TOOL_PROFILES.md](docs/TOOL_PROFILES.md) for complete tool list and details.

---

## Installation Options

### pipx (Recommended)

```bash
pipx install memorygraphMCP                      # Core mode (default, SQLite)
pipx install "memorygraphMCP[neo4j]"             # With Neo4j backend support
pipx install "memorygraphMCP[falkordblite]"      # With FalkorDBLite backend (embedded)
pipx install "memorygraphMCP[falkordb]"          # With FalkorDB backend (client-server)
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
# Core mode (default)
claude mcp add --scope user memorygraph -- memorygraph

# Extended mode
claude mcp add --scope user memorygraph -- memorygraph --profile extended

# Extended mode with Neo4j backend
claude mcp add --scope user memorygraph \
  --env MEMORY_NEO4J_URI=bolt://localhost:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=password \
  -- memorygraph --profile extended --backend neo4j
```

### Other MCP Clients

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

See [CONFIGURATION.md](docs/CONFIGURATION.md) for all options.

### Recommended: Add to CLAUDE.md

For best results, add this to your `CLAUDE.md` or project instructions:

```markdown
## Memory Tools
When recalling past work or learnings, always start with `recall_memories`
before using `search_memories`. The recall tool has optimized defaults
for natural language queries (fuzzy matching, relationship context included).
```

This helps Claude use the optimal tool for memory recall.

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

### Recall Memories (Recommended)

```json
{
  "tool": "recall_memories",
  "query": "authentication security"
}
```

Returns fuzzy-matched results with relationship context and match quality hints.

### Search Memories (Advanced)

```json
{
  "tool": "search_memories",
  "query": "authentication",
  "search_tolerance": "strict",
  "limit": 5
}
```

Use when you need exact matching or advanced filtering.

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

## Memory Best Practices

### Why Memories Aren't Automatic

MemoryGraph is an MCP tool provider, not an autonomous agent. This means:
- **Claude needs to be prompted** to use the memory tools
- **You control what gets stored** - nothing is saved without explicit instruction
- **Configuration is key** - Add memory protocols to your CLAUDE.md for consistent behavior

This design gives you full control over your memory graph, but requires setup to work effectively.

### How to Encourage Memory Creation

#### 1. Configure CLAUDE.md (Recommended)

Add a memory protocol to `~/.claude/CLAUDE.md` for persistent behavior across all sessions:

```markdown
## Memory Protocol

### Storage Guidelines
After completing significant tasks, store a memory using `store_memory`:
- **Type**: Choose appropriate type (solution, problem, code_pattern, decision, etc.)
- **Title**: Brief, descriptive (e.g., "Fixed Redis timeout with connection pooling")
- **Content**: Include:
  - What was accomplished
  - Why this approach was chosen
  - Key decisions and trade-offs
  - Context that makes it reusable
- **Tags**: Add relevant keywords (technology, domain, pattern name)
- **Relationships**: Link to related memories using `create_relationship`:
  - Solutions SOLVE problems
  - Fixes ADDRESS errors
  - Patterns APPLY_TO projects
  - Decisions IMPROVE previous approaches

### Recall Guidelines
Before starting work on a topic, use `recall_memories` to check for:
- Past solutions to similar problems
- Known issues and their fixes
- Established patterns and conventions
- Previous decisions and their rationale

### Session Wrap-Up
At the end of each session, store a summary memory:
- Type: task
- Content: What was accomplished, what's next
- Tags: project name, session date
```

#### 2. Use Trigger Phrases

Claude responds well to explicit memory-related requests:

**For storing**:
- "Store this for later..."
- "Remember that..."
- "Save this pattern..."
- "Record this decision..."
- "Create a memory about..."

**For recalling**:
- "What do you remember about...?"
- "Have we solved this before?"
- "Recall any patterns for..."
- "What did we decide about...?"

**For session management**:
- "Summarize and store what we accomplished today"
- "Store a summary of this session"
- "Catch me up on this project" (uses stored memories)

#### 3. Establish Workflow Habits

**Start of session**:
```
You: "What do you remember about the authentication system?"
Claude: [Uses recall_memories to find relevant context]
```

**During work**:
```
You: "We fixed the Redis timeout by increasing the connection pool to 50. Store this solution."
Claude: [Uses store_memory, then create_relationship to link to the problem]
```

**End of session**:
```
You: "Store a summary of what we accomplished today"
Claude: [Creates a task-type memory with summary and links]
```

#### 4. Project-Specific Configuration

For team projects or specific repositories, add `.claude/CLAUDE.md` to the project:

```markdown
## Project Memory Protocol

This project uses MemoryGraph for team knowledge sharing.

### When to Store
- Solutions to project-specific problems
- Architecture decisions and rationale
- Deployment procedures and gotchas
- Performance optimizations
- Bug fixes and root causes

### Tagging Convention
Always include these tags:
- Project name: "my-app"
- Component: "auth", "api", "database", etc.
- Type: "fix", "feature", "optimization", etc.

### Example
When fixing a bug:
1. Store the problem (type: problem)
2. Store the solution (type: solution)
3. Link them: solution SOLVES problem
4. Tag both with component and "bug-fix"
```

### Memory Types Guide

Choose the right type for better organization:

| Type | Use For | Example |
|------|---------|---------|
| **solution** | Working fixes and implementations | "Fixed N+1 query with eager loading" |
| **problem** | Issues encountered | "Database deadlock under high concurrency" |
| **code_pattern** | Reusable patterns | "Repository pattern for database access" |
| **decision** | Architecture choices | "Chose PostgreSQL over MongoDB for transactions" |
| **task** | Work completed | "Implemented user authentication" |
| **technology** | Tool/framework knowledge | "FastAPI dependency injection best practices" |
| **error** | Specific errors | "ImportError: module not found" |
| **fix** | Error resolutions | "Added missing import statement" |

### Relationship Types Guide

Common relationship patterns:

```markdown
# Causal relationships
problem --CAUSES--> error
change --TRIGGERS--> bug

# Solution relationships
solution --SOLVES--> problem
fix --ADDRESSES--> error
pattern --IMPROVES--> code

# Context relationships
pattern --APPLIES_TO--> project
solution --REQUIRES--> dependency
pattern --WORKS_WITH--> technology

# Learning relationships
new_approach --BUILDS_ON--> old_approach
finding --CONTRADICTS--> assumption
result --CONFIRMS--> hypothesis
```

### Example Workflows

**Debugging workflow**:
```
1. Encounter error → Store as type: error
2. Find root cause → Store as type: problem, link: error TRIGGERS problem
3. Implement fix → Store as type: solution, link: solution SOLVES problem
4. Result: Complete chain for future reference
```

**Feature development workflow**:
```
1. Start: "Recall any patterns for user authentication"
2. Implement: [Work on feature]
3. Store: "Store this authentication pattern" → type: code_pattern
4. Link: pattern APPLIES_TO project
5. End: "Store summary of authentication implementation"
```

**Optimization workflow**:
```
1. Identify issue → Store as type: problem
2. Test solutions → Store each as type: solution
3. Compare → Link: best_solution IMPROVES other_solutions
4. Document → Store decision with rationale
```

### More Examples and Templates

For comprehensive CLAUDE.md configuration examples including:
- Domain-specific setups (web dev, ML, DevOps)
- Team collaboration protocols
- Migration strategies from other systems

See: [CLAUDE.md Configuration Examples](docs/examples/CLAUDE_MD_EXAMPLES.md)

---

## Backends

MemoryGraph supports 5 backend options to fit your deployment needs:

| Backend | Type | Config | Native Graph | Zero-Config | Best For |
|---------|------|--------|--------------|-------------|----------|
| **sqlite** | Embedded | File path | No (simulated) | ✅ | Default, simple use |
| **falkordblite** | Embedded | File path | ✅ Cypher | ✅ | Graph queries without server |
| **falkordb** | Client-server | Host:port | ✅ Cypher | ❌ | High-performance production |
| **neo4j** | Client-server | URI | ✅ Cypher | ❌ | Enterprise features |
| **memgraph** | Client-server | Host:port | ✅ Cypher | ❌ | Real-time analytics |

**New: FalkorDB Options**
- **FalkorDBLite**: Zero-config embedded database with native Cypher support, perfect upgrade from SQLite
- **FalkorDB**: Redis-based graph DB with 500x faster p99 than Neo4j ([docs](https://docs.falkordb.com/))

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for setup details.

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
│   ├── server.py        # MCP server (11 tools)
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

### Current (v0.7.1+)
- SQLite default backend
- Two-tier profiles (core/extended)
- 11 fully implemented MCP tools
- 93% test coverage
- PyPI + Docker

### Planned (v1.0+)
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
