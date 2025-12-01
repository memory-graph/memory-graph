"""
Integration tests for FalkorDBLite backend.

These tests use real FalkorDBLite (if available) to test the full backend implementation.
Tests are skipped if falkordblite is not installed.
"""

import pytest
import uuid
from datetime import datetime
import tempfile
import os

try:
    from falkordblite import FalkorDB
    from unittest.mock import MagicMock

    # Check if falkordblite is a mock object (from unit tests)
    # Verify it's the real package by checking if FalkorDB is callable and not a mock
    if isinstance(FalkorDB, MagicMock) or not callable(FalkorDB):
        FALKORDBLITE_AVAILABLE = False
    else:
        FALKORDBLITE_AVAILABLE = True
except ImportError:
    FALKORDBLITE_AVAILABLE = False

from memorygraph.backends.falkordblite_backend import FalkorDBLiteBackend
from memorygraph.models import (
    Memory,
    MemoryType,
    RelationshipType,
    RelationshipProperties,
    SearchQuery,
    MemoryContext,
)


@pytest.mark.skipif(not FALKORDBLITE_AVAILABLE, reason="falkordblite not installed")
class TestFalkorDBLiteIntegration:
    """Integration tests with real FalkorDBLite database."""

    @pytest.fixture
    async def backend(self):
        """Create a temporary FalkorDBLite backend for testing."""
        # Use temporary file for test database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            backend = FalkorDBLiteBackend(db_path=db_path)
            await backend.connect()
            await backend.initialize_schema()
            yield backend
            await backend.disconnect()
        finally:
            # Clean up temporary file
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_store_and_retrieve_memory(self, backend):
        """Test storing and retrieving a memory."""
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test Memory",
            content="This is a test memory for FalkorDBLite",
            tags=["test", "integration"],
            importance=0.8,
            confidence=0.9
        )

        # Store memory
        memory_id = await backend.store_memory(memory)
        assert memory_id is not None

        # Retrieve memory
        retrieved = await backend.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved.title == "Test Memory"
        assert retrieved.content == "This is a test memory for FalkorDBLite"
        assert "test" in retrieved.tags
        assert "integration" in retrieved.tags

    @pytest.mark.asyncio
    async def test_update_memory(self, backend):
        """Test updating a memory."""
        memory = Memory(
            type=MemoryType.PROBLEM,
            title="Original Title",
            content="Original content",
            tags=["original"],
            importance=0.5,
            confidence=0.7
        )

        # Store memory
        memory_id = await backend.store_memory(memory)

        # Update memory
        memory.title = "Updated Title"
        memory.content = "Updated content"
        memory.tags = ["updated"]
        memory.importance = 0.9

        success = await backend.update_memory(memory)
        assert success

        # Verify update
        retrieved = await backend.get_memory(memory_id)
        assert retrieved.title == "Updated Title"
        assert retrieved.content == "Updated content"
        assert "updated" in retrieved.tags
        assert retrieved.importance == 0.9

    @pytest.mark.asyncio
    async def test_delete_memory(self, backend):
        """Test deleting a memory."""
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="To Be Deleted",
            content="This memory will be deleted",
            tags=["delete"],
            importance=0.5,
            confidence=0.5
        )

        # Store memory
        memory_id = await backend.store_memory(memory)

        # Verify it exists
        retrieved = await backend.get_memory(memory_id)
        assert retrieved is not None

        # Delete memory
        success = await backend.delete_memory(memory_id)
        assert success

        # Verify it's gone
        deleted = await backend.get_memory(memory_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_search_memories(self, backend):
        """Test searching for memories."""
        # Store multiple memories
        memory1 = Memory(
            type=MemoryType.SOLUTION,
            title="Python Async Solution",
            content="How to use async/await in Python",
            tags=["python", "async"],
            importance=0.8,
            confidence=0.9
        )
        await backend.store_memory(memory1)

        memory2 = Memory(
            type=MemoryType.PROBLEM,
            title="JavaScript Async Problem",
            content="Promise chain is too complex",
            tags=["javascript", "async"],
            importance=0.6,
            confidence=0.7
        )
        await backend.store_memory(memory2)

        memory3 = Memory(
            type=MemoryType.SOLUTION,
            title="Database Query Optimization",
            content="Added index to improve query performance",
            tags=["database", "performance"],
            importance=0.7,
            confidence=0.8
        )
        await backend.store_memory(memory3)

        # Search by query text
        query = SearchQuery(query="async")
        results = await backend.search_memories(query)
        assert len(results) >= 2

        # Search by tags
        query = SearchQuery(tags=["python"])
        results = await backend.search_memories(query)
        assert len(results) >= 1
        assert any("python" in r.tags for r in results)

        # Search by type
        query = SearchQuery(memory_types=[MemoryType.SOLUTION])
        results = await backend.search_memories(query)
        assert len(results) >= 2
        assert all(r.type == MemoryType.SOLUTION for r in results)

        # Search by importance
        query = SearchQuery(min_importance=0.75)
        results = await backend.search_memories(query)
        assert len(results) >= 1
        assert all(r.importance >= 0.75 for r in results)

    @pytest.mark.asyncio
    async def test_create_and_retrieve_relationships(self, backend):
        """Test creating relationships between memories."""
        # Create two memories
        problem = Memory(
            type=MemoryType.PROBLEM,
            title="Connection Timeout",
            content="Database connections timing out",
            tags=["database", "timeout"],
            importance=0.8,
            confidence=0.9
        )
        problem_id = await backend.store_memory(problem)

        solution = Memory(
            type=MemoryType.SOLUTION,
            title="Increase Connection Pool",
            content="Increased max connections to 50",
            tags=["database", "fix"],
            importance=0.9,
            confidence=0.95
        )
        solution_id = await backend.store_memory(solution)

        # Create relationship
        props = RelationshipProperties(
            strength=0.9,
            confidence=0.85,
            context="This solution fixed the timeout problem"
        )
        rel_id = await backend.create_relationship(
            from_memory_id=solution_id,
            to_memory_id=problem_id,
            relationship_type=RelationshipType.SOLVES,
            properties=props
        )
        assert rel_id is not None

        # Retrieve related memories
        related = await backend.get_related_memories(problem_id)
        assert len(related) >= 1

        # Check the relationship
        found = False
        for memory, relationship in related:
            if memory.id == solution_id:
                found = True
                assert relationship.type == RelationshipType.SOLVES
                break
        assert found, "Related memory not found"

    @pytest.mark.asyncio
    async def test_memory_with_context(self, backend):
        """Test storing and retrieving memory with context."""
        context = MemoryContext(
            project_path="/test/project",
            file_path="/test/project/main.py",
            function_name="process_data",
            line_numbers=[42, 43, 44],
            user="test_user",
            session_id="test_session_123",
            additional_metadata={"version": "1.0.0", "environment": "test"}
        )

        memory = Memory(
            type=MemoryType.CODE_PATTERN,
            title="Data Processing Pattern",
            content="Efficient data processing using generators",
            tags=["python", "generators", "performance"],
            importance=0.85,
            confidence=0.9,
            context=context
        )

        # Store memory with context
        memory_id = await backend.store_memory(memory)

        # Retrieve and verify context
        retrieved = await backend.get_memory(memory_id)
        assert retrieved is not None
        assert retrieved.context is not None
        assert retrieved.context.project_path == "/test/project"
        assert retrieved.context.file_path == "/test/project/main.py"
        assert retrieved.context.function_name == "process_data"
        assert retrieved.context.line_numbers == [42, 43, 44]
        assert retrieved.context.user == "test_user"
        assert retrieved.context.additional_metadata.get("version") == "1.0.0"

    @pytest.mark.asyncio
    async def test_get_memory_statistics(self, backend):
        """Test retrieving database statistics."""
        # Store some memories
        for i in range(5):
            memory = Memory(
                type=MemoryType.SOLUTION if i % 2 == 0 else MemoryType.PROBLEM,
                title=f"Memory {i}",
                content=f"Content {i}",
                tags=["test"],
                importance=0.5 + (i * 0.1),
                confidence=0.8
            )
            await backend.store_memory(memory)

        # Get statistics
        stats = await backend.get_memory_statistics()

        assert "total_memories" in stats
        assert stats["total_memories"]["count"] >= 5

        assert "memories_by_type" in stats
        assert len(stats["memories_by_type"]) >= 1

    @pytest.mark.asyncio
    async def test_health_check(self, backend):
        """Test health check functionality."""
        health = await backend.health_check()

        assert health["connected"] is True
        assert health["backend_type"] == "falkordblite"
        assert "db_path" in health
        assert "graph_name" in health
        assert "statistics" in health

    @pytest.mark.asyncio
    async def test_backend_capabilities(self, backend):
        """Test backend capability reporting."""
        assert backend.backend_name() == "falkordblite"
        assert backend.supports_fulltext_search() is True
        assert backend.supports_transactions() is True

    @pytest.mark.asyncio
    async def test_multiple_relationships(self, backend):
        """Test creating multiple relationships with different types."""
        # Create memories
        mem1 = Memory(
            type=MemoryType.PROBLEM,
            title="Issue A",
            content="Description A",
            tags=["issue"],
            importance=0.7,
            confidence=0.8
        )
        id1 = await backend.store_memory(mem1)

        mem2 = Memory(
            type=MemoryType.SOLUTION,
            title="Solution B",
            content="Description B",
            tags=["solution"],
            importance=0.8,
            confidence=0.9
        )
        id2 = await backend.store_memory(mem2)

        mem3 = Memory(
            type=MemoryType.SOLUTION,
            title="Alternative C",
            content="Description C",
            tags=["solution"],
            importance=0.75,
            confidence=0.85
        )
        id3 = await backend.store_memory(mem3)

        # Create different relationship types
        await backend.create_relationship(
            id2, id1, RelationshipType.SOLVES,
            RelationshipProperties(strength=0.9, confidence=0.9)
        )

        await backend.create_relationship(
            id3, id1, RelationshipType.SOLVES,
            RelationshipProperties(strength=0.8, confidence=0.85)
        )

        await backend.create_relationship(
            id3, id2, RelationshipType.ALTERNATIVE_TO,
            RelationshipProperties(strength=0.7, confidence=0.8)
        )

        # Get related memories
        related = await backend.get_related_memories(id1)
        assert len(related) >= 2

        # Verify relationship types
        rel_types = [rel.type for _, rel in related]
        assert RelationshipType.SOLVES in rel_types
