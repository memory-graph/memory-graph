"""
Configuration management for MemoryGraph.

This module centralizes all configuration options and environment variable handling
for the multi-backend memory server.
"""

import os
from enum import Enum
from typing import Optional, List


class BackendType(Enum):
    """Supported backend types."""
    NEO4J = "neo4j"
    MEMGRAPH = "memgraph"
    SQLITE = "sqlite"
    TURSO = "turso"
    CLOUD = "cloud"
    FALKORDB = "falkordb"
    FALKORDBLITE = "falkordblite"
    AUTO = "auto"


# Tool profile definitions
# Core mode: Essential tools for daily use (9 tools)
# Extended mode: Core + advanced analytics (11 tools)
TOOL_PROFILES = {
    "core": [
        # Essential memory operations (5 tools)
        "store_memory",
        "get_memory",
        "search_memories",
        "update_memory",
        "delete_memory",
        # Essential relationship operations (2 tools)
        "create_relationship",
        "get_related_memories",
        # Discovery and navigation (2 tools)
        "recall_memories",  # Primary search with fuzzy matching
        "get_recent_activity",  # Session briefing
    ],
    "extended": [
        # All Core tools (9)
        "store_memory",
        "get_memory",
        "search_memories",
        "update_memory",
        "delete_memory",
        "create_relationship",
        "get_related_memories",
        "recall_memories",
        "get_recent_activity",
        # Advanced analytics (2 additional)
        "get_memory_statistics",  # Database stats
        "search_relationships_by_context",  # Complex relationship queries
    ],
}


class Config:
    """
    Configuration class for the memory server.

    Environment Variables:
        MEMORY_BACKEND: Backend type (neo4j|memgraph|sqlite|turso|cloud|falkordb|falkordblite|auto) [default: sqlite]

        Neo4j Configuration:
            MEMORY_NEO4J_URI or NEO4J_URI: Connection URI [default: bolt://localhost:7687]
            MEMORY_NEO4J_USER or NEO4J_USER: Username [default: neo4j]
            MEMORY_NEO4J_PASSWORD or NEO4J_PASSWORD: Password [required for Neo4j]

        Memgraph Configuration:
            MEMORY_MEMGRAPH_URI: Connection URI [default: bolt://localhost:7687]
            MEMORY_MEMGRAPH_USER: Username [default: ""]
            MEMORY_MEMGRAPH_PASSWORD: Password [default: ""]

        SQLite Configuration:
            MEMORY_SQLITE_PATH: Database file path [default: ~/.memorygraph/memory.db]

        Turso Configuration:
            MEMORY_TURSO_PATH: Local database file path [default: ~/.memorygraph/memory.db]
            TURSO_DATABASE_URL: Turso database URL (e.g., libsql://your-db.turso.io)
            TURSO_AUTH_TOKEN: Turso authentication token

        Cloud Configuration:
            MEMORYGRAPH_API_KEY: API key for MemoryGraph Cloud (required for cloud backend)
            MEMORYGRAPH_API_URL: Cloud API base URL [default: https://graph-api.memorygraph.dev]
            MEMORYGRAPH_TIMEOUT: Request timeout in seconds [default: 30]

        Tool Profile Configuration:
            MEMORY_TOOL_PROFILE: Tool profile (core|extended) [default: core]

        Logging Configuration:
            MEMORY_LOG_LEVEL: Log level (DEBUG|INFO|WARNING|ERROR) [default: INFO]
    """

    # Backend Selection
    BACKEND: str = os.getenv("MEMORY_BACKEND", "sqlite")

    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: Optional[str] = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
    NEO4J_DATABASE: str = os.getenv("MEMORY_NEO4J_DATABASE", "neo4j")

    # Memgraph Configuration
    MEMGRAPH_URI: str = os.getenv("MEMORY_MEMGRAPH_URI", "bolt://localhost:7687")
    MEMGRAPH_USER: str = os.getenv("MEMORY_MEMGRAPH_USER", "")
    MEMGRAPH_PASSWORD: str = os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

    # SQLite Configuration
    SQLITE_PATH: str = os.getenv("MEMORY_SQLITE_PATH", os.path.expanduser("~/.memorygraph/memory.db"))

    # Turso Configuration
    TURSO_PATH: str = os.getenv("MEMORY_TURSO_PATH", os.path.expanduser("~/.memorygraph/memory.db"))
    TURSO_DATABASE_URL: Optional[str] = os.getenv("TURSO_DATABASE_URL")
    TURSO_AUTH_TOKEN: Optional[str] = os.getenv("TURSO_AUTH_TOKEN")

    # Cloud Configuration
    MEMORYGRAPH_API_KEY: Optional[str] = os.getenv("MEMORYGRAPH_API_KEY")
    MEMORYGRAPH_API_URL: str = os.getenv("MEMORYGRAPH_API_URL", "https://graph-api.memorygraph.dev")
    MEMORYGRAPH_TIMEOUT: int = int(os.getenv("MEMORYGRAPH_TIMEOUT", "30"))

    # Tool Profile Configuration
    TOOL_PROFILE: str = os.getenv("MEMORY_TOOL_PROFILE", "core")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("MEMORY_LOG_LEVEL", "INFO")

    # Feature Flags
    AUTO_EXTRACT_ENTITIES: bool = os.getenv("MEMORY_AUTO_EXTRACT_ENTITIES", "true").lower() == "true"
    SESSION_BRIEFING: bool = os.getenv("MEMORY_SESSION_BRIEFING", "true").lower() == "true"
    BRIEFING_VERBOSITY: str = os.getenv("MEMORY_BRIEFING_VERBOSITY", "standard")
    BRIEFING_RECENCY_DAYS: int = int(os.getenv("MEMORY_BRIEFING_RECENCY_DAYS", "7"))

    # Relationship Configuration
    ALLOW_RELATIONSHIP_CYCLES: bool = os.getenv("MEMORY_ALLOW_CYCLES", "false").lower() == "true"

    @classmethod
    def get_backend_type(cls) -> BackendType:
        """
        Get the configured backend type.

        Returns:
            BackendType enum value
        """
        backend_str = cls.BACKEND.lower()
        try:
            return BackendType(backend_str)
        except ValueError:
            return BackendType.AUTO

    @classmethod
    def is_neo4j_configured(cls) -> bool:
        """Check if Neo4j backend is properly configured."""
        return bool(cls.NEO4J_PASSWORD)

    @classmethod
    def is_memgraph_configured(cls) -> bool:
        """Check if Memgraph backend is configured."""
        return bool(cls.MEMGRAPH_URI)

    @classmethod
    def get_enabled_tools(cls) -> Optional[List[str]]:
        """
        Get the list of enabled tools based on the configured profile.

        Returns:
            List of tool names to enable, or None for legacy profiles (defaults to core)
        """
        profile = cls.TOOL_PROFILE.lower()
        # Map legacy profiles to new ones
        legacy_map = {
            "lite": "core",
            "standard": "extended",
            "full": "extended"
        }
        profile = legacy_map.get(profile, profile)
        return TOOL_PROFILES.get(profile, TOOL_PROFILES["core"])

    @classmethod
    def get_config_summary(cls) -> dict:
        """
        Get a summary of current configuration (without sensitive data).

        Returns:
            Dictionary with configuration summary
        """
        return {
            "backend": cls.BACKEND,
            "neo4j": {
                "uri": cls.NEO4J_URI,
                "user": cls.NEO4J_USER,
                "password_configured": bool(cls.NEO4J_PASSWORD),
                "database": cls.NEO4J_DATABASE
            },
            "memgraph": {
                "uri": cls.MEMGRAPH_URI,
                "user": cls.MEMGRAPH_USER,
                "password_configured": bool(cls.MEMGRAPH_PASSWORD)
            },
            "sqlite": {
                "path": cls.SQLITE_PATH
            },
            "turso": {
                "path": cls.TURSO_PATH,
                "database_url": cls.TURSO_DATABASE_URL,
                "auth_token_configured": bool(cls.TURSO_AUTH_TOKEN)
            },
            "cloud": {
                "api_url": cls.MEMORYGRAPH_API_URL,
                "api_key_configured": bool(cls.MEMORYGRAPH_API_KEY),
                "timeout": cls.MEMORYGRAPH_TIMEOUT
            },
            "logging": {
                "level": cls.LOG_LEVEL
            },
            "features": {
                "auto_extract_entities": cls.AUTO_EXTRACT_ENTITIES,
                "session_briefing": cls.SESSION_BRIEFING,
                "briefing_verbosity": cls.BRIEFING_VERBOSITY,
                "briefing_recency_days": cls.BRIEFING_RECENCY_DAYS
            },
            "relationships": {
                "allow_cycles": cls.ALLOW_RELATIONSHIP_CYCLES
            }
        }


# Convenience function for getting config
def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance
    """
    return Config
