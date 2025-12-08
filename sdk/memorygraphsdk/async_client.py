"""
Async MemoryGraph client.
"""
import os
from typing import Any

import httpx

from .exceptions import (
    AuthenticationError,
    MemoryGraphError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import Memory, Relationship, RelatedMemory


class AsyncMemoryGraphClient:
    """
    Asynchronous client for MemoryGraph API.

    Usage:
        async with AsyncMemoryGraphClient(api_key="mgraph_...") as client:
            memory = await client.create_memory(
                type="solution",
                title="Fixed timeout with retry",
                content="...",
                tags=["redis", "timeout"]
            )
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = "https://api.memorygraph.dev",
        timeout: float = 30.0,
    ):
        """
        Initialize the async MemoryGraph client.

        Args:
            api_key: Your MemoryGraph API key (starts with 'mgraph_').
                If not provided, will look for MEMORYGRAPH_API_KEY environment variable.
            api_url: Base URL for the API (default: https://api.memorygraph.dev)
            timeout: Request timeout in seconds (default: 30.0)

        Raises:
            AuthenticationError: If no API key is provided and MEMORYGRAPH_API_KEY
                environment variable is not set.
        """
        if api_key is None:
            api_key = os.environ.get("MEMORYGRAPH_API_KEY")
            if api_key is None:
                raise AuthenticationError(
                    "API key required. Provide via api_key parameter or "
                    "MEMORYGRAPH_API_KEY environment variable."
                )

        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def create_memory(
        self,
        type: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
        importance: float = 0.5,
        context: dict[str, Any] | None = None,
        summary: str | None = None,
    ) -> Memory:
        """
        Create a new memory.

        Args:
            type: Type of memory (e.g., 'solution', 'problem', 'code_pattern')
            title: Short descriptive title
            content: Full content of the memory
            tags: Optional list of tags for categorization
            importance: Importance score 0.0-1.0 (default: 0.5)
            context: Optional context metadata
            summary: Optional brief summary

        Returns:
            Created Memory object
        """
        payload: dict[str, Any] = {
            "type": type,
            "title": title,
            "content": content,
            "tags": tags or [],
            "importance": importance,
        }
        if context is not None:
            payload["context"] = context
        if summary is not None:
            payload["summary"] = summary

        response = await self.client.post(f"{self.api_url}/api/v1/memories", json=payload)
        self._check_response(response)
        return Memory(**response.json())

    async def get_memory(self, memory_id: str, include_relationships: bool = True) -> Memory:
        """
        Get a memory by ID.

        Args:
            memory_id: The ID of the memory to retrieve
            include_relationships: Whether to include related memories (default: True)

        Returns:
            Memory object
        """
        params = {"include_relationships": include_relationships}
        response = await self.client.get(
            f"{self.api_url}/api/v1/memories/{memory_id}",
            params=params,
        )
        self._check_response(response)
        return Memory(**response.json())

    async def update_memory(
        self,
        memory_id: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
        importance: float | None = None,
        summary: str | None = None,
    ) -> Memory:
        """
        Update an existing memory.

        Args:
            memory_id: The ID of the memory to update
            title: New title (optional)
            content: New content (optional)
            tags: New tags (optional)
            importance: New importance score (optional)
            summary: New summary (optional)

        Returns:
            Updated Memory object
        """
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if tags is not None:
            payload["tags"] = tags
        if importance is not None:
            payload["importance"] = importance
        if summary is not None:
            payload["summary"] = summary

        response = await self.client.patch(
            f"{self.api_url}/api/v1/memories/{memory_id}",
            json=payload,
        )
        self._check_response(response)
        return Memory(**response.json())

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory and its relationships.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            True if successful
        """
        response = await self.client.delete(f"{self.api_url}/api/v1/memories/{memory_id}")
        self._check_response(response)
        return True

    async def search_memories(
        self,
        query: str | None = None,
        memory_types: list[str] | None = None,
        tags: list[str] | None = None,
        min_importance: float | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Memory]:
        """
        Search for memories.

        Args:
            query: Text to search for in memory content
            memory_types: Filter by memory types
            tags: Filter by tags
            min_importance: Minimum importance score
            limit: Maximum number of results (default: 20)
            offset: Number of results to skip (default: 0)

        Returns:
            List of matching Memory objects
        """
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if query is not None:
            params["query"] = query
        if memory_types is not None:
            params["memory_types"] = memory_types
        if tags is not None:
            params["tags"] = tags
        if min_importance is not None:
            params["min_importance"] = min_importance

        response = await self.client.get(f"{self.api_url}/api/v1/memories", params=params)
        self._check_response(response)
        data = response.json()
        return [Memory(**m) for m in data.get("memories", [])]

    async def recall_memories(
        self,
        query: str,
        memory_types: list[str] | None = None,
        project_path: str | None = None,
        limit: int = 20,
    ) -> list[Memory]:
        """
        Recall memories using natural language query.

        Args:
            query: Natural language query
            memory_types: Optional filter by memory types
            project_path: Optional project path filter
            limit: Maximum results (default: 20)

        Returns:
            List of relevant Memory objects
        """
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }
        if memory_types is not None:
            params["memory_types"] = memory_types
        if project_path is not None:
            params["project_path"] = project_path

        response = await self.client.get(f"{self.api_url}/api/v1/memories/recall", params=params)
        self._check_response(response)
        data = response.json()
        return [Memory(**m) for m in data.get("memories", [])]

    async def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: str,
        strength: float = 0.5,
        confidence: float = 0.8,
        context: str | None = None,
    ) -> Relationship:
        """
        Create a relationship between two memories.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship (e.g., 'SOLVES', 'CAUSES')
            strength: Relationship strength 0.0-1.0 (default: 0.5)
            confidence: Confidence in relationship 0.0-1.0 (default: 0.8)
            context: Optional context description

        Returns:
            Created Relationship object
        """
        payload: dict[str, Any] = {
            "from_memory_id": from_memory_id,
            "to_memory_id": to_memory_id,
            "relationship_type": relationship_type,
            "strength": strength,
            "confidence": confidence,
        }
        if context is not None:
            payload["context"] = context

        response = await self.client.post(f"{self.api_url}/api/v1/relationships", json=payload)
        self._check_response(response)
        return Relationship(**response.json())

    async def get_related_memories(
        self,
        memory_id: str,
        relationship_types: list[str] | None = None,
        max_depth: int = 1,
    ) -> list[RelatedMemory]:
        """
        Get memories related to a specific memory.

        Args:
            memory_id: The memory to find relations for
            relationship_types: Filter by relationship types
            max_depth: Maximum traversal depth (default: 1)

        Returns:
            List of RelatedMemory objects
        """
        params: dict[str, Any] = {
            "max_depth": max_depth,
        }
        if relationship_types is not None:
            params["relationship_types"] = relationship_types

        response = await self.client.get(
            f"{self.api_url}/api/v1/memories/{memory_id}/related",
            params=params,
        )
        self._check_response(response)
        data = response.json()
        return [RelatedMemory(**r) for r in data.get("related", [])]

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncMemoryGraphClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context manager."""
        await self.close()

    def _check_response(self, response: httpx.Response) -> None:
        """
        Check response status and raise appropriate exceptions.

        Args:
            response: The HTTP response to check

        Raises:
            AuthenticationError: If API key is invalid (401)
            RateLimitError: If rate limit exceeded (429)
            NotFoundError: If resource not found (404)
            ValidationError: If request validation fails (400)
            ServerError: If server error (5xx)
            MemoryGraphError: For other errors
        """
        if response.status_code < 400:
            return

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 404:
            raise NotFoundError(f"Resource not found: {response.text}")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Please retry later.")
        elif response.status_code == 400:
            raise ValidationError(f"Validation error: {response.text}")
        elif response.status_code >= 500:
            raise ServerError(f"Server error: {response.status_code} - {response.text}")
        else:
            raise MemoryGraphError(
                f"API error: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )
