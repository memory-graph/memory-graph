"""
Claude Code Memory Server

A graph-based MCP server that provides intelligent memory capabilities for Claude Code,
enabling persistent knowledge tracking, relationship mapping, and contextual development assistance.

Supports multiple backends: SQLite (default), Neo4j, and Memgraph.
"""

__version__ = "0.10.0"
__author__ = "Gregory Dickson"
__email__ = "gregory@example.com"

from .server import ClaudeMemoryServer
from .models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    MemoryNode,
    MemoryContext,
    MemoryError,
    MemoryNotFoundError,
    RelationshipError,
    ValidationError,
    DatabaseConnectionError,
    SchemaError,
    NotFoundError,
    BackendError,
    ConfigurationError,
)

__all__ = [
    "ClaudeMemoryServer",
    "Memory",
    "MemoryType",
    "Relationship",
    "RelationshipType",
    "MemoryNode",
    "MemoryContext",
    "MemoryError",
    "MemoryNotFoundError",
    "RelationshipError",
    "ValidationError",
    "DatabaseConnectionError",
    "SchemaError",
    "NotFoundError",
    "BackendError",
    "ConfigurationError",
]