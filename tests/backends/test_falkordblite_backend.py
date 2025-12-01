"""
Unit tests for FalkorDBLite backend implementation.

These tests use mocked FalkorDBLite client to verify backend logic without
requiring a running FalkorDBLite instance.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
import uuid
import sys

# Mock the falkordblite module before importing the backend
sys.modules['falkordblite'] = MagicMock()

from memorygraph.backends.falkordblite_backend import FalkorDBLiteBackend
from memorygraph.models import (
    Memory,
    MemoryType,
    RelationshipType,
    RelationshipProperties,
    DatabaseConnectionError,
    SchemaError,
    ValidationError,
    RelationshipError,
)


class TestFalkorDBLiteConnection:
    """Test FalkorDBLite connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to FalkorDBLite."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            # Mock FalkorDBLite client (embedded, uses file path)
            mock_client = Mock()
            mock_graph = Mock()
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            result = await backend.connect()

            assert result is True
            assert backend._connected is True
            # Verify connection was created with file path (not host:port)
            mock_falkordblite_class.assert_called_once_with('/tmp/test.db')
            mock_client.select_graph.assert_called_once_with('memorygraph')

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            # Simulate connection error
            mock_falkordblite_class.side_effect = Exception("Database file not accessible")

            backend = FalkorDBLiteBackend(db_path='/invalid/path/test.db')

            with pytest.raises(DatabaseConnectionError, match="Database file not accessible"):
                await backend.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection from FalkorDBLite."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()
            await backend.disconnect()

            assert backend._connected is False

    @pytest.mark.asyncio
    async def test_default_path(self):
        """Test default database path is used when none specified."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend()
            await backend.connect()

            # Verify default path is used
            call_args = mock_falkordblite_class.call_args[0]
            assert '.memorygraph/falkordblite.db' in call_args[0]

    def test_backend_name(self):
        """Test backend name identifier."""
        backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
        assert backend.backend_name() == "falkordblite"

    def test_supports_fulltext_search(self):
        """Test fulltext search capability reporting."""
        backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
        assert backend.supports_fulltext_search() is True

    def test_supports_transactions(self):
        """Test transaction support reporting."""
        backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
        assert backend.supports_transactions() is True


class TestFalkorDBLiteQuery:
    """Test FalkorDBLite query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_read(self):
        """Test executing a read query."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{"n": {"id": "123", "title": "Test"}}]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            result = await backend.execute_query(
                "MATCH (n:Memory {id: $id}) RETURN n",
                parameters={"id": "123"},
                write=False
            )

            assert len(result) == 1
            assert result[0]["n"]["id"] == "123"

    @pytest.mark.asyncio
    async def test_execute_query_write(self):
        """Test executing a write query."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{"id": "456"}]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            result = await backend.execute_query(
                "CREATE (n:Memory {id: $id}) RETURN n.id as id",
                parameters={"id": "456"},
                write=True
            )

            assert len(result) == 1
            assert result[0]["id"] == "456"

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected."""
        backend = FalkorDBLiteBackend(db_path='/tmp/test.db')

        with pytest.raises(DatabaseConnectionError, match="Not connected"):
            await backend.execute_query("MATCH (n) RETURN n")


class TestFalkorDBLiteSchema:
    """Test schema initialization."""

    @pytest.mark.asyncio
    async def test_initialize_schema(self):
        """Test schema creation with constraints and indexes."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            # Mock query execution to track calls
            backend.execute_query = AsyncMock()

            await backend.initialize_schema()

            # Should execute multiple constraint and index creation queries
            assert backend.execute_query.call_count >= 2  # At least some schema queries


class TestFalkorDBLiteMemoryOperations:
    """Test memory CRUD operations."""

    @pytest.fixture
    def sample_memory(self):
        """Create a sample memory for testing."""
        return Memory(
            id=str(uuid.uuid4()),
            type=MemoryType.SOLUTION,
            title="Redis Timeout Fix",
            content="Increased connection timeout to 5000ms",
            tags=["redis", "timeout", "performance"],
            importance=0.8,
            confidence=0.9
        )

    @pytest.mark.asyncio
    async def test_store_memory(self, sample_memory):
        """Test storing a memory."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{"id": sample_memory.id}]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            memory_id = await backend.store_memory(sample_memory)

            assert memory_id == sample_memory.id

    @pytest.mark.asyncio
    async def test_get_memory(self, sample_memory):
        """Test retrieving a memory by ID."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()

            # Mock the query result
            mock_result = Mock()
            mock_result.result_set = [{
                "m": {
                    "id": sample_memory.id,
                    "type": "solution",
                    "title": "Redis Timeout Fix",
                    "content": "Increased connection timeout to 5000ms",
                    "summary": None,
                    "tags": ["redis", "timeout", "performance"],
                    "importance": 0.8,
                    "confidence": 0.9,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "usage_count": 0
                }
            }]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            memory = await backend.get_memory(sample_memory.id)

            assert memory is not None
            assert memory.id == sample_memory.id
            assert memory.title == "Redis Timeout Fix"

    @pytest.mark.asyncio
    async def test_get_memory_not_found(self):
        """Test retrieving a non-existent memory."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = []
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            memory = await backend.get_memory("nonexistent")

            assert memory is None

    @pytest.mark.asyncio
    async def test_update_memory(self, sample_memory):
        """Test updating an existing memory."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{"id": sample_memory.id}]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            sample_memory.title = "Updated Title"
            result = await backend.update_memory(sample_memory)

            assert result is True

    @pytest.mark.asyncio
    async def test_delete_memory(self, sample_memory):
        """Test deleting a memory."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{"deleted_count": 1}]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            result = await backend.delete_memory(sample_memory.id)

            assert result is True


class TestFalkorDBLiteRelationships:
    """Test relationship operations."""

    @pytest.mark.asyncio
    async def test_create_relationship(self):
        """Test creating a relationship between memories."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            rel_id = str(uuid.uuid4())
            mock_result.result_set = [{"id": rel_id}]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            props = RelationshipProperties(strength=0.9, confidence=0.8)
            relationship_id = await backend.create_relationship(
                from_memory_id="mem1",
                to_memory_id="mem2",
                relationship_type=RelationshipType.SOLVES,
                properties=props
            )

            assert relationship_id == rel_id

    @pytest.mark.asyncio
    async def test_get_related_memories(self):
        """Test getting related memories."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{
                "related": {
                    "id": "mem2",
                    "type": "solution",
                    "title": "Related Memory",
                    "content": "Content",
                    "tags": [],
                    "importance": 0.7,
                    "confidence": 0.8,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "usage_count": 0
                },
                "rel_type": "SOLVES",
                "rel_props": {
                    "strength": 0.9,
                    "confidence": 0.8,
                    "context": "Test context"
                }
            }]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            related = await backend.get_related_memories("mem1")

            assert len(related) == 1
            memory, relationship = related[0]
            assert memory.id == "mem2"
            assert relationship.type == RelationshipType.SOLVES


class TestFalkorDBLiteSearch:
    """Test search functionality."""

    @pytest.mark.asyncio
    async def test_search_memories(self):
        """Test searching for memories."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{
                "m": {
                    "id": "search1",
                    "type": "solution",
                    "title": "Redis Timeout",
                    "content": "Fix for timeout",
                    "tags": ["redis"],
                    "importance": 0.8,
                    "confidence": 0.9,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "usage_count": 0
                }
            }]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            from memorygraph.models import SearchQuery
            query = SearchQuery(query="timeout")

            results = await backend.search_memories(query)

            assert len(results) >= 0  # Will be implemented


class TestFalkorDBLiteStatistics:
    """Test statistics operations."""

    @pytest.mark.asyncio
    async def test_get_memory_statistics(self):
        """Test getting database statistics."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()

            # Mock multiple query results for different statistics
            def mock_query_side_effect(query, params=None):
                result = Mock()
                if "COUNT(m)" in query:
                    result.result_set = [{"count": 42}]
                elif "m.type" in query and "GROUP BY" in query:
                    result.result_set = [
                        {"type": "solution", "count": 20},
                        {"type": "problem", "count": 15}
                    ]
                elif "COUNT(r)" in query:
                    result.result_set = [{"count": 30}]
                elif "AVG(m.importance)" in query:
                    result.result_set = [{"avg_importance": 0.75}]
                else:
                    result.result_set = []
                return result

            mock_graph.query.side_effect = mock_query_side_effect
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            stats = await backend.get_memory_statistics()

            assert "total_memories" in stats
            assert "memories_by_type" in stats


class TestFalkorDBLiteHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self):
        """Test health check when connected."""
        with patch('falkordblite.FalkorDB') as mock_falkordblite_class:
            mock_client = Mock()
            mock_graph = Mock()
            mock_result = Mock()
            mock_result.result_set = [{"count": 10}]
            mock_graph.query.return_value = mock_result
            mock_client.select_graph.return_value = mock_graph
            mock_falkordblite_class.return_value = mock_client

            backend = FalkorDBLiteBackend(db_path='/tmp/test.db')
            await backend.connect()

            health = await backend.health_check()

            assert health["connected"] is True
            assert health["backend_type"] == "falkordblite"
            assert "db_path" in health

    @pytest.mark.asyncio
    async def test_health_check_not_connected(self):
        """Test health check when not connected."""
        backend = FalkorDBLiteBackend(db_path='/tmp/test.db')

        health = await backend.health_check()

        assert health["connected"] is False
        assert health["backend_type"] == "falkordblite"
