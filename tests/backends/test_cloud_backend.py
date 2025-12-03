"""
Comprehensive tests for cloud backend module.

Tests cover:
- Connection management
- Memory CRUD operations
- Relationship operations
- Search operations
- Error handling
- Retry logic
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from memorygraph.backends.cloud_backend import (
    CloudBackend,
    CloudBackendError,
    AuthenticationError,
    UsageLimitExceeded,
    RateLimitExceeded,
)
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, Relationship,
    RelationshipType, RelationshipProperties, SearchQuery,
    DatabaseConnectionError,
)


@pytest.fixture
def api_key():
    """Test API key."""
    return "mg_test_api_key_12345"


@pytest.fixture
def api_url():
    """Test API URL."""
    return "https://test-api.memorygraph.dev"


@pytest.fixture
def backend(api_key, api_url):
    """Create a test cloud backend."""
    return CloudBackend(api_key=api_key, api_url=api_url, timeout=10)


@pytest.fixture
def sample_memory():
    """Create a sample memory for testing."""
    return Memory(
        id="mem_12345",
        type=MemoryType.SOLUTION,
        title="Test Solution",
        content="This is a test solution for a problem",
        summary="Test summary",
        tags=["python", "testing"],
        importance=0.8,
        confidence=0.9,
        context=MemoryContext(
            project_path="/test/project",
            files_involved=["test.py"],
            languages=["python"]
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    def _create_response(status_code=200, json_data=None, headers=None):
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.headers = headers or {}
        response.content = b'{}' if json_data else b''
        response.json.return_value = json_data or {}
        response.raise_for_status = MagicMock()
        return response
    return _create_response


class TestCloudBackendInitialization:
    """Test CloudBackend initialization."""

    def test_initialization_with_api_key(self, api_key, api_url):
        """Test initialization with explicit API key."""
        backend = CloudBackend(api_key=api_key, api_url=api_url)
        assert backend.api_key == api_key
        assert backend.api_url == api_url
        assert backend.timeout == CloudBackend.DEFAULT_TIMEOUT

    def test_initialization_without_api_key_raises(self):
        """Test that missing API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                CloudBackend()
            assert "MEMORYGRAPH_API_KEY is required" in str(exc_info.value)

    def test_initialization_with_env_vars(self, api_key, api_url):
        """Test initialization from environment variables."""
        with patch.dict('os.environ', {
            'MEMORYGRAPH_API_KEY': api_key,
            'MEMORYGRAPH_API_URL': api_url,
            'MEMORYGRAPH_TIMEOUT': '60'
        }):
            backend = CloudBackend()
            assert backend.api_key == api_key
            assert backend.api_url == api_url
            assert backend.timeout == 60

    def test_api_key_warning_for_invalid_prefix(self, api_url, caplog):
        """Test warning for API key without mg_ prefix."""
        with patch.dict('os.environ', {}, clear=True):
            backend = CloudBackend(api_key="invalid_key", api_url=api_url)
            assert "does not start with 'mg_'" in caplog.text

    def test_default_api_url(self, api_key):
        """Test default API URL is used when not provided."""
        with patch.dict('os.environ', {'MEMORYGRAPH_API_KEY': api_key}, clear=True):
            backend = CloudBackend(api_key=api_key)
            assert backend.api_url == CloudBackend.DEFAULT_API_URL


class TestCloudBackendConnection:
    """Test connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, backend, mock_response):
        """Test successful connection."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "healthy", "version": "1.0.0"}

            result = await backend.connect()

            assert result is True
            assert backend._connected is True
            mock_request.assert_called_once_with("GET", "/health")

    @pytest.mark.asyncio
    async def test_connect_failure(self, backend):
        """Test connection failure."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = DatabaseConnectionError("Connection failed")

            with pytest.raises(DatabaseConnectionError):
                await backend.connect()

    @pytest.mark.asyncio
    async def test_connect_auth_failure(self, backend):
        """Test authentication failure during connection."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = AuthenticationError("Invalid API key")

            with pytest.raises(AuthenticationError):
                await backend.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, backend):
        """Test disconnection."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        backend._client = mock_client
        backend._connected = True

        await backend.disconnect()

        mock_client.aclose.assert_called_once()
        assert backend._connected is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, backend):
        """Test successful health check."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "healthy", "version": "1.0.0"}

            result = await backend.health_check()

            assert result["connected"] is True
            assert result["backend_type"] == "cloud"
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, backend):
        """Test health check on failure."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Connection error")

            result = await backend.health_check()

            assert result["connected"] is False
            assert "error" in result


class TestCloudBackendMemoryOperations:
    """Test memory CRUD operations."""

    @pytest.mark.asyncio
    async def test_store_memory(self, backend, sample_memory):
        """Test storing a memory."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "mem_new_12345"}

            result = await backend.store_memory(sample_memory)

            assert result == "mem_new_12345"
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/memories"

    @pytest.mark.asyncio
    async def test_get_memory_found(self, backend):
        """Test getting an existing memory."""
        memory_data = {
            "id": "mem_12345",
            "type": "solution",
            "title": "Test Solution",
            "content": "Test content",
            "tags": ["python"],
            "importance": 0.8,
            "confidence": 0.9,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = memory_data

            result = await backend.get_memory("mem_12345")

            assert result is not None
            assert result.id == "mem_12345"
            assert result.type == MemoryType.SOLUTION
            assert result.title == "Test Solution"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, backend):
        """Test getting a non-existent memory."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            result = await backend.get_memory("mem_nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_update_memory(self, backend):
        """Test updating a memory."""
        updated_data = {
            "id": "mem_12345",
            "type": "solution",
            "title": "Updated Title",
            "content": "Updated content",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = updated_data

            result = await backend.update_memory("mem_12345", {"title": "Updated Title"})

            assert result.title == "Updated Title"
            mock_request.assert_called_once_with(
                "PUT", "/memories/mem_12345", json={"title": "Updated Title"}
            )

    @pytest.mark.asyncio
    async def test_delete_memory(self, backend):
        """Test deleting a memory."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {}

            result = await backend.delete_memory("mem_12345")

            assert result is True
            mock_request.assert_called_once_with("DELETE", "/memories/mem_12345")


class TestCloudBackendRelationshipOperations:
    """Test relationship operations."""

    @pytest.mark.asyncio
    async def test_create_relationship(self, backend):
        """Test creating a relationship."""
        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "rel_12345"}

            result = await backend.create_relationship(
                from_memory_id="mem_1",
                to_memory_id="mem_2",
                relationship_type=RelationshipType.SOLVES,
                properties=RelationshipProperties(
                    strength=0.9,
                    confidence=0.95,
                    context="Solution solves the problem"
                )
            )

            assert result == "rel_12345"
            call_args = mock_request.call_args
            assert call_args[1]["json"]["from_memory_id"] == "mem_1"
            assert call_args[1]["json"]["to_memory_id"] == "mem_2"
            assert call_args[1]["json"]["relationship_type"] == "SOLVES"

    @pytest.mark.asyncio
    async def test_get_related_memories(self, backend):
        """Test getting related memories."""
        related_data = {
            "related_memories": [
                {
                    "memory": {
                        "id": "mem_related",
                        "type": "problem",
                        "title": "Related Problem",
                        "content": "Problem content",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "relationship": {
                        "type": "SOLVES",
                        "strength": 0.9,
                        "confidence": 0.95
                    }
                }
            ]
        }

        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = related_data

            result = await backend.get_related_memories(
                "mem_12345",
                relationship_types=[RelationshipType.SOLVES],
                max_depth=2
            )

            assert len(result) == 1
            memory, relationship = result[0]
            assert memory.id == "mem_related"
            assert relationship.type == RelationshipType.SOLVES


class TestCloudBackendSearchOperations:
    """Test search operations."""

    @pytest.mark.asyncio
    async def test_search_memories(self, backend):
        """Test searching memories."""
        search_results = {
            "memories": [
                {
                    "id": "mem_1",
                    "type": "solution",
                    "title": "Solution 1",
                    "content": "Content 1",
                    "tags": ["python"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "mem_2",
                    "type": "problem",
                    "title": "Problem 2",
                    "content": "Content 2",
                    "tags": ["python"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = search_results

            query = SearchQuery(
                query="python",
                memory_types=[MemoryType.SOLUTION, MemoryType.PROBLEM],
                tags=["python"],
                limit=20
            )

            result = await backend.search_memories(query)

            assert len(result) == 2
            assert result[0].id == "mem_1"
            assert result[1].id == "mem_2"

    @pytest.mark.asyncio
    async def test_recall_memories(self, backend):
        """Test recalling memories with natural language query."""
        recall_results = {
            "memories": [
                {
                    "id": "mem_1",
                    "type": "solution",
                    "title": "Redis Timeout Fix",
                    "content": "Fixed Redis timeout by...",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = recall_results

            result = await backend.recall_memories(
                query="Redis timeout solutions",
                memory_types=[MemoryType.SOLUTION],
                limit=10
            )

            assert len(result) == 1
            assert "Redis" in result[0].title

    @pytest.mark.asyncio
    async def test_get_recent_activity(self, backend):
        """Test getting recent activity."""
        activity_data = {
            "memories_by_type": {"solution": 5, "problem": 3},
            "recent_memories": [],
            "unresolved_problems": []
        }

        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = activity_data

            result = await backend.get_recent_activity(days=7)

            assert "memories_by_type" in result

    @pytest.mark.asyncio
    async def test_get_statistics(self, backend):
        """Test getting statistics."""
        stats_data = {
            "total_memories": 100,
            "total_relationships": 50,
            "memories_by_type": {"solution": 40, "problem": 30, "general": 30}
        }

        with patch.object(backend, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = stats_data

            result = await backend.get_statistics()

            assert result["total_memories"] == 100
            assert result["total_relationships"] == 50


class TestCloudBackendErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, backend):
        """Test handling of authentication errors."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_client:
            client = AsyncMock()
            client.request = AsyncMock(return_value=mock_response)
            mock_client.return_value = client

            with pytest.raises(AuthenticationError) as exc_info:
                await backend._request("GET", "/test")

            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_usage_limit_exceeded(self, backend):
        """Test handling of usage limit errors."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.content = b'{"detail": "Storage limit exceeded"}'
        mock_response.json.return_value = {"detail": "Storage limit exceeded"}

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_client:
            client = AsyncMock()
            client.request = AsyncMock(return_value=mock_response)
            mock_client.return_value = client

            with pytest.raises(UsageLimitExceeded) as exc_info:
                await backend._request("POST", "/memories", json={})

            assert "Storage limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, backend):
        """Test handling of rate limit errors."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_client:
            client = AsyncMock()
            client.request = AsyncMock(return_value=mock_response)
            mock_client.return_value = client

            with pytest.raises(RateLimitExceeded) as exc_info:
                await backend._request("GET", "/test")

            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_server_error_retry(self, backend):
        """Test retry on server errors."""
        # First two calls fail with 500, third succeeds
        mock_responses = [
            MagicMock(status_code=500),
            MagicMock(status_code=500),
            MagicMock(status_code=200, json=MagicMock(return_value={"success": True}))
        ]
        mock_responses[2].raise_for_status = MagicMock()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_client:
            client = AsyncMock()
            client.request = AsyncMock(side_effect=mock_responses)
            mock_client.return_value = client

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await backend._request("GET", "/test")

            assert result == {"success": True}
            assert client.request.call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_retry(self, backend):
        """Test retry on timeout."""
        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_client:
            client = AsyncMock()
            # Fail 3 times with timeout, then give up
            client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value = client

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(DatabaseConnectionError) as exc_info:
                    await backend._request("GET", "/test")

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_connection_error_retry(self, backend):
        """Test retry on connection errors."""
        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_client:
            client = AsyncMock()
            client.request = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.return_value = client

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(DatabaseConnectionError) as exc_info:
                    await backend._request("GET", "/test")

            assert "Cannot connect" in str(exc_info.value)


class TestCloudBackendInterface:
    """Test GraphBackend interface compliance."""

    def test_backend_name(self, backend):
        """Test backend name."""
        assert backend.backend_name() == "cloud"

    def test_supports_fulltext_search(self, backend):
        """Test full-text search support."""
        assert backend.supports_fulltext_search() is True

    def test_supports_transactions(self, backend):
        """Test transaction support."""
        assert backend.supports_transactions() is True

    @pytest.mark.asyncio
    async def test_execute_query_not_supported(self, backend):
        """Test that raw query execution is not supported."""
        with pytest.raises(NotImplementedError):
            await backend.execute_query("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    async def test_initialize_schema_noop(self, backend):
        """Test that schema initialization is a no-op."""
        # Should not raise
        await backend.initialize_schema()


class TestCloudBackendPayloadConversion:
    """Test payload conversion methods."""

    def test_memory_to_api_payload(self, backend, sample_memory):
        """Test converting Memory to API payload."""
        payload = backend._memory_to_api_payload(sample_memory)

        assert payload["type"] == "solution"
        assert payload["title"] == "Test Solution"
        assert payload["content"] == "This is a test solution for a problem"
        assert payload["tags"] == ["python", "testing"]
        assert payload["importance"] == 0.8
        assert "context" in payload
        assert payload["context"]["project_path"] == "/test/project"
        assert payload["context"]["files_involved"] == ["test.py"]
        assert payload["context"]["languages"] == ["python"]

    def test_api_response_to_memory(self, backend):
        """Test converting API response to Memory."""
        data = {
            "id": "mem_12345",
            "type": "solution",
            "title": "Test Solution",
            "content": "Test content",
            "summary": "Test summary",
            "tags": ["python"],
            "importance": 0.8,
            "confidence": 0.9,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "context": {
                "project_path": "/test/project",
                "languages": ["python"],
                "files_involved": ["test.py"],
                "additional_metadata": {}
            }
        }

        memory = backend._api_response_to_memory(data)

        assert memory.id == "mem_12345"
        assert memory.type == MemoryType.SOLUTION
        assert memory.title == "Test Solution"
        assert memory.context.project_path == "/test/project"
        assert memory.context.languages == ["python"]

    def test_api_response_to_memory_with_invalid_type(self, backend):
        """Test handling of invalid memory type."""
        data = {
            "id": "mem_12345",
            "type": "invalid_type",
            "title": "Test",
            "content": "Content",
            "created_at": "2024-01-01T00:00:00Z"
        }

        memory = backend._api_response_to_memory(data)

        # Should default to GENERAL
        assert memory.type == MemoryType.GENERAL

    def test_api_response_to_memory_handles_errors(self, backend):
        """Test that conversion errors return None."""
        data = {"invalid": "data"}

        memory = backend._api_response_to_memory(data)

        # Should return None on error
        assert memory is None
