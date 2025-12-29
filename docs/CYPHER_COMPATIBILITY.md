# Cypher Compatibility Guide

This document outlines Cypher dialect differences between supported graph database backends (Neo4j, Memgraph, LadybugDB) and how the memory server handles them.

## Overview

MemoryGraph uses Cypher as its query language across all graph-based backends. While Neo4j, Memgraph, and LadybugDB all support Cypher, there are some dialect differences that need to be considered.

## Backend Comparison

| Feature | Neo4j | Memgraph | LadybugDB | SQLite Fallback |
|---------|-------|----------|------------|-----------------|
| Cypher Support | Full | Subset | Subset | Limited (translated) |
| Schema Required | ❌ No | ❌ No | ✅ Yes (NODE/REL TABLE) | ❌ No |
| FULLTEXT INDEX | ✅ Yes | ⚠️ Limited | ✅ Yes (via FTS extension) | ✅ FTS5 |
| Constraints | ✅ Full | ⚠️ Basic | ❌ No (PK only) | ✅ Basic |
| Indexes | ✅ Yes | ✅ Yes | ❌ No (PK auto) | ✅ Yes |
| APOC Procedures | ✅ Yes | ❌ No | ❌ No | N/A |
| Transactions | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Graph Algorithms | ✅ GDS | ⚠️ Limited | ⚠️ Limited | ✅ NetworkX |
| List Storage | Native | Native | JSON[] extension | N/A |

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

**LadybugDB** (uses FTS extension):
```cypher
INSTALL FTS
LOAD EXTENSION FTS
CALL CREATE_FTS_INDEX('Memory', 'memory_content_index', ['title', 'content', 'summary'])
```

### 2. Constraint Creation

**Input** (Neo4j v5 syntax):
```cypher
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE
```

**Neo4j** (no change):
```cypher
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS
FOR (m:Memory) REQUIRE m.id IS UNIQUE
```

**Memgraph** (adapted for older versions):
```cypher
CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE
```

**LadybugDB** (constraints not supported):
```cypher
-- LadybugDB does not support CREATE CONSTRAINT
-- Use PRIMARY KEY in NODE TABLE definition instead
CREATE NODE TABLE Memory(
    id STRING PRIMARY KEY,
    ...
)
```

### 3. Schema Initialization

**Neo4j/Memgraph** (schemaless - nodes/relationships can be created anytime):
```cypher
-- Can create nodes directly without schema
CREATE (m:Memory {id: '123', title: 'Test'})
```

**LadybugDB** (requires NODE TABLE and REL TABLE first):
```cypher
-- Must create NODE TABLE before creating nodes
CREATE NODE TABLE IF NOT EXISTS Memory(
    id STRING PRIMARY KEY,
    title STRING,
    content STRING,
    tags STRING,  -- Stored as JSON string
    ...
)

CREATE REL TABLE IF NOT EXISTS REL(
    FROM Memory TO Memory,
    id STRING,
    type STRING,
    ...
)

-- Then can create nodes
CREATE (m:Memory {id: '123', title: 'Test'})
```

### 4. List Field Handling (e.g., tags)

**Neo4j/Memgraph** (native list support):
```cypher
-- Storage: Tags stored as native list/array
MATCH (m:Memory)
WHERE ANY(tag IN $tags WHERE tag IN m.tags)
RETURN m
```

**LadybugDB** (JSON extension with native JSON array type):
```cypher
-- Schema: Tags defined as JSON[] array type
CREATE NODE TABLE Memory(
    id STRING PRIMARY KEY,
    tags JSON[],
    ...
)

-- Storage: Tags stored as JSON array (same as Neo4j/Memgraph)
MATCH (m:Memory {id: $id})
SET m.tags = $tags  -- Pass list directly, no serialization needed

-- Query: Uses same list operations as other backends
MATCH (m:Memory)
WHERE ANY(tag IN $tags WHERE tag IN m.tags)
RETURN m
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

### LadybugDB
- **Strengths**:
  - Embedded database (no separate server needed)
  - Low resource footprint
  - Fast for embedded use cases
  - Schema-defined tables (compile-time type checking)

- **Best For**:
  - Embedded applications
  - Single-user scenarios
  - Development/testing
  - Desktop applications

- **Limitations**:
  - Requires explicit schema (NODE TABLE, REL TABLE)
  - No index creation (primary keys only)
  - No constraint support (beyond PK)
  - Requires JSON extension for list/array types (JSON[], JSON, etc.)

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

### LadybugDB
- ❌ Requires explicit schema (NODE TABLE, REL TABLE)
- ❌ No CREATE INDEX support (primary keys only)
- ❌ No CREATE CONSTRAINT support
- ❌ List fields stored as JSON strings (not native arrays)
- ❌ Limited to embedded use (not multi-client)

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
1. **Start with SQLite**: No setup required, simple and reliable
2. **Use LadybugDB**: When you need schema-defined graph tables
3. **Upgrade to Memgraph**: When testing graph performance
4. **Use Neo4j**: When preparing for production

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

# LadybugDB
export MEMORY_BACKEND=ladybugdb
export MEMORY_LADYBUGDB_PATH=~/.memorygraph/memory.lbdb

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
