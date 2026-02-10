"""
FalkorDBLite backend implementation for the Claude Code Memory Server.

This module provides the FalkorDBLite-specific implementation of the GraphBackend interface.
FalkorDBLite is an embedded graph database (like SQLite) with native Cypher support and exceptional performance.
Unlike FalkorDB (client-server), FalkorDBLite uses a file path for embedded local storage.
"""

import logging
from typing import Any, Optional

from ..config import Config
from ..models import DatabaseConnectionError
from ._falkordb_shared import BaseFalkorDBBackend

logger = logging.getLogger(__name__)


class FalkorDBLiteBackend(BaseFalkorDBBackend):
    """FalkorDBLite implementation of the GraphBackend interface."""

    _display_name = "FalkorDBLite"

    def __init__(
        self,
        db_path: Optional[str] = None,
        graph_name: str = "memorygraph",
    ):
        """
        Initialize FalkorDBLite backend.

        Args:
            db_path: Path to database file (defaults to FALKORDBLITE_PATH env var or ~/.memorygraph/falkordblite.db)
            graph_name: Name of the graph database (defaults to 'memorygraph')
        """
        if db_path is None:
            db_path = Config.FALKORDBLITE_PATH

        self.db_path = db_path
        self.graph_name = graph_name
        self.client = None
        self.graph = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish connection to FalkorDBLite database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            try:
                from redislite.falkordb_client import FalkorDB
            except ImportError as e:
                raise DatabaseConnectionError(
                    "falkordblite package is required for FalkorDBLite backend. "
                    "Install with: pip install falkordblite"
                ) from e

            self.client = FalkorDB(self.db_path)

            self.graph = self.client.select_graph(self.graph_name)
            self._connected = True

            logger.info(f"Successfully connected to FalkorDBLite at {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to FalkorDBLite: {e}")
            raise DatabaseConnectionError(f"Failed to connect to FalkorDBLite: {e}") from e

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "falkordblite",
            "db_path": self.db_path,
            "graph_name": self.graph_name,
        }

        if self._connected:
            try:
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
        return "falkordblite"

    # Backward-compatible alias for the renamed internal method.
    _falkordblite_to_memory = BaseFalkorDBBackend._node_to_memory

    @classmethod
    async def create(
        cls,
        db_path: Optional[str] = None,
        graph_name: str = "memorygraph",
    ) -> "FalkorDBLiteBackend":
        """
        Factory method to create and connect to a FalkorDBLite backend.

        Args:
            db_path: Path to database file
            graph_name: Name of the graph database

        Returns:
            Connected FalkorDBLiteBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        backend = cls(db_path, graph_name)
        await backend.connect()
        return backend
