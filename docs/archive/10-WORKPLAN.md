# 10-WORKPLAN: Migration Manager & CLI Commands

**Status**: CORE IMPLEMENTATION COMPLETE ✅
**Completion Date**: 2025-12-04
**Goal**: Implement backend-to-backend migration with validation and rollback
**Priority**: HIGH - Enables production workflows (dev → prod migration)
**Reference**: ADR 015 (Universal Export and Backend Migration Architecture) - Phases 2-3
**Estimated Tasks**: 24 tasks (Core implementation complete)
**Target Version**: v0.10.0
**Note**: MigrationManager core implemented, tested with SQLite. Full backend-pair testing and documentation deferred.

---

## Prerequisites

- [x] 9-WORKPLAN completed (universal export working from all backends)
- [x] Export tests passing for all 5 backends (SQLite wrapper fix applied)
- [x] ADR 015 Phase 1 complete

---

## Overview

This workplan implements the **Migration Manager** - a sophisticated system for migrating memories between backends with validation, verification, and rollback capability.

**Use Cases**:
- Migrate from SQLite (dev) to FalkorDB (production)
- Test performance across different backends
- Disaster recovery (restore to different backend)
- Switch cloud providers (Neo4j → Memgraph)

**Architecture**:
```
CLI Command → MigrationManager → Source Backend (export)
                                ↓
                         Validation Pipeline
                                ↓
                         Target Backend (import)
                                ↓
                         Verification & Rollback
```

---

## 1. Create Migration Data Models

### 1.1 Define Configuration Models

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/models.py`

Create new module with data models:

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

class BackendType(str, Enum):
    """Supported backend types."""
    SQLITE = "sqlite"
    NEO4J = "neo4j"
    MEMGRAPH = "memgraph"
    FALKORDB = "falkordb"
    FALKORDBLITE = "falkordblite"

@dataclass
class BackendConfig:
    """Configuration for a backend connection."""
    backend_type: BackendType
    path: Optional[str] = None  # For SQLite/FalkorDBLite
    uri: Optional[str] = None  # For Neo4j/Memgraph/FalkorDB
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None

    @classmethod
    def from_env(cls) -> "BackendConfig":
        """Create config from current environment variables."""
        from ..config import Config
        return cls(
            backend_type=BackendType(Config.BACKEND),
            path=Config.SQLITE_PATH,
            uri=Config.NEO4J_URI or Config.MEMGRAPH_URI or Config.FALKORDB_URI,
            username=Config.NEO4J_USER,
            password=Config.NEO4J_PASSWORD
        )

@dataclass
class MigrationOptions:
    """Options for migration operation."""
    dry_run: bool = False
    verbose: bool = False
    skip_duplicates: bool = True
    verify: bool = True
    rollback_on_failure: bool = True
    since: Optional[str] = None  # Timestamp for incremental migration

@dataclass
class ValidationResult:
    """Result of validation checks."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class VerificationResult:
    """Result of post-migration verification."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    source_count: int = 0
    target_count: int = 0
    sample_checks: int = 0
    sample_passed: int = 0

@dataclass
class MigrationResult:
    """Result of migration operation."""
    success: bool
    dry_run: bool = False
    source_stats: Optional[Dict[str, Any]] = None
    target_stats: Optional[Dict[str, Any]] = None
    imported_memories: int = 0
    imported_relationships: int = 0
    skipped_memories: int = 0
    verification_result: Optional[VerificationResult] = None
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
```

**Tasks**:
- [x] Create `src/memorygraph/migration/` module directory
- [x] Create `models.py` with all data classes
- [x] Add `__init__.py` to export public classes
- [x] Add type hints and docstrings
- [x] Add validation to BackendConfig (check required fields)

### 1.2 Write Model Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/migration/test_models.py`

- [x] Test BackendConfig creation from env vars
- [x] Test BackendConfig validation (missing required fields)
- [x] Test MigrationOptions defaults
- [x] Test all model serialization/deserialization (15/15 tests passing)

---

## 2. Implement Migration Manager

### 2.1 Create MigrationManager Core

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/manager.py`

Implement the main migration orchestrator:

```python
class MigrationManager:
    """Manages backend-to-backend memory migrations."""

    async def migrate(
        self,
        source_config: BackendConfig,
        target_config: BackendConfig,
        options: MigrationOptions
    ) -> MigrationResult:
        """
        Migrate memories from source backend to target backend.

        Phases:
        1. Pre-flight validation (backends accessible, compatible)
        2. Export from source
        3. Validate export data
        4. Import to target (if not dry-run)
        5. Verify migration
        6. Cleanup temp files

        Args:
            source_config: Source backend configuration
            target_config: Target backend configuration
            options: Migration options (dry_run, verify, etc.)

        Returns:
            MigrationResult with statistics and any errors

        Raises:
            MigrationError: If migration fails
        """
        start_time = time.time()
        logger.info(f"Starting migration: {source_config.backend_type} → {target_config.backend_type}")

        try:
            # Phase 1: Pre-flight checks
            await self._validate_source(source_config)
            await self._validate_target(target_config)
            await self._check_compatibility(source_config, target_config)

            # Phase 2: Export from source
            temp_export = await self._export_from_source(source_config, options)

            # Phase 3: Validate export
            validation_result = await self._validate_export(temp_export)
            if not validation_result.valid:
                raise MigrationError(f"Export validation failed: {validation_result.errors}")

            if options.dry_run:
                return MigrationResult(
                    success=True,
                    dry_run=True,
                    source_stats=await self._get_backend_stats(source_config),
                    validation_result=validation_result,
                    duration_seconds=time.time() - start_time
                )

            # Phase 4: Import to target
            import_stats = await self._import_to_target(target_config, temp_export, options)

            # Phase 5: Verify migration
            verification_result = await self._verify_migration(
                source_config,
                target_config,
                temp_export
            )

            if not verification_result.valid and options.rollback_on_failure:
                logger.error("Verification failed, rolling back...")
                await self._rollback_target(target_config)
                raise MigrationError(f"Verification failed: {verification_result.errors}")

            # Phase 6: Cleanup
            await self._cleanup_temp_files(temp_export)

            return MigrationResult(
                success=True,
                source_stats=await self._get_backend_stats(source_config),
                target_stats=await self._get_backend_stats(target_config),
                imported_memories=import_stats["imported_memories"],
                imported_relationships=import_stats["imported_relationships"],
                skipped_memories=import_stats["skipped_memories"],
                verification_result=verification_result,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return MigrationResult(
                success=False,
                duration_seconds=time.time() - start_time,
                errors=[str(e)]
            )
```

**Tasks**:
- [x] Create `manager.py` with MigrationManager class
- [x] Implement `migrate()` orchestration method
- [x] Add comprehensive error handling
- [x] Add logging at each phase
- [x] Add progress callbacks for verbose mode

### 2.2 Implement Validation Methods

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/manager.py`

Add validation methods to MigrationManager:

- [x] Implement `_validate_source()` - check source backend accessibility
- [x] Implement `_validate_target()` - check target backend accessibility and writability
- [x] Implement `_check_compatibility()` - verify backends are compatible
- [x] Implement `_validate_export()` - validate export file integrity
- [x] Add health check calls to backends
- [x] Warn if target already contains data

```python
async def _validate_source(self, config: BackendConfig) -> None:
    """Validate source backend is accessible and healthy."""
    backend = await self._create_backend(config)
    try:
        health = await backend.health_check()
        if not health.get("connected"):
            raise MigrationError(f"Source backend not accessible: {health.get('error')}")
        logger.info(f"Source backend healthy: {health.get('statistics', {}).get('memory_count', 0)} memories")
    finally:
        await backend.disconnect()

async def _validate_target(self, config: BackendConfig) -> None:
    """Validate target backend is accessible and writable."""
    backend = await self._create_backend(config)
    try:
        health = await backend.health_check()
        if not health.get("connected"):
            raise MigrationError(f"Target backend not accessible: {health.get('error')}")

        # Warn if target already has data
        stats = health.get("statistics", {})
        memory_count = stats.get("memory_count", 0)
        if memory_count > 0:
            logger.warning(f"Target backend already contains {memory_count} memories")
    finally:
        await backend.disconnect()
```

### 2.3 Implement Export/Import Methods

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/manager.py`

- [x] Implement `_export_from_source()` - export to temp file
- [x] Implement `_import_to_target()` - import from temp file
- [x] Use universal export from 9-WORKPLAN
- [x] Add progress reporting for verbose mode
- [x] Handle large datasets efficiently
- [x] Fix SQLite wrapper detection (use SQLiteMemoryDatabase for SQLite/FalkorDBLite backends)

```python
async def _export_from_source(
    self,
    config: BackendConfig,
    options: MigrationOptions
) -> Path:
    """Export data from source backend to temporary file."""
    backend = await self._create_backend(config)
    db = MemoryDatabase(backend)

    # Create temp export file
    temp_dir = Path(tempfile.gettempdir()) / "memorygraph_migration"
    temp_dir.mkdir(exist_ok=True)
    export_path = temp_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Use universal export (from 9-WORKPLAN)
    progress_callback = self._report_progress if options.verbose else None
    await export_to_json(db, str(export_path), progress_callback=progress_callback)

    await backend.disconnect()
    return export_path
```

### 2.4 Implement Verification Methods

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/manager.py`

- [x] Implement `_verify_migration()` - compare source and target
- [x] Check memory counts match
- [x] Check relationship counts match
- [x] Sample random memories for content verification
- [x] Return detailed VerificationResult
- [x] Fix SQLite wrapper detection in verification method

```python
async def _verify_migration(
    self,
    source_config: BackendConfig,
    target_config: BackendConfig,
    export_path: Path
) -> VerificationResult:
    """Verify target backend has same data as source."""
    source_backend = await self._create_backend(source_config)
    target_backend = await self._create_backend(target_config)

    source_db = MemoryDatabase(source_backend)
    target_db = MemoryDatabase(target_backend)

    errors = []

    try:
        # Check memory counts
        source_count = await self._count_memories(source_db)
        target_count = await self._count_memories(target_db)

        if source_count != target_count:
            errors.append(f"Memory count mismatch: source={source_count}, target={target_count}")

        # Check relationship counts
        source_rels = await self._count_relationships(source_db)
        target_rels = await self._count_relationships(target_db)

        if source_rels != target_rels:
            errors.append(f"Relationship count mismatch: source={source_rels}, target={target_rels}")

        # Sample check: verify 10 random memories
        sample_size = min(10, source_count)
        sample_passed = 0

        if sample_size > 0:
            sample_memories = await self._get_random_sample(source_db, sample_size)
            for memory in sample_memories:
                target_memory = await target_db.get_memory(memory.id)
                if not target_memory:
                    errors.append(f"Memory {memory.id} not found in target")
                elif target_memory.content != memory.content:
                    errors.append(f"Memory {memory.id} content mismatch")
                else:
                    sample_passed += 1

        return VerificationResult(
            valid=(len(errors) == 0),
            errors=errors,
            source_count=source_count,
            target_count=target_count,
            sample_checks=sample_size,
            sample_passed=sample_passed
        )

    finally:
        await source_backend.disconnect()
        await target_backend.disconnect()
```

### 2.5 Implement Rollback Method

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/manager.py`

- [x] Implement `_rollback_target()` - clean up failed migration
- [x] Delete all imported memories
- [x] Delete all imported relationships
- [x] Log rollback actions
- [x] Handle rollback failures gracefully

```python
async def _rollback_target(self, config: BackendConfig) -> None:
    """Rollback target backend to pre-migration state."""
    logger.info("Rolling back target backend...")
    backend = await self._create_backend(config)
    db = MemoryDatabase(backend)

    try:
        # WARNING: This deletes ALL data in target backend
        # In future, could track imported IDs and delete only those
        await db.clear_all_data()
        logger.info("Rollback complete")
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise MigrationError(f"Rollback failed: {e}")
    finally:
        await backend.disconnect()
```

### 2.6 Add Helper Methods

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/migration/manager.py`

- [x] Implement `_create_backend()` - create backend from config
- [x] Implement `_get_backend_stats()` - get statistics from backend
- [x] Implement `_count_memories()` - count memories in database
- [x] Implement `_count_relationships()` - count relationships in database
- [x] Implement `_get_random_sample()` - get random memories for verification
- [x] Implement `_cleanup_temp_files()` - delete temporary export files
- [x] Implement `_report_progress()` - progress callback for verbose mode

---

## 3. Add CLI Commands

### 3.1 Implement migrate Command

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`

Add new subcommand:

```python
# Migration command
migrate_parser = subparsers.add_parser(
    "migrate",
    help="Migrate memories between backends"
)
migrate_parser.add_argument(
    "--from",
    dest="source_backend",
    type=str,
    choices=["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"],
    help="Source backend type (defaults to current MEMORY_BACKEND)"
)
migrate_parser.add_argument(
    "--from-path",
    type=str,
    help="Source database path (for sqlite/falkordblite)"
)
migrate_parser.add_argument(
    "--from-uri",
    type=str,
    help="Source database URI (for neo4j/memgraph/falkordb)"
)
migrate_parser.add_argument(
    "--to",
    dest="target_backend",
    type=str,
    required=True,
    choices=["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"],
    help="Target backend type"
)
migrate_parser.add_argument(
    "--to-path",
    type=str,
    help="Target database path (for sqlite/falkordblite)"
)
migrate_parser.add_argument(
    "--to-uri",
    type=str,
    help="Target database URI (for neo4j/memgraph/falkordb)"
)
migrate_parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Validate migration without making changes"
)
migrate_parser.add_argument(
    "--verbose",
    action="store_true",
    help="Show detailed progress information"
)
migrate_parser.add_argument(
    "--skip-duplicates",
    action="store_true",
    default=True,
    help="Skip memories that already exist in target"
)
migrate_parser.add_argument(
    "--no-verify",
    action="store_true",
    help="Skip post-migration verification (faster but less safe)"
)
```

**Tasks**:
- [x] Add `migrate` subcommand with all arguments
- [x] Add argument validation
- [x] Add help text and examples

### 3.2 Implement migrate Handler

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`

Create handler function:

```python
async def handle_migrate(args: argparse.Namespace) -> None:
    """Handle migrate command."""
    from .migration.manager import MigrationManager
    from .migration.models import BackendConfig, MigrationOptions

    print(f"\n🔄 Migrating memories: {args.source_backend or 'current'} → {args.target_backend}")

    # Build source config
    if args.source_backend:
        source_config = BackendConfig(
            backend_type=BackendType(args.source_backend),
            path=args.from_path,
            uri=args.from_uri
        )
    else:
        source_config = BackendConfig.from_env()

    # Build target config
    target_config = BackendConfig(
        backend_type=BackendType(args.target_backend),
        path=args.to_path,
        uri=args.to_uri
    )

    # Build options
    options = MigrationOptions(
        dry_run=args.dry_run,
        verbose=args.verbose,
        skip_duplicates=args.skip_duplicates,
        verify=not args.no_verify,
        rollback_on_failure=True
    )

    try:
        manager = MigrationManager()
        result = await manager.migrate(source_config, target_config, options)

        if result.dry_run:
            print("\n✅ Dry-run successful - migration would proceed safely")
            print(f"   Source: {result.source_stats['memory_count']} memories")
            if result.validation_result.warnings:
                print("\n⚠️  Warnings:")
                for warning in result.validation_result.warnings:
                    print(f"   - {warning}")
        elif result.success:
            print("\n✅ Migration completed successfully!")
            print(f"   Migrated: {result.imported_memories} memories")
            print(f"   Migrated: {result.imported_relationships} relationships")
            if result.skipped_memories > 0:
                print(f"   Skipped: {result.skipped_memories} duplicates")
            print(f"   Duration: {result.duration_seconds:.1f} seconds")
        else:
            print("\n❌ Migration failed!")
            for error in result.errors:
                print(f"   - {error}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
```

**Tasks**:
- [x] Create `handle_migrate()` function
- [x] Add config building from CLI args
- [x] Add progress output formatting
- [x] Add error handling and exit codes
- [x] Wire up handler to subparser

---

## 4. Testing

### 4.1 Unit Tests for MigrationManager

**File**: `/Users/gregorydickson/claude-code-memory/tests/migration/test_manager.py`

- [ ] Test `_validate_source()` with healthy backend
- [ ] Test `_validate_source()` with unhealthy backend
- [ ] Test `_validate_target()` with empty target
- [ ] Test `_validate_target()` with existing data (should warn)
- [ ] Test `_check_compatibility()` for all backend pairs
- [ ] Test `_verify_migration()` with matching data
- [ ] Test `_verify_migration()` with mismatched counts
- [ ] Test `_verify_migration()` with mismatched content
- [ ] Test `_rollback_target()` clears target backend

### 4.2 Integration Tests for Migration

**File**: `/Users/gregorydickson/claude-code-memory/tests/migration/test_migration_e2e.py`

Test complete migration flows:

- [x] Test SQLite → SQLite migration (baseline)
- [ ] Test SQLite → FalkorDBLite migration
- [x] Test dry-run mode (no data written)
- [x] Test migration with skip_duplicates
- [x] Test migration with verification
- [x] Test migration with rollback on failure
- [ ] Test large dataset migration (1000+ memories)

### 4.3 CLI Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/cli/test_migrate_command.py`

- [ ] Test `memorygraph migrate --help`
- [ ] Test migrate with --dry-run
- [ ] Test migrate with --verbose
- [ ] Test migrate with invalid source backend
- [ ] Test migrate with invalid target backend
- [ ] Test migrate with missing required arguments
- [ ] Test migrate success output formatting

---

## 5. Documentation

### 5.1 Create Migration Guide

**File**: `/Users/gregorydickson/claude-code-memory/docs/MIGRATION_GUIDE.md`

Create comprehensive guide:

- [ ] Introduction to backend migration
- [ ] When to use migration
- [ ] Migration use cases (dev→prod, disaster recovery, etc.)
- [ ] Step-by-step migration instructions
- [ ] Dry-run recommendations
- [ ] Troubleshooting section
- [ ] Performance expectations

### 5.2 Update CLI Documentation

**File**: `/Users/gregorydickson/claude-code-memory/docs/CLI.md` (or README)

- [ ] Add `migrate` command documentation
- [ ] Add command-line examples
- [ ] Document all flags and options
- [ ] Add common migration scenarios

### 5.3 Update CHANGELOG

**File**: `/Users/gregorydickson/claude-code-memory/CHANGELOG.md`

- [ ] Add migration feature to changelog
- [ ] List supported migration paths
- [ ] Note verification and rollback capabilities

---

## Acceptance Criteria

- [ ] MigrationManager successfully migrates between all backend pairs
- [ ] Dry-run mode validates without writing data
- [ ] Verification detects data mismatches
- [ ] Rollback works on migration failure
- [ ] CLI `migrate` command works with all arguments
- [ ] Progress reporting works in verbose mode
- [ ] Migration of 1000 memories completes in <30 seconds
- [ ] All tests pass (unit + integration)
- [ ] Documentation complete and accurate

---

## Notes for Coding Agent

1. **Safety First**: Rollback capability is critical - test thoroughly
2. **Validation is Key**: Multi-stage validation prevents data loss
3. **Progress Feedback**: Users need to see progress on large migrations
4. **Error Messages**: Clear, actionable error messages help users debug
5. **Temp Files**: Clean up temp files even on failure (use try/finally)
6. **Backend Compatibility**: Test all backend pairs, not just SQLite
7. **Async Handling**: MigrationManager is async, CLI needs sync wrapper

## Dependencies

- Requires 9-WORKPLAN (universal export)
- Requires all 5 backends to be functional
- No new Python dependencies

## Estimated Effort

**Total**: 6-8 hours

| Phase | Effort |
|-------|--------|
| 1. Data Models | 1 hour |
| 2. MigrationManager | 3-4 hours |
| 3. CLI Commands | 1 hour |
| 4. Testing | 2-3 hours |
| 5. Documentation | 1 hour |

---

## Next Steps

After this workplan is complete:
- **11-WORKPLAN**: MCP tools for migration, comprehensive testing, benchmarks
