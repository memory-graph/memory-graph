"""Tests for MemoryGraph async client."""
import pytest
import respx
from httpx import Response

from memorygraphsdk import (
    AsyncMemoryGraphClient,
    Memory,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
)


@pytest.fixture
def api_url():
    """Base API URL for tests."""
    return "https://api.memorygraph.dev"


@pytest.fixture
def sample_memory_response():
    """Sample memory API response."""
    return {
        "id": "mem_123",
        "type": "solution",
        "title": "Test Memory",
        "content": "Test content",
        "tags": ["test"],
        "importance": 0.5,
        "context": None,
        "summary": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


class TestAsyncMemoryGraphClient:
    """Tests for AsyncMemoryGraphClient."""

    def test_init(self, api_url):
        """Test client initialization."""
        client = AsyncMemoryGraphClient(api_key="test_key", api_url=api_url)
        assert client.api_key == "test_key"
        assert client.api_url == api_url

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from API URL."""
        client = AsyncMemoryGraphClient(api_key="test", api_url="https://api.test.com/")
        assert client.api_url == "https://api.test.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_memory(self, api_url, sample_memory_response):
        """Test creating a memory."""
        respx.post(f"{api_url}/api/v1/memories").mock(
            return_value=Response(200, json=sample_memory_response)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memory = await client.create_memory(
                type="solution",
                title="Test Memory",
                content="Test content",
                tags=["test"],
            )

            assert isinstance(memory, Memory)
            assert memory.id == "mem_123"
            assert memory.title == "Test Memory"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_memory(self, api_url, sample_memory_response):
        """Test getting a memory by ID."""
        respx.get(f"{api_url}/api/v1/memories/mem_123").mock(
            return_value=Response(200, json=sample_memory_response)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memory = await client.get_memory("mem_123")

            assert isinstance(memory, Memory)
            assert memory.id == "mem_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_memories(self, api_url, sample_memory_response):
        """Test searching memories."""
        respx.get(f"{api_url}/api/v1/memories").mock(
            return_value=Response(200, json={"memories": [sample_memory_response]})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memories = await client.search_memories(query="test")

            assert len(memories) == 1
            assert memories[0].id == "mem_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_memory(self, api_url, sample_memory_response):
        """Test updating a memory."""
        updated = {**sample_memory_response, "title": "Updated Title"}
        respx.patch(f"{api_url}/api/v1/memories/mem_123").mock(
            return_value=Response(200, json=updated)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memory = await client.update_memory("mem_123", title="Updated Title")

            assert memory.title == "Updated Title"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_memory(self, api_url):
        """Test deleting a memory."""
        respx.delete(f"{api_url}/api/v1/memories/mem_123").mock(
            return_value=Response(204)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            result = await client.delete_memory("mem_123")

            assert result is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_authentication_error(self, api_url):
        """Test authentication error handling."""
        respx.get(f"{api_url}/api/v1/memories/mem_123").mock(
            return_value=Response(401, json={"error": "Invalid API key"})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            with pytest.raises(AuthenticationError):
                await client.get_memory("mem_123")

    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, api_url):
        """Test rate limit error handling."""
        respx.get(f"{api_url}/api/v1/memories/mem_123").mock(
            return_value=Response(429, json={"error": "Rate limited"})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            with pytest.raises(RateLimitError):
                await client.get_memory("mem_123")

    @respx.mock
    @pytest.mark.asyncio
    async def test_not_found_error(self, api_url):
        """Test not found error handling."""
        respx.get(f"{api_url}/api/v1/memories/invalid").mock(
            return_value=Response(404, json={"error": "Not found"})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            with pytest.raises(NotFoundError):
                await client.get_memory("invalid")

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_relationship(self, api_url):
        """Test creating a relationship."""
        response = {
            "id": "rel_123",
            "from_memory_id": "mem_1",
            "to_memory_id": "mem_2",
            "relationship_type": "SOLVES",
            "strength": 0.5,
            "confidence": 0.8,
            "context": None,
            "created_at": "2024-01-01T00:00:00Z",
        }
        respx.post(f"{api_url}/api/v1/relationships").mock(
            return_value=Response(200, json=response)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            rel = await client.create_relationship(
                from_memory_id="mem_1",
                to_memory_id="mem_2",
                relationship_type="SOLVES",
            )

            assert rel.id == "rel_123"
            assert rel.relationship_type == "SOLVES"

    @pytest.mark.asyncio
    async def test_async_context_manager(self, api_url):
        """Test async context manager usage."""
        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            assert client.api_key == "test"
        # Client should be closed after exiting


class TestAsyncAdditionalCoverage:
    """Additional async tests for full coverage."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_memory_with_context_and_summary(self, api_url):
        """Test creating a memory with context and summary."""
        response = {
            "id": "mem_123",
            "type": "solution",
            "title": "Test",
            "content": "Content",
            "tags": [],
            "importance": 0.5,
            "context": {"key": "value"},
            "summary": "Test summary",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        respx.post(f"{api_url}/api/v1/memories").mock(
            return_value=Response(200, json=response)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memory = await client.create_memory(
                type="solution",
                title="Test",
                content="Content",
                context={"key": "value"},
                summary="Test summary",
            )

            assert memory.context == {"key": "value"}
            assert memory.summary == "Test summary"

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_memory_with_all_fields(self, api_url):
        """Test updating memory with all optional fields."""
        response = {
            "id": "mem_123",
            "type": "solution",
            "title": "New Title",
            "content": "New Content",
            "tags": ["new"],
            "importance": 0.9,
            "context": None,
            "summary": "New summary",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        respx.patch(f"{api_url}/api/v1/memories/mem_123").mock(
            return_value=Response(200, json=response)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memory = await client.update_memory(
                "mem_123",
                title="New Title",
                content="New Content",
                tags=["new"],
                importance=0.9,
                summary="New summary",
            )

            assert memory.title == "New Title"
            assert memory.content == "New Content"
            assert memory.importance == 0.9
            assert memory.summary == "New summary"

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_memories_with_all_filters(self, api_url, sample_memory_response):
        """Test searching with all filter parameters."""
        respx.get(f"{api_url}/api/v1/memories").mock(
            return_value=Response(200, json={"memories": [sample_memory_response]})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memories = await client.search_memories(
                query="test",
                memory_types=["solution"],
                tags=["test"],
                min_importance=0.5,
                limit=10,
                offset=5,
            )

            assert len(memories) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_recall_memories(self, api_url, sample_memory_response):
        """Test recall_memories method."""
        respx.get(f"{api_url}/api/v1/memories/recall").mock(
            return_value=Response(200, json={"memories": [sample_memory_response]})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            memories = await client.recall_memories(
                query="redis timeout",
                memory_types=["solution"],
                project_path="/path/to/project",
            )

            assert len(memories) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_relationship_with_context(self, api_url):
        """Test creating a relationship with context."""
        response = {
            "id": "rel_123",
            "from_memory_id": "mem_1",
            "to_memory_id": "mem_2",
            "relationship_type": "SOLVES",
            "strength": 0.8,
            "confidence": 0.9,
            "context": "This solution solves that problem",
            "created_at": "2024-01-01T00:00:00Z",
        }
        respx.post(f"{api_url}/api/v1/relationships").mock(
            return_value=Response(200, json=response)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            rel = await client.create_relationship(
                from_memory_id="mem_1",
                to_memory_id="mem_2",
                relationship_type="SOLVES",
                strength=0.8,
                confidence=0.9,
                context="This solution solves that problem",
            )

            assert rel.context == "This solution solves that problem"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_related_memories(self, api_url, sample_memory_response):
        """Test getting related memories with filters."""
        response = {
            "related": [
                {
                    "memory": sample_memory_response,
                    "relationship_type": "SOLVES",
                    "strength": 0.8,
                    "depth": 2,
                }
            ]
        }
        respx.get(f"{api_url}/api/v1/memories/mem_123/related").mock(
            return_value=Response(200, json=response)
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            related = await client.get_related_memories(
                "mem_123",
                relationship_types=["SOLVES"],
                max_depth=2,
            )

            assert len(related) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_validation_error(self, api_url):
        """Test validation error handling."""
        respx.post(f"{api_url}/api/v1/memories").mock(
            return_value=Response(400, json={"error": "Invalid input"})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            with pytest.raises(ValidationError):
                await client.create_memory(type="", title="", content="")

    @respx.mock
    @pytest.mark.asyncio
    async def test_server_error(self, api_url):
        """Test server error handling."""
        respx.get(f"{api_url}/api/v1/memories/mem_123").mock(
            return_value=Response(500, json={"error": "Internal server error"})
        )

        async with AsyncMemoryGraphClient(api_key="test", api_url=api_url) as client:
            with pytest.raises(ServerError):
                await client.get_memory("mem_123")
