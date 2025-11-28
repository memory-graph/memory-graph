"""
Command-line interface for MemoryGraph MCP Server.

Provides easy server startup with configuration options for AI coding agents.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

from . import __version__
from .config import Config, BackendType, TOOL_PROFILES
from .server import main as server_main

logger = logging.getLogger(__name__)


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
    valid_profiles = list(TOOL_PROFILES.keys())
    if profile not in valid_profiles:
        print(f"Error: Invalid profile '{profile}'")
        print(f"Valid options: {', '.join(valid_profiles)}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MemoryGraph - MCP memory server for AI coding agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings (SQLite backend, lite profile)
  memorygraph

  # Use Neo4j backend with full tool profile
  memorygraph --backend neo4j --profile full

  # Show current configuration
  memorygraph --show-config

  # Run health check
  memorygraph --health

Environment Variables:
  MEMORY_BACKEND         Backend type (sqlite|neo4j|memgraph|auto) [default: sqlite]
  MEMORY_TOOL_PROFILE    Tool profile (lite|standard|full) [default: lite]
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
        choices=["lite", "standard", "full"],
        help="Tool profile to use (overrides MEMORY_TOOL_PROFILE env var)"
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
        print(f"MemoryGraph MCP Server v{__version__}")
        print("\n🏥 Running health check...\n")
        # TODO: Implement proper health check
        print("Health check not yet implemented.")
        print("Use --show-config to see current configuration.")
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
