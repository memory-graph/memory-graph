# ADR 016: Bi-Temporal Tracking for Relationships

**Status**: Accepted

**Date**: 2025-12-05
**Accepted**: 2025-12-07

**Context**: Knowledge evolves over time. Solutions that worked yesterday may not work today. Dependencies change. Error causes get fixed. Currently, MemoryGraph lacks the ability to track when facts became true, when they stopped being true, and when we learned about them. This limits our ability to answer questions like "What solutions were we using when bug X first appeared?" or "How did our understanding of this problem evolve?"

---

## Decision

Implement **bi-temporal tracking** for relationships by adding four temporal fields that distinguish between validity time (when the fact was true) and transaction time (when we learned it):

### Temporal Fields

1. **`valid_from`** ∈ T (validity time): When the fact became true in the real world
2. **`valid_until`** ∈ T (validity time): When the fact stopped being true (NULL = still valid)
3. **`recorded_at`** ∈ T' (transaction time): When we ingested this fact into the system
4. **`invalidated_by`** (reference): ID of the relationship that superseded this one

### Implementation Approach

**Schema Changes**:
```sql
-- SQLite schema enhancement
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    from_id TEXT NOT NULL,
    to_id TEXT NOT NULL,
    rel_type TEXT NOT NULL,

    -- Temporal fields (NEW)
    valid_from TIMESTAMP NOT NULL,        -- When fact became true
    valid_until TIMESTAMP,                -- When fact stopped being true (NULL = current)
    recorded_at TIMESTAMP NOT NULL,       -- When we learned this fact
    invalidated_by TEXT,                  -- ID of relationship that superseded this

    -- Existing fields
    properties TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (from_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (invalidated_by) REFERENCES relationships(id) ON DELETE SET NULL
);

-- Performance indexes
CREATE INDEX idx_relationships_temporal ON relationships(valid_from, valid_until);
CREATE INDEX idx_relationships_current ON relationships(valid_until) WHERE valid_until IS NULL;
CREATE INDEX idx_relationships_recorded ON relationships(recorded_at);
```

**Default Behavior** (no breaking changes):
- `valid_from` defaults to current timestamp
- `valid_until` defaults to NULL (currently valid)
- `recorded_at` automatically set to ingestion time
- Queries without temporal parameters return only current relationships

**Temporal Query Patterns**:

1. **Current state** (default, most common):
```sql
SELECT * FROM relationships WHERE valid_until IS NULL;
```

2. **Point-in-time query**:
```sql
SELECT * FROM relationships
WHERE valid_from <= :query_time
  AND (valid_until IS NULL OR valid_until > :query_time);
```

3. **Relationship history**:
```sql
SELECT * FROM relationships
WHERE from_id = :entity_id
  AND rel_type = 'SOLVES'
ORDER BY valid_from DESC;
```

4. **Recent changes**:
```sql
SELECT * FROM relationships
WHERE recorded_at > :since_time
ORDER BY recorded_at DESC;
```

---

## Rationale

### Why Bi-Temporal?

**Single timestamp is insufficient**:
- Can't distinguish "when it was true" from "when we learned it"
- Example: "Alan Turing was born on June 23, 1912" (valid_from=1912) but "we recorded this in 2024" (recorded_at=2024)

**Validity time vs Transaction time**:
- **Validity time** (valid_from, valid_until): External reality
- **Transaction time** (recorded_at): System's knowledge

### Inspiration from Graphiti (Zep AI)

Graphiti's proven approach (arXiv:2501.13956):
- Four timestamps: `t_created`, `t_expired` (transaction time), `t_valid`, `t_invalid` (validity time)
- Temporal edge invalidation for contradictions
- Point-in-time queries without recomputation
- Semantic comparison for contradiction detection

**Our adaptation**:
- Simpler field names: `valid_from`, `valid_until`, `recorded_at`, `invalidated_by`
- Same core concept: track both when facts were true AND when we learned them
- Coding-specific optimizations (no LLM calls for invalidation by default)

### Use Cases

1. **Solution Evolution Tracking**:
```
2024-01-01: ErrorA SOLVED_BY SolutionX (works)
2024-06-01: ErrorA SOLVED_BY SolutionY (SolutionX stopped working)
Query: "What solution were we using in March 2024?" → SolutionX
```

2. **Point-in-Time Debugging**:
```
Query: "What dependencies did ServiceA have when bug Y first appeared?"
→ Time-travel to that date, see historical dependency graph
```

3. **Knowledge Audit**:
```
Query: "Show all facts we learned last month"
→ Filter by recorded_at timestamp
```

4. **Understanding When Solutions Stopped Working**:
```
Query: "When did SolutionX stop working?"
→ Check valid_until timestamp
```

---

## Alternatives Considered

### 1. Single Timestamp (Rejected)

**Approach**: Add only `created_at` and `deprecated_at`

**Pros**:
- Simplest implementation
- Lower storage overhead

**Cons**:
- Can't distinguish validity time from transaction time
- Loses important temporal distinctions
- Doesn't support Graphiti-level use cases

### 2. Full Event Sourcing (Rejected)

**Approach**: Store all relationship changes as immutable events

**Pros**:
- Complete audit trail
- Can replay to any point

**Cons**:
- Massive storage overhead (10x-50x)
- Query complexity
- Overkill for coding workflows
- Performance impact

### 3. Soft Delete with Archive Table (Rejected)

**Approach**: Move invalidated relationships to separate archive table

**Pros**:
- Keeps main table small
- Clear separation of current vs historical

**Cons**:
- Complicates point-in-time queries (need JOINs)
- Doesn't preserve temporal evolution in single view
- Migration complexity

### 4. Version Numbers (Rejected)

**Approach**: Add `version` field, increment on changes

**Pros**:
- Simple integer tracking
- Easy to find "latest"

**Cons**:
- No time information (can't query "as of date")
- Doesn't track validity periods
- Limited semantic meaning

---

## Consequences

### Positive

1. **Time-Travel Queries**: Query memory state as it existed at any past date
2. **Evolution Tracking**: See how understanding changed over time
3. **Contradiction Detection**: Automatically invalidate outdated facts
4. **Audit Trail**: Know when we learned each fact
5. **No Breaking Changes**: Default behavior unchanged (returns current only)
6. **Graphiti-Proven**: Based on production-tested architecture

### Negative

1. **Storage Overhead**: ~20% increase for temporal fields
2. **Query Complexity**: Temporal queries require WHERE clauses
3. **Migration Needed**: Existing databases need upgrade
4. **Index Overhead**: Additional indexes for temporal queries
5. **Testing Complexity**: Need to test temporal edge cases

### Neutral

1. **Implementation Effort**: 12-16 hours (significant but manageable)
2. **Learning Curve**: Users need to understand bi-temporal concepts
3. **Backend Compatibility**: Need to implement for SQLite, Neo4j, Turso, etc.

---

## Performance Impact

### Storage

**Before**:
```
Relationship: ~200 bytes (avg)
10,000 relationships = 2MB
```

**After**:
```
Relationship: ~240 bytes (avg, +20%)
10,000 relationships = 2.4MB (+400KB)
```

**Impact**: Negligible for typical workloads (10k-100k relationships)

### Query Performance

**Current state queries** (most common):
- Index on `valid_until IS NULL` enables fast filtering
- Target: <10ms (same as current)

**Point-in-time queries**:
- Composite index on `(valid_from, valid_until)` enables range scans
- Target: <50ms

**History queries**:
- Sequential scan on `from_id` + `rel_type`, sorted by `valid_from`
- Target: <100ms

### Migration Performance

**10,000 relationships**:
- Add columns: <1 second (ALTER TABLE)
- Create indexes: <2 seconds
- Total: <10 seconds

---

## Implementation Plan

### Phase 1: Schema Changes (Section 2-3 of Workplan 13)
1. Update SQLite schema with temporal fields
2. Update Neo4j/Turso/other backends
3. Add indexes for temporal queries
4. Update Backend interface

### Phase 2: Core Operations (Section 3-4)
1. Update `create_relationship()` to set temporal fields
2. Update `get_relationships()` to support `as_of` parameter
3. Implement `invalidate_relationship()` method
4. Add contradiction detection (optional, opt-in)

### Phase 3: Migration (Section 5)
1. Create migration script (006_add_bitemporal.py)
2. Set sensible defaults for existing data
3. Test on databases with 1000+ relationships
4. Provide rollback capability (with warnings)

### Phase 4: Tools & Testing (Section 6-7)
1. Add temporal query tools (`query_as_of`, `get_relationship_history`, `what_changed`)
2. Write comprehensive tests (25+ tests)
3. Integration tests for temporal workflows
4. Performance benchmarks

---

## Migration Strategy

### For Existing Data

**Defaults**:
- `valid_from` = `created_at` (assume fact was true when recorded)
- `valid_until` = NULL (assume still valid)
- `recorded_at` = `created_at`
- `invalidated_by` = NULL

**Rationale**: These defaults preserve current semantics while enabling temporal features

### User Migration Steps

1. Backup database: `memorygraph export backup.json`
2. Run migration: `memorygraph migrate` (auto-detects need for 006_add_bitemporal)
3. Verify: `memorygraph status` (shows migration success)
4. Test: Run existing queries (should work unchanged)
5. Use new features: Temporal queries now available

### Rollback

**Warning**: Downgrade loses temporal data!

```bash
# Export temporal data first
memorygraph export temporal_backup.json

# Rollback (WARNING: loses valid_from, valid_until, etc.)
memorygraph migrate downgrade 006
```

---

## References

**Research**:
- [Graphiti GitHub](https://github.com/getzep/graphiti) (Apache 2.0)
- [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/html/2501.13956v1) (arXiv:2501.13956)
- [Graphiti: Knowledge Graph Memory for an Agentic World](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/) (Neo4j Blog)
- [Building Temporal Knowledge Graphs with Graphiti](https://www.falkordb.com/blog/building-temporal-knowledge-graphs-graphiti/) (FalkorDB Blog)

**Internal**:
- PRODUCT_ROADMAP.md: Phase 2.2 (Bi-Temporal Tracking)
- ADR-012: Cycle Detection (relationship constraints)
- Workplan 13: Bi-Temporal Schema Implementation

---

## Decision

**Accept** this ADR and proceed with implementation following Workplan 13.

The bi-temporal approach is proven (Graphiti/Zep), addresses real user needs (time-travel queries, evolution tracking), and can be implemented with minimal breaking changes. The 20% storage overhead is acceptable for the significant capability gains.

---

**Last Updated**: 2025-12-06
**Status**: Accepted - Implementation Complete
**Implementation**: Workplan 13 completed successfully (Sections 1-8)
