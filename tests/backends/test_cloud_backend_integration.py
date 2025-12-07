"""
Integration tests for cloud backend with mocked HTTP API.

These tests simulate realistic workflows with the cloud backend,
testing full memory lifecycle, relationship operations, and search.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from memorygraph.backends.cloud_backend import (
    CloudBackend,
    AuthenticationError,
    UsageLimitExceeded,
)
from memorygraph.models import (
    Memory, MemoryType, MemoryContext,
    RelationshipType, RelationshipProperties, SearchQuery,
)


@pytest.fixture
def api_key():
    """Test API key."""
    return "mg_integration_test_key"


@pytest.fixture
def api_url():
    """Test API URL."""
    return "https://graph-service-793446666872.us-central1.run.app"


@pytest.fixture
def backend(api_key, api_url):
    """Create a cloud backend for integration testing."""
    return CloudBackend(api_key=api_key, api_url=api_url, timeout=30)


class MockHTTPClient:
    """Mock HTTP client that simulates Graph API responses."""

    def __init__(self):
        self.memories = {}
        self.relationships = {}
        self.memory_counter = 1
        self.relationship_counter = 1

    async def request(self, method: str, url: str, json=None, params=None):
        """Simulate HTTP requests to the Graph API."""
        # Health check
        if url == "/health" and method == "GET":
            return self._create_response(200, {"status": "healthy", "version": "1.0.0"})

        # Statistics
        if url == "/graphs/statistics" and method == "GET":
            return self._create_response(200, {
                "total_memories": len(self.memories),
                "total_relationships": len(self.relationships),
                "memories_by_type": self._count_by_type()
            })

        # Recent activity (check before general /memories/ pattern)
        if url.startswith("/memories/recent") and method == "GET":
            recent = list(self.memories.values())[-10:]
            return self._create_response(200, {
                "recent_memories": recent,
                "memories_by_type": self._count_by_type(),
                "unresolved_problems": []
            })

        # Search memories (check before general /memories/ pattern)
        if url == "/memories/search" and method == "POST":
            results = self._search_memories(json)
            return self._create_response(200, {"memories": results})

        # Recall memories (check before general /memories/ pattern)
        if url == "/memories/recall" and method == "POST":
            results = self._search_memories(json)
            return self._create_response(200, {"memories": results})

        # Store memory
        if url == "/memories" and method == "POST":
            memory_id = f"mem_{self.memory_counter}"
            self.memory_counter += 1
            memory_data = {**json, "id": memory_id}
            self.memories[memory_id] = memory_data
            return self._create_response(200, {"id": memory_id})

        # Get memory
        if url.startswith("/memories/") and method == "GET":
            # Extract memory_id from URL
            parts = url.split("/")
            if len(parts) >= 3:
                memory_id = parts[2].split("?")[0]  # Remove query params

                # Check if it's a related memories request
                if url.endswith("/related") or "/related?" in url:
                    return self._handle_related_memories(memory_id, params)

                # Regular get memory
                if memory_id in self.memories:
                    return self._create_response(200, self.memories[memory_id])
            return self._create_response(404, {"detail": "Memory not found"})

        # Update memory
        if url.startswith("/memories/") and method == "PUT":
            memory_id = url.split("/")[2]
            if memory_id in self.memories:
                self.memories[memory_id].update(json)
                return self._create_response(200, self.memories[memory_id])
            return self._create_response(404, {"detail": "Memory not found"})

        # Delete memory
        if url.startswith("/memories/") and method == "DELETE":
            memory_id = url.split("/")[2]
            if memory_id in self.memories:
                del self.memories[memory_id]
                return self._create_response(204)
            return self._create_response(404, {"detail": "Memory not found"})

        # Create relationship
        if url == "/relationships" and method == "POST":
            rel_id = f"rel_{self.relationship_counter}"
            self.relationship_counter += 1
            rel_data = {**json, "id": rel_id}
            self.relationships[rel_id] = rel_data
            return self._create_response(200, {"id": rel_id})

        return self._create_response(404, {"detail": "Not found"})

    def _handle_related_memories(self, memory_id: str, params: dict):
        """Handle related memories request."""
        if memory_id not in self.memories:
            return self._create_response(404, {"detail": "Memory not found"})

        # Find all relationships involving this memory
        related = []
        for rel_id, rel_data in self.relationships.items():
            if rel_data["from_memory_id"] == memory_id:
                target_id = rel_data["to_memory_id"]
                if target_id in self.memories:
                    related.append({
                        "memory": self.memories[target_id],
                        "relationship": {
                            "type": rel_data["relationship_type"],
                            "strength": rel_data.get("strength", 0.5),
                            "confidence": rel_data.get("confidence", 0.8)
                        }
                    })

        return self._create_response(200, {"related_memories": related})

    def _search_memories(self, search_params: dict):
        """Simulate memory search."""
        results = []
        query = search_params.get("query", "").lower()
        memory_types = search_params.get("memory_types", [])
        tags = search_params.get("tags", [])
        limit = search_params.get("limit", 20)

        for memory in self.memories.values():
            # Filter by query (fuzzy - any word matches)
            if query:
                query_words = query.split()
                title = memory.get("title", "").lower()
                content = memory.get("content", "").lower()
                # Match if any query word is in title or content
                if not any(word in title or word in content for word in query_words):
                    continue

            # Filter by type
            if memory_types and memory.get("type") not in memory_types:
                continue

            # Filter by tags (if specified, must match at least one)
            if tags:
                memory_tags = memory.get("tags", [])
                if not any(tag in memory_tags for tag in tags):
                    continue

            results.append(memory)

            if len(results) >= limit:
                break

        return results

    def _count_by_type(self):
        """Count memories by type."""
        counts = {}
        for memory in self.memories.values():
            mem_type = memory.get("type", "general")
            counts[mem_type] = counts.get(mem_type, 0) + 1
        return counts

    def _create_response(self, status_code: int, json_data=None):
        """Create a mock HTTP response."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.headers = {}
        response.content = b'{}' if json_data else b''
        response.json.return_value = json_data or {}
        response.raise_for_status = MagicMock()
        return response

    async def aclose(self):
        """Close the client."""
        pass

    @property
    def is_closed(self):
        """Check if client is closed."""
        return False


class TestCloudBackendIntegration:
    """Integration tests for cloud backend with full workflows."""

    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self, backend):
        """Test complete memory lifecycle: store, retrieve, update, delete."""
        mock_client = MockHTTPClient()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client

            # 1. Connect
            connected = await backend.connect()
            assert connected is True

            # 2. Store a memory
            memory = Memory(
                type=MemoryType.PROBLEM,
                title="Redis timeout in production",
                content="Database connections timing out after 30 seconds",
                tags=["redis", "database", "production"],
                importance=0.9,
                context=MemoryContext(
                    project_path="/app/backend",
                    languages=["python"]
                )
            )

            memory_id = await backend.store_memory(memory)
            assert memory_id.startswith("mem_")

            # 3. Retrieve the memory
            retrieved = await backend.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.title == "Redis timeout in production"
            assert "redis" in retrieved.tags

            # 4. Update the memory
            updated = await backend.update_memory(
                memory_id,
                {"content": "Database connections timing out - root cause identified"}
            )
            assert updated is not None
            assert "root cause identified" in updated.content

            # 5. Delete the memory
            deleted = await backend.delete_memory(memory_id)
            assert deleted is True

            # 6. Verify deletion
            retrieved_after_delete = await backend.get_memory(memory_id)
            assert retrieved_after_delete is None

    @pytest.mark.asyncio
    async def test_problem_solution_workflow(self, backend):
        """Test storing a problem, solution, and creating relationship."""
        mock_client = MockHTTPClient()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client

            await backend.connect()

            # 1. Store problem
            problem = Memory(
                type=MemoryType.PROBLEM,
                title="High memory usage in API server",
                content="Memory grows continuously, reaching 8GB",
                tags=["performance", "memory"],
                importance=0.9
            )
            problem_id = await backend.store_memory(problem)

            # 2. Store solution
            solution = Memory(
                type=MemoryType.SOLUTION,
                title="Fix memory leak with connection pooling",
                content="Implemented connection pooling with max 50 connections",
                tags=["performance", "fix"],
                importance=0.9
            )
            solution_id = await backend.store_memory(solution)

            # 3. Create relationship
            rel_id = await backend.create_relationship(
                from_memory_id=solution_id,
                to_memory_id=problem_id,
                relationship_type=RelationshipType.SOLVES,
                properties=RelationshipProperties(
                    strength=0.95,
                    confidence=0.9,
                    context="Solution completely resolves the memory leak"
                )
            )
            assert rel_id.startswith("rel_")

            # 4. Get related memories
            related = await backend.get_related_memories(
                solution_id,
                relationship_types=[RelationshipType.SOLVES]
            )
            assert len(related) == 1
            related_memory, relationship = related[0]
            assert related_memory.title == "High memory usage in API server"
            assert relationship.type == RelationshipType.SOLVES

    @pytest.mark.asyncio
    async def test_search_and_recall_workflow(self, backend):
        """Test storing multiple memories and searching/recalling them."""
        mock_client = MockHTTPClient()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client

            await backend.connect()

            # Store multiple memories
            memories = [
                Memory(
                    type=MemoryType.SOLUTION,
                    title="Redis cache implementation",
                    content="Implemented Redis caching for API responses",
                    tags=["redis", "caching", "performance"]
                ),
                Memory(
                    type=MemoryType.PROBLEM,
                    title="Redis connection failures",
                    content="Redis connections dropping intermittently",
                    tags=["redis", "connection", "bug"]
                ),
                Memory(
                    type=MemoryType.CODE_PATTERN,
                    title="Repository pattern for database access",
                    content="Use repository pattern to abstract database operations",
                    tags=["design-pattern", "database"]
                )
            ]

            for memory in memories:
                await backend.store_memory(memory)

            # Search for Redis-related memories
            search_query = SearchQuery(
                query="redis",
                tags=["redis"],
                limit=10
            )
            results = await backend.search_memories(search_query)
            assert len(results) == 2

            # Recall with natural language
            recalled = await backend.recall_memories(
                query="Redis problems",
                memory_types=[MemoryType.PROBLEM],
                limit=5
            )
            assert len(recalled) == 1
            assert "connection failures" in recalled[0].title

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, backend):
        """Test that multiple operations can be performed sequentially."""
        mock_client = MockHTTPClient()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client

            await backend.connect()

            # Store multiple memories in sequence
            memory_ids = []
            for i in range(5):
                memory = Memory(
                    type=MemoryType.GENERAL,
                    title=f"Test memory {i}",
                    content=f"Content {i}",
                    tags=["test"]
                )
                memory_id = await backend.store_memory(memory)
                memory_ids.append(memory_id)

            # Verify all stored
            assert len(memory_ids) == 5

            # Get statistics
            stats = await backend.get_statistics()
            assert stats["total_memories"] == 5

            # Get recent activity
            activity = await backend.get_recent_activity(days=7)
            assert "recent_memories" in activity

    @pytest.mark.asyncio
    async def test_error_handling_during_workflow(self, backend):
        """Test error handling during a typical workflow."""
        mock_client = MockHTTPClient()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client

            await backend.connect()

            # Try to get non-existent memory
            result = await backend.get_memory("mem_nonexistent")
            assert result is None

            # Try to update non-existent memory (should raise)
            from memorygraph.models import MemoryNotFoundError
            with pytest.raises(MemoryNotFoundError):
                await backend.update_memory("mem_nonexistent", {"title": "New title"})

            # Store a memory
            memory = Memory(
                type=MemoryType.GENERAL,
                title="Test memory",
                content="Test content"
            )
            memory_id = await backend.store_memory(memory)

            # Get related memories for a memory (should return empty list)
            related = await backend.get_related_memories("mem_nonexistent")
            assert related == []

    @pytest.mark.asyncio
    async def test_health_check_workflow(self, backend):
        """Test health check integration."""
        mock_client = MockHTTPClient()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client

            # Health check before connection
            health = await backend.health_check()
            assert health["backend_type"] == "cloud"
            assert health["connected"] is True
            assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_cleanup_workflow(self, backend):
        """Test proper cleanup and disconnection."""
        mock_client = MockHTTPClient()

        with patch.object(backend, '_get_client', new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_client

            # Connect and use
            await backend.connect()

            memory = Memory(
                type=MemoryType.GENERAL,
                title="Test",
                content="Content"
            )
            await backend.store_memory(memory)

            # Disconnect
            await backend.disconnect()
            assert backend._connected is False
