"""
Backend abstraction layer for the Claude Code Memory Server.

This package provides a unified interface for different graph database backends,
allowing the memory server to work with Neo4j, Memgraph, or SQLite.
"""

from .base import GraphBackend
from .factory import BackendFactory

# Backend classes are imported lazily via the factory to avoid
# import-time dependencies on optional packages (neo4j, etc.)
# Import them explicitly when needed:
#   from claude_memory.backends.neo4j_backend import Neo4jBackend
#   from claude_memory.backends.memgraph_backend import MemgraphBackend
#   from claude_memory.backends.sqlite_fallback import SQLiteFallbackBackend

__all__ = [
    "GraphBackend",
    "BackendFactory",
]
