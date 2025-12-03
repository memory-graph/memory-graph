# Documentation Update Checklist - v0.9.0

This checklist breaks down the documentation updates needed across 5 workplans of completed implementation.

---

## Quick Reference: What to Document

| Feature | Status | Where | Effort | Priority |
|---------|--------|-------|--------|----------|
| **Pagination** | Implemented | TOOL_SELECTION_GUIDE.md, CONFIGURATION.md, README.md | 2-3h | P1 |
| **Cycle Detection** | Implemented | CONFIGURATION.md, TROUBLESHOOTING.md, README.md | 2-3h | P1 |
| **Health Check** | Implemented | TROUBLESHOOTING.md, CONFIGURATION.md | 2-3h | P1 |
| **Exception Hierarchy** | Implemented | EXCEPTION_REFERENCE.md (new file) | 2h | P4 |
| **Server Refactoring** | Implemented | ADR 010 (already exists) | — | ✅ Done |
| **Datetime Migration** | Implemented | No user docs needed | — | ✅ Done |
| **Structured Context** | Implemented | TOOL_SELECTION_GUIDE.md | 1h | P3 |

---

## Priority 1: CRITICAL - User-Facing Feature Documentation

### Task 1.1: Add Pagination to TOOL_SELECTION_GUIDE.md

**Location**: `/docs/TOOL_SELECTION_GUIDE.md`

**What to Add** (insert in "Tool Profiles and Availability" section):
```markdown
## Pagination Support

All search tools support result pagination to handle large result sets efficiently.

### Pagination Parameters

Available in: `search_memories`, `recall_memories`, `get_recent_activity`

- **limit**: Maximum results per page (1-1000, default: 50)
- **offset**: Number of results to skip before returning (default: 0)

### PaginatedResult Response

When pagination is used, results include:
- **results**: Array of matching items (limited by `limit` parameter)
- **total_count**: Total number of items matching the query
- **limit**: The limit used in this query
- **offset**: The offset used in this query
- **has_more**: Boolean indicating whether more results are available
- **next_offset**: Offset value for the next page (null if no more pages)

### Example Usage

```
User: "Find all authentication-related solutions, showing 25 per page"

Step 1: recall_memories(query="authentication", memory_types=["solution"], limit=25, offset=0)
→ Returns: {results: [...25 items...], total_count: 87, has_more: true, next_offset: 25}

Step 2: recall_memories(query="authentication", memory_types=["solution"], limit=25, offset=25)
→ Returns: {results: [...25 items...], total_count: 87, has_more: true, next_offset: 50}
```

### When to Use Pagination

- Large result sets (100+ items)
- UI with page-based navigation
- Reducing memory consumption in client applications
- Batch processing (process results in chunks)
```

**Checklist**:
- [ ] Add pagination section to TOOL_SELECTION_GUIDE.md
- [ ] Include parameter descriptions
- [ ] Add example showing pagination flow
- [ ] Document response format
- [ ] Note which tools support pagination

---

### Task 1.2: Add Cycle Detection to CONFIGURATION.md

**Location**: `/docs/CONFIGURATION.md` (add to "Environment Variables" section)

**What to Add**:
```markdown
# Cycle Detection

## MEMORY_ALLOW_CYCLES

Controls whether the system allows circular relationship chains.

```bash
export MEMORY_ALLOW_CYCLES=false    # Default: prevent cycles (recommended)
export MEMORY_ALLOW_CYCLES=true     # Allow circular relationships
```

### What are Relationship Cycles?

A cycle occurs when a chain of relationships forms a loop:
```
Memory A --RELATES_TO--> Memory B --RELATES_TO--> Memory C --RELATES_TO--> Memory A
```

### Default Behavior (MEMORY_ALLOW_CYCLES=false)

By default, MemoryGraph prevents cycles to:
- Prevent infinite traversal during graph queries
- Maintain relationship integrity
- Ensure predictable query results
- Avoid recursive loops in relationship analysis

When a cycle would be created, you'll receive an error:
```
Error: Would create a cycle in the RELATES_TO relationship graph
Suggestion: Check your relationship chain before creating, or enable cycles with MEMORY_ALLOW_CYCLES=true
```

### Allowing Cycles (MEMORY_ALLOW_CYCLES=true)

Set this if you need circular relationships for your specific use case.

**When you might need cycles**:
- Bidirectional causal relationships (A causes B, B causes A)
- Mutual dependencies between components
- Circular knowledge domains (philosophy, linguistics, etc.)

**Warning**: Enabling cycles requires careful query design to avoid infinite loops.

### Example Usage

```bash
# Prevent cycles (default - recommended)
claude mcp add --scope user memorygraph memorygraph

# Allow cycles (if needed)
claude mcp add --scope user memorygraph memorygraph \
  --env MEMORY_ALLOW_CYCLES=true
```

### Configuration Example

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "env": {
        "MEMORY_ALLOW_CYCLES": "false"  // Default
      }
    }
  }
}
```
```

**Checklist**:
- [ ] Add MEMORY_ALLOW_CYCLES to environment variables section
- [ ] Explain what cycles are
- [ ] Document default behavior
- [ ] Provide use cases for enabling cycles
- [ ] Include error message example
- [ ] Show CLI configuration example

---

### Task 1.3: Document Health Check in TROUBLESHOOTING.md

**Location**: `/docs/TROUBLESHOOTING.md` (update "Quick Diagnostics" section)

**What to Expand**:
```markdown
## Health Check Command

The health check command verifies that MemoryGraph is properly configured and connected to its backend.

### Running Health Check

```bash
memorygraph --health
```

### Health Check Output

Returns JSON with the following fields:

```json
{
  "status": "healthy",                    // "healthy" or "unhealthy"
  "backend": "sqlite",                    // Backend type
  "backend_version": "3.x",               // Backend version (if available)
  "connected": true,                      // Database connectivity
  "response_time_ms": 45,                 // Query execution time
  "memory_path": "/Users/you/.memorygraph/memory.db",  // Storage location
  "tool_profile": "extended",             // Configured tool profile
  "version": "0.9.0"                      // MemoryGraph version
}
```

### Interpreting Results

**Healthy (status: "healthy")**
- All checks passed
- Backend is connected and responding
- MemoryGraph is ready to use

**Unhealthy (status: "unhealthy")**
- Check the `error` field for specific problem
- See "Common Health Check Failures" below

### Common Health Check Failures

#### SQLite database locked
```
"status": "unhealthy",
"error": "database is locked"
```

**Solutions**:
```bash
# Check for running processes
ps aux | grep memorygraph

# Kill stale processes
pkill -f memorygraph

# Remove lock file if safe
rm ~/.memorygraph/memory.db-lock
```

#### Neo4j connection refused
```
"status": "unhealthy",
"error": "Connection refused"
```

**Solutions**:
```bash
# Verify Neo4j is running
docker ps | grep neo4j

# Check credentials in configuration
memorygraph --show-config | grep NEO4J

# Restart Neo4j
docker restart neo4j
```

#### Backend not initialized
```
"status": "unhealthy",
"error": "Backend initialization failed"
```

**Solutions**:
- Check environment variables: `memorygraph --show-config`
- Verify database path has write permissions: `ls -la ~/.memorygraph/`
- Check logs: `MEMORY_LOG_LEVEL=DEBUG memorygraph --health`

### When to Run Health Check

- After installing or upgrading MemoryGraph
- When experiencing connection issues
- Before deploying to production
- After changing backend configuration
- When Claude Code reports MCP server issues

### Health Check with JSON Output

The output is already JSON formatted, suitable for:
- Monitoring systems
- CI/CD pipelines
- Status dashboards

Example using jq to check status:
```bash
memorygraph --health | jq '.status'
# Output: "healthy"
```
```

**Checklist**:
- [ ] Expand health check section in TROUBLESHOOTING.md
- [ ] Add JSON output format documentation
- [ ] Include specific error messages and solutions
- [ ] Document when to use health check
- [ ] Add examples for different backends

---

### Task 1.4: Update README.md with New Features

**Location**: `/docs/README.md` (add to "Why MemoryGraph?" section or Features)

**What to Add**:
```markdown
## Key Features

### Graph-Based Memory with Relationships
[existing content...]

### Pagination for Large Result Sets
Handle unlimited scale with efficient pagination:
- Offset-based pagination with configurable page size (1-1000 results)
- Metadata includes total count and has_more flag
- Perfect for UI pagination, batch processing, and memory-efficient queries

### Cycle Detection for Relationship Integrity
Prevents circular relationship chains by default:
- Configurable to allow cycles when needed
- Maintains predictable graph queries
- Optional configuration: `MEMORY_ALLOW_CYCLES`

### Health Checks and Diagnostics
Built-in health monitoring:
- `memorygraph --health` command verifies backend connectivity
- JSON output suitable for monitoring systems
- Useful for troubleshooting configuration issues

### Comprehensive Error Handling
Structured exception hierarchy for reliable error handling:
- ValidationError, NotFoundError, BackendError, ConfigurationError
- Clear error messages with recovery suggestions
- Consistent error response format

### Zero-Config SQLite by Default
Get started immediately without infrastructure:
- Automatic database creation
- No service setup required
- Upgradeable to Neo4j, Memgraph, or FalkorDB when needed
```

**Checklist**:
- [ ] Add features subsection to README.md
- [ ] Include pagination benefits
- [ ] Document cycle detection
- [ ] Mention health check availability
- [ ] Highlight zero-config default

---

## Priority 2: HIGH - Architecture Decision Records

### Task 2.1: Create ADR 011 - Pagination Design

**File**: Create `/docs/adr/011-pagination-design.md`

**Template Content**:
```markdown
# ADR 011: Result Pagination Design

## Status
Accepted and Implemented

## Context
Large memory databases can return hundreds or thousands of matching items in a single query.
Returning all results at once creates problems:
- Memory overhead on client and server
- Network bandwidth consumption
- UI responsiveness issues
- Processing latency for batch operations

## Decision
Implement offset-based pagination for search and recall operations.

### Design Choices
- **Strategy**: Offset-based (not cursor-based) for simplicity
- **Default limit**: 50 results per page
- **Maximum limit**: 1,000 results per page
- **Metadata included**: total_count, has_more, next_offset

### Why Offset-Based?
- Simpler implementation and understanding
- Works well for typical use cases (up to 10k items)
- Sufficient for MemoryGraph use cases
- Future: Can add cursor-based pagination if needed for massive datasets

## Alternatives Considered
1. **Cursor-based pagination** - More complex, better for very large datasets
   - Rejected: Overkill for current use cases, adds complexity
2. **No pagination** - Return all results
   - Rejected: Poor performance and memory usage
3. **Streaming results** - Progressive result delivery
   - Rejected: Requires different client handling, can add later

## Consequences
### Positive
- Clients can handle large result sets efficiently
- Batch processing becomes feasible
- UI pagination easily implemented
- Predictable memory usage

### Negative
- Adds parameters to search tools
- Requires client pagination logic
- Offset becomes invalid if underlying data changes between requests

### Implementation Notes
- All search methods return PaginatedResult
- Limit defaults to 50, maximum 1,000
- has_more flag indicates more results available
- next_offset field provides suggested next page offset

## Examples

```python
# First page
recall_memories(query="auth", limit=25, offset=0)
→ {
    results: [...25 items...],
    total_count: 87,
    has_more: true,
    next_offset: 25
  }

# Next page
recall_memories(query="auth", limit=25, offset=25)
→ {
    results: [...25 items...],
    total_count: 87,
    has_more: true,
    next_offset: 50
  }
```

## References
- 5-WORKPLAN: Pagination implementation plan
- PaginatedResult: src/memorygraph/models.py
- Implementation: All backends support pagination
- Issue: None (feature request from users)

## Date
2025-12-02
```

**Checklist**:
- [ ] Create `/docs/adr/011-pagination-design.md`
- [ ] Include rationale for offset vs cursor
- [ ] Document design choices
- [ ] Add implementation examples
- [ ] Reference implementation details

---

### Task 2.2: Create ADR 012 - Cycle Detection Strategy

**File**: Create `/docs/adr/012-cycle-detection-strategy.md`

**Template Content**:
```markdown
# ADR 012: Relationship Cycle Detection

## Status
Accepted and Implemented

## Context
Circular relationship chains can cause issues in graph traversal:
- Infinite loops in relationship queries
- Unpredictable query results
- Complex reasoning when cycles exist
- Graph analysis becomes more difficult

## Decision
Prevent relationship cycles by default with optional configuration to allow them.

### Design
- **Default**: Cycles prevented (MEMORY_ALLOW_CYCLES=false)
- **Configuration**: MEMORY_ALLOW_CYCLES environment variable
- **Algorithm**: DFS-based cycle detection before relationship creation
- **Error handling**: Clear error message when cycle would be created

## Why Prevent Cycles by Default?
1. **Simplicity**: Easier to reason about relationship graphs
2. **Performance**: Prevents infinite traversal in queries
3. **Integrity**: Maintains acyclic property of causal chains
4. **Safety**: Most use cases don't need cycles

## Alternatives Considered
1. **Always allow cycles** - No restrictions
   - Rejected: Unsafe defaults, requires careful query design
2. **Always prevent cycles** - No configuration option
   - Rejected: Some use cases need cycles
3. **Detect but don't prevent** - Log warning instead of error
   - Rejected: Silent failures are dangerous

## Consequences
### Positive
- Relationship graphs remain acyclic by default (DAG)
- Graph queries are simpler and faster
- Prevents accidental infinite loops
- Configurable for advanced use cases

### Negative
- Prevents some valid circular relationships
- Requires configuration change for edge cases
- Adds validation overhead to relationship creation

## Use Cases for Allowing Cycles
- Bidirectional causality (A causes B, B causes A)
- Mutual dependencies between components
- Circular knowledge domains
- Feedback loops in processes

## Implementation
- Location: `sqlite_database.py` create_relationship method
- Algorithm: `graph_algorithms.has_cycle()` function
- Error message includes suggestion to enable cycles
- Configuration checked before validation

## Examples

### Default Behavior (Cycles Prevented)
```
Attempt: Create auth_service RELATES_TO api_service, api_service RELATES_TO auth_service
Error: Would create a cycle in the RELATES_TO relationship graph
```

### With Cycles Allowed
```
MEMORY_ALLOW_CYCLES=true
Same attempt succeeds, cycle is created
```

## Future Enhancements
- Cycle detection logging/analytics
- Cycle depth reporting
- Configurable maximum cycle depth
- Performance optimization for large graphs

## References
- 5-WORKPLAN: Cycle detection implementation
- Implementation: src/memorygraph/utils/graph_algorithms.py
- Configuration: MEMORY_ALLOW_CYCLES environment variable
- Tests: tests/test_cycle_detection.py

## Date
2025-12-02
```

**Checklist**:
- [ ] Create `/docs/adr/012-cycle-detection-strategy.md`
- [ ] Include algorithm and implementation details
- [ ] Document configuration option
- [ ] Provide use cases for allowing cycles
- [ ] Include error handling examples

---

## Priority 3: MEDIUM - Feature Integration

### Task 3.1: Update TOOL_SELECTION_GUIDE.md - Remove Future References

**Location**: `/docs/TOOL_SELECTION_GUIDE.md`

**Changes**:
- [ ] Find "Phase 2.D" reference and update status (already complete)
- [ ] Find "Phase 2.E" reference and update status (already complete)
- [ ] Add section: "Pagination in Tool Selection"
- [ ] Add section: "Cycle Detection Considerations"
- [ ] Update "Future Enhancements" section to remove pagination/cycles

**Current References to Update**:
```
Line 51: "Need multi-term queries → use search_memories with different parameters"
→ Change to: "Need multi-term queries → use search_memories with terms parameter"

Lines 233-235: Mentions Phase 2.E as planned
→ Change to: Document get_recent_activity as implemented feature

Lines 299-320: Discusses Phase 2.D implementation timeline
→ Remove timeline references, document as current feature
```

**Checklist**:
- [ ] Search for "Phase 2.D" and "Phase 2.E" references
- [ ] Update status to "implemented"
- [ ] Remove timeline language
- [ ] Add pagination to tool selection decision trees

---

## Priority 4: LOW - Polish and Reference

### Task 4.1: Create EXCEPTION_REFERENCE.md (Optional)

**File**: Create `/docs/EXCEPTION_REFERENCE.md`

**Content Structure**:
```markdown
# Exception Reference Guide

## Exception Hierarchy

```
MemoryGraphError (base)
├── ValidationError
├── NotFoundError
├── BackendError
├── ConfigurationError
└── DatabaseConnectionError
```

## Exception Classes

### MemoryGraphError
Base exception for all MemoryGraph errors.

**When raised**: Any MemoryGraph-related error

**Example**:
```python
try:
    memory = await memory_db.get_memory("invalid-id")
except MemoryGraphError as e:
    print(f"MemoryGraph error: {e}")
```

### ValidationError
Raised when input validation fails.

**When raised**:
- Memory title is empty
- Tags are invalid
- Limit parameter exceeds maximum
- Relationship type is invalid

**Example**:
```python
try:
    await memory_db.store_memory(
        type="invalid_type",  # Invalid memory type
        title="...",
        content="..."
    )
except ValidationError as e:
    print(f"Validation failed: {e}")
```

**Recovery**: Check input parameters and validate before retrying

### NotFoundError
Raised when requested resource doesn't exist.

**When raised**:
- Memory ID not found
- Relationship doesn't exist
- Memory type doesn't exist

**Example**:
```python
try:
    memory = await memory_db.get_memory("nonexistent-id")
except NotFoundError as e:
    print(f"Memory not found: {e}")
```

**Recovery**: Verify the ID exists before requesting

### BackendError
Raised when backend operation fails.

**When raised**:
- Database connection error
- Query execution error
- Transaction failure
- Cypher syntax error (Neo4j/Memgraph)

**Example**:
```python
try:
    await memory_db.search_memories(query)
except BackendError as e:
    print(f"Backend error: {e}")
```

**Recovery**: Check backend connectivity, retry with exponential backoff

### ConfigurationError
Raised when configuration is invalid.

**When raised**:
- Invalid environment variables
- Missing required configuration
- Conflicting configuration settings
- Invalid backend specified

**Example**:
```python
try:
    database = create_database(backend="invalid")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

**Recovery**: Check environment variables and configuration

## Error Response Format

All errors include:
- `type`: Exception class name
- `message`: Human-readable error message
- `context`: Additional context (when available)
- `suggestion`: Recovery suggestion (when available)

## Error Handling Best Practices

1. Catch specific exceptions when possible
2. Use the suggestion field for user guidance
3. Log errors with full context
4. Implement exponential backoff for transient errors
5. Distinguish between user errors and system errors
```

**Checklist**:
- [ ] Create EXCEPTION_REFERENCE.md (optional)
- [ ] Document all exception classes
- [ ] Include recovery strategies
- [ ] Add usage examples

---

### Task 4.2: Minor Updates to CLAUDE_CODE_SETUP.md

**Location**: `/docs/CLAUDE_CODE_SETUP.md`

**Changes**:
- [ ] Add Python version requirement note to Prerequisites section
- [ ] Add: "Python 3.10+ required (3.12+ recommended)"
- [ ] Mention datetime compatibility (Python 3.12+ no longer uses utcnow)

**Checklist**:
- [ ] Update Prerequisites section
- [ ] Add Python version requirement
- [ ] Note about datetime changes in Python 3.12+

---

## Execution Order

### Session 1 (Priority 1 - Most Critical)
1. Task 1.1: Add Pagination to TOOL_SELECTION_GUIDE.md
2. Task 1.2: Add Cycle Detection to CONFIGURATION.md
3. Task 1.3: Expand Health Check in TROUBLESHOOTING.md
4. Task 1.4: Update README.md Features

**Time**: 6-9 hours
**Outcome**: Users can discover and use all new v0.9.0 features

### Session 2 (Priority 2 - Architecture)
5. Task 2.1: Create ADR 011 (Pagination Design)
6. Task 2.2: Create ADR 012 (Cycle Detection)

**Time**: 2-4 hours
**Outcome**: Architecture decisions formally documented

### Session 3 (Priority 3-4 - Polish)
7. Task 3.1: Update TOOL_SELECTION_GUIDE.md (remove future refs)
8. Task 4.1: Create EXCEPTION_REFERENCE.md (optional)
9. Task 4.2: Minor CLAUDE_CODE_SETUP.md updates

**Time**: 2-4 hours (1-2 if skipping EXCEPTION_REFERENCE)
**Outcome**: Consistent documentation, no forward references

---

## Verification Checklist

After completing updates:

- [ ] All new features mentioned in README.md
- [ ] CONFIGURATION.md has MEMORY_ALLOW_CYCLES documented
- [ ] TROUBLESHOOTING.md explains health check command
- [ ] TOOL_SELECTION_GUIDE.md shows pagination usage
- [ ] ADR 011 and 012 created and well-formatted
- [ ] No references to "Phase 2.D" or "Phase 2.E" as future work
- [ ] All example code is correct and tested
- [ ] Links between documents are consistent
- [ ] Spelling and grammar checked

---

## Files Summary

**To Create**:
- [ ] `/docs/adr/011-pagination-design.md`
- [ ] `/docs/adr/012-cycle-detection-strategy.md`
- [ ] `/docs/EXCEPTION_REFERENCE.md` (optional)

**To Update**:
- [ ] `/docs/TOOL_SELECTION_GUIDE.md` (add pagination, remove future refs)
- [ ] `/docs/CONFIGURATION.md` (add cycle detection, health check)
- [ ] `/docs/TROUBLESHOOTING.md` (expand health check section)
- [ ] `/docs/README.md` (add features section)
- [ ] `/docs/CLAUDE_CODE_SETUP.md` (minor: Python version note)

---

**Total Estimated Time**: 11-19 hours (excluding optional)
**Priority Focus**: Complete Priority 1 tasks first for immediate user benefit

---

**Created**: December 2, 2025
**For**: v0.9.0 Release Documentation
**Status**: Ready for execution
