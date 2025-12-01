# Deployment Guide

Complete guide for deploying MemoryGraph in any environment.

## Table of Contents

1. [Installation Methods](#installation-methods)
2. [Configuration](#configuration)
3. [Backend Selection](#backend-selection)
4. [Tool Profiles](#tool-profiles)
5. [Environment Variables](#environment-variables)
6. [Docker Deployment](#docker-deployment)
7. [Migration Guide](#migration-guide)
8. [Troubleshooting](#troubleshooting)
9. [Production Checklist](#production-checklist)

---

## Installation Methods

### Method 1: pip (Recommended)

**Core Mode (Default)**
```bash
pip install memorygraphMCP
```
- SQLite backend
- 9 core tools
- Zero configuration
- Best for: Getting started, personal use

**Extended Mode**
```bash
pip install "memorygraphMCP[neo4j]"
# or
pip install "memorygraphMCP[falkordblite]"  # FalkorDBLite: embedded with Cypher
# or
pip install "memorygraphMCP[falkordb]"      # FalkorDB: client-server with high performance
# or
pip install "memorygraphMCP[all]"
```
- SQLite/FalkorDBLite/FalkorDB/Neo4j/Memgraph backend
- 11 tools (core + advanced)
- Complex queries and analytics
- Best for: Power users, production

### Method 2: Docker

**SQLite Mode**
```bash
# Clone repository
git clone https://github.com/gregorydickson/memory-graph.git
cd memory-graph

# Start with Docker Compose
docker compose up -d
```

**Neo4j Mode**
```bash
docker compose -f docker-compose.neo4j.yml up -d
```

**Memgraph Mode**
```bash
docker compose -f docker-compose.full.yml up -d
```

### Method 3: From Source

```bash
# Clone repository
git clone https://github.com/gregorydickson/memory-graph.git
cd memory-graph

# Install in development mode
pip install -e .

# Or with all features
pip install -e ".[all,dev]"
```

### Method 4: uvx (Ephemeral / Testing)

**Use Cases**:
- Quick testing without installation
- CI/CD pipelines and automation
- Version testing and comparison
- One-time operations
- Trying before installing

**Installation**:
```bash
# Install uv (one time only)
pip install uv

# or via curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Usage**:
```bash
# Check version
uvx memorygraph --version

# Show configuration
uvx memorygraph --show-config

# Health check
uvx memorygraph --health

# Run server (ephemeral)
uvx memorygraph --backend sqlite --profile extended

# Test specific version
uvx memorygraph@1.0.0 --version
```

**Limitations**:
- ⚠️ **First run slower** - Downloads and caches package from PyPI (~5-10 seconds)
- ⚠️ **Not recommended for persistent MCP servers** - Better to use pip install
- ⚠️ **Requires explicit database path** for data persistence:
  ```bash
  MEMORY_SQLITE_PATH=~/.memorygraph/memory.db uvx memorygraph
  ```
- ⚠️ **Environment variables** must be set per invocation (no persistent config)

**CI/CD Example** (GitHub Actions):
```yaml
name: Test Memory Server

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Install uv
        run: pip install uv

      - name: Test memory server
        run: |
          uvx memorygraph --version
          uvx memorygraph --show-config

      - name: Test specific version
        run: uvx memorygraph@1.0.0 --health
```

**GitLab CI Example**:
```yaml
test_memory:
  stage: test
  script:
    - pip install uv
    - uvx memorygraph --version
    - uvx memorygraph --health
```

**Docker Build Example**:
```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Use uvx to run one-time operations without installing
RUN uvx memorygraph --show-config

# For persistent server, use pip install instead
RUN pip install memorygraphMCP
```

**When to Use uvx vs pip install**:

| Scenario | Use uvx | Use pip install |
|----------|---------|-----------------|
| Quick testing | ✅ Yes | ❌ Overkill |
| MCP server (daily use) | ❌ No | ✅ Yes |
| CI/CD automation | ✅ Yes | Either works |
| Version comparison | ✅ Yes | Manual switching |
| Production deployment | ❌ No | ✅ Yes |

---

## Configuration

### For Claude Code CLI: Use `claude mcp add` Command

According to the [official Claude Code documentation](https://code.claude.com/docs/en/mcp), the **recommended and official way** to configure MCP servers for **Claude Code CLI** is using the `claude mcp add` command. Manual JSON editing is not the intended workflow for CLI users.

**Note**: These instructions are specific to **Claude Code CLI**. For other Claude Code interfaces (VS Code extension, Desktop app, Web), see [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md) for interface-specific instructions.

### Understanding Claude Code's Configuration Files

Claude Code uses multiple configuration files with different purposes. **This is admittedly messy**, and Anthropic is aware of the documentation issues.

| File | Purpose | What Goes Here |
|------|---------|----------------|
| **`.mcp.json`** | Project MCP servers | Server configurations for specific project (created by `claude mcp add --scope project`) |
| **`~/.claude.json`** | Global MCP servers (legacy) | User-level server configurations (managed by `claude mcp add`) |
| **`~/.claude/settings.json`** | Permissions & behavior | `enabledMcpjsonServers`, environment variables, tool behavior settings |

### Key Takeaways

✅ **DO**:
- Use `claude mcp add` command (official method)
- Let the CLI manage configuration files for you
- Use `--scope project` for project-specific servers
- Use default (user-level) for servers available across all projects

❌ **DON'T**:
- Put MCP servers in `~/.claude/settings.json` - **it won't work**
- Manually edit `.mcp.json` or `~/.claude.json` unless absolutely necessary
- Try to manually manage the "chaotic grab bag" of legacy global settings

**Why this matters**: The configuration system is complex and has legacy files. Using `claude mcp add` ensures your MCP servers are configured in the correct location and format.

**Prerequisites**: You must have already installed MemoryGraph via pip (see [Installation Methods](#installation-methods) above). The `claude mcp add` command configures Claude Code to use the already-installed `memorygraph` command.

---

### Claude Code CLI Configuration Examples

**These examples use `claude mcp add` which is CLI-specific.** For VS Code extension, Desktop app, or Web, see [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md).

#### User-Level Configuration (Default)

```bash
# Prerequisite: pip install memorygraphMCP (must be run first)
claude mcp add --transport stdio memorygraph memorygraph
```

Uses:
- SQLite backend
- Core profile (9 tools)
- Default database path: `~/.memorygraph/memory.db`
- Available across all projects

#### Project-Level Configuration

```bash
# Prerequisite: pip install memorygraphMCP (must be run first)
claude mcp add --transport stdio memorygraph memorygraph --scope project
```

Creates `.mcp.json` in your project root.

#### Extended Configuration

```bash
# Prerequisite: pip install "memorygraphMCP[neo4j]" (must be run first)
claude mcp add --transport stdio memorygraph memorygraph --profile extended
```

#### Extended Configuration with Neo4j

```bash
# Prerequisite: pip install "memorygraphMCP[neo4j,intelligence]" (must be run first)
claude mcp add --transport stdio memorygraph memorygraph --profile extended --backend neo4j \
  --env MEMORY_NEO4J_URI=bolt://localhost:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=your-password
```

#### Verify Configuration

```bash
# List all MCP servers
claude mcp list

# Get details for memorygraph
claude mcp get memorygraph
```

---

### Manual Configuration

**For Claude Code CLI users**: Use `claude mcp add` instead (see above).

**For other Claude Code interfaces** (VS Code extension, Desktop app): Manual configuration is required as the `claude mcp add` command is CLI-specific. See [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md#configuration-by-interface) for interface-specific instructions.

**For other MCP clients** (Cursor, Continue, etc.): Use the manual JSON configuration below.

If you need to manually configure (for non-Claude Code clients):

#### Quick Start Configuration (Minimal)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

Uses:
- SQLite backend
- Core profile (9 tools)
- Default database path: `~/.memorygraph/memory.db`

#### Extended Configuration

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

#### Extended Configuration with Neo4j

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

---

## Backend Selection

MemoryGraph supports 5 backend options:

1. **sqlite** - Embedded, default, zero-config
2. **falkordblite** - Embedded, zero-config with native Cypher/graph support
3. **falkordb** - Client-server, user manages FalkorDB
4. **neo4j** - Client-server, enterprise
5. **memgraph** - Client-server, real-time analytics

### SQLite (Default)

**When to Use**:
- Getting started
- Personal projects
- <10k memories
- No setup time
- Portable database

**Configuration**:
```bash
export MEMORY_BACKEND=sqlite
export MEMORY_SQLITE_PATH=~/.memorygraph/memory.db
```

**Pros**:
- Zero configuration
- No dependencies
- Portable file-based
- Fast for small datasets

**Cons**:
- Slower graph queries at scale
- Limited concurrent writes
- Manual relationship traversal

### FalkorDBLite (Embedded with Native Graph)

**When to Use**:
- Want native Cypher query support
- Need better graph traversal than SQLite
- Prefer embedded (no server setup)
- <10k memories
- Zero-config like SQLite

**Configuration**:
```bash
export MEMORY_BACKEND=falkordblite
export MEMORY_FALKORDBLITE_PATH=~/.memorygraph/falkordblite.db  # Optional, this is default
```

**Installation**:
```bash
pip install "memorygraphMCP[falkordblite]"

# macOS users may need libomp:
brew install libomp
```

**Pros**:
- Zero configuration (embedded)
- Native Cypher support
- Better graph performance than SQLite
- No server management
- Portable file-based storage

**Cons**:
- Requires additional dependency (falkordblite)
- macOS may need libomp installation
- Not suitable for >10k memories

### FalkorDB (Client-Server)

**When to Use**:
- Production deployments
- Need high-performance graph operations
- >10k memories
- 500x faster p99 than Neo4j
- Team collaboration

**Setup**:
```bash
# Option 1: Docker
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  falkordb/falkordb:latest

# Option 2: Docker with password
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  -e FALKORDB_PASSWORD=your-password \
  falkordb/falkordb:latest

# Configure
export MEMORY_BACKEND=falkordb
export MEMORY_FALKORDB_HOST=localhost
export MEMORY_FALKORDB_PORT=6379
export MEMORY_FALKORDB_PASSWORD=your-password  # If set above
```

**Installation**:
```bash
pip install "memorygraphMCP[falkordb]"
```

**Pros**:
- Exceptional performance (500x faster p99 than Neo4j)
- Redis-based (familiar to many teams)
- Native Cypher query language
- Production-ready
- Excellent for high-throughput workloads

**Cons**:
- Requires FalkorDB server (user manages deployment)
- Setup more complex than embedded options
- Needs network configuration

**Documentation**: [FalkorDB Docs](https://docs.falkordb.com/)

### Neo4j

**When to Use**:
- Production deployments
- Team collaboration
- >10k memories
- Complex graph analytics
- Rich query requirements

**Setup**:
```bash
# Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community

# Configure
export MEMORY_BACKEND=neo4j
export MEMORY_NEO4J_URI=bolt://localhost:7687
export MEMORY_NEO4J_USER=neo4j
export MEMORY_NEO4J_PASSWORD=password
```

**Pros**:
- Industry-standard graph DB
- Excellent query performance
- Rich tooling (Browser, Bloom)
- Cypher query language
- Strong community

**Cons**:
- Requires setup
- Resource intensive
- Learning curve

### Memgraph

**When to Use**:
- High-performance analytics
- Real-time queries
- Large-scale graphs
- In-memory processing

**Setup**:
```bash
# Docker
docker run -d \
  --name memgraph \
  -p 7687:7687 \
  -p 3000:3000 \
  memgraph/memgraph-platform

# Configure
export MEMORY_BACKEND=memgraph
export MEMORY_MEMGRAPH_URI=bolt://localhost:7687
```

**Pros**:
- Fastest graph analytics
- In-memory processing
- Cypher compatible
- Built for scale

**Cons**:
- Requires setup
- Higher memory usage
- Smaller ecosystem

---

## Tool Profiles

### Core Profile (Default)

**Tools**: 9 core tools
**Backend**: SQLite
**Setup Time**: 30 seconds
**Best For**: Getting started, daily use (95% of users)

```bash
memorygraph
# or explicitly
memorygraph --profile core
```

**Available Tools**:
- store_memory, recall_memories, search_memories
- get_memory, update_memory, delete_memory
- create_relationship, get_related_memories
- get_session_briefing

### Extended Profile

**Tools**: 11 tools (core + advanced)
**Backend**: SQLite/Neo4j/Memgraph
**Setup Time**: 30 seconds (SQLite) or 5 minutes (Neo4j/Memgraph)
**Best For**: Power users, advanced analytics

```bash
memorygraph --profile extended
# or with Neo4j
memorygraph --profile extended --backend neo4j
```

**Additional Tools** (beyond core):
- get_memory_statistics - Database statistics
- analyze_relationship_patterns - Advanced relationship analysis

See [TOOL_PROFILES.md](TOOL_PROFILES.md) for complete list.

---

## Environment Variables

### Core Configuration

```bash
# Backend selection (required)
export MEMORY_BACKEND=sqlite          # sqlite | falkordblite | falkordb | neo4j | memgraph

# Tool profile (optional, default: core)
export MEMORY_TOOL_PROFILE=core       # core | extended

# Logging (optional, default: INFO)
export MEMORY_LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
```

### SQLite Configuration

```bash
# Database file path (optional)
export MEMORY_SQLITE_PATH=~/.memorygraph/memory.db

# WAL mode (optional, default: true)
export MEMORY_SQLITE_WAL_MODE=true

# Cache size (optional, default: -64000 = 64MB)
export MEMORY_SQLITE_CACHE_SIZE=-64000
```

### FalkorDBLite Configuration

```bash
# Database file path (optional, default: ~/.memorygraph/falkordblite.db)
export MEMORY_FALKORDBLITE_PATH=~/.memorygraph/falkordblite.db

# Or use short form:
export FALKORDBLITE_PATH=~/.memorygraph/falkordblite.db
```

### FalkorDB Configuration

```bash
# Connection host (required if backend=falkordb)
export MEMORY_FALKORDB_HOST=localhost
export FALKORDB_HOST=localhost  # Alternative

# Connection port (optional, default: 6379)
export MEMORY_FALKORDB_PORT=6379
export FALKORDB_PORT=6379  # Alternative

# Authentication (optional)
export MEMORY_FALKORDB_PASSWORD=your-password
export FALKORDB_PASSWORD=your-password  # Alternative
```

### Neo4j Configuration

```bash
# Connection URI (required if backend=neo4j)
export MEMORY_NEO4J_URI=bolt://localhost:7687

# Authentication (required)
export MEMORY_NEO4J_USER=neo4j
export MEMORY_NEO4J_PASSWORD=your-password

# Connection pool (optional)
export MEMORY_NEO4J_MAX_POOL_SIZE=50
export MEMORY_NEO4J_CONNECTION_TIMEOUT=30

# Database name (optional, default: neo4j)
export MEMORY_NEO4J_DATABASE=neo4j
```

### Memgraph Configuration

```bash
# Connection URI (required if backend=memgraph)
export MEMORY_MEMGRAPH_URI=bolt://localhost:7687

# Authentication (optional, default: no auth)
export MEMORY_MEMGRAPH_USER=memgraph
export MEMORY_MEMGRAPH_PASSWORD=your-password

# Connection pool (optional)
export MEMORY_MEMGRAPH_MAX_POOL_SIZE=50
```

### Intelligence Configuration (Optional)

```bash
# Embedding model (optional, default: all-MiniLM-L6-v2)
export MEMORY_EMBEDDING_MODEL=all-MiniLM-L6-v2

# SpaCy model (optional, default: en_core_web_sm)
export MEMORY_SPACY_MODEL=en_core_web_sm

# Context token limit (optional, default: 4000)
export MEMORY_CONTEXT_TOKEN_LIMIT=4000
```

---

## Docker Deployment

### SQLite Mode (docker-compose.yml)

```yaml
version: '3.8'

services:
  memorygraph:
    build: .
    stdin_open: true
    tty: true
    environment:
      - MEMORY_BACKEND=sqlite
      - MEMORY_SQLITE_PATH=/data/memory.db
    volumes:
      - memory_data:/data

volumes:
  memory_data:
```

**Usage**:
```bash
docker compose up -d
docker compose logs -f
```

### Neo4j Mode (docker-compose.neo4j.yml)

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_dbms_memory_heap_max__size=2g
      - NEO4J_dbms_memory_pagecache_size=1g
    volumes:
      - neo4j_data:/data

  memorygraph:
    build: .
    depends_on:
      - neo4j
    stdin_open: true
    tty: true
    environment:
      - MEMORY_BACKEND=neo4j
      - MEMORY_TOOL_PROFILE=extended
      - MEMORY_NEO4J_URI=bolt://neo4j:7687
      - MEMORY_NEO4J_USER=neo4j
      - MEMORY_NEO4J_PASSWORD=password

volumes:
  neo4j_data:
```

**Usage**:
```bash
docker compose -f docker-compose.neo4j.yml up -d

# Access Neo4j Browser
open http://localhost:7474
```

### Memgraph Mode (docker-compose.full.yml)

```yaml
version: '3.8'

services:
  memgraph:
    image: memgraph/memgraph-platform
    ports:
      - "7687:7687"
      - "3000:3000"
    volumes:
      - memgraph_data:/var/lib/memgraph

  memorygraph:
    build: .
    depends_on:
      - memgraph
    stdin_open: true
    tty: true
    environment:
      - MEMORY_BACKEND=memgraph
      - MEMORY_TOOL_PROFILE=extended
      - MEMORY_MEMGRAPH_URI=bolt://memgraph:7687

volumes:
  memgraph_data:
```

**Usage**:
```bash
docker compose -f docker-compose.full.yml up -d

# Access Memgraph Lab
open http://localhost:3000
```

---

## Migration Guide

### Upgrading Profiles

#### Core to Extended

No migration needed:
```bash
# Before
memorygraph --profile core

# After
memorygraph --profile extended
```

Extended mode adds 2 additional tools (get_memory_statistics, analyze_relationship_patterns) but uses the same database.

### Migrating Backends

#### SQLite to Neo4j

**1. Export SQLite data** (when implemented):
```bash
memorygraph --backend sqlite --export backup.json
```

**2. Set up Neo4j**:
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community
```

**3. Import to Neo4j** (when implemented):
```bash
memorygraph --backend neo4j --import backup.json
```

**4. Update MCP config**:
```json
{
  "command": "memorygraph",
  "args": ["--backend", "neo4j", "--profile", "extended"],
  "env": {
    "MEMORY_NEO4J_URI": "bolt://localhost:7687",
    "MEMORY_NEO4J_USER": "neo4j",
    "MEMORY_NEO4J_PASSWORD": "password"
  }
}
```

#### Manual Migration

If export/import not available:

**1. Get all memories from SQLite**:
Use `search_memories` with no filters to get all IDs, then `get_memory` for each.

**2. Store in Neo4j**:
Use `store_memory` for each memory in the new backend.

**3. Recreate relationships**:
Get all relationships from SQLite and recreate with `create_relationship`.

---

## Troubleshooting

### Common Issues

#### Server Won't Start

**Check configuration**:
```bash
memorygraph --show-config
```

**Check backend connection**:
```bash
# SQLite
ls -lah ~/.memorygraph/

# Neo4j
docker ps | grep neo4j
docker logs neo4j

# Memgraph
docker ps | grep memgraph
docker logs memgraph
```

**Check logs**:
```bash
memorygraph --log-level DEBUG
```

#### Database Connection Errors

**SQLite locked**:
```bash
# Check for running processes
ps aux | grep memorygraph

# Remove lock file (if safe)
rm ~/.memorygraph/memory.db-lock

# Check permissions
ls -la ~/.memorygraph/
```

**Neo4j connection refused**:
```bash
# Verify Neo4j is running
docker ps | grep neo4j

# Check ports
netstat -an | grep 7687

# Verify credentials
memorygraph --backend neo4j --show-config

# Test connection manually
cypher-shell -a bolt://localhost:7687 -u neo4j -p password
```

**Memgraph connection refused**:
```bash
# Verify Memgraph is running
docker ps | grep memgraph

# Restart if needed
docker restart memgraph

# Check logs
docker logs memgraph
```

#### Performance Issues

**SQLite slow queries**:
```bash
# Check database size
ls -lh ~/.memorygraph/memory.db

# Vacuum database
sqlite3 ~/.memorygraph/memory.db "VACUUM;"

# Consider upgrading to Neo4j
memorygraph --backend neo4j --profile extended
```

**Neo4j out of memory**:
```bash
# Increase heap size
docker run -e NEO4J_dbms_memory_heap_max__size=4g ...

# Check current memory usage
# In Neo4j Browser: :sysinfo
```

**Memgraph high memory usage**:
```bash
# Check memory limit
docker inspect memgraph | grep Memory

# Increase limit
docker run -e MEMGRAPH_MEM_LIMIT=8192 ...
```

#### Tool Not Available

**Check profile**:
```bash
memorygraph --show-config
# Verify tool_profile is correct
```

**Upgrade profile**:
```bash
# From core to extended
memorygraph --profile extended
```

**Check tool exists**:
```bash
# List all tools (in server logs)
memorygraph --log-level DEBUG
# Look for "Registered X/11 tools" (9 for core, 11 for extended)
```

### Debug Mode

Enable debug logging:
```bash
export MEMORY_LOG_LEVEL=DEBUG
memorygraph
```

Or via CLI:
```bash
memorygraph --log-level DEBUG
```

### Health Checks

**Verify configuration**:
```bash
memorygraph --show-config
```

**Test backend connection** (when implemented):
```bash
memorygraph --health
```

**Check version**:
```bash
memorygraph --version
```

---

## Production Checklist

### Pre-Deployment

- [ ] Choose appropriate backend (SQLite/Neo4j/Memgraph)
- [ ] Select tool profile (core/extended)
- [ ] Configure environment variables
- [ ] Set up database (if Neo4j/Memgraph)
- [ ] Test connection locally
- [ ] Configure MCP integration
- [ ] Test with Claude Code

### Security

- [ ] Use strong passwords (Neo4j/Memgraph)
- [ ] Enable TLS/SSL for remote connections
- [ ] Restrict network access (firewall)
- [ ] Regular security updates
- [ ] Backup encryption (if sensitive data)
- [ ] Audit access logs

### Performance

- [ ] Tune database memory settings
- [ ] Create appropriate indexes
- [ ] Monitor query performance
- [ ] Set up performance alerts
- [ ] Plan for scaling

### Monitoring

- [ ] Log aggregation (ELK, Splunk)
- [ ] Metrics collection (Prometheus)
- [ ] Alerting (PagerDuty, Slack)
- [ ] Database monitoring
- [ ] Resource usage tracking

### Backup & Recovery

- [ ] Automated daily backups
- [ ] Test restore procedures
- [ ] Off-site backup storage
- [ ] Retention policy (7/30/90 days)
- [ ] Disaster recovery plan

### Documentation

- [ ] Document configuration
- [ ] Document backup procedures
- [ ] Document troubleshooting steps
- [ ] Document team access
- [ ] Document upgrade path

---

## Deployment Scenarios

### Personal Use (Local)

**Recommendation**: SQLite, core profile

**Step 1: Install**
```bash
pip install memorygraphMCP
```

**Step 2: Configure MCP** (Claude Code CLI):
```bash
claude mcp add --transport stdio memorygraph memorygraph
```

**Step 2: Configure MCP** (Manual):
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph"
    }
  }
}
```

### Team Use (Shared Server)

**Recommendation**: Neo4j, extended profile

**Step 1: Server setup**
```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/strong-password \
  neo4j:5-community
```

**Step 2: Each team member installs**
```bash
pip install "memorygraphMCP[neo4j]"
```

**Step 3: Configure MCP** (Claude Code CLI - team members):
```bash
claude mcp add --transport stdio memorygraph memorygraph --profile extended --backend neo4j \
  --env MEMORY_NEO4J_URI=bolt://team-server:7687 \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=strong-password
```

**Step 3: Configure MCP** (Manual - team members):
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "extended"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://team-server:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "strong-password"
      }
    }
  }
}
```

### Cloud Deployment

**Recommendation**: Neo4j Aura, extended profile

**Step 1: Create Neo4j Aura instance**:
- Go to https://neo4j.com/cloud/aura/
- Create free instance
- Save connection details

**Step 2: Install locally**:
```bash
pip install "memorygraphMCP[neo4j]"
```

**Step 3: Configure MCP** (Claude Code CLI):
```bash
claude mcp add --transport stdio memorygraph memorygraph --profile extended --backend neo4j \
  --env MEMORY_NEO4J_URI=neo4j+s://your-instance.neo4j.io \
  --env MEMORY_NEO4J_USER=neo4j \
  --env MEMORY_NEO4J_PASSWORD=your-password
```

**Step 3: Configure MCP** (Manual):
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "extended"],
      "env": {
        "MEMORY_NEO4J_URI": "neo4j+s://your-instance.neo4j.io",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
```

---

## Performance Benchmarks

### SQLite Performance

| Memories | Query Time | Storage | RAM |
|----------|-----------|---------|-----|
| 1,000 | <50ms | 5MB | 50MB |
| 10,000 | <100ms | 50MB | 100MB |
| 100,000 | <500ms | 500MB | 200MB |

### Neo4j Performance

| Memories | Query Time | Storage | RAM |
|----------|-----------|---------|-----|
| 1,000 | <10ms | 10MB | 500MB |
| 10,000 | <50ms | 100MB | 1GB |
| 100,000 | <100ms | 1GB | 2GB |

### Memgraph Performance

| Memories | Query Time | Storage | RAM |
|----------|-----------|---------|-----|
| 1,000 | <5ms | 10MB | 200MB |
| 10,000 | <20ms | 100MB | 2GB |
| 100,000 | <50ms | 1GB | 4GB |

---

## Next Steps

1. Choose your deployment method
2. Set up your backend
3. Configure environment variables
4. Test the connection
5. Integrate with Claude Code
6. Monitor and optimize

For more help:
- [TOOL_PROFILES.md](TOOL_PROFILES.md) - Tool reference
- [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md) - Claude Code integration
- [archive/FULL_MODE_LEGACY.md](archive/FULL_MODE_LEGACY.md) - Legacy documentation (archived)
- [GitHub Issues](https://github.com/gregorydickson/memory-graph/issues) - Support

---

**Last Updated**: November 28, 2025
