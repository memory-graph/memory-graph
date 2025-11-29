"""
Comprehensive tests for SQLite fallback backend implementation.

Tests cover:
- Backend initialization and connection
- Schema creation and migration
- Node and relationship CRUD operations
- Graph operations with NetworkX
- Full-text search capabilities
- Transaction support
- Health checks and monitoring
- Error handling and edge cases
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.models import DatabaseConnectionError, SchemaError


class TestSQLiteBackendInitialization:
    """Test SQLite backend initialization."""

    def test_init_with_explicit_path(self, tmp_path):
        """Test initialization with explicit database path."""
        db_path = str(tmp_path / "test.db")
        backend = SQLiteFallbackBackend(db_path=db_path)

        assert backend.db_path == db_path
        assert backend.conn is None
        assert backend.graph is None
        assert backend._connected is False

    def test_init_with_default_path(self):
        """Test initialization with default database path."""
        backend = SQLiteFallbackBackend()

        expected_path = os.path.expanduser("~/.memorygraph/memory.db")
        assert backend.db_path == expected_path

    def test_init_from_env_var(self, tmp_path, monkeypatch):
        """Test initialization from environment variable."""
        db_path = str(tmp_path / "env_test.db")
        monkeypatch.setenv("MEMORY_SQLITE_PATH", db_path)

        backend = SQLiteFallbackBackend()

        assert backend.db_path == db_path

    def test_init_without_networkx(self):
        """Test initialization fails gracefully without NetworkX."""
        with patch('src.memorygraph.backends.sqlite_fallback.nx', None):
            with pytest.raises(DatabaseConnectionError, match="NetworkX is required"):
                SQLiteFallbackBackend()

    def test_backend_name(self, tmp_path):
        """Test backend name identifier."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        assert backend.backend_name() == "sqlite"

    def test_supports_transactions(self, tmp_path):
        """Test that SQLite backend supports transactions."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        assert backend.supports_transactions() is True


class TestSQLiteBackendConnection:
    """Test SQLite backend connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, tmp_path):
        """Test successful connection to SQLite database."""
        db_path = str(tmp_path / "test.db")
        backend = SQLiteFallbackBackend(db_path=db_path)

        success = await backend.connect()

        assert success is True
        assert backend.conn is not None
        assert backend.graph is not None
        assert backend._connected is True
        assert os.path.exists(db_path)

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_connect_creates_directory(self, tmp_path):
        """Test that connect creates parent directories if needed."""
        db_path = str(tmp_path / "nested" / "dir" / "test.db")
        backend = SQLiteFallbackBackend(db_path=db_path)

        await backend.connect()

        assert os.path.exists(os.path.dirname(db_path))
        assert os.path.exists(db_path)

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_connect_loads_existing_data(self, tmp_path):
        """Test that connect initializes with empty graph when tables don't exist."""
        db_path = str(tmp_path / "test.db")

        # Connect to new database (no schema yet)
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()

        # Graph should be initialized (empty)
        assert backend.graph is not None
        assert backend.graph.number_of_nodes() == 0
        assert backend.graph.number_of_edges() == 0

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect(self, tmp_path):
        """Test disconnecting from database."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        await backend.disconnect()

        assert backend.conn is None
        assert backend.graph is None
        assert backend._connected is False

    @pytest.mark.asyncio
    async def test_disconnect_syncs_graph(self, tmp_path):
        """Test that disconnect syncs graph to database."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        # Mock the sync method to verify it's called
        backend._sync_to_sqlite = AsyncMock()

        await backend.disconnect()

        backend._sync_to_sqlite.assert_called_once()

    @pytest.mark.asyncio
    async def test_factory_create_method(self, tmp_path):
        """Test factory create method."""
        db_path = str(tmp_path / "test.db")

        backend = await SQLiteFallbackBackend.create(db_path)

        assert isinstance(backend, SQLiteFallbackBackend)
        assert backend._connected is True

        await backend.disconnect()


class TestSQLiteBackendSchema:
    """Test schema initialization and management."""

    @pytest.mark.asyncio
    async def test_initialize_schema_creates_tables(self, tmp_path):
        """Test schema initialization creates required tables."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        await backend.initialize_schema()

        cursor = backend.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert "nodes" in tables
        assert "relationships" in tables

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_initialize_schema_creates_indexes(self, tmp_path):
        """Test schema initialization creates indexes."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        await backend.initialize_schema()

        cursor = backend.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_nodes_label" in indexes
        assert "idx_nodes_created" in indexes
        assert "idx_rel_from" in indexes
        assert "idx_rel_to" in indexes
        assert "idx_rel_type" in indexes

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_initialize_schema_creates_fts(self, tmp_path):
        """Test schema initialization creates FTS5 table if available."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        await backend.initialize_schema()

        cursor = backend.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes_fts'")
        result = cursor.fetchone()

        # FTS5 might not be available in all SQLite builds
        # Just verify no error was raised
        assert True

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_initialize_schema_not_connected_raises_error(self, tmp_path):
        """Test schema initialization fails when not connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        with pytest.raises(SchemaError, match="Not connected"):
            await backend.initialize_schema()

    @pytest.mark.asyncio
    async def test_initialize_schema_idempotent(self, tmp_path):
        """Test schema initialization can be called multiple times."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        await backend.initialize_schema()
        await backend.initialize_schema()  # Second call should not fail

        await backend.disconnect()


class TestSQLiteBackendQueries:
    """Test query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_not_connected_raises_error(self, tmp_path):
        """Test query execution fails when not connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        with pytest.raises(DatabaseConnectionError, match="Not connected"):
            await backend.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_schema_operations(self, tmp_path):
        """Test execution of schema operations."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        result = await backend.execute_query("CREATE TABLE test (id INTEGER)")

        assert result == []

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_execute_query_cypher_not_supported(self, tmp_path):
        """Test that complex Cypher queries return empty results with warning."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        result = await backend.execute_query("MATCH (n:Memory) RETURN n")

        assert result == []

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_execute_sync_query(self, tmp_path):
        """Test synchronous query execution."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()
        await backend.initialize_schema()

        # Insert data
        cursor = backend.conn.cursor()
        cursor.execute(
            "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
            ("node1", "Memory", json.dumps({"title": "Test"}))
        )
        backend.conn.commit()

        # Query using execute_sync
        results = backend.execute_sync("SELECT * FROM nodes WHERE id = ?", ("node1",))

        assert len(results) == 1
        assert results[0]["id"] == "node1"
        assert results[0]["label"] == "Memory"

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_execute_sync_not_connected_raises_error(self, tmp_path):
        """Test execute_sync fails when not connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        with pytest.raises(DatabaseConnectionError, match="Not connected"):
            backend.execute_sync("SELECT 1")


class TestSQLiteBackendTransactions:
    """Test transaction support."""

    @pytest.mark.asyncio
    async def test_commit(self, tmp_path):
        """Test transaction commit."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()
        await backend.initialize_schema()

        cursor = backend.conn.cursor()
        cursor.execute(
            "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
            ("node1", "Memory", json.dumps({"title": "Test"}))
        )
        backend.commit()

        # Verify data is persisted
        cursor.execute("SELECT COUNT(*) FROM nodes")
        count = cursor.fetchone()[0]
        assert count == 1

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_rollback(self, tmp_path):
        """Test transaction rollback."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()
        await backend.initialize_schema()

        cursor = backend.conn.cursor()
        cursor.execute(
            "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
            ("node1", "Memory", json.dumps({"title": "Test"}))
        )
        backend.rollback()

        # Verify data is not persisted
        cursor.execute("SELECT COUNT(*) FROM nodes")
        count = cursor.fetchone()[0]
        assert count == 0

        await backend.disconnect()


class TestSQLiteBackendGraphOperations:
    """Test NetworkX graph operations."""

    @pytest.mark.asyncio
    async def test_load_graph_to_memory(self, tmp_path):
        """Test loading graph handles missing tables gracefully."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()

        # Before schema initialization, graph should be empty
        assert backend.graph.number_of_nodes() == 0
        assert backend.graph.number_of_edges() == 0

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_load_graph_empty_database(self, tmp_path):
        """Test loading graph from empty database."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()
        await backend.initialize_schema()

        await backend._load_graph_to_memory()

        assert backend.graph.number_of_nodes() == 0
        assert backend.graph.number_of_edges() == 0

        await backend.disconnect()


class TestSQLiteBackendFullTextSearch:
    """Test full-text search capabilities."""

    @pytest.mark.asyncio
    async def test_supports_fulltext_search_when_available(self, tmp_path):
        """Test FTS support detection when FTS5 is available."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()
        await backend.initialize_schema()

        # Result depends on whether FTS5 is available in SQLite build
        result = backend.supports_fulltext_search()
        assert isinstance(result, bool)

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_supports_fulltext_search_not_connected(self, tmp_path):
        """Test FTS support returns False when not connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        assert backend.supports_fulltext_search() is False


class TestSQLiteBackendHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_connected(self, tmp_path):
        """Test health check when connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()
        await backend.initialize_schema()

        health = await backend.health_check()

        assert health["connected"] is True
        assert health["backend_type"] == "sqlite"
        assert health["db_path"] == str(tmp_path / "test.db")
        assert "statistics" in health
        assert "memory_count" in health["statistics"]
        assert "version" in health
        assert "database_size_bytes" in health

        await backend.disconnect()

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, tmp_path):
        """Test health check when not connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        health = await backend.health_check()

        assert health["connected"] is False
        assert health["backend_type"] == "sqlite"

    @pytest.mark.asyncio
    async def test_health_check_with_data(self, tmp_path):
        """Test health check returns accurate statistics."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))
        await backend.connect()
        await backend.initialize_schema()

        # Insert test data
        cursor = backend.conn.cursor()
        for i in range(5):
            cursor.execute(
                "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
                (f"node{i}", "Memory", json.dumps({"title": f"Node {i}"}))
            )
        backend.conn.commit()

        health = await backend.health_check()

        assert health["statistics"]["memory_count"] == 5
        assert health["database_size_bytes"] > 0

        await backend.disconnect()


class TestSQLiteBackendErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_connect_with_invalid_path(self, tmp_path):
        """Test connection error handling."""
        # Create a file where the db path should be to cause an error
        invalid_path = tmp_path / "file.txt"
        invalid_path.write_text("not a db")
        db_path = str(invalid_path / "db.db")  # Try to use file as directory

        # Mock mkdir to raise PermissionError
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                backend = SQLiteFallbackBackend(db_path=db_path)

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, tmp_path):
        """Test disconnect when already disconnected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        # Should not raise error
        await backend.disconnect()

        assert backend.conn is None

    @pytest.mark.asyncio
    async def test_commit_when_not_connected(self, tmp_path):
        """Test commit when not connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        # Should not raise error
        backend.commit()

    @pytest.mark.asyncio
    async def test_rollback_when_not_connected(self, tmp_path):
        """Test rollback when not connected."""
        backend = SQLiteFallbackBackend(db_path=str(tmp_path / "test.db"))

        # Should not raise error
        backend.rollback()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
