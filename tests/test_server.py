"""
Comprehensive tests for MCP server handlers.

Tests cover:
- MCP tool registration
- Handler validation
- Success and failure cases
- Error handling
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from claude_memory.server import ClaudeMemoryServer
from claude_memory.database import MemoryDatabase, Neo4jConnection
from claude_memory.models import (
    Memory, MemoryType, MemoryContext, Relationship,
    RelationshipType, RelationshipProperties, SearchQuery,
    MemoryNotFoundError, ValidationError
)


@pytest.fixture
async def mock_database():
    """Create a mock MemoryDatabase."""
    db = AsyncMock(spec=MemoryDatabase)
    db.initialize_schema = AsyncMock()
    db.store_memory = AsyncMock()
    db.get_memory = AsyncMock()
    db.search_memories = AsyncMock()
    db.update_memory = AsyncMock()
    db.delete_memory = AsyncMock()
    db.create_relationship = AsyncMock()
    db.get_related_memories = AsyncMock()
    db.get_memory_statistics = AsyncMock()
    return db


@pytest.fixture
async def mcp_server(mock_database):
    """Create MCP server with mocked database."""
    server = ClaudeMemoryServer()
    server.db = mock_database
    return server


@pytest.fixture
def sample_memory_args():
    """Sample arguments for storing a memory."""
    return {
        "memory_type": "solution",
        "title": "Test Solution",
        "content": "This is a test solution",
        "tags": ["python", "testing"],
        "importance": 0.8,
        "confidence": 0.9,
        "context": {
            "project_path": "/test/project",
            "files_involved": ["test.py"],
            "languages": ["python"]
        }
    }


class TestStoreMemory:
    """Test store_memory handler."""

    @pytest.mark.asyncio
    async def test_store_memory_success(self, mcp_server, mock_database, sample_memory_args):
        """Test successful memory storage."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        result = await mcp_server._handle_store_memory(sample_memory_args)

        assert result.isError is False
        assert memory_id in str(result.content)
        mock_database.store_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_memory_missing_required_fields(self, mcp_server):
        """Test store_memory with missing required fields."""
        args = {"title": "Test"}  # Missing type and content

        result = await mcp_server._handle_store_memory(args)

        assert result.isError is True
        assert "required" in str(result.content).lower() or "missing" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_store_memory_invalid_type(self, mcp_server):
        """Test store_memory with invalid memory type."""
        args = {
            "memory_type": "invalid_type",
            "title": "Test",
            "content": "Test content"
        }

        result = await mcp_server._handle_store_memory(args)

        assert result.isError is True


class TestGetMemory:
    """Test get_memory handler."""

    @pytest.mark.asyncio
    async def test_get_memory_success(self, mcp_server, mock_database):
        """Test successful memory retrieval."""
        memory_id = str(uuid.uuid4())
        mock_memory = Memory(
            id=memory_id,
            type=MemoryType.SOLUTION,
            title="Test Solution",
            content="Test content"
        )
        mock_database.get_memory.return_value = mock_memory

        result = await mcp_server._handle_get_memory({"memory_id": memory_id})

        assert result.isError is False
        assert memory_id in str(result.content)
        mock_database.get_memory.assert_called_once_with(memory_id, True)

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, mcp_server, mock_database):
        """Test get_memory when memory doesn't exist."""
        memory_id = str(uuid.uuid4())
        mock_database.get_memory.return_value = None

        result = await mcp_server._handle_get_memory({"memory_id": memory_id})

        assert result.isError is True
        assert "not found" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_memory_missing_id(self, mcp_server):
        """Test get_memory without providing ID."""
        result = await mcp_server._handle_get_memory({})

        assert result.isError is True


class TestSearchMemories:
    """Test search_memories handler."""

    @pytest.mark.asyncio
    async def test_search_memories_success(self, mcp_server, mock_database):
        """Test successful memory search."""
        mock_memories = [
            Memory(
                id=str(uuid.uuid4()),
                type=MemoryType.SOLUTION,
                title="Test 1",
                content="Content 1"
            ),
            Memory(
                id=str(uuid.uuid4()),
                type=MemoryType.PROBLEM,
                title="Test 2",
                content="Content 2"
            )
        ]
        mock_database.search_memories.return_value = mock_memories

        args = {
            "query": "test",
            "memory_types": ["solution", "problem"],
            "limit": 10
        }
        result = await mcp_server._handle_search_memories(args)

        assert result.isError is False
        assert "Test 1" in str(result.content) or "found" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_search_memories_no_results(self, mcp_server, mock_database):
        """Test search with no results."""
        mock_database.search_memories.return_value = []

        result = await mcp_server._handle_search_memories({"query": "nonexistent"})

        assert result.isError is False
        assert "0" in str(result.content) or "no" in str(result.content).lower()


class TestUpdateMemory:
    """Test update_memory handler."""

    @pytest.mark.asyncio
    async def test_update_memory_success(self, mcp_server, mock_database):
        """Test successful memory update."""
        memory_id = str(uuid.uuid4())
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": memory_id,
            "title": "Updated Title",
            "content": "Updated content"
        }
        result = await mcp_server._handle_update_memory(args)

        assert result.isError is False
        assert "updated" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_update_memory_not_found(self, mcp_server, mock_database):
        """Test update when memory doesn't exist."""
        memory_id = str(uuid.uuid4())
        mock_database.update_memory.return_value = False

        args = {
            "memory_id": memory_id,
            "title": "Updated Title"
        }
        result = await mcp_server._handle_update_memory(args)

        assert result.isError is True


class TestDeleteMemory:
    """Test delete_memory handler."""

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, mcp_server, mock_database):
        """Test successful memory deletion."""
        memory_id = str(uuid.uuid4())
        mock_database.delete_memory.return_value = True

        result = await mcp_server._handle_delete_memory({"memory_id": memory_id})

        assert result.isError is False
        assert "deleted" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, mcp_server, mock_database):
        """Test delete when memory doesn't exist."""
        memory_id = str(uuid.uuid4())
        mock_database.delete_memory.return_value = False

        result = await mcp_server._handle_delete_memory({"memory_id": memory_id})

        assert result.isError is True


class TestCreateRelationship:
    """Test create_relationship handler."""

    @pytest.mark.asyncio
    async def test_create_relationship_success(self, mcp_server, mock_database):
        """Test successful relationship creation."""
        from_id = str(uuid.uuid4())
        to_id = str(uuid.uuid4())

        mock_relationship = Relationship(
            from_memory_id=from_id,
            to_memory_id=to_id,
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties()
        )
        mock_database.create_relationship.return_value = mock_relationship

        args = {
            "from_memory_id": from_id,
            "to_memory_id": to_id,
            "relationship_type": "SOLVES",
            "strength": 0.9
        }
        result = await mcp_server._handle_create_relationship(args)

        assert result.isError is False
        assert "relationship" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_create_relationship_missing_ids(self, mcp_server):
        """Test create_relationship with missing IDs."""
        args = {"relationship_type": "SOLVES"}

        result = await mcp_server._handle_create_relationship(args)

        assert result.isError is True


class TestGetRelatedMemories:
    """Test get_related_memories handler."""

    @pytest.mark.asyncio
    async def test_get_related_memories_success(self, mcp_server, mock_database):
        """Test successful retrieval of related memories."""
        memory_id = str(uuid.uuid4())
        mock_related = [
            Memory(
                id=str(uuid.uuid4()),
                type=MemoryType.PROBLEM,
                title="Related Problem",
                content="Problem content"
            )
        ]
        mock_database.get_related_memories.return_value = mock_related

        args = {
            "memory_id": memory_id,
            "relationship_types": ["SOLVES"],
            "max_depth": 2
        }
        result = await mcp_server._handle_get_related_memories(args)

        assert result.isError is False

    @pytest.mark.asyncio
    async def test_get_related_memories_no_relations(self, mcp_server, mock_database):
        """Test get_related_memories with no relations found."""
        memory_id = str(uuid.uuid4())
        mock_database.get_related_memories.return_value = []

        result = await mcp_server._handle_get_related_memories({"memory_id": memory_id})

        assert result.isError is False


class TestGetMemoryStatistics:
    """Test get_memory_statistics handler."""

    @pytest.mark.asyncio
    async def test_get_memory_statistics_success(self, mcp_server, mock_database):
        """Test successful statistics retrieval."""
        mock_stats = {
            "total_memories": 100,
            "total_relationships": 250,
            "memory_types": {"solution": 50, "problem": 30},
            "relationship_types": {"SOLVES": 100}
        }
        mock_database.get_memory_statistics.return_value = mock_stats

        result = await mcp_server._handle_get_memory_statistics({})

        assert result.isError is False
        assert "100" in str(result.content) or "total" in str(result.content).lower()


class TestErrorHandling:
    """Test error handling across handlers."""

    @pytest.mark.asyncio
    async def test_database_error_handling(self, mcp_server, mock_database):
        """Test handling of database errors."""
        from claude_memory.models import DatabaseConnectionError

        mock_database.store_memory.side_effect = DatabaseConnectionError("DB connection failed")

        args = {
            "memory_type": "solution",
            "title": "Test",
            "content": "Test content"
        }
        result = await mcp_server._handle_store_memory(args)

        assert result.isError is True
        assert "error" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, mcp_server, mock_database):
        """Test handling of validation errors."""
        mock_database.store_memory.side_effect = ValidationError("Invalid data")

        args = {
            "memory_type": "solution",
            "title": "Test",
            "content": "Test content"
        }
        result = await mcp_server._handle_store_memory(args)

        assert result.isError is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
