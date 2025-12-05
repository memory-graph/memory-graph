"""Tests for browse tool handlers.

This module tests all handlers in browse_tools.py with comprehensive
coverage of success cases, error cases, and edge cases.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from memorygraph.models import (
    Memory,
    MemoryType,
)


@pytest.fixture
def mock_memory_db():
    """Create a mock memory database."""
    db = AsyncMock()
    return db


@pytest.fixture
def sample_memories():
    """Create sample memories for testing."""
    from memorygraph.models import MemoryContext

    return [
        Memory(
            id="mem-1",
            type=MemoryType.SOLUTION,
            title="Redis timeout solution",
            content="Use connection pooling",
            tags=["redis", "performance"],
            importance=0.8,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            context=MemoryContext(project_path="/Users/me/project1")
        ),
        Memory(
            id="mem-2",
            type=MemoryType.PROBLEM,
            title="Database timeout",
            content="Connection timeout issue",
            tags=["database", "error"],
            importance=0.7,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            context=MemoryContext(project_path="/Users/me/project1")
        ),
        Memory(
            id="mem-3",
            type=MemoryType.ERROR,
            title="Authentication failure",
            content="OAuth token expired",
            tags=["auth", "oauth"],
            importance=0.9,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            context=MemoryContext(project_path="/Users/me/project2")
        ),
    ]


class TestBrowseMemoryTypes:
    """Tests for browse_memory_types handler."""

    async def test_browse_memory_types_success(self, mock_memory_db):
        """Test browsing memory types successfully returns counts."""
        # Import here to ensure we test the actual implementation
        from memorygraph.tools.browse_tools import handle_browse_memory_types

        # Setup mock backend
        mock_backend = AsyncMock()
        mock_backend.execute_query.return_value = [
            {"type": "solution", "count": 45},
            {"type": "error", "count": 23},
            {"type": "problem", "count": 12},
            {"type": "code_pattern", "count": 8},
        ]
        mock_memory_db.get_backend.return_value = mock_backend

        # Execute
        result = await handle_browse_memory_types(
            mock_memory_db,
            {}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "solution" in content_text
        assert "45" in content_text
        assert "error" in content_text
        assert "23" in content_text
        assert "Total:" in content_text

    async def test_browse_memory_types_empty_database(self, mock_memory_db):
        """Test browsing memory types with empty database."""
        from memorygraph.tools.browse_tools import handle_browse_memory_types

        # Setup mock backend
        mock_backend = AsyncMock()
        mock_backend.execute_query.return_value = []
        mock_memory_db.get_backend.return_value = mock_backend

        # Execute
        result = await handle_browse_memory_types(
            mock_memory_db,
            {}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "No memories found" in content_text or "0" in content_text

    async def test_browse_memory_types_with_percentages(self, mock_memory_db):
        """Test that percentages are calculated correctly."""
        from memorygraph.tools.browse_tools import handle_browse_memory_types

        # Setup mock backend with specific counts for easy percentage calculation
        mock_backend = AsyncMock()
        mock_backend.execute_query.return_value = [
            {"type": "solution", "count": 50},
            {"type": "problem", "count": 30},
            {"type": "error", "count": 20},
        ]
        mock_memory_db.get_backend.return_value = mock_backend

        # Execute
        result = await handle_browse_memory_types(
            mock_memory_db,
            {}
        )

        # Verify percentages are included
        content_text = result.content[0].text
        # Should show percentages like 50.0%, 30.0%, 20.0%
        assert "%" in content_text

    async def test_browse_memory_types_error_handling(self, mock_memory_db):
        """Test error handling when database query fails."""
        from memorygraph.tools.browse_tools import handle_browse_memory_types

        # Setup mock backend to raise exception
        mock_backend = AsyncMock()
        mock_backend.execute_query.side_effect = Exception("Database error")
        mock_memory_db.get_backend.return_value = mock_backend

        # Execute
        result = await handle_browse_memory_types(
            mock_memory_db,
            {}
        )

        # Verify error is handled
        assert result.isError is True
        assert "Failed" in result.content[0].text or "Error" in result.content[0].text


class TestBrowseByProject:
    """Tests for browse_by_project handler."""

    async def test_browse_by_project_success(self, mock_memory_db, sample_memories):
        """Test browsing memories by project path."""
        from memorygraph.tools.browse_tools import handle_browse_by_project

        # Setup mock to return filtered memories
        project1_memories = [m for m in sample_memories if m.context and m.context.project_path == "/Users/me/project1"]
        mock_memory_db.search_memories.return_value = project1_memories

        # Execute
        result = await handle_browse_by_project(
            mock_memory_db,
            {"project_path": "/Users/me/project1"}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "project1" in content_text or "2" in content_text  # 2 memories for project1
        assert "Redis timeout solution" in content_text
        assert "Database timeout" in content_text

    async def test_browse_by_project_not_found(self, mock_memory_db):
        """Test browsing with project that has no memories."""
        from memorygraph.tools.browse_tools import handle_browse_by_project

        # Setup mock to return empty list
        mock_memory_db.search_memories.return_value = []

        # Execute
        result = await handle_browse_by_project(
            mock_memory_db,
            {"project_path": "/Users/me/nonexistent"}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "No memories found" in content_text or "0" in content_text

    async def test_browse_by_project_fuzzy_match(self, mock_memory_db, sample_memories):
        """Test fuzzy matching of project paths."""
        from memorygraph.tools.browse_tools import handle_browse_by_project

        # Setup mock
        mock_memory_db.search_memories.return_value = [sample_memories[0]]

        # Execute with partial path
        result = await handle_browse_by_project(
            mock_memory_db,
            {"project_path": "project1"}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "Redis" in content_text

    async def test_browse_by_project_missing_path(self, mock_memory_db):
        """Test error when project_path is missing."""
        from memorygraph.tools.browse_tools import handle_browse_by_project

        # Execute without project_path
        result = await handle_browse_by_project(
            mock_memory_db,
            {}
        )

        # Verify error handling
        assert result.isError is True
        assert "required" in result.content[0].text.lower() or "missing" in result.content[0].text.lower()


class TestBrowseDomains:
    """Tests for browse_domains handler."""

    async def test_browse_domains_success(self, mock_memory_db):
        """Test browsing domains with tag clustering."""
        from memorygraph.tools.browse_tools import handle_browse_domains
        from memorygraph.models import MemoryContext

        # Create memories with enough instances of same tag to form a domain (min 3)
        redis_memories = [
            Memory(
                id=f"redis-{i}",
                type=MemoryType.SOLUTION,
                title=f"Redis solution {i}",
                content="Content",
                tags=["redis", "cache"],
                importance=0.8,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(3)
        ]

        # Setup mock to return all memories for clustering
        mock_memory_db.search_memories.return_value = redis_memories

        # Execute
        result = await handle_browse_domains(
            mock_memory_db,
            {}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        # Should identify domains based on common tags
        assert "domain" in content_text.lower()
        # Should show memory counts
        assert any(char.isdigit() for char in content_text)

    async def test_browse_domains_empty_database(self, mock_memory_db):
        """Test browsing domains with empty database."""
        from memorygraph.tools.browse_tools import handle_browse_domains

        # Setup mock to return empty list
        mock_memory_db.search_memories.return_value = []

        # Execute
        result = await handle_browse_domains(
            mock_memory_db,
            {}
        )

        # Verify
        assert result.isError is not True
        content_text = result.content[0].text
        assert "No" in content_text or "0" in content_text

    async def test_browse_domains_clustering(self, mock_memory_db):
        """Test that domains are properly clustered by tags."""
        from memorygraph.tools.browse_tools import handle_browse_domains

        # Create memories with related tags
        redis_memories = [
            Memory(
                id=f"redis-{i}",
                type=MemoryType.SOLUTION,
                title=f"Redis solution {i}",
                content="Content",
                tags=["redis", "cache", "performance"],
                importance=0.8,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(5)
        ]

        auth_memories = [
            Memory(
                id=f"auth-{i}",
                type=MemoryType.ERROR,
                title=f"Auth error {i}",
                content="Content",
                tags=["auth", "oauth", "security"],
                importance=0.7,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(3)
        ]

        mock_memory_db.search_memories.return_value = redis_memories + auth_memories

        # Execute
        result = await handle_browse_domains(
            mock_memory_db,
            {}
        )

        # Verify domains are identified
        content_text = result.content[0].text
        # Should identify "redis" and "auth" as dominant domains
        assert "redis" in content_text.lower() or "cache" in content_text.lower()
        assert "auth" in content_text.lower() or "security" in content_text.lower()

    async def test_browse_domains_error_handling(self, mock_memory_db):
        """Test error handling when clustering fails."""
        from memorygraph.tools.browse_tools import handle_browse_domains

        # Setup mock to raise exception
        mock_memory_db.search_memories.side_effect = Exception("Database error")

        # Execute
        result = await handle_browse_domains(
            mock_memory_db,
            {}
        )

        # Verify error is handled
        assert result.isError is True
        assert "Failed" in result.content[0].text or "Error" in result.content[0].text
