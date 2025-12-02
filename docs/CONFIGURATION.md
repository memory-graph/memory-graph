# Configuration Reference

Complete configuration examples for MemoryGraph with various MCP clients and backends.

## Claude Code CLI (Recommended Method)

Use `claude mcp add` to configure MemoryGraph:

```bash
# Core mode (default, 9 tools)
claude mcp add --scope user memorygraph -- memorygraph

# Extended mode (11 tools)
claude mcp add --scope user memorygraph -- memorygraph --profile extended

# Extended mode with Neo4j backend
claude mcp add --scope user memorygraph \
  --env MEMORY_NEO4J_URI=bolt://localhost:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=your-password \
  -- memorygraph --profile extended --backend neo4j

# FalkorDBLite backend (embedded, like SQLite with Cypher)
claude mcp add --scope user memorygraph \
  --env MEMORY_FALKORDBLITE_PATH=~/.memorygraph/falkordblite.db \
  -- memorygraph --backend falkordblite

# FalkorDB backend (client-server)
claude mcp add --scope user memorygraph \
  --env MEMORY_FALKORDB_HOST=localhost \
  --env MEMORY_FALKORDB_PORT=6379 \
  --env MEMORY_FALKORDB_PASSWORD=your-password \
  -- memorygraph --backend falkordb

# Project-specific (creates .mcp.json in project root)
claude mcp add --scope project memorygraph -- memorygraph
```

## JSON Configuration Examples

### Basic Configuration (Core Mode - Default)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

This uses the default core profile with 9 essential tools.

### Extended Mode (11 Tools)

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

Adds database statistics and complex relationship queries to the core tools.

### Extended Mode with SQLite (Custom Path)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended"],
      "env": {
        "MEMORY_TOOL_PROFILE": "extended",
        "MEMORY_SQLITE_PATH": "/Users/yourname/.memorygraph/memory.db"
      }
    }
  }
}
```

### Extended Mode with Neo4j

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "extended"],
      "env": {
        "MEMORY_BACKEND": "neo4j",
        "MEMORY_NEO4J_URI": "bolt://localhost:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "your-password",
        "MEMORY_TOOL_PROFILE": "extended"
      }
    }
  }
}
```

### Extended Mode with Memgraph

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "memgraph", "--profile", "extended"],
      "env": {
        "MEMORY_BACKEND": "memgraph",
        "MEMORY_MEMGRAPH_URI": "bolt://localhost:7687",
        "MEMORY_MEMGRAPH_USER": "memgraph",
        "MEMORY_MEMGRAPH_PASSWORD": "memgraph",
        "MEMORY_TOOL_PROFILE": "extended"
      }
    }
  }
}
```

### FalkorDBLite Backend (Embedded with Cypher)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "falkordblite"],
      "env": {
        "MEMORY_BACKEND": "falkordblite",
        "MEMORY_FALKORDBLITE_PATH": "/Users/yourname/.memorygraph/falkordblite.db"
      }
    }
  }
}
```

### FalkorDB Backend (Client-Server)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "falkordb", "--profile", "extended"],
      "env": {
        "MEMORY_BACKEND": "falkordb",
        "MEMORY_FALKORDB_HOST": "localhost",
        "MEMORY_FALKORDB_PORT": "6379",
        "MEMORY_FALKORDB_PASSWORD": "your-password",
        "MEMORY_TOOL_PROFILE": "extended"
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
        "memorygraph.server"
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
      "args": ["--profile", "extended"],
      "env": {
        "MEMORY_SQLITE_PATH": "/path/to/your/project/.memory/memory.db",
        "MEMORY_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Multiple Memory Servers

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
      "args": ["--profile", "extended", "--backend", "neo4j"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://work-server:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "work-password"
      }
    }
  }
}
```

### Using Full Path (Prevents Version Conflicts)

```json
{
  "mcpServers": {
    "memorygraph": {
      "type": "stdio",
      "command": "/Users/yourname/.local/bin/memorygraph",
      "args": [],
      "env": {}
    }
  }
}
```

## Environment Variables

```bash
# Backend selection
export MEMORY_BACKEND=sqlite          # sqlite (default) | falkordblite | falkordb | neo4j | memgraph

# Tool profile
export MEMORY_TOOL_PROFILE=core       # core (default) | extended

# SQLite configuration (default backend)
export MEMORY_SQLITE_PATH=~/.memorygraph/memory.db

# FalkorDBLite configuration (embedded with Cypher)
export MEMORY_FALKORDBLITE_PATH=~/.memorygraph/falkordblite.db

# FalkorDB configuration (client-server)
export MEMORY_FALKORDB_HOST=localhost
export MEMORY_FALKORDB_PORT=6379
export MEMORY_FALKORDB_PASSWORD=your-password

# Neo4j configuration (if using neo4j backend)
export MEMORY_NEO4J_URI=bolt://localhost:7687
export MEMORY_NEO4J_USER=neo4j
export MEMORY_NEO4J_PASSWORD=your-password

# Memgraph configuration (if using memgraph backend)
export MEMORY_MEMGRAPH_URI=bolt://localhost:7687
export MEMORY_MEMGRAPH_USER=memgraph
export MEMORY_MEMGRAPH_PASSWORD=memgraph

# Relationship configuration (v0.9.0+)
export MEMORY_ALLOW_CYCLES=false      # true | false (default) - Allow circular relationships

# Logging
export MEMORY_LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
```

### New in v0.9.0

**Cycle Detection Configuration**:
- `MEMORY_ALLOW_CYCLES` - Controls whether circular relationships are permitted
  - `false` (default): Prevents cycles using DFS algorithm, raises error if cycle detected
  - `true`: Allows circular relationships (use with caution)
  - Example use case: Allowing mutually-dependent patterns or bidirectional workflows

**Health Check Options**:
- Use `memorygraph --health` to check backend connection and statistics
- Use `memorygraph --health-json` for JSON output (useful for monitoring/CI)
- Use `memorygraph --health-timeout 10.0` to set timeout in seconds (default: 5.0)

## CLI Options

```bash
# Show help
memorygraph --help

# Show current configuration
memorygraph --show-config

# Show version
memorygraph --version

# Run with custom settings
memorygraph --backend neo4j --profile extended --log-level DEBUG
```

## Configuration File Locations

| File | Purpose | Created By |
|------|---------|------------|
| `.mcp.json` | Project MCP servers | `claude mcp add --scope project` |
| `~/.claude.json` | Global MCP servers | `claude mcp add --scope user` |
| `settings.json` | Permissions & behavior | Claude Code settings |

## Backend Platform Support

| Backend | Linux | macOS | Windows |
|---------|-------|-------|---------|
| SQLite | ✅ | ✅ | ✅ |
| Neo4j | ✅ | ✅ | ✅ |
| Memgraph | ✅ | ✅ | ✅ |
| FalkorDB | ✅ | ✅ | ✅ |
| FalkorDBLite | ✅ | ❌ | ❌ |

### FalkorDBLite Platform Limitation

**FalkorDBLite is currently Linux-only** (as of v0.4.0). The bundled `falkordb.so` module is compiled as a Linux ELF binary and is not compatible with macOS or Windows.

- On **Linux**: FalkorDBLite works as an embedded database similar to SQLite but with Cypher query support
- On **macOS/Windows**: Use SQLite (default), FalkorDB (client-server), or Neo4j instead

If you need Cypher query support on macOS:
1. Use FalkorDB with Docker: `docker run -p 6379:6379 falkordb/falkordb:latest`
2. Or use Neo4j: `docker run -p 7687:7687 neo4j:latest`

## Best Practices

1. **Use `claude mcp add`** - Let the CLI manage configuration files
2. **Use `--scope user`** - For global installation across all projects
3. **Use full paths** - Prevents version conflicts with project venvs
4. **Start with core mode** - Upgrade to extended when needed
5. **Don't manually edit** - Config files are managed by `claude mcp`
6. **Configure memory protocols** - Add memory storage guidelines to your CLAUDE.md

## Encouraging Memory Creation

MemoryGraph provides the tools, but Claude won't automatically use them. To enable proactive memory creation:

### Add to ~/.claude/CLAUDE.md

```markdown
## Memory Protocol
After completing significant tasks, store a memory using `store_memory`:
- Type: solution, problem, code_pattern, decision, etc.
- Title: Brief description
- Content: What was accomplished, key decisions, patterns discovered
- Tags: Relevant keywords for future recall
- Relationships: Link to related memories

Before starting work, use `recall_memories` to check for relevant past learnings.

At session end, store a summary with type=task.
```

### Use Trigger Phrases

- **Store**: "Store this for later...", "Remember that...", "Save this pattern..."
- **Recall**: "What do you remember about...?", "Have we solved this before?"
- **Session**: "Summarize and store what we accomplished today"

See [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md#configuring-proactive-memory-creation) for comprehensive configuration examples and workflows.
