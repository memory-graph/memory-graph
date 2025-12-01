# Configuration Reference

Complete configuration examples for MemoryGraph with various MCP clients and backends.

## Claude Code CLI (Recommended Method)

Use `claude mcp add` to configure MemoryGraph:

```bash
# Lite mode (default)
claude mcp add --scope user memorygraph -- memorygraph

# Standard mode (pattern recognition)
claude mcp add --scope user memorygraph -- memorygraph --profile standard

# Full mode with Neo4j
claude mcp add --scope user memorygraph \
  --env MEMORY_NEO4J_URI=bolt://localhost:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=your-password \
  -- memorygraph --profile full --backend neo4j

# Project-specific (creates .mcp.json in project root)
claude mcp add --scope project memorygraph -- memorygraph
```

## JSON Configuration Examples

### Basic Configuration (Lite Mode)

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
      "args": ["--profile", "standard"],
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

## CLI Options

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

## Configuration File Locations

| File | Purpose | Created By |
|------|---------|------------|
| `.mcp.json` | Project MCP servers | `claude mcp add --scope project` |
| `~/.claude.json` | Global MCP servers | `claude mcp add --scope user` |
| `settings.json` | Permissions & behavior | Claude Code settings |

## Best Practices

1. **Use `claude mcp add`** - Let the CLI manage configuration files
2. **Use `--scope user`** - For global installation across all projects
3. **Use full paths** - Prevents version conflicts with project venvs
4. **Start with lite mode** - Upgrade to standard/full when needed
5. **Don't manually edit** - Config files are managed by `claude mcp`
