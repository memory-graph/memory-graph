"""Tests for contextual search handler.

This module tests the contextual_search handler with comprehensive
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
    """Create sample memories for contextual search testing."""
    return {
        "root": Memory(
            id="root-1",
            type=MemoryType.PROBLEM,
            title="Redis timeout issue",
            content="Redis connections timing out in production",
            tags=["redis", "timeout", "production"],
            importance=0.9,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        "solution": Memory(
            id="solution-1",
            type=MemoryType.SOLUTION,
            title="Use connection pooling",
            content="Implement Redis connection pooling with timeout configuration",
            tags=["redis", "solution", "pooling"],
            importance=0.8,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        "config": Memory(
            id="config-1",
            type=MemoryType.CODE_PATTERN,
            title="Redis pool config",
            content="Configuration pattern for Redis connection pool with timeout settings",
            tags=["redis", "config", "pattern"],
            importance=0.7,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        "unrelated": Memory(
            id="unrelated-1",
            type=MemoryType.SOLUTION,
            title="Database optimization",
            content="PostgreSQL query optimization techniques",
            tags=["postgres", "optimization"],
            importance=0.6,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    }


@pytest.fixture
def sample_relationships():
    """Create sample relationships."""
    return {
        "solves": Relationship(
            from_memory_id="solution-1",
            to_memory_id="root-1",
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(strength=0.9, confidence=0.8),
        ),
        "uses": Relationship(
            from_memory_id="solution-1",
            to_memory_id="config-1",
            type=RelationshipType.USED_IN,
            properties=RelationshipProperties(strength=0.8, confidence=0.9),
        ),
    }


class TestContextualSearch:
    """Tests for contextual_search handler."""

    async def test_contextual_search_finds_related(
        self, mock_memory_db, sample_memories, sample_relationships
    ):
        """Test that contextual search finds memories in the context."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock to return related memories
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["solution"], sample_relationships["solves"]),
            (sample_memories["config"], sample_relationships["uses"]),
        ]

        # Mock search to return matches from related memories
        mock_memory_db.search_memories.return_value = [
            sample_memories["config"]  # Matches "config" query
        ]

        # Execute
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "config",
                "max_depth": 2,
            }
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "config-1" in content_text or "Redis pool config" in content_text
        assert "context" in content_text.lower()

    async def test_contextual_search_excludes_unrelated(
        self, mock_memory_db, sample_memories, sample_relationships
    ):
        """Test that contextual search only returns related memories."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock to return only related memories (not unrelated)
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["solution"], sample_relationships["solves"]),
        ]

        # Mock search to filter by related IDs only
        mock_memory_db.search_memories.return_value = [
            sample_memories["solution"]
        ]

        # Execute
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "solution",
                "max_depth": 1,
            }
        )

        # Verify solution is included but unrelated is not
        content_text = result.content[0].text
        assert "solution-1" in content_text or "connection pooling" in content_text
        assert "unrelated-1" not in content_text
        assert "Database optimization" not in content_text

    async def test_contextual_search_empty_context(self, mock_memory_db):
        """Test contextual search when no related memories exist."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock to return empty related memories
        mock_memory_db.get_related_memories.return_value = []
        mock_memory_db.search_memories.return_value = []

        # Execute
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "test",
            }
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "No" in content_text or "not found" in content_text.lower() or "0" in content_text

    async def test_contextual_search_no_matches(
        self, mock_memory_db, sample_memories, sample_relationships
    ):
        """Test contextual search when query matches nothing in context."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock to return related memories but no search matches
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["solution"], sample_relationships["solves"]),
        ]
        mock_memory_db.search_memories.return_value = []

        # Execute
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "nonexistent",
            }
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "No" in content_text or "not found" in content_text.lower() or "0" in content_text

    async def test_contextual_search_depth_limit(
        self, mock_memory_db, sample_memories, sample_relationships
    ):
        """Test that max_depth is respected."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["solution"], sample_relationships["solves"]),
        ]
        mock_memory_db.search_memories.return_value = [
            sample_memories["solution"]
        ]

        # Execute with depth 1
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "test",
                "max_depth": 1,
            }
        )

        # Verify get_related_memories was called with correct depth
        assert mock_memory_db.get_related_memories.called
        call_args = mock_memory_db.get_related_memories.call_args
        assert call_args[1]["max_depth"] == 1

    async def test_contextual_search_default_depth(
        self, mock_memory_db, sample_memories, sample_relationships
    ):
        """Test that default max_depth is 2."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["solution"], sample_relationships["solves"]),
        ]
        mock_memory_db.search_memories.return_value = []

        # Execute without specifying depth
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "test",
            }
        )

        # Verify default depth was used
        call_args = mock_memory_db.get_related_memories.call_args
        assert call_args[1]["max_depth"] == 2

    async def test_contextual_search_missing_memory_id(self, mock_memory_db):
        """Test error when memory_id is missing."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Execute without memory_id
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "query": "test",
            }
        )

        # Verify error
        assert result.isError is True
        assert "required" in result.content[0].text.lower() or "missing" in result.content[0].text.lower()

    async def test_contextual_search_missing_query(self, mock_memory_db):
        """Test error when query is missing."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Execute without query
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
            }
        )

        # Verify error
        assert result.isError is True
        assert "required" in result.content[0].text.lower() or "missing" in result.content[0].text.lower()

    async def test_contextual_search_error_handling(self, mock_memory_db):
        """Test error handling when database query fails."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock to raise exception
        mock_memory_db.get_related_memories.side_effect = Exception("Database error")

        # Execute
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "test",
            }
        )

        # Verify error is handled
        assert result.isError is True
        assert "Failed" in result.content[0].text or "Error" in result.content[0].text

    async def test_contextual_search_shows_context(
        self, mock_memory_db, sample_memories, sample_relationships
    ):
        """Test that results show they are within a context."""
        from memorygraph.tools.search_tools import handle_contextual_search

        # Setup mock
        mock_memory_db.get_related_memories.return_value = [
            (sample_memories["solution"], sample_relationships["solves"]),
        ]
        mock_memory_db.search_memories.return_value = [
            sample_memories["solution"]
        ]

        # Execute
        result = await handle_contextual_search(
            mock_memory_db,
            {
                "memory_id": "root-1",
                "query": "pool",
            }
        )

        # Verify context is mentioned
        content_text = result.content[0].text
        assert "context" in content_text.lower() or "related to" in content_text.lower()
        assert "root-1" in content_text  # Shows the root memory ID
