# Claude Code Setup Guide

Step-by-step guide to integrate MemoryGraph with Claude Code.

## Table of Contents

1. [Understanding Claude Code Interfaces](#understanding-claude-code-interfaces)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [MCP Configuration](#mcp-configuration)
5. [Verifying Connection](#verifying-connection)
6. [First Memory](#first-memory)
7. [Upgrading to Extended Mode](#upgrading-to-extended-mode)
8. [Troubleshooting](#troubleshooting)
9. [Usage Tips](#usage-tips)

---

## Understanding Claude Code Interfaces

Claude Code is available in multiple interfaces. **MCP server support and configuration methods vary by interface**:

| Interface | MCP Support | Configuration Method |
|-----------|-------------|----------------------|
| **Claude Code CLI** | ✅ Full support | `claude mcp add` command (recommended) |
| **VS Code Extension** | ✅ Full support | Manual JSON config in VS Code settings |
| **Desktop App** | ✅ Full support | Manual JSON config in app settings |
| **Web (Beta)** | ⚠️ Limited/TBD | May not support custom MCP servers yet |

**This guide primarily covers Claude Code CLI** (using `claude mcp add` command). For other interfaces, see the [Manual Configuration](#manual-configuration-not-recommended) section.

---

## Quick Start

### For Claude Code CLI

Get up and running in 3 steps:

```bash
# 1. Install with pipx (recommended - handles PATH automatically)
pipx install memorygraphMCP

# 2. Add to Claude Code CLI
# User scope (global - recommended to start)
claude mcp add --transport stdio memorygraph memorygraph

# OR Project scope (local to current directory)
claude mcp add --transport stdio memorygraph memorygraph --scope project

# 3. Restart Claude Code CLI
```

> **Alternative**: If Python bin is already in your PATH: `pip install memorygraphMCP`
>
> **Don't have pipx?** Install it first: `pip install --user pipx && pipx ensurepath` (one-time setup)

**Which scope should I use?**
- **User scope** (default): If you want memory available everywhere across all projects
- **Project scope**: If you want project-specific memory or different configurations per project

### For Other Claude Code Interfaces

See [MCP Configuration](#mcp-configuration) section below for interface-specific instructions.

---

## Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Claude Code**: Latest version with MCP support
- **pip**: Python package installer (for pipx installation)

Check prerequisites:
```bash
python3 --version  # Should be 3.10+
pip --version      # Should be installed
```

### Install the Package

**Recommended: pipx (Handles PATH automatically)**

```bash
# Install pipx if you don't have it (one-time setup)
pip install --user pipx
pipx ensurepath

# Then install memorygraph
pipx install memorygraphMCP

# With intelligence features (standard mode)
pipx install "memorygraphMCP[intelligence]"

# Full power with Neo4j
pipx install "memorygraphMCP[neo4j,intelligence]"
```

**Why pipx?**
- ✅ Automatic PATH configuration
- ✅ Isolated environment (no dependency conflicts)
- ✅ Standard for Python CLI tools
- ✅ Easy upgrades and uninstalls

**Alternative: pip (If Python bin already in your PATH)**

```bash
# Basic installation (SQLite, lite mode)
pip install memorygraphMCP

# With intelligence features (standard mode)
pip install "memorygraphMCP[intelligence]"

# Full power with Neo4j
pip install "memorygraphMCP[neo4j,intelligence]"
```

Use this if you've already configured Python's bin directory in your PATH.

### Verify Installation

```bash
# Check version
memorygraph --version
# Should show: memorygraph v1.0.0

# Check configuration
memorygraph --show-config
# Should show default settings
```

## MCP Configuration

### For Claude Code CLI: Use `claude mcp add` Command

According to the [official Claude Code documentation](https://code.claude.com/docs/en/mcp), the **recommended and official way** to configure MCP servers for **Claude Code CLI** is using the `claude mcp add` command. Manual JSON editing is not the intended workflow for CLI users.

### Understanding Claude Code's Configuration Files

Claude Code uses multiple configuration files with different purposes. **This is admittedly messy**, and Anthropic is aware of the documentation issues.

| File | Purpose | Scope | What Goes Here |
|------|---------|-------|----------------|
| **`.mcp.json`** | Project MCP servers | Local/Project | Server configurations for specific project (created by `claude mcp add --scope project` or `--scope local`) |
| **`~/.claude.json`** | Global MCP servers | User/Global | User-level server configurations (created by `claude mcp add` or `claude mcp add --scope user`) |
| **`~/.claude/settings.json`** | Permissions & behavior | User/Global | `enabledMcpjsonServers`, permissions, tool behavior settings (NOT for MCP server definitions) |

### Key Takeaways

✅ **DO**:
- Use `claude mcp add` command (official method)
- Let the CLI manage configuration files for you
- Use `--scope user` (or omit `--scope`) for servers available across all projects
- Use `--scope project` (or `--scope local`) for project-specific servers
- Choose scope based on whether you want shared or isolated server instances

❌ **DON'T**:
- Put MCP servers in `~/.claude/settings.json` - **it won't work**
- Manually edit `.mcp.json` or `~/.claude.json` unless absolutely necessary
- Try to manually manage the "chaotic grab bag" of legacy global settings
- Forget to specify `--scope project` if you want project-local configuration

**Why this matters**: The configuration system is complex and has legacy files. Using `claude mcp add` ensures your MCP servers are configured in the correct location and format.

**Prerequisites**: You must have already installed MemoryGraph via pip (see [Installation](#installation) section above). The `claude mcp add` command configures Claude Code to use the already-installed `memorygraph` command.

---

### Configuration Examples

#### Understanding Scopes

MCP servers can be configured at two different scopes:

| Scope | Where Configured | When to Use |
|-------|------------------|-------------|
| **User/Global** | `~/.claude.json` | Server available across all projects and directories |
| **Local/Project** | `.mcp.json` in current directory | Server only available in specific project |

**Default behavior**: Without `--scope`, servers are added at **user** scope (global).

#### User/Global Scope Configuration

**Recommended for**: Servers you want available everywhere (memory, filesystem, time, etc.)

Servers available across all projects:

```bash
# Prerequisite: pipx install memorygraphMCP (must be run first)
# Default (user scope - available globally)
claude mcp add --transport stdio memorygraph memorygraph

# Or explicitly specify user scope
claude mcp add --transport stdio memorygraph memorygraph --scope user
```

This configuration:
- Creates/updates `~/.claude.json`
- Available in all projects and directories
- Uses SQLite backend (zero config)
- Lite profile (8 core tools)
- Default database path: `~/.memorygraph/memory.db`

#### Local/Project Scope Configuration

**Recommended for**: Project-specific servers with custom configuration or project-specific data

Creates `.mcp.json` in your current directory:

```bash
# Prerequisite: pipx install memorygraphMCP (must be run first)
# Project scope - only available in this project
claude mcp add --transport stdio memorygraph memorygraph --scope project

# Alternative syntax (same result)
claude mcp add --transport stdio memorygraph memorygraph --scope local
```

This configuration:
- Creates `.mcp.json` in current directory
- Only available when working in this directory
- Useful for project-specific database paths or profiles
- Can be committed to git for team sharing

#### Practical Examples by Scope

**Example 1: Global memory server (user scope)**
```bash
# Prerequisite: pipx install memorygraphMCP (must be run first)
# Add memory globally - available in all projects
claude mcp add --transport stdio memorygraph memorygraph --scope user
```
Use when: You want one shared memory across all your work.

**Example 2: Project-specific memory (local scope)**
```bash
# Prerequisite: pipx install memorygraphMCP (must be run first)
# Navigate to your project directory first
cd /path/to/my-project

# Add memory for this project only
claude mcp add --transport stdio memorygraph memorygraph --scope project \
  --env MEMORY_SQLITE_PATH=./.memory/project.db
```
Use when: Each project should have isolated memory (e.g., team projects, client work).

**Example 3: Different profiles per project**
```bash
# Global: Lite profile for general use
claude mcp add --transport stdio memorygraph memorygraph --scope user

# Project A: Standard profile with intelligence
cd /path/to/project-a
claude mcp add --transport stdio memorygraph-ai memorygraph --scope project --profile extended

# Project B: Full profile with Neo4j
cd /path/to/project-b
claude mcp add --transport stdio memorygraph-full memorygraph --scope project --profile extended \
  --env MEMORY_NEO4J_URI=bolt://localhost:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=your-password
```
Use when: Different projects need different capabilities.

#### Standard Configuration (Pattern Recognition)

```bash
# Prerequisite: pipx install "memorygraphMCP[intelligence]" (must be run first)
# User scope (global)
claude mcp add --transport stdio memorygraph memorygraph --profile extended

# Or project scope
claude mcp add --transport stdio memorygraph memorygraph --scope project --profile extended
```

This adds:
- Pattern recognition
- Intelligence features
- 11 tools total

#### Full Configuration (SQLite)

```bash
# Prerequisite: pipx install "memorygraphMCP[intelligence]" (must be run first)
claude mcp add --transport stdio memorygraph memorygraph --profile extended
```

This enables:
- 11 tools total
- Graph analytics
- Advanced features

#### Full Configuration (Neo4j)

```bash
# Prerequisite: pipx install "memorygraphMCP[neo4j,intelligence]" (must be run first)
claude mcp add --transport stdio memorygraph memorygraph --profile extended --backend neo4j \
  --env MEMORY_NEO4J_URI=bolt://localhost:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=your-password
```

This enables:
- 11 tools total
- Neo4j backend
- Graph analytics
- Advanced features

#### Custom Database Path

```bash
# Prerequisite: pipx install memorygraphMCP (must be run first)
# User scope with custom path
claude mcp add --transport stdio memorygraph memorygraph --scope user \
  --env MEMORY_SQLITE_PATH=/path/to/your/custom/memory.db \
  --env MEMORY_LOG_LEVEL=DEBUG

# Or project scope with relative path
claude mcp add --transport stdio memorygraph memorygraph --scope project \
  --env MEMORY_SQLITE_PATH=./.memory/memory.db \
  --env MEMORY_LOG_LEVEL=DEBUG
```

#### Additional MCP Server Examples

These examples show general `claude mcp add` usage patterns for any MCP server:

**Adding with environment variables (user scope):**
```bash
# GitHub server globally available
claude mcp add github --scope user --env GITHUB_TOKEN=ghp_xxx -- npx -y @modelcontextprotocol/server-github

# Multiple environment variables
claude mcp add postgres --scope user \
  --env DB_HOST=localhost \
  --env DB_PORT=5432 \
  --env DB_NAME=mydb \
  -- npx -y @modelcontextprotocol/server-postgres
```

**Adding HTTP/remote servers:**
```bash
# HTTP transport (user scope)
claude mcp add sentry --transport http --scope user https://mcp.sentry.dev/mcp

# HTTP transport (project scope)
claude mcp add api-server --transport http --scope project http://localhost:8080/mcp
```

**Adding from JSON configuration:**
```bash
# User scope JSON
claude mcp add-json memory --scope user '{"command":"npx","args":["-y","@modelcontextprotocol/server-memory"]}'

# Project scope JSON
claude mcp add-json memory --scope project '{"command":"npx","args":["-y","@modelcontextprotocol/server-memory"]}'
```

#### Verify Installation

```bash
# List all MCP servers (both user and project scope)
claude mcp list

# Get details for specific server
claude mcp get memorygraph

# Remove a server (specify scope if needed)
claude mcp remove memorygraph --scope user
claude mcp remove memorygraph --scope project
```

---

### Manual Configuration

**For Claude Code CLI users**: Use `claude mcp add` instead (see above).

**For other Claude Code interfaces** (VS Code extension, Desktop app): Manual configuration is required as the `claude mcp add` command is CLI-specific.

#### Configuration by Interface

**VS Code Extension**:
- MCP servers are configured via VS Code settings
- Location: `.vscode/settings.json` or User Settings
- See [VS Code MCP documentation](https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-code) for details

**Desktop App**:
- MCP servers are configured via app settings/preferences
- Configuration UI available in app settings
- May also support JSON config file (check app documentation)

**Web (Beta)**:
- MCP server support may be limited or unavailable
- Check [Claude Code documentation](https://code.claude.com/docs) for current status

#### Manual JSON Configuration Reference

If you need to manually configure (non-CLI interfaces or other MCP clients):

#### Manual Configuration Reference

**⚠️ Warning**: This section is provided for reference only. The configuration system has legacy files and known complexity issues.

**For Claude Code users**: Just use `claude mcp add` and avoid this entirely.

**For other MCP clients**: You'll need to manually configure based on your client's documentation.

**Common Mistake**: Don't put MCP server definitions in `~/.claude/settings.json` - they go in `.mcp.json` (project) or `~/.claude.json` (global).

#### Minimal Configuration (Recommended to Start)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

This uses:
- SQLite backend (zero config)
- Lite profile (8 core tools)
- Default database path: `~/.memorygraph/memory.db`

#### Standard Configuration

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

This adds:
- Pattern recognition
- Intelligence features
- 11 tools total

#### Full Configuration (Neo4j)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "extended"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://localhost:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
```

This enables:
- 11 tools total
- Graph analytics
- Advanced features

---

#### uvx Configuration (Advanced - Not Recommended)

**⚠️ Warning**: This configuration is **not recommended** for production MCP servers. Use `pip install memorygraphMCP` instead.

If you insist on using uvx (for testing purposes only):

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "uvx",
      "args": ["memorygraph"],
      "env": {
        "MEMORY_SQLITE_PATH": "/Users/yourname/.memorygraph/memory.db",
        "MEMORY_TOOL_PROFILE": "core"
      }
    }
  }
}
```

**Limitations of uvx with MCP**:
- ❌ Slower startup (package download/cache check on every connection)
- ❌ Environment variables must be explicitly set in mcp.json
- ❌ Database path required (no default)
- ❌ Harder to debug connection issues
- ❌ Not suitable for production use

**Why this exists**: Useful for quickly testing different versions without reinstalling:
```json
{
  "mcpServers": {
    "memory-test-v1": {
      "command": "uvx",
      "args": ["memorygraph@1.0.0"]
    },
    "memory-test-v2": {
      "command": "uvx",
      "args": ["memorygraph@1.1.0"]
    }
  }
}
```

**Recommendation**: For daily use, install via pip and use the standard configurations above.

#### Step 3: Save and Restart

1. Save `mcp.json`
2. Restart Claude Code
3. Check for memory tools in Claude Code

---

## Verifying Connection

### Method 1: Ask Claude

Start a new conversation in Claude Code and ask:
```
Do you have access to memory tools?
```

Claude should respond with something like:
```
Yes, I have access to the following memory tools:
- store_memory
- get_memory
- search_memories
- [etc...]
```

### Method 2: Check Server Logs

If you set up logging:
```bash
# In MCP config, add:
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--log-level", "INFO"]
    }
  }
}
```

Check logs in Claude Code's output panel.

### Method 3: Manual Test

Run the server directly:
```bash
memorygraph --show-config
```

Should show:
```
MemoryGraph v1.0.0
Configuration:
  backend: sqlite
  tool_profile: lite
  sqlite_path: /Users/you/.memorygraph/memory.db
  log_level: INFO

Backend Status: ✓ Connected
Tools Enabled: 8/44
```

---

## First Memory

Let's store and retrieve your first memory!

### Step 1: Store a Memory

Ask Claude:
```
Store a memory: "Use bcrypt for password hashing in Python projects.
It's secure and well-maintained."
Tag it as: security, python, authentication
Memory type: CodePattern
```

Claude will use the `store_memory` tool and respond with:
```
I've stored that memory with ID: mem_abc123
```

### Step 2: Search for the Memory

Ask Claude:
```
Find all memories about authentication
```

Claude will use `search_memories` and show you the memory you just stored.

### Step 3: Create a Relationship

Store another memory:
```
Store a memory: "Never store passwords in plain text - always hash them."
Tag it as: security, best-practices
Memory type: Problem
```

Then link them:
```
Create a relationship between these two memories.
The bcrypt memory SOLVES the plain text password problem.
```

Claude will use `create_relationship`.

### Step 4: Find Related Memories

Ask Claude:
```
Show me memories related to password security
```

Claude will find both memories and their relationship!

---

## Upgrading to Extended Mode

### Why Upgrade?

Upgrade to extended mode when you need:
- Graph analytics (cluster analysis, path finding)
- Workflow automation
- Project integration (codebase scanning)
- Proactive suggestions
- Better performance at scale

### Prerequisites

1. **Set up Neo4j or Memgraph** (see [DEPLOYMENT.md](DEPLOYMENT.md))

**Quick Neo4j Setup**:
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community
```

2. **Install with Neo4j support**:
```bash
pip install "memorygraph[neo4j,intelligence]"
```

### Update MCP Configuration

Edit `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "extended"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://localhost:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "password",
        "MEMORY_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Restart and Verify

1. Restart Claude Code
2. Ask: "How many memory tools do you have now?"
3. Claude should report 11 tools (extended mode)

### Migrate Existing Data

If you have existing SQLite data (when migration tools are implemented):
```bash
# Export from SQLite
memorygraph --backend sqlite --export backup.json

# Import to Neo4j
memorygraph --backend neo4j --import backup.json
```

---

## Troubleshooting

### Server Not Starting

**Check if command is found**:
```bash
which memorygraph
# Should show: /path/to/python/bin/memorygraph
```

If not found:
```bash
# Reinstall
pip install --force-reinstall memorygraph

# Or use full path in mcp.json
{
  "command": "/path/to/python/bin/memorygraph"
}
```

**Check Python version**:
```bash
python3 --version
# Must be 3.10 or higher
```

### Claude Can't See Memory Tools

**Verify MCP config**:
```bash
cat ~/.claude/mcp.json
# Check for syntax errors (use a JSON validator)
```

**Check Claude Code logs**:
- Open Claude Code
- Check output panel for errors
- Look for MCP server initialization messages

**Restart Claude Code**:
- Fully quit Claude Code
- Start it again
- Wait for MCP servers to initialize

### Database Connection Errors

**SQLite locked**:
```bash
# Check for running processes
ps aux | grep memorygraph

# Kill if necessary
pkill -f memorygraph

# Remove lock file (if safe)
rm ~/.memorygraph/memory.db-lock
```

**Neo4j connection refused**:
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check logs
docker logs neo4j

# Restart Neo4j
docker restart neo4j
```

**Permission errors**:
```bash
# Check database directory permissions
ls -la ~/.memorygraph/

# Fix permissions if needed
chmod 755 ~/.memorygraph
chmod 644 ~/.memorygraph/memory.db
```

### Tools Not Working

**Check profile**:
```bash
memorygraph --show-config
# Verify tool_profile matches your needs
```

**Upgrade profile**:
```json
{
  "command": "memorygraph",
  "args": ["--profile", "extended"]
}
```

**Check specific tool availability**:
Ask Claude: "Do you have the find_similar_solutions tool?"

### Performance Issues

**SQLite slow**:
```bash
# Check database size
ls -lh ~/.memorygraph/memory.db

# If >100MB, consider upgrading to Neo4j
```

**Memory usage high**:
```bash
# Check Claude Code memory usage
ps aux | grep memorygraph

# Consider using core profile if not needed
{
  "args": ["--profile", "core"]
}
```

---

## Configuring Proactive Memory Creation

### Why This Matters

MemoryGraph is an MCP tool provider, not an autonomous system. Claude won't automatically store memories unless:
1. You explicitly ask: "Store this..."
2. You configure Claude with memory protocols in CLAUDE.md
3. You establish workflow habits (see examples below)

This section shows you how to configure Claude to proactively use memory tools.

### Global CLAUDE.md Configuration

Add a memory protocol to `~/.claude/CLAUDE.md` for consistent behavior across all sessions:

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

### Project-Specific CLAUDE.md

For team projects or specific repositories, add `.claude/CLAUDE.md` to your project root:

```markdown
## Project: [Your Project Name]

### Memory Storage Protocol
This project uses MemoryGraph for team knowledge sharing.

When working on this project:
1. Before starting: "What do you remember about [component]?"
2. After solving issues: Store the problem and solution, link them
3. After implementing features: Store the pattern used
4. At session end: Store a task summary

### Tagging Convention
Always tag memories with:
- `project:[project-name]`
- `component:[auth|api|database|frontend|etc]`
- `type:[fix|feature|optimization|refactor]`
- Relevant technologies: `fastapi`, `react`, `postgresql`, etc.

### Memory Types for This Project
- **solution**: Working implementations (API endpoints, features)
- **problem**: Issues we encountered (performance, bugs)
- **code_pattern**: Reusable patterns (error handling, validation)
- **decision**: Architecture choices (why we chose X over Y)
- **task**: Sprint work, feature completion

### Example Memory Flow
When fixing a bug:
1. Store problem: type=problem, title="API timeout under load"
2. Store solution: type=solution, title="Fixed with connection pooling"
3. Link them: solution SOLVES problem
4. Both tagged: `project:myapp`, `component:api`, `postgresql`
```

### Trigger Phrases Guide

Train yourself to use these phrases for consistent memory creation:

**Storing knowledge**:
- "Store this for later: [content]"
- "Remember that [pattern/solution]"
- "Save this pattern: [description]"
- "Record this decision: [what we chose and why]"
- "Create a memory about [topic]"

**Recalling knowledge**:
- "What do you remember about [topic]?"
- "Have we solved [problem] before?"
- "Recall any patterns for [use case]"
- "What did we decide about [topic]?"
- "Catch me up on [project/component]"

**Session management**:
- "Summarize and store what we accomplished today"
- "Store a summary of this session"
- "What have we learned in this session?" (triggers storage)

### Workflow Integration Examples

#### Example 1: Debugging Session

```
Start of session:
You: "What do you remember about Redis timeout issues?"
Claude: [Uses recall_memories to find past solutions]

During work:
You: "We fixed it by increasing the connection pool to 50. Store this solution."
Claude: [Uses store_memory with type=solution]
Claude: [Searches for related problem with recall_memories]
Claude: [Uses create_relationship to link solution to problem]

End of session:
You: "Store a summary of what we accomplished"
Claude: [Creates task-type memory with summary]
```

#### Example 2: Feature Development

```
Start:
You: "Recall any authentication patterns we've used"
Claude: [Uses recall_memories for auth-related patterns]

During:
[You implement the feature together]

After implementation:
You: "Store this authentication pattern with the JWT refresh token approach"
Claude: [Stores as code_pattern with detailed content]

Link to project:
Claude: [Automatically creates relationship: pattern APPLIES_TO project]

End:
You: "Summarize today's auth work for the memory"
Claude: [Stores task summary with links to patterns used]
```

#### Example 3: Architecture Decision

```
Discussion:
You: "Should we use PostgreSQL or MongoDB?"
[Discussion of trade-offs]

After decision:
You: "Store our decision to use PostgreSQL, including the reasoning about ACID compliance"
Claude: [Stores as type=decision with full context]
Claude: [Tags with project, database, architecture]

Later:
You: "Why did we choose PostgreSQL?"
Claude: [Recalls the decision memory with full rationale]
```

### Advanced: Memory Habits for Teams

If your team uses MemoryGraph, establish these habits:

**Daily standup**:
```
"Recall what the team worked on yesterday"
[At end of standup] "Store today's task assignments"
```

**Code review**:
```
[After finding issue] "Store this code smell and the better pattern"
[Link]: code_smell SOLVED_BY better_pattern
```

**Sprint retrospective**:
```
"Recall all problems we encountered this sprint"
"Store the top 3 improvements we're implementing"
```

**Onboarding**:
```
New dev: "Catch me up on the authentication system"
Claude: [Recalls architecture decisions, patterns, known issues]
```

### Verification

To verify your CLAUDE.md is working:

1. Start a new Claude Code session
2. Do some work (fix a bug, implement a feature)
3. Check if Claude proactively suggests storing memories
4. If not, try: "What's our memory protocol?" - Claude should reference your CLAUDE.md

---

## Usage Tips

### Effective Memory Storage

**Be Descriptive**:
```
✅ Good: "Use FastAPI's dependency injection for database connections.
          Create a get_db() function that yields a session."

❌ Bad: "FastAPI database stuff"
```

**Use Tags**:
```
✅ Good: tags: ["fastapi", "database", "sqlalchemy", "dependency-injection"]

❌ Bad: tags: ["code"]
```

**Choose Right Memory Type**:
- **Task**: "Implemented user authentication"
- **CodePattern**: "Use repository pattern for database access"
- **Problem**: "Database connection pool exhausted under load"
- **Solution**: "Increased pool size to 50 connections"
- **Project**: "E-commerce API - FastAPI + PostgreSQL"
- **Technology**: "FastAPI best practices for async routes"

### Effective Searching

**Use Context**:
```
✅ "Find memories about database optimization in Python projects"

❌ "Find database"
```

**Filter by Type**:
```
"Find all CodePattern memories about authentication"
```

**Filter by Tags**:
```
"Search for memories tagged with 'performance' and 'postgresql'"
```

### Building Knowledge Graph

**Create Relationships**:
```
"Link the 'use connection pooling' solution to the
'database timeout' problem with SOLVES relationship"
```

**Track Workflows**:
```
"Remember that when implementing auth, I usually:
1. Set up JWT tokens
2. Create login endpoint
3. Add middleware
4. Test with Postman"
```

**Pattern Recognition** (Standard/Full profiles):
```
"What patterns have I used for error handling in FastAPI?"
```

### Project Organization

**Tag by Project**:
```
{
  "project": "my-saas-app",
  "tags": ["authentication", "fastapi"]
}
```

**Use Namespaces**:
```
"Store this pattern for the payment-service project"
```

**Track Technology Stack**:
```
"Remember this project uses: FastAPI, PostgreSQL, Redis, Celery"
```

---

## Advanced Features

### Intelligence Features (Extended Profile)

**Find Similar Solutions**:
```
"I need to validate user input. What similar solutions have we used?"
```

**Get Project Summary**:
```
"Give me a summary of all memories for the e-commerce project"
```

**Session Briefing**:
```
"Give me a briefing of what we worked on this session"
```

### Analytics (Extended Profile)

**Cluster Analysis**:
```
"Analyze memory clusters to find related topics"
```

**Path Finding**:
```
"Find the path of memories connecting authentication to deployment"
```

**Workflow Suggestions**:
```
"Based on my history, what's the next step when implementing a new API endpoint?"
```

### Project Integration (Extended Profile)

**Analyze Codebase**:
```
"Analyze the codebase at /path/to/project and create memories"
```

**Track Changes**:
```
"Track changes to auth.py and api.py"
```

**Identify Patterns**:
```
"What code patterns are used in this project?"
```

---

## Configuration Examples

### For Different Use Cases

#### Solo Developer (Personal Projects)
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

#### Team Development (Shared Server)
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "extended"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://team-server:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "team-password"
      }
    }
  }
}
```

#### High-Performance (Memgraph)
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "memgraph", "--profile", "extended"],
      "env": {
        "MEMORY_MEMGRAPH_URI": "bolt://localhost:7687"
      }
    }
  }
}
```

#### Debug Mode
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--log-level", "DEBUG"]
    }
  }
}
```

---

## Best Practices

1. **Start Simple**: Begin with core profile, upgrade when needed
2. **Be Consistent**: Use consistent tags and naming conventions
3. **Create Relationships**: Link related memories for better retrieval
4. **Use Memory Types**: Choose appropriate types for context
5. **Regular Cleanup**: Delete outdated or incorrect memories
6. **Backup Regularly**: Export your data periodically
7. **Monitor Size**: Check database size as it grows
8. **Upgrade Thoughtfully**: Move to Neo4j when you hit 10k+ memories

---

## Next Steps

1. **Store Your First Memories**: Start building your knowledge graph
2. **Create Relationships**: Link related concepts
3. **Explore Search**: Try different search queries
4. **Track Patterns**: Store successful approaches
5. **Monitor Usage**: See how memory helps your workflow
6. **Upgrade When Ready**: Move to extended mode for advanced features

For more information:
- [README.md](../README.md) - Overview and features
- [TOOL_PROFILES.md](TOOL_PROFILES.md) - Complete tool reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Advanced features guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment options
- [GitHub Issues](https://github.com/gregorydickson/memory-graph/issues) - Support

---

**Last Updated**: November 28, 2025

Happy remembering! 🧠
