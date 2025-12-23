# MemoryGraph v0.12.0 Release Notes

**Release Date:** December 23, 2025

This is a major release featuring significant architectural improvements, enhanced type safety, and comprehensive test coverage. It also includes the tool description optimizations from v0.11.13.

---

## Highlights

- **81% Test Coverage** - Up from 70%, with 1,578 tests passing
- **Type-Safe Backend Interface** - New `MemoryOperations` Protocol
- **Cleaner Tool Handlers** - 40% less boilerplate with `@handle_tool_errors` decorator
- **Optimized Tool Descriptions** - Better LLM guidance for `recall_memories` vs `search_memories`

---

## New Features

### MemoryOperations Protocol
A new type-safe interface (`src/memorygraph/protocols.py`) that defines the common operations all backends must support. This enables better IDE support, type checking, and clearer API contracts.

```python
from memorygraph.protocols import MemoryOperations

def process_memories(backend: MemoryOperations):
    # Type-safe operations across any backend
    await backend.store_memory(memory)
    await backend.search_memories(query)
```

### Tool Handler Registry
New centralized registry (`src/memorygraph/tools/registry.py`) that maps tool names to handlers, replacing the previous if/elif dispatch chain. This improves maintainability and makes adding new tools easier.

### Error Handling Decorator
The `@handle_tool_errors` decorator (`src/memorygraph/tools/error_handling.py`) provides consistent error handling across all tool handlers, reducing boilerplate by ~40%.

```python
@handle_tool_errors("store memory")
async def handle_store_memory(memory_db, arguments):
    # Just the happy path - errors handled by decorator
    ...
```

### Input Validation
New validation utilities (`src/memorygraph/utils/validation.py`) including:
- Content size limits (50KB max)
- Tag normalization with Pydantic field validators
- Consistent validation across all inputs

### Backend Capability Detection
All backends now implement `is_cypher_capable()` for runtime capability checking:
- Graph backends (Neo4j, Memgraph, FalkorDB): Returns `True`
- REST backends (Cloud): Returns `False`
- SQLite: Returns `False`

---

## Improvements

### Tool Descriptions Optimized for Retrieval (from v0.11.13)
Updated MCP tool descriptions to guide LLMs on when to use each search tool:

**`recall_memories`** - Best for:
- Conceptual queries ("how does authentication work")
- Fuzzy matching and natural language

**`search_memories`** - Best for:
- Acronyms (DCAD, JWT, API)
- Proper nouns and technical terms
- Known tags
- Exact matching

**`store_memory`** - New guidance:
- Tag acronyms explicitly for reliable retrieval
- Example: A memory about "DCAD - Dallas County Appraisal District" should have tags: `["dcad", "dallas-county", "property-lookup"]`

### CloudBackend Refactoring
- Renamed internally to `CloudRESTAdapter` to reflect its REST API nature
- Backwards-compatible `CloudBackend` alias maintained
- Documented in ADR-018

### Datetime Handling
All code now uses `datetime.now(timezone.utc)` instead of the deprecated `datetime.utcnow()`, ensuring timezone-aware datetime handling throughout.

---

## Bug Fixes

- **LSP Violation**: CloudBackend no longer violates Liskov Substitution Principle
- **Timezone Safety**: Fixed naive vs aware datetime comparison issues
- **SDK Model Sync**: SDK models now properly synchronized with server models
- **Neo4j Optional Dependency**: Tests properly skip when neo4j package not installed

---

## Testing

### Coverage Improved: 70% → 81%

| Module | Before | After |
|--------|--------|-------|
| `cli.py` | 6% | 92% |
| `backends/factory.py` | 20% | 99% |
| `tools/activity_tools.py` | 12% | 98% |
| `tools/error_handling.py` | - | 100% |
| `tools/registry.py` | - | 100% |
| `tools/validation.py` | - | 100% |
| `analytics/advanced_queries.py` | 29% | 96% |
| `cloud_database.py` | 44% | 100% |
| `sqlite_database.py` | 5% | 85% |

### New Test Files
- `tests/test_cli_coverage.py`
- `tests/backends/test_factory_coverage.py`
- `tests/tools/test_activity_tools_coverage.py`
- `tests/tools/test_temporal_tools_coverage.py`
- `tests/tools/test_error_handling.py`
- `tests/tools/test_registry.py`
- `tests/tools/test_validation.py`
- `tests/analytics/test_advanced_queries_coverage.py`
- `tests/test_cloud_database_coverage.py`
- `tests/test_sqlite_database_coverage.py`

### Test Results
- **1,578 tests passing**
- **139 skipped** (neo4j optional dependency)
- **3 warnings** (minor async mock warnings)

---

## Breaking Changes

None. All changes are backwards compatible.

---

## Migration Guide

No migration required. Existing code will continue to work without changes.

### Optional Improvements

1. **Use the new Protocol for type hints:**
   ```python
   from memorygraph.protocols import MemoryOperations
   ```

2. **Check backend capabilities at runtime:**
   ```python
   if backend.is_cypher_capable():
       # Use Cypher-specific features
   ```

3. **Update tag strategy for acronyms:**
   - Add acronyms as explicit tags when storing memories
   - Use `search_memories` with tag filters for acronym lookups

---

## Documentation

- **ADR-018**: Architecture Decision Record for CloudBackend type hierarchy
- **WORKPLAN-24**: Detailed implementation plan for architectural fixes

---

## Contributors

- Gregory Dickson
- Claude Opus 4.5 (AI pair programmer)

---

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for the complete list of changes.
