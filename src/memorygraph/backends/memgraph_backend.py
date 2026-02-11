"""
Memgraph backend implementation for the Claude Code Memory Server.

Memgraph uses the Bolt protocol and Cypher via the same Neo4j driver
with some Cypher dialect adaptations.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable

from ..config import Config
from ..models import DatabaseConnectionError
from .base import GraphBackend

logger = logging.getLogger(__name__)


class MemgraphBackend(GraphBackend):
    """Memgraph implementation of the GraphBackend interface."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "memgraph",
    ):
        """Initialize Memgraph backend.

        Note: Memgraph Community Edition has no authentication by default.
        Enterprise Edition supports authentication.
        """
        self.uri = uri if uri is not None else Config.MEMGRAPH_URI
        self.user = user if user is not None else Config.MEMGRAPH_USER
        self.password = password if password is not None else Config.MEMGRAPH_PASSWORD
        self.database = database
        self.driver: Optional[AsyncDriver] = None
        self._connected = False

    async def connect(self) -> bool:
        """Establish async connection to Memgraph database."""
        try:
            auth = (self.user, self.password) if self.user or self.password else None

            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=auth,
                max_connection_lifetime=30 * 60,
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0,
            )

            await self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Successfully connected to Memgraph at {self.uri}")
            return True

        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Memgraph: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Memgraph: {e}") from e
        except AuthError as e:
            logger.error(f"Authentication failed for Memgraph: {e}")
            raise DatabaseConnectionError(f"Authentication failed for Memgraph: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error connecting to Memgraph: {e}")
            raise DatabaseConnectionError(f"Unexpected error connecting to Memgraph: {e}") from e

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
        write: bool = False,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query adapted for the Memgraph dialect."""
        if not self._connected or not self.driver:
            raise DatabaseConnectionError(
                "Connection failed: not connected to Memgraph (call connect() first)"
            )

        params = parameters or {}
        adapted_query = self._adapt_cypher(query)

        try:
            async with self._session() as session:
                return await session.execute_write(self._run_query_async, adapted_query, params)
        except Neo4jError as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}") from e

    @asynccontextmanager
    async def _session(self):
        """Async context manager for Memgraph session."""
        if not self.driver:
            raise DatabaseConnectionError(
                "Connection failed: not connected to Memgraph (call connect() first)"
            )

        session = self.driver.session()
        try:
            yield session
        finally:
            await session.close()

    @staticmethod
    async def _run_query_async(tx, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        """Run a query within an async transaction and return records."""
        result = await tx.run(query, parameters)
        return await result.data()

    def _adapt_cypher(self, query: str) -> str:
        """Adapt Cypher query for Memgraph dialect differences.

        Memgraph does not support FULLTEXT INDEX syntax, so those queries
        are replaced with a no-op. Other Cypher is passed through unchanged.
        """
        if "CREATE FULLTEXT INDEX" in query:
            logger.debug("Skipping fulltext index creation for Memgraph (not supported)")
            return "RETURN 1"

        return query

    async def initialize_schema(self) -> None:
        """Initialize database schema including indexes and constraints."""
        logger.info("Initializing Memgraph schema for Claude Memory...")

        constraints = [
            "CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX ON :Memory(type)",
            "CREATE INDEX ON :Memory(created_at)",
            "CREATE INDEX ON :Memory(tags)",
            "CREATE INDEX ON :Memory(importance)",
            "CREATE INDEX ON :Memory(confidence)",
        ]

        if Config.is_multi_tenant_mode():
            indexes.extend([
                "CREATE INDEX ON :Memory(context_tenant_id)",
                "CREATE INDEX ON :Memory(context_team_id)",
                "CREATE INDEX ON :Memory(context_visibility)",
                "CREATE INDEX ON :Memory(context_created_by)",
                "CREATE INDEX ON :Memory(version)",
            ])
            logger.info("Multi-tenant mode enabled, adding tenant indexes")

        for statement in constraints + indexes:
            await self._execute_schema_statement(statement)

        logger.info("Schema initialization completed")

    async def _execute_schema_statement(self, statement: str) -> None:
        """Execute a single schema statement, ignoring 'already exists' errors."""
        try:
            await self.execute_query(statement, write=True)
            logger.debug(f"Executed schema statement: {statement}")
        except DatabaseConnectionError as e:
            error_msg = str(e).lower()
            if "already exists" not in error_msg and "not supported" not in error_msg:
                logger.warning(f"Failed to execute schema statement: {e}")

    async def health_check(self) -> dict[str, Any]:
        """Check backend health and return status information."""
        health_info = {
            "connected": self._connected,
            "backend_type": "memgraph",
            "uri": self.uri,
            "database": self.database,
        }

        if self._connected:
            try:
                count_result = await self.execute_query(
                    "MATCH (m:Memory) RETURN count(m) as count", write=False
                )
                if count_result:
                    health_info["statistics"] = {
                        "memory_count": count_result[0].get("count", 0)
                    }
                health_info["version"] = "unknown"
            except Exception as e:
                logger.warning(f"Could not get detailed health info: {e}")
                health_info["warning"] = str(e)

        return health_info

    def backend_name(self) -> str:
        """Return the name of this backend implementation."""
        return "memgraph"

    def supports_fulltext_search(self) -> bool:
        """Memgraph does not support full FULLTEXT INDEX functionality."""
        return False

    def supports_transactions(self) -> bool:
        """Check if this backend supports ACID transactions."""
        return True

    def is_cypher_capable(self) -> bool:
        """Memgraph supports native Cypher query execution."""
        return True

    @classmethod
    async def create(
        cls,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "memgraph",
    ) -> "MemgraphBackend":
        """Factory method to create and connect to a Memgraph backend."""
        backend = cls(uri, user, password, database)
        await backend.connect()
        return backend
