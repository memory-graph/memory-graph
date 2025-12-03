"""
Cloud backend for MemoryGraph.

This is a placeholder for future cloud sync functionality.
When MEMORYGRAPH_API_KEY is set, this backend will sync
memories to the MemoryGraph cloud service.

NOTE: This backend is not yet implemented. Use Turso backend
for cloud persistence today.
"""

from typing import Any, Optional
from .base import GraphBackend
from ..models import DatabaseConnectionError


class CloudBackend(GraphBackend):
    """Placeholder for cloud backend implementation."""

    def __init__(self, api_key: str, api_url: str = "https://api.memorygraph.dev"):
        """
        Initialize cloud backend.

        Args:
            api_key: MemoryGraph API key
            api_url: MemoryGraph API endpoint URL

        Raises:
            NotImplementedError: Cloud backend not yet available
        """
        self.api_key = api_key
        self.api_url = api_url

        raise NotImplementedError(
            "Cloud backend coming soon. "
            "For persistent cloud storage, use Turso backend: "
            "pip install memorygraphMCP[turso] and set TURSO_DATABASE_URL"
        )

    async def connect(self) -> bool:
        """Not implemented."""
        raise NotImplementedError("Cloud backend not yet available")

    async def disconnect(self) -> None:
        """Not implemented."""
        raise NotImplementedError("Cloud backend not yet available")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False,
    ) -> list[dict[str, Any]]:
        """Not implemented."""
        raise NotImplementedError("Cloud backend not yet available")

    async def initialize_schema(self) -> None:
        """Not implemented."""
        raise NotImplementedError("Cloud backend not yet available")

    async def health_check(self) -> dict[str, Any]:
        """Not implemented."""
        raise NotImplementedError("Cloud backend not yet available")

    def backend_name(self) -> str:
        """Return backend identifier."""
        return "cloud"

    def supports_fulltext_search(self) -> bool:
        """Not implemented."""
        return False

    def supports_transactions(self) -> bool:
        """Not implemented."""
        return False
