"""
Unit tests for LadybugDB backend implementation.

These tests use mocked real_ladybug client to verify backend logic without
requiring a running LadybugDB instance.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
import uuid
import sys

# Check if real_ladybug is available
try:
    import real_ladybug
    LADYBUGDB_AVAILABLE = True
except ImportError:
    LADYBUGDB_AVAILABLE = False

# Skip all tests in this module if real_ladybug is not installed
pytestmark = pytest.mark.skipif(
    not LADYBUGDB_AVAILABLE,
    reason="real_ladybug package not installed"
)

if LADYBUGDB_AVAILABLE:
    from memorygraph.backends.ladybugdb_backend import LadybugDBBackend

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


def setup_mock_ladybug(result_set=None):
    """
    Helper to set up mock LadybugDB client with proper result handling.

    Args:
        result_set: The result set to return from queries

    Returns:
        Tuple of (mock_client, mock_connection, mock_Database_class)
    """
    mock_client = Mock()
    mock_connection = Mock()
    mock_result = Mock()

    # Set up the result to behave like LadybugDB QueryResult
    if result_set:
        mock_result.has_next.side_effect = [True] * len(result_set) + [False]
        mock_result.get_next.side_effect = result_set
    else:
        mock_result.has_next.return_value = False

    mock_connection.execute.return_value = mock_result

    mock_Database_class = Mock(return_value=mock_client)
    mock_Connection_class = Mock(return_value=mock_connection)

    return (
        mock_client,
        mock_connection,
        mock_Database_class,
        mock_Database_class,
        mock_Connection_class,
    )


class TestLadybugDBConnection:
    """Test LadybugDB connection management."""

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_connect_success(self, mock_lb):
        """Test successful connection to LadybugDB."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        result = await backend.connect()

        assert result is True
        assert backend._connected is True
        # Verify connection was created with file path
        mock_Database_class.assert_called_once_with("/tmp/test.db")
        # Verify Connection was created with the database
        mock_Connection_class.assert_called_once_with(mock_client)

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_connect_failure(self, mock_lb):
        """Test connection failure handling."""
        mock_Database = Mock(side_effect=Exception("Database file not accessible"))
        mock_lb.Database = mock_Database

        backend = LadybugDBBackend(db_path="/invalid/path/test.db")

        with pytest.raises(
            DatabaseConnectionError, match="Database file not accessible"
        ):
            await backend.connect()

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_disconnect(self, mock_lb):
        """Test disconnection from LadybugDB."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()
        await backend.disconnect()

        assert backend._connected is False
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_default_path(self, mock_lb):
        """Test default database path is used when none specified."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend()
        await backend.connect()

        # Should use default path
        mock_Database_class.assert_called_once()
        call_args = mock_Database_class.call_args[0]
        assert call_args[0].endswith(".memorygraph/memory.lbdb")

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_custom_graph_name(self, mock_lb):
        """Test custom graph name is stored (though not currently used in connection)."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db", graph_name="custom_graph")
        await backend.connect()

        assert backend.graph_name == "custom_graph"
        # Connection is still made normally
        mock_Database_class.assert_called_once_with("/tmp/test.db")
        mock_Connection_class.assert_called_once_with(mock_client)


class TestLadybugDBQueryExecution:
    """Test LadybugDB query execution."""

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_success(self, mock_lb):
        """Test successful query execution."""
        mock_result_data = [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        result = await backend.execute_query("MATCH (n) RETURN n", write=False)

        assert result == mock_result_data
        mock_connection.execute.assert_called_once_with("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_with_parameters(self, mock_lb):
        """Test query execution with parameters (note: LadybugDB doesn't support parameterized queries)."""
        mock_result_data = [{"count": 5}]
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        # LadybugDB doesn't support parameters, so they are ignored
        params = {"name": "test_node"}
        result = await backend.execute_query(
            "MATCH (n {name: 'test_node'}) RETURN count(n) as count",
            params,
            write=False,
        )

        assert result == mock_result_data
        mock_connection.execute.assert_called_once_with(
            "MATCH (n {name: 'test_node'}) RETURN count(n) as count"
        )

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_write_operation(self, mock_lb):
        """Test write query execution."""
        mock_result_data = []
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug(mock_result_data)

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        result = await backend.execute_query(
            "CREATE (n:Node {name: 'test'})", write=True
        )

        assert result == mock_result_data
        mock_connection.execute.assert_called_once_with(
            "CREATE (n:Node {name: 'test'})"
        )

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected."""
        backend = LadybugDBBackend(db_path="/tmp/test.db")

        with pytest.raises(DatabaseConnectionError, match="Not connected to LadybugDB"):
            await backend.execute_query("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_execute_query_error(self, mock_lb):
        """Test query execution error handling."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        mock_connection.execute.side_effect = Exception("Query syntax error")

        backend = LadybugDBBackend(db_path="/tmp/test.db")
        await backend.connect()

        with pytest.raises(
            SchemaError, match="Query execution failed: Query syntax error"
        ):
            await backend.execute_query("INVALID QUERY")


class TestLadybugDBBackendInitialization:
    """Test LadybugDB backend initialization."""

    def test_init_with_path(self):
        """Test initialization with custom path."""
        backend = LadybugDBBackend(
            db_path="/custom/path/db.db", graph_name="test_graph"
        )

        assert backend.db_path == "/custom/path/db.db"
        assert backend.graph_name == "test_graph"
        assert backend._connected is False
        assert backend.client is None
        assert backend.graph is None

    def test_init_defaults(self):
        """Test initialization with defaults."""
        backend = LadybugDBBackend()

        assert backend.graph_name == "memorygraph"
        assert backend._connected is False
        assert backend.client is None
        assert backend.graph is None
        # db_path will be set to default in connect()

    @pytest.mark.asyncio
    @patch("memorygraph.backends.ladybugdb_backend.lb")
    async def test_connect_sets_default_path(self, mock_lb):
        """Test that connect sets default path when none provided."""
        (
            mock_client,
            mock_connection,
            mock_Database,
            mock_Database_class,
            mock_Connection_class,
        ) = setup_mock_ladybug()

        mock_lb.Database = mock_Database_class
        mock_lb.Connection = mock_Connection_class

        backend = LadybugDBBackend()
        await backend.connect()

        # Should have set a default path
        assert backend.db_path is not None
        assert ".memorygraph/memory.lbdb" in backend.db_path
