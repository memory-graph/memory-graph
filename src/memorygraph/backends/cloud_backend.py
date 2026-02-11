"""
Cloud backend for MemoryGraph MCP Server.

This module provides a backend that communicates with the MemoryGraph Cloud API,
enabling multi-device sync, team collaboration, and cloud-based memory storage.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from ..config import Config
from ..models import (
    DatabaseConnectionError,
    Memory,
    MemoryContext,
    MemoryNotFoundError,
    MemoryType,
    Relationship,
    RelationshipProperties,
    RelationshipType,
    SearchQuery,
    ValidationError,
)
from .base import GraphBackend

logger = logging.getLogger(__name__)


def _mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """Mask a sensitive value, showing only the first ``visible_chars`` characters."""
    if not value or len(value) <= visible_chars:
        return "***"
    return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars)}"


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures (closed -> open -> half_open)."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
        self._lock = asyncio.Lock()

    async def can_execute(self) -> bool:
        """Check if a request should be allowed through."""
        async with self._lock:
            if self.state == "closed":
                return True

            if self.state == "open":
                if self.last_failure_time and (time.time() - self.last_failure_time >= self.recovery_timeout):
                    logger.info("Circuit breaker entering half-open state for recovery attempt")
                    self.state = "half_open"
                    return True
                return False

            return True  # half_open: allow recovery attempt

    async def record_success(self) -> None:
        async with self._lock:
            if self.state == "half_open":
                logger.info("Circuit breaker closing after successful recovery")
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "closed"

    async def record_failure(self) -> None:
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == "half_open":
                logger.warning("Circuit breaker reopening after failed recovery attempt")
                self.state = "open"
            elif self.failure_count >= self.failure_threshold:
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


class CloudRESTAdapter(GraphBackend):
    """Cloud REST adapter for MemoryGraph Cloud API (multi-device sync, collaboration).

    Uses REST API calls instead of Cypher -- check ``is_cypher_capable()`` before
    calling ``execute_query()``.
    """

    DEFAULT_API_URL = "https://graph-api.memorygraph.dev"
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.api_key = api_key if api_key is not None else Config.MEMORYGRAPH_API_KEY
        self.api_url = (api_url if api_url is not None else Config.MEMORYGRAPH_API_URL or "").rstrip("/")
        self.timeout = timeout if timeout is not None else Config.MEMORYGRAPH_TIMEOUT

        if not self.api_key:
            raise DatabaseConnectionError(
                "MEMORYGRAPH_API_KEY is required for cloud backend. "
                "Get your API key at https://app.memorygraph.dev"
            )

        if not self.api_key.startswith("mg_"):
            masked_key = _mask_sensitive(self.api_key)
            logger.warning(
                f"API key {masked_key} does not start with 'mg_' prefix. "
                "Ensure you're using a valid MemoryGraph API key."
            )

        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=Config.CLOUD_CIRCUIT_BREAKER_THRESHOLD,
            recovery_timeout=Config.CLOUD_CIRCUIT_BREAKER_TIMEOUT
        )

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "memorygraph-mcp/1.0"
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=self._get_headers(),
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True
            )
        return self._client

    async def _retry_or_raise(
        self,
        error_message: str,
        method: str,
        path: str,
        json: Optional[dict],
        params: Optional[dict],
        retry_count: int,
        log_prefix: str,
    ) -> dict[str, Any]:
        """Record a circuit-breaker failure and either retry with backoff or raise."""
        await self._circuit_breaker.record_failure()
        if retry_count < Config.CLOUD_MAX_RETRIES:
            backoff = Config.CLOUD_RETRY_BACKOFF_BASE * (2 ** retry_count)
            logger.warning(
                f"{log_prefix}, retrying in {backoff}s "
                f"(attempt {retry_count + 1}/{Config.CLOUD_MAX_RETRIES})"
            )
            await asyncio.sleep(backoff)
            return await self._request(method, path, json, params, retry_count + 1)
        raise DatabaseConnectionError(error_message)

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        retry_count: int = 0
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic and circuit breaker."""
        if not await self._circuit_breaker.can_execute():
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
                raise MemoryNotFoundError(f"Resource not found: {path}")

            if response.status_code == 413:
                raise ValidationError(
                    "Payload too large. Please reduce the size of your content."
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitExceeded(
                    "Rate limit exceeded. Please slow down requests.",
                    retry_after=int(retry_after) if retry_after else None
                )

            if response.status_code >= 500:
                return await self._retry_or_raise(
                    error_message=f"Graph API server error after {Config.CLOUD_MAX_RETRIES} retries: {response.status_code}",
                    method=method, path=path, json=json, params=params,
                    retry_count=retry_count,
                    log_prefix=f"Server error {response.status_code}",
                )

            response.raise_for_status()
            await self._circuit_breaker.record_success()

            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.TimeoutException:
            return await self._retry_or_raise(
                error_message=f"Request timeout after {Config.CLOUD_MAX_RETRIES} retries",
                method=method, path=path, json=json, params=params,
                retry_count=retry_count,
                log_prefix="Request timeout",
            )

        except httpx.ConnectError as e:
            return await self._retry_or_raise(
                error_message=f"Cannot connect to Graph API at {self.api_url}: {e}",
                method=method, path=path, json=json, params=params,
                retry_count=retry_count,
                log_prefix="Connection error",
            )

        except (AuthenticationError, UsageLimitExceeded, RateLimitExceeded, MemoryNotFoundError):
            raise

        except httpx.HTTPStatusError as e:
            raise DatabaseConnectionError(f"HTTP error: {e}") from e

        except Exception as e:
            raise DatabaseConnectionError(f"Unexpected error: {e}") from e

    # -- GraphBackend interface --------------------------------------------------

    async def connect(self) -> bool:
        try:
            logger.info(f"Connecting to MemoryGraph Cloud at {self.api_url}...")

            result = await self._request("GET", "/health")

            if result and result.get("status") == "healthy":
                self._connected = True
                logger.info("✓ Successfully connected to MemoryGraph Cloud")
                return True

            raise DatabaseConnectionError(f"Health check failed: {result}")

        except AuthenticationError:
            raise
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to cloud: {e}") from e

    async def disconnect(self) -> None:
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
        """Not supported -- cloud backend uses REST, not Cypher."""
        raise NotImplementedError(
            "Cloud backend does not support raw Cypher queries. "
            "Use store_memory(), search_memories(), etc. instead."
        )

    async def initialize_schema(self) -> None:
        """No-op; schema is managed by the cloud service."""
        logger.debug("Schema initialization skipped - managed by cloud service")

    async def health_check(self) -> dict[str, Any]:
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
        return "cloud"

    def supports_fulltext_search(self) -> bool:
        return True

    def supports_transactions(self) -> bool:
        return True

    def is_cypher_capable(self) -> bool:
        return False

    # -- Memory operations -------------------------------------------------------

    async def store_memory(self, memory: Memory) -> str:
        payload = self._memory_to_api_payload(memory)

        result = await self._request("POST", "/memories", json=payload)

        memory_id = result.get("id") or result.get("memory_id")
        logger.info(f"Stored memory in cloud: {memory_id}")
        return memory_id

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        try:
            result = await self._request("GET", f"/memories/{memory_id}")
            return self._api_response_to_memory(result)
        except MemoryNotFoundError:
            return None

    async def update_memory(self, memory_id: str, updates: dict[str, Any]) -> Optional[Memory]:
        result = await self._request("PUT", f"/memories/{memory_id}", json=updates)
        return self._api_response_to_memory(result)

    async def delete_memory(self, memory_id: str) -> bool:
        await self._request("DELETE", f"/memories/{memory_id}")
        logger.info(f"Deleted memory from cloud: {memory_id}")
        return True

    # -- Relationship operations --------------------------------------------------

    async def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: Optional[RelationshipProperties] = None
    ) -> str:
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
        params = {"max_depth": max_depth}

        if relationship_types:
            params["relationship_types"] = ",".join(rt.value for rt in relationship_types)

        try:
            result = await self._request(
                "GET",
                f"/search/memories/{memory_id}/related",
                params=params
            )
        except MemoryNotFoundError:
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

    # -- Search operations --------------------------------------------------------

    async def search_memories(self, search_query: SearchQuery) -> list[Memory]:
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

        result = await self._request("POST", "/search/advanced", json=payload)

        memories = [
            m for item in result.get("memories", result.get("results", []))
            if (m := self._api_response_to_memory(item)) is not None
        ]

        logger.info(f"Cloud search returned {len(memories)} memories")
        return memories

    async def recall_memories(
        self,
        query: str,
        memory_types: Optional[list[MemoryType]] = None,
        project_path: Optional[str] = None,
        limit: int = 20
    ) -> list[Memory]:
        payload = {
            "query": query,
            "limit": limit
        }

        if memory_types:
            payload["memory_types"] = [mt.value for mt in memory_types]

        if project_path:
            payload["project_path"] = project_path

        result = await self._request("POST", "/search/recall", json=payload)

        return [
            m for item in result.get("memories", result.get("results", []))
            if (m := self._api_response_to_memory(item)) is not None
        ]

    async def get_recent_activity(
        self,
        days: int = 7,
        project: Optional[str] = None
    ) -> dict[str, Any]:
        params = {"days": days}
        if project:
            params["project"] = project

        result = await self._request("GET", "/memories/recent", params=params)
        if not result:
            return {
                "total_count": 0,
                "memories_by_type": {},
                "recent_memories": [],
                "unresolved_problems": [],
                "days": days,
                "project": project
            }

        recent_memories = [
            m for item in result.get("recent_memories", [])
            if (m := self._api_response_to_memory(item)) is not None
        ]
        unresolved_problems = [
            m for item in result.get("unresolved_problems", [])
            if (m := self._api_response_to_memory(item)) is not None
        ]

        return {
            "total_count": result.get("total_count", 0),
            "memories_by_type": result.get("memories_by_type", {}),
            "recent_memories": recent_memories,
            "unresolved_problems": unresolved_problems,
            "days": result.get("days", days),
            "project": result.get("project", project)
        }

    async def get_statistics(self) -> dict[str, Any]:
        result = await self._request("GET", "/graphs/statistics")
        return result or {}

    # -- Helpers -----------------------------------------------------------------

    def _memory_to_api_payload(self, memory: Memory) -> dict[str, Any]:
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
            context_fields = [
                "project_path", "files_involved", "languages", "frameworks",
                "technologies", "git_commit", "git_branch", "working_directory",
                "additional_metadata",
            ]
            context_dict = {
                field: getattr(memory.context, field)
                for field in context_fields
                if getattr(memory.context, field)
            }
            if context_dict:
                payload["context"] = context_dict

        return payload

    @staticmethod
    def _parse_timestamp(value: Any, fallback: Optional[datetime] = None) -> datetime:
        """Parse an ISO timestamp string, returning fallback or now(UTC) if missing."""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        if isinstance(value, datetime):
            return value
        return fallback or datetime.now(timezone.utc)

    def _api_response_to_memory(self, data: dict[str, Any]) -> Optional[Memory]:
        try:
            type_str = data.get("type", "general")
            try:
                memory_type = MemoryType(type_str)
            except ValueError:
                memory_type = MemoryType.GENERAL

            created_at = self._parse_timestamp(data.get("created_at"))
            updated_at = self._parse_timestamp(data.get("updated_at"), fallback=created_at)

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


# Deprecated alias -- use CloudRESTAdapter instead
CloudBackend = CloudRESTAdapter
