"""
Migration tools module - MCP tool definitions and handlers for database migration.
"""

from mcp.types import Tool
from .tools.migration_tools import handle_migrate_database, handle_validate_migration

# Tool definitions for MCP
MIGRATION_TOOLS = [
    Tool(
        name="migrate_database",
        description="""Migrate memories from current backend to another backend (e.g., SQLite → FalkorDB).

WHEN TO USE:
- Moving from development (SQLite) to production (FalkorDB, Neo4j)
- Switching backend providers
- Disaster recovery to different backend
- Testing performance across backends
- Backend consolidation or splitting

HOW TO USE:
- Always use dry_run=True first to validate
- Specify target_backend type (sqlite, neo4j, memgraph, falkordb, falkordblite)
- Provide target_config with connection details
- Set verify=True to ensure data integrity
- Migration includes memories and relationships

SAFETY FEATURES:
- Dry-run mode validates without changes
- Verification checks data integrity
- Automatic rollback on failure
- Progress reporting for large migrations

EXAMPLES:
- Validate: migrate_database(target_backend="falkordb", target_config={"uri": "redis://prod:6379"}, dry_run=True)
- Migrate: migrate_database(target_backend="falkordb", target_config={"uri": "redis://prod:6379"}, verify=True)
- Test: migrate_database(target_backend="sqlite", target_config={"path": "/tmp/test.db"})

RETURNS:
- success: Boolean indicating if migration succeeded
- imported_memories: Number of memories migrated
- imported_relationships: Number of relationships migrated
- verification: Data integrity check results
- errors: Any errors encountered""",
        inputSchema={
            "type": "object",
            "properties": {
                "target_backend": {
                    "type": "string",
                    "enum": ["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"],
                    "description": "Target backend type to migrate to"
                },
                "target_config": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Database path (for sqlite/falkordblite)"
                        },
                        "uri": {
                            "type": "string",
                            "description": "Database URI (for neo4j/memgraph/falkordb)"
                        },
                        "username": {
                            "type": "string",
                            "description": "Database username (optional)"
                        },
                        "password": {
                            "type": "string",
                            "description": "Database password (optional)"
                        },
                        "database": {
                            "type": "string",
                            "description": "Database name (optional)"
                        }
                    },
                    "description": "Target backend configuration"
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "Validate without making changes (RECOMMENDED: use true first)"
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
    ),
    Tool(
        name="validate_migration",
        description="""Validate that migration to target backend would succeed without making changes.

This is a convenience wrapper for migrate_database with dry_run=True.

WHEN TO USE:
- Before running actual migration
- Checking if target backend is accessible
- Estimating migration size and duration
- Validating target configuration

CHECKS PERFORMED:
- Source backend accessible
- Target backend accessible
- Backend compatibility
- Configuration validity
- Data export feasibility

EXAMPLES:
- validate_migration(target_backend="falkordb", target_config={"uri": "redis://prod:6379"})
- validate_migration(target_backend="neo4j", target_config={"uri": "bolt://localhost:7687", "username": "neo4j", "password": "password"})

RETURNS:
- Same as migrate_database but with dry_run=True
- No data is written to target""",
        inputSchema={
            "type": "object",
            "properties": {
                "target_backend": {
                    "type": "string",
                    "enum": ["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"],
                    "description": "Target backend type to validate migration to"
                },
                "target_config": {
                    "type": "object",
                    "description": "Target backend configuration"
                }
            },
            "required": ["target_backend"]
        }
    )
]

# Tool handlers mapping
MIGRATION_TOOL_HANDLERS = {
    "migrate_database": handle_migrate_database,
    "validate_migration": handle_validate_migration
}
