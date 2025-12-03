"""
Turso (libSQL) backend implementation for MemoryGraph.

Provides cloud-hosted SQLite-compatible storage with embedded replica support.
Users can create a free Turso database for persistent memory in Claude Code Web
and other remote environments.
"""

import asyncio
import logging
import os
import json
from typing import Any, Optional
from pathlib import Path

try:
    import libsql_experimental as libsql
except ImportError:
    libsql = None  # type: ignore

try:
    import networkx as nx
except ImportError:
    nx = None

from .base import GraphBackend
from ..models import DatabaseConnectionError, SchemaError

logger = logging.getLogger(__name__)


class TursoBackend(GraphBackend):
    """Turso/libSQL backend using same schema as SQLite."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        sync_url: Optional[str] = None,
        auth_token: Optional[str] = None,
    ):
        """
        Initialize Turso backend.

        Args:
            db_path: Path to local database file (for embedded replicas)
            sync_url: Turso database URL (e.g., libsql://your-db.turso.io)
            auth_token: Turso authentication token

        Raises:
            DatabaseConnectionError: If libsql or NetworkX not installed
        """
        if libsql is None:
            raise DatabaseConnectionError(
                "libsql-experimental is required for Turso backend. "
                "Install with: pip install memorygraphMCP[turso]"
            )

        if nx is None:
            raise DatabaseConnectionError(
                "NetworkX is required for Turso backend. "
                "Install with: pip install networkx"
            )

        # Configuration
        default_path = os.path.expanduser("~/.memorygraph/memory.db")
        self.db_path = db_path or os.getenv("MEMORY_TURSO_PATH", default_path)
        self.sync_url = sync_url or os.getenv("TURSO_DATABASE_URL")
        self.auth_token = auth_token or os.getenv("TURSO_AUTH_TOKEN")

        # Connection state
        self.conn = None
        self.graph: Optional[nx.DiGraph] = None  # type: ignore
        self._connected = False

        # Ensure directory exists for local file
        if self.db_path:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def connect(self) -> bool:
        """
        Establish connection to Turso database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            if self.sync_url and self.auth_token:
                # Embedded replica mode (local + sync)
                logger.info("Connecting to Turso with embedded replica...")
                self.conn = libsql.connect(
                    self.db_path,
                    sync_url=self.sync_url,
                    auth_token=self.auth_token,
                )
                # Initial sync (non-blocking)
                await asyncio.to_thread(self.conn.sync)
                logger.info(f"Connected to Turso (embedded replica at {self.db_path})")
            elif self.sync_url:
                # Remote-only mode
                logger.info("Connecting to Turso (remote-only)...")
                self.conn = libsql.connect(
                    database_url=self.sync_url,
                    auth_token=self.auth_token or "",
                )
                logger.info("Connected to Turso (remote)")
            else:
                # Local-only mode (same as SQLite)
                logger.info("Using Turso in local-only mode...")
                self.conn = libsql.connect(self.db_path)
                logger.info(f"Connected to local libSQL database at {self.db_path}")

            self.graph = nx.DiGraph()
            self._connected = True

            # Load existing graph into memory
            await self._load_graph_to_memory()

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Turso: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Turso: {e}")

    async def disconnect(self) -> None:
        """Close the database connection and sync if needed."""
        if self.conn:
            # Sync before closing (if embedded replica) - non-blocking
            if self.sync_url and self.auth_token:
                try:
                    await asyncio.to_thread(self.conn.sync)
                    logger.info("Synced to Turso before disconnect")
                except Exception as e:
                    logger.warning(f"Failed to sync before disconnect: {e}")

            # Sync graph to database before closing
            await self._sync_to_database()

            self.conn.close()
            self.conn = None
            self.graph = None
            self._connected = False
            logger.info("Turso connection closed")

    async def sync(self) -> None:
        """
        Manually sync embedded replica with Turso primary.

        Only applicable in embedded replica mode.
        """
        if self.conn and self.sync_url and self.auth_token:
            try:
                await asyncio.to_thread(self.conn.sync)
                logger.info("Synced with Turso primary")
            except Exception as e:
                logger.error(f"Failed to sync with Turso: {e}")
                raise DatabaseConnectionError(f"Sync failed: {e}")
        else:
            logger.warning("Sync not available (not in embedded replica mode)")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query against Turso database.

        Args:
            query: SQL query string
            parameters: Query parameters
            write: Whether this is a write operation

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseConnectionError: If not connected
        """
        if not self._connected or not self.conn:
            raise DatabaseConnectionError(
                "Not connected to Turso. Call connect() first."
            )

        params = parameters or {}

        try:
            # Wrap all blocking libsql operations in asyncio.to_thread
            def _execute_sync():
                cursor = self.conn.cursor()
                cursor.execute(query, params)

                if write:
                    self.conn.commit()

                # Return results
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                return []

            # Execute in thread pool
            result = await asyncio.to_thread(_execute_sync)

            # Sync after writes if embedded replica (non-blocking)
            if write and self.sync_url and self.auth_token:
                await asyncio.to_thread(self.conn.sync)

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query failed: {e}")

    async def initialize_schema(self) -> None:
        """
        Initialize database schema (same as SQLite backend).

        Raises:
            SchemaError: If schema initialization fails
        """
        logger.info("Initializing Turso schema...")

        if not self.conn:
            raise DatabaseConnectionError("Not connected to database")

        try:
            # Wrap all blocking operations in asyncio.to_thread
            def _initialize_sync():
                cursor = self.conn.cursor()

                # Create nodes table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS nodes (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        summary TEXT,
                        context TEXT,
                        importance REAL DEFAULT 0.5,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        tags TEXT
                    )
                """
                )

                # Create relationships table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS relationships (
                        id TEXT PRIMARY KEY,
                        from_id TEXT NOT NULL,
                        to_id TEXT NOT NULL,
                        type TEXT NOT NULL,
                        context TEXT,
                        strength REAL DEFAULT 0.5,
                        confidence REAL DEFAULT 0.8,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (from_id) REFERENCES nodes(id) ON DELETE CASCADE,
                        FOREIGN KEY (to_id) REFERENCES nodes(id) ON DELETE CASCADE
                    )
                """
                )

                # Create indexes for performance
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_nodes_created_at ON nodes(created_at)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type)"
                )

                # Create full-text search virtual table
                cursor.execute(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                        id UNINDEXED,
                        title,
                        content,
                        summary,
                        content='nodes',
                        content_rowid='rowid'
                    )
                """
                )

                # Create triggers to keep FTS in sync
                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS nodes_fts_insert AFTER INSERT ON nodes BEGIN
                        INSERT INTO nodes_fts(rowid, id, title, content, summary)
                        VALUES (new.rowid, new.id, new.title, new.content, new.summary);
                    END
                """
                )

                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS nodes_fts_update AFTER UPDATE ON nodes BEGIN
                        UPDATE nodes_fts SET
                            title = new.title,
                            content = new.content,
                            summary = new.summary
                        WHERE rowid = new.rowid;
                    END
                """
                )

                cursor.execute(
                    """
                    CREATE TRIGGER IF NOT EXISTS nodes_fts_delete AFTER DELETE ON nodes BEGIN
                        DELETE FROM nodes_fts WHERE rowid = old.rowid;
                    END
                """
                )

                self.conn.commit()

            # Execute schema initialization in thread pool
            await asyncio.to_thread(_initialize_sync)

            # Sync after schema initialization if embedded replica
            if self.sync_url and self.auth_token:
                await asyncio.to_thread(self.conn.sync)

            logger.info("Turso schema initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise SchemaError(f"Schema initialization failed: {e}")

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and connection status.

        Returns:
            Dictionary with health information
        """
        health_info = {
            "backend": "turso",
            "connected": self._connected,
            "database_path": self.db_path,
            "sync_enabled": bool(self.sync_url and self.auth_token),
            "mode": "embedded_replica"
            if (self.sync_url and self.auth_token)
            else ("remote" if self.sync_url else "local"),
        }

        if self._connected and self.conn:
            try:
                # Wrap blocking operations in asyncio.to_thread
                def _get_counts():
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT COUNT(*) as count FROM nodes")
                    node_result = cursor.fetchone()
                    node_count = node_result[0] if node_result else 0

                    cursor.execute("SELECT COUNT(*) as count FROM relationships")
                    rel_result = cursor.fetchone()
                    rel_count = rel_result[0] if rel_result else 0

                    return node_count, rel_count

                node_count, rel_count = await asyncio.to_thread(_get_counts)

                health_info["node_count"] = node_count
                health_info["relationship_count"] = rel_count
                health_info["status"] = "healthy"
            except Exception as e:
                health_info["status"] = "error"
                health_info["error"] = str(e)
        else:
            health_info["status"] = "disconnected"

        return health_info

    def backend_name(self) -> str:
        """Return the backend identifier."""
        return "turso"

    def supports_fulltext_search(self) -> bool:
        """Turso supports FTS5 full-text search (SQLite compatible)."""
        return True

    def supports_transactions(self) -> bool:
        """Turso supports ACID transactions."""
        return True

    # Helper methods (same as SQLite backend)

    async def _load_graph_to_memory(self) -> None:
        """Load graph from database into NetworkX graph."""
        if not self.conn or not self.graph:
            return

        try:
            # Wrap blocking operations in asyncio.to_thread
            def _load_sync():
                cursor = self.conn.cursor()

                # Load nodes
                cursor.execute("SELECT id, type, title FROM nodes")
                nodes = cursor.fetchall()

                # Load relationships
                cursor.execute("SELECT from_id, to_id, type FROM relationships")
                relationships = cursor.fetchall()

                return nodes, relationships

            nodes, relationships = await asyncio.to_thread(_load_sync)

            # Add to graph (NetworkX operations are fast, no need to thread)
            for row in nodes:
                self.graph.add_node(row[0], type=row[1], title=row[2])

            for row in relationships:
                self.graph.add_edge(row[0], row[1], type=row[2])

            logger.info(
                f"Loaded graph: {self.graph.number_of_nodes()} nodes, "
                f"{self.graph.number_of_edges()} edges"
            )

        except Exception as e:
            logger.warning(f"Failed to load graph to memory: {e}")

    async def _sync_to_database(self) -> None:
        """Sync NetworkX graph to database (for consistency)."""
        # In Turso backend, we primarily use database operations
        # This is here for compatibility with SQLite backend pattern
        pass
