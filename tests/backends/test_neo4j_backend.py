"""
Tests for Neo4j backend implementation.

These tests verify that the Neo4j backend correctly implements the GraphBackend
interface and maintains compatibility with the existing Neo4j functionality.
"""

import pytest
import os
from unittest.mock import AsyncMock, Mock, patch

from src.memorygraph.backends.neo4j_backend import Neo4jBackend
from src.memorygraph.models import DatabaseConnectionError, SchemaError


class TestNeo4jBackendInitialization:
    """Test Neo4j backend initialization and configuration."""

    def test_init_with_explicit_params(self):
        """Test initialization with explicit parameters."""
        backend = Neo4jBackend(
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

    def test_init_from_env_vars(self):
        """Test initialization from environment variables."""
        with patch.dict(os.environ, {
            "MEMORY_NEO4J_URI": "bolt://env:7687",
            "MEMORY_NEO4J_USER": "envuser",
            "MEMORY_NEO4J_PASSWORD": "envpass"
        }):
            backend = Neo4jBackend()

            assert backend.uri == "bolt://env:7687"
            assert backend.user == "envuser"
            assert backend.password == "envpass"

    def test_init_fallback_to_neo4j_env_vars(self):
        """Test fallback to NEO4J_* environment variables."""
        with patch.dict(os.environ, {
            "NEO4J_URI": "bolt://fallback:7687",
            "NEO4J_USER": "fallbackuser",
            "NEO4J_PASSWORD": "fallbackpass"
        }, clear=True):
            backend = Neo4jBackend()

            assert backend.uri == "bolt://fallback:7687"
            assert backend.user == "fallbackuser"
            assert backend.password == "fallbackpass"

    def test_init_missing_password_raises_error(self):
        """Test that missing password raises DatabaseConnectionError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DatabaseConnectionError, match="password must be provided"):
                Neo4jBackend(uri="bolt://test:7687", user="test")

    def test_backend_name(self):
        """Test backend_name method returns correct value."""
        backend = Neo4jBackend(
            uri="bolt://test:7687",
            password="test"
        )
        assert backend.backend_name() == "neo4j"

    def test_supports_fulltext_search(self):
        """Test that Neo4j backend reports fulltext search support."""
        backend = Neo4jBackend(
            uri="bolt://test:7687",
            password="test"
        )
        assert backend.supports_fulltext_search() is True

    def test_supports_transactions(self):
        """Test that Neo4j backend reports transaction support."""
        backend = Neo4jBackend(
            uri="bolt://test:7687",
            password="test"
        )
        assert backend.supports_transactions() is True


class TestNeo4jBackendConnection:
    """Test Neo4j backend connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to Neo4j."""
        with patch('src.memorygraph.backends.neo4j_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = Neo4jBackend(uri="bolt://test:7687", password="test")
            result = await backend.connect()

            assert result is True
            assert backend._connected is True
            assert backend.driver is not None
            mock_driver.verify_connectivity.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_service_unavailable(self):
        """Test connection failure when service is unavailable."""
        from neo4j.exceptions import ServiceUnavailable

        with patch('src.memorygraph.backends.neo4j_backend.AsyncGraphDatabase') as mock_db:
            mock_db.driver.side_effect = ServiceUnavailable("Service unavailable")

            backend = Neo4jBackend(uri="bolt://test:7687", password="test")

            with pytest.raises(DatabaseConnectionError, match="Failed to connect to Neo4j"):
                await backend.connect()

            assert backend._connected is False

    @pytest.mark.asyncio
    async def test_connect_auth_error(self):
        """Test connection failure with authentication error."""
        from neo4j.exceptions import AuthError

        with patch('src.memorygraph.backends.neo4j_backend.AsyncGraphDatabase') as mock_db:
            mock_db.driver.side_effect = AuthError("Authentication failed")

            backend = Neo4jBackend(uri="bolt://test:7687", password="test")

            with pytest.raises(DatabaseConnectionError, match="Authentication failed"):
                await backend.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Neo4j."""
        with patch('src.memorygraph.backends.neo4j_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_driver.close = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = Neo4jBackend(uri="bolt://test:7687", password="test")
            await backend.connect()
            await backend.disconnect()

            assert backend._connected is False
            assert backend.driver is None
            mock_driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using backend as async context manager."""
        with patch('src.memorygraph.backends.neo4j_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_driver.close = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = Neo4jBackend(uri="bolt://test:7687", password="test")

            async with backend as ctx_backend:
                assert ctx_backend._connected is True
                assert ctx_backend is backend

            assert backend._connected is False
            mock_driver.close.assert_called_once()


class TestNeo4jBackendQueries:
    """Test Neo4j backend query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_not_connected_raises_error(self):
        """Test that executing query without connection raises error."""
        backend = Neo4jBackend(uri="bolt://test:7687", password="test")

        with pytest.raises(DatabaseConnectionError, match="Not connected"):
            await backend.execute_query("RETURN 1")

    @pytest.mark.asyncio
    async def test_execute_query_read(self):
        """Test executing a read query."""
        backend = Neo4jBackend(uri="bolt://test:7687", password="test")
        backend._connected = True
        backend.driver = AsyncMock()  # Need to set driver

        # Just mock execute_query directly as it's the public API
        with patch.object(backend, '_session') as mock_session_ctx:
            mock_session = AsyncMock()
            expected_result = [{"result": 1}]
            mock_session.execute_read = AsyncMock(return_value=expected_result)
            mock_session_ctx.return_value.__aenter__.return_value = mock_session
            mock_session_ctx.return_value.__aexit__.return_value = AsyncMock()

            result = await backend.execute_query("RETURN 1", write=False)

            assert result == expected_result
            mock_session.execute_read.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_write(self):
        """Test executing a write query."""
        backend = Neo4jBackend(uri="bolt://test:7687", password="test")
        backend._connected = True
        backend.driver = AsyncMock()  # Need to set driver

        # Just mock execute_query directly as it's the public API
        with patch.object(backend, '_session') as mock_session_ctx:
            mock_session = AsyncMock()
            expected_result = [{"created": 1}]
            mock_session.execute_write = AsyncMock(return_value=expected_result)
            mock_session_ctx.return_value.__aenter__.return_value = mock_session
            mock_session_ctx.return_value.__aexit__.return_value = AsyncMock()

            result = await backend.execute_query("CREATE (n) RETURN n", write=True)

            assert result == expected_result
            mock_session.execute_write.assert_called_once()


class TestNeo4jBackendSchema:
    """Test Neo4j backend schema initialization."""

    @pytest.mark.asyncio
    async def test_initialize_schema(self):
        """Test schema initialization creates indexes and constraints."""
        backend = Neo4jBackend(uri="bolt://test:7687", password="test")
        backend._connected = True
        backend.driver = AsyncMock()

        query_count = 0

        async def count_queries(query, parameters=None, write=False):
            nonlocal query_count
            query_count += 1
            return []

        # Mock the execute_query method
        with patch.object(backend, 'execute_query', side_effect=count_queries):
            await backend.initialize_schema()

            # Should execute multiple constraint and index creation queries
            assert query_count > 0

    @pytest.mark.asyncio
    async def test_health_check_connected(self):
        """Test health check when connected."""
        with patch('src.memorygraph.backends.neo4j_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = Neo4jBackend(uri="bolt://test:7687", password="test")
            await backend.connect()

            with patch.object(backend, 'execute_query', new=AsyncMock(
                side_effect=[
                    [{"version": "5.0.0", "edition": "community"}],
                    [{"count": 42}]
                ]
            )):
                health = await backend.health_check()

                assert health["connected"] is True
                assert health["backend_type"] == "neo4j"
                assert health["uri"] == "bolt://test:7687"
                assert "version" in health
                assert "statistics" in health

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        """Test health check when disconnected."""
        backend = Neo4jBackend(uri="bolt://test:7687", password="test")

        health = await backend.health_check()

        assert health["connected"] is False
        assert health["backend_type"] == "neo4j"

    @pytest.mark.asyncio
    async def test_factory_create_method(self):
        """Test the factory create method."""
        with patch('src.memorygraph.backends.neo4j_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = await Neo4jBackend.create(
                uri="bolt://test:7687",
                password="test"
            )

            assert backend._connected is True
            assert isinstance(backend, Neo4jBackend)
