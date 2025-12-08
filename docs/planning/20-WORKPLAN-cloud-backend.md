# Workplan 20: MCP Cloud Backend Adaptation

> **Phase**: Integration
> **Dependencies**: Graph Service (cloud infrastructure)
> **Estimated Effort**: Medium complexity, adapter implementation
> **Status**: ✅ COMPLETE (2025-12-08) - Ready for manual release steps

## Overview

Adapt the existing MemoryGraph MCP server to support cloud backend mode. This workplan adds a new backend adapter that communicates with the cloud Graph API (https://graph-api.memorygraph.dev) while maintaining backward compatibility with existing local backends (SQLite, Neo4j, FalkorDB).

The cloud backend enables:
- Multi-device synchronization
- Team collaboration
- Cloud-hosted memory graphs
- Managed infrastructure (no local database setup required)

---

## 1. Backend Architecture Analysis

### 1.1 Review existing backend interface
- [x] Read `src/memorygraph/backends/` directory
- [x] Identify common interface methods required:
  - `connect()`, `close()`
  - `store_memory()`, `get_memory()`, `update_memory()`, `delete_memory()`
  - `create_relationship()`, `get_related_memories()`
  - `search_memories()`, `get_statistics()`
- [x] Document the backend abstraction pattern
- [x] Identify modifications needed to support async HTTP operations

### 1.2 Design cloud backend adapter
- [x] Create design doc (documented in code)
- [x] Define interface between MCP server and Graph API
- [x] Plan error handling for network failures
- [ ] Plan offline fallback strategy (optional for MVP) → Deferred to v1.1
- [x] Document authentication flow (API key → Graph API)

---

## 2. Cloud Backend Implementation

### 2.1 Create cloud backend module
- [x] Create file: `src/memorygraph/backends/cloud_backend.py`
- [x] Implement `CloudBackend` class
- [x] Constructor accepts:
  - `api_key: str` (from environment variable)
  - `api_base_url: str` (default: `https://graph-api.memorygraph.dev`)
  - `timeout: int` (default: 30 seconds)
- [x] Initialize `httpx.AsyncClient` for HTTP requests
- [x] Add API key to all requests via header: `X-API-Key`

### 2.2 Implement connection management
- [x] Implement `async connect()`:
  - Test connection with health check: `GET /health`
  - Validate API key works
  - Log connection success
- [x] Implement `async close()`:
  - Close HTTP client
  - Clean up resources
- [x] Implement `async ping()` via `health_check()`:
  - Health check endpoint
  - Return True if successful
- [x] Add retry logic for transient failures (3 retries with exponential backoff)

### 2.3 Implement memory operations
- [x] Implement `async store_memory(memory: Memory) -> str`:
  - POST `/memories` with memory data
  - Return memory_id from response
  - Handle 403 errors (usage limit exceeded)
- [x] Implement `async get_memory(memory_id: str) -> Memory`:
  - GET `/memories/{memory_id}`
  - Return Memory object
  - Handle 404 errors
- [x] Implement `async update_memory(memory_id: str, updates: Dict) -> Memory`:
  - PUT `/memories/{memory_id}` with updates
  - Return updated Memory
- [x] Implement `async delete_memory(memory_id: str) -> None`:
  - DELETE `/memories/{memory_id}`
  - Handle 404 gracefully

### 2.4 Implement relationship operations
- [x] Implement `async create_relationship(from_id: str, to_id: str, rel_type: str, ...) -> str`:
  - POST `/relationships` with relationship data
  - Return relationship_id
- [x] Implement `async get_related_memories(memory_id: str, rel_types: List[str], max_depth: int) -> List[Memory]`:
  - GET `/memories/{memory_id}/related?relationship_types=X&max_depth=Y`
  - Parse and return list of related memories

### 2.5 Implement search operations
- [x] Implement `async search_memories(query: SearchQuery) -> List[Memory]`:
  - POST `/memories/search` with search params
  - Handle pagination (limit, offset)
  - Return list of memories
- [x] Implement `async recall_memories(query: str, limit: int) -> List[Memory]`:
  - POST `/memories/recall` with natural language query
  - Return fuzzy-matched results with context
- [x] Implement `async get_recent_activity(days: int, project: str) -> Dict`:
  - GET `/memories/recent?days=X&project=Y`
  - Return activity summary

### 2.6 Implement statistics
- [x] Implement `async get_statistics() -> Dict`:
  - GET `/graphs/statistics`
  - Return graph statistics (memory count, relationship count, etc.)

---

## 3. Configuration Integration

### 3.1 Add cloud backend config
- [x] Update `src/memorygraph/backends/factory.py`
- [x] Add new backend type: `cloud`
- [x] Add environment variables:
  - `MEMORY_BACKEND=cloud` (to enable cloud mode)
  - `MEMORYGRAPH_API_KEY=mg_xxxxx` (required for cloud)
  - `MEMORYGRAPH_API_URL=https://graph-api.memorygraph.dev` (optional, has default)
- [x] Add validation: Require API key if backend is cloud
- [x] Document configuration in docstrings

### 3.2 Update backend factory
- [x] Update `src/memorygraph/backends/factory.py` backend selection logic
- [x] Add cloud backend to factory with `_create_cloud()` method
- [x] Ensure backward compatibility with existing backends
- [x] Backend selection tests inherited from existing test suite

---

## 4. Error Handling and Resilience

### 4.1 Network error handling
- [x] Implement retry logic for transient errors (503, 502, timeout)
- [x] Implement exponential backoff (1s, 2s, 4s, 8s)
- [ ] Add circuit breaker pattern for repeated failures (optional for MVP)
- [x] Log all retry attempts

### 4.2 API error translation
- [x] Map HTTP status codes to MemoryGraph exceptions:
  - 401 → `AuthenticationError("Invalid API key")`
  - 403 → `UsageLimitExceeded("Upgrade to continue")`
  - 404 → Returns `None` (caller handles)
  - 429 → `RateLimitExceeded("Retry after X seconds")`
  - 500 → `DatabaseConnectionError("Graph service error")`
- [x] Include helpful error messages with upgrade links
- [x] Write unit tests for error mapping

### 4.3 Offline fallback (optional for v1.1)
- [ ] Design offline queue for operations
- [ ] Store operations locally when cloud unavailable
- [ ] Sync when connection restored
- [ ] Handle conflict resolution
- [ ] **Note**: This is a nice-to-have, not required for MVP

---

## 5. Testing

### 5.1 Unit tests
- [x] Mock `httpx.AsyncClient` for testing
- [x] Test all cloud backend methods
- [x] Test error handling (401, 404, 500, etc.)
- [x] Test retry logic
- [x] Test connection management
- [x] Achieve >80% code coverage for cloud backend (37 tests passing)

### 5.2 Integration tests
- [x] Set up test environment with Graph API (mocked HTTP client)
- [x] Create test fixtures for integration tests
- [x] Test full memory lifecycle via cloud backend
- [x] Test relationship operations
- [x] Test search and recall
- [x] Test concurrent operations
- [x] Test error handling during workflows
- **Note**: Created comprehensive integration tests with MockHTTPClient simulating the Graph API

### 5.3 End-to-end tests
- [x] Test MCP server with cloud backend
- [x] Simulate MCP client requests (store, recall, search)
- [x] Verify responses match expected format
- [x] Test error scenarios (invalid key, not found, etc.)
- [x] Test full workflows (problem → solution → link → search)
- **Note**: Created e2e tests simulating complete MCP workflows with cloud backend

---

## 6. Documentation

### 6.1 User documentation
- [x] Update `README.md`:
  - Add cloud backend section with features
  - Document setup: `export MEMORYGRAPH_API_KEY=mg_xxxxx`
  - Document backend selection: `memorygraph --backend cloud`
  - Add configuration example for Claude Code CLI
- [x] Create `docs/CLOUD_BACKEND.md`:
  - Getting API key (link to signup)
  - Configuration steps
  - Troubleshooting (connection errors, auth errors)
  - Migration from local to cloud
  - Benefits of cloud backend (sync, collaboration)

### 6.2 Developer documentation
- [x] Document cloud backend architecture (in code docstrings)
- [x] Document API client implementation (in code)
- [x] Document error handling strategy (in CLOUD_BACKEND.md)
- [x] Document testing procedures (integration and e2e tests added)
- **Note**: Comprehensive test suite serves as examples for developers

### 6.3 Quick start guide
- [x] Create `docs/CLOUD_BACKEND.md` (includes quick start):
  - Step 1: Sign up at memorygraph.dev
  - Step 2: Generate API key from dashboard
  - Step 3: Configure MCP server: `export MEMORYGRAPH_API_KEY=mg_xxxxx`
  - Step 4: Update Claude Code config: `memorygraph --backend cloud`
  - Step 5: Verify: Ask Claude to store and recall a memory
  - Troubleshooting section

---

## 7. Claude Code Configuration ✅ COMPLETE

### 7.1 Update setup instructions
- [x] Update `docs/CLAUDE_CODE_SETUP.md`:
  - Added cloud backend configuration section
  - Added comparison: Local vs Cloud backend table
  - Documented migration path (export → import)
- [x] Add comparison: Local vs Cloud backend
- [x] Document migration path (export → import)

### 7.2 Create cloud-specific examples
- [ ] Example: Team collaboration workflow (deferred)
- [ ] Example: Multi-device sync workflow (deferred)
- [ ] Example: Sharing memories with team members (deferred)
- [ ] Add to `docs/examples/cloud-workflows.md` (deferred)

---

## 8. Release and Packaging ✅ COMPLETE

### 8.1 Version bump
- [x] Bump version to `v0.10.0` (cloud backend support)
- [x] Update `CHANGELOG.md` with cloud backend feature
- [ ] Tag release: `git tag v0.10.0` (manual step)

### 8.2 PyPI release
- [x] Build package: `python -m build` (verified)
- [ ] Upload to PyPI: `twine upload dist/*` (manual step)
- [ ] Verify installation: `pipx install memorygraphMCP --force` (post-upload)
- [ ] Test cloud backend: `memorygraph --backend cloud --version` (post-upload)

### 8.3 Docker image update
- [x] Update Dockerfile with cloud backend support (profile: lite→core)
- [x] Update `docker-compose.yml` with correct profile (lite→core)
- [x] Update `docker-compose.full.yml` with correct profile (full→extended)
- [x] Update `docker-compose.neo4j.yml` with correct profile (full→extended)
- [ ] Build image: `docker build -t memorygraph:v0.10.0 .` (manual step)
- [ ] Push to Docker Hub: `docker push gregorydickson/memorygraph:v0.10.0` (manual step)

---

## 9. Optional Enhancements (Post-MVP)

### 9.1 Migration tool
- [ ] Create CLI command: `memorygraph migrate local-to-cloud`
- [ ] Export all memories from local backend
- [ ] Import to cloud backend via API
- [ ] Preserve relationships
- [ ] Show progress bar
- [ ] Verify migration completeness

### 9.2 Sync tool
- [ ] Create CLI command: `memorygraph sync`
- [ ] Compare local and cloud graphs
- [ ] Resolve conflicts (last-write-wins or manual)
- [ ] Sync bidirectionally
- [ ] Show sync status

### 9.3 Offline fallback
- [ ] Queue operations when offline
- [ ] Store in local SQLite as cache
- [ ] Sync when online
- [ ] Handle conflict resolution
- [ ] Notify user of sync status

---

## Verification Checklist

After completing this workplan, verify:

- [x] Cloud backend implemented and tested
- [x] MCP server works with `--backend cloud`
- [x] All memory operations work via API
- [x] Search and recall work via API
- [x] Error handling graceful (network errors, auth errors)
- [x] Tests passing with >80% coverage
- [x] Documentation updated (README, setup guides)
- [ ] PyPI package released with cloud support (deferred to release phase)
- [ ] Claude Code works with cloud backend (manual test - to be done by users)
- [x] Example workflows documented (in e2e tests)

---

## Implementation Status

**Core Implementation**: Complete (Sections 1-6)
- Cloud backend fully implemented with comprehensive test coverage
- All memory and relationship operations working
- Error handling and retry logic in place
- Documentation created

**Release Preparation**: Pending (Sections 7-8)
- Claude Code setup documentation needs updating
- PyPI package release pending
- Docker image update pending

**Future Enhancements**: Not Started (Section 9)
- Migration tools
- Sync tools
- Offline fallback

---

## Key Files

**Implementation**:
- `src/memorygraph/backends/cloud_backend.py` - Cloud backend implementation
- `src/memorygraph/backends/factory.py` - Backend factory with cloud support

**Tests**:
- `tests/unit/backends/test_cloud_backend.py` - Unit tests (37 tests)
- `tests/integration/test_cloud_backend_integration.py` - Integration tests
- `tests/e2e/test_cloud_backend_e2e.py` - End-to-end tests

**Documentation**:
- `docs/CLOUD_BACKEND.md` - Cloud backend user guide
- `docs/CLAUDE_CODE_SETUP.md` - Setup instructions (needs cloud backend section)
- `README.md` - Updated with cloud backend information

---

## Graph API

**Production Endpoint**: `https://graph-api.memorygraph.dev`

**Authentication**: API Key via `X-API-Key` header
- Get API key from: https://memorygraph.dev/dashboard
- Format: `mg_xxxxx...`

**Environment Variables**:
```bash
export MEMORYGRAPH_API_KEY=mg_your_key_here
export MEMORY_BACKEND=cloud
# Optional: Override default API URL
export MEMORYGRAPH_API_URL=https://graph-api.memorygraph.dev
```

---

## Next Steps

After completing release preparation (Sections 7-8):
1. Update Claude Code setup documentation with cloud backend examples
2. Release v0.10.0 to PyPI
3. Update Docker images
4. Announce cloud backend availability
5. Gather user feedback for future enhancements

---

## References

- **Graph API**: https://graph-api.memorygraph.dev
- **MCP Server Source**: `src/memorygraph/server.py`
- **Backend Implementations**: `src/memorygraph/backends/`
- **Cloud Backend Documentation**: `docs/CLOUD_BACKEND.md`
- **httpx Documentation**: https://www.python-httpx.org/
- **MCP Protocol Specification**: https://modelcontextprotocol.io/
