# ADR 004: Module Organization Strategy

## Status
Accepted

## Date
2025-06-28

## Context
We needed to organize the codebase for:

1. **Clear Responsibilities**: Separation of concerns
2. **Maintainability**: Easy to find and modify code
3. **Testability**: Each module can be tested independently
4. **Extensibility**: Easy to add new features
5. **Import Clarity**: Minimal circular dependencies

## Decision Drivers
- **Single Responsibility**: Each module has one clear purpose
- **Layer Separation**: Models, database, server layers
- **Test Organization**: Tests mirror source structure
- **MCP Convention**: Follow MCP server patterns
- **Python Best Practices**: Standard project layout

## Considered Options

### Option 1: Monolithic Module
**Pros:**
- Simple file structure
- No import complexity

**Cons:**
- Large files (1000+ lines)
- Hard to navigate
- Difficult to test in isolation
- Poor separation of concerns

### Option 2: Feature-Based Organization
**Pros:**
- All memory code in one place
- Clear feature boundaries

**Cons:**
- Relationship code scattered
- Hard to reuse components
- Doesn't match architectural layers

### Option 3: Layer-Based Organization
**Pros:**
- Clear architectural layers
- Easy to test layers independently
- Reusable components
- Standard pattern

**Cons:**
- More files to navigate
- Need clear module boundaries

## Decision
We chose **Layer-Based Organization** with the following structure:

```
src/claude_memory/
├── __init__.py        # Package exports
├── __main__.py        # Entry point
├── models.py          # Data models and validation
├── database.py        # Database operations
└── server.py          # MCP server implementation

tests/
├── test_models.py     # Model tests
├── test_database.py   # Database tests
├── test_server.py     # Server tests
└── test_exceptions.py # Exception tests
```

## Module Responsibilities

### models.py (197 statements, 97% coverage)
**Purpose**: Data models and validation

**Contains:**
- `Memory` - Core memory model with Pydantic validation
- `MemoryContext` - Context metadata (project, files, languages)
- `Relationship` - Relationship model with properties
- `RelationshipProperties` - Relationship metadata
- `MemoryType` - Enum of memory types
- `RelationshipType` - Enum of 35 relationship types
- `SearchQuery` - Search query model
- Custom exceptions (7 types)

**Dependencies:**
- pydantic (for validation)
- enum (for types)
- datetime (for timestamps)

**Why Separate:**
- Models are reused across database and server
- Validation logic is independent
- Easy to test without database
- Can be imported by other modules

### database.py (286 statements, 71% coverage)
**Purpose**: Neo4j database operations

**Contains:**
- `Neo4jConnection` - Async database connection management
- `MemoryDatabase` - Memory CRUD operations
- Schema initialization
- Query execution
- Transaction management
- Relationship creation and traversal

**Dependencies:**
- neo4j (async driver)
- models (for data types)
- logging

**Why Separate:**
- Database logic is independent of server
- Can be tested with mocked Neo4j
- Reusable in other contexts
- Clear boundary for database operations

### server.py (206 statements, 63% coverage)
**Purpose**: MCP server implementation

**Contains:**
- `ClaudeMemoryServer` - Main MCP server class
- 8 MCP tool handlers:
  - `_handle_store_memory`
  - `_handle_get_memory`
  - `_handle_search_memories`
  - `_handle_update_memory`
  - `_handle_delete_memory`
  - `_handle_create_relationship`
  - `_handle_get_related_memories`
  - `_handle_get_memory_statistics`
- MCP protocol compliance
- Error response formatting

**Dependencies:**
- mcp (SDK)
- models (for types)
- database (for operations)

**Why Separate:**
- MCP server logic is independent
- Handlers are testable with mocked database
- Clear API boundary
- Follows MCP conventions

## Import Strategy

### Hierarchical Imports
```python
# models.py - No internal imports
from pydantic import BaseModel
from enum import Enum

# database.py - Imports models only
from claude_memory.models import Memory, Relationship

# server.py - Imports models and database
from claude_memory.models import Memory, ValidationError
from claude_memory.database import MemoryDatabase
```

### Avoiding Circular Dependencies
- Models never import database or server
- Database only imports models
- Server imports models and database
- Clear unidirectional dependency flow: server → database → models

### Public API (__init__.py)
```python
from claude_memory.models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
)
from claude_memory.database import MemoryDatabase, Neo4jConnection
from claude_memory.server import ClaudeMemoryServer
```

## Test Organization

### Mirroring Source Structure
```
tests/
├── test_models.py      → src/claude_memory/models.py
├── test_database.py    → src/claude_memory/database.py
├── test_server.py      → src/claude_memory/server.py
└── test_exceptions.py  → src/claude_memory/models.py (exceptions)
```

### Test Independence
- Each test module can run independently
- Fixtures defined per test file
- Mocks isolate layers (e.g., mock database in server tests)

## Consequences

### Positive
- **Clear Boundaries**: Each module has a clear purpose
- **Testable**: Can test each layer independently
- **Maintainable**: Easy to find relevant code
- **Extensible**: Easy to add new features to appropriate module
- **No Cycles**: Unidirectional dependency flow
- **Standard Pattern**: Familiar to Python developers

### Negative
- **Multiple Files**: More files to navigate
- **Import Management**: Need to manage imports carefully
- **Cross-Module Changes**: Changes may touch multiple files

### Mitigations
- **Clear Documentation**: README explains module purposes
- **Type Hints**: Make dependencies explicit
- **Test Coverage**: Verify module boundaries
- **Import Validation**: Tests verify no circular imports

## Future Considerations

### When to Add New Modules
Consider splitting when:
- A module exceeds 500 lines
- Multiple unrelated responsibilities emerge
- Testing becomes difficult due to coupling
- Clear subdomain emerges (e.g., analytics, migrations)

### Potential Future Modules
- `analytics.py` - Memory analytics and insights
- `migrations.py` - Schema migration tools
- `cache.py` - Caching layer
- `workflow.py` - Workflow-specific operations

## Validation
All 62 tests pass with current structure:
- ✅ models.py: 7 tests, 97% coverage
- ✅ database.py: 28 tests, 71% coverage
- ✅ server.py: 19 tests, 63% coverage
- ✅ exceptions: 8 tests, 100% coverage

## References
- [Python Project Layout](https://docs.python-guide.org/writing/structure/)
- [Separation of Concerns](https://en.wikipedia.org/wiki/Separation_of_concerns)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
