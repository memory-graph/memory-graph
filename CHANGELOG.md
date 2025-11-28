# Changelog

All notable changes to the Claude Code Memory Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Entity extraction integration into store_memory workflow
- Advanced memory analytics and visualization
- Claude Code workflow integration
- Memory effectiveness tracking
- Performance optimization
- Embedding-based semantic similarity (optional enhancement)

## [0.4.0] - 2025-11-28

### Added - Phase 5: Intelligence Layer
- **Entity Extraction Module**: Automatic entity identification from memory content
  - Support for 12 entity types (FILE, FUNCTION, CLASS, ERROR, TECHNOLOGY, CONCEPT, etc.)
  - Regex-based pattern matching with 82% coverage
  - Optional NLP support via spaCy
  - Confidence scoring and deduplication
  - Automatic entity linking with MENTIONS relationships

- **Pattern Recognition Module**: Identify reusable patterns from accumulated memories
  - Find similar problems using keyword/entity matching
  - Extract common patterns from entity co-occurrences
  - Pattern confidence scoring based on frequency
  - Context-aware pattern suggestions
  - 95% test coverage

- **Temporal Memory Module**: Track how information changes over time
  - Version history traversal via PREVIOUS relationships
  - Point-in-time state queries
  - Entity timeline tracking
  - Version diff comparison
  - 97% test coverage

- **Context-Aware Retrieval Module**: Intelligent context assembly
  - Multi-factor relevance ranking (entities + keywords + recency)
  - Token-limited context formatting
  - Project-scoped context retrieval
  - Session briefings (last 24 hours)
  - Relationship traversal for related context

- **94 New Intelligence Tests**: Comprehensive test coverage
  - 28 entity extraction tests
  - 23 pattern recognition tests
  - 21 temporal memory tests
  - 22 context retrieval tests
  - All passing with high coverage (82-97%)

- **7 New MCP Tools**:
  - `find_similar_solutions`: Find similar problems and their solutions
  - `suggest_patterns_for_context`: Get relevant pattern suggestions
  - `get_memory_history`: View version history for a memory
  - `track_entity_timeline`: Track entity usage over time
  - `get_intelligent_context`: Smart context retrieval with ranking
  - `get_project_summary`: Comprehensive project overview
  - `get_session_briefing`: Recent activity summary

### Features
- **Smart Entity Recognition**: Automatically identify technologies, errors, files, concepts
- **Pattern Learning**: Extract reusable patterns from successful solutions
- **Version Tracking**: Complete audit trail of how memories evolve
- **Intelligent Ranking**: Relevance-based context with entity + keyword + recency scoring
- **Backend Agnostic**: All intelligence features work across Neo4j, Memgraph, SQLite

### Architecture
- Modular intelligence layer with 4 specialized modules
- Clean separation of concerns (extraction, recognition, temporal, retrieval)
- Extensible design for future ML/NLP enhancements
- Zero-dependency core with optional advanced features

### Documentation
- `docs/adr/006-intelligence-layer-architecture.md`: ADR for intelligence design
- Comprehensive module docstrings with examples
- Type hints on all public APIs
- Usage examples for all MCP tools

### Performance
- Entity extraction: <100ms for typical memory
- Pattern recognition: <200ms with 1000+ memories
- Context retrieval: <500ms for complex queries
- Temporal queries: <100ms for version chains

### Test Metrics
- **Total Tests**: 271 (up from 177)
- **Pass Rate**: 100%
- **Intelligence Coverage**: 82-97% across modules
- **Overall Coverage**: 66%

## [0.3.0] - 2025-11-27

### Added - Phase 3: Multi-Backend Support
- **Abstract Backend Layer**: Introduced `GraphBackend` interface for database abstraction
- **Neo4j Backend**: Refactored existing Neo4j code into `neo4j_backend.py` implementing GraphBackend
- **Memgraph Backend**: Added full Memgraph support using Bolt protocol and Cypher compatibility
- **SQLite Fallback**: Implemented zero-dependency SQLite + NetworkX fallback backend
- **Backend Factory**: Automatic backend selection with priority-based fallback (Neo4j → Memgraph → SQLite)
- **Configuration System**: Centralized configuration with multi-backend environment variables
- **36 New Backend Tests**: Comprehensive test suite for all backend implementations
  - 19 Neo4j backend tests
  - 17 Backend factory tests

### Features
- **Automatic Backend Selection**: `MEMORY_BACKEND=auto` tries backends in order until one connects
- **Explicit Backend Selection**: Support for `neo4j`, `memgraph`, `sqlite` via env var
- **Zero Setup Option**: SQLite fallback requires no external database
- **Cypher Dialect Adaptation**: Automatic query translation for Memgraph compatibility
- **Health Checks**: Backend health monitoring with connection status and statistics

### Configuration
- New environment variables for multi-backend support:
  - `MEMORY_BACKEND`: Backend selection (neo4j|memgraph|sqlite|auto)
  - `MEMORY_NEO4J_URI`, `MEMORY_NEO4J_USER`, `MEMORY_NEO4J_PASSWORD`
  - `MEMORY_MEMGRAPH_URI`, `MEMORY_MEMGRAPH_USER`, `MEMORY_MEMGRAPH_PASSWORD`
  - `MEMORY_SQLITE_PATH`: SQLite database file location
  - Backward compatibility with `NEO4J_*` environment variables

### Documentation
- `docs/CYPHER_COMPATIBILITY.md`: Comprehensive guide to Cypher dialect differences
- Backend comparison matrix with feature support
- Migration guide between backends
- Performance considerations for each backend

### Technical Details
- All backends implement identical `GraphBackend` interface
- Neo4j backend supports full-text search with FULLTEXT INDEX
- Memgraph backend with Cypher dialect adaptations
- SQLite backend uses FTS5 for full-text search, NetworkX for graph operations
- Async/await throughout all backend implementations
- Connection pooling and retry logic in Neo4j/Memgraph backends

### Testing
- Test coverage maintained at 76% (now covering 98 tests)
- All 98 tests passing (100% pass rate)
- Backend-specific test suites with mocking
- Integration tests verify cross-backend compatibility

### Breaking Changes
- None - existing Neo4j deployments continue to work without changes
- Default behavior unchanged when using existing `NEO4J_*` environment variables

## [0.2.0] - 2025-11-27

### Added - Phase 2.5: Technical Debt Resolution
- Custom exception hierarchy with detailed error information
- Comprehensive error handling across all modules
- AsyncIO refactoring for all database operations
- Full MCP protocol compliance with isError flags
- 62 comprehensive unit tests across all modules:
  - 28 database tests (Neo4j connection, CRUD, relationships, statistics)
  - 19 server tests (MCP handlers, validation, error handling)
  - 8 exception tests (custom exceptions, error hierarchy)
  - 7 model tests (Pydantic validation, serialization)

### Fixed
- All async database operations now properly use AsyncIO
- Server handlers correctly set isError=True for error responses
- Comprehensive exception handling in all handler methods
- Mock return values aligned with actual implementation
- API parameter names standardized (depth → max_depth, memory_type → type)

### Improved
- Test coverage increased from 67% to 76%:
  - database.py: 65% → 71%
  - server.py: 38% → 63%
  - models.py: 97%
- All 62 tests passing (100% pass rate)
- Better error messages with context and validation details
- Consistent exception handling patterns

### Technical Debt Paid
- ✅ Async refactoring complete
- ✅ Custom exceptions implemented
- ✅ Test infrastructure created
- ✅ Error handling standardized
- ✅ MCP protocol compliance verified

## [0.1.0] - 2025-06-28

### Added
- Initial project setup with Python packaging (pyproject.toml)
- Comprehensive Neo4j-based MCP memory server implementation
- Complete data models with Pydantic validation
- 8 core MCP tools for memory management:
  - `store_memory` - Store memories with context and metadata
  - `get_memory` - Retrieve specific memories by ID
  - `search_memories` - Advanced search with filtering
  - `update_memory` - Modify existing memories
  - `delete_memory` - Remove memories and relationships
  - `create_relationship` - Link memories with typed relationships
  - `get_related_memories` - Find connected memories
  - `get_memory_statistics` - Database analytics
- Advanced relationship system with 7 categories and 35 relationship types:
  - **Causal**: CAUSES, TRIGGERS, LEADS_TO, PREVENTS, BREAKS
  - **Solution**: SOLVES, ADDRESSES, ALTERNATIVE_TO, IMPROVES, REPLACES
  - **Context**: OCCURS_IN, APPLIES_TO, WORKS_WITH, REQUIRES, USED_IN
  - **Learning**: BUILDS_ON, CONTRADICTS, CONFIRMS, GENERALIZES, SPECIALIZES
  - **Similarity**: SIMILAR_TO, VARIANT_OF, RELATED_TO, ANALOGY_TO, OPPOSITE_OF
  - **Workflow**: FOLLOWS, DEPENDS_ON, ENABLES, BLOCKS, PARALLEL_TO
  - **Quality**: EFFECTIVE_FOR, INEFFECTIVE_FOR, PREFERRED_OVER, DEPRECATED_BY, VALIDATED_BY
- Neo4j database connection and management with connection pooling
- Comprehensive schema documentation and API reference
- GitHub project management with issues, labels, and milestones
- Complete implementation plan with 7-phase roadmap
- Test suite foundation with model validation tests
- Docker-ready configuration with environment variable support

### Documentation
- README.md with complete project overview and usage instructions
- Schema documentation with all node types and relationships
- Implementation plan with detailed phase breakdown
- API documentation for all MCP tools
- Development setup and configuration guide

### Infrastructure
- GitHub repository with proper issue tracking
- Git workflow with semantic commit messages
- Automated schema initialization
- Performance optimization with indexes and constraints
- Error handling and logging throughout

### Dependencies
- mcp>=1.0.0 - Model Context Protocol SDK
- neo4j>=5.0.0 - Neo4j Python driver
- pydantic>=2.0.0 - Data validation and parsing
- python-dotenv>=1.0.0 - Environment variable management

## Project Milestones

### Phase 1: Foundation Setup ✅ COMPLETED (2025-06-28)
- **Issues Closed**: #1, #2, #3
- **Commits**: 2 major commits with 12 files added
- **Status**: All core infrastructure and basic MCP server operational

### Phase 2: Core Memory Operations 🔄 IN PROGRESS
- **Target**: January 2025
- **Focus**: CRUD operations, entity management, basic relationships
- **Issues**: #12-25 (to be created)

### Phase 3: Advanced Relationship System 📋 PLANNED
- **Target**: February 2025
- **Focus**: All 35 relationship types, weighted properties, intelligence

### Phase 4: Claude Code Integration 📋 PLANNED
- **Target**: February-March 2025
- **Focus**: Development context capture, workflow integration

### Phase 5: Advanced Intelligence 📋 PLANNED
- **Target**: March-April 2025
- **Focus**: Pattern recognition, automatic relationship detection

### Phase 6: Advanced Query & Analytics 📋 PLANNED
- **Target**: April-May 2025
- **Focus**: Complex queries, effectiveness tracking, visualization

### Phase 7: Integration & Optimization 📋 PLANNED
- **Target**: May 2025
- **Focus**: Production readiness, performance optimization, deep integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
