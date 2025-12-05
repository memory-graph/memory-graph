"""Tests for chain tool handlers.

This module tests all handlers in chain_tools.py with comprehensive
coverage of success cases, error cases, and edge cases.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from memorygraph.models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    RelationshipProperties,
)


@pytest.fixture
def mock_memory_db():
    """Create a mock memory database."""
    db = AsyncMock()
    return db


@pytest.fixture
def sample_memories():
    """Create sample memories for chain testing."""
    return {
        "problem": Memory(
            id="problem-1",
            type=MemoryType.PROBLEM,
            title="Redis timeout issue",
            content="Redis connections timing out",
            tags=["redis", "timeout"],
            importance=0.8,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        "solution": Memory(
            id="solution-1",
            type=MemoryType.SOLUTION,
            title="Use connection pooling",
            content="Implement connection pooling",
            tags=["redis", "solution"],
            importance=0.9,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        "dependency": Memory(
            id="dep-1",
            type=MemoryType.CODE_PATTERN,
            title="Redis pool config",
            content="Configuration for Redis pool",
            tags=["redis", "config"],
            importance=0.7,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    }


@pytest.fixture
def sample_relationships():
    """Create sample relationships for chain testing."""
    return {
        "solves": Relationship(
            from_memory_id="solution-1",
            to_memory_id="problem-1",
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(strength=0.9, confidence=0.8),
        ),
        "depends": Relationship(
            from_memory_id="solution-1",
            to_memory_id="dep-1",
            type=RelationshipType.DEPENDS_ON,
            properties=RelationshipProperties(strength=0.8, confidence=0.9),
        ),
    }


class TestFindChain:
    """Tests for find_chain handler."""

    async def test_find_chain_single_relationship(
        self, mock_memory_db, sample_memories, sample_relationships
    ):
        """Test finding a simple chain with one relationship."""
        from memorygraph.tools.chain_tools import handle_find_chain

        # Setup mock to return related memory
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["problem"], sample_relationships["solves"])
        ]

        # Execute
        result = await handle_find_chain(
            mock_memory_db,
            {
                "memory_id": "solution-1",
                "relationship_type": "SOLVES",
                "max_depth": 1,
            }
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "chain" in content_text.lower() or "found" in content_text.lower()
        assert "problem-1" in content_text or "Redis timeout" in content_text

    async def test_find_chain_multiple_hops(self, mock_memory_db, sample_memories):
        """Test finding a chain with multiple hops."""
        from memorygraph.tools.chain_tools import handle_find_chain

        intermediate = Memory(
            id="intermediate-1",
            type=MemoryType.SOLUTION,
            title="Intermediate solution",
            content="Intermediate",
            tags=["test"],
            importance=0.7,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # First call returns intermediate, second call returns final
        mock_memory_db.get_related_memories.side_effect = [
            [(intermediate, Relationship(
                from_memory_id="solution-1",
                to_memory_id="intermediate-1",
                type=RelationshipType.DEPENDS_ON,
                properties=RelationshipProperties(strength=0.8, confidence=0.8),
            ))],
            [(sample_memories["dependency"], Relationship(
                from_memory_id="intermediate-1",
                to_memory_id="dep-1",
                type=RelationshipType.DEPENDS_ON,
                properties=RelationshipProperties(strength=0.7, confidence=0.9),
            ))],
            []  # No more connections
        ]

        # Execute
        result = await handle_find_chain(
            mock_memory_db,
            {
                "memory_id": "solution-1",
                "relationship_type": "DEPENDS_ON",
                "max_depth": 2,
            }
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "intermediate-1" in content_text or "Intermediate" in content_text

    async def test_find_chain_no_relationships(self, mock_memory_db):
        """Test finding chain when no relationships exist."""
        from memorygraph.tools.chain_tools import handle_find_chain

        # Setup mock to return empty list
        mock_memory_db.get_related_memories.return_value = []

        # Execute
        result = await handle_find_chain(
            mock_memory_db,
            {
                "memory_id": "solution-1",
                "relationship_type": "SOLVES",
                "max_depth": 1,
            }
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "No" in content_text or "not found" in content_text.lower() or "0" in content_text

    async def test_find_chain_with_cycle_detection(self, mock_memory_db, sample_memories):
        """Test that cycles are detected and prevented."""
        from memorygraph.tools.chain_tools import handle_find_chain

        # Create circular reference
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["solution"], Relationship(
                from_memory_id="problem-1",
                to_memory_id="solution-1",
                type=RelationshipType.CAUSES,
                properties=RelationshipProperties(strength=0.5, confidence=0.5),
            ))
        ]

        # Execute
        result = await handle_find_chain(
            mock_memory_db,
            {
                "memory_id": "solution-1",
                "relationship_type": "CAUSES",
                "max_depth": 3,
            }
        )

        # Verify - should not infinite loop
        assert result.isError is not True

    async def test_find_chain_max_depth_limit(self, mock_memory_db, sample_memories):
        """Test that max_depth is respected."""
        from memorygraph.tools.chain_tools import handle_find_chain

        # Setup mock to always return a relationship
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["problem"], Relationship(
                from_memory_id="any",
                to_memory_id="any",
                type=RelationshipType.DEPENDS_ON,
                properties=RelationshipProperties(strength=0.5, confidence=0.5),
            ))
        ]

        # Execute with depth 1
        result = await handle_find_chain(
            mock_memory_db,
            {
                "memory_id": "solution-1",
                "relationship_type": "DEPENDS_ON",
                "max_depth": 1,
            }
        )

        # Verify - should only make one traversal
        assert result.isError is not True
        # get_related_memories should be called limited number of times
        assert mock_memory_db.get_related_memories.call_count <= 2

    async def test_find_chain_missing_memory_id(self, mock_memory_db):
        """Test error when memory_id is missing."""
        from memorygraph.tools.chain_tools import handle_find_chain

        # Execute without memory_id
        result = await handle_find_chain(
            mock_memory_db,
            {
                "relationship_type": "SOLVES",
            }
        )

        # Verify error
        assert result.isError is True
        assert "required" in result.content[0].text.lower() or "missing" in result.content[0].text.lower()

    async def test_find_chain_error_handling(self, mock_memory_db):
        """Test error handling when database query fails."""
        from memorygraph.tools.chain_tools import handle_find_chain

        # Setup mock to raise exception
        mock_memory_db.get_related_memories.side_effect = Exception("Database error")

        # Execute
        result = await handle_find_chain(
            mock_memory_db,
            {
                "memory_id": "solution-1",
                "relationship_type": "SOLVES",
            }
        )

        # Verify error is handled
        assert result.isError is True
        assert "Failed" in result.content[0].text or "Error" in result.content[0].text


class TestTraceDependencies:
    """Tests for trace_dependencies handler."""

    async def test_trace_dependencies_simple(self, mock_memory_db, sample_memories, sample_relationships):
        """Test tracing dependencies for a memory."""
        from memorygraph.tools.chain_tools import handle_trace_dependencies

        # Setup mock to return dependency
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["dependency"], sample_relationships["depends"])
        ]

        # Execute
        result = await handle_trace_dependencies(
            mock_memory_db,
            {"memory_id": "solution-1"}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "dep-1" in content_text or "Redis pool config" in content_text
        assert "dependenc" in content_text.lower()

    async def test_trace_dependencies_nested(self, mock_memory_db, sample_memories):
        """Test tracing nested dependencies."""
        from memorygraph.tools.chain_tools import handle_trace_dependencies

        dep2 = Memory(
            id="dep-2",
            type=MemoryType.TECHNOLOGY,
            title="Redis library",
            content="Redis client library",
            tags=["redis", "library"],
            importance=0.6,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # First call returns dep-1, second call returns dep-2
        mock_memory_db.get_related_memories.side_effect = [
            [(sample_memories["dependency"], Relationship(
                from_memory_id="solution-1",
                to_memory_id="dep-1",
                type=RelationshipType.DEPENDS_ON,
                properties=RelationshipProperties(strength=0.8, confidence=0.9),
            ))],
            [(dep2, Relationship(
                from_memory_id="dep-1",
                to_memory_id="dep-2",
                type=RelationshipType.REQUIRES,
                properties=RelationshipProperties(strength=0.7, confidence=0.8),
            ))],
            []  # No more dependencies
        ]

        # Execute
        result = await handle_trace_dependencies(
            mock_memory_db,
            {"memory_id": "solution-1"}
        )

        # Verify both dependencies are found
        assert result.isError is not True
        content_text = result.content[0].text
        assert "dep-1" in content_text or "Redis pool config" in content_text
        assert "dep-2" in content_text or "Redis library" in content_text

    async def test_trace_dependencies_none(self, mock_memory_db):
        """Test tracing dependencies when none exist."""
        from memorygraph.tools.chain_tools import handle_trace_dependencies

        # Setup mock to return empty list
        mock_memory_db.get_related_memories.return_value = []

        # Execute
        result = await handle_trace_dependencies(
            mock_memory_db,
            {"memory_id": "solution-1"}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "No" in content_text or "not found" in content_text.lower() or "0" in content_text

    async def test_trace_dependencies_circular(self, mock_memory_db, sample_memories):
        """Test circular dependency detection."""
        from memorygraph.tools.chain_tools import handle_trace_dependencies

        # Create circular dependency: solution -> dep-1 -> solution
        mock_memory_db.get_related_memories.side_effect = [
            [(sample_memories["dependency"], Relationship(
                from_memory_id="solution-1",
                to_memory_id="dep-1",
                type=RelationshipType.DEPENDS_ON,
                properties=RelationshipProperties(strength=0.8, confidence=0.9),
            ))],
            [(sample_memories["solution"], Relationship(
                from_memory_id="dep-1",
                to_memory_id="solution-1",
                type=RelationshipType.DEPENDS_ON,
                properties=RelationshipProperties(strength=0.5, confidence=0.5),
            ))],
        ]

        # Execute
        result = await handle_trace_dependencies(
            mock_memory_db,
            {"memory_id": "solution-1"}
        )

        # Verify - should detect circular dependency
        assert result.isError is not True
        content_text = result.content[0].text
        assert "circular" in content_text.lower() or "cycle" in content_text.lower()

    async def test_trace_dependencies_missing_memory_id(self, mock_memory_db):
        """Test error when memory_id is missing."""
        from memorygraph.tools.chain_tools import handle_trace_dependencies

        # Execute without memory_id
        result = await handle_trace_dependencies(
            mock_memory_db,
            {}
        )

        # Verify error
        assert result.isError is True
        assert "required" in result.content[0].text.lower() or "missing" in result.content[0].text.lower()

    async def test_trace_dependencies_error_handling(self, mock_memory_db):
        """Test error handling when database query fails."""
        from memorygraph.tools.chain_tools import handle_trace_dependencies

        # Setup mock to raise exception
        mock_memory_db.get_related_memories.side_effect = Exception("Database error")

        # Execute
        result = await handle_trace_dependencies(
            mock_memory_db,
            {"memory_id": "solution-1"}
        )

        # Verify error is handled
        assert result.isError is True
        assert "Failed" in result.content[0].text or "Error" in result.content[0].text
