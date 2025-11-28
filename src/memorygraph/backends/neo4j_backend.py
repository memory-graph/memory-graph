"""
Neo4j backend implementation for the Claude Code Memory Server.

This module provides the Neo4j-specific implementation of the GraphBackend interface,
wrapping the existing Neo4j connection and query logic.
"""

import logging
import os
from typing import Any, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError
from contextlib import asynccontextmanager

from .base import GraphBackend
from ..models import DatabaseConnectionError, SchemaError

logger = logging.getLogger(__name__)


class Neo4jBackend(GraphBackend):
    """Neo4j implementation of the GraphBackend interface."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j"
    ):
        """
        Initialize Neo4j backend.

        Args:
            uri: Neo4j database URI (defaults to MEMORY_NEO4J_URI or NEO4J_URI env var)
            user: Database username (defaults to MEMORY_NEO4J_USER or NEO4J_USER env var)
            password: Database password (defaults to MEMORY_NEO4J_PASSWORD or NEO4J_PASSWORD env var)
            database: Database name (defaults to 'neo4j')

        Raises:
            DatabaseConnectionError: If password is not provided
        """
        self.uri = uri or os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
        self.database = database
        self.driver: Optional[AsyncDriver] = None
        self._connected = False

        if not self.password:
            raise DatabaseConnectionError(
                "Neo4j password must be provided via parameter or MEMORY_NEO4J_PASSWORD/NEO4J_PASSWORD env var"
            )

    async def connect(self) -> bool:
        """
        Establish async connection to Neo4j database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0
            )

            # Verify connectivity
            await self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True

        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Neo4j: {e}")
        except AuthError as e:
            logger.error(f"Authentication failed for Neo4j: {e}")
            raise DatabaseConnectionError(f"Authentication failed for Neo4j: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise DatabaseConnectionError(f"Unexpected error connecting to Neo4j: {e}")

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            self._connected = False
            logger.info("Neo4j connection closed")

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
            raise DatabaseConnectionError("Not connected to Neo4j. Call connect() first.")

        params = parameters or {}

        try:
            async with self._session() as session:
                if write:
                    result = await session.execute_write(self._run_query_async, query, params)
                else:
                    result = await session.execute_read(self._run_query_async, query, params)
                return result
        except Neo4jError as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}")

    @asynccontextmanager
    async def _session(self):
        """Async context manager for Neo4j session."""
        if not self.driver:
            raise DatabaseConnectionError("Not connected to Neo4j. Call connect() first.")

        session = self.driver.session(database=self.database)
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

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        Raises:
            SchemaError: If schema initialization fails
        """
        logger.info("Initializing Neo4j schema for Claude Memory...")

        # Create constraints
        constraints = [
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR (r:RELATIONSHIP) REQUIRE r.id IS UNIQUE",
        ]

        # Create indexes for performance
        indexes = [
            "CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type)",
            "CREATE INDEX memory_created_at_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
            "CREATE INDEX memory_tags_index IF NOT EXISTS FOR (m:Memory) ON (m.tags)",
            "CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS FOR (m:Memory) ON EACH [m.title, m.content, m.summary]",
            "CREATE INDEX memory_importance_index IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
            "CREATE INDEX memory_confidence_index IF NOT EXISTS FOR (m:Memory) ON (m.confidence)",
            "CREATE INDEX memory_project_path_index IF NOT EXISTS FOR (m:Memory) ON (m.context_project_path)",
        ]

        # Execute schema creation
        for constraint in constraints:
            try:
                await self.execute_query(constraint, write=True)
                logger.debug(f"Created constraint: {constraint}")
            except DatabaseConnectionError as e:
                if "already exists" not in str(e).lower():
                    raise SchemaError(f"Failed to create constraint: {e}")

        for index in indexes:
            try:
                await self.execute_query(index, write=True)
                logger.debug(f"Created index: {index}")
            except DatabaseConnectionError as e:
                if "already exists" not in str(e).lower():
                    raise SchemaError(f"Failed to create index: {e}")

        logger.info("Schema initialization completed")

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "neo4j",
            "uri": self.uri,
            "database": self.database
        }

        if self._connected:
            try:
                # Try to get version and basic statistics
                query = """
                CALL dbms.components() YIELD name, versions, edition
                RETURN name, versions[0] as version, edition
                """
                result = await self.execute_query(query, write=False)
                if result:
                    health_info["version"] = result[0].get("version", "unknown")
                    health_info["edition"] = result[0].get("edition", "unknown")

                # Get basic node count
                count_query = "MATCH (m:Memory) RETURN count(m) as count"
                count_result = await self.execute_query(count_query, write=False)
                if count_result:
                    health_info["statistics"] = {
                        "memory_count": count_result[0].get("count", 0)
                    }
            except Exception as e:
                logger.warning(f"Could not get detailed health info: {e}")
                health_info["warning"] = str(e)

        return health_info

    def backend_name(self) -> str:
        """Return the name of this backend implementation."""
        return "neo4j"

    def supports_fulltext_search(self) -> bool:
        """Check if this backend supports full-text search."""
        return True

    def supports_transactions(self) -> bool:
        """Check if this backend supports ACID transactions."""
        return True

    @classmethod
    async def create(
        cls,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j"
    ) -> "Neo4jBackend":
        """
        Factory method to create and connect to a Neo4j backend.

        Args:
            uri: Neo4j database URI
            user: Database username
            password: Database password
            database: Database name

        Returns:
            Connected Neo4jBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        backend = cls(uri, user, password, database)
        await backend.connect()
        return backend
