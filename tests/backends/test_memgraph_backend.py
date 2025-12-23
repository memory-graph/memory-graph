"""
Tests for Memgraph backend implementation.

These tests verify that the Memgraph backend correctly implements the GraphBackend
interface and provides the expected functionality for Cypher-based graph operations.
"""

import importlib.util
import pytest
import os
from unittest.mock import AsyncMock, Mock, patch, MagicMock

# Check if neo4j is available before importing backends
neo4j_available = importlib.util.find_spec("neo4j") is not None

if neo4j_available:
    from src.memorygraph.backends.memgraph_backend import MemgraphBackend
else:
    MemgraphBackend = None

from src.memorygraph.models import DatabaseConnectionError, SchemaError

# Skip entire module if neo4j not available
pytestmark = pytest.mark.skipif(
    not neo4j_available,
    reason="neo4j package not installed"
)

neo4j_skip = pytest.mark.skipif(
    not neo4j_available,
    reason="neo4j package not installed"
)


class TestMemgraphBackendInitialization:
    """Test Memgraph backend initialization and configuration."""

    def test_init_with_explicit_params(self):
        """Test initialization with explicit parameters."""
        backend = MemgraphBackend(
            uri="bolt://test:7687",
            user="testuser",
            password="testpass",
            database="testdb"
        )

        assert backend.uri == "bolt://test:7687"
        assert backend.user == "testuser"
        assert backend.password == "testpass"
        assert backend.database == "testdb"
        assert backend._connected is False
        assert backend.driver is None

    def test_init_from_env_vars(self):
        """Test initialization from environment variables."""
        with patch.dict(os.environ, {
            "MEMORY_MEMGRAPH_URI": "bolt://env:7687",
            "MEMORY_MEMGRAPH_USER": "envuser",
            "MEMORY_MEMGRAPH_PASSWORD": "envpass"
        }):
            backend = MemgraphBackend()

            assert backend.uri == "bolt://env:7687"
            assert backend.user == "envuser"
            assert backend.password == "envpass"

    def test_init_defaults(self):
        """Test initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            backend = MemgraphBackend()

            assert backend.uri == "bolt://localhost:7687"
            assert backend.user == ""
            assert backend.password == ""
            assert backend.database == "memgraph"

    def test_init_empty_auth(self):
        """Test initialization with empty authentication (Community Edition)."""
        backend = MemgraphBackend(uri="bolt://test:7687", user="", password="")

        assert backend.user == ""
        assert backend.password == ""

    def test_backend_name(self):
        """Test backend_name method returns correct value."""
        backend = MemgraphBackend(uri="bolt://test:7687")
        assert backend.backend_name() == "memgraph"

    def test_supports_fulltext_search(self):
        """Test that Memgraph backend reports limited fulltext search support."""
        backend = MemgraphBackend(uri="bolt://test:7687")
        assert backend.supports_fulltext_search() is False

    def test_supports_transactions(self):
        """Test that Memgraph backend reports transaction support."""
        backend = MemgraphBackend(uri="bolt://test:7687")
        assert backend.supports_transactions() is True


class TestMemgraphBackendConnection:
    """Test Memgraph backend connection management."""

    @pytest.mark.asyncio
    async def test_connect_success_with_auth(self):
        """Test successful connection to Memgraph with authentication."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(
                uri="bolt://test:7687",
                user="testuser",
                password="testpass"
            )
            result = await backend.connect()

            assert result is True
            assert backend._connected is True
            assert backend.driver is not None
            mock_driver.verify_connectivity.assert_called_once()

            # Verify auth was passed
            mock_db.driver.assert_called_once()
            call_kwargs = mock_db.driver.call_args[1]
            assert call_kwargs['auth'] == ("testuser", "testpass")

    @pytest.mark.asyncio
    async def test_connect_success_without_auth(self):
        """Test successful connection to Memgraph without authentication."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687", user="", password="")
            result = await backend.connect()

            assert result is True
            assert backend._connected is True

            # Verify no auth was passed (None)
            call_kwargs = mock_db.driver.call_args[1]
            assert call_kwargs['auth'] is None

    @neo4j_skip
    @pytest.mark.asyncio
    async def test_connect_service_unavailable(self):
        """Test connection failure when service is unavailable."""
        from neo4j.exceptions import ServiceUnavailable

        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_db.driver.side_effect = ServiceUnavailable("Service unavailable")

            backend = MemgraphBackend(uri="bolt://test:7687")

            with pytest.raises(DatabaseConnectionError, match="Unexpected error connecting to Memgraph"):
                await backend.connect()

            assert backend._connected is False

    @neo4j_skip
    @pytest.mark.asyncio
    async def test_connect_auth_error(self):
        """Test connection failure with authentication error."""
        from neo4j.exceptions import AuthError

        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_db.driver.side_effect = AuthError("Authentication failed")

            backend = MemgraphBackend(uri="bolt://test:7687", user="test", password="wrong")

            with pytest.raises(DatabaseConnectionError, match="Unexpected error connecting to Memgraph"):
                await backend.connect()

    @pytest.mark.asyncio
    async def test_connect_unexpected_error(self):
        """Test connection failure with unexpected error."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_db.driver.side_effect = Exception("Unexpected error")

            backend = MemgraphBackend(uri="bolt://test:7687")

            with pytest.raises(DatabaseConnectionError, match="Unexpected error connecting to Memgraph"):
                await backend.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Memgraph."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_driver.close = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()
            await backend.disconnect()

            assert backend._connected is False
            assert backend.driver is None
            mock_driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnect when already disconnected."""
        backend = MemgraphBackend(uri="bolt://test:7687")
        # Should not raise error
        await backend.disconnect()
        assert backend._connected is False


class TestMemgraphBackendQueryExecution:
    """Test Memgraph query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful query execution."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            # Setup mock driver and session
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()

            mock_result.data = AsyncMock(return_value=[{"count": 10}])
            mock_tx.run = AsyncMock(return_value=mock_result)

            # Need to properly await the coroutine
            async def execute_write_side_effect(fn, *args):
                return await fn(mock_tx, *args)

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Execute query
            result = await backend.execute_query("MATCH (n) RETURN count(n) as count")

            assert result == [{"count": 10}]
            mock_tx.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_with_parameters(self):
        """Test query execution with parameters."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()

            mock_result.data = AsyncMock(return_value=[{"name": "test"}])
            mock_tx.run = AsyncMock(return_value=mock_result)

            async def execute_write_side_effect(fn, *args):
                return await fn(mock_tx, *args)

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Execute query with parameters
            result = await backend.execute_query(
                "MATCH (n:Memory {id: $id}) RETURN n.name as name",
                parameters={"id": "123"}
            )

            assert result == [{"name": "test"}]

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self):
        """Test query execution when not connected."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        with pytest.raises(DatabaseConnectionError, match="Not connected to Memgraph"):
            await backend.execute_query("MATCH (n) RETURN n")

    @pytest.mark.asyncio
    async def test_execute_query_driver_none(self):
        """Test query execution when driver is None."""
        backend = MemgraphBackend(uri="bolt://test:7687")
        backend._connected = True  # Simulate inconsistent state
        backend.driver = None

        with pytest.raises(DatabaseConnectionError, match="Not connected to Memgraph"):
            await backend.execute_query("MATCH (n) RETURN n")

    @neo4j_skip
    @pytest.mark.asyncio
    async def test_execute_query_neo4j_error(self):
        """Test query execution with Neo4j error."""
        from neo4j.exceptions import Neo4jError

        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_session.execute_write = AsyncMock(side_effect=Neo4jError("Query error"))
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            with pytest.raises(DatabaseConnectionError, match="Query execution failed"):
                await backend.execute_query("INVALID QUERY")


class TestMemgraphCypherAdaptation:
    """Test Cypher query adaptation for Memgraph."""

    def test_adapt_cypher_fulltext_index(self):
        """Test that fulltext index creation is skipped."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        query = "CREATE FULLTEXT INDEX memory_fulltext FOR (m:Memory) ON EACH [m.content, m.title]"
        adapted = backend._adapt_cypher(query)

        # Should be replaced with no-op
        assert adapted == "RETURN 1"

    def test_adapt_cypher_regular_query(self):
        """Test that regular queries are not modified."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        query = "MATCH (n:Memory) RETURN n"
        adapted = backend._adapt_cypher(query)

        assert adapted == query

    def test_adapt_cypher_constraint(self):
        """Test that constraint queries are passed through."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        query = "CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE"
        adapted = backend._adapt_cypher(query)

        assert adapted == query


class TestMemgraphSchemaInitialization:
    """Test Memgraph schema initialization."""

    @pytest.mark.asyncio
    async def test_initialize_schema_success(self):
        """Test successful schema initialization."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()

            mock_result.data = AsyncMock(return_value=[])
            mock_tx.run = AsyncMock(return_value=mock_result)

            async def execute_write_side_effect(fn, *args):
                return await fn(mock_tx, *args)

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()
            await backend.initialize_schema()

            # Should have called execute_write multiple times (constraints + indexes)
            assert mock_session.execute_write.call_count > 0

    @neo4j_skip
    @pytest.mark.asyncio
    async def test_initialize_schema_constraint_exists(self):
        """Test schema initialization when constraints already exist."""
        from neo4j.exceptions import Neo4jError

        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()

            # First call (constraint) raises "already exists", rest succeed
            call_count = [0]
            async def execute_write_side_effect(fn, *args):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Neo4jError("Constraint already exists")
                # Create a mock tx for successful calls
                mock_tx = AsyncMock()
                mock_result = AsyncMock()
                mock_result.data = AsyncMock(return_value=[])
                mock_tx.run = AsyncMock(return_value=mock_result)
                return await fn(mock_tx, *args)

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Should not raise error despite constraint existing
            await backend.initialize_schema()

    @neo4j_skip
    @pytest.mark.asyncio
    async def test_initialize_schema_not_supported(self):
        """Test schema initialization with unsupported features."""
        from neo4j.exceptions import Neo4jError

        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()

            def execute_write_side_effect(fn, *args):
                raise Neo4jError("Feature not supported")

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Should not raise error, just log warnings
            await backend.initialize_schema()


class TestMemgraphHealthCheck:
    """Test Memgraph health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_not_connected(self):
        """Test health check when not connected."""
        backend = MemgraphBackend(uri="bolt://test:7687", database="testdb")
        health = await backend.health_check()

        assert health["connected"] is False
        assert health["backend_type"] == "memgraph"
        assert health["uri"] == "bolt://test:7687"
        assert health["database"] == "testdb"
        assert "statistics" not in health

    @pytest.mark.asyncio
    async def test_health_check_connected(self):
        """Test health check when connected."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()

            mock_result.data = AsyncMock(return_value=[{"count": 42}])
            mock_tx.run = AsyncMock(return_value=mock_result)

            async def execute_write_side_effect(fn, *args):
                return await fn(mock_tx, *args)

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()
            health = await backend.health_check()

            assert health["connected"] is True
            assert health["backend_type"] == "memgraph"
            assert health["statistics"]["memory_count"] == 42
            assert health["version"] == "unknown"

    @pytest.mark.asyncio
    async def test_health_check_query_error(self):
        """Test health check when query fails."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_session.execute_write = AsyncMock(side_effect=Exception("Query failed"))
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()
            health = await backend.health_check()

            assert health["connected"] is True
            assert "warning" in health
            assert "Query failed" in health["warning"]


class TestMemgraphBackendFactory:
    """Test Memgraph backend factory method."""

    @pytest.mark.asyncio
    async def test_create_success(self):
        """Test factory method creates and connects backend."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = await MemgraphBackend.create(
                uri="bolt://test:7687",
                user="testuser",
                password="testpass",
                database="testdb"
            )

            assert isinstance(backend, MemgraphBackend)
            assert backend._connected is True
            assert backend.uri == "bolt://test:7687"
            assert backend.user == "testuser"
            assert backend.database == "testdb"

    @neo4j_skip
    @pytest.mark.asyncio
    async def test_create_connection_failure(self):
        """Test factory method with connection failure."""
        from neo4j.exceptions import ServiceUnavailable

        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_db.driver.side_effect = ServiceUnavailable("Service unavailable")

            with pytest.raises(DatabaseConnectionError):
                await MemgraphBackend.create(uri="bolt://test:7687")


class TestMemgraphSessionManagement:
    """Test Memgraph session context manager."""

    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Test session context manager properly opens and closes session."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            async with backend._session() as session:
                assert session is mock_session

            # Verify session was closed
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_not_connected(self):
        """Test session context manager when not connected."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        with pytest.raises(DatabaseConnectionError, match="Not connected to Memgraph"):
            async with backend._session():
                pass


class TestMemgraphRunQueryAsync:
    """Test async query execution helper."""

    @pytest.mark.asyncio
    async def test_run_query_async(self):
        """Test _run_query_async helper method."""
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=[{"key": "value"}])
        mock_tx.run = AsyncMock(return_value=mock_result)

        result = await MemgraphBackend._run_query_async(
            mock_tx,
            "MATCH (n) RETURN n",
            {"param": "value"}
        )

        assert result == [{"key": "value"}]
        mock_tx.run.assert_called_once_with("MATCH (n) RETURN n", {"param": "value"})
