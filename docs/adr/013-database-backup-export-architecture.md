# ADR 010: Database Backup and Export Architecture

## Status
Proposed

## Date
2025-12-03

## Context

MemoryGraph currently has basic JSON and Markdown export functionality (`export_import.py`), but lacks a comprehensive backup/restore strategy for production use. Users need:

1. **Reliable Backups**: Protect against data loss from crashes, corruption, or user error
2. **Data Portability**: Move memories between environments (dev → staging → production)
3. **Version Migration**: Upgrade between MemoryGraph versions without data loss
4. **Multi-Backend Support**: Backup works across all 5 backends (SQLite, FalkorDBLite, FalkorDB, Neo4j, Memgraph)
5. **Large Dataset Handling**: Handle thousands of memories without memory exhaustion

### Current Implementation

The existing `export_import.py` provides:
- JSON export/import (all memories + relationships)
- Markdown export (individual .md files per memory)
- Basic duplicate handling
- Round-trip preservation

**Limitations:**
- No compression
- No versioning or metadata
- SQLite-specific implementation
- Loads all data into memory at once
- No CLI interface for backups
- No scheduled backup capability
- No backup verification/validation

## Decision Drivers

1. **Zero-Config Philosophy**: Backups should work out-of-the-box with sensible defaults
2. **Multi-Backend Support**: Must work identically across all 5 backends
3. **Production Ready**: Handle 10k+ memories, automatic recovery, clear error messages
4. **MCP Integration**: Expose backup/restore as MCP tools for agent automation
5. **Developer Experience**: Simple CLI commands, clear documentation
6. **Data Integrity**: Verify backups, detect corruption, ensure consistency

## Design Overview

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Tools Layer                          │
│  - backup_database()    - restore_database()                │
│  - list_backups()       - verify_backup()                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                       │
│  memorygraph backup create [--incremental] [--compress]     │
│  memorygraph backup restore <backup-id>                     │
│  memorygraph backup list                                    │
│  memorygraph backup verify <backup-id>                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backup Manager (Core Logic)                │
│  - Format negotiation   - Streaming export                  │
│  - Compression          - Integrity checking                │
│  - Metadata tracking    - Version compatibility             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Backend Strategy Layer                         │
│  SQLiteBackupStrategy | Neo4jBackupStrategy                 │
│  FalkorDBBackupStrategy | MemgraphBackupStrategy            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                            │
│  Local filesystem | S3 | Custom storage adapter            │
└─────────────────────────────────────────────────────────────┘
```

## Proposed Solution

### 1. Backup Format Specification

#### Primary Format: Enhanced JSON v2.0

```json
{
  "format_version": "2.0",
  "memorygraph_version": "0.9.4",
  "backend_type": "sqlite",
  "created_at": "2025-12-03T10:30:00Z",
  "backup_type": "full",
  "compression": "gzip",
  "integrity": {
    "checksum": "sha256:abc123...",
    "memory_count": 1543,
    "relationship_count": 2891
  },
  "metadata": {
    "source_db": "/path/to/memory.db",
    "include_context": true,
    "include_embeddings": false
  },
  "data": {
    "memories": [...],
    "relationships": [...]
  }
}
```

**Rationale:**
- JSON is human-readable, debuggable, and universally supported
- Version field enables migration logic
- Checksum prevents silent corruption
- Metadata enables smart restore decisions

#### Secondary Format: SQLite Archive

For SQLite backend only, support native `.db` file backup:
- Direct file copy (fastest)
- SQLite's built-in VACUUM INTO (compact copy)
- Write-Ahead Log (WAL) checkpoint before copy

**Use when:**
- Source and target both use SQLite backend
- Maximum speed required
- Binary compatibility acceptable

#### Tertiary Format: Cypher Script

For Neo4j/Memgraph/FalkorDB backends:
- Export as executable Cypher statements
- Useful for manual inspection/editing
- Compatible with native database tools

```cypher
// MemoryGraph Export v2.0
CREATE (m1:Memory {
  id: "abc-123",
  type: "solution",
  title: "Redis Timeout Fix",
  ...
});
CREATE (m2:Memory {...});
CREATE (m1)-[r:SOLVES {strength: 0.9}]->(m2);
```

### 2. Backup Strategies

#### Full Backup
```bash
memorygraph backup create --type full --output ~/.memorygraph/backups/
```

**Process:**
1. Create backup metadata file
2. Stream all memories (paginated, 1000 per batch)
3. Stream all relationships
4. Calculate checksum
5. Compress (optional, gzip by default)
6. Write manifest

**Output:**
```
~/.memorygraph/backups/memorygraph-backup-20251203-103045-full.json.gz
~/.memorygraph/backups/memorygraph-backup-20251203-103045-full.manifest
```

### 3. API Design

#### MCP Tool: `backup_database`

```python
{
  "name": "backup_database",
  "description": "Create a backup of the memory database",
  "parameters": {
    "type": "object",
    "properties": {
      "backup_type": {
        "type": "string",
        "enum": ["full", "incremental"],
        "default": "full",
        "description": "Full backup or incremental since last backup"
      },
      "output_path": {
        "type": "string",
        "description": "Directory to store backup (defaults to ~/.memorygraph/backups)"
      },
      "compress": {
        "type": "boolean",
        "default": true,
        "description": "Compress backup with gzip"
      },
      "include_context": {
        "type": "boolean",
        "default": true,
        "description": "Include full MemoryContext data"
      }
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "backup_id": "memorygraph-backup-20251203-103045-full",
  "backup_path": "/home/user/.memorygraph/backups/memorygraph-backup-20251203-103045-full.json.gz",
  "statistics": {
    "memories_backed_up": 1543,
    "relationships_backed_up": 2891,
    "backup_size_bytes": 2458932,
    "compressed": true,
    "duration_seconds": 4.2
  }
}
```

#### MCP Tool: `restore_database`

```python
{
  "name": "restore_database",
  "parameters": {
    "backup_path": {
      "type": "string",
      "description": "Path to backup file or backup ID"
    },
    "mode": {
      "type": "string",
      "enum": ["replace", "merge", "dry-run"],
      "default": "merge",
      "description": "replace: Delete existing data; merge: Keep existing, add new; dry-run: Validate only"
    },
    "skip_validation": {
      "type": "boolean",
      "default": false,
      "description": "Skip checksum verification (faster but unsafe)"
    }
  }
}
```

#### MCP Tool: `list_backups`

```python
{
  "name": "list_backups",
  "parameters": {
    "backup_dir": {
      "type": "string",
      "description": "Directory to search for backups (defaults to ~/.memorygraph/backups)"
    },
    "limit": {
      "type": "integer",
      "default": 20,
      "description": "Maximum number of backups to return"
    }
  }
}
```

**Response:**
```json
{
  "backups": [
    {
      "id": "memorygraph-backup-20251203-103045-full",
      "path": "/home/user/.memorygraph/backups/...",
      "type": "full",
      "created_at": "2025-12-03T10:30:45Z",
      "size_bytes": 2458932,
      "memories": 1543,
      "relationships": 2891,
      "memorygraph_version": "0.9.4",
      "backend": "sqlite",
      "valid": true
    }
  ]
}
```

### 4. Backend-Specific Strategies

#### SQLite Backend

**Full Backup:**
```python
class SQLiteBackupStrategy:
    async def backup_full(self, output_path: str, compress: bool = True):
        # Option 1: Direct file copy (fastest)
        if not db.is_active():
            shutil.copy2(db_path, output_path)

        # Option 2: SQLite VACUUM INTO (compact)
        await db.execute("VACUUM INTO ?", (output_path,))

        # Option 3: JSON export (portable)
        await export_to_json(db, output_path)
```

**Incremental:**
- Query `WHERE updated_at > ?` using timestamp index
- Export only changed memories + affected relationships

#### Neo4j Backend

**Full Backup:**
```cypher
// Export all nodes and relationships
CALL apoc.export.json.all(output_path, {
  useTypes: true,
  storeNodeIds: false
})
```

**Incremental:**
```cypher
// Export changed memories
MATCH (m:Memory)
WHERE m.updated_at > $since_date
RETURN m

// Export affected relationships
MATCH (m:Memory)-[r]-(other:Memory)
WHERE m.updated_at > $since_date OR other.updated_at > $since_date
RETURN r
```

#### FalkorDB/Memgraph Backends

Similar to Neo4j, using Cypher queries:
```cypher
// FalkorDB: Use GRAPH.QUERY with JSON serialization
// Memgraph: Use CALL export.json()
```

### 5. CLI Implementation

Add to `src/memorygraph/cli.py`:

```python
@click.group(name="backup")
def backup_cli():
    """Backup and restore commands."""
    pass

@backup_cli.command(name="create")
@click.option("--type", type=click.Choice(["full", "incremental"]), default="full")
@click.option("--output", type=click.Path(), default=None)
@click.option("--compress/--no-compress", default=True)
@click.option("--format", type=click.Choice(["json", "cypher", "sqlite"]), default="json")
def backup_create(type, output, compress, format):
    """Create a new backup."""
    pass

@backup_cli.command(name="restore")
@click.argument("backup_path")
@click.option("--mode", type=click.Choice(["replace", "merge", "dry-run"]), default="merge")
def backup_restore(backup_path, mode):
    """Restore from a backup."""
    pass

@backup_cli.command(name="list")
@click.option("--dir", type=click.Path(), default=None)
def backup_list(dir):
    """List available backups."""
    pass

@backup_cli.command(name="verify")
@click.argument("backup_path")
@click.option("--deep/--shallow", default=False)
def backup_verify(backup_path, deep):
    """Verify backup integrity."""
    pass

```

### 6. Data Integrity & Validation

#### Checksum Calculation
```python
import hashlib

def calculate_backup_checksum(backup_data: dict) -> str:
    """Calculate SHA256 checksum of backup data."""
    # Canonical JSON (sorted keys, no whitespace)
    canonical = json.dumps(backup_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()
```

#### Validation Steps
1. **Format Validation**: Verify JSON structure matches schema
2. **Version Compatibility**: Check `memorygraph_version` compatibility
3. **Checksum Verification**: Recompute and compare checksums
4. **Referential Integrity**: Verify all relationship endpoints exist
5. **Data Type Validation**: Validate memory types, relationship types
6. **Optional Deep Check**: Validate all Memory/Relationship objects via Pydantic

```python
class BackupValidator:
    def validate(self, backup_path: str, deep: bool = False) -> ValidationResult:
        # 1. Load and parse JSON
        with open(backup_path) as f:
            data = json.load(f)

        # 2. Check format version
        if data["format_version"] != "2.0":
            raise ValidationError(f"Unsupported format: {data['format_version']}")

        # 3. Verify checksum
        stored_checksum = data["integrity"]["checksum"]
        computed_checksum = calculate_backup_checksum(data["data"])
        if stored_checksum != computed_checksum:
            raise ValidationError("Checksum mismatch - backup may be corrupted")

        # 4. Validate counts
        actual_memories = len(data["data"]["memories"])
        expected_memories = data["integrity"]["memory_count"]
        if actual_memories != expected_memories:
            raise ValidationError(f"Memory count mismatch: {actual_memories} != {expected_memories}")

        # 5. Check referential integrity
        memory_ids = {m["id"] for m in data["data"]["memories"]}
        for rel in data["data"]["relationships"]:
            if rel["from_memory_id"] not in memory_ids:
                raise ValidationError(f"Invalid relationship: from_id {rel['from_memory_id']} not found")
            if rel["to_memory_id"] not in memory_ids:
                raise ValidationError(f"Invalid relationship: to_id {rel['to_memory_id']} not found")

        # 6. Deep validation (optional)
        if deep:
            for mem_data in data["data"]["memories"]:
                Memory(**mem_data)  # Pydantic validation

        return ValidationResult(valid=True, errors=[])
```

### 7. Large Dataset Handling

#### Streaming Export (Memory-Efficient)

```python
class StreamingBackupWriter:
    """Write backup in streaming fashion to avoid loading all data into memory."""

    def __init__(self, output_path: str, compress: bool = True):
        self.output_path = output_path
        self.compress = compress
        self.memory_count = 0
        self.relationship_count = 0

    async def write_backup(self, db: MemoryDatabase):
        # Open file (with optional compression)
        file_obj = gzip.open(self.output_path, 'wt') if self.compress else open(self.output_path, 'w')

        try:
            # Write header
            file_obj.write('{\n')
            file_obj.write(f'  "format_version": "2.0",\n')
            file_obj.write(f'  "created_at": "{datetime.now(timezone.utc).isoformat()}",\n')
            file_obj.write('  "data": {\n')
            file_obj.write('    "memories": [\n')

            # Stream memories in batches
            offset = 0
            batch_size = 1000
            first_batch = True

            while True:
                query = SearchQuery(limit=batch_size, offset=offset)
                result = await db.search_memories(query)

                if not result.results:
                    break

                for memory in result.results:
                    if not first_batch:
                        file_obj.write(',\n')
                    file_obj.write('      ' + json.dumps(memory.dict(), default=str))
                    first_batch = False
                    self.memory_count += 1

                offset += batch_size

                if not result.has_more:
                    break

            file_obj.write('\n    ],\n')
            file_obj.write('    "relationships": [\n')

            # Stream relationships in batches
            # ... similar pagination logic ...

            file_obj.write('\n    ]\n')
            file_obj.write('  }\n')
            file_obj.write('}\n')

        finally:
            file_obj.close()
```

### 8. Migration & Version Compatibility

#### Version Detection
```python
def detect_backup_version(backup_path: str) -> str:
    """Detect backup format version."""
    with open(backup_path) as f:
        data = json.load(f)
    return data.get("format_version", "1.0")  # Default to 1.0 for legacy
```

#### Migration Pipeline
```python
class BackupMigrator:
    """Migrate backups between format versions."""

    async def migrate(self, backup_path: str, target_version: str) -> str:
        source_version = detect_backup_version(backup_path)

        if source_version == target_version:
            return backup_path

        # Apply migration chain
        migrated_path = backup_path
        for migrator in self.get_migration_path(source_version, target_version):
            migrated_path = await migrator.migrate(migrated_path)

        return migrated_path

    def get_migration_path(self, from_version: str, to_version: str) -> List[Migrator]:
        """Get chain of migrators to apply."""
        # e.g., 1.0 -> 1.1 -> 2.0
        return [
            V1_0_to_V1_1_Migrator(),
            V1_1_to_V2_0_Migrator()
        ]
```

**Migration Example: v1.0 → v2.0**
```python
class V1_0_to_V2_0_Migrator:
    async def migrate(self, backup_path: str) -> str:
        # Load v1.0 backup
        with open(backup_path) as f:
            v1_data = json.load(f)

        # Transform to v2.0 format
        v2_data = {
            "format_version": "2.0",
            "memorygraph_version": "0.9.4",
            "created_at": v1_data.get("export_date", datetime.now().isoformat()),
            "backup_type": "full",
            "compression": "none",
            "integrity": {
                "checksum": calculate_backup_checksum(v1_data),
                "memory_count": len(v1_data["memories"]),
                "relationship_count": len(v1_data["relationships"])
            },
            "data": {
                "memories": v1_data["memories"],
                "relationships": v1_data["relationships"]
            }
        }

        # Write v2.0 backup
        output_path = backup_path.replace(".json", ".v2.json")
        with open(output_path, 'w') as f:
            json.dump(v2_data, f, indent=2)

        return output_path
```

### 9. Error Handling & Recovery

#### Backup Failure Scenarios

**Partial Backup (disk full):**
```python
try:
    await backup_manager.create_backup(output_path)
except IOError as e:
    # Clean up partial backup
    if os.path.exists(output_path):
        os.unlink(output_path)
    raise BackupError(f"Backup failed: {e}")
```

**Corrupted Backup:**
```python
try:
    validation_result = validator.validate(backup_path)
except ValidationError as e:
    logger.error(f"Backup validation failed: {e}")
    # Try repair if possible
    if repair_possible(e):
        repaired_path = repair_backup(backup_path)
        return restore_from_backup(repaired_path)
    raise
```

**Restore Failure (incompatible version):**
```python
try:
    await restore_manager.restore(backup_path)
except VersionError as e:
    # Attempt migration
    migrated_path = await migrator.migrate(backup_path, current_version)
    await restore_manager.restore(migrated_path)
```

### 10. Configuration & Defaults

Environment variables:
```bash
# Backup location
MEMORY_BACKUP_PATH=~/.memorygraph/backups

# Automatic backups
MEMORY_AUTO_BACKUP=daily          # none, hourly, daily, weekly
MEMORY_BACKUP_RETENTION=7         # Days to keep backups

# Backup options
MEMORY_BACKUP_COMPRESS=true       # gzip compression
MEMORY_BACKUP_FORMAT=json         # json, cypher, sqlite
MEMORY_BACKUP_INCLUDE_CONTEXT=true

# Incremental backup
MEMORY_BACKUP_INCREMENTAL=false   # Enable incremental backups
```

Config file (`~/.memorygraph/config.yaml`):
```yaml
backups:
  path: ~/.memorygraph/backups
  auto_backup:
    enabled: true
    frequency: daily
    retention_days: 7
    compress: true
  defaults:
    format: json
    include_context: true
    verify_after_backup: true
```

## Implementation Plan

### Phase 1: Core Backup Infrastructure (Week 1)
- [ ] Create `src/memorygraph/backup/` module
- [ ] Implement `BackupManager` class
- [ ] Implement JSON v2.0 format with metadata
- [ ] Add checksum calculation and verification
- [ ] Implement streaming export for large datasets
- [ ] Add `BackupValidator` with integrity checks
- [ ] Write comprehensive unit tests

### Phase 2: CLI Interface (Week 1)
- [ ] Add `backup` command group to CLI
- [ ] Implement `backup create` command
- [ ] Implement `backup restore` command
- [ ] Implement `backup list` command
- [ ] Implement `backup verify` command
- [ ] Add CLI tests

### Phase 3: MCP Integration (Week 2)
- [ ] Create `backup_tools.py` with MCP tool definitions
- [ ] Implement `backup_database` tool
- [ ] Implement `restore_database` tool
- [ ] Implement `list_backups` tool
- [ ] Implement `verify_backup` tool
- [ ] Add to appropriate tool profiles (extended mode)
- [ ] Add integration tests

### Phase 4: Backend Strategies (Week 2)
- [ ] Implement `SQLiteBackupStrategy`
- [ ] Implement `Neo4jBackupStrategy`
- [ ] Implement `FalkorDBBackupStrategy`
- [ ] Implement `MemgraphBackupStrategy`
- [ ] Add backend-specific optimizations
- [ ] Test across all backends

### Phase 5: Advanced Features (Week 3)
- [ ] Implement incremental backup
- [ ] Add compression support (gzip, zstd)
- [ ] Implement scheduled backups
- [ ] Add backup rotation/retention
- [ ] Implement migration system
- [ ] Add repair utilities for corrupted backups

### Phase 6: Documentation & Polish (Week 3)
- [ ] Write user documentation
- [ ] Add backup examples to README
- [ ] Create backup troubleshooting guide
- [ ] Add performance benchmarks
- [ ] Update CHANGELOG
- [ ] Create video tutorial

## File Structure

```
src/memorygraph/
├── backup/
│   ├── __init__.py
│   ├── manager.py              # BackupManager, RestoreManager
│   ├── formats.py              # Format handlers (JSON, Cypher, SQLite)
│   ├── validator.py            # BackupValidator
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py            # BackupStrategy abstract class
│   │   ├── sqlite_strategy.py
│   │   ├── neo4j_strategy.py
│   │   ├── falkordb_strategy.py
│   │   └── memgraph_strategy.py
│   ├── streaming.py           # StreamingBackupWriter
│   ├── migration.py           # Version migration
│   ├── scheduler.py           # Automatic backup scheduling
│   └── models.py              # BackupMetadata, ValidationResult
├── tools/
│   └── backup_tools.py        # MCP tool definitions
├── cli.py                     # Add backup commands
└── config.py                  # Add backup config options

tests/
├── backup/
│   ├── test_manager.py
│   ├── test_formats.py
│   ├── test_validator.py
│   ├── test_strategies.py
│   ├── test_streaming.py
│   ├── test_migration.py
│   └── test_cli.py
└── integration/
    └── test_backup_e2e.py

docs/
├── guides/
│   ├── BACKUP_GUIDE.md
│   └── BACKUP_TROUBLESHOOTING.md
└── examples/
    └── backup_examples.sh
```

## Testing Strategy

### Unit Tests
- Format serialization/deserialization
- Checksum calculation
- Validation logic
- Migration transformations
- CLI argument parsing

### Integration Tests
- Round-trip backup/restore
- Cross-backend compatibility
- Large dataset handling (10k+ memories)
- Incremental backup chains
- Corrupted backup recovery

### Performance Tests
- Backup speed (target: 1000 memories/sec)
- Restore speed
- Memory usage during streaming
- Compression ratios

### Edge Cases
- Empty database
- Single memory
- No relationships
- Circular relationships (if allowed)
- Unicode/special characters
- Very large memories (1MB+ content)

## Alternatives Considered

### Alternative 1: Use Native Database Backups Only

Use each database's native backup tools:
- SQLite: `.backup` command
- Neo4j: `neo4j-admin backup`
- FalkorDB: Redis RDB snapshots

**Rejected because:**
- No cross-backend portability
- Requires users to learn multiple tools
- No consistent metadata format
- Harder to migrate between backends

### Alternative 2: Git-Based Versioning

Store memories as individual JSON files in a Git repository.

**Rejected because:**
- Poor performance for large datasets
- Relationship management complex
- Git overhead for binary data
- Not suitable for production databases

### Alternative 3: Cloud-Native Only (S3, etc.)

Only support cloud storage for backups.

**Rejected because:**
- Breaks zero-config philosophy
- Privacy concerns
- Network dependency
- Local backups are essential baseline

### Alternative 4: Real-Time Replication

Focus on database replication instead of backups.

**Rejected because:**
- Complexity overhead
- Not all backends support replication
- Backups still needed for point-in-time recovery
- Different use case (HA vs. backup)

## Success Metrics

1. **Reliability**: 99.9% backup success rate in production
2. **Performance**: <5 seconds for 1000 memories (uncompressed)
3. **Portability**: Round-trip fidelity across all backends
4. **Usability**: Zero-config works for 90% of users
5. **Adoption**: 50% of users enable automatic backups
6. **Recovery**: <2 minute mean time to restore

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Backup corruption | High | Low | Checksums, validation, redundant backups |
| Performance degradation | Medium | Medium | Streaming, compression, incremental |
| Storage exhaustion | Medium | Medium | Retention policies, compression |
| Version incompatibility | High | Low | Migration system, version detection |
| Data loss during restore | High | Low | Dry-run mode, merge mode, backups before restore |

## Future Enhancements

1. **Cloud Storage Integration**: S3, GCS, Azure Blob storage adapters
2. **Encrypted Backups**: AES-256 encryption for sensitive data
3. **Differential Backups**: More efficient than incremental
4. **Parallel Export/Import**: Multi-threaded for large datasets
5. **Backup Catalogs**: Searchable index of all backups
6. **Webhook Notifications**: Alert on backup completion/failure
7. **Backup Analytics**: Track backup sizes, durations, trends
8. **Cross-Instance Sync**: Sync memories between multiple instances

## References

- Existing implementation: `/src/memorygraph/utils/export_import.py`
- Tests: `/tests/test_export_import.py`
- ADR 001: Neo4j Over PostgreSQL (relationship storage rationale)
- SQLite Backup API: https://www.sqlite.org/backup.html
- Neo4j Backup: https://neo4j.com/docs/operations-manual/current/backup-restore/

## Conclusion

This design provides a comprehensive, production-ready backup solution that:
- Maintains MemoryGraph's zero-config philosophy
- Works consistently across all 5 backends
- Handles large datasets efficiently
- Enables data portability and migration
- Integrates naturally with MCP and CLI workflows

The phased implementation allows incremental delivery of value while maintaining backward compatibility with existing export functionality.
