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
from datetime import datetime, UTC
from typing import Optional

from . import __version__
from .config import Config, BackendType, TOOL_PROFILES
from .server import main as server_main

logger = logging.getLogger(__name__)


async def handle_export(args: argparse.Namespace) -> None:
    """Handle export command."""
    from .backends.factory import BackendFactory
    from .sqlite_database import SQLiteMemoryDatabase
    from .backends.sqlite_fallback import SQLiteFallbackBackend
    from .utils.export_import import export_to_json, export_to_markdown

    print(f"\n📤 Exporting memories to {args.format.upper()} format...")

    try:
        # Connect to database
        backend = await BackendFactory.create_backend()

        if not isinstance(backend, SQLiteFallbackBackend):
            print("❌ Error: Export currently only supported for SQLite backend")
            sys.exit(1)

        db = SQLiteMemoryDatabase(backend)

        # Perform export
        if args.format == "json":
            await export_to_json(db, args.output)
            print(f"✅ Successfully exported to {args.output}")
        elif args.format == "markdown":
            await export_to_markdown(db, args.output)
            print(f"✅ Successfully exported to {args.output}/")

        await backend.disconnect()

    except Exception as e:
        print(f"❌ Export failed: {e}")
        logger.error(f"Export failed: {e}", exc_info=True)
        sys.exit(1)


async def handle_import(args: argparse.Namespace) -> None:
    """Handle import command."""
    from .backends.factory import BackendFactory
    from .sqlite_database import SQLiteMemoryDatabase
    from .backends.sqlite_fallback import SQLiteFallbackBackend
    from .utils.export_import import import_from_json

    print(f"\n📥 Importing memories from {args.format.upper()} format...")

    try:
        # Connect to database
        backend = await BackendFactory.create_backend()

        if not isinstance(backend, SQLiteFallbackBackend):
            print("❌ Error: Import currently only supported for SQLite backend")
            sys.exit(1)

        db = SQLiteMemoryDatabase(backend)
        await db.initialize_schema()

        # Perform import
        if args.format == "json":
            result = await import_from_json(db, args.input, skip_duplicates=args.skip_duplicates)

            print(f"\n✅ Import complete:")
            print(f"   - Imported: {result['imported_memories']} memories, {result['imported_relationships']} relationships")
            if result['skipped_memories'] > 0 or result['skipped_relationships'] > 0:
                print(f"   - Skipped: {result['skipped_memories']} memories, {result['skipped_relationships']} relationships")

        await backend.disconnect()

    except Exception as e:
        print(f"❌ Import failed: {e}")
        logger.error(f"Import failed: {e}", exc_info=True)
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
        "timestamp": datetime.now(UTC).isoformat()
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

        # Update result with health check information
        result.update(health_info)

        # Determine overall status
        if health_info.get("connected", False):
            result["status"] = "healthy"
        else:
            result["status"] = "unhealthy"
            if "error" not in result:
                result["error"] = "Backend reports disconnected status"

        # Clean up
        await backend.disconnect()

    except asyncio.TimeoutError:
        result["error"] = f"Health check timed out after {timeout} seconds"
        result["status"] = "unhealthy"
        logger.error(f"Health check timeout after {timeout}s")

    except Exception as e:
        result["error"] = str(e)
        result["status"] = "unhealthy"
        logger.error(f"Health check failed: {e}", exc_info=True)

    return result


def print_config_summary() -> None:
    """Print current configuration summary."""
    config = Config.get_config_summary()

    print("\n📋 Current Configuration:")
    print(f"  Backend: {config['backend']}")
    print(f"  Tool Profile: {Config.TOOL_PROFILE}")
    print(f"  Log Level: {config['logging']['level']}")

    if config['backend'] in ['neo4j', 'auto']:
        print(f"\n  Neo4j URI: {config['neo4j']['uri']}")
        print(f"  Neo4j User: {config['neo4j']['user']}")
        print(f"  Neo4j Password: {'✓ Configured' if config['neo4j']['password_configured'] else '✗ Not set'}")

    if config['backend'] in ['memgraph', 'auto']:
        print(f"\n  Memgraph URI: {config['memgraph']['uri']}")

    if config['backend'] in ['sqlite', 'auto']:
        print(f"\n  SQLite Path: {config['sqlite']['path']}")

    print()


def validate_backend(backend: str) -> None:
    """Validate backend choice."""
    valid_backends = [b.value for b in BackendType]
    if backend not in valid_backends:
        print(f"Error: Invalid backend '{backend}'")
        print(f"Valid options: {', '.join(valid_backends)}")
        sys.exit(1)


def validate_profile(profile: str) -> None:
    """Validate tool profile choice."""
    valid_profiles = list(TOOL_PROFILES.keys()) + ["lite", "standard", "full"]  # Include legacy
    if profile not in valid_profiles:
        print(f"Error: Invalid profile '{profile}'")
        print(f"Valid options: core, extended (or legacy: lite, standard, full)")
        sys.exit(1)

    # Warn about legacy profiles
    legacy_map = {"lite": "core", "standard": "extended", "full": "extended"}
    if profile in legacy_map:
        print(f"⚠️  Warning: Profile '{profile}' is deprecated. Using '{legacy_map[profile]}' instead.")
        print(f"   Update your configuration to use: --profile {legacy_map[profile]}")


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
  MEMORY_BACKEND         Backend type (sqlite|neo4j|memgraph|auto) [default: sqlite]
  MEMORY_TOOL_PROFILE    Tool profile (core|extended) [default: core]
  MEMORY_SQLITE_PATH     SQLite database path [default: ~/.memorygraph/memory.db]
  MEMORY_LOG_LEVEL       Log level (DEBUG|INFO|WARNING|ERROR) [default: INFO]

  Neo4j Configuration:
    MEMORY_NEO4J_URI       Connection URI [default: bolt://localhost:7687]
    MEMORY_NEO4J_USER      Username [default: neo4j]
    MEMORY_NEO4J_PASSWORD  Password (required for Neo4j)

  Memgraph Configuration:
    MEMORY_MEMGRAPH_URI    Connection URI [default: bolt://localhost:7687]
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
        choices=["sqlite", "neo4j", "memgraph", "auto"],
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
    export_parser = subparsers.add_parser("export", help="Export memories to file")
    export_parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown"],
        required=True,
        help="Export format"
    )
    export_parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path (file for JSON, directory for Markdown)"
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import memories from file")
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

    args = parser.parse_args()

    # Apply CLI arguments to environment variables
    if args.backend:
        validate_backend(args.backend)
        os.environ["MEMORY_BACKEND"] = args.backend

    if args.profile:
        validate_profile(args.profile)
        os.environ["MEMORY_TOOL_PROFILE"] = args.profile

    if args.log_level:
        os.environ["MEMORY_LOG_LEVEL"] = args.log_level

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handle special commands
    if args.show_config:
        print(f"MemoryGraph MCP Server v{__version__}")
        print_config_summary()
        sys.exit(0)

    if args.health:
        # Perform health check
        result = asyncio.run(perform_health_check(timeout=args.health_timeout))

        # Output in JSON format if requested
        if args.health_json:
            print(json.dumps(result, indent=2))
        else:
            # Human-readable format
            print(f"MemoryGraph MCP Server v{__version__}")
            print("\n🏥 Health Check Results\n")
            print(f"Status: {'✅ Healthy' if result['status'] == 'healthy' else '❌ Unhealthy'}")
            print(f"Backend: {result.get('backend_type', 'unknown')}")
            print(f"Connected: {'Yes' if result.get('connected') else 'No'}")

            if result.get('version'):
                print(f"Version: {result['version']}")

            if result.get('db_path'):
                print(f"Database: {result['db_path']}")

            if result.get('statistics'):
                stats = result['statistics']
                print(f"\nStatistics:")
                if 'memory_count' in stats:
                    print(f"  Memories: {stats['memory_count']}")
                for key, value in stats.items():
                    if key != 'memory_count':
                        print(f"  {key.replace('_', ' ').title()}: {value}")

            if result.get('database_size_bytes'):
                size_mb = result['database_size_bytes'] / (1024 * 1024)
                print(f"  Database Size: {size_mb:.2f} MB")

            if result.get('error'):
                print(f"\nError: {result['error']}")

            print(f"\nTimestamp: {result['timestamp']}")

        # Exit with appropriate status code
        sys.exit(0 if result['status'] == 'healthy' else 1)

    # Handle export/import commands
    if args.command == "export":
        asyncio.run(handle_export(args))
        sys.exit(0)

    if args.command == "import":
        asyncio.run(handle_import(args))
        sys.exit(0)

    # Start the server
    print(f"🚀 Starting MemoryGraph MCP Server v{__version__}")
    print(f"Backend: {Config.BACKEND}")
    print(f"Profile: {Config.TOOL_PROFILE}")
    print(f"Log Level: {Config.LOG_LEVEL}")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped gracefully")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
