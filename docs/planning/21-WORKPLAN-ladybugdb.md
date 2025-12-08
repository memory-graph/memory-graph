# Workplan 21: LadybugDB Backend Completion

> ⏸️ **STATUS: PENDING** (2025-12-08)
>
> **Priority**: 🟡 MEDIUM - Backend expansion
> **Prerequisites**: WP16 (SDK) and WP20 (Cloud) releases complete
> **Estimated Effort**: 14-21 hours

---

## Overview

Complete the LadybugDB backend implementation to production-ready status. The current skeleton implementation is missing critical GraphBackend methods and has security/quality issues identified in code review.

**Current State**: Skeleton with ~30% implementation
**Target State**: Full GraphBackend implementation matching FalkorDBLite quality

---

## Parallel Execution Guide

This workplan can be executed with **2 parallel agents** after Section 1 is complete.

### Dependency Graph

```
Section 1: Core Methods (SEQUENTIAL - must complete first)
    │
    ├──► Section 2: Query/Search Methods ──┐
    │                                       ├──► Section 4: Testing
    └──► Section 3: Relationship Methods ──┘
                                            │
                                            ▼
                                    Section 5: Documentation
```

### Parallel Work Units

| Agent | Section | Dependencies | Can Run With |
|-------|---------|--------------|--------------|
| **Agent 1** | Section 1: Core Methods | None | Solo (prerequisite) |
| **Agent 2** | Section 2: Query/Search | Section 1 | Agent 3 |
| **Agent 3** | Section 3: Relationships | Section 1 | Agent 2 |
| **Agent 4** | Section 4: Testing | Sections 2-3 | Solo |
| **Agent 5** | Section 5: Documentation | Section 4 | Solo |

---

## Section 1: Core Infrastructure (CRITICAL)

### 1.1 Fix Parameterized Query Support

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/ladybugdb_backend.py`

**Current Issue**: Parameters are ignored, creating SQL injection vulnerability.

**Tasks**:
- [ ] Research LadybugDB's parameterized query support
- [ ] If supported: Implement proper parameter passing in `execute_query()`
- [ ] If not supported: Implement query sanitization/escaping
- [ ] Add security warning to docstring if parameterization unavailable
- [ ] Update all query construction to use safe patterns

**Acceptance Criteria**:
- No string interpolation with user data in queries
- All queries use either parameterization or sanitization
- Security documented in module docstring

### 1.2 Fix Result Format Handling

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/ladybugdb_backend.py`

**Current Issue**: Code expects dict results, but LadybugDB returns arrays.

**Tasks**:
- [ ] Verify actual result format from LadybugDB `get_next()` method
- [ ] Create `_result_to_dict(row, columns)` helper method
- [ ] Update `execute_query()` to return consistent dict format
- [ ] Fix `health_check()` result access (line 200)
- [ ] Add column name extraction from query results

**Reference**: See FalkorDBLite's result handling pattern

### 1.3 Add Type Conversion Helpers

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/ladybugdb_backend.py`

**Tasks**:
- [ ] Implement `_ladybugdb_to_memory(data: dict) -> Memory`
- [ ] Implement `_memory_to_properties(memory: Memory) -> dict`
- [ ] Implement `_parse_datetime(dt_value) -> datetime`
- [ ] Implement `_ensure_utc(dt: datetime) -> datetime`
- [ ] Implement `_ladybugdb_to_relationship(data: dict) -> Relationship`

**Reference**: Copy patterns from `falkordblite_backend.py` lines 110-180

### 1.4 Fix Exception Types

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/ladybugdb_backend.py:149-151`

**Tasks**:
- [ ] Change query execution errors from `SchemaError` to `DatabaseConnectionError`
- [ ] Reserve `SchemaError` for schema initialization failures only
- [ ] Review all exception usage for consistency

---

## Section 2: Memory CRUD Methods

### 2.1 Implement store_memory()

**Tasks**:
- [ ] Implement `async def store_memory(self, memory: Memory) -> str`
- [ ] Generate UUID if not provided
- [ ] Convert Memory to properties dict
- [ ] Create Cypher CREATE query
- [ ] Handle duplicate key errors
- [ ] Return memory ID

**Cypher Pattern**:
```cypher
CREATE (m:Memory {
    id: $id,
    type: $type,
    title: $title,
    content: $content,
    tags: $tags,
    importance: $importance,
    created_at: $created_at,
    updated_at: $updated_at
})
RETURN m.id
```

### 2.2 Implement get_memory()

**Tasks**:
- [ ] Implement `async def get_memory(self, memory_id: str, include_relationships: bool = True) -> Optional[Memory]`
- [ ] Query by memory ID
- [ ] Optionally fetch relationships
- [ ] Convert result to Memory object
- [ ] Return None if not found

### 2.3 Implement update_memory()

**Tasks**:
- [ ] Implement `async def update_memory(self, memory: Memory) -> bool`
- [ ] Use Cypher MATCH...SET pattern
- [ ] Update updated_at timestamp
- [ ] Return True on success, False if not found

### 2.4 Implement delete_memory()

**Tasks**:
- [ ] Implement `async def delete_memory(self, memory_id: str) -> bool`
- [ ] Delete memory node
- [ ] Delete all connected relationships
- [ ] Return True on success

### 2.5 Implement get_all_memories()

**Tasks**:
- [ ] Implement `async def get_all_memories(self, limit: int = 100, offset: int = 0) -> List[Memory]`
- [ ] Support pagination with SKIP and LIMIT
- [ ] Order by created_at descending
- [ ] Convert results to Memory objects

---

## Section 3: Relationship Methods

### 3.1 Implement create_relationship()

**Tasks**:
- [ ] Implement `async def create_relationship(self, relationship: Relationship) -> str`
- [ ] Validate source and target memories exist
- [ ] Create relationship with properties
- [ ] Handle duplicate relationship errors
- [ ] Return relationship ID

**Cypher Pattern**:
```cypher
MATCH (a:Memory {id: $from_id}), (b:Memory {id: $to_id})
CREATE (a)-[r:$type {
    id: $id,
    strength: $strength,
    confidence: $confidence,
    created_at: $created_at
}]->(b)
RETURN r.id
```

### 3.2 Implement get_relationships()

**Tasks**:
- [ ] Implement `async def get_relationships(self, memory_id: str, direction: str = "both", relationship_type: Optional[str] = None) -> List[Relationship]`
- [ ] Support direction: "outgoing", "incoming", "both"
- [ ] Optional filter by relationship type
- [ ] Convert results to Relationship objects

### 3.3 Implement delete_relationship()

**Tasks**:
- [ ] Implement `async def delete_relationship(self, from_id: str, to_id: str, relationship_type: str) -> bool`
- [ ] Delete specific relationship between nodes
- [ ] Return True on success

### 3.4 Implement get_related_memories()

**Tasks**:
- [ ] Implement `async def get_related_memories(self, memory_id: str, relationship_types: Optional[List[str]] = None, max_depth: int = 1) -> List[Memory]`
- [ ] Support multi-hop traversal
- [ ] Filter by relationship types
- [ ] Return unique memories

---

## Section 4: Search and Query Methods

### 4.1 Implement search_memories()

**Tasks**:
- [ ] Implement `async def search_memories(self, search_query: SearchQuery) -> List[Memory]`
- [ ] Support text search on title and content
- [ ] Support filtering by:
  - [ ] Memory types
  - [ ] Tags
  - [ ] Date range
  - [ ] Importance threshold
- [ ] Support pagination
- [ ] Support sorting

### 4.2 Implement recall_memories()

**Tasks**:
- [ ] Implement natural language recall if applicable
- [ ] Or delegate to search_memories with appropriate query

### 4.3 Complete Schema Initialization

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/ladybugdb_backend.py:153-180`

**Tasks**:
- [ ] Add multi-tenant index support (check `Config.is_multi_tenant_mode()`)
- [ ] Add all indexes from FalkorDBLite:
  - [ ] type index
  - [ ] created_at index
  - [ ] importance index
  - [ ] confidence index (for relationships)
- [ ] Add proper error handling for constraint creation
- [ ] Add debug logging for schema operations

---

## Section 5: Testing

### 5.1 Fix Unit Test Mocking

**File**: `/Users/gregorydickson/claude-code-memory/tests/backends/test_ladybugdb_backend.py`

**Tasks**:
- [ ] Fix duplicate return value in `setup_mock_ladybug()` (line 68-74)
- [ ] Align mock result format with actual LadybugDB behavior
- [ ] Add tests for all new methods:
  - [ ] store_memory tests
  - [ ] get_memory tests
  - [ ] update_memory tests
  - [ ] delete_memory tests
  - [ ] search_memories tests
  - [ ] create_relationship tests
  - [ ] get_relationships tests
  - [ ] delete_relationship tests
- [ ] Add edge case tests:
  - [ ] Empty results
  - [ ] Not found errors
  - [ ] Duplicate key errors
  - [ ] Connection errors

### 5.2 Complete Integration Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/backends/test_ladybugdb_integration.py`

**Tasks**:
- [ ] Fix duplicate cleanup code (lines 60-62)
- [ ] Use unique table names to prevent test conflicts
- [ ] Add comprehensive integration tests:
  - [ ] Full Memory CRUD lifecycle
  - [ ] Relationship creation and traversal
  - [ ] Search with various filters
  - [ ] Multi-hop relationship queries
  - [ ] Pagination
  - [ ] Error conditions

### 5.3 Add Security Tests

**Tasks**:
- [ ] Test parameterized query handling
- [ ] Test injection attempt handling
- [ ] Test input validation

---

## Section 6: Documentation

### 6.1 Update Module Docstring

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/ladybugdb_backend.py:1-6`

**Tasks**:
- [ ] Fix inaccurate comparison to Kuzu
- [ ] Document actual API compatibility
- [ ] Add security notes if parameterization not supported
- [ ] Document result format handling

### 6.2 Update README

**File**: `/Users/gregorydickson/claude-code-memory/README.md`

**Tasks**:
- [ ] Add LadybugDB to supported backends section
- [ ] Document installation: `pip install real-ladybug`
- [ ] Add configuration example
- [ ] Document environment variables

### 6.3 Add Backend-Specific Documentation

**File**: `/Users/gregorydickson/claude-code-memory/docs/backends/LADYBUGDB.md` (new)

**Tasks**:
- [ ] Create backend-specific documentation
- [ ] Document setup and configuration
- [ ] Document limitations vs other backends
- [ ] Add troubleshooting section

---

## Acceptance Criteria

### Functional
- [ ] All GraphBackend abstract methods implemented
- [ ] All Memory CRUD operations working
- [ ] All Relationship operations working
- [ ] Search with filters working
- [ ] Pagination working
- [ ] Multi-tenant mode supported (if enabled)

### Quality
- [ ] No SQL/Cypher injection vulnerabilities
- [ ] Consistent exception handling
- [ ] Type hints on all methods
- [ ] Docstrings on all public methods
- [ ] 90%+ test coverage for new code

### Testing
- [ ] All unit tests passing
- [ ] All integration tests passing (when real_ladybug installed)
- [ ] Tests properly skip when dependency missing

### Documentation
- [ ] README updated
- [ ] Module docstrings accurate
- [ ] Backend-specific docs created

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Methods implemented | 100% of GraphBackend |
| Test coverage | 90%+ |
| Security issues | 0 |
| Integration tests | 15+ |
| Documentation | Complete |

---

## Dependencies

**External**:
- `real-ladybug` Python package

**Internal**:
- GraphBackend base class
- Memory and Relationship models
- Config for multi-tenant mode

---

## Reference Files

Use these as implementation references:
- `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/falkordblite_backend.py` - Primary reference
- `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/sqlite_backend.py` - SQL patterns
- `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/base.py` - Interface definition

---

## Notes for Coding Agent

1. **Start with Section 1** - Infrastructure must be fixed before methods can work
2. **Use FalkorDBLite as reference** - It's the most similar backend
3. **Test with real_ladybug if available** - Integration tests are critical
4. **Security first** - No string interpolation in queries
5. **Maintain consistency** - Follow patterns from other backends

---

**Last Updated**: 2025-12-08
**Status**: PENDING
**Next Step**: Complete WP16 and WP20 releases first
