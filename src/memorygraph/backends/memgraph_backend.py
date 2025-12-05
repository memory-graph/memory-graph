"""
Memgraph backend implementation for the Claude Code Memory Server.

This module provides Memgraph-specific implementation of the GraphBackend interface.
Memgraph uses the Bolt protocol and Cypher, so it can use the same driver as Neo4j
with some Cypher dialect adaptations.
"""

import logging
import os
from typing import Any, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError
from contextlib import asynccontextmanager

from .base import GraphBackend
from ..models import DatabaseConnectionError, SchemaError
from ..config import Config

logger = logging.getLogger(__name__)


class MemgraphBackend(GraphBackend):
    """Memgraph implementation of the GraphBackend interface."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: str = "",
        password: str = "",
        database: str = "memgraph"
    ):
        """
        Initialize Memgraph backend.

        Args:
            uri: Memgraph database URI (defaults to MEMORY_MEMGRAPH_URI env var)
            user: Database username (Memgraph Community has no auth by default)
            password: Database password (empty for Community Edition)
            database: Database name (default: 'memgraph')

        Note:
            Memgraph Community Edition has no authentication by default.
            Enterprise Edition supports authentication.
        """
        self.uri = uri or os.getenv("MEMORY_MEMGRAPH_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("MEMORY_MEMGRAPH_USER", "")
        self.password = password or os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")
        self.database = database
        self.driver: Optional[AsyncDriver] = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish async connection to Memgraph database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            # Memgraph uses same Bolt protocol as Neo4j
            # Community Edition: auth is typically empty tuple or ("", "")
            auth = (self.user, self.password) if self.user or self.password else None

            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=auth,
                max_connection_lifetime=30 * 60,
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0
            )

            # Verify connectivity
            await self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Successfully connected to Memgraph at {self.uri}")
            return True

        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Memgraph: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Memgraph: {e}")
        except AuthError as e:
            logger.error(f"Authentication failed for Memgraph: {e}")
            raise DatabaseConnectionError(f"Authentication failed for Memgraph: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Memgraph: {e}")
            raise DatabaseConnectionError(f"Unexpected error connecting to Memgraph: {e}")

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            self._connected = False
            logger.info("Memgraph connection closed")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: The Cypher query string
            parameters: Query parameters for parameterized queries
            write: Whether this is a write operation (default: False)

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseConnectionError: If not connected or query fails
        """
        if not self._connected or not self.driver:
            raise DatabaseConnectionError("Not connected to Memgraph. Call connect() first.")

        params = parameters or {}

        # Adapt Cypher for Memgraph dialect differences
        adapted_query = self._adapt_cypher(query)

        try:
            async with self._session() as session:
                # Memgraph doesn't distinguish between read/write transactions in the same way
                # We'll use execute_write for both to ensure consistency
                result = await session.execute_write(self._run_query_async, adapted_query, params)
                return result
        except Neo4jError as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}")

    @asynccontextmanager
    async def _session(self):
        """Async context manager for Memgraph session."""
        if not self.driver:
            raise DatabaseConnectionError("Not connected to Memgraph. Call connect() first.")

        session = self.driver.session()
        try:
            yield session
        finally:
            await session.close()

    @staticmethod
    async def _run_query_async(tx, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Helper method to run a query within an async transaction.

        Args:
            tx: Transaction object
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        result = await tx.run(query, parameters)
        records = await result.data()
        return records

    def _adapt_cypher(self, query: str) -> str:
        """
        Adapt Cypher query for Memgraph dialect differences.

        Args:
            query: Original Cypher query

        Returns:
            Adapted query for Memgraph

        Note:
            Main differences:
            - FULLTEXT INDEX syntax is different
            - Some constraint syntax differs
            - CALL dbms.* procedures may not be available
        """
        # Memgraph uses CREATE TEXT INDEX instead of CREATE FULLTEXT INDEX
        # But it doesn't support fulltext the same way, so we skip it
        if "CREATE FULLTEXT INDEX" in query:
            logger.debug(f"Skipping fulltext index creation for Memgraph (not fully supported)")
            return "RETURN 1"  # No-op query

        # Memgraph uses different constraint syntax pre-v2.11
        # But modern Memgraph should support standard syntax
        return query

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        Raises:
            SchemaError: If schema initialization fails
        """
        logger.info("Initializing Memgraph schema for Claude Memory...")

        # Create constraints (Memgraph syntax)
        constraints = [
            "CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE",
            # Note: Relationship constraints may not be supported in all Memgraph versions
        ]

        # Create indexes for performance
        indexes = [
            "CREATE INDEX ON :Memory(type)",
            "CREATE INDEX ON :Memory(created_at)",
            "CREATE INDEX ON :Memory(tags)",
            "CREATE INDEX ON :Memory(importance)",
            "CREATE INDEX ON :Memory(confidence)",
            # Note: Memgraph doesn't support multi-property indexes the same way
        ]

        # Conditional multi-tenant indexes (Phase 1)
        if Config.is_multi_tenant_mode():
            multitenant_indexes = [
                "CREATE INDEX ON :Memory(context_tenant_id)",
                "CREATE INDEX ON :Memory(context_team_id)",
                "CREATE INDEX ON :Memory(context_visibility)",
                "CREATE INDEX ON :Memory(context_created_by)",
                "CREATE INDEX ON :Memory(version)",
            ]
            indexes.extend(multitenant_indexes)
            logger.info("Multi-tenant mode enabled, adding tenant indexes")

        # Execute schema creation
        for constraint in constraints:
            try:
                await self.execute_query(constraint, write=True)
                logger.debug(f"Created constraint: {constraint}")
            except DatabaseConnectionError as e:
                # Memgraph may not support all constraint types
                if "already exists" not in str(e).lower() and "not supported" not in str(e).lower():
                    logger.warning(f"Failed to create constraint (may not be supported): {e}")

        for index in indexes:
            try:
                await self.execute_query(index, write=True)
                logger.debug(f"Created index: {index}")
            except DatabaseConnectionError as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create index: {e}")

        logger.info("Schema initialization completed")

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "memgraph",
            "uri": self.uri,
            "database": self.database
        }

        if self._connected:
            try:
                # Get basic node count
                count_query = "MATCH (m:Memory) RETURN count(m) as count"
                count_result = await self.execute_query(count_query, write=False)
                if count_result:
                    health_info["statistics"] = {
                        "memory_count": count_result[0].get("count", 0)
                    }

                # Try to get Memgraph version (if available)
                # Note: Memgraph may not have dbms.components()
                health_info["version"] = "unknown"
            except Exception as e:
                logger.warning(f"Could not get detailed health info: {e}")
                health_info["warning"] = str(e)

        return health_info

    def backend_name(self) -> str:
        """Return the name of this backend implementation."""
        return "memgraph"

    def supports_fulltext_search(self) -> bool:
        """
        Check if this backend supports full-text search.

        Note:
            Memgraph has limited full-text search support compared to Neo4j.
            Text indexing is available but not full FULLTEXT INDEX functionality.
        """
        return False  # Limited support

    def supports_transactions(self) -> bool:
        """Check if this backend supports ACID transactions."""
        return True

    @classmethod
    async def create(
        cls,
        uri: Optional[str] = None,
        user: str = "",
        password: str = "",
        database: str = "memgraph"
    ) -> "MemgraphBackend":
        """
        Factory method to create and connect to a Memgraph backend.

        Args:
            uri: Memgraph database URI
            user: Database username
            password: Database password
            database: Database name

        Returns:
            Connected MemgraphBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        backend = cls(uri, user, password, database)
        await backend.connect()
        return backend
