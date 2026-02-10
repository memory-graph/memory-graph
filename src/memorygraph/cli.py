"""
Command-line interface for MemoryGraph MCP Server.

Provides easy server startup with configuration options for AI coding agents.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Tuple

from . import __version__
from .config import TOOL_PROFILES, BackendType, Config
from .server import main as server_main

logger = logging.getLogger(__name__)


def _eprint(*args, **kwargs):
    """Print to stderr to avoid polluting MCP stdio transport on stdout."""
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)


async def _create_backend_and_db() -> Tuple:
    """Create a backend and the appropriate database wrapper.

    Returns a (backend, backend_name, db) tuple. The caller is responsible
    for calling ``await backend.disconnect()`` when finished.
    """
    from .backends.factory import BackendFactory
    from .backends.sqlite_fallback import SQLiteFallbackBackend
    from .database import MemoryDatabase
    from .sqlite_database import SQLiteMemoryDatabase

    backend = await BackendFactory.create_backend()
    backend_name = backend.backend_name()

    if isinstance(backend, SQLiteFallbackBackend):
        db = SQLiteMemoryDatabase(backend)
    else:
        db = MemoryDatabase(backend)

    return backend, backend_name, db


async def handle_export(args: argparse.Namespace) -> None:
    """Handle export command - works with all backends."""
    from .utils.export_import import export_to_json, export_to_markdown

    try:
        backend, backend_name, db = await _create_backend_and_db()
        _eprint(f"\nExporting memories from {backend_name} backend...")

        start_time = time.time()

        if args.format == "json":
            result = await export_to_json(db, args.output)
            duration = time.time() - start_time

            _eprint("\nExport complete!")
            _eprint(f"   Backend: {result.get('backend_type', backend_name)}")
            _eprint(f"   Output: {args.output}")
            _eprint(f"   Memories: {result['memory_count']}")
            _eprint(f"   Relationships: {result['relationship_count']}")
            _eprint(f"   Duration: {duration:.1f} seconds")

        elif args.format == "markdown":
            await export_to_markdown(db, args.output)
            duration = time.time() - start_time

            _eprint("\nExport complete!")
            _eprint(f"   Backend: {backend_name}")
            _eprint(f"   Output: {args.output}/")
            _eprint(f"   Duration: {duration:.1f} seconds")

        await backend.disconnect()

    except Exception as e:
        _eprint(f"Export failed: {e}")
        logger.error(f"Export failed: {e}", exc_info=True)
        sys.exit(1)


async def handle_import(args: argparse.Namespace) -> None:
    """Handle import command - works with all backends."""
    from .utils.export_import import import_from_json

    try:
        backend, backend_name, db = await _create_backend_and_db()
        _eprint(f"\nImporting memories to {backend_name} backend...")

        await db.initialize_schema()

        start_time = time.time()

        if args.format == "json":
            result = await import_from_json(db, args.input, skip_duplicates=args.skip_duplicates)
            duration = time.time() - start_time

            _eprint("\nImport complete!")
            _eprint(f"   Backend: {backend_name}")
            _eprint(f"   Imported: {result['imported_memories']} memories, {result['imported_relationships']} relationships")
            if result['skipped_memories'] > 0 or result['skipped_relationships'] > 0:
                _eprint(f"   Skipped: {result['skipped_memories']} memories, {result['skipped_relationships']} relationships")
            _eprint(f"   Duration: {duration:.1f} seconds")

        await backend.disconnect()

    except Exception as e:
        _eprint(f"Import failed: {e}")
        logger.error(f"Import failed: {e}", exc_info=True)
        sys.exit(1)


async def handle_migrate(args: argparse.Namespace) -> None:
    """Handle migrate command."""
    from .migration.manager import MigrationManager
    from .migration.models import BackendConfig, MigrationOptions

    _eprint(f"\nMigrating memories: {args.source_backend or 'current'} -> {args.target_backend}")

    try:
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
        # For cloud backend, read API key from Config
        target_password = None
        if args.target_backend == "cloud":
            target_password = Config.MEMORYGRAPH_API_KEY
            if not target_password:
                _eprint("Error: MEMORYGRAPH_API_KEY environment variable is required for cloud backend")
                sys.exit(1)

        target_config = BackendConfig(
            backend_type=BackendType(args.target_backend),
            path=args.to_path,
            uri=args.to_uri,
            password=target_password
        )

        # Build options
        options = MigrationOptions(
            dry_run=args.dry_run,
            verbose=args.verbose,
            skip_duplicates=args.skip_duplicates,
            verify=not args.no_verify,
            rollback_on_failure=True
        )

        # Perform migration
        manager = MigrationManager()
        result = await manager.migrate(source_config, target_config, options)

        # Display results
        if result.dry_run:
            _eprint("\nDry-run successful - migration would proceed safely")
            if result.source_stats:
                memory_count = result.source_stats.get('memory_count', 0)
                _eprint(f"   Source: {memory_count} memories")
            if result.errors:
                _eprint("\nWarnings:")
                for error in result.errors:
                    _eprint(f"   - {error}")

        elif result.success:
            _eprint("\nMigration completed successfully!")
            _eprint(f"   Migrated: {result.imported_memories} memories")
            _eprint(f"   Migrated: {result.imported_relationships} relationships")
            if result.skipped_memories > 0:
                _eprint(f"   Skipped: {result.skipped_memories} duplicates")
            _eprint(f"   Duration: {result.duration_seconds:.1f} seconds")

            if result.verification_result and result.verification_result.valid:
                _eprint("\nVerification passed:")
                _eprint(f"   Source: {result.verification_result.source_count} memories")
                _eprint(f"   Target: {result.verification_result.target_count} memories")
                _eprint(f"   Sample check: {result.verification_result.sample_passed}/{result.verification_result.sample_checks} passed")

        else:
            _eprint("\nMigration failed!")
            for error in result.errors:
                _eprint(f"   - {error}")
            sys.exit(1)

    except Exception as e:
        _eprint(f"Migration failed: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


async def handle_migrate_multitenant(args: argparse.Namespace) -> None:
    """Handle migrate-to-multitenant command."""
    from .backends.factory import BackendFactory
    from .migration.scripts import migrate_to_multitenant, rollback_from_multitenant

    try:
        # Connect to backend
        backend = await BackendFactory.create_backend()
        backend_name = backend.backend_name()

        if args.rollback:
            _eprint(f"\nRolling back multi-tenancy migration on {backend_name}...")

            result = await rollback_from_multitenant(backend, dry_run=args.dry_run)

            if result['dry_run']:
                _eprint("\nDry-run successful - rollback would proceed safely")
                _eprint(f"   Would clear tenant_id from: {result['memories_updated']} memories")
            elif result['success']:
                _eprint("\nRollback completed successfully!")
                _eprint(f"   Cleared tenant_id from: {result['memories_updated']} memories")
            else:
                _eprint("\nRollback failed!")
                for error in result['errors']:
                    _eprint(f"   - {error}")
                sys.exit(1)

        else:
            # Migrate to multi-tenant
            _eprint(f"\nMigrating to multi-tenant mode on {backend_name}...")
            _eprint(f"   Tenant ID: {args.tenant_id}")
            _eprint(f"   Visibility: {args.visibility}")

            result = await migrate_to_multitenant(
                backend,
                tenant_id=args.tenant_id,
                dry_run=args.dry_run,
                visibility=args.visibility
            )

            if result['dry_run']:
                _eprint("\nDry-run successful - migration would proceed safely")
                _eprint(f"   Would update: {result['memories_updated']} memories")
                _eprint(f"   Tenant ID would be: {result['tenant_id']}")
                _eprint(f"   Visibility would be: {result['visibility']}")
            elif result['success']:
                _eprint("\nMigration completed successfully!")
                _eprint(f"   Updated: {result['memories_updated']} memories")
                _eprint(f"   Tenant ID: {result['tenant_id']}")
                _eprint(f"   Visibility: {result['visibility']}")
                _eprint("\nNext steps:")
                _eprint("   1. Set MEMORY_MULTI_TENANT_MODE=true in your environment")
                _eprint("   2. Restart the server to enable multi-tenant indexes")
            else:
                _eprint("\nMigration failed!")
                for error in result['errors']:
                    _eprint(f"   - {error}")
                sys.exit(1)

        await backend.disconnect()

    except Exception as e:
        _eprint(f"Migration failed: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


async def perform_health_check(timeout: float = 5.0) -> dict:
    """
    Perform health check on the backend and return status information.

    Args:
        timeout: Maximum time in seconds to wait for health check (default: 5.0)

    Returns:
        Dictionary containing health check results:
            - status: "healthy" or "unhealthy"
            - connected: bool indicating if backend is connected
            - backend_type: str with backend type (e.g., "sqlite", "neo4j")
            - version: str with backend version (if available)
            - statistics: dict with database statistics (if available)
            - timestamp: ISO format timestamp of the check
            - error: str with error message (if unhealthy)
    """
    from .backends.factory import BackendFactory

    result = {
        "status": "unhealthy",
        "connected": False,
        "backend_type": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        # Create backend with timeout
        backend = await asyncio.wait_for(
            BackendFactory.create_backend(),
            timeout=timeout
        )

        # Run health check
        health_info = await asyncio.wait_for(
            backend.health_check(),
            timeout=timeout
        )

        result.update(health_info)
        connected = health_info.get("connected", False)
        result["status"] = "healthy" if connected else "unhealthy"
        if not connected and "error" not in result:
            result["error"] = "Backend reports disconnected status"

        await backend.disconnect()

    except asyncio.TimeoutError:
        result["error"] = f"Health check timed out after {timeout} seconds"
        logger.error(f"Health check timeout after {timeout}s")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Health check failed: {e}", exc_info=True)

    return result


def print_config_summary() -> None:
    """Print current configuration summary to stderr."""
    config = Config.get_config_summary()

    _eprint("\nCurrent Configuration:")
    _eprint(f"  Backend: {config['backend']}")
    _eprint(f"  Tool Profile: {Config.TOOL_PROFILE}")
    _eprint(f"  Log Level: {config['logging']['level']}")

    if config['backend'] in ['neo4j', 'auto']:
        _eprint(f"\n  Neo4j URI: {config['neo4j']['uri']}")
        _eprint(f"  Neo4j User: {config['neo4j']['user']}")
        _eprint(f"  Neo4j Password: {'[configured]' if config['neo4j']['password_configured'] else '[not set]'}")

    if config['backend'] in ['memgraph', 'auto']:
        _eprint(f"\n  Memgraph URI: {config['memgraph']['uri']}")

    if config['backend'] in ['sqlite', 'auto']:
        _eprint(f"\n  SQLite Path: {config['sqlite']['path']}")

    if config['backend'] in ['turso', 'auto']:
        _eprint(f"\n  Turso URL: {config['turso']['database_url'] or '[not set]'}")
        _eprint(f"  Turso Token: {'[configured]' if config['turso']['auth_token_configured'] else '[not set]'}")
        _eprint(f"  Turso Local Path: {config['turso']['path']}")

    if config['backend'] in ['cloud', 'auto']:
        _eprint(f"\n  Cloud API URL: {config['cloud']['api_url']}")
        _eprint(f"  Cloud API Key: {'[configured]' if config['cloud']['api_key_configured'] else '[not set]'}")
        _eprint(f"  Cloud Timeout: {config['cloud']['timeout']}s")

    if config['backend'] in ['falkordb', 'auto']:
        _eprint(f"\n  FalkorDB Host: {config['falkordb']['host']}")
        _eprint(f"  FalkorDB Port: {config['falkordb']['port']}")
        _eprint(f"  FalkorDB Password: {'[configured]' if config['falkordb']['password_configured'] else '[not set]'}")

    if config['backend'] in ['falkordblite', 'auto']:
        _eprint(f"\n  FalkorDBLite Path: {config['falkordblite']['path']}")

    _eprint()


def validate_backend(backend: str) -> None:
    """Validate backend choice."""
    valid_backends = [b.value for b in BackendType]
    if backend not in valid_backends:
        _eprint(f"Error: Invalid backend '{backend}'")
        _eprint(f"Valid options: {', '.join(valid_backends)}")
        sys.exit(1)


def validate_profile(profile: str) -> None:
    """Validate tool profile choice."""
    valid_profiles = list(TOOL_PROFILES.keys()) + ["lite", "standard", "full"]  # Include legacy
    if profile not in valid_profiles:
        _eprint(f"Error: Invalid profile '{profile}'")
        _eprint("Valid options: core, extended (or legacy: lite, standard, full)")
        sys.exit(1)

    # Warn about legacy profiles
    legacy_map = {"lite": "core", "standard": "extended", "full": "extended"}
    if profile in legacy_map:
        _eprint(f"Warning: Profile '{profile}' is deprecated. Using '{legacy_map[profile]}' instead.")
        _eprint(f"   Update your configuration to use: --profile {legacy_map[profile]}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MemoryGraph - MCP memory server for AI coding agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings (SQLite backend, core profile)
  memorygraph

  # Use extended profile (11 tools)
  memorygraph --profile extended

  # Use Neo4j backend with extended profile
  memorygraph --backend neo4j --profile extended

  # Show current configuration
  memorygraph --show-config

  # Run health check
  memorygraph --health

Environment Variables:
  MEMORY_BACKEND         Backend type (sqlite|neo4j|memgraph|falkordb|falkordblite|turso|cloud|auto) [default: sqlite]
  MEMORY_TOOL_PROFILE    Tool profile (core|extended) [default: core]
  MEMORY_SQLITE_PATH     SQLite database path [default: ~/.memorygraph/memory.db]
  MEMORY_LOG_LEVEL       Log level (DEBUG|INFO|WARNING|ERROR) [default: INFO]

  Neo4j Configuration:
    MEMORY_NEO4J_URI       Connection URI [default: bolt://localhost:7687]
    MEMORY_NEO4J_USER      Username [default: neo4j]
    MEMORY_NEO4J_PASSWORD  Password (required for Neo4j)

  Memgraph Configuration:
    MEMORY_MEMGRAPH_URI    Connection URI [default: bolt://localhost:7687]

  FalkorDB Configuration:
    MEMORY_FALKORDB_HOST   FalkorDB host [default: localhost]
    MEMORY_FALKORDB_PORT   FalkorDB port [default: 6379]
    MEMORY_FALKORDB_PASSWORD  Password (if required)

  FalkorDBLite Configuration:
    MEMORY_FALKORDBLITE_PATH  Database path [default: ~/.memorygraph/falkordblite.db]

  Turso Configuration:
    MEMORY_TURSO_URL       Turso database URL (required for turso backend)
    MEMORY_TURSO_AUTH_TOKEN  Turso authentication token (required for turso backend)

  Cloud Configuration:
    MEMORYGRAPH_API_KEY    API key for MemoryGraph Cloud (required for cloud backend)
    MEMORYGRAPH_API_URL    Cloud API URL [default: https://graph-api.memorygraph.dev]
    MEMORYGRAPH_TIMEOUT    Request timeout in seconds [default: 30]
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"memorygraph {__version__}"
    )

    parser.add_argument(
        "--backend",
        type=str,
        choices=["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite", "turso", "cloud", "auto"],
        help="Database backend to use (overrides MEMORY_BACKEND env var)"
    )

    parser.add_argument(
        "--profile",
        type=str,
        choices=["core", "extended", "lite", "standard", "full"],  # Include legacy for compatibility
        help="Tool profile to use: core (default, 9 tools) or extended (11 tools). Legacy profiles lite/standard/full are mapped to core/extended."
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (overrides MEMORY_LOG_LEVEL env var)"
    )

    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration and exit"
    )

    parser.add_argument(
        "--health",
        action="store_true",
        help="Run health check and exit"
    )

    parser.add_argument(
        "--health-json",
        action="store_true",
        help="Output health check as JSON (use with --health)"
    )

    parser.add_argument(
        "--health-timeout",
        type=float,
        default=5.0,
        help="Health check timeout in seconds (default: 5.0)"
    )

    # Export/Import subcommand
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export memories to file (works with all backends)"
    )
    export_parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown"],
        required=True,
        help="Export format (json or markdown)"
    )
    export_parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path (file for JSON, directory for Markdown)"
    )

    # Import command
    import_parser = subparsers.add_parser(
        "import",
        help="Import memories from file (works with all backends)"
    )
    import_parser.add_argument(
        "--format",
        type=str,
        choices=["json"],
        required=True,
        help="Import format (currently only JSON supported)"
    )
    import_parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input JSON file path"
    )
    import_parser.add_argument(
        "--skip-duplicates",
        action="store_true",
        help="Skip memories with existing IDs instead of overwriting"
    )

    # Migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate memories between backends"
    )
    migrate_parser.add_argument(
        "--from",
        dest="source_backend",
        type=str,
        choices=["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite", "turso", "cloud"],
        help="Source backend type (defaults to current MEMORY_BACKEND)"
    )
    migrate_parser.add_argument(
        "--from-path",
        type=str,
        help="Source database path (for sqlite/falkordblite/turso)"
    )
    migrate_parser.add_argument(
        "--from-uri",
        type=str,
        help="Source database URI (for neo4j/memgraph/falkordb/turso/cloud)"
    )
    migrate_parser.add_argument(
        "--to",
        dest="target_backend",
        type=str,
        required=True,
        choices=["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite", "turso", "cloud"],
        help="Target backend type"
    )
    migrate_parser.add_argument(
        "--to-path",
        type=str,
        help="Target database path (for sqlite/falkordblite/turso)"
    )
    migrate_parser.add_argument(
        "--to-uri",
        type=str,
        help="Target database URI (for neo4j/memgraph/falkordb/turso/cloud)"
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

    # Migrate to multi-tenant command
    multitenant_parser = subparsers.add_parser(
        "migrate-to-multitenant",
        help="Migrate existing single-tenant database to multi-tenant mode"
    )
    multitenant_parser.add_argument(
        "--tenant-id",
        type=str,
        default="default",
        help="Tenant ID to assign to existing memories (default: default)"
    )
    multitenant_parser.add_argument(
        "--visibility",
        type=str,
        choices=["private", "project", "team", "public"],
        default="team",
        help="Visibility level to set for existing memories (default: team)"
    )
    multitenant_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    multitenant_parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback multi-tenancy migration (clear tenant_id fields)"
    )

    args = parser.parse_args()

    # Apply CLI arguments to environment variables.
    # Config uses _EnvVar descriptors that read os.environ dynamically,
    # so setting env vars is sufficient for the current process.
    if args.backend:
        validate_backend(args.backend)
        os.environ["MEMORY_BACKEND"] = args.backend

    if args.profile:
        validate_profile(args.profile)
        profile = {"lite": "core", "standard": "extended", "full": "extended"}.get(args.profile, args.profile)
        os.environ["MEMORY_TOOL_PROFILE"] = profile

    if args.log_level:
        os.environ["MEMORY_LOG_LEVEL"] = args.log_level

    # Configure logging to stderr (default) so it doesn't pollute MCP stdout
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

    # Handle special commands
    if args.show_config:
        _eprint(f"MemoryGraph MCP Server v{__version__}")
        print_config_summary()
        sys.exit(0)

    if args.health:
        # Perform health check
        result = asyncio.run(perform_health_check(timeout=args.health_timeout))

        # Output in JSON format if requested (stdout is intentional for machine-readable output)
        if args.health_json:
            print(json.dumps(result, indent=2))
        else:
            # Human-readable format goes to stderr
            _eprint(f"MemoryGraph MCP Server v{__version__}")
            _eprint("\nHealth Check Results\n")
            _eprint(f"Status: {'Healthy' if result['status'] == 'healthy' else 'Unhealthy'}")
            _eprint(f"Backend: {result.get('backend_type', 'unknown')}")
            _eprint(f"Connected: {'Yes' if result.get('connected') else 'No'}")

            if result.get('version'):
                _eprint(f"Version: {result['version']}")

            if result.get('db_path'):
                _eprint(f"Database: {result['db_path']}")

            if result.get('statistics'):
                stats = result['statistics']
                _eprint("\nStatistics:")
                if 'memory_count' in stats:
                    _eprint(f"  Memories: {stats['memory_count']}")
                for key, value in stats.items():
                    if key != 'memory_count':
                        _eprint(f"  {key.replace('_', ' ').title()}: {value}")

            if result.get('database_size_bytes'):
                size_mb = result['database_size_bytes'] / (1024 * 1024)
                _eprint(f"  Database Size: {size_mb:.2f} MB")

            if result.get('error'):
                _eprint(f"\nError: {result['error']}")

            _eprint(f"\nTimestamp: {result['timestamp']}")

        # Exit with appropriate status code
        sys.exit(0 if result['status'] == 'healthy' else 1)

    # Handle export/import/migrate commands
    if args.command == "export":
        asyncio.run(handle_export(args))
        sys.exit(0)

    if args.command == "import":
        asyncio.run(handle_import(args))
        sys.exit(0)

    if args.command == "migrate":
        asyncio.run(handle_migrate(args))
        sys.exit(0)

    if args.command == "migrate-to-multitenant":
        asyncio.run(handle_migrate_multitenant(args))
        sys.exit(0)

    # Start the server - all diagnostic output to stderr to keep stdout
    # clean for MCP JSON-RPC transport
    _eprint(f"Starting MemoryGraph MCP Server v{__version__}")
    _eprint(f"Backend: {Config.BACKEND}")
    _eprint(f"Profile: {Config.TOOL_PROFILE}")
    _eprint(f"Log Level: {Config.LOG_LEVEL}")
    _eprint("\nPress Ctrl+C to stop the server\n")

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        _eprint("\n\nServer stopped gracefully")
        sys.exit(0)
    except Exception as e:
        _eprint(f"\nServer error: {e}")
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
