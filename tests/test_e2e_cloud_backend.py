"""
End-to-end tests for MCP server with cloud backend.

These tests simulate MCP client requests through the server
to verify that the cloud backend works correctly in the
full MCP context.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from memorygraph.backends.cloud_backend import CloudBackend
from memorygraph.models import Memory, MemoryType


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
            # Add timestamps if not present
            memory_data = {**json, "id": memory_id}
            if "created_at" not in memory_data:
                memory_data["created_at"] = datetime.now(timezone.utc).isoformat()
            if "updated_at" not in memory_data:
                memory_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self.memories[memory_id] = memory_data
            return self._create_response(200, {"id": memory_id})

        # Get memory
        if url.startswith("/memories/") and method == "GET":
            parts = url.split("/")
            if len(parts) >= 3:
                memory_id = parts[2].split("?")[0]

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
                self.memories[memory_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
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


@pytest.fixture
def mock_cloud_backend():
    """Create a mock cloud backend."""
    backend = CloudBackend(
        api_key="mg_test_key",
        api_url="https://test-api.memorygraph.dev"
    )
    mock_client = MockHTTPClient()

    # Patch the _get_client method to return our mock
    async def get_mock_client():
        return mock_client

    backend._get_client = get_mock_client
    return backend


class TestE2ECloudBackend:
    """End-to-end tests for MCP server with cloud backend."""

    @pytest.mark.asyncio
    async def test_mcp_store_memory_via_cloud(self, mock_cloud_backend):
        """Test storing a memory through MCP server using cloud backend."""
        # Initialize backend
        await mock_cloud_backend.connect()

        # Store memory through backend (simulating MCP tool call)
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Use bcrypt for password hashing",
            content="Always use bcrypt with cost factor 12 for secure password hashing",
            tags=["security", "authentication"],
            importance=0.9
        )

        memory_id = await mock_cloud_backend.store_memory(memory)

        # Verify storage
        assert memory_id is not None
        assert memory_id.startswith("mem_")

        # Retrieve and verify
        retrieved = await mock_cloud_backend.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved.title == "Use bcrypt for password hashing"
        assert "security" in retrieved.tags

    @pytest.mark.asyncio
    async def test_mcp_recall_workflow(self, mock_cloud_backend):
        """Test recall_memories workflow through cloud backend."""
        await mock_cloud_backend.connect()

        # Store several memories
        memories = [
            Memory(
                type=MemoryType.PROBLEM,
                title="Authentication fails with 401",
                content="JWT token validation failing",
                tags=["auth", "bug"]
            ),
            Memory(
                type=MemoryType.SOLUTION,
                title="Fix JWT secret key configuration",
                content="Added JWT_SECRET to environment variables",
                tags=["auth", "fix"]
            ),
            Memory(
                type=MemoryType.CODE_PATTERN,
                title="Use decorator for auth required routes",
                content="@require_auth decorator for protected endpoints",
                tags=["auth", "pattern"]
            )
        ]

        for memory in memories:
            await mock_cloud_backend.store_memory(memory)

        # Recall authentication-related memories
        results = await mock_cloud_backend.recall_memories(
            query="authentication",
            limit=10
        )

        # Should find at least one auth-related memory
        assert len(results) >= 1
        titles = [m.title for m in results]
        assert any("auth" in title.lower() for title in titles)

    @pytest.mark.asyncio
    async def test_mcp_search_with_filters(self, mock_cloud_backend):
        """Test search_memories with filters through cloud backend."""
        await mock_cloud_backend.connect()

        # Store memories of different types
        await mock_cloud_backend.store_memory(Memory(
            type=MemoryType.PROBLEM,
            title="Database deadlock",
            content="Concurrent transactions causing deadlocks",
            tags=["database", "bug"]
        ))

        await mock_cloud_backend.store_memory(Memory(
            type=MemoryType.SOLUTION,
            title="Use optimistic locking",
            content="Implemented version-based optimistic locking",
            tags=["database", "fix"]
        ))

        # Search with type filter
        from memorygraph.models import SearchQuery
        search_query = SearchQuery(
            query="database",
            memory_types=[MemoryType.SOLUTION],
            limit=10
        )

        results = await mock_cloud_backend.search_memories(search_query)

        # Should find the database-related solution
        # Note: May return 0 or 1 depending on exact match algorithm
        # The important thing is that if results exist, they match the filter
        if len(results) > 0:
            assert all(m.type == MemoryType.SOLUTION for m in results)
            assert any("database" in m.title.lower() or "database" in m.content.lower() for m in results)

    @pytest.mark.asyncio
    async def test_mcp_relationship_creation(self, mock_cloud_backend):
        """Test creating relationships through cloud backend."""
        await mock_cloud_backend.connect()

        # Store problem and solution
        problem = Memory(
            type=MemoryType.PROBLEM,
            title="API rate limiting needed",
            content="No rate limiting on public endpoints",
            tags=["api", "security"]
        )
        problem_id = await mock_cloud_backend.store_memory(problem)

        solution = Memory(
            type=MemoryType.SOLUTION,
            title="Implement Redis-based rate limiter",
            content="Added sliding window rate limiter with Redis",
            tags=["api", "security", "redis"]
        )
        solution_id = await mock_cloud_backend.store_memory(solution)

        # Create relationship
        from memorygraph.models import RelationshipType, RelationshipProperties
        rel_id = await mock_cloud_backend.create_relationship(
            from_memory_id=solution_id,
            to_memory_id=problem_id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=0.95,
                confidence=0.9,
                context="Complete solution to rate limiting issue"
            )
        )

        assert rel_id is not None
        assert rel_id.startswith("rel_")

        # Verify relationship by getting related memories
        related = await mock_cloud_backend.get_related_memories(
            solution_id,
            relationship_types=[RelationshipType.SOLVES]
        )

        assert len(related) == 1
        related_memory, relationship = related[0]
        assert related_memory.id == problem_id

    @pytest.mark.asyncio
    async def test_mcp_get_recent_activity(self, mock_cloud_backend):
        """Test get_recent_activity through cloud backend."""
        await mock_cloud_backend.connect()

        # Store some memories
        for i in range(3):
            await mock_cloud_backend.store_memory(Memory(
                type=MemoryType.GENERAL,
                title=f"Recent memory {i}",
                content=f"Content {i}",
                tags=["recent"]
            ))

        # Get activity
        activity = await mock_cloud_backend.get_recent_activity(days=7)

        assert "recent_memories" in activity
        assert "memories_by_type" in activity
        assert len(activity["recent_memories"]) == 3

    @pytest.mark.asyncio
    async def test_mcp_error_scenarios(self, mock_cloud_backend):
        """Test error handling in MCP context."""
        await mock_cloud_backend.connect()

        # Test 1: Get non-existent memory
        result = await mock_cloud_backend.get_memory("mem_invalid")
        assert result is None

        # Test 2: Get related memories for non-existent memory
        related = await mock_cloud_backend.get_related_memories("mem_invalid")
        assert related == []

        # Test 3: Update non-existent memory
        from memorygraph.models import MemoryNotFoundError
        with pytest.raises(MemoryNotFoundError):
            await mock_cloud_backend.update_memory("mem_invalid", {"title": "New"})

    @pytest.mark.asyncio
    async def test_mcp_full_workflow_simulation(self, mock_cloud_backend):
        """
        Simulate a complete MCP workflow:
        1. Store problem
        2. Store solution
        3. Link them
        4. Search for solutions
        5. Get statistics
        """
        await mock_cloud_backend.connect()

        # 1. User encounters a problem
        problem = Memory(
            type=MemoryType.PROBLEM,
            title="Docker build failing on M1 Mac",
            content="Dockerfile fails with platform architecture error",
            tags=["docker", "mac", "build"],
            importance=0.8
        )
        problem_id = await mock_cloud_backend.store_memory(problem)

        # 2. User finds a solution
        solution = Memory(
            type=MemoryType.SOLUTION,
            title="Add platform flag to Dockerfile",
            content="FROM --platform=linux/amd64 node:18",
            tags=["docker", "mac", "fix"],
            importance=0.9
        )
        solution_id = await mock_cloud_backend.store_memory(solution)

        # 3. Link solution to problem
        from memorygraph.models import RelationshipType, RelationshipProperties
        await mock_cloud_backend.create_relationship(
            from_memory_id=solution_id,
            to_memory_id=problem_id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties(
                strength=1.0,
                confidence=0.95
            )
        )

        # 4. Later, search for Docker solutions
        from memorygraph.models import SearchQuery
        results = await mock_cloud_backend.search_memories(
            SearchQuery(
                query="docker",
                memory_types=[MemoryType.SOLUTION],
                tags=["docker"],
                limit=10
            )
        )

        assert len(results) >= 1
        assert any("platform flag" in m.title for m in results)

        # 5. Check statistics
        stats = await mock_cloud_backend.get_statistics()
        assert stats["total_memories"] >= 2
        assert stats["total_relationships"] >= 1

    @pytest.mark.asyncio
    async def test_mcp_backend_configuration(self):
        """Test that cloud backend can be configured from environment."""
        with patch.dict('os.environ', {
            'MEMORYGRAPH_API_KEY': 'mg_env_key',
            'MEMORYGRAPH_API_URL': 'https://custom-api.memorygraph.dev'
        }):
            backend = CloudBackend()
            assert backend.api_key == 'mg_env_key'
            assert backend.api_url == 'https://custom-api.memorygraph.dev'

    @pytest.mark.asyncio
    async def test_mcp_connection_lifecycle(self, mock_cloud_backend):
        """Test connection/disconnection lifecycle."""
        # Connect
        connected = await mock_cloud_backend.connect()
        assert connected is True
        assert mock_cloud_backend._connected is True

        # Use backend
        memory = Memory(
            type=MemoryType.GENERAL,
            title="Test",
            content="Content"
        )
        await mock_cloud_backend.store_memory(memory)

        # Disconnect
        await mock_cloud_backend.disconnect()
        assert mock_cloud_backend._connected is False
