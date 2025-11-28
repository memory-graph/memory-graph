# Deployment Guide

Complete guide for deploying Claude Code Memory Server in any environment.

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

**Lite Mode (Default)**
```bash
pip install memorygraph
```
- SQLite backend
- 8 core tools
- Zero configuration
- Best for: Getting started, personal use

**Standard Mode**
```bash
pip install "memorygraph[intelligence]"
```
- SQLite backend
- 15 tools (core + intelligence)
- Pattern recognition
- Best for: Most users

**Full Mode**
```bash
pip install "memorygraph[neo4j,intelligence]"
# or
pip install "memorygraph[all]"
```
- Neo4j/Memgraph backend
- All 44 tools
- Advanced analytics
- Best for: Power users, production

### Method 2: Docker

**SQLite Mode**
```bash
# Clone repository
git clone https://github.com/gregorydickson/memorygraph.git
cd memorygraph

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
git clone https://github.com/gregorydickson/memorygraph.git
cd memorygraph

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
uvx memorygraph --backend sqlite --profile standard

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
RUN pip install memorygraph
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

### Quick Start Configuration

**Minimal (Default)**
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
- Lite profile (8 tools)
- Default database path: `~/.memorygraph/memory.db`

### Standard Configuration

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

### Full Configuration

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

---

## Backend Selection

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

### Lite Profile (Default)

**Tools**: 8 core tools
**Backend**: SQLite
**Setup Time**: 30 seconds
**Best For**: Getting started, basic memory needs

```bash
memorygraph
# or explicitly
memorygraph --profile lite
```

**Available Tools**:
- store_memory, get_memory, search_memories
- update_memory, delete_memory
- create_relationship, get_related_memories
- get_memory_statistics

### Standard Profile

**Tools**: 15 tools (core + intelligence)
**Backend**: SQLite
**Setup Time**: 30 seconds
**Best For**: Most users, pattern recognition

```bash
memorygraph --profile standard
```

**Additional Tools**:
- find_similar_solutions
- suggest_patterns_for_context
- get_intelligent_context
- get_project_summary
- get_session_briefing
- get_memory_history
- track_entity_timeline

### Full Profile

**Tools**: All 44 tools
**Backend**: SQLite/Neo4j/Memgraph
**Setup Time**: 5 minutes (with backend)
**Best For**: Power users, advanced analytics

```bash
memorygraph --profile full --backend neo4j
```

**Additional Tools**:
- Advanced relationship tools (7)
- Project integration tools (11)
- Proactive intelligence tools (11)

See [TOOL_PROFILES.md](TOOL_PROFILES.md) for complete list.

---

## Environment Variables

### Core Configuration

```bash
# Backend selection (required)
export MEMORY_BACKEND=sqlite          # sqlite | neo4j | memgraph

# Tool profile (optional, default: lite)
export MEMORY_TOOL_PROFILE=lite       # lite | standard | full

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
      - MEMORY_TOOL_PROFILE=lite
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
      - MEMORY_TOOL_PROFILE=full
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
      - MEMORY_TOOL_PROFILE=full
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

#### Lite to Standard

No migration needed:
```bash
# Before
memorygraph --profile lite

# After
memorygraph --profile standard
```

#### Standard to Full

If staying with SQLite:
```bash
# No migration needed
memorygraph --profile full
```

If switching to Neo4j/Memgraph:
See backend migration below.

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
  "args": ["--backend", "neo4j", "--profile", "full"],
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
memorygraph --backend neo4j --profile full
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
# From lite to standard
memorygraph --profile standard

# From standard to full
memorygraph --profile full
```

**Check tool exists**:
```bash
# List all tools (in server logs)
memorygraph --log-level DEBUG
# Look for "Registered X/44 tools"
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
- [ ] Select tool profile (lite/standard/full)
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

**Recommendation**: SQLite, lite profile
```bash
pip install memorygraph
memorygraph
```

**MCP Config**:
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

**Recommendation**: Neo4j, full profile
```bash
# Server setup
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/strong-password \
  neo4j:5-community

# Each team member
pip install "memorygraph[neo4j]"
```

**MCP Config** (team members):
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "full"],
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

**Recommendation**: Neo4j Aura, full profile

**1. Create Neo4j Aura instance**:
- Go to https://neo4j.com/cloud/aura/
- Create free instance
- Save connection details

**2. Install locally**:
```bash
pip install "memorygraph[neo4j]"
```

**3. MCP Config**:
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "neo4j", "--profile", "full"],
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
- [FULL_MODE.md](FULL_MODE.md) - Advanced features
- [TOOL_PROFILES.md](TOOL_PROFILES.md) - Tool reference
- [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md) - Claude Code integration
- [GitHub Issues](https://github.com/gregorydickson/memorygraph/issues) - Support

---

**Last Updated**: November 28, 2025
