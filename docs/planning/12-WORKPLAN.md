# Workplan 12: Semantic Navigation Tools (v0.10.0)

**Version Target**: v0.10.0
**Priority**: HIGH (Competitive Gap)
**Prerequisites**: Workplans 1-5 complete ✅
**Estimated Effort**: 8-12 hours

---

## Overview

Implement enhanced navigation tools that enable Claude to semantically traverse the knowledge graph without embeddings. This validates our graph-first approach (confirmed by Cipher's pivot away from vectors in v0.3.1).

**Philosophy**: Claude already understands language semantically. We don't need embeddings—we need better tools for LLM-driven graph navigation.

**Reference**: PRODUCT_ROADMAP.md Phase 2.3 (Semantic Navigation)

---

## Goal

Enable Claude to navigate memories using natural language intent by providing specialized MCP tools for:
- Browsing memory types and domains
- Traversing relationship chains automatically
- Finding solutions to problems via graph traversal
- Contextual search within related memories

---

## Success Criteria

- [x] 6 new navigation tools implemented and tested
- [ ] Navigation queries <50ms p95 latency (to be profiled)
- [x] Zero vector/embedding dependencies
- [x] 20+ tests passing for navigation tools (35 tests added)
- [ ] Demo video showing semantic navigation (deferred)
- [ ] Documentation with navigation examples (deferred)

---

## Section 1: New Navigation Tools

### 1.1 Implement `browse_memory_types` Tool

**Purpose**: Show entity types with counts, enabling high-level discovery

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/browse_tools.py`

**Implementation**:
```python
def browse_memory_types(backend: Backend) -> dict:
    """
    List all memory types with counts.

    Returns:
        {
            "types": [
                {"type": "solution", "count": 45},
                {"type": "error", "count": 23},
                {"type": "code_pattern", "count": 12},
                ...
            ]
        }
    """
```

**Tasks**:
- [x] Create `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/browse_tools.py`
- [x] Implement `browse_memory_types()` with SQL GROUP BY query
- [x] Add sorting by count (descending)
- [x] Include percentage of total for each type
- [x] Register as MCP tool in server.py

### 1.2 Implement `browse_by_project` Tool

**Purpose**: Navigate memories scoped to specific project paths

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/browse_tools.py`

**Implementation**:
```python
def browse_by_project(project_path: str, backend: Backend) -> dict:
    """
    List memories for a specific project.

    Args:
        project_path: Project identifier (e.g., "/Users/me/myproject")

    Returns:
        List of memories with project context
    """
```

**Tasks**:
- [x] Implement `browse_by_project()` in browse_tools.py
- [x] Filter by `context.project_path` field
- [x] Support fuzzy project path matching
- [x] Return summary stats (total memories, types breakdown)
- [x] Register as MCP tool

### 1.3 Implement `browse_domains` Tool

**Purpose**: High-level categorization (inspired by Cipher's Context Tree, but graph-based)

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/browse_tools.py`

**Implementation**:
```python
def browse_domains(backend: Backend) -> dict:
    """
    List high-level domains (auto-inferred from tags and content).

    Domains are clusters of related memories inferred from:
    - Common tags (e.g., "redis", "auth", "payment")
    - Technology types
    - Project paths

    Returns:
        {
            "domains": [
                {"name": "Redis", "memory_count": 15, "tags": ["redis", "cache"]},
                {"name": "Authentication", "memory_count": 23, "tags": ["auth", "oauth"]},
                ...
            ]
        }
    """
```

**Tasks**:
- [x] Implement domain clustering algorithm (tag frequency analysis)
- [x] Group memories by dominant tags
- [x] Calculate domain statistics
- [x] Register as MCP tool
- [ ] Add caching for performance (domains don't change often) (deferred)

---

## Section 2: Relationship Chain Tools

### 2.1 Implement `find_chain` Tool

**Purpose**: Auto-traverse SOLVES/CAUSES/DEPENDS_ON chains

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/chain_tools.py`

**Implementation**:
```python
def find_chain(
    memory_id: str,
    relationship_type: str,
    max_depth: int = 3,
    backend: Backend
) -> dict:
    """
    Automatically traverse relationship chains.

    Args:
        memory_id: Starting memory
        relationship_type: Type of chain to follow (SOLVES, CAUSES, DEPENDS_ON, etc.)
        max_depth: Maximum traversal depth

    Returns:
        {
            "chain": [
                {"memory": {...}, "relationship": "SOLVES"},
                {"memory": {...}, "relationship": "DEPENDS_ON"},
                ...
            ],
            "depth": 2
        }
    """
```

**Tasks**:
- [x] Create `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/chain_tools.py`
- [x] Implement BFS traversal for relationship chains
- [x] Support multiple relationship types in one query
- [x] Add cycle detection (reuse from ADR-012)
- [x] Register as MCP tool
- [x] Add tests for chain traversal

### 2.2 Implement `trace_dependencies` Tool

**Purpose**: Follow DEPENDS_ON/REQUIRES chains specifically

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/chain_tools.py`

**Implementation**:
```python
def trace_dependencies(memory_id: str, backend: Backend) -> dict:
    """
    Trace all dependencies for a given memory.

    Follows DEPENDS_ON and REQUIRES relationships to build
    a complete dependency tree.
    """
```

**Tasks**:
- [x] Implement specialized dependency traversal
- [x] Build dependency tree structure
- [x] Detect circular dependencies
- [x] Register as MCP tool

---

## Section 3: Contextual Search

### 3.1 Implement `contextual_search` Tool

**Purpose**: Search only within related memories (scoped search)

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/search_tools.py`

**Implementation**:
```python
def contextual_search(
    memory_id: str,
    query: str,
    max_depth: int = 2,
    backend: Backend
) -> dict:
    """
    Search within the context of a given memory.

    1. Find all memories related to memory_id (up to max_depth)
    2. Search query only within those related memories

    This provides semantic scoping without embeddings.
    """
```

**Tasks**:
- [x] Extend existing search_tools.py or create new file
- [x] Implement two-phase search (traverse → filter)
- [x] Reuse get_related_memories for traversal
- [x] Apply text search only to related set
- [x] Register as MCP tool
- [x] Add tests for contextual search

### 3.2 Enhance Existing `search_memories` Tool

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/search_tools.py`

**Enhancements**:
- [ ] Add intent classification (solution vs problem vs pattern)
- [ ] Add "why this result?" explanation field
- [ ] Include relationship context in results
- [ ] Add result ranking by importance + relationship strength

---

## Section 4: Tool Registration

### 4.1 Update Server Tool Registry

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`

**Tasks**:
- [x] Import new tools from browse_tools.py
- [x] Import new tools from chain_tools.py
- [x] Register all 6 new tools with MCP
- [x] Add tool descriptions optimized for LLM understanding
- [ ] Update server startup logging to show navigation tools (optional)

### 4.2 Tool Description Optimization

**Purpose**: Help Claude understand when to use each tool

**Tasks**:
- [ ] Write clear, intent-based tool descriptions
- [ ] Add usage examples in tool docstrings
- [ ] Include parameter constraints and defaults
- [ ] Test tool discovery by asking Claude "what tools do you have?"

---

## Section 5: Performance Optimization

### 5.1 Query Optimization

**Files**: All tool files

**Tasks**:
- [ ] Add database indexes for common navigation queries
- [ ] Optimize GROUP BY queries in browse_memory_types
- [ ] Add query result caching for browse_domains
- [ ] Profile queries with EXPLAIN ANALYZE
- [ ] Target <50ms p95 latency for all navigation queries

### 5.2 Add Query Caching

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cache.py`

**Tasks**:
- [ ] Create simple in-memory cache for browse operations
- [ ] Implement TTL-based cache invalidation
- [ ] Cache browse_domains results (expensive clustering)
- [ ] Cache browse_memory_types (changes infrequently)
- [ ] Add cache statistics for monitoring

---

## Section 6: Testing

### 6.1 Unit Tests for Navigation Tools

**File**: `/Users/gregorydickson/claude-code-memory/tests/tools/test_browse_tools.py`

**Tasks**:
- [x] Create test file for browse tools
- [x] Test browse_memory_types with various data
- [x] Test browse_by_project filtering
- [x] Test browse_domains clustering
- [x] Mock backend responses

**File**: `/Users/gregorydickson/claude-code-memory/tests/tools/test_chain_tools.py`

**Tasks**:
- [x] Create test file for chain tools
- [x] Test find_chain with SOLVES chains
- [x] Test find_chain with DEPENDS_ON chains
- [x] Test max_depth limits
- [x] Test cycle detection in chains
- [x] Test trace_dependencies

**File**: `/Users/gregorydickson/claude-code-memory/tests/tools/test_contextual_search.py`

**Tasks**:
- [x] Create test file for contextual search
- [x] Test contextual_search with various scopes
- [x] Test query filtering within context
- [x] Verify search doesn't leak outside context

### 6.2 Integration Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/integration/test_navigation_flow.py`

**Tasks**:
- [ ] Create end-to-end navigation test
- [ ] Simulate user query: "What solved the timeout issue?"
- [ ] Test flow: search → find_chain → contextual_search
- [ ] Verify results match expected navigation path
- [ ] Test performance under load (100+ memories)

### 6.3 Test Coverage Target

**Target**: 90%+ coverage for all new tools

**Tasks**:
- [ ] Run coverage report: `pytest --cov=src/memorygraph/tools/`
- [ ] Identify uncovered branches
- [ ] Add tests for edge cases
- [ ] Verify all error paths are tested

---

## Section 7: Documentation

### 7.1 Update Tool Documentation

**File**: `/Users/gregorydickson/claude-code-memory/docs/tools.md`

**Tasks**:
- [ ] Document all 6 new navigation tools
- [ ] Include usage examples for each tool
- [ ] Add navigation workflow examples
- [ ] Show how tools work together (e.g., browse → find_chain → contextual_search)

### 7.2 Create Navigation Guide

**File**: `/Users/gregorydickson/claude-code-memory/docs/guides/semantic-navigation.md`

**Content**:
```markdown
# Semantic Navigation Guide

How MemoryGraph enables Claude to navigate your knowledge graph semantically.

## Philosophy
Claude understands language. We provide tools for intelligent graph traversal.

## Navigation Workflows

### Finding Solutions to Problems
1. `search_memories(query="timeout", type="error")` → Find TimeoutError
2. `find_chain(memory_id, "SOLVES")` → Find RetryWithBackoff solution
3. `trace_dependencies(solution_id)` → Find ExponentialBackoff dependency

### Exploring Project Context
1. `browse_by_project("/path/to/project")` → List project memories
2. `browse_domains()` → See high-level categories
3. `contextual_search(domain_memory_id, "pattern")` → Find patterns in domain

## Tool Reference
[Document each tool with examples]
```

**Tasks**:
- [ ] Create semantic-navigation.md guide
- [ ] Include 5+ workflow examples
- [ ] Add diagrams showing navigation paths
- [ ] Include performance tips

### 7.3 Update README

**File**: `/Users/gregorydickson/claude-code-memory/README.md`

**Tasks**:
- [ ] Add "Semantic Navigation" feature highlight
- [ ] Mention new tools in features section
- [ ] Add comparison: "No embeddings needed"
- [ ] Link to navigation guide

---

## Section 8: Demo and Marketing

### 8.1 Create Demo Video

**Tasks**:
- [ ] Record asciinema demo showing navigation in action
- [ ] Script: "What solved the timeout issue?"
- [ ] Show Claude using browse → find_chain → result
- [ ] Highlight speed (<50ms queries)
- [ ] Upload to GitHub and include in README

### 8.2 Marketing Materials

**Tasks**:
- [ ] Write blog post: "Why We Chose Semantic Navigation Over Vectors"
- [ ] Create comparison diagram: Navigation vs Vector Search
- [ ] Update COMPARISON.md with navigation capabilities
- [ ] Prepare HN/Reddit post highlighting navigation

---

## Section 9: Migration and Backward Compatibility

### 9.1 Backward Compatibility

**Tasks**:
- [ ] Ensure existing tools (search_memories, get_related_memories) still work
- [ ] New tools are additive (no breaking changes)
- [ ] Test that old queries still work with new code

### 9.2 Database Indexes

**File**: Database migration (if needed)

**Tasks**:
- [ ] Add index on `type` column for browse_memory_types
- [ ] Add index on `context.project_path` for browse_by_project
- [ ] Add composite index on tags for browse_domains
- [ ] Create migration script if needed
- [ ] Test performance before/after indexes

---

## Acceptance Criteria Summary

### Functional
- [ ] All 6 navigation tools implemented and working
- [ ] Tools integrate seamlessly with existing search
- [ ] No vector/embedding dependencies
- [ ] Relationship chains traverse correctly

### Performance
- [ ] <50ms p95 latency for navigation queries
- [ ] browse_domains clustering completes in <100ms
- [ ] Cache hit rate >80% for browse operations

### Quality
- [ ] 20+ tests passing for navigation tools
- [ ] 90%+ test coverage for new code
- [ ] All edge cases handled (empty results, cycles, etc.)

### Documentation
- [ ] All tools documented with examples
- [ ] Navigation guide published
- [ ] Demo video created and embedded

---

## Notes for Coding Agent

**Important Implementation Details**:

1. **No LLM calls in tools**: Navigation tools should NOT call LLMs. Claude orchestrates, tools execute queries.

2. **Reuse existing code**:
   - Use get_related_memories for traversal
   - Reuse cycle detection from ADR-012
   - Extend existing search infrastructure

3. **Database queries**:
   - Use parameterized queries (prevent SQL injection)
   - Add indexes before testing performance
   - Profile queries with EXPLAIN

4. **Tool descriptions**:
   - Write for LLM consumption (clear intent signals)
   - Include when to use each tool
   - Provide parameter constraints

5. **Testing strategy**:
   - Unit test each tool in isolation
   - Integration test workflows (multi-tool sequences)
   - Performance test with realistic data volumes

---

## Dependencies

**Internal**:
- Existing search_memories implementation
- get_related_memories from relationship tools
- Cycle detection from ADR-012

**External**:
- None (no new dependencies)

---

## Estimated Timeline

| Section | Effort | Dependencies |
|---------|--------|--------------|
| Section 1: Browse Tools | 2-3 hours | None |
| Section 2: Chain Tools | 2-3 hours | get_related_memories |
| Section 3: Contextual Search | 2 hours | search_memories |
| Section 4: Tool Registration | 1 hour | All tools complete |
| Section 5: Performance | 2 hours | All tools complete |
| Section 6: Testing | 2-3 hours | All tools complete |
| Section 7: Documentation | 2 hours | All tools complete |
| Section 8: Demo/Marketing | 1-2 hours | Docs complete |
| Section 9: Migration | 1 hour | All complete |
| **Total** | **15-20 hours** | Sequential + parallel |

---

## References

- **PRODUCT_ROADMAP.md**: Phase 2.3 (Semantic Navigation)
- **ADR-012**: Cycle detection implementation
- **Cipher v0.3.1**: Validation of non-vector approach
- **docs/tools.md**: Existing tool documentation

---

**Last Updated**: 2025-12-05
**Status**: CORE IMPLEMENTATION COMPLETE
**Next Step**: Performance profiling and documentation (deferred to future workplan)
