"""
Comprehensive tests for Turso backend module.

Tests cover:
- Initialization and configuration
- Connection management (local, remote, embedded replica)
- Schema initialization
- Query execution
- Health checks
- Sync functionality
- Error handling
"""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from pathlib import Path

from memorygraph.backends.turso import TursoBackend
from memorygraph.models import DatabaseConnectionError, SchemaError


@pytest.fixture
def mock_libsql():
    """Mock libsql module."""
    with patch('memorygraph.backends.turso.libsql') as mock:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = None
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock.connect.return_value = mock_conn
        yield mock


@pytest.fixture
def mock_networkx():
    """Mock NetworkX module."""
    with patch('memorygraph.backends.turso.nx') as mock:
        mock_graph = MagicMock()
        mock_graph.number_of_nodes.return_value = 0
        mock_graph.number_of_edges.return_value = 0
        mock.DiGraph.return_value = mock_graph
        yield mock


class TestTursoBackendInitialization:
    """Test TursoBackend initialization."""

    def test_initialization_without_libsql_raises(self):
        """Test that missing libsql raises error."""
        with patch('memorygraph.backends.turso.libsql', None):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                TursoBackend()
            assert "libsql-experimental is required" in str(exc_info.value)

    def test_initialization_without_networkx_raises(self):
        """Test that missing NetworkX raises error."""
        # NetworkX check happens after libsql check, so we need to mock libsql first
        with patch('memorygraph.backends.turso.libsql') as mock_libsql:
            mock_libsql.connect.return_value = MagicMock()
            with patch('memorygraph.backends.turso.nx', None):
                with pytest.raises(DatabaseConnectionError) as exc_info:
                    TursoBackend()
                assert "NetworkX is required" in str(exc_info.value)

    def test_initialization_with_defaults(self, mock_libsql, mock_networkx):
        """Test initialization with default values."""
        backend = TursoBackend()
        assert backend.db_path is not None
        assert backend.sync_url is None
        assert backend.auth_token is None
        assert backend._connected is False

    def test_initialization_with_explicit_path(self, mock_libsql, mock_networkx):
        """Test initialization with explicit database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = TursoBackend(db_path=db_path)
            assert backend.db_path == db_path

    def test_initialization_with_sync_url(self, mock_libsql, mock_networkx):
        """Test initialization with sync URL and auth token."""
        backend = TursoBackend(
            sync_url="libsql://test.turso.io",
            auth_token="test_token"
        )
        assert backend.sync_url == "libsql://test.turso.io"
        assert backend.auth_token == "test_token"

    def test_initialization_from_env_vars(self, mock_libsql, mock_networkx):
        """Test initialization from environment variables."""
        with patch.dict('os.environ', {
            'TURSO_DATABASE_URL': 'libsql://env.turso.io',
            'TURSO_AUTH_TOKEN': 'env_token'
        }):
            backend = TursoBackend()
            assert backend.sync_url == 'libsql://env.turso.io'
            assert backend.auth_token == 'env_token'

    def test_creates_directory_for_db_path(self, mock_libsql, mock_networkx):
        """Test that parent directory is created for db_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "nested", "test.db")
            backend = TursoBackend(db_path=db_path)
            assert Path(db_path).parent.exists()


class TestTursoBackendConnection:
    """Test connection management."""

    @pytest.mark.asyncio
    async def test_connect_local_mode(self, mock_libsql, mock_networkx):
        """Test connection in local-only mode."""
        backend = TursoBackend(db_path=":memory:")

        result = await backend.connect()

        assert result is True
        assert backend._connected is True
        mock_libsql.connect.assert_called_once_with(":memory:")

    @pytest.mark.asyncio
    async def test_connect_remote_mode(self, mock_libsql, mock_networkx):
        """Test connection in remote-only mode."""
        backend = TursoBackend(
            sync_url="libsql://test.turso.io",
            auth_token=None
        )

        result = await backend.connect()

        assert result is True
        assert backend._connected is True
        mock_libsql.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_embedded_replica_mode(self, mock_libsql, mock_networkx):
        """Test connection in embedded replica mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            backend = TursoBackend(
                db_path=db_path,
                sync_url="libsql://test.turso.io",
                auth_token="test_token"
            )

            # Mock sync method
            mock_conn = mock_libsql.connect.return_value
            mock_conn.sync = Mock()

            result = await backend.connect()

            assert result is True
            assert backend._connected is True
            mock_libsql.connect.assert_called_once()
            # Verify sync was called
            assert mock_conn.sync.called

    @pytest.mark.asyncio
    async def test_connect_loads_graph_to_memory(self, mock_libsql, mock_networkx):
        """Test that connection loads existing graph data."""
        backend = TursoBackend(db_path=":memory:")

        # Mock cursor to return test data
        mock_cursor = mock_libsql.connect.return_value.cursor.return_value
        mock_cursor.fetchall.side_effect = [
            [("node1", "solution", "Title 1"), ("node2", "problem", "Title 2")],  # nodes
            [("node1", "node2", "SOLVES")]  # relationships
        ]

        await backend.connect()

        assert backend.graph is not None
        # Verify add_node and add_edge were called
        assert backend.graph.add_node.call_count == 2
        assert backend.graph.add_edge.call_count == 1

    @pytest.mark.asyncio
    async def test_connect_failure_raises_error(self, mock_libsql, mock_networkx):
        """Test connection failure raises DatabaseConnectionError."""
        backend = TursoBackend(db_path=":memory:")
        mock_libsql.connect.side_effect = Exception("Connection failed")

        with pytest.raises(DatabaseConnectionError) as exc_info:
            await backend.connect()

        assert "Failed to connect to Turso" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect_without_sync(self, mock_libsql, mock_networkx):
        """Test disconnection in local mode."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        await backend.disconnect()

        assert backend._connected is False
        assert backend.conn is None
        assert backend.graph is None

    @pytest.mark.asyncio
    async def test_disconnect_with_sync(self, mock_libsql, mock_networkx):
        """Test disconnection in embedded replica mode syncs first."""
        backend = TursoBackend(
            db_path=":memory:",
            sync_url="libsql://test.turso.io",
            auth_token="test_token"
        )
        await backend.connect()

        mock_conn = backend.conn
        mock_conn.sync = Mock()

        await backend.disconnect()

        # Verify sync was called before close
        assert mock_conn.sync.called
        assert backend._connected is False


class TestTursoBackendSchemaInitialization:
    """Test schema initialization."""

    @pytest.mark.asyncio
    async def test_initialize_schema_creates_tables(self, mock_libsql, mock_networkx):
        """Test that initialize_schema creates required tables."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value

        await backend.initialize_schema()

        # Verify cursor.execute was called with CREATE TABLE statements
        execute_calls = mock_cursor.execute.call_args_list
        sql_statements = [call[0][0] for call in execute_calls]

        # Check for key tables
        assert any("CREATE TABLE IF NOT EXISTS nodes" in sql for sql in sql_statements)
        assert any("CREATE TABLE IF NOT EXISTS relationships" in sql for sql in sql_statements)
        assert any("CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts" in sql for sql in sql_statements)

    @pytest.mark.asyncio
    async def test_initialize_schema_creates_indexes(self, mock_libsql, mock_networkx):
        """Test that initialize_schema creates indexes."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value

        await backend.initialize_schema()

        execute_calls = mock_cursor.execute.call_args_list
        sql_statements = [call[0][0] for call in execute_calls]

        # Check for indexes
        assert any("CREATE INDEX IF NOT EXISTS idx_nodes_type" in sql for sql in sql_statements)
        assert any("CREATE INDEX IF NOT EXISTS idx_relationships_from" in sql for sql in sql_statements)

    @pytest.mark.asyncio
    async def test_initialize_schema_creates_fts_triggers(self, mock_libsql, mock_networkx):
        """Test that initialize_schema creates FTS triggers."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value

        await backend.initialize_schema()

        execute_calls = mock_cursor.execute.call_args_list
        sql_statements = [call[0][0] for call in execute_calls]

        # Check for triggers
        assert any("CREATE TRIGGER IF NOT EXISTS nodes_fts_insert" in sql for sql in sql_statements)
        assert any("CREATE TRIGGER IF NOT EXISTS nodes_fts_update" in sql for sql in sql_statements)
        assert any("CREATE TRIGGER IF NOT EXISTS nodes_fts_delete" in sql for sql in sql_statements)

    @pytest.mark.asyncio
    async def test_initialize_schema_syncs_in_replica_mode(self, mock_libsql, mock_networkx):
        """Test that schema initialization syncs in embedded replica mode."""
        backend = TursoBackend(
            db_path=":memory:",
            sync_url="libsql://test.turso.io",
            auth_token="test_token"
        )
        await backend.connect()

        mock_conn = backend.conn
        mock_conn.sync = Mock()

        await backend.initialize_schema()

        # Verify sync was called after schema creation
        assert mock_conn.sync.called

    @pytest.mark.asyncio
    async def test_initialize_schema_without_connection_raises(self, mock_libsql, mock_networkx):
        """Test that initialize_schema fails without connection."""
        backend = TursoBackend(db_path=":memory:")

        with pytest.raises(DatabaseConnectionError):
            await backend.initialize_schema()

    @pytest.mark.asyncio
    async def test_initialize_schema_error_raises_schema_error(self, mock_libsql, mock_networkx):
        """Test that schema initialization errors raise SchemaError."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value
        mock_cursor.execute.side_effect = Exception("SQL error")

        with pytest.raises(SchemaError) as exc_info:
            await backend.initialize_schema()

        assert "Schema initialization failed" in str(exc_info.value)


class TestTursoBackendQueryExecution:
    """Test query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_without_connection_raises(self, mock_libsql, mock_networkx):
        """Test that execute_query fails without connection."""
        backend = TursoBackend(db_path=":memory:")

        with pytest.raises(DatabaseConnectionError):
            await backend.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_read_operation(self, mock_libsql, mock_networkx):
        """Test executing a read query."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value
        mock_cursor.description = [("count",)]
        mock_cursor.fetchall.return_value = [(5,)]

        result = await backend.execute_query("SELECT COUNT(*) as count FROM nodes")

        assert len(result) == 1
        assert result[0]["count"] == 5

    @pytest.mark.asyncio
    async def test_execute_query_write_operation_commits(self, mock_libsql, mock_networkx):
        """Test that write operations commit."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        await backend.execute_query("INSERT INTO nodes VALUES (...)", write=True)

        backend.conn.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_write_operation_syncs_in_replica_mode(self, mock_libsql, mock_networkx):
        """Test that write operations sync in embedded replica mode."""
        backend = TursoBackend(
            db_path=":memory:",
            sync_url="libsql://test.turso.io",
            auth_token="test_token"
        )
        await backend.connect()

        mock_conn = backend.conn
        mock_conn.sync = Mock()

        await backend.execute_query("INSERT INTO nodes VALUES (...)", write=True)

        # Verify sync was called after commit
        assert mock_conn.sync.called

    @pytest.mark.asyncio
    async def test_execute_query_with_parameters(self, mock_libsql, mock_networkx):
        """Test executing query with parameters."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        # Reset mock after connect (which makes some queries)
        mock_cursor = backend.conn.cursor.return_value
        mock_cursor.reset_mock()

        await backend.execute_query(
            "SELECT * FROM nodes WHERE id = :id",
            parameters={"id": "test123"}
        )

        # Verify parameters were passed (check last call)
        call_args = mock_cursor.execute.call_args
        assert call_args[0][0] == "SELECT * FROM nodes WHERE id = :id"
        assert call_args[0][1] == {"id": "test123"}

    @pytest.mark.asyncio
    async def test_execute_query_error_raises(self, mock_libsql, mock_networkx):
        """Test query execution error handling."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value
        mock_cursor.execute.side_effect = Exception("SQL error")

        with pytest.raises(DatabaseConnectionError) as exc_info:
            await backend.execute_query("INVALID SQL")

        assert "Query failed" in str(exc_info.value)


class TestTursoBackendSync:
    """Test sync functionality."""

    @pytest.mark.asyncio
    async def test_sync_in_embedded_replica_mode(self, mock_libsql, mock_networkx):
        """Test manual sync in embedded replica mode."""
        backend = TursoBackend(
            db_path=":memory:",
            sync_url="libsql://test.turso.io",
            auth_token="test_token"
        )
        await backend.connect()

        mock_conn = backend.conn
        mock_conn.sync = Mock()

        await backend.sync()

        assert mock_conn.sync.called

    @pytest.mark.asyncio
    async def test_sync_in_local_mode_logs_warning(self, mock_libsql, mock_networkx, caplog):
        """Test that sync in local mode logs warning."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        await backend.sync()

        assert "Sync not available" in caplog.text

    @pytest.mark.asyncio
    async def test_sync_failure_raises_error(self, mock_libsql, mock_networkx):
        """Test sync failure handling."""
        backend = TursoBackend(
            db_path=":memory:",
            sync_url="libsql://test.turso.io",
            auth_token="test_token"
        )
        await backend.connect()

        mock_conn = backend.conn
        mock_conn.sync = Mock(side_effect=Exception("Sync failed"))

        with pytest.raises(DatabaseConnectionError) as exc_info:
            await backend.sync()

        assert "Sync failed" in str(exc_info.value)


class TestTursoBackendHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_when_connected(self, mock_libsql, mock_networkx):
        """Test health check when backend is connected."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value
        mock_cursor.fetchone.side_effect = [(10,), (5,)]

        health = await backend.health_check()

        assert health["backend"] == "turso"
        assert health["connected"] is True
        assert health["status"] == "healthy"
        assert health["node_count"] == 10
        assert health["relationship_count"] == 5
        assert health["mode"] == "local"

    @pytest.mark.asyncio
    async def test_health_check_embedded_replica_mode(self, mock_libsql, mock_networkx):
        """Test health check shows embedded replica mode."""
        backend = TursoBackend(
            db_path=":memory:",
            sync_url="libsql://test.turso.io",
            auth_token="test_token"
        )
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value
        mock_cursor.fetchone.return_value = (0,)

        health = await backend.health_check()

        assert health["mode"] == "embedded_replica"
        assert health["sync_enabled"] is True

    @pytest.mark.asyncio
    async def test_health_check_when_disconnected(self, mock_libsql, mock_networkx):
        """Test health check when backend is disconnected."""
        backend = TursoBackend(db_path=":memory:")

        health = await backend.health_check()

        assert health["connected"] is False
        assert health["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_health_check_error_handling(self, mock_libsql, mock_networkx):
        """Test health check error handling."""
        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_cursor = backend.conn.cursor.return_value
        mock_cursor.execute.side_effect = Exception("Query failed")

        health = await backend.health_check()

        assert health["status"] == "error"
        assert "error" in health


class TestTursoBackendInterface:
    """Test GraphBackend interface compliance."""

    def test_backend_name(self, mock_libsql, mock_networkx):
        """Test backend_name returns correct identifier."""
        backend = TursoBackend(db_path=":memory:")
        assert backend.backend_name() == "turso"

    def test_supports_fulltext_search(self, mock_libsql, mock_networkx):
        """Test full-text search support."""
        backend = TursoBackend(db_path=":memory:")
        assert backend.supports_fulltext_search() is True

    def test_supports_transactions(self, mock_libsql, mock_networkx):
        """Test transaction support."""
        backend = TursoBackend(db_path=":memory:")
        assert backend.supports_transactions() is True
