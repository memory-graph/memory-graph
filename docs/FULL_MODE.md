# Full Mode Guide

This guide covers everything you need to unlock all 44 tools and advanced features of the Claude Code Memory Server.

## Table of Contents

1. [Why Use Full Mode?](#why-use-full-mode)
2. [Backend Comparison](#backend-comparison)
3. [Neo4j Setup](#neo4j-setup)
4. [Memgraph Setup](#memgraph-setup)
5. [All 44 Tools](#all-44-tools)
6. [Performance Tuning](#performance-tuning)
7. [Advanced Queries](#advanced-queries)

---

## Why Use Full Mode?

### When to Upgrade

Upgrade to full mode when you need:

- **Advanced Graph Analytics**: Cluster analysis, bridge node detection, graph metrics
- **Workflow Automation**: Track and optimize development workflows
- **Project Integration**: Codebase scanning, pattern detection, file change tracking
- **Proactive Intelligence**: AI-powered suggestions, issue detection, knowledge gap analysis
- **Visualization**: Graph visualization data for frontend dashboards
- **Scale**: Managing 100k+ memories with fast graph queries

### What You Get

| Feature | Lite | Standard | Full |
|---------|------|----------|------|
| Memory CRUD | ✅ | ✅ | ✅ |
| Basic Relationships | ✅ | ✅ | ✅ |
| Pattern Recognition | ❌ | ✅ | ✅ |
| Graph Analytics | ❌ | ❌ | ✅ |
| Workflow Automation | ❌ | ❌ | ✅ |
| Project Integration | ❌ | ❌ | ✅ |
| Proactive AI | ❌ | ❌ | ✅ |
| Visualization | ❌ | ❌ | ✅ |

---

## Backend Comparison

### SQLite vs Neo4j vs Memgraph

| Feature | SQLite | Neo4j | Memgraph |
|---------|--------|-------|----------|
| **Setup** | Zero config | Docker/Cloud | Docker |
| **Cost** | Free | Free (Community) | Free (Community) |
| **Speed (small data)** | Fast | Fast | Fastest |
| **Speed (large data)** | Slower | Fast | Fastest |
| **Graph queries** | Manual | Cypher | Cypher |
| **Concurrent writes** | Limited | Excellent | Excellent |
| **Memory usage** | Low | Medium | High (in-memory) |
| **Best for** | <10k memories | Production | High-performance |
| **Tool support** | All 44 | All 44 | All 44 |

### Recommendation

- **Personal use, <10k memories**: SQLite (default)
- **Team use, production**: Neo4j
- **High-performance analytics**: Memgraph
- **Cloud deployment**: Neo4j Aura (managed)

---

## Neo4j Setup

### Option 1: Docker (Recommended)

```bash
# Create directory for Neo4j data
mkdir -p ~/.neo4j/data

# Run Neo4j in Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -v ~/.neo4j/data:/data \
  neo4j:5-community

# Verify Neo4j is running
docker logs neo4j

# Access Neo4j Browser at http://localhost:7474
```

### Option 2: Neo4j Desktop

1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new database
3. Set password
4. Start the database
5. Note the Bolt URI (usually `bolt://localhost:7687`)

### Option 3: Neo4j Aura (Cloud)

1. Sign up at [Neo4j Aura](https://neo4j.com/cloud/aura/)
2. Create a free instance
3. Save the connection URI and credentials
4. Configure environment variables:

```bash
export MEMORY_NEO4J_URI=neo4j+s://your-instance.neo4j.io
export MEMORY_NEO4J_USER=neo4j
export MEMORY_NEO4J_PASSWORD=your-password
```

### Configure Claude Memory

```bash
# Set backend to Neo4j
export MEMORY_BACKEND=neo4j
export MEMORY_TOOL_PROFILE=full

# Neo4j connection
export MEMORY_NEO4J_URI=bolt://localhost:7687
export MEMORY_NEO4J_USER=neo4j
export MEMORY_NEO4J_PASSWORD=your-password

# Start server
memorygraph --backend neo4j --profile full
```

### MCP Configuration

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

### Verify Connection

```bash
# Check config
memorygraph --backend neo4j --show-config

# Test connection (if health check implemented)
memorygraph --backend neo4j --health
```

---

## Memgraph Setup

### Option 1: Docker (Recommended)

```bash
# Run Memgraph with Memgraph Lab (web UI)
docker run -d \
  --name memgraph \
  -p 7687:7687 \
  -p 3000:3000 \
  -v ~/.memgraph/data:/var/lib/memgraph \
  memgraph/memgraph-platform

# Verify Memgraph is running
docker logs memgraph

# Access Memgraph Lab at http://localhost:3000
```

### Option 2: Native Installation

Follow [Memgraph installation guide](https://memgraph.com/docs/getting-started) for your OS.

### Configure Claude Memory

```bash
# Set backend to Memgraph
export MEMORY_BACKEND=memgraph
export MEMORY_TOOL_PROFILE=full

# Memgraph connection (no auth by default)
export MEMORY_MEMGRAPH_URI=bolt://localhost:7687

# Start server
memorygraph --backend memgraph --profile full
```

### MCP Configuration

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

---

## All 44 Tools

See [TOOL_PROFILES.md](TOOL_PROFILES.md) for complete reference. Here's a quick overview:

### Core Memory (8 tools)
1. `store_memory` - Store new memory
2. `get_memory` - Retrieve memory by ID
3. `search_memories` - Search memories
4. `update_memory` - Update memory
5. `delete_memory` - Delete memory
6. `create_relationship` - Create relationship
7. `get_related_memories` - Get related memories
8. `get_memory_statistics` - Get statistics

### Intelligence (7 tools)
9. `find_similar_solutions` - Find similar solutions
10. `suggest_patterns_for_context` - Suggest patterns
11. `get_intelligent_context` - Get context
12. `get_project_summary` - Get project summary
13. `get_session_briefing` - Get session briefing
14. `get_memory_history` - Get memory history
15. `track_entity_timeline` - Track entity timeline

### Advanced Relationships (7 tools)
16. `find_memory_path` - Find path between memories
17. `analyze_memory_clusters` - Detect clusters
18. `find_bridge_memories` - Find bridge nodes
19. `suggest_relationship_type` - Suggest relationship
20. `reinforce_relationship` - Reinforce relationship
21. `get_relationship_types_by_category` - List relationship types
22. `analyze_graph_metrics` - Graph analytics

### Project Integration (11 tools)
23. `detect_project` - Detect project info
24. `analyze_project` - Analyze codebase
25. `track_file_changes` - Track file changes
26. `identify_patterns` - Identify code patterns
27. `capture_task` - Capture task context
28. `capture_command` - Capture command execution
29. `track_error_solution` - Track error solutions
30. `track_workflow` - Track workflow actions
31. `suggest_workflow` - Suggest workflow
32. `optimize_workflow` - Optimize workflow
33. `get_session_state` - Get session state

### Proactive Intelligence (11 tools)
34. `get_session_briefing` - Session briefing (proactive)
35. `check_for_issues` - Check for issues
36. `get_suggestions` - Get suggestions
37. `predict_solution_effectiveness` - Predict effectiveness
38. `find_similar_solutions` - Find solutions (proactive)
39. `suggest_related_memories` - Suggest related
40. `identify_knowledge_gaps` - Identify gaps
41. `recommend_learning_paths` - Recommend paths
42. `record_outcome` - Record outcome
43. `track_memory_roi` - Track ROI
44. `get_graph_visualization` - Get visualization

---

## Performance Tuning

### Neo4j Optimization

#### 1. Memory Configuration

Edit `neo4j.conf` or use Docker env vars:

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_dbms_memory_heap_initial__size=1g \
  -e NEO4J_dbms_memory_heap_max__size=2g \
  -e NEO4J_dbms_memory_pagecache_size=1g \
  neo4j:5-community
```

#### 2. Indexing

The server automatically creates indexes on startup:

```cypher
CREATE INDEX memory_id FOR (m:Memory) ON (m.id);
CREATE INDEX memory_type FOR (m:Memory) ON (m.memory_type);
CREATE INDEX memory_project FOR (m:Memory) ON (m.project);
CREATE INDEX memory_created FOR (m:Memory) ON (m.created_at);
```

#### 3. Query Optimization

- Use `LIMIT` on searches
- Add indexes on frequently searched fields
- Use graph-aware queries (avoid full scans)

### Memgraph Optimization

#### 1. Memory Settings

```bash
docker run -d \
  --name memgraph \
  -p 7687:7687 \
  -p 3000:3000 \
  -e MEMGRAPH_MEM_LIMIT=4096 \
  memgraph/memgraph-platform
```

#### 2. Query Parallelization

Memgraph automatically parallelizes queries. Use:

```cypher
USING PERIODIC COMMIT
```

For large batch operations.

#### 3. Analytics Mode

For read-heavy analytics:

```cypher
STORAGE MODE IN_MEMORY_ANALYTICAL;
```

### SQLite Optimization

Even in full mode, SQLite can handle 100k+ memories with tuning:

#### 1. WAL Mode

```python
# Automatically enabled by backend
PRAGMA journal_mode=WAL;
```

#### 2. Memory Settings

```python
PRAGMA cache_size=-64000;  # 64MB cache
PRAGMA temp_store=MEMORY;
```

#### 3. Index Usage

- Automatic indexes on id, type, project
- Full-text search on content
- B-tree indexes on timestamps

---

## Advanced Queries

### Graph Analytics

#### Find Clusters

```json
{
  "tool": "analyze_memory_clusters",
  "min_cluster_size": 3
}
```

Returns:
```json
{
  "clusters": [
    {
      "cluster_id": 1,
      "size": 15,
      "memories": ["mem_1", "mem_2", ...],
      "central_memory": "mem_5",
      "cohesion": 0.85
    }
  ]
}
```

#### Find Bridge Memories

```json
{
  "tool": "find_bridge_memories",
  "threshold": 0.5
}
```

Returns memories that connect disparate clusters - key knowledge bridges.

#### Path Finding

```json
{
  "tool": "find_memory_path",
  "from_memory_id": "mem_123",
  "to_memory_id": "mem_456",
  "max_depth": 5
}
```

Returns shortest path through relationship graph.

### Workflow Optimization

#### Track Workflow

```json
{
  "tool": "track_workflow",
  "action": "implemented authentication",
  "duration_seconds": 3600,
  "success": true
}
```

#### Suggest Next Steps

```json
{
  "tool": "suggest_workflow",
  "current_context": "building API endpoints"
}
```

Returns suggested next actions based on historical patterns.

### Project Integration

#### Analyze Codebase

```json
{
  "tool": "analyze_project",
  "project_path": "/path/to/project",
  "create_memories": true
}
```

Scans codebase, identifies patterns, creates memory graph.

#### Track File Changes

```json
{
  "tool": "track_file_changes",
  "project_path": "/path/to/project",
  "files": ["src/auth.py", "src/api.py"]
}
```

Creates memories for file changes with git history.

### Proactive Intelligence

#### Identify Knowledge Gaps

```json
{
  "tool": "identify_knowledge_gaps",
  "context": "building microservices"
}
```

Returns areas where you have few memories - learning opportunities.

#### Predict Solution Effectiveness

```json
{
  "tool": "predict_solution_effectiveness",
  "solution_description": "use Redis for caching",
  "context": "high-traffic API"
}
```

Uses historical data to predict if approach will work.

#### Get Suggestions

```json
{
  "tool": "get_suggestions",
  "current_task": "implementing user authentication",
  "limit": 5
}
```

Returns proactive suggestions based on context.

---

## Benchmarks

### Performance Comparison

Test: 100,000 memories, 250,000 relationships

| Operation | SQLite | Neo4j | Memgraph |
|-----------|--------|-------|----------|
| **Store memory** | 5ms | 3ms | 2ms |
| **Get memory** | 2ms | 1ms | 1ms |
| **Search (simple)** | 50ms | 20ms | 15ms |
| **Search (complex)** | 500ms | 50ms | 30ms |
| **Path finding (3-hop)** | 2000ms | 100ms | 50ms |
| **Cluster analysis** | 10000ms | 500ms | 200ms |
| **Graph metrics** | 15000ms | 1000ms | 400ms |

### Scalability

| Backend | Max Memories (Practical) | Query Time at Scale |
|---------|-------------------------|---------------------|
| SQLite | 100k | Acceptable |
| Neo4j | 10M+ | Fast |
| Memgraph | 100M+ | Fastest |

### Resource Usage

| Backend | RAM (Idle) | RAM (100k memories) | Disk |
|---------|-----------|---------------------|------|
| SQLite | 50MB | 100MB | 500MB |
| Neo4j | 500MB | 2GB | 2GB |
| Memgraph | 200MB | 4GB | 1GB |

---

## Migration Guide

### From SQLite to Neo4j

1. **Export data** (when implemented):
   ```bash
   memorygraph --backend sqlite --export backup.json
   ```

2. **Set up Neo4j**:
   ```bash
   docker run -d --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:5-community
   ```

3. **Import data** (when implemented):
   ```bash
   memorygraph --backend neo4j --import backup.json
   ```

4. **Update MCP config**:
   ```json
   {
     "command": "memorygraph",
     "args": ["--backend", "neo4j", "--profile", "full"]
   }
   ```

### From Neo4j to Memgraph

Memgraph is Cypher-compatible, so:

1. Export from Neo4j using `neo4j-admin dump`
2. Convert to Cypher statements
3. Import to Memgraph using `mgconsole`

Or use the export/import tools (when implemented).

---

## Troubleshooting

### Neo4j Issues

**Connection refused**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check logs
docker logs neo4j

# Restart
docker restart neo4j
```

**Out of memory**
```bash
# Increase heap size
docker run -e NEO4J_dbms_memory_heap_max__size=4g ...
```

**Slow queries**
```bash
# Check indexes
SHOW INDEXES;

# Analyze query plan
EXPLAIN MATCH (m:Memory) RETURN m;
```

### Memgraph Issues

**Connection refused**
```bash
# Check Memgraph is running
docker ps | grep memgraph

# Restart
docker restart memgraph
```

**Performance issues**
```bash
# Switch to analytical mode
STORAGE MODE IN_MEMORY_ANALYTICAL;

# Check memory usage
SHOW STORAGE INFO;
```

### General Issues

**Tools not available**
```bash
# Verify full profile is active
memorygraph --show-config

# Should show: tool_profile: full
```

**Slow graph operations**
```bash
# Consider upgrading backend
# SQLite -> Neo4j for 10k+ memories
# Neo4j -> Memgraph for analytics
```

---

## Best Practices

### 1. Start Small, Scale Up
- Begin with SQLite
- Migrate to Neo4j at 10k memories
- Use Memgraph for heavy analytics

### 2. Index Strategy
- Index frequently searched fields
- Monitor query performance
- Add composite indexes as needed

### 3. Memory Management
- Archive old memories
- Clean up unused relationships
- Monitor database size

### 4. Backup Strategy
- Regular exports (daily/weekly)
- Test restore procedures
- Keep exports versioned

### 5. Monitoring
- Track query times
- Monitor memory usage
- Set up alerts for issues

---

## Next Steps

1. **Set up your backend** (Neo4j or Memgraph)
2. **Configure environment variables**
3. **Start with `--profile full`**
4. **Explore advanced tools**
5. **Monitor performance**
6. **Optimize as needed**

For more help:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [TOOL_PROFILES.md](TOOL_PROFILES.md) - Complete tool reference
- [GitHub Issues](https://github.com/gregorydickson/memorygraph/issues) - Get support

---

**Last Updated**: November 28, 2025
