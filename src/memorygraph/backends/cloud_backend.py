"""
Cloud backend for MemoryGraph MCP Server.

This module provides a backend that communicates with the MemoryGraph Cloud API,
enabling multi-device sync, team collaboration, and cloud-based memory storage.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from .base import GraphBackend
from ..models import (
    Memory, MemoryType, MemoryContext, Relationship, RelationshipType,
    RelationshipProperties, SearchQuery, DatabaseConnectionError,
    MemoryNotFoundError, ValidationError
)

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests proceed
    - OPEN: Too many failures, requests fail fast
    - HALF_OPEN: Recovery period, limited requests allowed
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open

    def can_execute(self) -> bool:
        """
        Check if request should be allowed to proceed.

        Returns:
            True if request should proceed, False to fail fast
        """
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if recovery timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout):
                logger.info("Circuit breaker entering half-open state for recovery attempt")
                self.state = "half_open"
                return True
            return False

        # half_open state - allow the request through
        return True

    def record_success(self) -> None:
        """Record a successful request."""
        if self.state == "half_open":
            logger.info("Circuit breaker closing after successful recovery")
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"

    def record_failure(self) -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "half_open":
            # Failed during recovery, reopen circuit
            logger.warning("Circuit breaker reopening after failed recovery attempt")
            self.state = "open"
        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open circuit
            logger.warning(
                f"Circuit breaker opening after {self.failure_count} consecutive failures. "
                f"Will retry in {self.recovery_timeout} seconds"
            )
            self.state = "open"


class CloudBackendError(Exception):
    """Base exception for cloud backend errors."""
    pass


class AuthenticationError(CloudBackendError):
    """Raised when API key is invalid or expired."""
    pass


class UsageLimitExceeded(CloudBackendError):
    """Raised when usage limits are exceeded."""
    pass


class RateLimitExceeded(CloudBackendError):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreakerOpenError(CloudBackendError):
    """Raised when circuit breaker is open (failing fast)."""
    pass


class CloudBackend(GraphBackend):
    """
    Cloud backend that connects to MemoryGraph Cloud API.

    This backend enables:
    - Multi-device synchronization
    - Team collaboration and shared memories
    - Cloud-based storage with automatic backups
    - Usage tracking and analytics

    Configuration:
        MEMORYGRAPH_API_KEY: API key for authentication (required)
        MEMORYGRAPH_API_URL: API base URL (default: https://graph-api.memorygraph.dev)
        MEMORYGRAPH_TIMEOUT: Request timeout in seconds (default: 30)
    """

    # Production API URL - configurable via MEMORYGRAPH_API_URL environment variable
    DEFAULT_API_URL = "https://graph-api.memorygraph.dev"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 1.0  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize cloud backend.

        Args:
            api_key: API key for authentication. If not provided, reads from
                     MEMORYGRAPH_API_KEY environment variable.
            api_url: Base URL for the Graph API. Defaults to production URL.
            timeout: Request timeout in seconds. Defaults to 30.

        Raises:
            DatabaseConnectionError: If API key is not provided.
        """
        self.api_key = api_key or os.getenv("MEMORYGRAPH_API_KEY")
        self.api_url = (
            api_url or
            os.getenv("MEMORYGRAPH_API_URL") or
            self.DEFAULT_API_URL
        ).rstrip("/")
        self.timeout = timeout or int(os.getenv("MEMORYGRAPH_TIMEOUT", str(self.DEFAULT_TIMEOUT)))

        if not self.api_key:
            raise DatabaseConnectionError(
                "MEMORYGRAPH_API_KEY is required for cloud backend. "
                "Get your API key at https://app.memorygraph.dev"
            )

        if not self.api_key.startswith("mg_"):
            logger.warning(
                "API key does not start with 'mg_' prefix. "
                "Ensure you're using a valid MemoryGraph API key."
            )

        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "memorygraph-mcp/1.0"
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=self._get_headers(),
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        retry_count: int = 0
    ) -> dict[str, Any]:
        """
        Make an HTTP request with retry logic and circuit breaker.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/memories")
            json: JSON body for POST/PUT requests
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If API key is invalid
            UsageLimitExceeded: If usage limits exceeded
            RateLimitExceeded: If rate limits exceeded
            CircuitBreakerOpenError: If circuit breaker is open
            DatabaseConnectionError: For network or server errors
        """
        # Check circuit breaker
        if not self._circuit_breaker.can_execute():
            raise CircuitBreakerOpenError(
                "Circuit breaker is open due to repeated failures. "
                f"Will retry in {self._circuit_breaker.recovery_timeout} seconds."
            )

        client = await self._get_client()

        try:
            response = await client.request(
                method=method,
                url=path,
                json=json,
                params=params
            )

            # Handle specific error codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid API key. Get a valid key at https://app.memorygraph.dev"
                )

            if response.status_code == 403:
                error_data = response.json() if response.content else {}
                raise UsageLimitExceeded(
                    error_data.get("detail", "Usage limit exceeded. Upgrade at https://app.memorygraph.dev/pricing")
                )

            if response.status_code == 404:
                # Raise consistent exception for not found
                raise MemoryNotFoundError(f"Resource not found: {path}")

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitExceeded(
                    "Rate limit exceeded. Please slow down requests.",
                    retry_after=int(retry_after) if retry_after else None
                )

            if response.status_code >= 500:
                # Server error - retry with backoff
                self._circuit_breaker.record_failure()
                if retry_count < self.MAX_RETRIES:
                    backoff = self.RETRY_BACKOFF_BASE * (2 ** retry_count)
                    logger.warning(
                        f"Server error {response.status_code}, "
                        f"retrying in {backoff}s (attempt {retry_count + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(backoff)
                    return await self._request(method, path, json, params, retry_count + 1)
                else:
                    raise DatabaseConnectionError(
                        f"Graph API server error after {self.MAX_RETRIES} retries: {response.status_code}"
                    )

            response.raise_for_status()

            # Record success with circuit breaker
            self._circuit_breaker.record_success()

            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.TimeoutException:
            self._circuit_breaker.record_failure()
            if retry_count < self.MAX_RETRIES:
                backoff = self.RETRY_BACKOFF_BASE * (2 ** retry_count)
                logger.warning(
                    f"Request timeout, retrying in {backoff}s "
                    f"(attempt {retry_count + 1}/{self.MAX_RETRIES})"
                )
                await asyncio.sleep(backoff)
                return await self._request(method, path, json, params, retry_count + 1)
            raise DatabaseConnectionError(
                f"Request timeout after {self.MAX_RETRIES} retries"
            )

        except httpx.ConnectError as e:
            self._circuit_breaker.record_failure()
            if retry_count < self.MAX_RETRIES:
                backoff = self.RETRY_BACKOFF_BASE * (2 ** retry_count)
                logger.warning(
                    f"Connection error, retrying in {backoff}s "
                    f"(attempt {retry_count + 1}/{self.MAX_RETRIES})"
                )
                await asyncio.sleep(backoff)
                return await self._request(method, path, json, params, retry_count + 1)
            raise DatabaseConnectionError(
                f"Cannot connect to Graph API at {self.api_url}: {e}"
            )

        except (AuthenticationError, UsageLimitExceeded, RateLimitExceeded, MemoryNotFoundError):
            raise

        except httpx.HTTPStatusError as e:
            raise DatabaseConnectionError(f"HTTP error: {e}")

        except Exception as e:
            raise DatabaseConnectionError(f"Unexpected error: {e}")

    # =========================================================================
    # GraphBackend Interface Implementation
    # =========================================================================

    async def connect(self) -> bool:
        """
        Establish connection to the cloud API.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
            AuthenticationError: If API key is invalid
        """
        try:
            logger.info(f"Connecting to MemoryGraph Cloud at {self.api_url}...")

            # Verify connection with health check
            result = await self._request("GET", "/health")

            if result and result.get("status") == "healthy":
                self._connected = True
                logger.info("✓ Successfully connected to MemoryGraph Cloud")
                return True
            else:
                raise DatabaseConnectionError(
                    f"Health check failed: {result}"
                )

        except AuthenticationError:
            raise
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to cloud: {e}")

    async def disconnect(self) -> None:
        """Close the connection and clean up resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Disconnected from MemoryGraph Cloud")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False
    ) -> list[dict[str, Any]]:
        """
        Execute a query (not supported for cloud backend).

        Cloud backend uses REST API, not Cypher queries.
        Use the specific memory/relationship methods instead.

        Raises:
            NotImplementedError: Always, as cloud backend doesn't support raw queries
        """
        raise NotImplementedError(
            "Cloud backend does not support raw Cypher queries. "
            "Use store_memory(), search_memories(), etc. instead."
        )

    async def initialize_schema(self) -> None:
        """
        Initialize schema (no-op for cloud backend).

        Schema is managed by the cloud service.
        """
        logger.debug("Schema initialization skipped - managed by cloud service")

    async def health_check(self) -> dict[str, Any]:
        """
        Check cloud API health and return status.

        Returns:
            Dictionary with health check results
        """
        try:
            result = await self._request("GET", "/health")
            return {
                "connected": True,
                "backend_type": "cloud",
                "api_url": self.api_url,
                "status": result.get("status", "unknown"),
                "version": result.get("version", "unknown")
            }
        except Exception as e:
            return {
                "connected": False,
                "backend_type": "cloud",
                "api_url": self.api_url,
                "error": str(e)
            }

    def backend_name(self) -> str:
        """Return backend name."""
        return "cloud"

    def supports_fulltext_search(self) -> bool:
        """Cloud backend supports full-text search."""
        return True

    def supports_transactions(self) -> bool:
        """Cloud backend handles transactions server-side."""
        return True

    # =========================================================================
    # Memory Operations
    # =========================================================================

    async def store_memory(self, memory: Memory) -> str:
        """
        Store a memory in the cloud.

        Args:
            memory: Memory object to store

        Returns:
            ID of the stored memory

        Raises:
            UsageLimitExceeded: If storage limits exceeded
            DatabaseConnectionError: If storage fails
        """
        payload = self._memory_to_api_payload(memory)

        result = await self._request("POST", "/memories", json=payload)

        memory_id = result.get("id") or result.get("memory_id")
        logger.info(f"Stored memory in cloud: {memory_id}")
        return memory_id

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve a memory by ID.

        Args:
            memory_id: ID of the memory

        Returns:
            Memory object if found, None otherwise

        Raises:
            MemoryNotFoundError: If memory doesn't exist
        """
        try:
            result = await self._request("GET", f"/memories/{memory_id}")
            return self._api_response_to_memory(result)
        except MemoryNotFoundError:
            # get_memory returns None for not found (API contract)
            return None

    async def update_memory(self, memory_id: str, updates: dict[str, Any]) -> Optional[Memory]:
        """
        Update an existing memory.

        Args:
            memory_id: ID of the memory to update
            updates: Dictionary of fields to update

        Returns:
            Updated Memory object

        Raises:
            MemoryNotFoundError: If memory doesn't exist
        """
        result = await self._request("PUT", f"/memories/{memory_id}", json=updates)
        return self._api_response_to_memory(result)

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if deleted successfully

        Raises:
            MemoryNotFoundError: If memory doesn't exist
        """
        await self._request("DELETE", f"/memories/{memory_id}")
        logger.info(f"Deleted memory from cloud: {memory_id}")
        return True

    # =========================================================================
    # Relationship Operations
    # =========================================================================

    async def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: Optional[RelationshipProperties] = None
    ) -> str:
        """
        Create a relationship between two memories.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship
            properties: Optional relationship properties

        Returns:
            ID of the created relationship
        """
        payload = {
            "from_memory_id": from_memory_id,
            "to_memory_id": to_memory_id,
            "relationship_type": relationship_type.value,
        }

        if properties:
            payload["strength"] = properties.strength
            payload["confidence"] = properties.confidence
            if properties.context:
                payload["context"] = properties.context

        result = await self._request("POST", "/relationships", json=payload)

        relationship_id = result.get("id") or result.get("relationship_id")
        logger.info(
            f"Created relationship in cloud: {from_memory_id} "
            f"-[{relationship_type.value}]-> {to_memory_id}"
        )
        return relationship_id

    async def get_related_memories(
        self,
        memory_id: str,
        relationship_types: Optional[list[RelationshipType]] = None,
        max_depth: int = 1
    ) -> list[tuple[Memory, Relationship]]:
        """
        Get memories related to a specific memory.

        Args:
            memory_id: ID of the memory
            relationship_types: Filter by relationship types
            max_depth: Maximum traversal depth

        Returns:
            List of (Memory, Relationship) tuples, empty if memory not found
        """
        params = {"max_depth": max_depth}

        if relationship_types:
            params["relationship_types"] = ",".join(rt.value for rt in relationship_types)

        try:
            result = await self._request(
                "GET",
                f"/memories/{memory_id}/related",
                params=params
            )
        except MemoryNotFoundError:
            # Memory doesn't exist, return empty list
            return []

        if not result:
            return []

        related = []
        for item in result.get("related_memories", []):
            memory = self._api_response_to_memory(item.get("memory", item))

            rel_data = item.get("relationship", {})
            try:
                rel_type = RelationshipType(rel_data.get("type", "RELATED_TO"))
            except ValueError:
                rel_type = RelationshipType.RELATED_TO

            relationship = Relationship(
                from_memory_id=memory_id,
                to_memory_id=memory.id,
                type=rel_type,
                properties=RelationshipProperties(
                    strength=rel_data.get("strength", 0.5),
                    confidence=rel_data.get("confidence", 0.8),
                    context=rel_data.get("context")
                )
            )
            related.append((memory, relationship))

        return related

    # =========================================================================
    # Search Operations
    # =========================================================================

    async def search_memories(self, search_query: SearchQuery) -> list[Memory]:
        """
        Search for memories based on query parameters.

        Args:
            search_query: SearchQuery object with filter criteria

        Returns:
            List of matching Memory objects
        """
        payload = {}

        if search_query.query:
            payload["query"] = search_query.query

        if search_query.memory_types:
            payload["memory_types"] = [mt.value for mt in search_query.memory_types]

        if search_query.tags:
            payload["tags"] = search_query.tags

        if search_query.project_path:
            payload["project_path"] = search_query.project_path

        if search_query.min_importance is not None:
            payload["min_importance"] = search_query.min_importance

        if search_query.limit:
            payload["limit"] = search_query.limit

        if search_query.offset:
            payload["offset"] = search_query.offset

        result = await self._request("POST", "/memories/search", json=payload)

        memories = []
        for item in result.get("memories", result.get("results", [])):
            memory = self._api_response_to_memory(item)
            if memory:
                memories.append(memory)

        logger.info(f"Cloud search returned {len(memories)} memories")
        return memories

    async def recall_memories(
        self,
        query: str,
        memory_types: Optional[list[MemoryType]] = None,
        project_path: Optional[str] = None,
        limit: int = 20
    ) -> list[Memory]:
        """
        Recall memories using natural language query (fuzzy search).

        Args:
            query: Natural language query
            memory_types: Optional filter by memory types
            project_path: Optional filter by project
            limit: Maximum results

        Returns:
            List of relevant Memory objects
        """
        payload = {
            "query": query,
            "limit": limit
        }

        if memory_types:
            payload["memory_types"] = [mt.value for mt in memory_types]

        if project_path:
            payload["project_path"] = project_path

        result = await self._request("POST", "/memories/recall", json=payload)

        memories = []
        for item in result.get("memories", result.get("results", [])):
            memory = self._api_response_to_memory(item)
            if memory:
                memories.append(memory)

        return memories

    async def get_recent_activity(
        self,
        days: int = 7,
        project: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get recent memory activity summary.

        Args:
            days: Number of days to look back
            project: Optional project filter

        Returns:
            Activity summary dictionary
        """
        params = {"days": days}
        if project:
            params["project"] = project

        result = await self._request("GET", "/memories/recent", params=params)
        return result or {}

    async def get_statistics(self) -> dict[str, Any]:
        """
        Get graph statistics.

        Returns:
            Statistics dictionary
        """
        result = await self._request("GET", "/graphs/statistics")
        return result or {}

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _memory_to_api_payload(self, memory: Memory) -> dict[str, Any]:
        """Convert Memory object to API payload."""
        payload = {
            "type": memory.type.value,
            "title": memory.title,
            "content": memory.content,
        }

        if memory.id:
            payload["id"] = memory.id

        if memory.summary:
            payload["summary"] = memory.summary

        if memory.tags:
            payload["tags"] = memory.tags

        if memory.importance is not None:
            payload["importance"] = memory.importance

        if memory.confidence is not None:
            payload["confidence"] = memory.confidence

        if memory.context:
            context_dict = {}
            if memory.context.project_path:
                context_dict["project_path"] = memory.context.project_path
            if memory.context.files_involved:
                context_dict["files_involved"] = memory.context.files_involved
            if memory.context.languages:
                context_dict["languages"] = memory.context.languages
            if memory.context.frameworks:
                context_dict["frameworks"] = memory.context.frameworks
            if memory.context.technologies:
                context_dict["technologies"] = memory.context.technologies
            if memory.context.git_commit:
                context_dict["git_commit"] = memory.context.git_commit
            if memory.context.git_branch:
                context_dict["git_branch"] = memory.context.git_branch
            if memory.context.working_directory:
                context_dict["working_directory"] = memory.context.working_directory
            if memory.context.additional_metadata:
                context_dict["additional_metadata"] = memory.context.additional_metadata

            if context_dict:
                payload["context"] = context_dict

        return payload

    def _api_response_to_memory(self, data: dict[str, Any]) -> Optional[Memory]:
        """Convert API response to Memory object."""
        try:
            # Parse memory type
            type_str = data.get("type", "general")
            try:
                memory_type = MemoryType(type_str)
            except ValueError:
                memory_type = MemoryType.GENERAL

            # Parse timestamps
            created_at = data.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elif created_at is None:
                created_at = datetime.now(timezone.utc)

            updated_at = data.get("updated_at")
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            elif updated_at is None:
                updated_at = created_at

            # Parse context
            context = None
            context_data = data.get("context")
            if context_data and isinstance(context_data, dict):
                context = MemoryContext(
                    project_path=context_data.get("project_path"),
                    files_involved=context_data.get("files_involved", []),
                    languages=context_data.get("languages", []),
                    frameworks=context_data.get("frameworks", []),
                    technologies=context_data.get("technologies", []),
                    git_commit=context_data.get("git_commit"),
                    git_branch=context_data.get("git_branch"),
                    working_directory=context_data.get("working_directory"),
                    additional_metadata=context_data.get("additional_metadata", {})
                )

            return Memory(
                id=data.get("id") or data.get("memory_id"),
                type=memory_type,
                title=data.get("title", ""),
                content=data.get("content", ""),
                summary=data.get("summary"),
                tags=data.get("tags", []),
                importance=data.get("importance", 0.5),
                confidence=data.get("confidence", 0.8),
                created_at=created_at,
                updated_at=updated_at,
                context=context
            )

        except Exception as e:
            logger.error(f"Failed to parse memory from API response: {e}")
            return None
