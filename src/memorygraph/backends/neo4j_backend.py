"""Neo4j backend implementation for the Claude Code Memory Server."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable

from ..config import Config
from ..models import DatabaseConnectionError, SchemaError
from .base import GraphBackend

logger = logging.getLogger(__name__)


class Neo4jBackend(GraphBackend):
    """Neo4j implementation of the GraphBackend interface."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ):
        self.uri = uri if uri is not None else Config.NEO4J_URI
        self.user = user if user is not None else Config.NEO4J_USER
        self.password = password if password is not None else Config.NEO4J_PASSWORD
        self.database = database
        self.driver: Optional[AsyncDriver] = None
        self._connected = False

        if not self.password:
            raise DatabaseConnectionError(
                "Neo4j password must be provided via parameter or MEMORY_NEO4J_PASSWORD/NEO4J_PASSWORD env var"
            )

    async def connect(self) -> bool:
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0,
            )
            await self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True

        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Neo4j: {e}") from e
        except AuthError as e:
            logger.error(f"Authentication failed for Neo4j: {e}")
            raise DatabaseConnectionError(
                f"Authentication failed for Neo4j: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise DatabaseConnectionError(
                f"Unexpected error connecting to Neo4j: {e}"
            ) from e

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
        write: bool = False,
    ) -> list[dict[str, Any]]:
        if not self._connected or not self.driver:
            raise DatabaseConnectionError(
                "Connection failed: not connected to Neo4j (call connect() first)"
            )

        params = parameters or {}

        try:
            async with self._session() as session:
                executor = session.execute_write if write else session.execute_read
                return await executor(self._run_query_async, query, params)
        except Neo4jError as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}") from e

    @asynccontextmanager
    async def _session(self):
        """Async context manager for Neo4j session."""
        if not self.driver:
            raise DatabaseConnectionError(
                "Connection failed: not connected to Neo4j (call connect() first)"
            )

        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            await session.close()

    @staticmethod
    async def _run_query_async(
        tx, query: str, parameters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Run a query within an async transaction and return records."""
        result = await tx.run(query, parameters)
        return await result.data()

    async def initialize_schema(self) -> None:
        logger.info("Initializing Neo4j schema for Claude Memory...")

        constraints = [
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR (r:RELATIONSHIP) REQUIRE r.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type)",
            "CREATE INDEX memory_created_at_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
            "CREATE INDEX memory_tags_index IF NOT EXISTS FOR (m:Memory) ON (m.tags)",
            "CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS FOR (m:Memory) ON EACH [m.title, m.content, m.summary]",
            "CREATE INDEX memory_importance_index IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
            "CREATE INDEX memory_confidence_index IF NOT EXISTS FOR (m:Memory) ON (m.confidence)",
            "CREATE INDEX memory_project_path_index IF NOT EXISTS FOR (m:Memory) ON (m.context_project_path)",
        ]

        if Config.is_multi_tenant_mode():
            multitenant_indexes = [
                "CREATE INDEX memory_tenant_index IF NOT EXISTS FOR (m:Memory) ON (m.context_tenant_id)",
                "CREATE INDEX memory_team_index IF NOT EXISTS FOR (m:Memory) ON (m.context_team_id)",
                "CREATE INDEX memory_visibility_index IF NOT EXISTS FOR (m:Memory) ON (m.context_visibility)",
                "CREATE INDEX memory_created_by_index IF NOT EXISTS FOR (m:Memory) ON (m.context_created_by)",
                "CREATE INDEX memory_version_index IF NOT EXISTS FOR (m:Memory) ON (m.version)",
            ]
            indexes.extend(multitenant_indexes)
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
            if "already exists" not in str(e).lower():
                raise SchemaError(f"Failed to execute schema statement: {e}") from e

    async def health_check(self) -> dict[str, Any]:
        health_info = {
            "connected": self._connected,
            "backend_type": "neo4j",
            "uri": self.uri,
            "database": self.database,
        }

        if self._connected:
            try:
                query = """
                CALL dbms.components() YIELD name, versions, edition
                RETURN name, versions[0] as version, edition
                """
                result = await self.execute_query(query, write=False)
                if result:
                    health_info["version"] = result[0].get("version", "unknown")
                    health_info["edition"] = result[0].get("edition", "unknown")

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
        return "neo4j"

    def supports_fulltext_search(self) -> bool:
        return True

    def supports_transactions(self) -> bool:
        return True

    def is_cypher_capable(self) -> bool:
        return True

    @classmethod
    async def create(
        cls,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ) -> "Neo4jBackend":
        """Create and return a connected Neo4jBackend instance."""
        backend = cls(uri, user, password, database)
        await backend.connect()
        return backend
