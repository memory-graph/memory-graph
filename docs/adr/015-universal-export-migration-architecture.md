# ADR 015: Universal Export and Backend Migration Architecture

## Status
Proposed

## Date
2025-12-03

## Context

MemoryGraph currently supports multiple backends (SQLite, Neo4j, Memgraph, FalkorDB, FalkorDBLite) through a unified `GraphBackend` interface. However, the existing export/import functionality in `src/memorygraph/utils/export_import.py` and CLI commands have critical limitations:

### Current State

1. **Export/Import is SQLite-Only**: The CLI explicitly checks and rejects non-SQLite backends:
   ```python
   if not isinstance(backend, SQLiteFallbackBackend):
       print("❌ Error: Export currently only supported for SQLite backend")
       sys.exit(1)
   ```

2. **Backend Lock-In**: Users cannot:
   - Export from Neo4j/Memgraph/FalkorDB for backup
   - Migrate from local SQLite to remote FalkorDB when scaling up
   - Switch between cloud providers (Neo4j → Memgraph)
   - Create portable backups independent of backend choice

3. **Growing Use Cases**:
   - **Scaling Up**: Start with SQLite for development, migrate to FalkorDB for production
   - **Backend Evaluation**: Test same dataset across different backends for performance comparison
   - **Disaster Recovery**: Create backend-agnostic backups that can restore to any backend
   - **Team Collaboration**: Share memory dumps between teammates using different backends
   - **Cloud Migration**: Move from self-hosted Neo4j to managed Memgraph

### Related Work

- **ADR 013** covers comprehensive backup architecture but focuses on backup workflows and automation
- This ADR focuses specifically on:
  1. Making export work from **any backend** (not just SQLite)
  2. Enabling **backend-to-backend migration** as a first-class feature
  3. Backend migration workflows and validation

## Decision Drivers

1. **Backend Agnosticism**: Export/import should work identically across all backends using the `GraphBackend` interface
2. **Zero Data Loss**: Round-trip fidelity must be 100% (all memories, relationships, metadata preserved)
3. **User Experience**: Single command for complex migrations (`memorygraph migrate`)
4. **Performance**: Handle large datasets (10k+ memories) efficiently
5. **Safety**: Validate data integrity before, during, and after migration
6. **Backward Compatibility**: Existing export files remain valid

## Decision

Implement universal export and backend-to-backend migration through:

1. **Backend-Agnostic Export**: Refactor export to use `GraphBackend` interface methods instead of SQLite-specific queries
2. **Migration Command**: New `memorygraph migrate` CLI command for backend-to-backend transfers
3. **Validation Pipeline**: Multi-stage validation to ensure data integrity
4. **Progress Reporting**: Real-time feedback for long-running operations
5. **Rollback Capability**: Safe migration with ability to revert on failure

## Architecture

### 1. Universal Export Implementation

**Current Problem:**
```python
# export_import.py - Direct SQLite query, non-portable
query = "SELECT properties FROM nodes WHERE label = 'Memory' ORDER BY created_at DESC"
rows = db.backend.execute_sync(query)
```

**Solution:**
Use the backend-agnostic database interface that already exists:

```python
async def export_to_json(db: MemoryDatabase, output_path: str) -> None:
    """
    Export from ANY backend using MemoryDatabase interface.

    Works with: SQLite, Neo4j, Memgraph, FalkorDB, FalkorDBLite
    """
    all_memories = []
    offset = 0
    batch_size = 1000

    # Use search_memories (works on all backends)
    while True:
        query = SearchQuery(
            query="",  # Empty query = all memories
            limit=batch_size,
            offset=offset,
            match_mode=MatchMode.ANY
        )

        result = await db.search_memories(query)
        all_memories.extend(result.results)

        if not result.has_more:
            break

        offset += batch_size

    # Export relationships (also backend-agnostic)
    relationships = []
    for memory in all_memories:
        related = await db.get_related_memories(
            memory_id=memory.id,
            max_depth=1
        )
        for related_memory, relationship in related:
            relationships.append(relationship)

    # Build export format (from ADR 013)
    export_data = {
        "format_version": "2.0",
        "export_date": datetime.now(timezone.utc).isoformat(),
        "backend_type": db.backend.backend_name(),
        "memories": [memory.dict() for memory in all_memories],
        "relationships": [rel.dict() for rel in relationships]
    }

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
```

**Key Changes:**
- Remove `SQLiteFallbackBackend` type check
- Use `MemoryDatabase.search_memories()` instead of raw SQL
- Use `MemoryDatabase.get_related_memories()` for relationships
- Works with any backend implementing `GraphBackend` interface

### 2. Migration Command Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLI: memorygraph migrate                   │
│  --source-backend sqlite --target-backend falkordb              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     MigrationManager                            │
│  - Validation (pre-flight checks)                               │
│  - Export from source backend                                   │
│  - Import to target backend                                     │
│  - Verification (data integrity)                                │
│  - Rollback on failure                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
           ┌──────────────────┴──────────────────┐
           ↓                                      ↓
┌──────────────────────┐               ┌──────────────────────┐
│   Source Backend     │               │   Target Backend     │
│  (SQLite, Neo4j...)  │               │  (FalkorDB, ...)     │
└──────────────────────┘               └──────────────────────┘
```

### 3. Migration Command API

```bash
# Basic migration (auto-detect backends from env)
memorygraph migrate --to falkordb

# Explicit source and target
memorygraph migrate \
  --from sqlite \
  --from-path ~/.memorygraph/memory.db \
  --to falkordb \
  --to-host falkordb.example.com \
  --to-port 6379

# Dry-run (validate without making changes)
memorygraph migrate --from sqlite --to neo4j --dry-run

# With progress reporting
memorygraph migrate --from sqlite --to memgraph --verbose

# Incremental (only new/changed memories since timestamp)
memorygraph migrate --from sqlite --to neo4j --since "2025-12-01T00:00:00Z"
```

### 4. Migration Manager Implementation

```python
class MigrationManager:
    """Handles backend-to-backend migration with validation."""

    async def migrate(
        self,
        source_config: BackendConfig,
        target_config: BackendConfig,
        options: MigrationOptions
    ) -> MigrationResult:
        """
        Migrate memories from source backend to target backend.

        Args:
            source_config: Source backend configuration
            target_config: Target backend configuration
            options: Migration options (dry_run, validate, etc.)

        Returns:
            MigrationResult with statistics and any errors
        """
        logger.info(f"Starting migration: {source_config.backend_type} → {target_config.backend_type}")

        # Phase 1: Pre-flight validation
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
                source_stats=self._get_backend_stats(source_config),
                validation_result=validation_result
            )

        # Phase 4: Import to target
        try:
            import_result = await self._import_to_target(
                target_config,
                temp_export,
                options
            )
        except Exception as e:
            logger.error(f"Import failed: {e}")
            await self._cleanup_temp_files(temp_export)
            raise MigrationError(f"Import failed: {e}")

        # Phase 5: Post-migration verification
        verification_result = await self._verify_migration(
            source_config,
            target_config,
            temp_export
        )

        if not verification_result.valid:
            logger.error("Migration verification failed")
            if options.rollback_on_failure:
                await self._rollback_target(target_config)
            raise MigrationError(f"Verification failed: {verification_result.errors}")

        # Phase 6: Cleanup
        await self._cleanup_temp_files(temp_export)

        logger.info("Migration completed successfully")
        return MigrationResult(
            success=True,
            source_stats=self._get_backend_stats(source_config),
            target_stats=self._get_backend_stats(target_config),
            import_result=import_result,
            verification_result=verification_result
        )

    async def _validate_source(self, config: BackendConfig) -> None:
        """Validate source backend is accessible and healthy."""
        backend = await BackendFactory.create_backend(config)
        health = await backend.health_check()

        if not health.get("connected"):
            raise MigrationError(f"Source backend not accessible: {health.get('error')}")

        await backend.disconnect()

    async def _validate_target(self, config: BackendConfig) -> None:
        """Validate target backend is accessible and writable."""
        backend = await BackendFactory.create_backend(config)
        health = await backend.health_check()

        if not health.get("connected"):
            raise MigrationError(f"Target backend not accessible: {health.get('error')}")

        # Check if target is empty or get user confirmation if not
        stats = health.get("statistics", {})
        if stats.get("memory_count", 0) > 0:
            logger.warning(f"Target backend already contains {stats['memory_count']} memories")
            # In CLI, prompt user for confirmation

        await backend.disconnect()

    async def _check_compatibility(
        self,
        source: BackendConfig,
        target: BackendConfig
    ) -> None:
        """Check if migration between these backends is supported."""
        # All backends use the same GraphBackend interface, so all migrations supported
        # But check for feature parity

        source_backend = await BackendFactory.create_backend(source)
        target_backend = await BackendFactory.create_backend(target)

        # Check feature compatibility
        if source_backend.supports_fulltext_search() and not target_backend.supports_fulltext_search():
            logger.warning("Source supports full-text search but target does not")

        await source_backend.disconnect()
        await target_backend.disconnect()

    async def _export_from_source(
        self,
        config: BackendConfig,
        options: MigrationOptions
    ) -> Path:
        """Export data from source backend to temporary file."""
        backend = await BackendFactory.create_backend(config)
        db = MemoryDatabase(backend)

        # Create temp export file
        temp_dir = Path(tempfile.gettempdir()) / "memorygraph_migration"
        temp_dir.mkdir(exist_ok=True)

        export_path = temp_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Use universal export (works for all backends now!)
        await export_to_json(db, str(export_path))

        await backend.disconnect()
        return export_path

    async def _validate_export(self, export_path: Path) -> ValidationResult:
        """Validate exported data integrity."""
        validator = BackupValidator()
        return await validator.validate(str(export_path), deep=True)

    async def _import_to_target(
        self,
        config: BackendConfig,
        export_path: Path,
        options: MigrationOptions
    ) -> ImportResult:
        """Import data to target backend."""
        backend = await BackendFactory.create_backend(config)
        db = MemoryDatabase(backend)

        # Initialize schema on target
        await db.initialize_schema()

        # Import with progress reporting
        import_result = await import_from_json(
            db,
            str(export_path),
            skip_duplicates=options.skip_duplicates,
            progress_callback=self._report_progress if options.verbose else None
        )

        await backend.disconnect()
        return import_result

    async def _verify_migration(
        self,
        source_config: BackendConfig,
        target_config: BackendConfig,
        export_path: Path
    ) -> VerificationResult:
        """Verify target backend has same data as source."""
        # Connect to both backends
        source_backend = await BackendFactory.create_backend(source_config)
        target_backend = await BackendFactory.create_backend(target_config)

        source_db = MemoryDatabase(source_backend)
        target_db = MemoryDatabase(target_backend)

        errors = []

        # Check memory counts
        source_count = await source_db.count_memories()
        target_count = await target_db.count_memories()

        if source_count != target_count:
            errors.append(f"Memory count mismatch: source={source_count}, target={target_count}")

        # Check relationship counts
        source_rels = await source_db.count_relationships()
        target_rels = await target_db.count_relationships()

        if source_rels != target_rels:
            errors.append(f"Relationship count mismatch: source={source_rels}, target={target_rels}")

        # Sample check: verify 10 random memories exist in target
        sample_size = min(10, source_count)
        if sample_size > 0:
            source_sample = await source_db.get_random_memories(sample_size)
            for memory in source_sample:
                target_memory = await target_db.get_memory(memory.id)
                if not target_memory:
                    errors.append(f"Memory {memory.id} not found in target")
                elif target_memory.content != memory.content:
                    errors.append(f"Memory {memory.id} content mismatch")

        await source_backend.disconnect()
        await target_backend.disconnect()

        return VerificationResult(
            valid=(len(errors) == 0),
            errors=errors,
            source_count=source_count,
            target_count=target_count
        )

    async def _rollback_target(self, config: BackendConfig) -> None:
        """Rollback target backend to pre-migration state."""
        logger.info("Rolling back target backend...")

        backend = await BackendFactory.create_backend(config)
        db = MemoryDatabase(backend)

        # Delete all memories (cascades to relationships)
        await db.clear_all_data()

        await backend.disconnect()

    def _report_progress(self, current: int, total: int, message: str) -> None:
        """Report migration progress to user."""
        percent = (current / total * 100) if total > 0 else 0
        print(f"[{percent:3.0f}%] {message} ({current}/{total})")
```

### 5. CLI Integration

Add migration subcommand to `src/memorygraph/cli.py`:

```python
# Migration command
migrate_parser = subparsers.add_parser("migrate", help="Migrate memories between backends")
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
    choices=["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"],
    required=True,
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
    help="Skip memories that already exist in target"
)
migrate_parser.add_argument(
    "--no-verify",
    action="store_true",
    help="Skip post-migration verification (faster but less safe)"
)


async def handle_migrate(args: argparse.Namespace) -> None:
    """Handle migrate command."""
    from .migration.manager import MigrationManager, MigrationOptions
    from .backends.factory import BackendConfig

    print(f"\n🔄 Migrating memories: {args.source_backend or 'current'} → {args.target_backend}")

    # Build source config
    source_config = BackendConfig.from_env() if not args.source_backend else BackendConfig(
        backend_type=args.source_backend,
        path=args.from_path,
        uri=args.from_uri
    )

    # Build target config
    target_config = BackendConfig(
        backend_type=args.target_backend,
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
        else:
            print("\n✅ Migration completed successfully!")
            print(f"   Migrated: {result.import_result['imported_memories']} memories")
            print(f"   Migrated: {result.import_result['imported_relationships']} relationships")
            if result.import_result['skipped_memories'] > 0:
                print(f"   Skipped: {result.import_result['skipped_memories']} duplicates")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
```

### 6. MCP Tools

Add migration tools to MCP server (extended profile):

```python
{
    "name": "migrate_database",
    "description": "Migrate memories from one backend to another (e.g., SQLite to FalkorDB)",
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
                "description": "Target backend configuration (path, URI, credentials)"
            },
            "dry_run": {
                "type": "boolean",
                "default": False,
                "description": "Validate without making changes"
            },
            "skip_duplicates": {
                "type": "boolean",
                "default": True,
                "description": "Skip existing memories in target"
            }
        },
        "required": ["target_backend"]
    }
}
```

### 7. Data Models

```python
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
        """Create config from environment variables."""
        return cls(
            backend_type=Config.BACKEND,
            path=Config.SQLITE_PATH,
            uri=Config.NEO4J_URI or Config.MEMGRAPH_URI,
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


@dataclass
class MigrationResult:
    """Result of migration operation."""
    success: bool
    dry_run: bool = False
    source_stats: Optional[Dict[str, Any]] = None
    target_stats: Optional[Dict[str, Any]] = None
    import_result: Optional[Dict[str, int]] = None
    verification_result: Optional["VerificationResult"] = None
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Result of post-migration verification."""
    valid: bool
    errors: List[str]
    source_count: int = 0
    target_count: int = 0
    sample_checks: int = 0
```

## Migration Use Cases

### Use Case 1: Local Development → Production

**Scenario**: Developer has 500 memories in local SQLite, wants to deploy to production FalkorDB.

```bash
# 1. Dry-run to validate
memorygraph migrate \
  --from sqlite \
  --from-path ~/.memorygraph/memory.db \
  --to falkordb \
  --to-uri redis://prod.falkordb.com:6379 \
  --dry-run

# 2. Perform migration
memorygraph migrate \
  --from sqlite \
  --from-path ~/.memorygraph/memory.db \
  --to falkordb \
  --to-uri redis://prod.falkordb.com:6379 \
  --verbose
```

**Output**:
```
🔄 Migrating memories: sqlite → falkordb

Phase 1: Validating source backend...
✓ Source backend healthy (500 memories, 892 relationships)

Phase 2: Validating target backend...
✓ Target backend accessible and empty

Phase 3: Exporting from source...
[100%] Exported 500 memories (500/500)
[100%] Exported 892 relationships (892/892)

Phase 4: Importing to target...
[100%] Imported 500 memories (500/500)
[100%] Imported 892 relationships (892/892)

Phase 5: Verifying migration...
✓ Memory count matches (500 = 500)
✓ Relationship count matches (892 = 892)
✓ Sample check passed (10/10 memories verified)

✅ Migration completed successfully!
   Duration: 12.3 seconds
   Migrated: 500 memories, 892 relationships
```

### Use Case 2: Backend Performance Comparison

**Scenario**: Test same dataset on Neo4j vs Memgraph to compare performance.

```bash
# Export current Neo4j data
memorygraph export --format json --output ~/backup.json

# Import to Memgraph
MEMORY_BACKEND=memgraph memorygraph import --format json --input ~/backup.json

# Or use migrate command directly
memorygraph migrate \
  --from neo4j \
  --from-uri bolt://localhost:7687 \
  --to memgraph \
  --to-uri bolt://localhost:7688
```

### Use Case 3: Disaster Recovery

**Scenario**: Production Neo4j crashed, restore from last night's backup to new Memgraph instance.

```bash
# Backup was created with: memorygraph export --format json --output backup.json
# (Works from any backend now!)

# Restore to Memgraph
MEMORY_BACKEND=memgraph \
MEMORY_MEMGRAPH_URI=bolt://new-instance:7687 \
memorygraph import --format json --input backup.json
```

### Use Case 4: Multi-Device Sync

**Scenario**: Work laptop has SQLite with latest changes, sync to home desktop also running SQLite.

```bash
# On laptop: export
memorygraph export --format json --output ~/memories_latest.json

# Transfer file to desktop
scp ~/memories_latest.json desktop:~/

# On desktop: import (merge mode)
memorygraph import --format json --input ~/memories_latest.json --skip-duplicates
```

## Validation Pipeline

### Pre-Flight Checks
1. Source backend connectivity and health
2. Target backend connectivity and writability
3. Feature compatibility assessment
4. Target backend state check (warn if not empty)

### Export Validation
1. JSON format validation (schema compliance)
2. Checksum calculation and storage
3. Memory count verification
4. Relationship endpoint validation (all IDs exist)

### Import Validation
1. Duplicate detection (if skip_duplicates enabled)
2. Referential integrity (relationships → memories)
3. Type validation (MemoryType, RelationshipType enums)
4. Pydantic model validation (deep check)

### Post-Migration Verification
1. Count comparison (source vs target)
2. Random sampling (10 memories content verification)
3. Relationship preservation check
4. Optional: Full deep comparison (expensive for large datasets)

## Performance Considerations

### Batch Processing
- Export: 1000 memories per batch
- Import: 1000 memories per batch
- Progress reporting every 100 items

### Memory Management
- Stream export to disk (don't load all into RAM)
- Use pagination for large result sets
- Release connections after each phase

### Optimization Opportunities
- Parallel relationship export (independent of memories)
- Bulk import APIs where available (Neo4j: UNWIND)
- Compression for network transfer
- Connection pooling for multi-threaded operations

### Expected Performance
| Operation | Dataset Size | Duration (Estimated) |
|-----------|--------------|---------------------|
| Export | 1,000 memories | ~3 seconds |
| Export | 10,000 memories | ~30 seconds |
| Import | 1,000 memories | ~5 seconds |
| Import | 10,000 memories | ~50 seconds |
| Full migration | 1,000 memories | ~15 seconds |
| Full migration | 10,000 memories | ~2 minutes |

## Alternatives Considered

### Alternative 1: Keep SQLite-Only Export

**Rejected because:**
- Locks users into SQLite for portable backups
- Forces manual backend-specific backup procedures
- Inconsistent user experience across backends
- Blocks backend switching use cases

### Alternative 2: Backend-Specific Export Formats

Each backend exports in its native format (Neo4j → Cypher, SQLite → .db file).

**Rejected because:**
- No cross-backend compatibility
- Complex migration logic for each backend pair
- User must understand multiple formats
- Harder to validate and verify

### Alternative 3: Real-Time Sync Instead of Migration

Implement real-time replication between backends.

**Rejected because:**
- Much higher complexity
- Not all backends support replication
- Different use case (HA vs migration)
- One-time migrations are sufficient for most users

### Alternative 4: External ETL Tools

Use existing ETL tools (Apache Airflow, etc.) for migrations.

**Rejected because:**
- Adds external dependency
- Requires users to learn another system
- Overhead for simple use case
- Should be native to MemoryGraph

## Implementation Plan

### Phase 1: Universal Export (Week 1)
- [ ] Refactor `export_to_json` to use `MemoryDatabase` interface
- [ ] Remove SQLite-specific query logic
- [ ] Update `export_to_markdown` similarly
- [ ] Test export from all 5 backends
- [ ] Update CLI to remove backend type check
- [ ] Add export format validation

### Phase 2: Migration Manager (Week 2)
- [ ] Create `src/memorygraph/migration/` module
- [ ] Implement `MigrationManager` class
- [ ] Implement `BackendConfig` and data models
- [ ] Add pre-flight validation logic
- [ ] Add post-migration verification
- [ ] Implement rollback capability
- [ ] Add progress reporting

### Phase 3: CLI Integration (Week 2)
- [ ] Add `migrate` subcommand to CLI
- [ ] Implement `handle_migrate` function
- [ ] Add command-line argument parsing
- [ ] Add interactive confirmations
- [ ] Add verbose output mode
- [ ] Write CLI usage documentation

### Phase 4: MCP Tools (Week 3)
- [ ] Add `migrate_database` MCP tool
- [ ] Add `validate_migration` MCP tool
- [ ] Add to extended tool profile
- [ ] Write tool documentation
- [ ] Add integration tests for MCP tools

### Phase 5: Testing & Validation (Week 3)
- [ ] Unit tests for MigrationManager
- [ ] Integration tests for all backend pairs (5x5 = 25 combinations)
- [ ] Performance tests with large datasets
- [ ] Edge case testing (empty db, single memory, etc.)
- [ ] Rollback scenario tests
- [ ] Documentation updates

### Phase 6: Polish & Release (Week 4)
- [ ] User guide for migrations
- [ ] Migration troubleshooting doc
- [ ] Video tutorial
- [ ] Update CHANGELOG
- [ ] Release notes
- [ ] Announcement blog post

## Success Metrics

1. **Feature Completeness**: Export works from all 5 backends
2. **Migration Success Rate**: 99%+ successful migrations in testing
3. **Data Fidelity**: 100% round-trip preservation (verified via checksums)
4. **Performance**: <2 minutes for 10k memories
5. **User Adoption**: 30% of users try backend migration within 3 months
6. **Documentation**: <5 support requests about migrations per month

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Data loss during migration | Critical | Very Low | Multi-stage validation, dry-run mode, rollback capability |
| Performance issues with large datasets | High | Medium | Batch processing, streaming, progress reporting |
| Backend-specific edge cases | Medium | Medium | Comprehensive testing matrix, graceful error handling |
| Incomplete migration (partial data) | High | Low | Atomic operations, verification step, error detection |
| User confusion about configuration | Medium | Medium | Clear CLI help, examples, interactive prompts |

## Future Enhancements

1. **Incremental Migration**: Only migrate changed memories since last migration
2. **Bi-Directional Sync**: Keep two backends in sync continuously
3. **Migration Scheduling**: Automated periodic migrations
4. **Cloud Storage Transit**: Migrate via S3/GCS instead of temp files
5. **Parallel Import**: Multi-threaded import for faster migrations
6. **Migration Analytics**: Track migration patterns and performance
7. **Schema Evolution**: Handle migrations across MemoryGraph version changes
8. **Selective Migration**: Migrate only specific memory types or tags

## References

- **ADR 013**: Database Backup and Export Architecture (backup workflows)
- **Existing Implementation**: `/src/memorygraph/utils/export_import.py`
- **Backend Interface**: `/src/memorygraph/backends/base.py`
- **Backend Factory**: `/src/memorygraph/backends/factory.py`
- **CLI**: `/src/memorygraph/cli.py`

## Conclusion

Universal export and backend migration are essential features for MemoryGraph's multi-backend architecture. By leveraging the existing `GraphBackend` interface, we can:

1. **Enable export from any backend** with minimal code changes
2. **Provide seamless migration** between all backend pairs
3. **Maintain data integrity** through multi-stage validation
4. **Deliver excellent UX** with progress reporting and dry-run mode
5. **Support real-world workflows** like development → production, disaster recovery, and backend evaluation

This design maintains MemoryGraph's zero-config philosophy while unlocking powerful backend portability that users need as they scale.

## Appendix A: File Structure

```
src/memorygraph/
├── migration/
│   ├── __init__.py
│   ├── manager.py              # MigrationManager
│   ├── validator.py            # Pre/post validation
│   ├── models.py               # BackendConfig, MigrationResult, etc.
│   └── progress.py             # Progress reporting utilities
├── utils/
│   └── export_import.py        # Updated to use MemoryDatabase interface
├── tools/
│   └── migration_tools.py      # MCP tool definitions
├── cli.py                      # Add migrate subcommand
└── backends/
    ├── base.py                 # GraphBackend interface (unchanged)
    └── factory.py              # BackendFactory (unchanged)

tests/
├── migration/
│   ├── test_manager.py
│   ├── test_validator.py
│   └── test_backend_pairs.py   # Test all 25 backend combinations
└── integration/
    └── test_migration_e2e.py

docs/
└── guides/
    └── MIGRATION_GUIDE.md
```

## Appendix B: Example Migration Scenarios

### Scenario: SQLite → FalkorDB (Local → Production)

```bash
# Before migration - using SQLite
export MEMORY_BACKEND=sqlite
export MEMORY_SQLITE_PATH=~/.memorygraph/dev.db

memorygraph health
# ✓ 500 memories in SQLite

# Migrate to FalkorDB
memorygraph migrate \
  --to falkordb \
  --to-uri redis://prod.example.com:6379 \
  --verbose

# Switch to FalkorDB
export MEMORY_BACKEND=falkordb
export MEMORY_FALKORDB_URI=redis://prod.example.com:6379

memorygraph health
# ✓ 500 memories in FalkorDB
```

### Scenario: Neo4j → Neo4j (Cross-Region)

```bash
# Migrate from US to EU region
memorygraph migrate \
  --from neo4j \
  --from-uri bolt://us-neo4j.example.com:7687 \
  --to neo4j \
  --to-uri bolt://eu-neo4j.example.com:7687 \
  --verbose
```

### Scenario: Testing Multiple Backends

```python
# Python script to test performance across backends
import subprocess
import time

backends = ["sqlite", "neo4j", "memgraph", "falkordb"]
results = {}

# Start with SQLite (populated with test data)
for target_backend in backends[1:]:  # Skip SQLite (source)
    start = time.time()

    subprocess.run([
        "memorygraph", "migrate",
        "--from", "sqlite",
        "--to", target_backend,
        "--to-uri", f"{target_backend}://localhost:7687"
    ])

    duration = time.time() - start
    results[target_backend] = duration

    # Run performance benchmarks on target backend
    # ... (omitted for brevity)

    # Clean up target backend
    subprocess.run(["memorygraph", "clear", "--backend", target_backend])

print("Migration Performance:")
for backend, duration in results.items():
    print(f"  SQLite → {backend}: {duration:.2f}s")
```
