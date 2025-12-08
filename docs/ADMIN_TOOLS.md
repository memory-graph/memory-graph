# Admin-Only Tools

This document describes tools that are available in MemoryGraph but **not included in standard tool profiles** (Core/Extended). These tools are for administrative operations and require careful use.

---

## Migration Tools

These tools are available for database migrations and validation. They are **not included in any tool profile** to prevent accidental use during normal operation.

### migrate_database

**Purpose**: Migrate a MemoryGraph database from one backend to another.

**Use Cases**:
- Migrating from SQLite to Neo4j
- Migrating from local SQLite to Turso Cloud
- Migrating between Neo4j instances
- Copying data to a new backend for testing

**Parameters**:
```json
{
  "source_backend": "sqlite|neo4j|memgraph|turso|cloud",
  "target_backend": "sqlite|neo4j|memgraph|turso|cloud",
  "source_config": {
    // Backend-specific configuration (paths, URIs, credentials)
  },
  "target_config": {
    // Backend-specific configuration (paths, URIs, credentials)
  },
  "dry_run": true|false  // Optional: Preview migration without executing
}
```

**Example - SQLite to Neo4j**:
```json
{
  "source_backend": "sqlite",
  "target_backend": "neo4j",
  "source_config": {
    "path": "/path/to/memory.db"
  },
  "target_config": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your-password"
  },
  "dry_run": false
}
```

**Returns**:
```json
{
  "success": true,
  "memories_migrated": 150,
  "relationships_migrated": 250,
  "errors": [],
  "warnings": ["Some non-critical issues"],
  "duration_seconds": 12.5
}
```

**Warnings**:
- Always backup your data before migration
- Target database will be cleared before migration
- Large migrations can take significant time
- Some backend-specific features may not translate

---

### validate_migration

**Purpose**: Validate that a migration completed successfully by comparing source and target databases.

**Use Cases**:
- Verify migration integrity after running migrate_database
- Audit data consistency between backends
- Troubleshoot migration issues

**Parameters**:
```json
{
  "source_backend": "sqlite|neo4j|memgraph|turso|cloud",
  "target_backend": "sqlite|neo4j|memgraph|turso|cloud",
  "source_config": {
    // Backend-specific configuration
  },
  "target_config": {
    // Backend-specific configuration
  }
}
```

**Returns**:
```json
{
  "success": true,
  "validation_passed": true,
  "source_memory_count": 150,
  "target_memory_count": 150,
  "source_relationship_count": 250,
  "target_relationship_count": 250,
  "discrepancies": [],
  "details": {
    "memory_ids_matched": true,
    "relationship_ids_matched": true,
    "content_integrity": true
  }
}
```

**Validation Checks**:
- Memory count matches
- Relationship count matches
- All memory IDs present in both databases
- All relationship IDs present in both databases
- Content integrity (sampling)

---

## Temporal Backend Methods (Python API Only)

These backend methods are available for Python developers but **not exposed as MCP tools** to save context budget.

### query_as_of(memory_id, as_of, backend)

Query relationships as they existed at a specific point in time.

**Python Usage**:
```python
from datetime import datetime
from memorygraph.backends.factory import BackendFactory
from memorygraph.sqlite_database import SQLiteMemoryDatabase

backend = await BackendFactory.create_backend()
memory_db = SQLiteMemoryDatabase(backend)

# Query as of June 1, 2024
as_of = datetime(2024, 6, 1, tzinfo=timezone.utc)
relationships = await memory_db.get_related_memories(
    memory_id="problem-123",
    as_of=as_of
)
```

### get_relationship_history(memory_id, backend)

Get full history of relationships for a memory, including invalidated ones.

**Python Usage**:
```python
# Get complete temporal history
history = await memory_db.get_relationship_history(memory_id="problem-123")

for entry in history:
    print(f"{entry['valid_from']} - {entry['valid_until']}: {entry['relationship_type']}")
```

### what_changed(since, backend)

Show all relationship changes since a specific time.

**Python Usage**:
```python
from datetime import datetime, timedelta, timezone

# What changed in the last 7 days
since = datetime.now(timezone.utc) - timedelta(days=7)
changes = await memory_db.what_changed(since=since)

print(f"New relationships: {len(changes['created'])}")
print(f"Invalidated relationships: {len(changes['invalidated'])}")
```

---

## Why Admin-Only?

These tools are excluded from standard profiles for several reasons:

1. **Context Budget**: Each tool consumes ~1-1.5k tokens. The 2 migration tools + 3 temporal tools = ~5-7k tokens that would rarely be used.

2. **Risk of Accidental Use**: Migration tools can clear databases or move large amounts of data. They should be used deliberately, not accidentally invoked during normal sessions.

3. **Specialized Use Cases**: These tools are used infrequently:
   - Migration: Once during setup or major infrastructure changes
   - Validation: After migrations or during troubleshooting
   - Temporal queries: Advanced debugging scenarios (~5% of sessions)

4. **Alternative Access**:
   - Migration tools can be called directly via Python API or dedicated CLI commands
   - Temporal methods are available via backend Python API
   - No functionality is lost, just moved to more appropriate access patterns

---

## How to Access Admin Tools

### Option 1: Direct Python API

```python
from memorygraph.migration.migrate import migrate_database, validate_migration

# Run migration
result = await migrate_database(
    source_backend="sqlite",
    target_backend="neo4j",
    source_config={"path": "/path/to/memory.db"},
    target_config={"uri": "bolt://localhost:7687", "user": "neo4j", "password": "pw"}
)
```

### Option 2: CLI Commands (Future)

```bash
# Planned for future release
memorygraph migrate --from sqlite --to neo4j
memorygraph validate --source sqlite --target neo4j
```

### Option 3: Temporary MCP Registration

If you need these tools in an MCP session temporarily:

1. Edit `src/memorygraph/config.py`
2. Add tool names to your profile temporarily
3. Restart MCP server
4. Remove after use

**Not recommended** for production use.

---

## Related Documentation

- [Tool Profiles Reference](TOOL_PROFILES.md) - Standard Core/Extended profiles
- [ADR-017: Context Budget Constraint](adr/017-context-budget-constraint.md) - Decision rationale
- [Migration Guide](guides/migration.md) - Step-by-step migration procedures
- [Temporal Memory Guide](guides/temporal-memory.md) - Bi-temporal tracking documentation

---

**Last Updated**: December 7, 2025
**Tools Documented**: 5 (2 migration + 3 temporal backend methods)
**Status**: Admin-only, not in standard profiles
