# ADR 001: Neo4j Over PostgreSQL for Memory Storage

## Status
Accepted

## Date
2025-06-28

## Context
We needed to choose a database for storing Claude Code's memory system, including memories, relationships, and context. The key requirements were:

1. **Rich Relationship Modeling**: Memories are highly connected with typed relationships
2. **Graph Traversal**: Need to traverse memory networks to find related information
3. **Flexible Schema**: Memory types and properties may evolve
4. **Performance**: Fast queries for memory retrieval and relationship traversal
5. **MCP Compatibility**: Must work well with Model Context Protocol

## Decision Drivers
- **Relationship Complexity**: 35 relationship types across 7 categories (Causal, Solution, Context, Learning, Similarity, Workflow, Quality)
- **Query Patterns**: Frequently need to traverse relationships (e.g., "find all solutions related to this problem")
- **Data Model**: Memories are nodes with properties, relationships are first-class entities with metadata
- **Scalability**: Expected to grow to thousands of memories with dense connections

## Considered Options

### Option 1: PostgreSQL with Foreign Keys
**Pros:**
- Mature, well-understood technology
- ACID compliance
- Rich query language (SQL)
- Good tooling and ecosystem

**Cons:**
- Complex JOIN queries for relationship traversal
- Performance degrades with deep graph traversals
- Relationships are second-class (just foreign keys)
- Schema rigidity for evolving relationship types

### Option 2: Neo4j Graph Database
**Pros:**
- Native graph database optimized for relationships
- Cypher query language designed for graph patterns
- First-class relationships with properties
- Excellent performance for graph traversal
- Visual query tools and graph visualization

**Cons:**
- Less familiar to some developers
- Smaller ecosystem than PostgreSQL
- Additional infrastructure to manage

### Option 3: MongoDB with Document References
**Pros:**
- Flexible schema
- Good for hierarchical data
- Mature ecosystem

**Cons:**
- Relationships are still references, not first-class
- No native graph traversal
- Manual join implementation needed

## Decision
We chose **Neo4j** because:

1. **Native Graph Model**: Relationships are first-class entities with properties (strength, confidence, context)
2. **Query Performance**: Cypher makes complex relationship queries simple and fast
3. **Semantic Fit**: The memory model is inherently a graph (memories → relationships → memories)
4. **Traversal Efficiency**: Can traverse relationships in any direction without complex JOINs
5. **Future Proof**: Easy to add new relationship types and properties

## Example Use Case
Finding all solutions related to a problem (with depth limit):

**Neo4j Cypher:**
```cypher
MATCH (p:Memory {id: $problem_id})-[r:SOLVES|ADDRESSES*1..2]-(solution:Memory)
WHERE solution.type = 'solution'
RETURN solution, r
ORDER BY r.strength DESC
```

**PostgreSQL SQL:**
```sql
WITH RECURSIVE memory_tree AS (
  SELECT m.*, r.*, 1 as depth
  FROM memories m
  JOIN relationships r ON m.id = r.to_memory_id
  WHERE r.from_memory_id = $problem_id
  UNION ALL
  SELECT m.*, r.*, mt.depth + 1
  FROM memories m
  JOIN relationships r ON m.id = r.to_memory_id
  JOIN memory_tree mt ON r.from_memory_id = mt.id
  WHERE mt.depth < 2
)
SELECT * FROM memory_tree WHERE type = 'solution'
ORDER BY strength DESC;
```

The Neo4j version is clearer, more maintainable, and performs better.

## Consequences

### Positive
- **Simpler Queries**: Graph patterns are expressed naturally
- **Better Performance**: Native graph traversal algorithms
- **Rich Relationship Model**: Can store metadata on relationships
- **Visual Tools**: Neo4j Browser for exploring memory graphs
- **Flexibility**: Easy to add new node types and relationship types

### Negative
- **Learning Curve**: Team needs to learn Cypher
- **Deployment**: Additional database to deploy and manage
- **Tooling**: Fewer tools than PostgreSQL ecosystem
- **Backup/Restore**: Different patterns than traditional RDBMS

### Mitigations
- **Documentation**: Comprehensive Cypher examples in README
- **Docker**: Containerized deployment for easy setup
- **Async Driver**: Use async Neo4j Python driver for performance
- **Schema Docs**: Clear documentation of node types and relationships

## References
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Graph Database Use Cases](https://neo4j.com/use-cases/)
