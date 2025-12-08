# 11-WORKPLAN: MCP Tools, Testing & Release Preparation

**Status**: MCP TOOLS COMPLETE ✅ | TESTING PARTIAL
**Completion Date**: 2025-12-04 (MCP tools)
**Goal**: Add MCP migration tools, comprehensive testing, and prepare for release
**Priority**: HIGH - Completes ADR 015 implementation
**Reference**: ADR 015 (Universal Export and Backend Migration Architecture) - Phases 4-6
**Estimated Tasks**: 26 tasks (MCP tools complete, comprehensive testing/docs pending)
**Target Version**: v0.10.0
**Note**: MCP migration tools implemented and tested. Performance benchmarks, full backend-pair testing, and release documentation pending.

---

## Prerequisites

- [x] 9-WORKPLAN completed (universal export from all backends)
- [x] 10-WORKPLAN completed (MigrationManager and CLI working)
- [ ] All export/import tests passing
- [ ] All migration tests passing

---

## Overview

This workplan completes the ADR 015 implementation by:
1. Adding MCP tools for migrations (Claude/AI access)
2. Comprehensive backend-to-backend testing matrix
3. Performance benchmarks
4. Documentation polish
5. Release preparation

**Deliverables**:
- `migrate_database` MCP tool
- `validate_migration` MCP tool
- 25 backend-pair migration tests (5x5 matrix)
- Performance benchmarks for all backends
- Complete user documentation
- Release-ready v0.10.0

---

## 1. MCP Tools for Migration

### 1.1 Add migrate_database Tool

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/migration_tools.py`

Create new tools module for migration:

```python
"""MCP tools for database migration."""

from typing import Dict, Any, Optional
from ..migration.manager import MigrationManager
from ..migration.models import BackendConfig, MigrationOptions, BackendType

async def handle_migrate_database(
    target_backend: str,
    target_config: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    skip_duplicates: bool = True,
    verify: bool = True
) -> Dict[str, Any]:
    """
    Migrate memories from current backend to target backend.

    This tool enables AI assistants to help users migrate their memory database
    to a different backend (e.g., SQLite → FalkorDB for production).

    Args:
        target_backend: Target backend type (sqlite, neo4j, memgraph, falkordb, falkordblite)
        target_config: Target backend configuration (path, URI, credentials)
        dry_run: Validate without making changes
        skip_duplicates: Skip memories that already exist in target
        verify: Verify data integrity after migration

    Returns:
        Migration result with statistics and status

    Example:
        # Migrate from SQLite to FalkorDB
        result = await migrate_database(
            target_backend="falkordb",
            target_config={
                "uri": "redis://prod.example.com:6379",
                "username": "admin",
                "password": "secret"
            },
            dry_run=True  # Test first
        )
    """
    try:
        # Source is current environment
        source_config = BackendConfig.from_env()

        # Build target config
        target_config_obj = BackendConfig(
            backend_type=BackendType(target_backend),
            path=target_config.get("path") if target_config else None,
            uri=target_config.get("uri") if target_config else None,
            username=target_config.get("username") if target_config else None,
            password=target_config.get("password") if target_config else None,
            database=target_config.get("database") if target_config else None
        )

        # Build options
        options = MigrationOptions(
            dry_run=dry_run,
            verbose=True,
            skip_duplicates=skip_duplicates,
            verify=verify,
            rollback_on_failure=True
        )

        # Perform migration
        manager = MigrationManager()
        result = await manager.migrate(source_config, target_config_obj, options)

        # Format response
        return {
            "success": result.success,
            "dry_run": result.dry_run,
            "source_backend": source_config.backend_type.value,
            "target_backend": target_backend,
            "imported_memories": result.imported_memories,
            "imported_relationships": result.imported_relationships,
            "skipped_memories": result.skipped_memories,
            "duration_seconds": result.duration_seconds,
            "verification": {
                "valid": result.verification_result.valid if result.verification_result else None,
                "source_count": result.verification_result.source_count if result.verification_result else None,
                "target_count": result.verification_result.target_count if result.verification_result else None,
                "errors": result.verification_result.errors if result.verification_result else []
            } if result.verification_result else None,
            "errors": result.errors
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

**Tasks**:
- [x] Create `src/memorygraph/tools/migration_tools.py`
- [x] Implement `handle_migrate_database()` tool handler
- [x] Add comprehensive error handling
- [x] Add logging for debugging
- [x] Format response for MCP protocol

### 1.2 Add validate_migration Tool

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/migration_tools.py`

Add validation tool (dry-run helper):

```python
async def handle_validate_migration(
    target_backend: str,
    target_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate that migration to target backend would succeed.

    This is a dry-run that checks:
    - Source backend is accessible
    - Target backend is accessible
    - Backends are compatible
    - Estimates migration size and duration

    Args:
        target_backend: Target backend type
        target_config: Target backend configuration

    Returns:
        Validation result with checks and estimates
    """
    # Call migrate_database with dry_run=True
    return await handle_migrate_database(
        target_backend=target_backend,
        target_config=target_config,
        dry_run=True,
        verify=False  # No need to verify in dry-run
    )
```

**Tasks**:
- [x] Implement `handle_validate_migration()` tool handler
- [x] Reuse migrate_database with dry_run=True
- [x] Add migration size estimates to response

### 1.3 Register MCP Tools

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`

Add tools to extended profile:

```python
# Migration tools (extended profile)
{
    "name": "migrate_database",
    "description": "Migrate memories from current backend to another backend (e.g., SQLite → FalkorDB). Supports dry-run for validation.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "target_backend": {
                "type": "string",
                "enum": ["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"],
                "description": "Target backend to migrate to"
            },
            "target_config": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Database path (for SQLite/FalkorDBLite)"},
                    "uri": {"type": "string", "description": "Database URI (for Neo4j/Memgraph/FalkorDB)"},
                    "username": {"type": "string", "description": "Database username"},
                    "password": {"type": "string", "description": "Database password"},
                    "database": {"type": "string", "description": "Database name"}
                },
                "description": "Target backend configuration"
            },
            "dry_run": {
                "type": "boolean",
                "default": False,
                "description": "Validate without making changes"
            },
            "skip_duplicates": {
                "type": "boolean",
                "default": True,
                "description": "Skip memories that already exist in target"
            },
            "verify": {
                "type": "boolean",
                "default": True,
                "description": "Verify data integrity after migration"
            }
        },
        "required": ["target_backend"]
    }
},
{
    "name": "validate_migration",
    "description": "Validate that migration to target backend would succeed without making changes. Returns compatibility checks and size estimates.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "target_backend": {
                "type": "string",
                "enum": ["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"],
                "description": "Target backend to validate migration to"
            },
            "target_config": {
                "type": "object",
                "description": "Target backend configuration"
            }
        },
        "required": ["target_backend"]
    }
}
```

**Tasks**:
- [x] Add tool schemas to extended profile in `server.py`
- [x] Wire up handlers in tool dispatcher
- [x] Add to extended tool list (not core tools)
- [x] Test tool registration with MCP client

### 1.4 Write MCP Tool Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/tools/test_migration_tools.py`

- [x] Test `migrate_database` with valid config
- [x] Test `migrate_database` with dry_run=True
- [x] Test `migrate_database` with invalid backend
- [x] Test `migrate_database` with missing credentials
- [x] Test `validate_migration` returns correct validation
- [x] Test tool response format matches MCP protocol
- [x] Test error handling in tools

---

## 2. Comprehensive Backend Testing

### 2.1 Backend-to-Backend Migration Matrix

**File**: `/Users/gregorydickson/claude-code-memory/tests/migration/test_backend_pairs.py`

Test all 25 backend pair combinations (5x5 matrix):

```python
"""Test migration between all backend pairs."""

import pytest
from memorygraph.migration.manager import MigrationManager
from memorygraph.migration.models import BackendConfig, MigrationOptions, BackendType

BACKENDS = [
    BackendType.SQLITE,
    BackendType.NEO4J,
    BackendType.MEMGRAPH,
    BackendType.FALKORDB,
    BackendType.FALKORDBLITE
]

@pytest.mark.parametrize("source_backend", BACKENDS)
@pytest.mark.parametrize("target_backend", BACKENDS)
async def test_migration_between_backends(
    source_backend: BackendType,
    target_backend: BackendType,
    sample_memories  # Fixture with test data
):
    """Test migration from source_backend to target_backend."""

    if source_backend == target_backend:
        pytest.skip("Skipping same-backend migration")

    # Skip if backend not available (e.g., Neo4j not running)
    if not is_backend_available(source_backend):
        pytest.skip(f"{source_backend} not available")
    if not is_backend_available(target_backend):
        pytest.skip(f"{target_backend} not available")

    # Setup source with test data
    source_config = create_test_backend_config(source_backend)
    source_db = await setup_backend_with_data(source_config, sample_memories)

    # Setup empty target
    target_config = create_test_backend_config(target_backend)
    target_db = await setup_empty_backend(target_config)

    # Perform migration
    manager = MigrationManager()
    options = MigrationOptions(
        dry_run=False,
        verbose=True,
        skip_duplicates=False,
        verify=True,
        rollback_on_failure=True
    )

    result = await manager.migrate(source_config, target_config, options)

    # Assertions
    assert result.success
    assert result.imported_memories == len(sample_memories)
    assert result.verification_result.valid
    assert result.verification_result.source_count == result.verification_result.target_count

    # Cleanup
    await cleanup_backend(source_db)
    await cleanup_backend(target_db)
```

**Tasks**:
- [ ] Create parametrized test for all backend pairs
- [ ] Create test fixtures for backend setup
- [ ] Create helper functions (is_backend_available, setup_with_data, etc.)
- [ ] Skip tests if backend not available (don't fail CI)
- [ ] Add cleanup to prevent test pollution
- [ ] Test with 100 memories and 150 relationships
- [ ] Verify data fidelity for each pair
- [ ] Document which pairs pass/fail

### 2.2 Data Fidelity Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/migration/test_data_fidelity.py`

Test that all data is preserved exactly:

- [ ] Test all memory fields preserved (title, content, type, tags, etc.)
- [ ] Test all relationship fields preserved (type, context, strength, etc.)
- [ ] Test context fields preserved (project_path, session_id, etc.)
- [ ] Test timestamps preserved
- [ ] Test special characters in content (Unicode, emojis, etc.)
- [ ] Test large content (10KB+ text)
- [ ] Test empty fields (None, empty lists)
- [ ] Compare checksums of exported data

### 2.3 Edge Case Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/migration/test_migration_edge_cases.py`

- [ ] Test empty database migration (0 memories)
- [ ] Test single memory migration
- [ ] Test large database migration (10,000+ memories)
- [ ] Test migration with orphaned relationships
- [ ] Test migration with duplicate memory IDs
- [ ] Test migration interrupted mid-way (rollback)
- [ ] Test target backend already has data
- [ ] Test source backend disconnects during export
- [ ] Test target backend disconnects during import

---

## 3. Performance Benchmarks

### 3.1 Export Performance Benchmarks

**File**: `/Users/gregorydickson/claude-code-memory/tests/benchmarks/test_export_benchmarks.py`

Benchmark export from each backend:

- [ ] Benchmark SQLite export (1k, 5k, 10k memories)
- [ ] Benchmark Neo4j export (if available)
- [ ] Benchmark Memgraph export (if available)
- [ ] Benchmark FalkorDB export (if available)
- [ ] Benchmark FalkorDBLite export (1k, 5k, 10k memories)
- [ ] Measure throughput (memories/second)
- [ ] Measure memory usage during export
- [ ] Document performance characteristics

**Performance Targets** (from ADR 015):
- 1,000 memories: ~3 seconds
- 10,000 memories: ~30 seconds

### 3.2 Import Performance Benchmarks

**File**: `/Users/gregorydickson/claude-code-memory/tests/benchmarks/test_import_benchmarks.py`

Benchmark import to each backend:

- [ ] Benchmark SQLite import (1k, 5k, 10k memories)
- [ ] Benchmark Neo4j import (if available)
- [ ] Benchmark Memgraph import (if available)
- [ ] Benchmark FalkorDB import (if available)
- [ ] Benchmark FalkorDBLite import (1k, 5k, 10k memories)
- [ ] Measure throughput (memories/second)
- [ ] Measure memory usage during import
- [ ] Document performance characteristics

**Performance Targets** (from ADR 015):
- 1,000 memories: ~5 seconds
- 10,000 memories: ~50 seconds

### 3.3 Full Migration Benchmarks

**File**: `/Users/gregorydickson/claude-code-memory/tests/benchmarks/test_migration_benchmarks.py`

Benchmark complete migration flows:

- [ ] Benchmark SQLite → FalkorDB migration (most common use case)
- [ ] Benchmark SQLite → Neo4j migration
- [ ] Benchmark FalkorDBLite → FalkorDB migration
- [ ] Test with 1k, 5k, 10k memories
- [ ] Measure end-to-end duration
- [ ] Measure verification overhead
- [ ] Document realistic migration times

**Performance Target** (from ADR 015):
- Full migration of 10,000 memories: ~2 minutes

### 3.4 Performance Report

**File**: `/Users/gregorydickson/claude-code-memory/docs/PERFORMANCE.md`

Create performance documentation:

- [ ] Document all benchmark results
- [ ] Create performance comparison tables
- [ ] Add graphs/charts if helpful
- [ ] Document performance tuning tips
- [ ] Note performance differences between backends
- [ ] Add guidance for large datasets (100k+ memories)

---

## 4. Documentation Updates

### 4.1 Update User Guide

**File**: `/Users/gregorydickson/claude-code-memory/docs/USER_GUIDE.md` (or similar)

- [ ] Add "Backend Migration" section
- [ ] Document when to migrate backends
- [ ] Add step-by-step migration tutorial
- [ ] Include screenshots or examples
- [ ] Document common pitfalls
- [ ] Add troubleshooting FAQ

### 4.2 Update Tool Selection Guide

**File**: `/Users/gregorydickson/claude-code-memory/docs/TOOL_SELECTION_GUIDE.md`

- [ ] Add `migrate_database` tool to guide
- [ ] Add `validate_migration` tool to guide
- [ ] Document use cases for migration tools
- [ ] Add examples of AI-assisted migration
- [ ] Update decision tree for when to use migration

### 4.3 Create Migration Examples

**File**: `/Users/gregorydickson/claude-code-memory/docs/examples/MIGRATION_EXAMPLES.md`

Create practical examples:

- [ ] Example: Dev → Prod migration (SQLite → FalkorDB)
- [ ] Example: Backend performance comparison
- [ ] Example: Disaster recovery
- [ ] Example: Multi-device sync
- [ ] Example: Cloud provider switch (Neo4j → Memgraph)
- [ ] Add complete CLI commands for each example
- [ ] Add expected output for each example

### 4.4 Update README

**File**: `/Users/gregorydickson/claude-code-memory/README.md`

- [ ] Add "Backend Migration" to features list
- [ ] Add quick migration example
- [ ] Link to MIGRATION_GUIDE.md
- [ ] Update backend support table (show migration support)
- [ ] Add migration to "Key Features" section

### 4.5 Update CHANGELOG

**File**: `/Users/gregorydickson/claude-code-memory/CHANGELOG.md`

Create complete v0.10.0 changelog entry:

```markdown
## [0.10.0] - 2025-XX-XX

### Added
- **Universal Export**: Export/import now works from ANY backend (SQLite, Neo4j, Memgraph, FalkorDB, FalkorDBLite)
- **Backend Migration**: New `memorygraph migrate` command for backend-to-backend migrations
- **Migration Tools**: MCP tools `migrate_database` and `validate_migration` for AI-assisted migrations
- **Migration Validation**: Multi-stage validation (pre-flight, export, verification)
- **Rollback Capability**: Automatic rollback on migration failure
- **Progress Reporting**: Real-time progress for large migrations
- **Dry-Run Mode**: Validate migrations without making changes

### Changed
- Export/import refactored to use backend-agnostic MemoryDatabase interface
- Export no longer restricted to SQLite backend
- Export format includes backend type metadata

### Fixed
- Export now works from Neo4j, Memgraph, and FalkorDB backends
- Import handles large datasets efficiently with pagination

### Performance
- Export: 1k memories in ~3s, 10k memories in ~30s
- Import: 1k memories in ~5s, 10k memories in ~50s
- Full migration: 10k memories in ~2 minutes (including verification)

### Documentation
- Added MIGRATION_GUIDE.md with step-by-step instructions
- Added PERFORMANCE.md with benchmark results
- Added migration examples for common use cases
- Updated README with migration features
```

**Tasks**:
- [ ] Create comprehensive changelog entry
- [ ] Document all new features
- [ ] Document breaking changes (none expected)
- [ ] Document performance improvements
- [ ] Document new documentation

---

## 5. Release Preparation

### 5.1 Version Bump

**File**: `/Users/gregorydickson/claude-code-memory/pyproject.toml`

- [ ] Update version to 0.10.0
- [ ] Update dependencies if needed
- [ ] Update Python version requirements if needed

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/__init__.py`

- [ ] Update `__version__` to "0.10.0"

### 5.2 Pre-Release Checklist

Create release checklist:

- [ ] All tests pass (unit + integration + benchmarks)
- [ ] Test coverage > 90%
- [ ] All backends tested manually
- [ ] Migration tested on real data
- [ ] Documentation reviewed and complete
- [ ] CHANGELOG complete
- [ ] README updated
- [ ] Examples tested and working
- [ ] CLI help text accurate
- [ ] MCP tools work in Claude Desktop
- [ ] No known critical bugs
- [ ] Performance targets met

### 5.3 Create Release Notes

**File**: `/Users/gregorydickson/claude-code-memory/docs/RELEASE_NOTES_0.10.0.md`

Create detailed release notes:

- [ ] Executive summary of v0.10.0
- [ ] Key features and benefits
- [ ] Migration guide for existing users
- [ ] Known issues and limitations
- [ ] What's coming in v0.11.0
- [ ] Thank contributors

### 5.4 Test on Clean Install

- [ ] Create fresh virtual environment
- [ ] Install from PyPI test repository
- [ ] Test basic functionality
- [ ] Test migration command
- [ ] Test MCP server registration
- [ ] Test with Claude Desktop
- [ ] Document any installation issues

### 5.5 Update Issue Tracker

- [ ] Close all issues addressed in v0.10.0
- [ ] Update milestone to "0.10.0 - Released"
- [ ] Create milestone for v0.11.0 (next features)
- [ ] Triage remaining open issues

---

## 6. Optional Enhancements

### 6.1 Migration Analytics (Optional)

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/analytics.py`

- [ ] Track migration metadata (source, target, duration, success)
- [ ] Store migration history in database
- [ ] Create `memorygraph migration-history` command
- [ ] Add analytics to migration result

### 6.2 Incremental Migration (Optional)

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/manager.py`

- [ ] Add `--since` parameter to migration
- [ ] Only migrate memories created/updated after timestamp
- [ ] Useful for periodic syncs
- [ ] Document incremental migration use cases

### 6.3 Migration Scheduling (Optional)

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`

- [ ] Add `memorygraph schedule-migration` command
- [ ] Use cron or similar for scheduling
- [ ] Useful for automated backups
- [ ] Document scheduling setup

---

## Acceptance Criteria

### Functionality
- [x] MCP migration tools work correctly (7 tests passing)
- [ ] All 25 backend pair migrations pass tests (or documented as unsupported) - DEFERRED (Phase 2 - requires all backends available)
- [x] Data fidelity 100% (checksums match before/after) - VERIFIED for SQLite
- [x] Rollback works on migration failure (tested)
- [x] Dry-run mode works correctly (tested)
- [x] Progress reporting works for large migrations (implemented in manager)

### Performance
- [ ] Export: 10k memories in <30 seconds
- [ ] Import: 10k memories in <50 seconds
- [ ] Full migration: 10k memories in <2 minutes
- [ ] Memory usage reasonable (doesn't load all into RAM)

### Documentation
- [ ] MIGRATION_GUIDE.md complete
- [ ] PERFORMANCE.md with benchmarks
- [ ] README updated
- [ ] CHANGELOG complete
- [ ] Examples working
- [ ] Release notes ready

### Quality
- [ ] All tests pass (unit + integration + benchmarks)
- [ ] Test coverage > 90%
- [ ] No regressions in existing functionality
- [ ] CI pipeline passes
- [ ] Code reviewed and clean

---

## Notes for Coding Agent

1. **Comprehensive Testing**: This is the final workplan - testing must be thorough
2. **Performance Matters**: Run all benchmarks and document results
3. **Documentation is Critical**: Users need clear migration guidance
4. **Test Real Backends**: Don't just mock - test with actual Neo4j, FalkorDB, etc.
5. **Clean Up**: Remove temp files, close connections, prevent test pollution
6. **Async Handling**: Migration tools are async, ensure proper async/await usage
7. **Error Messages**: Clear, helpful error messages for users

## Dependencies

- Requires 9-WORKPLAN (universal export)
- Requires 10-WORKPLAN (MigrationManager)
- Requires all 5 backends functional
- No new Python dependencies

## Estimated Effort

**Total**: 8-10 hours

| Phase | Effort |
|-------|--------|
| 1. MCP Tools | 2 hours |
| 2. Backend Testing | 3-4 hours |
| 3. Performance Benchmarks | 2 hours |
| 4. Documentation | 2 hours |
| 5. Release Prep | 1-2 hours |

---

## Completion

When this workplan is complete:
- ✅ ADR 015 fully implemented
- ✅ Universal export works from all backends
- ✅ Backend migration is production-ready
- ✅ Comprehensive testing complete
- ✅ Documentation complete
- ✅ Ready for v0.10.0 release

**Next Major Feature**: Multi-tenancy (ADR 009) or Cloud Sync (future ADR)
