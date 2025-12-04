# Migration Quick Start Guide

**Version**: 0.10.0
**Feature**: Backend-to-Backend Memory Migration

---

## Overview

MemoryGraph now supports migrating memories between different backend types with full validation, verification, and rollback capabilities.

**Supported Backends**:
- SQLite (local file database)
- Neo4j (graph database)
- Memgraph (in-memory graph database)
- FalkorDB (Redis-based graph database)
- FalkorDBLite (SQLite-based graph database)

---

## Quick Start

### 1. Validate Before Migrating (Recommended)

Always start with a dry-run to ensure the migration will succeed:

```bash
memorygraph migrate \
  --to falkordb \
  --to-uri redis://prod.example.com:6379 \
  --dry-run
```

**Output**:
```
🔄 Migrating memories: current → falkordb
✅ Dry-run successful - migration would proceed safely
   Source: 150 memories
```

### 2. Perform the Migration

Once validation succeeds, run the actual migration:

```bash
memorygraph migrate \
  --to falkordb \
  --to-uri redis://prod.example.com:6379 \
  --verbose
```

**Output**:
```
🔄 Migrating memories: sqlite → falkordb
Phase 1: Pre-flight validation
Phase 2: Exporting from source
[100%] Exported 150 memories (150/150)
Phase 3: Validating export
Phase 4: Importing to target
[100%] Imported 150 memories (150/150)
Phase 5: Verifying migration
   Memory count - Source: 150, Target: 150
   Sample verification: 10/10 passed
Phase 6: Cleanup

✅ Migration completed successfully!
   Migrated: 150 memories
   Migrated: 342 relationships
   Duration: 3.2 seconds
```

---

## CLI Usage

### Command Structure

```bash
memorygraph migrate [OPTIONS]
```

### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--to <backend>` | Target backend type (required) | `--to falkordb` |
| `--to-uri <uri>` | Target database URI | `--to-uri redis://localhost:6379` |
| `--to-path <path>` | Target database path (SQLite/FalkorDBLite) | `--to-path /data/prod.db` |
| `--dry-run` | Validate without changes | `--dry-run` |
| `--verbose` | Show detailed progress | `--verbose` |
| `--no-verify` | Skip verification (faster but risky) | `--no-verify` |
| `--from <backend>` | Source backend (defaults to current) | `--from sqlite` |

### Examples

#### SQLite to FalkorDB (Development to Production)

```bash
# Current backend is SQLite (MEMORY_BACKEND=sqlite)
memorygraph migrate \
  --to falkordb \
  --to-uri redis://prod.example.com:6379 \
  --verbose
```

#### Explicit Source and Target

```bash
memorygraph migrate \
  --from sqlite \
  --from-path /Users/me/.memorygraph/memory.db \
  --to neo4j \
  --to-uri bolt://localhost:7687 \
  --to-username neo4j \
  --to-password password
```

#### Local Testing

```bash
memorygraph migrate \
  --to sqlite \
  --to-path /tmp/test-migration.db \
  --dry-run
```

---

## MCP Tools Usage

For use within Claude Desktop or other MCP clients:

### migrate_database

Perform a migration from the current backend to a target backend.

**Parameters**:
```json
{
  "target_backend": "falkordb",
  "target_config": {
    "uri": "redis://prod.example.com:6379"
  },
  "dry_run": false,
  "verify": true
}
```

**Response**:
```json
{
  "success": true,
  "dry_run": false,
  "source_backend": "sqlite",
  "target_backend": "falkordb",
  "imported_memories": 150,
  "imported_relationships": 342,
  "duration_seconds": 3.2,
  "verification": {
    "valid": true,
    "source_count": 150,
    "target_count": 150,
    "sample_checks": 10,
    "sample_passed": 10
  }
}
```

### validate_migration

Dry-run validation without making changes.

**Parameters**:
```json
{
  "target_backend": "neo4j",
  "target_config": {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "password"
  }
}
```

**Response**:
```json
{
  "success": true,
  "dry_run": true,
  "source_backend": "sqlite",
  "target_backend": "neo4j",
  "imported_memories": 0
}
```

---

## Configuration

### Backend-Specific Configuration

#### SQLite / FalkorDBLite
```bash
--to sqlite --to-path /path/to/database.db
```

#### Neo4j
```bash
--to neo4j \
  --to-uri bolt://localhost:7687 \
  --to-username neo4j \
  --to-password password
```

#### Memgraph
```bash
--to memgraph \
  --to-uri bolt://localhost:7687
```

#### FalkorDB
```bash
--to falkordb \
  --to-uri redis://localhost:6379
```

### Environment Variables

The source backend defaults to your current `MEMORY_BACKEND` setting:

```bash
# Check current backend
echo $MEMORY_BACKEND

# Set source backend
export MEMORY_BACKEND=sqlite
export MEMORY_SQLITE_PATH=/path/to/source.db
```

---

## Migration Process

### 6-Phase Pipeline

1. **Pre-flight Validation**
   - Verify source backend is accessible
   - Verify target backend is accessible
   - Check configuration validity
   - Warn if target already has data

2. **Export**
   - Create temporary export file
   - Export all memories with pagination
   - Export all relationships
   - Report progress (verbose mode)

3. **Validation**
   - Verify export file integrity
   - Check required fields
   - Validate data structure
   - Count memories and relationships

4. **Import** (skipped in dry-run)
   - Import memories to target
   - Import relationships to target
   - Skip duplicates (optional)
   - Report progress (verbose mode)

5. **Verification** (optional)
   - Compare memory counts
   - Compare relationship counts
   - Sample 10 random memories
   - Verify content matches

6. **Cleanup**
   - Delete temporary export file
   - Close all connections
   - Report final statistics

### Rollback on Failure

If verification fails, the migration automatically rolls back:

```bash
❌ Migration failed: Verification failed
   - Memory count mismatch: source=150, target=148
   Rolling back target backend...
   Rollback complete
```

---

## Best Practices

### 1. Always Dry-Run First

```bash
# STEP 1: Validate
memorygraph migrate --to <target> --dry-run

# STEP 2: If successful, migrate
memorygraph migrate --to <target>
```

### 2. Use Verification

Verification adds minimal overhead but ensures data integrity:

```bash
memorygraph migrate --to <target> --verify
```

### 3. Enable Verbose Mode

See detailed progress for large migrations:

```bash
memorygraph migrate --to <target> --verbose
```

### 4. Test with Small Datasets First

Before migrating production data:
1. Export a subset of memories
2. Import to test environment
3. Migrate test environment
4. Verify results

### 5. Backup Before Migrating

```bash
# Export current state
memorygraph export --format json --output backup-$(date +%Y%m%d).json

# Perform migration
memorygraph migrate --to <target>
```

---

## Troubleshooting

### "Source backend not accessible"

**Cause**: Source backend configuration is invalid or backend is offline.

**Solution**:
```bash
# Check current backend
memorygraph health

# Verify environment variables
echo $MEMORY_BACKEND
echo $MEMORY_SQLITE_PATH  # For SQLite
echo $MEMORY_NEO4J_URI    # For Neo4j
```

### "Target backend not accessible"

**Cause**: Target backend configuration is invalid or backend is offline.

**Solution**:
```bash
# Test target connection (example for FalkorDB)
redis-cli -h prod.example.com -p 6379 ping

# Test Neo4j connection
bolt://localhost:7687 (check credentials)
```

### "Verification failed: Memory count mismatch"

**Cause**: Import was incomplete or failed silently.

**Solution**:
1. Check target backend logs
2. Try migration again with `--verbose`
3. Check disk space on target
4. Rollback happens automatically

### "Export validation failed: Missing required fields"

**Cause**: Export file is corrupted or incomplete.

**Solution**:
1. Check source backend health
2. Ensure sufficient disk space for export
3. Try export again
4. Check permissions on temp directory

### Migration is Slow

**For large datasets** (>1000 memories):
- Use `--verbose` to monitor progress
- Ensure target backend is not rate-limited
- Check network latency for remote backends
- Consider pagination settings (internal)

---

## Performance Expectations

### Small Datasets (<100 memories)
- Export: <1 second
- Import: <2 seconds
- Verification: <1 second
- **Total**: ~3-5 seconds

### Medium Datasets (100-1000 memories)
- Export: 1-5 seconds
- Import: 2-10 seconds
- Verification: 1-2 seconds
- **Total**: ~5-20 seconds

### Large Datasets (1000-10000 memories)
- Export: 5-30 seconds
- Import: 10-50 seconds
- Verification: 2-5 seconds
- **Total**: ~20-120 seconds

*Performance varies by backend type and network latency.*

---

## Safety Features

### ✅ Dry-Run Mode
Validates migration without making changes.

### ✅ Verification
Compares source and target data after migration.

### ✅ Rollback
Automatically reverts target backend on failure.

### ✅ Duplicate Detection
Skips memories that already exist in target.

### ✅ Progress Reporting
Shows real-time progress for large migrations.

### ✅ Error Handling
Clear error messages with actionable solutions.

---

## Limitations

### Current Version (0.10.0)

**Supported**:
- ✅ All backend types (code complete)
- ✅ SQLite migrations (production tested)
- ✅ Verification and rollback
- ✅ Dry-run validation

**Not Yet Supported**:
- ❌ Incremental migration (--since)
- ❌ Migration analytics/history
- ❌ Scheduled migrations
- ❌ Multi-step migrations with transformation

**Testing Status**:
- ✅ SQLite ↔ SQLite (fully tested)
- ⚠️ Other backends (code complete, needs testing)

---

## Getting Help

### Documentation
- See `/docs/planning/MIGRATION_IMPLEMENTATION_SUMMARY.md` for implementation details
- See ADR-015 for architecture decisions

### Support
- GitHub Issues: Report bugs or request features
- CLI Help: `memorygraph migrate --help`

### Debugging
```bash
# Enable debug logging
export MEMORYGRAPH_LOG_LEVEL=DEBUG
memorygraph migrate --to <target> --verbose
```

---

## Next Steps

After completing your first migration:

1. **Verify Data**: Use search/recall to check memories
2. **Test Relationships**: Verify relationships are preserved
3. **Update Environment**: Point to new backend
4. **Backup**: Create backup of new backend

```bash
# Switch to new backend
export MEMORY_BACKEND=falkordb
export MEMORY_FALKORDB_URI=redis://prod:6379

# Verify data
memorygraph health

# Backup new backend
memorygraph export --format json --output prod-backup.json
```

---

**Quick Reference Card**:

```bash
# 1. Validate
memorygraph migrate --to <backend> --dry-run

# 2. Migrate
memorygraph migrate --to <backend> --verbose

# 3. Verify
memorygraph health
```

**That's it!** 🎉

---

**Document Version**: 1.0
**Last Updated**: 2025-12-04
**Status**: Production Ready (SQLite migrations)
