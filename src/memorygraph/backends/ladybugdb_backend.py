"""
LadybugDB backend implementation for the Claude Code Memory Server.

This module provides the LadybugDB-specific implementation of the GraphBackend interface.
LadybugDB is a graph database that uses Cypher queries, similar to Kuzu.
"""

import logging
import os
from typing import Any, Optional, List, Tuple, Dict
from pathlib import Path

try:
    import real_ladybug as lb
    LADYBUGDB_AVAILABLE = True
except ImportError:
    lb = None  # type: ignore
    LADYBUGDB_AVAILABLE = False

from .base import GraphBackend
from ..models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    RelationshipProperties,
    SearchQuery,
    MemoryContext,
    MemoryNode,
    DatabaseConnectionError,
    SchemaError,
    ValidationError,
    RelationshipError,
)
from ..config import Config
from datetime import datetime, timezone
import uuid
import json

logger = logging.getLogger(__name__)


class LadybugDBBackend(GraphBackend):
    """LadybugDB implementation of the GraphBackend interface."""

    def __init__(self, db_path: Optional[str] = None, graph_name: str = "memorygraph"):
        """
        Initialize LadybugDB backend.

        Args:
            db_path: Path to database file (defaults to MEMORY_LADYBUGDB_PATH env var or ~/.memorygraph/memory.lbdb)
            graph_name: Name of the graph database (defaults to 'memorygraph')

        Raises:
            ImportError: If real_ladybug package is not installed.
        """
        if not LADYBUGDB_AVAILABLE:
            raise ImportError(
                "LadybugDB backend requires real_ladybug package. "
                "Install it with: pip install real-ladybug"
            )
        if db_path is None:
            db_path = os.getenv("MEMORY_LADYBUGDB_PATH")
            if db_path is None:
                # Default to ~/.memorygraph/memory.lbdb
                home = Path.home()
                db_dir = home / ".memorygraph"
                db_dir.mkdir(parents=True, exist_ok=True)
                db_path = str(db_dir / "memory.lbdb")

        self.db_path = db_path
        self.graph_name = graph_name
        self.client = None
        self.graph = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish connection to LadybugDB database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            # Create LadybugDB database
            self.client = lb.Database(self.db_path)

            # Create connection for executing queries
            self.graph = lb.Connection(self.client)

            # Install and load JSON extension
            try:
                self.graph.execute("INSTALL JSON")
                self.graph.execute("LOAD EXTENSION JSON")
                logger.info("Loaded JSON extension for LadybugDB")
            except Exception as e:
                logger.warning(f"Failed to load JSON extension: {e}")

            # Install and load FTS extension, then create fulltext index using LadybugDB syntax
            try:
                self.graph.execute("INSTALL FTS")
                self.graph.execute("LOAD EXTENSION FTS")
                logger.info("Loaded FTS extension for LadybugDB")
            except Exception as e:
                logger.warning(f"Failed to load FTS extension: {e}")

            self._connected = True

            logger.info(f"Successfully connected to LadybugDB at {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to LadybugDB: {e}")
            raise DatabaseConnectionError(f"Failed to connect to LadybugDB: {e}")

    async def disconnect(self) -> None:
        """
        Close the LadybugDB connection and clean up resources.
        """
        if self.graph:
            self.graph.close()
            self.graph = None
        if self.client:
            self.client.close()
            self.client = None
            self._connected = False
            logger.info("Disconnected from LadybugDB")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters
            write: Whether this is a write operation

        Returns:
            List of result dictionaries
        """
        if not self._connected or not self.graph:
            raise DatabaseConnectionError("Not connected to LadybugDB")

        try:
            # Execute query using LadybugDB's connection with parameters
            result = self.graph.execute(query, parameters)

            # Convert result to list of dictionaries using get_as_pl() for consistent format
            # Polars is used instead of pandas for better performance
            rows = []
            if isinstance(result, list):
                # Handle multiple result sets (e.g., from multiple queries)
                for single_result in result:
                    df = single_result.get_as_pl()
                    rows.extend(df.to_dicts())
            else:
                # Handle single result set
                df = result.get_as_pl()
                rows = df.to_dicts()

            return rows

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise SchemaError(f"Query execution failed: {e}")

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including node and rel tables.

        LadybugDB requires NODE TABLE and REL TABLE to be created before adding data.
        LadybugDB does not support CREATE INDEX or CREATE CONSTRAINT commands.

        This should be idempotent and safe to call multiple times.

        Raises:
            SchemaError: If schema initialization fails
        """
        if not self._connected or not self.graph:
            raise DatabaseConnectionError("Not connected to LadybugDB")

        try:
            # LadybugDB requires NODE TABLE and REL TABLE to exist first
            # These tables must be created before any nodes/relationships can be added
            schema_queries = [
                # Create Memory node table
                """
                CREATE NODE TABLE IF NOT EXISTS Memory(
                    id UUID PRIMARY KEY,
                    type STRING,
                    title STRING,
                    content STRING,
                    summary STRING,
                    tags JSON,
                    importance DOUBLE,
                    confidence DOUBLE,
                    usage_count INT,
                    effectiveness DOUBLE,
                    last_accessed TIMESTAMP,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    version INT,
                    updated_by STRING,
                    context_project_path STRING,
                    context_file_path STRING,
                    context_line_start INT,
                    context_line_end INT,
                    context_commit_hash STRING,
                    context_branch STRING,
                    metadata STRING
                )
                """,
                # Create relationship table for connections between Memory nodes
                """
                CREATE REL TABLE IF NOT EXISTS REL(
                    FROM Memory TO Memory,
                    id UUID,
                    type STRING,
                    properties STRING,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    metadata STRING
                )
                """,
            ]

            for query in schema_queries:
                await self.execute_query(query, write=True)

            # Note: LadybugDB does not support CREATE INDEX commands
            # The primary keys on node tables provide indexing automatically

        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise SchemaError(f"Schema initialization failed: {e}")

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "ladybugdb",
            "backend_name": self.backend_name(),
            "supports_fulltext_search": self.supports_fulltext_search(),
            "supports_transactions": self.supports_transactions(),
        }

        if self._connected and self.graph:
            try:
                # Simple health check query
                result = await self.execute_query("RETURN 'healthy' as status")
                health_info["status"] = result[0]["status"] if result else "unknown"
                health_info["healthy"] = True
            except Exception as e:
                health_info["healthy"] = False
                health_info["error"] = str(e)
        else:
            health_info["healthy"] = False
            health_info["error"] = "Not connected"

        return health_info

    def backend_name(self) -> str:
        """
        Return the name of this backend implementation.

        Returns:
            Backend name
        """
        return "ladybugdb"

    def supports_fulltext_search(self) -> bool:
        """
        Check if this backend supports full-text search.

        Returns:
            True if full-text search is supported
        """
        # LadybugDB may support full-text search, but we'll be conservative
        return False

    def supports_transactions(self) -> bool:
        """
        Check if this backend supports ACID transactions.

        Returns:
            True if transactions are supported
        """
        # LadybugDB likely supports transactions
        return True

    def is_cypher_capable(self) -> bool:
        """LadybugDB supports native Cypher query execution."""
        return True

    # Additional methods would be implemented here following the GraphBackend interface
    # For brevity, only the core methods are shown
