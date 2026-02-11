"""
FalkorDB backend implementation for the Claude Code Memory Server.

This module provides the FalkorDB-specific implementation of the GraphBackend interface.
FalkorDB is a Redis-based graph database using client-server architecture.
"""

import logging
from typing import Any, Optional

from ..config import Config
from ..models import DatabaseConnectionError
from ._falkordb_shared import BaseFalkorDBBackend

logger = logging.getLogger(__name__)


class FalkorDBBackend(BaseFalkorDBBackend):
    """FalkorDB implementation of the GraphBackend interface."""

    _display_name = "FalkorDB"

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        graph_name: str = "memorygraph",
    ):
        self.host = host if host is not None else Config.FALKORDB_HOST
        self.port = port if port is not None else Config.FALKORDB_PORT
        self.password = password if password is not None else Config.FALKORDB_PASSWORD
        self.graph_name = graph_name
        self.client = None
        self.graph = None
        self._connected = False

    async def connect(self) -> bool:
        try:
            try:
                from falkordb import FalkorDB
            except ImportError as e:
                raise DatabaseConnectionError(
                    "falkordb package is required for FalkorDB backend. "
                    "Install with: pip install falkordb"
                ) from e

            conn_kwargs: dict[str, Any] = {"host": self.host, "port": self.port}
            if self.password:
                conn_kwargs["password"] = self.password
            self.client = FalkorDB(**conn_kwargs)

            self.graph = self.client.select_graph(self.graph_name)
            self._connected = True

            logger.info(f"Successfully connected to FalkorDB at {self.host}:{self.port}")
            return True

        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to connect to FalkorDB: {e}")
            raise DatabaseConnectionError(f"Failed to connect to FalkorDB: {e}") from e

    async def health_check(self) -> dict[str, Any]:
        health_info = {
            "connected": self._connected,
            "backend_type": "falkordb",
            "host": self.host,
            "port": self.port,
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
        return "falkordb"

    # Backward-compatible alias for the renamed internal method.
    _falkordb_to_memory = BaseFalkorDBBackend._node_to_memory

    @classmethod
    async def create(
        cls,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        graph_name: str = "memorygraph",
    ) -> "FalkorDBBackend":
        """Factory method to create and connect a FalkorDB backend."""
        backend = cls(host, port, password, graph_name)
        await backend.connect()
        return backend
