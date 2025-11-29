# Claude Code Setup Guide

Step-by-step guide to integrate Claude Code Memory Server with Claude Code.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [MCP Configuration](#mcp-configuration)
4. [Verifying Connection](#verifying-connection)
5. [First Memory](#first-memory)
6. [Upgrading to Full Mode](#upgrading-to-full-mode)
7. [Troubleshooting](#troubleshooting)
8. [Usage Tips](#usage-tips)

---

## Quick Start

Get up and running in 3 steps:

```bash
# 1. Install
pip install memorygraphMCP

# 2. Add to Claude Code config
# Edit ~/.claude/mcp.json (see below)

# 3. Restart Claude Code
```

---

## Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Claude Code**: Latest version with MCP support
- **pip**: Python package installer

Check prerequisites:
```bash
python3 --version  # Should be 3.10+
pip --version      # Should be installed
```

### Install the Package

**Option 1: Basic (Recommended to Start)**
```bash
pip install memorygraphMCP
```
- SQLite backend
- 8 core tools
- Zero configuration

**Option 2: With Intelligence**
```bash
pip install "memorygraph[intelligence]"
```
- SQLite backend
- 15 tools
- Pattern recognition

**Option 3: Full Power**
```bash
pip install "memorygraph[neo4j,intelligence]"
```
- Neo4j backend support
- All 44 tools
- Advanced analytics

### Verify Installation

```bash
# Check version
memorygraph --version
# Should show: memorygraph v1.0.0

# Check configuration
memorygraph --show-config
# Should show default settings
```

### Alternative: uvx (Not Recommended for MCP)

You can run via uvx for quick testing, though this is **not recommended for MCP servers**:

```bash
# Install uv
pip install uv

# Test without installing
uvx memorygraph --version
uvx memorygraph --show-config
```

**Why not recommended for MCP servers**:
- ⚠️ Adds latency to every MCP connection (package download/cache check)
- ⚠️ Harder to configure persistent environment variables
- ⚠️ Database path must be explicitly set every time
- ⚠️ MCP servers run continuously - installation overhead isn't worth it

**When uvx makes sense**: Quick testing, CI/CD, version comparison

**If you still want to use uvx for MCP** (not recommended):

See the uvx MCP configuration example in the [MCP Configuration](#uvx-configuration-advanced---not-recommended) section below.

**Better approach**: Use `pip install memorygraphMCP` for MCP servers, use uvx for quick testing only.

---

## MCP Configuration

### Step 1: Locate MCP Config File

Claude Code's MCP configuration is at:
```bash
~/.claude/mcp.json
```

If it doesn't exist, create it:
```bash
mkdir -p ~/.claude
touch ~/.claude/mcp.json
```

### Step 2: Add Memory Server

Edit `~/.claude/mcp.json` and add the memory server configuration.

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
      "args": ["--profile", "standard"]
    }
  }
}
```

This adds:
- Pattern recognition
- Intelligence features
- 15 tools total

#### Full Configuration (Neo4j)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "full"],
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
- All 44 tools
- Graph analytics
- Advanced features

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
        "MEMORY_TOOL_PROFILE": "lite"
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

### Step 3: Save and Restart

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
Claude Code Memory Server v1.0.0
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

## Upgrading to Full Mode

### Why Upgrade?

Upgrade to full mode when you need:
- Graph analytics (cluster analysis, path finding)
- Workflow automation
- Project integration (codebase scanning)
- Proactive suggestions
- Better performance at scale

### Prerequisites

1. **Set up Neo4j or Memgraph** (see [FULL_MODE.md](FULL_MODE.md))

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
      "args": ["--backend", "neo4j", "--profile", "full"],
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
3. Claude should report 44 tools (full mode)

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
  "args": ["--profile", "full"]
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

# Consider using lite profile if not needed
{
  "args": ["--profile", "lite"]
}
```

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

### Intelligence Features (Standard Profile)

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

### Analytics (Full Profile)

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

### Project Integration (Full Profile)

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
      "args": ["--profile", "standard"]
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
      "args": ["--backend", "neo4j", "--profile", "full"],
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
      "args": ["--backend", "memgraph", "--profile", "full"],
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

1. **Start Simple**: Begin with lite profile, upgrade when needed
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
6. **Upgrade When Ready**: Move to full mode for advanced features

For more information:
- [README.md](../README.md) - Overview and features
- [TOOL_PROFILES.md](TOOL_PROFILES.md) - Complete tool reference
- [FULL_MODE.md](FULL_MODE.md) - Advanced features guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment options
- [GitHub Issues](https://github.com/gregorydickson/memorygraph/issues) - Support

---

**Last Updated**: November 28, 2025

Happy remembering! 🧠
