# Cypher Compatibility Guide

This document outlines the Cypher dialect differences between supported graph database backends (Neo4j, Memgraph) and how the memory server handles them.

## Overview

MemoryGraph uses Cypher as its query language across all graph-based backends. While Neo4j and Memgraph both support Cypher, there are some dialect differences that need to be considered.

## Backend Comparison

| Feature | Neo4j | Memgraph | SQLite Fallback |
|---------|-------|----------|-----------------|
| Cypher Support | Full | Subset | Limited (translated) |
| FULLTEXT INDEX | ✅ Yes | ⚠️ Limited | ✅ FTS5 |
| Constraints | ✅ Full | ⚠️ Basic | ✅ Basic |
| APOC Procedures | ✅ Yes | ❌ No | N/A |
| Transactions | ✅ Yes | ✅ Yes | ✅ Yes |
| Graph Algorithms | ✅ GDS | ⚠️ Limited | ✅ NetworkX |

## Syntax Differences

### Index Creation

#### Neo4j Syntax
```cypher
-- Standard index
CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type)

-- Fulltext index
CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS
FOR (m:Memory) ON EACH [m.title, m.content, m.summary]
```

#### Memgraph Syntax
```cypher
-- Standard index
CREATE INDEX ON :Memory(type)

-- Text index (different from Neo4j FULLTEXT)
-- Memgraph doesn't fully support FULLTEXT INDEX
-- Use CREATE TEXT INDEX instead (limited functionality)
```

### Constraint Creation

#### Neo4j Syntax
```cypher
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE
```

#### Memgraph Syntax
```cypher
-- Pre-v2.11
CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE

-- Post-v2.11 (compatible with Neo4j syntax)
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE
```

## Feature Support Matrix

### Fulltext Search

**Neo4j**: Full support with advanced relevance scoring
```cypher
CALL db.index.fulltext.queryNodes("memory_content_index", "search terms")
YIELD node, score
RETURN node, score
ORDER BY score DESC
```

**Memgraph**: Limited text search support
- No FULLTEXT INDEX in the same way as Neo4j
- Can use CONTAINS operator for basic text matching
```cypher
MATCH (m:Memory)
WHERE m.content CONTAINS "search terms"
RETURN m
```

**SQLite**: FTS5 virtual tables
```sql
SELECT * FROM nodes_fts
WHERE nodes_fts MATCH 'search terms'
```

### Graph Algorithms

**Neo4j**: Graph Data Science (GDS) library
```cypher
CALL gds.pageRank.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
```

**Memgraph**: Built-in algorithms (limited set)
```cypher
MATCH path = (start:Memory)-[*..5]->(end:Memory)
WHERE start.id = $start_id
RETURN path
```

**SQLite**: NetworkX algorithms (Python-side)
```python
import networkx as nx
pagerank = nx.pagerank(graph)
```

## Backend-Specific Adaptations

The memory server automatically adapts queries for different backends:

### 1. Fulltext Index Queries

**Input** (generic):
```cypher
CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS
FOR (m:Memory) ON EACH [m.title, m.content, m.summary]
```

**Neo4j** (no change):
```cypher
CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS
FOR (m:Memory) ON EACH [m.title, m.content, m.summary]
```

**Memgraph** (skipped):
```cypher
RETURN 1  -- No-op query (fulltext not fully supported)
```

### 2. Constraint Creation

**Input** (Neo4j v5 syntax):
```cypher
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE
```

**Memgraph** (adapted for older versions):
```cypher
CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE
```

## Performance Considerations

### Neo4j
- **Strengths**:
  - Advanced indexing (fulltext, composite)
  - Mature query optimizer
  - Large graph handling (millions of nodes)
  - Enterprise features (clustering, backup)

- **Best For**:
  - Production deployments
  - Large knowledge graphs
  - Complex graph queries
  - Multi-user scenarios

### Memgraph
- **Strengths**:
  - In-memory performance (faster for small-medium graphs)
  - Real-time analytics
  - Simpler setup (no password by default)
  - Lower memory footprint

- **Best For**:
  - Development/testing
  - Real-time queries
  - Graphs under 10M nodes
  - Single-instance deployments

### SQLite Fallback
- **Strengths**:
  - Zero setup (no separate database server)
  - Portable (single file)
  - ACID transactions
  - Good for development

- **Best For**:
  - Development/testing
  - Single-user scenarios
  - Small graphs (< 10,000 nodes)
  - Portable deployments

## Limitations by Backend

### Neo4j
- ❌ Requires separate server installation
- ❌ Requires password configuration
- ❌ Higher resource usage

### Memgraph
- ❌ Limited fulltext search
- ❌ Smaller ecosystem than Neo4j
- ❌ Some APOC procedures not available
- ❌ In-memory first (persistence optional)

### SQLite
- ❌ No native graph query language
- ❌ Graph traversals slower (NetworkX overhead)
- ❌ Limited to single connection writes
- ❌ Not suitable for large graphs (> 10K nodes)

## Migration Between Backends

If you need to migrate from one backend to another:

### Export from Neo4j/Memgraph
```cypher
// Export all memories
MATCH (m:Memory)
RETURN m.id, properties(m) as props

// Export all relationships
MATCH (m1:Memory)-[r]->(m2:Memory)
RETURN m1.id, type(r), properties(r), m2.id
```

### Import to New Backend
Use the MCP tools to recreate memories and relationships:
```python
# Store memories
for memory_data in exported_memories:
    await store_memory(memory_data)

# Recreate relationships
for rel_data in exported_relationships:
    await create_relationship(
        from_id=rel_data["from_id"],
        to_id=rel_data["to_id"],
        relationship_type=rel_data["type"],
        properties=rel_data["properties"]
    )
```

## Recommendations

### For Development
1. **Start with SQLite**: No setup required
2. **Upgrade to Memgraph**: When testing graph performance
3. **Use Neo4j**: When preparing for production

### For Production
1. **Neo4j Community**: Best for most use cases
2. **Neo4j Enterprise**: For mission-critical deployments
3. **Memgraph**: For real-time analytics focus

### For Testing
1. **SQLite**: Unit tests (fast, isolated)
2. **Neo4j/Memgraph**: Integration tests (realistic)

## Environment Configuration

```bash
# Neo4j
export MEMORY_BACKEND=neo4j
export MEMORY_NEO4J_URI=bolt://localhost:7687
export MEMORY_NEO4J_PASSWORD=yourpassword

# Memgraph
export MEMORY_BACKEND=memgraph
export MEMORY_MEMGRAPH_URI=bolt://localhost:7687

# SQLite (auto-fallback)
export MEMORY_BACKEND=sqlite
export MEMORY_SQLITE_PATH=~/.memorygraph/memory.db

# Auto-select (recommended)
export MEMORY_BACKEND=auto  # Tries Neo4j → Memgraph → SQLite
```

## Future Compatibility

The backend abstraction layer is designed to support:
- Future Neo4j versions
- Memgraph updates
- Additional graph databases (e.g., ArangoDB, JanusGraph)

All Cypher dialect differences are handled in the backend implementation, ensuring that application code remains backend-agnostic.

## References

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Memgraph Cypher Documentation](https://memgraph.com/docs/cypher-manual)
- [NetworkX Documentation](https://networkx.org/documentation/stable/)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
