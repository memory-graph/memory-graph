"""
Additional tests for graph_algorithms.py to achieve 95%+ coverage.

Focus on:
- Error handling paths
- Edge cases
- Alternative backends
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.models import Memory, MemoryType, RelationshipType
from memorygraph.utils.graph_algorithms import has_cycle, _get_outgoing_relationships, find_all_cycles


class TestGraphAlgorithmsErrorHandling:
    """Test error handling in graph algorithms."""

    @pytest.fixture
    async def memory_db(self, tmp_path):
        """Create a test database."""
        db_path = str(tmp_path / "test_graph_alg.db")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        await backend.initialize_schema()
        db = SQLiteMemoryDatabase(backend)
        await db.initialize_schema()
        yield db
        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_has_cycle_with_database_error_during_dfs(self, memory_db):
        """Test has_cycle handles database errors during DFS traversal."""
        # Create memories
        mem1_id = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="M1", content="Memory 1")
        )
        mem2_id = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="M2", content="Memory 2")
        )

        # Mock get_related_memories to raise an exception
        original_get_related = memory_db.get_related_memories

        async def failing_get_related(*args, **kwargs):
            """Mock that raises an exception."""
            raise Exception("Database connection lost")

        memory_db.get_related_memories = failing_get_related

        # Should return False (not create cycle) when error occurs
        result = await has_cycle(memory_db, mem1_id, mem2_id, RelationshipType.FOLLOWS)

        # Restore original method
        memory_db.get_related_memories = original_get_related

        # Error during traversal should return False (safe default)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_outgoing_relationships_with_neo4j_backend(self):
        """Test _get_outgoing_relationships with Neo4j-style backend."""
        # Create a mock database without 'backend' attribute (like Neo4j)
        mock_db = MagicMock()
        # Remove backend attribute to trigger else branch
        del mock_db.backend

        # Create mock connection
        mock_connection = MagicMock()
        mock_db.connection = mock_connection

        # Mock execute_read_query
        mock_connection.execute_read_query = AsyncMock(
            return_value=[{"to_id": "mem2"}, {"to_id": "mem3"}]
        )

        # Call the function
        result = await _get_outgoing_relationships(
            mock_db, "mem1", RelationshipType.FOLLOWS
        )

        # Should have called execute_read_query
        mock_connection.execute_read_query.assert_called_once()
        assert result == ["mem2", "mem3"]

    @pytest.mark.asyncio
    async def test_get_outgoing_relationships_with_backend_error(self):
        """Test _get_outgoing_relationships handles errors gracefully."""
        # Create a mock database with backend
        mock_db = MagicMock()
        mock_backend = MagicMock()
        mock_db.backend = mock_backend

        # Mock execute_sync to raise exception
        mock_backend.execute_sync.side_effect = Exception("Database error")

        # Call the function
        result = await _get_outgoing_relationships(
            mock_db, "mem1", RelationshipType.FOLLOWS
        )

        # Should return empty list on error
        assert result == []

    @pytest.mark.asyncio
    async def test_get_outgoing_relationships_with_neo4j_error(self):
        """Test _get_outgoing_relationships handles Neo4j backend errors."""
        # Create a mock database without backend attribute
        mock_db = MagicMock()
        del mock_db.backend

        # Create mock connection that raises error
        mock_connection = MagicMock()
        mock_db.connection = mock_connection
        mock_connection.execute_read_query = AsyncMock(
            side_effect=Exception("Connection lost")
        )

        # Call the function
        result = await _get_outgoing_relationships(
            mock_db, "mem1", RelationshipType.FOLLOWS
        )

        # Should return empty list on error
        assert result == []


class TestFindAllCycles:
    """Test find_all_cycles function."""

    @pytest.mark.asyncio
    async def test_find_all_cycles_not_implemented(self):
        """Test that find_all_cycles raises NotImplementedError."""
        mock_db = MagicMock()

        with pytest.raises(NotImplementedError, match="not yet implemented"):
            await find_all_cycles(mock_db)

    @pytest.mark.asyncio
    async def test_find_all_cycles_with_relationship_type(self):
        """Test find_all_cycles with relationship type filter."""
        mock_db = MagicMock()

        with pytest.raises(NotImplementedError):
            await find_all_cycles(mock_db, relationship_type=RelationshipType.FOLLOWS)


class TestGraphAlgorithmsEdgeCases:
    """Test edge cases in graph algorithms."""

    @pytest.fixture
    async def memory_db(self, tmp_path):
        """Create a test database."""
        db_path = str(tmp_path / "test_edge_cases.db")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        await backend.initialize_schema()
        db = SQLiteMemoryDatabase(backend)
        await db.initialize_schema()
        yield db
        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_has_cycle_max_depth_limit(self, memory_db):
        """Test that max_depth limit is respected."""
        # Create a long chain of memories
        mem_ids = []
        for i in range(10):
            mem_id = await memory_db.store_memory(
                Memory(type=MemoryType.GENERAL, title=f"M{i}", content=f"Memory {i}")
            )
            mem_ids.append(mem_id)

        # Create a chain: M0 → M1 → M2 → ... → M9
        for i in range(len(mem_ids) - 1):
            await memory_db.create_relationship(
                mem_ids[i], mem_ids[i + 1], RelationshipType.FOLLOWS
            )

        # Try to detect cycle with very small max_depth
        # This should hit the depth limit
        result = await has_cycle(
            memory_db, mem_ids[-1], mem_ids[0], RelationshipType.FOLLOWS, max_depth=2
        )

        # With small depth limit, should return False (can't reach target)
        assert result is False

    @pytest.mark.asyncio
    async def test_has_cycle_already_visited_node(self, memory_db):
        """Test that visited nodes are not re-traversed."""
        # Create a diamond-shaped graph:
        #     A
        #    / \\
        #   B   C
        #    \\ /
        #     D
        mem_a = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="A", content="Node A")
        )
        mem_b = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="B", content="Node B")
        )
        mem_c = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="C", content="Node C")
        )
        mem_d = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="D", content="Node D")
        )

        # Create edges: A → B, A → C, B → D, C → D
        await memory_db.create_relationship(mem_a, mem_b, RelationshipType.FOLLOWS)
        await memory_db.create_relationship(mem_a, mem_c, RelationshipType.FOLLOWS)
        await memory_db.create_relationship(mem_b, mem_d, RelationshipType.FOLLOWS)
        await memory_db.create_relationship(mem_c, mem_d, RelationshipType.FOLLOWS)

        # Check if D → A would create a cycle (it would)
        result = await has_cycle(memory_db, mem_d, mem_a, RelationshipType.FOLLOWS)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_outgoing_relationships_with_sqlite_backend(self, memory_db):
        """Test _get_outgoing_relationships with SQLite backend."""
        # Create memories
        mem1 = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="M1", content="Memory 1")
        )
        mem2 = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="M2", content="Memory 2")
        )
        mem3 = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="M3", content="Memory 3")
        )

        # Create relationships: mem1 → mem2, mem1 → mem3
        await memory_db.create_relationship(mem1, mem2, RelationshipType.FOLLOWS)
        await memory_db.create_relationship(mem1, mem3, RelationshipType.FOLLOWS)

        # Get outgoing relationships
        result = await _get_outgoing_relationships(
            memory_db, mem1, RelationshipType.FOLLOWS
        )

        # Should return both targets
        assert len(result) == 2
        assert mem2 in result
        assert mem3 in result

    @pytest.mark.asyncio
    async def test_get_outgoing_relationships_no_matches(self, memory_db):
        """Test _get_outgoing_relationships with no matching relationships."""
        # Create a memory with no outgoing relationships
        mem1 = await memory_db.store_memory(
            Memory(type=MemoryType.GENERAL, title="M1", content="Memory 1")
        )

        # Get outgoing relationships (should be empty)
        result = await _get_outgoing_relationships(
            memory_db, mem1, RelationshipType.FOLLOWS
        )

        assert result == []
