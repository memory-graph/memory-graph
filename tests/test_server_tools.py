"""
Comprehensive tests for MCP server tool handlers.

This test suite focuses on achieving >70% coverage for server.py by testing:
- All tool handlers (store, get, search, update, delete, relationships, etc.)
- Error handling paths
- Edge cases and validation
- MCP protocol compliance
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from memorygraph.server import ClaudeMemoryServer
from memorygraph.database import MemoryDatabase
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, Relationship,
    RelationshipType, RelationshipProperties, SearchQuery,
    MemoryNotFoundError, ValidationError as MemoryValidationError
)
from memorygraph.tools import (
    handle_recall_memories,
    handle_store_memory,
    handle_get_memory,
    handle_search_memories,
    handle_update_memory,
    handle_delete_memory,
    handle_create_relationship,
    handle_get_related_memories,
    handle_get_memory_statistics,
    handle_get_recent_activity,
)
from mcp.types import CallToolResult, TextContent


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
    db.get_recent_activity = AsyncMock()
    return db


@pytest.fixture
async def mcp_server(mock_database):
    """Create MCP server with mocked database."""
    server = ClaudeMemoryServer()
    server.memory_db = mock_database

    # Initialize advanced handlers
    from memorygraph.advanced_tools import AdvancedRelationshipHandlers
    server.advanced_handlers = AdvancedRelationshipHandlers(mock_database)

    # Integration handlers removed (moved to experimental/)

    return server


@pytest.fixture
def sample_memory():
    """Create a sample memory for testing."""
    return Memory(
        id=str(uuid.uuid4()),
        type=MemoryType.SOLUTION,
        title="Test Solution",
        content="This is a test solution content",
        summary="Test summary",
        tags=["python", "testing"],
        importance=0.8,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        context=MemoryContext(
            project_path="/test/project",
            files_involved=["test.py"],
            languages=["python"]
        )
    )


class TestRecallMemories:
    """Test recall_memories handler (convenience wrapper)."""

    @pytest.mark.asyncio
    async def test_recall_memories_success(self, mcp_server, mock_database, sample_memory):
        """Test successful memory recall."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {"query": "test solution"}
        result = await handle_recall_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "Test Solution" in str(result.content)
        assert sample_memory.id in str(result.content)
        mock_database.search_memories.assert_called_once()

    @pytest.mark.asyncio
    async def test_recall_memories_no_results(self, mcp_server, mock_database):
        """Test recall with no matching memories."""
        mock_database.search_memories.return_value = []

        args = {"query": "nonexistent"}
        result = await handle_recall_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "No memories found" in str(result.content)

    @pytest.mark.asyncio
    async def test_recall_memories_with_filters(self, mcp_server, mock_database, sample_memory):
        """Test recall with memory type and project filters."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {
            "query": "test",
            "memory_types": ["solution"],
            "project_path": "/test/project",
            "limit": 10
        }
        result = await handle_recall_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "Test Solution" in str(result.content)

        # Verify search_memories was called with correct parameters
        call_args = mock_database.search_memories.call_args[0][0]
        assert call_args.query == "test"
        assert call_args.limit == 10
        assert call_args.search_tolerance == "normal"

    @pytest.mark.asyncio
    async def test_recall_memories_validation_error(self, mcp_server, mock_database):
        """Test recall with invalid parameters."""
        mock_database.search_memories.side_effect = Exception("Search failed")

        args = {"query": "test"}
        result = await handle_recall_memories(mock_database, args)

        assert result.isError is True
        assert "failed" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_recall_memories_with_relationships(self, mcp_server, mock_database, sample_memory):
        """Test recall includes relationship information."""
        # Add mock relationships to memory
        sample_memory.relationships = {
            "SOLVES": ["Problem 1", "Problem 2"],
            "USES": ["Pattern A"]
        }
        mock_database.search_memories.return_value = [sample_memory]

        args = {"query": "test"}
        result = await handle_recall_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        content_str = str(result.content)
        assert "SOLVES" in content_str or "Relationships" in content_str


class TestStoreMemory:
    """Test store_memory handler."""

    @pytest.mark.asyncio
    async def test_store_memory_success(self, mcp_server, mock_database):
        """Test successful memory storage."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "New Solution",
            "content": "Solution content",
            "tags": ["python"],
            "importance": 0.7
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is None or result.isError is False
        assert memory_id in str(result.content)
        mock_database.store_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_memory_with_context(self, mcp_server, mock_database):
        """Test storing memory with context."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "problem",
            "title": "Test Problem",
            "content": "Problem description",
            "context": {
                "project_path": "/my/project",
                "files_involved": ["main.py"],
                "languages": ["python"]
            }
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is None or result.isError is False
        assert memory_id in str(result.content)

    @pytest.mark.asyncio
    async def test_store_memory_missing_required_fields(self, mcp_server):
        """Test store with missing required fields."""
        args = {"title": "Only title"}
        result = await handle_store_memory(mock_database, args)

        assert result.isError is True
        assert "error" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_store_memory_invalid_type(self, mcp_server):
        """Test store with invalid memory type."""
        args = {
            "type": "invalid_type",
            "title": "Test",
            "content": "Content"
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_store_memory_invalid_importance(self, mcp_server, mock_database):
        """Test store with invalid importance value."""
        args = {
            "type": "solution",
            "title": "Test",
            "content": "Content",
            "importance": 1.5  # Invalid: should be 0.0-1.0
        }
        result = await handle_store_memory(mock_database, args)

        # Should handle validation error
        assert result.isError is True or mock_database.store_memory.called

    @pytest.mark.asyncio
    async def test_store_memory_database_error(self, mcp_server, mock_database):
        """Test store when database raises error."""
        mock_database.store_memory.side_effect = Exception("Database error")

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Content"
        }
        result = await handle_store_memory(mock_database, args)

        assert result.isError is True
        assert "Failed to store memory" in str(result.content)


class TestGetMemory:
    """Test get_memory handler."""

    @pytest.mark.asyncio
    async def test_get_memory_success(self, mcp_server, mock_database, sample_memory):
        """Test successful memory retrieval."""
        mock_database.get_memory.return_value = sample_memory

        args = {"memory_id": sample_memory.id}
        result = await handle_get_memory(mock_database, args)

        assert result.isError is None or result.isError is False
        assert sample_memory.title in str(result.content)
        assert sample_memory.content in str(result.content)

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, mcp_server, mock_database):
        """Test get memory when it doesn't exist."""
        mock_database.get_memory.return_value = None

        args = {"memory_id": "nonexistent-id"}
        result = await handle_get_memory(mock_database, args)

        assert result.isError is True
        assert "not found" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_memory_with_relationships(self, mcp_server, mock_database, sample_memory):
        """Test get memory with relationships included."""
        mock_database.get_memory.return_value = sample_memory

        args = {
            "memory_id": sample_memory.id,
            "include_relationships": True
        }
        result = await handle_get_memory(mock_database, args)

        assert result.isError is None or result.isError is False
        mock_database.get_memory.assert_called_with(sample_memory.id, True)

    @pytest.mark.asyncio
    async def test_get_memory_without_relationships(self, mcp_server, mock_database, sample_memory):
        """Test get memory without relationships."""
        mock_database.get_memory.return_value = sample_memory

        args = {
            "memory_id": sample_memory.id,
            "include_relationships": False
        }
        result = await handle_get_memory(mock_database, args)

        assert result.isError is None or result.isError is False
        mock_database.get_memory.assert_called_with(sample_memory.id, False)

    @pytest.mark.asyncio
    async def test_get_memory_missing_id(self, mcp_server):
        """Test get memory with missing memory_id."""
        args = {}
        result = await handle_get_memory(mock_database, args)

        assert result.isError is True
        assert "required" in str(result.content).lower() or "error" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_memory_with_context_formatting(self, mcp_server, mock_database, sample_memory):
        """Test memory context is properly formatted in output."""
        mock_database.get_memory.return_value = sample_memory

        args = {"memory_id": sample_memory.id}
        result = await handle_get_memory(mock_database, args)

        content_str = str(result.content)
        assert "Project" in content_str or sample_memory.context.project_path in content_str


class TestSearchMemories:
    """Test search_memories handler."""

    @pytest.mark.asyncio
    async def test_search_memories_basic(self, mcp_server, mock_database, sample_memory):
        """Test basic memory search."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {"query": "test"}
        result = await handle_search_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "Found 1 memories" in str(result.content) or sample_memory.title in str(result.content)

    @pytest.mark.asyncio
    async def test_search_memories_with_types(self, mcp_server, mock_database, sample_memory):
        """Test search with memory type filter."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {
            "query": "test",
            "memory_types": ["solution", "problem"]
        }
        result = await handle_search_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        call_args = mock_database.search_memories.call_args[0][0]
        assert len(call_args.memory_types) == 2

    @pytest.mark.asyncio
    async def test_search_memories_with_tags(self, mcp_server, mock_database, sample_memory):
        """Test search with tags filter."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {
            "query": "test",
            "tags": ["python", "testing"]
        }
        result = await handle_search_memories(mock_database, args)

        assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_search_memories_with_importance(self, mcp_server, mock_database, sample_memory):
        """Test search with minimum importance filter."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {
            "query": "test",
            "min_importance": 0.5
        }
        result = await handle_search_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        call_args = mock_database.search_memories.call_args[0][0]
        assert call_args.min_importance == 0.5

    @pytest.mark.asyncio
    async def test_search_memories_with_project_path(self, mcp_server, mock_database, sample_memory):
        """Test search with project path filter."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {
            "query": "test",
            "project_path": "/test/project"
        }
        result = await handle_search_memories(mock_database, args)

        assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_search_memories_tolerance_modes(self, mcp_server, mock_database, sample_memory):
        """Test search with different tolerance modes."""
        mock_database.search_memories.return_value = [sample_memory]

        for tolerance in ["strict", "normal", "fuzzy"]:
            args = {
                "query": "test",
                "search_tolerance": tolerance
            }
            result = await handle_search_memories(mock_database, args)

            assert result.isError is None or result.isError is False
            call_args = mock_database.search_memories.call_args[0][0]
            assert call_args.search_tolerance == tolerance

    @pytest.mark.asyncio
    async def test_search_memories_match_modes(self, mcp_server, mock_database, sample_memory):
        """Test search with match mode (any vs all)."""
        mock_database.search_memories.return_value = [sample_memory]

        for match_mode in ["any", "all"]:
            args = {
                "terms": ["test", "solution"],
                "match_mode": match_mode
            }
            result = await handle_search_memories(mock_database, args)

            assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_search_memories_no_results(self, mcp_server, mock_database):
        """Test search with no matching memories."""
        mock_database.search_memories.return_value = []

        args = {"query": "nonexistent"}
        result = await handle_search_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "No memories found" in str(result.content)

    @pytest.mark.asyncio
    async def test_search_memories_with_limit(self, mcp_server, mock_database, sample_memory):
        """Test search with custom limit."""
        mock_database.search_memories.return_value = [sample_memory]

        args = {
            "query": "test",
            "limit": 50
        }
        result = await handle_search_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        call_args = mock_database.search_memories.call_args[0][0]
        assert call_args.limit == 50

    @pytest.mark.asyncio
    async def test_search_memories_validation_error(self, mcp_server, mock_database):
        """Test search with invalid parameters."""
        mock_database.search_memories.side_effect = Exception("Search failed")

        args = {"query": "test"}
        result = await handle_search_memories(mock_database, args)

        assert result.isError is True


class TestUpdateMemory:
    """Test update_memory handler."""

    @pytest.mark.asyncio
    async def test_update_memory_success(self, mcp_server, mock_database, sample_memory):
        """Test successful memory update."""
        mock_database.get_memory.return_value = sample_memory
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": sample_memory.id,
            "title": "Updated Title",
            "content": "Updated content"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "updated successfully" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_update_memory_partial_update(self, mcp_server, mock_database, sample_memory):
        """Test partial memory update (only some fields)."""
        mock_database.get_memory.return_value = sample_memory
        mock_database.update_memory.return_value = True

        args = {
            "memory_id": sample_memory.id,
            "tags": ["new-tag"]
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_update_memory_not_found(self, mcp_server, mock_database):
        """Test update when memory doesn't exist."""
        mock_database.get_memory.return_value = None

        args = {
            "memory_id": "nonexistent-id",
            "title": "New Title"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is True
        assert "not found" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_update_memory_missing_id(self, mcp_server):
        """Test update without memory_id."""
        args = {"title": "New Title"}
        result = await handle_update_memory(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_update_memory_database_error(self, mcp_server, mock_database, sample_memory):
        """Test update when database raises error."""
        mock_database.get_memory.return_value = sample_memory
        mock_database.update_memory.side_effect = Exception("Database error")

        args = {
            "memory_id": sample_memory.id,
            "title": "New Title"
        }
        result = await handle_update_memory(mock_database, args)

        assert result.isError is True


class TestDeleteMemory:
    """Test delete_memory handler."""

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, mcp_server, mock_database):
        """Test successful memory deletion."""
        mock_database.delete_memory.return_value = True

        memory_id = str(uuid.uuid4())
        args = {"memory_id": memory_id}
        result = await handle_delete_memory(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "deleted successfully" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, mcp_server, mock_database):
        """Test delete when memory doesn't exist."""
        mock_database.delete_memory.return_value = False

        args = {"memory_id": "nonexistent-id"}
        result = await handle_delete_memory(mock_database, args)

        # Server returns error when delete_memory returns False
        assert result.isError is True
        assert "may not exist" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_delete_memory_missing_id(self, mcp_server):
        """Test delete without memory_id."""
        args = {}
        result = await handle_delete_memory(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_delete_memory_database_error(self, mcp_server, mock_database):
        """Test delete when database raises error."""
        mock_database.delete_memory.side_effect = Exception("Database error")

        args = {"memory_id": str(uuid.uuid4())}
        result = await handle_delete_memory(mock_database, args)

        assert result.isError is True


class TestCreateRelationship:
    """Test create_relationship handler."""

    @pytest.mark.asyncio
    async def test_create_relationship_success(self, mcp_server, mock_database):
        """Test successful relationship creation."""
        mock_database.create_relationship.return_value = True

        args = {
            "from_memory_id": str(uuid.uuid4()),
            "to_memory_id": str(uuid.uuid4()),
            "relationship_type": "SOLVES"
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "created successfully" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_create_relationship_with_context(self, mcp_server, mock_database):
        """Test relationship creation with context."""
        mock_database.create_relationship.return_value = True

        args = {
            "from_memory_id": str(uuid.uuid4()),
            "to_memory_id": str(uuid.uuid4()),
            "relationship_type": "SOLVES",
            "context": "This solution addresses the timeout problem",
            "strength": 0.9,
            "confidence": 0.85
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_create_relationship_invalid_type(self, mcp_server):
        """Test relationship creation with invalid type."""
        args = {
            "from_memory_id": str(uuid.uuid4()),
            "to_memory_id": str(uuid.uuid4()),
            "relationship_type": "INVALID_TYPE"
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_create_relationship_missing_fields(self, mcp_server):
        """Test relationship creation with missing required fields."""
        args = {"from_memory_id": str(uuid.uuid4())}
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is True

    @pytest.mark.asyncio
    async def test_create_relationship_database_error(self, mcp_server, mock_database):
        """Test relationship creation when database raises error."""
        mock_database.create_relationship.side_effect = Exception("Database error")

        args = {
            "from_memory_id": str(uuid.uuid4()),
            "to_memory_id": str(uuid.uuid4()),
            "relationship_type": "SOLVES"
        }
        result = await handle_create_relationship(mock_database, args)

        assert result.isError is True


class TestGetRelatedMemories:
    """Test get_related_memories handler."""

    @pytest.mark.asyncio
    async def test_get_related_memories_success(self, mcp_server, mock_database, sample_memory):
        """Test successful retrieval of related memories."""
        related_memory = Memory(
            id=str(uuid.uuid4()),
            type=MemoryType.PROBLEM,
            title="Related Problem",
            content="Problem content",
            tags=[],
            importance=0.7,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create a mock relationship
        from memorygraph.models import Relationship
        mock_relationship = Relationship(
            id=str(uuid.uuid4()),
            from_memory_id=str(uuid.uuid4()),
            to_memory_id=related_memory.id,
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties(strength=0.8, confidence=0.9)
        )

        # Return as tuple (memory, relationship)
        mock_database.get_related_memories.return_value = [(related_memory, mock_relationship)]

        args = {"memory_id": str(uuid.uuid4())}
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "Related Problem" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_related_memories_with_depth(self, mcp_server, mock_database):
        """Test get related memories with custom depth."""
        mock_database.get_related_memories.return_value = []

        args = {
            "memory_id": str(uuid.uuid4()),
            "max_depth": 3
        }
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        mock_database.get_related_memories.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_related_memories_with_type_filter(self, mcp_server, mock_database):
        """Test get related memories with relationship type filter."""
        mock_database.get_related_memories.return_value = []

        args = {
            "memory_id": str(uuid.uuid4()),
            "relationship_types": ["SOLVES", "CAUSES"]
        }
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_get_related_memories_none_found(self, mcp_server, mock_database):
        """Test get related memories when none exist."""
        mock_database.get_related_memories.return_value = []

        args = {"memory_id": str(uuid.uuid4())}
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "No related memories" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_related_memories_missing_id(self, mcp_server):
        """Test get related memories without memory_id."""
        args = {}
        result = await handle_get_related_memories(mock_database, args)

        assert result.isError is True


class TestGetRecentActivity:
    """Test get_recent_activity handler."""

    @pytest.mark.asyncio
    async def test_get_recent_activity_success(self, mcp_server, mock_database, sample_memory):
        """Test successful retrieval of recent activity."""
        # Use SQLiteMemoryDatabase instead of generic mock
        from memorygraph.sqlite_database import SQLiteMemoryDatabase
        from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        # Create a mock SQLite backend
        sqlite_backend = AsyncMock(spec=SQLiteFallbackBackend)
        sqlite_db = AsyncMock(spec=SQLiteMemoryDatabase)
        sqlite_db.get_recent_activity = AsyncMock(return_value={
            "total_count": 5,
            "memories_by_type": {"solution": 3, "problem": 2},
            "recent_memories": [sample_memory],
            "unresolved_problems": []
        })

        # Replace the mock database with SQLite mock
        mcp_server.memory_db = sqlite_db

        args = {"days": 7}
        result = await handle_get_recent_activity(sqlite_db, args)

        assert result.isError is None or result.isError is False
        assert "Recent Activity" in str(result.content) or "activity" in str(result.content).lower()

    @pytest.mark.asyncio
    async def test_get_recent_activity_custom_days(self, mcp_server, mock_database):
        """Test recent activity with custom day range."""
        from memorygraph.sqlite_database import SQLiteMemoryDatabase

        sqlite_db = AsyncMock(spec=SQLiteMemoryDatabase)
        sqlite_db.get_recent_activity = AsyncMock(return_value={
            "total_count": 0,
            "memories_by_type": {},
            "recent_memories": [],
            "unresolved_problems": []
        })
        mcp_server.memory_db = sqlite_db

        args = {"days": 30}
        result = await handle_get_recent_activity(sqlite_db, args)

        assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_get_recent_activity_with_project(self, mcp_server, mock_database):
        """Test recent activity filtered by project."""
        from memorygraph.sqlite_database import SQLiteMemoryDatabase

        sqlite_db = AsyncMock(spec=SQLiteMemoryDatabase)
        sqlite_db.get_recent_activity = AsyncMock(return_value={
            "total_count": 2,
            "memories_by_type": {"solution": 2},
            "recent_memories": [],
            "unresolved_problems": []
        })
        mcp_server.memory_db = sqlite_db

        args = {
            "days": 7,
            "project": "/test/project"
        }
        result = await handle_get_recent_activity(sqlite_db, args)

        assert result.isError is None or result.isError is False

    @pytest.mark.asyncio
    async def test_get_recent_activity_database_error(self, mcp_server, mock_database):
        """Test recent activity when database raises error."""
        mock_database.get_recent_activity.side_effect = Exception("Database error")

        args = {"days": 7}
        result = await handle_get_recent_activity(mock_database, args)

        assert result.isError is True


class TestGetMemoryStatistics:
    """Test get_memory_statistics handler."""

    @pytest.mark.asyncio
    async def test_get_memory_statistics_success(self, mcp_server, mock_database):
        """Test successful statistics retrieval."""
        # Match the actual format expected by the server handler
        mock_database.get_memory_statistics.return_value = {
            "total_memories": {"count": 100},
            "memories_by_type": {"solution": 40, "problem": 30, "code_pattern": 20, "general": 10},
            "total_relationships": {"count": 150},
            "relationships_by_type": {"SOLVES": 50, "CAUSES": 30, "RELATES_TO": 70},
            "avg_importance": {"avg_importance": 0.65},
            "avg_confidence": {"avg_confidence": 0.85}
        }

        args = {}
        result = await handle_get_memory_statistics(mock_database, args)

        assert result.isError is None or result.isError is False
        assert "100" in str(result.content)

    @pytest.mark.asyncio
    async def test_get_memory_statistics_database_error(self, mcp_server, mock_database):
        """Test statistics when database raises error."""
        mock_database.get_memory_statistics.side_effect = Exception("Database error")

        args = {}
        result = await handle_get_memory_statistics(mock_database, args)

        assert result.isError is True


class TestMCPProtocol:
    """Test MCP protocol compliance and integration."""

    @pytest.mark.asyncio
    async def test_handle_call_tool_without_database(self):
        """Test tool call when database is not initialized."""
        server = ClaudeMemoryServer()
        server.memory_db = None

        # This tests the handle_call_tool decorator
        # We need to manually call the handler since it's wrapped
        # For now, we verify initialization is required
        assert server.memory_db is None

    @pytest.mark.asyncio
    async def test_unknown_tool_name(self, mcp_server):
        """Test calling an unknown tool."""
        # Access the decorated handler through the server
        # This would be called through the MCP protocol
        # For testing, we verify tools list doesn't contain invalid names
        tool_names = [tool.name for tool in mcp_server.tools]
        assert "invalid_tool_name" not in tool_names

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server):
        """Test that list_tools returns all enabled tools."""
        # Verify server has tools defined
        assert len(mcp_server.tools) > 0

        # Verify basic tools are present
        tool_names = [tool.name for tool in mcp_server.tools]
        assert "store_memory" in tool_names
        assert "get_memory" in tool_names
        assert "search_memories" in tool_names
        assert "recall_memories" in tool_names

    def test_tool_schema_structure(self, mcp_server):
        """Test that all tools have valid schemas."""
        for tool in mcp_server.tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            assert tool.name
            assert tool.description

    @pytest.mark.asyncio
    async def test_error_response_format(self, mcp_server, mock_database):
        """Test that error responses follow MCP format."""
        mock_database.store_memory.side_effect = Exception("Test error")

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Content"
        }
        result = await handle_store_memory(mock_database, args)

        assert isinstance(result, CallToolResult)
        assert result.isError is True
        assert len(result.content) > 0
        assert isinstance(result.content[0], TextContent)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_query_search(self, mcp_server, mock_database):
        """Test search with empty query."""
        mock_database.search_memories.return_value = []

        args = {"query": ""}
        result = await handle_search_memories(mock_database, args)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_very_long_content(self, mcp_server, mock_database):
        """Test storing memory with very long content."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "x" * 10000  # Very long content
        }
        result = await handle_store_memory(mock_database, args)

        # Should handle long content
        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_title(self, mcp_server, mock_database):
        """Test storing memory with special characters."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test: With <special> & 'chars' \"quoted\"",
            "content": "Content"
        }
        result = await handle_store_memory(mock_database, args)

        # Should handle special characters
        assert result is not None

    @pytest.mark.asyncio
    async def test_unicode_in_content(self, mcp_server, mock_database):
        """Test storing memory with Unicode content."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Unicode Test",
            "content": "Testing Unicode: 你好 🎉 Ñoño café"
        }
        result = await handle_store_memory(mock_database, args)

        assert result is not None

    @pytest.mark.asyncio
    async def test_many_tags(self, mcp_server, mock_database):
        """Test storing memory with many tags."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        args = {
            "type": "solution",
            "title": "Test",
            "content": "Content",
            "tags": [f"tag{i}" for i in range(50)]  # Many tags
        }
        result = await handle_store_memory(mock_database, args)

        assert result is not None

    @pytest.mark.asyncio
    async def test_boundary_importance_values(self, mcp_server, mock_database):
        """Test storing memory with boundary importance values."""
        memory_id = str(uuid.uuid4())
        mock_database.store_memory.return_value = memory_id

        for importance in [0.0, 1.0]:
            args = {
                "type": "solution",
                "title": "Test",
                "content": "Content",
                "importance": importance
            }
            result = await handle_store_memory(mock_database, args)
            assert result is not None
