"""
Integration tests for FalkorDB backend.

These tests require a running FalkorDB instance (e.g., via Docker).
They verify end-to-end functionality with a real database.

To run FalkorDB locally:
    docker run -p 6379:6379 -it --rm falkordb/falkordb:latest
"""

import pytest
import os
from datetime import datetime
import uuid

from memorygraph.backends.falkordb_backend import FalkorDBBackend
from memorygraph.models import (
    Memory,
    MemoryType,
    RelationshipType,
    RelationshipProperties,
    SearchQuery,
    DatabaseConnectionError,
)


# Check if FalkorDB is available
def is_falkordb_available():
    """Check if FalkorDB is available for testing."""
    try:
        import falkordb
        # Try to connect to localhost
        host = os.getenv("FALKORDB_HOST", "localhost")
        port = int(os.getenv("FALKORDB_PORT", "6379"))
        try:
            client = falkordb.FalkorDB(host=host, port=port)
            graph = client.select_graph("test_connection")
            # Try a simple query to verify it's working
            graph.query("RETURN 1")
            return True
        except Exception:
            return False
    except ImportError:
        return False


FALKORDB_AVAILABLE = is_falkordb_available()
skip_if_no_falkordb = pytest.mark.skipif(
    not FALKORDB_AVAILABLE,
    reason="FalkorDB not available. Run: docker run -p 6379:6379 -it --rm falkordb/falkordb:latest"
)


@pytest.fixture
async def falkordb_backend():
    """Create a FalkorDB backend for testing."""
    if not FALKORDB_AVAILABLE:
        pytest.skip("FalkorDB not available")

    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", "6379"))

    backend = FalkorDBBackend(host=host, port=port, graph_name="test_memorygraph")
    await backend.connect()
    await backend.initialize_schema()

    yield backend

    # Cleanup: Delete all test data
    try:
        await backend.execute_query("MATCH (n) DETACH DELETE n", write=True)
    except Exception:
        pass

    await backend.disconnect()


@skip_if_no_falkordb
class TestFalkorDBIntegration:
    """Integration tests for FalkorDB backend."""

    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self, falkordb_backend):
        """Test creating, reading, updating, and deleting a memory."""
        # Create a memory
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Redis Connection Pool Fix",
            content="Increased max connections from 10 to 50 to handle concurrent requests",
            tags=["redis", "performance", "connection-pool"],
            importance=0.9,
            confidence=0.95
        )

        # Store the memory
        memory_id = await falkordb_backend.store_memory(memory)
        assert memory_id is not None
        assert memory_id == memory.id

        # Retrieve the memory
        retrieved = await falkordb_backend.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved.id == memory_id
        assert retrieved.title == "Redis Connection Pool Fix"
        assert retrieved.type == MemoryType.SOLUTION
        assert "redis" in retrieved.tags

        # Update the memory
        retrieved.title = "Updated Redis Connection Pool Fix"
        retrieved.importance = 1.0
        update_result = await falkordb_backend.update_memory(retrieved)
        assert update_result is True

        # Verify update
        updated = await falkordb_backend.get_memory(memory_id)
        assert updated.title == "Updated Redis Connection Pool Fix"
        assert updated.importance == 1.0

        # Delete the memory
        delete_result = await falkordb_backend.delete_memory(memory_id)
        assert delete_result is True

        # Verify deletion
        deleted = await falkordb_backend.get_memory(memory_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_relationship_creation_and_traversal(self, falkordb_backend):
        """Test creating relationships and traversing the graph."""
        # Create two memories
        problem = Memory(
            type=MemoryType.PROBLEM,
            title="High API Latency",
            content="API endpoints showing 2-3 second response times",
            tags=["api", "performance"],
            importance=0.8
        )

        solution = Memory(
            type=MemoryType.SOLUTION,
            title="Implemented Caching Layer",
            content="Added Redis caching for frequently accessed data",
            tags=["redis", "caching", "performance"],
            importance=0.9
        )

        # Store both memories
        problem_id = await falkordb_backend.store_memory(problem)
        solution_id = await falkordb_backend.store_memory(solution)

        # Create relationship
        props = RelationshipProperties(
            strength=0.95,
            confidence=0.9,
            context="Caching reduced API latency from 2-3s to 50-100ms"
        )

        rel_id = await falkordb_backend.create_relationship(
            from_memory_id=solution_id,
            to_memory_id=problem_id,
            relationship_type=RelationshipType.SOLVES,
            properties=props
        )

        assert rel_id is not None

        # Get related memories
        related = await falkordb_backend.get_related_memories(problem_id)
        assert len(related) > 0

        # Find the solution in related memories
        found_solution = False
        for related_memory, relationship in related:
            if related_memory.id == solution_id:
                found_solution = True
                assert relationship.type == RelationshipType.SOLVES
                assert relationship.properties.strength == 0.95
                break

        assert found_solution, "Solution should be in related memories"

    @pytest.mark.asyncio
    async def test_search_functionality(self, falkordb_backend):
        """Test search across multiple memories."""
        # Create several memories
        memories_data = [
            ("Redis Timeout Issue", "Connection timeouts after 30 seconds", ["redis", "timeout"]),
            ("Database Query Optimization", "Optimized slow queries using indexes", ["database", "performance"]),
            ("Redis Cache Implementation", "Implemented Redis for session storage", ["redis", "caching"]),
        ]

        memory_ids = []
        for title, content, tags in memories_data:
            memory = Memory(
                type=MemoryType.SOLUTION,
                title=title,
                content=content,
                tags=tags,
                importance=0.7
            )
            mem_id = await falkordb_backend.store_memory(memory)
            memory_ids.append(mem_id)

        # Search for "redis" - should find 2 memories
        query = SearchQuery(query="redis", limit=10)
        results = await falkordb_backend.search_memories(query)

        assert len(results) >= 2
        redis_titles = [m.title for m in results]
        assert any("Redis" in title for title in redis_titles)

        # Search by tag
        query = SearchQuery(tags=["timeout"], limit=10)
        results = await falkordb_backend.search_memories(query)

        assert len(results) >= 1
        assert any("Timeout" in m.title for m in results)

        # Search by memory type
        query = SearchQuery(memory_types=[MemoryType.SOLUTION], limit=10)
        results = await falkordb_backend.search_memories(query)

        assert len(results) >= 3
        assert all(m.type == MemoryType.SOLUTION for m in results)

    @pytest.mark.asyncio
    async def test_statistics(self, falkordb_backend):
        """Test statistics gathering."""
        # Create some test data
        for i in range(3):
            memory = Memory(
                type=MemoryType.SOLUTION if i % 2 == 0 else MemoryType.PROBLEM,
                title=f"Test Memory {i}",
                content=f"Content {i}",
                tags=["test"],
                importance=0.5
            )
            await falkordb_backend.store_memory(memory)

        # Get statistics
        stats = await falkordb_backend.get_memory_statistics()

        assert "total_memories" in stats
        assert stats["total_memories"]["count"] >= 3

        assert "memories_by_type" in stats
        assert len(stats["memories_by_type"]) > 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, falkordb_backend):
        """Test handling of concurrent operations."""
        import asyncio

        # Create multiple memories concurrently
        async def create_memory(index):
            memory = Memory(
                type=MemoryType.SOLUTION,
                title=f"Concurrent Memory {index}",
                content=f"Content {index}",
                tags=["concurrent", "test"],
                importance=0.5
            )
            return await falkordb_backend.store_memory(memory)

        # Create 10 memories concurrently
        tasks = [create_memory(i) for i in range(10)]
        memory_ids = await asyncio.gather(*tasks)

        assert len(memory_ids) == 10
        assert all(mid is not None for mid in memory_ids)

        # Verify all memories were created
        for mem_id in memory_ids:
            memory = await falkordb_backend.get_memory(mem_id)
            assert memory is not None

    @pytest.mark.asyncio
    async def test_health_check(self, falkordb_backend):
        """Test health check functionality."""
        health = await falkordb_backend.health_check()

        assert health["connected"] is True
        assert health["backend_type"] == "falkordb"
        assert "host" in health
        assert "port" in health
        assert "statistics" in health
