"""
SQLite fallback backend implementation for MemoryGraph.

This module provides a zero-dependency fallback using SQLite for persistence
and NetworkX for graph operations. This enables the memory server to work
without requiring Neo4j or Memgraph installation.
"""

import logging
import os
import json
import sqlite3
import uuid
from typing import Any, Optional
from pathlib import Path

try:
    import networkx as nx
except ImportError:
    nx = None

from .base import GraphBackend
from ..models import DatabaseConnectionError, SchemaError
from ..config import Config

logger = logging.getLogger(__name__)


class SQLiteFallbackBackend(GraphBackend):
    """SQLite + NetworkX fallback implementation of the GraphBackend interface."""

    def __init__(
        self,
        db_path: Optional[str] = None
    ):
        """
        Initialize SQLite fallback backend.

        Args:
            db_path: Path to SQLite database file (defaults to ~/.memorygraph/memory.db)

        Raises:
            DatabaseConnectionError: If NetworkX is not installed
        """
        if nx is None:
            raise DatabaseConnectionError(
                "NetworkX is required for SQLite fallback backend. "
                "Install with: pip install networkx"
            )

        default_path = os.path.expanduser("~/.memorygraph/memory.db")
        resolved_path = db_path or os.getenv("MEMORY_SQLITE_PATH", default_path)
        self.db_path: str = resolved_path if resolved_path else default_path
        self.conn: Optional[sqlite3.Connection] = None
        self.graph: Optional[nx.DiGraph] = None  # type: ignore[misc,no-any-unimported]
        self._connected = False

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def connect(self) -> bool:
        """
        Establish connection to SQLite database and initialize graph.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self.graph = nx.DiGraph()
            self._connected = True

            # Load existing graph into memory
            await self._load_graph_to_memory()

            logger.info(f"Successfully connected to SQLite database at {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise DatabaseConnectionError(f"Failed to connect to SQLite: {e}")

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self.conn:
            # Sync graph to SQLite before closing
            await self._sync_to_sqlite()
            self.conn.close()
            self.conn = None
            self.graph = None
            self._connected = False
            logger.info("SQLite connection closed")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher-like query translated to SQLite/NetworkX operations.

        Args:
            query: Cypher-style query string
            parameters: Query parameters
            write: Whether this is a write operation

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseConnectionError: If not connected
            NotImplementedError: For complex Cypher queries

        Note:
            This is a simplified implementation that supports basic operations.
            Complex Cypher queries will raise NotImplementedError.
        """
        if not self._connected or not self.conn:
            raise DatabaseConnectionError("Not connected to SQLite. Call connect() first.")

        params = parameters or {}

        # For schema operations, we can execute directly
        if query.strip().upper().startswith(("CREATE", "DROP", "ALTER")):
            try:
                cursor = self.conn.cursor()
                # SQLite doesn't support Cypher, so we'll handle schema separately
                return []
            except sqlite3.Error as e:
                raise DatabaseConnectionError(f"SQLite query failed: {e}")

        # For data operations, translate to SQLite/NetworkX
        # This is a simplified implementation - full Cypher translation would be complex
        logger.warning("Direct Cypher execution not supported in SQLite backend. Use database.py methods.")
        return []

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes.

        Raises:
            SchemaError: If schema initialization fails
        """
        logger.info("Initializing SQLite schema for Claude Memory...")

        if not self.conn:
            raise SchemaError("Not connected to database")

        cursor = self.conn.cursor()

        try:
            # Create nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    from_id TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    rel_type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_id) REFERENCES nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES nodes(id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_created ON nodes(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(from_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships(to_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(rel_type)")

            # Conditional multi-tenant indexes (Phase 1)
            if Config.is_multi_tenant_mode():
                self._create_multitenant_indexes(cursor)

            # Create FTS5 virtual table for full-text search
            try:
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                        id,
                        title,
                        content,
                        summary,
                        content='nodes',
                        content_rowid='rowid'
                    )
                """)
                logger.debug("Created FTS5 table for full-text search")
            except sqlite3.Error as e:
                logger.warning(f"Could not create FTS5 table (may not be available): {e}")

            self.conn.commit()
            logger.info("Schema initialization completed")

        except sqlite3.Error as e:
            self.conn.rollback()
            raise SchemaError(f"Failed to initialize schema: {e}")

    def _create_multitenant_indexes(self, cursor: sqlite3.Cursor) -> None:
        """
        Create indexes for multi-tenant queries.

        Only called when MEMORY_MULTI_TENANT_MODE=true. These indexes optimize
        queries filtering by tenant_id, team_id, visibility, and created_by.

        Args:
            cursor: SQLite cursor for executing index creation

        Note:
            Context fields are stored as JSON in properties column, so we use
            JSON extraction for indexing (requires SQLite 3.9.0+)
        """
        logger.info("Creating multi-tenant indexes...")

        try:
            # Tenant index - for tenant isolation queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_tenant
                ON nodes(json_extract(properties, '$.context.tenant_id'))
                WHERE label = 'Memory'
            """)

            # Team index - for team-scoped queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_team
                ON nodes(json_extract(properties, '$.context.team_id'))
                WHERE label = 'Memory'
            """)

            # Visibility index - for access control filtering
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_visibility
                ON nodes(json_extract(properties, '$.context.visibility'))
                WHERE label = 'Memory'
            """)

            # Created_by index - for user-specific queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_created_by
                ON nodes(json_extract(properties, '$.context.created_by'))
                WHERE label = 'Memory'
            """)

            # Composite index for common query pattern (tenant + visibility)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_tenant_visibility
                ON nodes(
                    json_extract(properties, '$.context.tenant_id'),
                    json_extract(properties, '$.context.visibility')
                )
                WHERE label = 'Memory'
            """)

            # Version index for optimistic locking
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_version
                ON nodes(json_extract(properties, '$.version'))
                WHERE label = 'Memory'
            """)

            logger.info("Multi-tenant indexes created successfully")

        except sqlite3.Error as e:
            logger.warning(f"Could not create some multi-tenant indexes: {e}")
            # Don't fail schema initialization if indexes fail
            # (e.g., older SQLite versions without JSON support)

    async def _load_graph_to_memory(self) -> None:
        """Load graph data from SQLite into NetworkX graph."""
        if not self.conn or not self.graph:
            return

        cursor = self.conn.cursor()

        # Load nodes
        cursor.execute("SELECT id, label, properties FROM nodes")
        for row in cursor.fetchall():
            node_id = row[0]
            label = row[1]
            properties = json.loads(row[2])
            self.graph.add_node(node_id, label=label, **properties)

        # Load relationships
        cursor.execute("SELECT id, from_id, to_id, rel_type, properties FROM relationships")
        for row in cursor.fetchall():
            rel_id = row[0]
            from_id = row[1]
            to_id = row[2]
            rel_type = row[3]
            properties = json.loads(row[4])
            self.graph.add_edge(from_id, to_id, id=rel_id, type=rel_type, **properties)

        logger.debug(f"Loaded {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges into memory")

    async def _sync_to_sqlite(self) -> None:
        """Sync in-memory NetworkX graph to SQLite database."""
        if not self.conn or not self.graph:
            return

        # This is a simplified sync - in production, we'd track changes
        # For now, we'll rely on direct SQLite operations for writes
        logger.debug("Graph sync to SQLite (using direct operations)")

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "sqlite",
            "db_path": self.db_path
        }

        if self._connected and self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM nodes WHERE label = 'Memory'")
                count = cursor.fetchone()[0]

                health_info["statistics"] = {
                    "memory_count": count
                }

                # Get SQLite version
                cursor.execute("SELECT sqlite_version()")
                health_info["version"] = cursor.fetchone()[0]

                # Get database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                health_info["database_size_bytes"] = db_size

            except Exception as e:
                logger.warning(f"Could not get detailed health info: {e}")
                health_info["warning"] = str(e)

        return health_info

    def backend_name(self) -> str:
        """Return the name of this backend implementation."""
        return "sqlite"

    def supports_fulltext_search(self) -> bool:
        """
        Check if this backend supports full-text search.

        Returns:
            True if FTS5 is available in SQLite
        """
        if not self.conn:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='nodes_fts'")
            result = cursor.fetchone()
            return bool(result[0] > 0) if result else False
        except Exception:
            return False

    def supports_transactions(self) -> bool:
        """Check if this backend supports ACID transactions."""
        return True  # SQLite supports transactions

    @classmethod
    async def create(cls, db_path: Optional[str] = None) -> "SQLiteFallbackBackend":
        """
        Factory method to create and connect to a SQLite backend.

        Args:
            db_path: Path to SQLite database file

        Returns:
            Connected SQLiteFallbackBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        backend = cls(db_path)
        await backend.connect()
        return backend

    # Helper methods for direct database operations (used by MemoryDatabase)

    def execute_sync(self, query: str, parameters: Optional[tuple[Any, ...]] = None) -> list[dict[str, Any]]:
        """
        Execute a synchronous SQL query (for internal use).

        Args:
            query: SQL query string
            parameters: Query parameters as tuple

        Returns:
            List of result rows as dictionaries
        """
        if not self.conn:
            raise DatabaseConnectionError("Not connected to SQLite")

        cursor = self.conn.cursor()
        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)

        # Convert rows to dictionaries
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def commit(self) -> None:
        """Commit current transaction."""
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        if self.conn:
            self.conn.rollback()
