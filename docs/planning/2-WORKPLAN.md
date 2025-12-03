# 2-WORKPLAN: Test Coverage Improvements

**Goal**: Increase test coverage for server.py and Memgraph backend
**Priority**: HIGH - Improves code quality and confidence
**Estimated Tasks**: 35 tasks
**Target Coverage**: server.py 49% → 70%, Memgraph 28% → 70%

---

## Prerequisites

- [x] 1-WORKPLAN completed (datetime fixes, health check)
- [x] All existing tests passing

---

## 1. Server.py Test Coverage (49% → >70%)

**Current**: 49% coverage (721/1473 lines)
**Target**: >70% coverage (~1030 lines)
**Gap**: Need ~300 additional lines tested

### 1.1 Analyze Coverage Gaps

- [x] Run coverage report: `pytest --cov=src/memorygraph/server --cov-report=html`
- [x] Open `htmlcov/index.html` and review uncovered lines
- [x] Document which tool handlers have <50% coverage
- [x] List untested edge cases and error paths

**Output file**: Document findings for reference

### 1.2 Test Tool Handlers - Memory CRUD

Create/expand `/Users/gregorydickson/claude-code-memory/tests/test_server_tools.py`:

**store_memory handler**:
- [x] Test successful memory storage
- [x] Test with missing required fields (title, content)
- [x] Test with invalid memory type
- [x] Test with empty content
- [x] Test importance validation (must be 0.0-1.0)
- [x] Test with maximum field lengths

**get_memory handler**:
- [x] Test successful retrieval
- [x] Test with non-existent memory_id
- [x] Test include_relationships=True
- [x] Test include_relationships=False

**update_memory handler**:
- [x] Test successful full update
- [x] Test partial updates (only title, only tags, etc.)
- [x] Test with non-existent memory_id
- [x] Test validation failures on update

**delete_memory handler**:
- [x] Test successful deletion
- [x] Test with non-existent memory_id
- [x] Test cascade deletion of relationships

### 1.3 Test Tool Handlers - Search & Recall

**search_memories handler**:
- [x] Test basic text query
- [x] Test with memory_types filter
- [x] Test with tags filter
- [x] Test with min_importance filter
- [x] Test with project_path filter
- [x] Test with empty results
- [x] Test search_tolerance modes (strict, normal, fuzzy)
- [x] Test match_mode (any, all)
- [x] Test with limit parameter

**recall_memories handler** (convenience wrapper):
- [x] Test natural language query
- [x] Test with memory_types filter
- [x] Test with project_path filter
- [x] Test with limit parameter
- [x] Verify uses search_memories internally
- [x] Verify default tolerance is "normal"

### 1.4 Test Tool Handlers - Relationships

**create_relationship handler**:
- [x] Test successful relationship creation
- [x] Test with invalid from_memory_id
- [x] Test with invalid to_memory_id
- [x] Test with invalid relationship_type
- [x] Test strength validation (0.0-1.0)
- [x] Test confidence validation (0.0-1.0)
- [x] Test context extraction

**get_related_memories handler**:
- [x] Test with max_depth=1
- [x] Test with max_depth=2
- [x] Test with max_depth=3
- [x] Test with relationship_types filter
- [x] Test with no related memories
- [x] Test bidirectional relationships

### 1.5 Test Tool Handlers - Activity

**get_recent_activity handler**:
- [x] Test default 7-day window
- [x] Test custom day ranges (1, 30, 90 days)
- [x] Test with project filter
- [x] Test with no recent activity
- [x] Verify counts by memory type
- [x] Verify unresolved problems list

### 1.6 Test Error Handling Paths

- [x] Test invalid tool name
- [x] Test malformed tool arguments
- [x] Test backend initialization failure
- [x] Test database connection errors during tool execution
- [x] Test transaction rollback scenarios
- [ ] Test timeout scenarios (if implemented)

### 1.7 Test MCP Protocol Integration

- [x] Test list_tools returns all tool schemas
- [x] Test tool schema validation
- [x] Test error response format matches MCP spec
- [x] Test result serialization
- [x] Test JSON encoding of complex types (datetime, relationships)

### 1.8 Verify Coverage Target

- [x] Run coverage: `pytest --cov=src/memorygraph/server --cov-report=term-missing`
- [x] Verify coverage >70% (1,006 tests passing)
- [x] Document any remaining gaps <70%
- [ ] Add coverage badge to README if appropriate

---

## 2. Memgraph Backend Test Coverage (28% → >70%)

**Current**: 28% coverage
**Target**: >70% coverage
**Approach**: Add integration tests (unit tests exist)

### 2.1 Set Up Memgraph Test Infrastructure

- [x] Verify Memgraph Docker setup in CI
- [x] Create test fixtures in `/Users/gregorydickson/claude-code-memory/tests/backends/test_memgraph_backend.py`
- [x] Set up test database initialization
- [x] Add cleanup after tests

### 2.2 Integration Tests - CRUD Operations

- [x] Test create memory in Memgraph
- [x] Test retrieve memory by ID
- [x] Test update memory (full and partial)
- [x] Test delete memory
- [x] Test bulk memory operations (create 100 memories)

### 2.3 Integration Tests - Search Operations

- [x] Test basic text search
- [x] Test search with memory_types filter
- [x] Test search with tags filter
- [x] Test search with importance filter
- [x] Test search with project_path filter
- [x] Test full-text search performance
- [x] Test search_tolerance modes
- [ ] Test large result sets (>1000 results)

### 2.4 Integration Tests - Relationship Operations

- [x] Test create relationship
- [x] Test get related memories (depth=1)
- [x] Test get related memories (depth=2)
- [x] Test get related memories (depth=3)
- [x] Test relationship queries with type filters
- [x] Test delete memory with relationships (cascade)
- [x] Test bidirectional relationship traversal

### 2.5 Integration Tests - Edge Cases

- [ ] Test concurrent memory creation (10 parallel clients)
- [ ] Test concurrent memory updates (optimistic locking)
- [x] Test transaction handling
- [ ] Test connection pool exhaustion
- [ ] Test query timeout
- [ ] Test large content (>1MB per memory)

### 2.6 Performance Benchmarks

Create `/Users/gregorydickson/claude-code-memory/tests/benchmarks/test_memgraph_performance.py`:

- [ ] Benchmark insert throughput (memories/second)
- [ ] Benchmark search query latency (p50, p95, p99)
- [ ] Benchmark relationship traversal (depth 1-5)
- [ ] Compare with SQLite backend
- [ ] Document results in performance report

### 2.7 Verify Coverage Target

- [x] Run Memgraph tests: `pytest tests/backends/test_memgraph_backend.py -v`
- [x] Run coverage: `pytest --cov=src/memorygraph/backends/memgraph_backend --cov-report=term-missing`
- [x] Verify coverage >70%
- [x] Document any gaps

---

## Acceptance Criteria

### Server.py Coverage
- [x] Coverage increased from 49% to >70%
- [x] All tool handlers tested
- [x] Error handling paths covered
- [x] MCP protocol integration tested
- [x] At least 50 new test cases added

### Memgraph Backend Coverage
- [x] Coverage increased from 28% to >70%
- [x] Integration tests run successfully in CI
- [x] All CRUD operations tested
- [x] Search and relationship operations tested
- [ ] Edge cases covered (partial - some edge cases remain)
- [ ] Performance benchmarks documented

### Overall
- [x] Full test suite passes (1,006 tests)
- [x] No regressions in other modules
- [x] Coverage report shows improvement
- [x] Documentation updated with coverage metrics

---

## Notes

- TDD approach: Write tests before fixing bugs found during testing
- Integration tests require running Memgraph instance (Docker)
- Performance benchmarks are informational, not blocking
- Focus on common code paths first, edge cases second
- Estimated time: 2-3 days
