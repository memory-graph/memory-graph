"""
Abstract base class for graph database backends.

This module defines the interface that all backend implementations must follow,
ensuring compatibility across Neo4j, Memgraph, and SQLite fallback.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class GraphBackend(ABC):
    """
    Abstract base class for graph database backends.

    All backend implementations (Neo4j, Memgraph, SQLite) must implement
    this interface to ensure compatibility with the memory server.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the database backend.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            DatabaseConnectionError: If connection cannot be established
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the database connection and clean up resources.

        This method should be idempotent and safe to call multiple times.
        """
        pass

    @abstractmethod
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
            DatabaseConnectionError: If not connected
            Exception: For query execution errors
        """
        pass

    @abstractmethod
    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        This should be idempotent and safe to call multiple times.

        Raises:
            SchemaError: If schema initialization fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results:
                - connected: bool
                - backend_type: str
                - version: str (if available)
                - statistics: dict (optional)
        """
        pass

    @abstractmethod
    def backend_name(self) -> str:
        """
        Return the name of this backend implementation.

        Returns:
            Backend name (e.g., "neo4j", "memgraph", "sqlite")
        """
        pass

    @abstractmethod
    def supports_fulltext_search(self) -> bool:
        """
        Check if this backend supports full-text search.

        Returns:
            True if full-text search is supported
        """
        pass

    @abstractmethod
    def supports_transactions(self) -> bool:
        """
        Check if this backend supports ACID transactions.

        Returns:
            True if transactions are supported
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        return False

    # Compatibility methods for legacy MemoryDatabase interface
    async def execute_write_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a write query (compatibility wrapper for execute_query).

        This method provides compatibility with the legacy Neo4jConnection interface
        used by MemoryDatabase.

        Args:
            query: The Cypher query string
            parameters: Query parameters for parameterized queries

        Returns:
            List of result records as dictionaries
        """
        return await self.execute_query(query, parameters, write=True)

    async def execute_read_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a read query (compatibility wrapper for execute_query).

        This method provides compatibility with the legacy Neo4jConnection interface
        used by MemoryDatabase.

        Args:
            query: The Cypher query string
            parameters: Query parameters for parameterized queries

        Returns:
            List of result records as dictionaries
        """
        return await self.execute_query(query, parameters, write=False)

    async def close(self) -> None:
        """
        Close the connection (compatibility wrapper for disconnect).

        This method provides compatibility with the legacy Neo4jConnection interface.
        """
        await self.disconnect()
