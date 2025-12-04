"""
MCP tools for database migration.

Provides migration tools for moving memories between different backend types.
"""

import logging
from typing import Dict, Any, Optional

from ..migration.manager import MigrationManager, MigrationError
from ..migration.models import BackendConfig, MigrationOptions, BackendType

logger = logging.getLogger(__name__)


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

        # Parse target backend type
        try:
            target_backend_type = BackendType(target_backend.lower())
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid target backend: {target_backend}. Must be one of: sqlite, neo4j, memgraph, falkordb, falkordblite",
                "error_type": "ValueError"
            }

        # Build target config
        target_config_obj = BackendConfig(
            backend_type=target_backend_type,
            path=target_config.get("path") if target_config else None,
            uri=target_config.get("uri") if target_config else None,
            username=target_config.get("username") if target_config else None,
            password=target_config.get("password") if target_config else None,
            database=target_config.get("database") if target_config else None
        )

        # Validate target config
        validation_errors = target_config_obj.validate()
        if validation_errors:
            return {
                "success": False,
                "error": f"Invalid target configuration: {', '.join(validation_errors)}",
                "error_type": "ValidationError"
            }

        # Build options
        options = MigrationOptions(
            dry_run=dry_run,
            verbose=True,
            skip_duplicates=skip_duplicates,
            verify=verify,
            rollback_on_failure=True
        )

        # Perform migration
        logger.info(f"Starting migration: {source_config.backend_type.value} → {target_backend_type.value}")
        manager = MigrationManager()
        result = await manager.migrate(source_config, target_config_obj, options)

        # Format response
        response = {
            "success": result.success,
            "dry_run": result.dry_run,
            "source_backend": source_config.backend_type.value,
            "target_backend": target_backend,
            "imported_memories": result.imported_memories,
            "imported_relationships": result.imported_relationships,
            "skipped_memories": result.skipped_memories,
            "duration_seconds": round(result.duration_seconds, 2),
            "errors": result.errors
        }

        # Add verification results if available
        if result.verification_result:
            response["verification"] = {
                "valid": result.verification_result.valid,
                "source_count": result.verification_result.source_count,
                "target_count": result.verification_result.target_count,
                "sample_checks": result.verification_result.sample_checks,
                "sample_passed": result.verification_result.sample_passed,
                "errors": result.verification_result.errors
            }

        # Add stats if available
        if result.source_stats:
            response["source_stats"] = result.source_stats
        if result.target_stats:
            response["target_stats"] = result.target_stats

        return response

    except MigrationError as e:
        logger.error(f"Migration failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "MigrationError"
        }
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


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

    Example:
        # Validate migration before running
        result = await validate_migration(
            target_backend="falkordb",
            target_config={
                "uri": "redis://prod.example.com:6379"
            }
        )
    """
    # Call migrate_database with dry_run=True
    return await handle_migrate_database(
        target_backend=target_backend,
        target_config=target_config,
        dry_run=True,
        verify=False  # No need to verify in dry-run
    )
