# MemoryGraph Database Schema

This document describes the Neo4j database schema used by MemoryGraph.

## Node Types

### Memory Node
The core node type representing a stored memory.

**Labels:** `Memory`

**Properties:**
- `id` (string, unique) - Unique identifier for the memory
- `type` (string) - Type of memory (see MemoryType enum)
- `title` (string) - Short descriptive title
- `content` (string) - Detailed memory content
- `summary` (string, optional) - Brief summary
- `tags` (array of strings) - Categorization tags
- `importance` (float, 0.0-1.0) - Importance score
- `confidence` (float, 0.0-1.0) - Confidence in the memory
- `effectiveness` (float, 0.0-1.0, optional) - How effective this memory has been
- `usage_count` (integer) - Number of times this memory has been accessed
- `created_at` (ISO datetime string) - When the memory was created
- `updated_at` (ISO datetime string) - When the memory was last updated
- `last_accessed` (ISO datetime string, optional) - When the memory was last accessed

**Context Properties:** (prefixed with `context_`)
- `context_project_path` (string, optional) - Project directory path
- `context_files_involved` (string, optional) - JSON array of involved files
- `context_languages` (string, optional) - JSON array of programming languages
- `context_frameworks` (string, optional) - JSON array of frameworks used
- `context_technologies` (string, optional) - JSON array of technologies
- `context_git_commit` (string, optional) - Git commit hash
- `context_git_branch` (string, optional) - Git branch name
- `context_working_directory` (string, optional) - Working directory
- `context_timestamp` (ISO datetime string, optional) - Context timestamp
- `context_session_id` (string, optional) - Session identifier
- `context_user_id` (string, optional) - User identifier

## Memory Types

The system supports the following memory types:

- `task` - Development tasks and their execution
- `code_pattern` - Reusable code patterns and solutions
- `problem` - Issues and problems encountered
- `solution` - Solutions to problems
- `project` - Project-specific context and knowledge
- `technology` - Technology, framework, and tool knowledge
- `error` - Error messages and their context
- `fix` - Fixes applied to resolve errors
- `command` - CLI commands and their usage
- `file_context` - File-specific context and knowledge
- `workflow` - Development workflow patterns
- `general` - General development knowledge

## Relationship Types

### Causal Relationships
Represent cause-and-effect relationships:
- `CAUSES` - One thing causes another
- `TRIGGERS` - One thing triggers another
- `LEADS_TO` - One thing leads to another
- `PREVENTS` - One thing prevents another
- `BREAKS` - One thing breaks another

### Solution Relationships
Represent problem-solving relationships:
- `SOLVES` - A solution solves a problem
- `ADDRESSES` - A solution partially addresses a problem
- `ALTERNATIVE_TO` - Different approaches to the same problem
- `IMPROVES` - An enhancement to an existing solution
- `REPLACES` - A new solution that replaces an old one

### Context Relationships
Represent contextual connections:
- `OCCURS_IN` - Something occurs in a specific context
- `APPLIES_TO` - Something applies to a specific situation
- `WORKS_WITH` - Things that work well together
- `REQUIRES` - Dependencies between concepts
- `USED_IN` - Usage relationships

### Learning Relationships
Represent knowledge building:
- `BUILDS_ON` - Knowledge that builds on previous knowledge
- `CONTRADICTS` - Conflicting information
- `CONFIRMS` - Confirming evidence
- `GENERALIZES` - Specific cases that generalize to patterns
- `SPECIALIZES` - General patterns specialized for specific cases

### Similarity Relationships
Represent similarity and analogy:
- `SIMILAR_TO` - Similar concepts or solutions
- `VARIANT_OF` - Variations of the same concept
- `RELATED_TO` - General relatedness
- `ANALOGY_TO` - Analogous situations
- `OPPOSITE_OF` - Contrasting approaches

### Workflow Relationships
Represent process and workflow connections:
- `FOLLOWS` - Sequential order in workflows
- `DEPENDS_ON` - Dependencies in task execution
- `ENABLES` - One thing enables another
- `BLOCKS` - One thing blocks another
- `PARALLEL_TO` - Things that can be done in parallel

### Quality Relationships
Represent effectiveness and preference:
- `EFFECTIVE_FOR` - Effectiveness in specific contexts
- `INEFFECTIVE_FOR` - Known ineffectiveness
- `PREFERRED_OVER` - Preference relationships
- `DEPRECATED_BY` - Replacement relationships
- `VALIDATED_BY` - Validation relationships

## Relationship Properties

All relationships can have the following properties:

- `id` (string, unique) - Unique identifier for the relationship
- `strength` (float, 0.0-1.0) - Strength of the relationship
- `confidence` (float, 0.0-1.0) - Confidence in the relationship
- `context` (string, optional) - Context description
- `evidence_count` (integer) - Number of supporting observations
- `success_rate` (float, 0.0-1.0, optional) - Success rate for effectiveness relationships
- `created_at` (ISO datetime string) - When the relationship was created
- `last_validated` (ISO datetime string) - When the relationship was last validated
- `validation_count` (integer) - Number of times the relationship was validated
- `counter_evidence_count` (integer) - Number of counter-examples

## Indexes and Constraints

### Constraints
```cypher
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR (r:RELATIONSHIP) REQUIRE r.id IS UNIQUE;
```

### Indexes
```cypher
-- Type-based filtering
CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type);

-- Temporal queries
CREATE INDEX memory_created_at_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at);

-- Tag-based search
CREATE INDEX memory_tags_index IF NOT EXISTS FOR (m:Memory) ON (m.tags);

-- Full-text search
CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS FOR (m:Memory) ON EACH [m.title, m.content, m.summary];

-- Quality-based filtering
CREATE INDEX memory_importance_index IF NOT EXISTS FOR (m:Memory) ON (m.importance);
CREATE INDEX memory_confidence_index IF NOT EXISTS FOR (m:Memory) ON (m.confidence);

-- Context-based queries
CREATE INDEX memory_project_path_index IF NOT EXISTS FOR (m:Memory) ON (m.context_project_path);
```

## Example Queries

### Store a Memory
```cypher
MERGE (m:Memory {id: $id})
SET m += $properties
RETURN m.id as id
```

### Search Memories
```cypher
MATCH (m:Memory)
WHERE m.title CONTAINS $query OR m.content CONTAINS $query
  AND m.type IN $memory_types
  AND m.importance >= $min_importance
RETURN m
ORDER BY m.importance DESC, m.created_at DESC
LIMIT $limit
```

### Create Relationship
```cypher
MATCH (from:Memory {id: $from_id})
MATCH (to:Memory {id: $to_id})
CREATE (from)-[r:SOLVES $properties]->(to)
RETURN r.id as id
```

### Find Related Memories
```cypher
MATCH (start:Memory {id: $memory_id})
MATCH (start)-[r*1..2]-(related:Memory)
WHERE related.id <> start.id
RETURN DISTINCT related, r[0] as relationship
ORDER BY r[0].strength DESC, related.importance DESC
LIMIT 20
```

## Performance Considerations

1. **Indexing Strategy**: All frequently queried properties are indexed
2. **Full-text Search**: Enabled for content-based queries
3. **Relationship Traversal**: Limited depth to prevent expensive queries
4. **Query Optimization**: Use parameterized queries and appropriate LIMIT clauses
5. **Connection Pooling**: Configured for optimal performance under load

## Schema Evolution

The schema is designed to be extensible:

1. **New Memory Types**: Can be added by extending the MemoryType enum
2. **New Relationship Types**: Can be added by extending the RelationshipType enum
3. **Additional Properties**: Can be added to nodes and relationships as needed
4. **New Indexes**: Can be created for new query patterns

## Data Validation

All data is validated at the application layer using Pydantic models before being stored in Neo4j. This ensures:

1. **Type Safety**: All properties have correct types
2. **Constraints**: Required fields are present and within valid ranges
3. **Consistency**: Relationships reference valid memory IDs
4. **Normalization**: Text fields are properly formatted and normalized