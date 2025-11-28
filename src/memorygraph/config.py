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
    AUTO = "auto"


# Tool profile definitions
TOOL_PROFILES = {
    "lite": [
        # Core memory operations (5 tools)
        "store_memory",
        "get_memory",
        "search_memories",
        "update_memory",
        "delete_memory",
        # Core relationship operations (3 tools)
        "create_relationship",
        "get_related_memories",
        "get_memory_statistics",
    ],
    "standard": [
        # Lite tools (8)
        "store_memory",
        "get_memory",
        "search_memories",
        "update_memory",
        "delete_memory",
        "create_relationship",
        "get_related_memories",
        "get_memory_statistics",
        # Intelligence tools (7 additional)
        "find_similar_solutions",
        "suggest_patterns_for_context",
        "get_intelligent_context",
        "get_project_summary",
        "get_session_briefing",
        "get_memory_history",
        "track_entity_timeline",
    ],
    "full": None,  # None means all tools enabled
}


class Config:
    """
    Configuration class for the memory server.

    Environment Variables:
        MEMORY_BACKEND: Backend type (neo4j|memgraph|sqlite|auto) [default: sqlite]

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

        Tool Profile Configuration:
            MEMORY_TOOL_PROFILE: Tool profile (lite|standard|full) [default: lite]

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

    # Tool Profile Configuration
    TOOL_PROFILE: str = os.getenv("MEMORY_TOOL_PROFILE", "lite")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("MEMORY_LOG_LEVEL", "INFO")

    # Feature Flags
    AUTO_EXTRACT_ENTITIES: bool = os.getenv("MEMORY_AUTO_EXTRACT_ENTITIES", "true").lower() == "true"
    SESSION_BRIEFING: bool = os.getenv("MEMORY_SESSION_BRIEFING", "true").lower() == "true"
    BRIEFING_VERBOSITY: str = os.getenv("MEMORY_BRIEFING_VERBOSITY", "standard")
    BRIEFING_RECENCY_DAYS: int = int(os.getenv("MEMORY_BRIEFING_RECENCY_DAYS", "7"))

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
            List of tool names to enable, or None for all tools (full profile)
        """
        profile = cls.TOOL_PROFILE.lower()
        return TOOL_PROFILES.get(profile, TOOL_PROFILES["lite"])

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
            "logging": {
                "level": cls.LOG_LEVEL
            },
            "features": {
                "auto_extract_entities": cls.AUTO_EXTRACT_ENTITIES,
                "session_briefing": cls.SESSION_BRIEFING,
                "briefing_verbosity": cls.BRIEFING_VERBOSITY,
                "briefing_recency_days": cls.BRIEFING_RECENCY_DAYS
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
