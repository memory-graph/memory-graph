# 1-WORKPLAN: Critical Fixes

**Goal**: Fix critical deprecation warnings and implement missing health check
**Priority**: CRITICAL - Must complete before other improvements
**Estimated Tasks**: 15 tasks
**Files Affected**: 50+ files across codebase

---

## Prerequisites

None - this is the starting point for code quality improvements.

---

## 1. Datetime Deprecation Fix (2,379 instances)

**Problem**: All `datetime.utcnow()` calls trigger deprecation warnings in Python 3.12+

**Solution**: Replace with `datetime.now(datetime.UTC)`

### 1.1 Identify All Instances

- [x] Run grep to find all files: `grep -r "datetime.utcnow()" src/ tests/`
- [x] Create comprehensive list of affected files
- [x] Document replacement pattern

**Files to search**:
- `/Users/gregorydickson/claude-code-memory/src/memorygraph/`
- `/Users/gregorydickson/claude-code-memory/tests/`

### 1.2 Update Core Models

- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/models/memory.py`
- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/models/relationship.py`
- [x] Run tests: `pytest tests/test_memory.py tests/test_relationships.py -v`

### 1.3 Update Backend Implementations

- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/sqlite_backend.py`
- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/sqlite_fallback.py`
- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/neo4j_backend.py`
- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/memgraph_backend.py`
- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/falkordb_backend.py`
- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/falkordblite_backend.py`
- [x] Run backend tests: `pytest tests/backends/ -v`

### 1.4 Update Server and Tools

- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
- [x] Replace in `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`
- [x] Run server tests

### 1.5 Update All Test Files

- [x] Replace in all files under `/Users/gregorydickson/claude-code-memory/tests/`
- [x] Update test fixtures
- [x] Run full test suite: `pytest -v`

### 1.6 Final Verification

- [x] Run full test suite with zero warnings: `pytest -v -W error::DeprecationWarning`
- [x] Verify all 910 tests still pass (899 passed, 20 skipped)
- [x] Run type checker: `mypy src/memorygraph`
- [x] Commit changes

---

## 2. Implement Health Check (TODO at cli.py:293)

**Problem**: Health check functionality marked as TODO

**Solution**: Implement complete health check with backend status reporting

### 2.1 Write Tests First (TDD)

Create `/Users/gregorydickson/claude-code-memory/tests/test_health_check.py`:

- [x] Test successful health check (all backends)
- [x] Test backend connection failure
- [x] Test database unavailable
- [x] Test health check timeout (5 seconds)
- [x] Test health check output format (JSON)

### 2.2 Implement Health Check Function

In `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`:

- [x] Remove TODO comment at line 293
- [x] Implement `perform_health_check()` function:
  - Check backend initialization
  - Check database connectivity
  - Check basic query execution (test query)
  - Report backend type and version
  - Return status code (0=healthy, 1=unhealthy)

### 2.3 Add CLI Command

- [x] Add `memorygraph --health` command
- [x] Add `--health-json` flag for JSON output
- [x] Add `--health-timeout` flag (default: 5 seconds)

### 2.4 Verify Implementation

- [x] Run health check tests: `pytest tests/test_health_check.py -v` (9 passed)
- [x] Test CLI command: `memorygraph --health` (works correctly)
- [x] Test with each backend type (SQLite tested, others via mocks)
- [x] Update documentation

---

## 3. Display Context in get_memory Output

**Problem**: The `get_memory` MCP tool stores structured context but doesn't display it in output

**Location**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py:949-957`

**Solution**: Add context fields to the formatted memory output

### 3.1 Update get_memory Output Format

- [x] Modify `_handle_get_memory()` in `server.py` to include context fields:
  - `project_path`
  - `files_involved`
  - `languages`
  - `frameworks`
  - `technologies`
  - `git_branch` (if present)
- [x] Only show non-empty context fields
- [x] Format context section clearly (e.g., "**Context:**" header)

### 3.2 Test the Change

- [x] Verify existing tests pass: `pytest tests/test_server.py -v` (all tests passed)
- [x] Manually test `get_memory` with a memory that has context
- [x] Verify backward compatibility (memories without context still display correctly)

---

## Acceptance Criteria

- [x] Zero `datetime.utcnow()` calls in codebase
- [x] Zero deprecation warnings when running tests
- [x] All 910 tests pass (899 passed, 20 skipped)
- [x] Health check implemented and tested
- [x] TODO removed from cli.py:293
- [x] Health check reports accurate backend status
- [x] `get_memory` displays structured context fields in output

---

## Notes

- This workplan MUST be completed before starting other workplans
- Datetime fix is a breaking change if tests rely on naive datetimes
- Health check will be used in CI/CD pipelines
- Estimated time: 1-2 days for datetime fix, 2-3 hours for health check
