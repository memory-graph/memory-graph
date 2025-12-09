<p align="center">
  <img src="docs/html/logo-220.png" alt="MemoryGraph Logo" width="220">
</p>

<h1 align="center">MemoryGraph</h1>

<p align="center">
  <strong>Graph-based MCP Memory Server for AI Coding Agents</strong>
</p>

<p align="center">
  <a href="https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml"><img src="https://github.com/gregorydickson/memory-graph/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://pypi.org/project/memorygraphMCP/"><img src="https://img.shields.io/pypi/v/memorygraphMCP" alt="PyPI MCP"></a>
  <a href="https://pypi.org/project/memorygraphsdk/"><img src="https://img.shields.io/pypi/v/memorygraphsdk" alt="PyPI SDK"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python"></a>
  <a href="docs/CONFIGURATION.md"><img src="https://img.shields.io/badge/setup-zero--config-green" alt="Zero Config"></a>
  <a href="docs/CONFIGURATION.md"><img src="https://img.shields.io/badge/backends-8%20options-purple" alt="8 Backends"></a>
</p>

<p align="center">
  A graph-based <a href="https://modelcontextprotocol.io">Model Context Protocol (MCP)</a> server that gives AI coding agents persistent memory.<br>
  Store patterns, track relationships, retrieve knowledge across sessions.
</p>

---

## Quick Start

### Claude Code CLI (30 seconds)

```bash
# 1. Install (will use default SQLite database)
pipx install memorygraphMCP

# 1b. Optionally, you can specify a backend
pipx install "memorygraphMCP[falkordblite]"

# 2. Add to Claude Code (see docs/quickstart/ for other coding agents)
claude mcp add --scope user memorygraph -- memorygraph

# 3. Restart Claude Code (exit and run 'claude' again)
```

**Verify it works:**
```bash
claude mcp list  # Should show memorygraph with "Connected"
```

Then in your coding agent you can ask it to remember important items: *"Remember this for later: Use pytest for Python testing"*

![Memory Creation](docs/images/memory-creation.jpg)

> **Other MCP clients?** See [Supported Clients](#supported-mcp-clients) below.
>
> **Need pipx?** `pip install --user pipx && pipx ensurepath`
>
> **Command not found?** Run `pipx ensurepath` and restart your terminal.

**Important:** MemoryGraph provides memory tools, but your coding agent won't use them automatically. You need to prompt or configure it to store memories. See [Memory Best Practices](#memory-best-practices) below.

**Quick setup:** Add this to your `~/.claude/CLAUDE.md` or `AGENTS.md` to enable automatic memory storage:
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

See [CLAUDE.md Examples](docs/examples/CLAUDE_MD_EXAMPLES.md) for more configuration templates.

## Supported MCP Clients

MemoryGraph works with any MCP-compliant AI coding tool:

| Client | Type | Quick Start |
|--------|------|-------------|
| **Claude Code** | CLI/IDE | [Setup Guide](docs/CLAUDE_CODE_SETUP.md) |
| **Claude Desktop** | Desktop App | [Setup Guide](docs/quickstart/CLAUDE_DESKTOP.md) |
| **ChatGPT Desktop** | Desktop App | [Setup Guide](docs/quickstart/CHATGPT_DESKTOP.md) |
| **Cursor AI** | IDE | [Setup Guide](docs/quickstart/CURSOR_SETUP.md) |
| **Windsurf** | IDE | [Setup Guide](docs/quickstart/WINDSURF_SETUP.md) |
| **VS Code + Copilot** | IDE (1.102+) | [Setup Guide](docs/quickstart/VSCODE_COPILOT_SETUP.md) |
| **Continue.dev** | VS Code/JetBrains | [Setup Guide](docs/quickstart/CONTINUE_SETUP.md) |
| **Cline** | VS Code | [Setup Guide](docs/quickstart/CLINE_SETUP.md) |
| **Gemini CLI** | CLI | [Setup Guide](docs/quickstart/GEMINI_CLI_SETUP.md) |

See [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed compatibility info.

---

## Why MemoryGraph?

### Graph Relationships Make the Difference

Research shows that naive vector search degrades on long-horizon and temporal tasks. Benchmarks such as Deep Memory Retrieval (DMR) and LongMemEval were introduced precisely because graph-based systems excel at temporal queries ("what did the user decide last week"), cross-session reasoning, and multi-hop questions requiring explicit relational paths.

Graph memory captures entities, relationships, and temporal markers that traditional vector stores miss. For example: `Alice COMPLETED authentication_service`, `Bob BLOCKED_BY schema_conflicts` with timeline information about when events occurred.

**Flat storage** (CLAUDE.md, vector stores):
```
Memory 1: "Fixed timeout by adding retry logic"
Memory 2: "Retry logic caused memory leak"
Memory 3: "Fixed memory leak with connection pooling"
```
No connection between these - search finds them separately. Best for static rules and prime directives.

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
| Static rules, prime directives | Dynamic learnings with relationships |

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
| Memory Storage | 9 tools | 12 tools |
| Relationships | Yes | Yes |
| Session Briefings | Yes | Yes |
| Database Stats | - | Yes |
| Complex Queries | - | Yes |
| Contextual Search | - | Yes |
| Backend | SQLite | SQLite |
| Setup Time | 30 sec | 30 sec |

```bash
memorygraph                    # Core (default, 9 tools)
memorygraph --profile extended # Extended (12 tools)
```

### Core Mode (Default)

Provides all essential tools for daily use. Store memories, create relationships, search with fuzzy matching, and get session briefings. **This is all most users need.**

### When to Use Extended Mode

Switch to extended mode when you need:

- **Database statistics** (`get_memory_statistics`) - See total memories, breakdown by type, average importance scores, and graph metrics. Useful for understanding how your knowledge base is growing.

- **Complex relationship queries** (`search_relationships_by_context`) - Search relationships by structured context fields like scope, conditions, and evidence. Example: "Find all partial implementations" or "Show relationships with experimental evidence."

**Common extended mode scenarios:**
- Auditing your memory graph before a major refactor
- Analyzing patterns across hundreds of memories
- Finding all conditionally-applied solutions
- Generating reports on project knowledge coverage

```bash
# Enable extended mode in Claude Code
claude mcp add --scope user memorygraph -- memorygraph --profile extended
```

See [TOOL_PROFILES.md](docs/TOOL_PROFILES.md) for complete tool list and details.

---

## Installation Options

### pipx (Recommended)

```bash
pipx install memorygraphMCP                      # Core mode (default, SQLite)
pipx install "memorygraphMCP[neo4j]"             # With Neo4j backend support
pipx install "memorygraphMCP[falkordblite]"      # With FalkorDBLite backend (embedded)
pipx install "memorygraphMCP[ladybugdb]"         # With LadybugDB backend (embedded)
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

See [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed options.

---

## Claude Code Web Support

MemoryGraph works in Claude Code Web (remote) environments via project hooks.

### Quick Setup

Copy the hook files to your project:

```bash
# From memorygraph repo
cp -r examples/claude-code-hooks/.claude /path/to/your/project/

# Commit to your repo
cd /path/to/your/project
git add .claude/
git commit -m "Add MemoryGraph auto-install hooks"
```

When you open this project in Claude Code Web, MemoryGraph installs automatically.

### Persistent Storage (Optional)

Remote environments are ephemeral. For persistent memories, configure cloud storage
in your Claude Code Web environment variables:

| Variable | Description |
|----------|-------------|
| `MEMORYGRAPH_API_KEY` | API key from memorygraph.dev (coming soon) |
| `MEMORYGRAPH_TURSO_URL` | Your Turso database URL |
| `MEMORYGRAPH_TURSO_TOKEN` | Your Turso auth token |

See [Claude Code Web Setup](docs/claude-code-web.md) for detailed instructions.

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

# Cloud backend (multi-device sync, zero setup)
claude mcp add --scope user memorygraph \
  --env MEMORYGRAPH_API_KEY=mg_your_key_here \
  -- memorygraph --backend cloud
```

> **Get your API key**: Sign up at [memorygraph.dev](https://memorygraph.dev) to get your free API key.

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

MemoryGraph supports 8 backend options to fit your deployment needs:

| Backend | Type | Config | Native Graph | Zero-Config | Best For |
|---------|------|--------|--------------|-------------|----------|
| **sqlite** | Embedded | File path | No (simulated) | ✅ | Default, simple use |
| **falkordblite** | Embedded | File path | ✅ Cypher | ✅ | Graph queries without server |
| **ladybugdb** | Embedded | File path | ✅ Cypher | ✅ | Graph queries without server |
| **falkordb** | Client-server | Host:port | ✅ Cypher | ❌ | High-performance production |
| **neo4j** | Client-server | URI | ✅ Cypher | ❌ | Enterprise features |
| **memgraph** | Client-server | Host:port | ✅ Cypher | ❌ | Real-time analytics |
| **turso** | Cloud | URL + Token | No (simulated) | ❌ | Distributed SQLite, edge deployments |
| **cloud** | Cloud | API Key | ✅ Cypher | ❌ | MemoryGraph Cloud (production ready) |

**New: FalkorDB Options**
- **FalkorDBLite**: Zero-config embedded database with native Cypher support, perfect upgrade from SQLite
- **LadybugDB**: Leading columnar embedded graph database with Cypher support
- **FalkorDB**: Redis-based graph DB with 500x faster p99 than Neo4j ([docs](https://docs.falkordb.com/))

**New: Cloud Backend**
- **Multi-device sync**: Access your memories from anywhere
- **Team collaboration**: Share memories with your team
- **Automatic backups**: Never lose your knowledge graph
- **Zero maintenance**: No database setup required

See [CONFIGURATION.md](docs/CONFIGURATION.md) for setup details and [Cloud Backend Guide](docs/CLOUD_BACKEND.md) for cloud-specific configuration.

---

## Multi-Tenancy (v0.10.0+)

MemoryGraph now supports optional multi-tenancy for team memory sharing and organizational deployments. Phase 1 provides the foundational schema with 100% backward compatibility.

**Key Features:**
- **Optional**: Disabled by default, zero impact on existing single-tenant deployments
- **Tenant Isolation**: Scope memories to specific organizations/teams
- **Visibility Levels**: Control access with `private`, `project`, `team`, or `public` visibility
- **Migration Support**: Migrate existing databases with built-in CLI command
- **Performance Optimized**: Conditional indexes only created when multi-tenant mode is enabled

**Quick Start:**
```bash
# Migrate existing database to multi-tenant mode
memorygraph migrate-to-multitenant --tenant-id="acme-corp" --dry-run

# Enable multi-tenant mode
export MEMORY_MULTI_TENANT_MODE=true
memorygraph
```

**Use Cases:**
- Team collaboration and shared memory
- Multi-team organizations
- Department-specific knowledge bases
- Enterprise deployments

See [MULTI_TENANCY.md](docs/MULTI_TENANCY.md) for complete guide including architecture, migration steps, and usage patterns.

**Roadmap:**
- ✅ Phase 1 (v0.10.0): Schema enhancement with optional tenant fields
- Phase 2 (v0.11.0): Query filtering and visibility enforcement
- Phase 3 (v1.0.0): Authentication integration (JWT, OAuth2)
- Phase 4 (v1.1.0): Advanced RBAC and audit logging

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
│   ├── backends/        # SQLite, Neo4j, Memgraph, FalkorDB, Turso, Cloud
│   ├── migration/       # Backend-to-backend migration
│   └── tools/           # Tool implementations
├── tests/               # 1,068 tests
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
# Option A: Use full path to avoid venv conflicts (recommended)
claude mcp add memorygraph -- ~/.local/bin/memorygraph

# Option B: Create symlink for cleaner config (requires sudo once)
sudo ln -s ~/.local/bin/memorygraph /usr/local/bin/memorygraph
# Then use simple command
claude mcp add memorygraph -- memorygraph
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

## What's New in v0.11.0

### Python SDK for Agent Frameworks

**NEW:** `memorygraphsdk` - Native integrations for popular AI frameworks!

```bash
pip install memorygraphsdk[all]  # All integrations
```

| Framework | Integration | Description |
|-----------|-------------|-------------|
| **LlamaIndex** | `MemoryGraphChatMemory`, `MemoryGraphRetriever` | Chat memory + RAG retrieval |
| **LangChain** | `MemoryGraphMemory` | BaseMemory with session support |
| **CrewAI** | `MemoryGraphCrewMemory` | Multi-agent persistent memory |
| **AutoGen** | `MemoryGraphAutoGenHistory` | Conversation history |

```python
from memorygraphsdk import MemoryGraphClient

client = MemoryGraphClient(api_key="mg_...")
memory = client.create_memory(
    type="solution",
    title="Fixed Redis timeout",
    content="Used exponential backoff",
    tags=["redis", "fix"]
)
```

See [SDK Documentation](sdk/README.md) for full integration guides.

---

## What's New in v0.10.0

### Context Budget Optimization (60-70% token savings)
- **Leaner tool profiles** - Removed 29 unimplemented tools, keeping only production-ready features
- **9 core tools / 12 extended** - Focused toolset that fits in any context window
- **~40k tokens saved** - More room for your actual work
- **ADR-017** - Context budget as architectural constraint ([docs/adr/017-context-budget-constraint.md](docs/adr/017-context-budget-constraint.md))

### Cloud Backend (Production Ready)
- **Multi-device sync** - Access memories from anywhere
- **Circuit breaker pattern** - Resilient to network failures with automatic recovery
- **Zero setup** - Just add your API key from [memorygraph.dev](https://memorygraph.dev)
- **Team collaboration ready** - Share knowledge graphs with your team

```bash
# Enable cloud backend
claude mcp add --scope user memorygraph \
  --env MEMORYGRAPH_API_KEY=mg_your_key_here \
  -- memorygraph --backend cloud
```

### Bi-Temporal Memory Tracking
- **Time-travel queries** - Query what was known at any point in time
- **Knowledge evolution** - Track how solutions and understanding changed
- **Four temporal fields** - `valid_from`, `valid_until`, `recorded_at`, `invalidated_by`
- **Migration support** - Upgrade existing databases with `migrate_to_bitemporal()`
- **Inspired by Graphiti** - Learned from Zep AI's proven temporal model

```python
# Query what solutions existed in March 2024
march_2024 = datetime(2024, 3, 1, tzinfo=timezone.utc)
relationships = await db.get_related_memories("error_id", as_of=march_2024)

# Get full history of how understanding evolved
history = await db.get_relationship_history("problem_id")

# See what changed in the last week
changes = await db.what_changed(since=one_week_ago)
```

### Semantic Navigation
- **Contextual search** - LLM-powered graph traversal without embeddings
- **Graph-first approach** - Validated by Cipher's shift away from vector search
- **Scoped queries** - Search within related memory contexts

See [temporal-memory.md](docs/temporal-memory.md) for comprehensive temporal tracking guide and [CLOUD_BACKEND.md](docs/CLOUD_BACKEND.md) for cloud setup.

---

## What's New in v0.9.5

### Cloud Backend & Turso Support
- **MemoryGraph Cloud** - REST API client with circuit breaker for resilience (coming soon)
- **Turso Backend** - Distributed SQLite with embedded replica support for edge deployments
- **8 total backends** - sqlite, neo4j, memgraph, falkordb, falkordblite, ladybugdb, turso, cloud

### Backend Migration
- **`memorygraph migrate`** - Migrate data between any two backends
- **5-phase validation** - Pre-flight checks, export, validate, import, verify
- **Dry-run mode** - Test migrations without writing data
- **Rollback support** - Automatic cleanup on failure

```bash
# Migrate from SQLite to FalkorDB
memorygraph migrate --from sqlite --to falkordb --to-uri redis://localhost:6379

# Test migration first
memorygraph migrate --from sqlite --to neo4j --dry-run
```

### Universal Export/Import
- **Works with ALL backends** - Export from any backend, import to any backend
- **Progress reporting** - Track long-running operations
- **Format v2.0** - Enhanced metadata with backend info and counts

```bash
memorygraph export --format json --output backup.json
memorygraph import --format json --input backup.json --skip-duplicates
```

### Architecture Improvements
- **Circuit breaker** - Prevents cascading failures in cloud backend
- **Thread-safe backend creation** - Safe for concurrent migrations
- **Async correctness** - All Turso operations properly non-blocking

## What's New in v0.9.0

### Pagination & Cycle Detection
- **Result pagination** for large datasets with `limit` and `offset` parameters
- **Cycle detection** prevents circular relationships by default

### Health Check CLI
- **Quick diagnostics** with `memorygraph --health`
- **JSON output** with `--health-json` for scripting

---

## Roadmap

### Current (v0.11.0) ✅
- **Python SDK** - `memorygraphsdk` with LlamaIndex, LangChain, CrewAI, AutoGen integrations
- **Cloud Backend** - Multi-device sync via memorygraph.dev
- **Bi-temporal tracking** - Track knowledge evolution over time
- **Semantic navigation** - LLM-powered contextual search
- 8 backend options (SQLite, Neo4j, Memgraph, FalkorDB, FalkorDBLite, LadybugDB, Turso, Cloud)
- 1,200+ tests passing
- Two PyPI packages: `memorygraphMCP` + `memorygraphsdk`

### Planned (v1.0+)
- Real-time team sync
- Multi-tenancy features
- Enhanced SDK documentation

See [PRODUCT_ROADMAP.md](docs/planning/PRODUCT_ROADMAP.md) for details.

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
