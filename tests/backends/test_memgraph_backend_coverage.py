"""
Additional tests for Memgraph backend to improve test coverage to >70%.

This test file adds missing edge cases and code paths not covered by existing tests.
"""

import pytest
import os
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from neo4j.exceptions import Neo4jError

from src.memorygraph.backends.memgraph_backend import MemgraphBackend
from src.memorygraph.models import DatabaseConnectionError


class TestMemgraphBackendAdditionalCoverage:
    """Additional test cases for comprehensive coverage."""

    @pytest.mark.parametrize("user,password,expected_user,expected_pass", [
        ("testuser", "", "testuser", ""),  # User but no password
        ("", "testpass", "", "testpass"),  # Password but no user (edge case)
        ("", "", "", ""),  # Both empty
    ])
    def test_init_with_various_auth_combinations(self, user, password, expected_user, expected_pass):
        """Test initialization with various authentication combinations."""
        backend = MemgraphBackend(
            uri="bolt://test:7687",
            user=user,
            password=password
        )
        assert backend.user == expected_user
        assert backend.password == expected_pass

    @pytest.mark.asyncio
    async def test_connect_with_empty_auth_credentials(self):
        """Test connection when user and password are empty strings."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687", user="", password="")
            await backend.connect()

            # Should pass auth=None when both are empty
            call_kwargs = mock_db.driver.call_args[1]
            assert call_kwargs['auth'] is None

    @pytest.mark.asyncio
    async def test_connect_verify_connection_parameters(self):
        """Test that connect passes correct connection pool parameters."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Verify connection pool parameters
            call_kwargs = mock_db.driver.call_args[1]
            assert call_kwargs['max_connection_lifetime'] == 30 * 60
            assert call_kwargs['max_connection_pool_size'] == 50
            assert call_kwargs['connection_acquisition_timeout'] == 30.0

    @pytest.mark.asyncio
    async def test_execute_query_with_empty_parameters(self):
        """Test query execution with explicitly empty parameters dict."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()

            mock_result.data = AsyncMock(return_value=[{"result": "test"}])
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

            # Execute with empty dict
            result = await backend.execute_query("RETURN 1", parameters={})

            assert result == [{"result": "test"}]

    @pytest.mark.asyncio
    async def test_execute_query_write_parameter(self):
        """Test that write parameter is passed but doesn't affect execution in Memgraph."""
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

            # Execute with write=True
            result = await backend.execute_query("CREATE (n:Test)", write=True)

            # Memgraph uses execute_write for all operations
            mock_session.execute_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_context_manager_exception_handling(self):
        """Test that session context manager closes session even on exception."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Test that session closes even if exception occurs
            try:
                async with backend._session() as session:
                    raise ValueError("Test exception")
            except ValueError:
                pass

            # Session should still be closed
            mock_session.close.assert_called_once()

    def test_adapt_cypher_with_other_fulltext_patterns(self):
        """Test cypher adaptation with variations of fulltext index."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        # Test uppercase - the code checks for exact "CREATE FULLTEXT INDEX"
        query1 = "CREATE FULLTEXT INDEX test FOR (n:Node) ON EACH [n.text]"
        adapted1 = backend._adapt_cypher(query1)
        assert adapted1 == "RETURN 1"

        # Test with different spacing - will NOT match because code looks for exact string
        query2 = "CREATE  FULLTEXT  INDEX test"
        adapted2 = backend._adapt_cypher(query2)
        # This won't be adapted because it has double spaces
        assert adapted2 == query2

    def test_adapt_cypher_preserves_other_create_statements(self):
        """Test that non-fulltext CREATE statements are not modified."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        query = "CREATE INDEX ON :Memory(property)"
        adapted = backend._adapt_cypher(query)
        assert adapted == query

    def test_adapt_cypher_complex_query(self):
        """Test adaptation of complex multi-line query."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        query = """
        MATCH (m:Memory)
        WHERE m.id = $id
        RETURN m
        """
        adapted = backend._adapt_cypher(query)
        assert adapted == query

    @pytest.mark.asyncio
    async def test_initialize_schema_partial_failure(self):
        """Test schema initialization when some operations fail but continues."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = AsyncMock(return_value=[])
            mock_tx.run = AsyncMock(return_value=mock_result)

            # Fail on first call, succeed on others
            call_count = [0]

            async def execute_write_side_effect(fn, *args):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First constraint fails
                    raise DatabaseConnectionError("Constraint error")
                # Other operations succeed
                return await fn(mock_tx, *args)

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Should not raise, just log warnings
            await backend.initialize_schema()

            # Should have attempted multiple operations
            assert mock_session.execute_write.call_count > 1

    @pytest.mark.asyncio
    async def test_health_check_empty_result(self):
        """Test health check when query returns empty result."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()

            # Empty result
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
            health = await backend.health_check()

            # Should handle empty result gracefully
            assert health["connected"] is True
            assert health["backend_type"] == "memgraph"

    @pytest.mark.asyncio
    async def test_health_check_result_without_count(self):
        """Test health check when result doesn't have expected 'count' field."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_tx = AsyncMock()
            mock_result = AsyncMock()

            # Result with different field name
            mock_result.data = AsyncMock(return_value=[{"other_field": 42}])
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

            # Should default to 0 when count not found
            assert health["statistics"]["memory_count"] == 0

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="disconnect() doesn't reset _connected when driver is None - known issue")
    async def test_disconnect_when_driver_none(self):
        """Test disconnect handles None driver gracefully."""
        backend = MemgraphBackend(uri="bolt://test:7687")
        backend.driver = None
        backend._connected = True

        # Should not raise error (disconnect checks if driver exists)
        await backend.disconnect()

        # Driver is None, so close() won't be called, but connected flag isn't changed
        # The disconnect logic only sets _connected=False after closing the driver
        assert backend._connected is False  # Expected: should be False even when driver is None

    @pytest.mark.asyncio
    async def test_create_factory_with_all_params(self):
        """Test factory method with all parameters specified."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = await MemgraphBackend.create(
                uri="bolt://test:7687",
                user="admin",
                password="secret",
                database="production"
            )

            assert backend._connected is True
            assert backend.uri == "bolt://test:7687"
            assert backend.user == "admin"
            assert backend.password == "secret"
            assert backend.database == "production"

    @pytest.mark.asyncio
    async def test_run_query_async_empty_parameters(self):
        """Test _run_query_async with empty parameters."""
        mock_tx = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=[{"test": "value"}])
        mock_tx.run = AsyncMock(return_value=mock_result)

        result = await MemgraphBackend._run_query_async(
            mock_tx,
            "RETURN 1",
            {}
        )

        assert result == [{"test": "value"}]
        mock_tx.run.assert_called_once_with("RETURN 1", {})

    def test_backend_capabilities_methods(self):
        """Test backend capability check methods."""
        backend = MemgraphBackend(uri="bolt://test:7687")

        # Test all capability methods
        assert backend.backend_name() == "memgraph"
        assert backend.supports_fulltext_search() is False
        assert backend.supports_transactions() is True

    @pytest.mark.asyncio
    async def test_execute_query_with_cypher_adaptation(self):
        """Test that execute_query adapts Cypher before execution."""
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

            # Execute query with fulltext - should be adapted
            await backend.execute_query("CREATE FULLTEXT INDEX test FOR (n:Node) ON EACH [n.text]")

            # Should have executed adapted query (RETURN 1)
            mock_tx.run.assert_called_once()
            call_args = mock_tx.run.call_args[0]
            assert "RETURN 1" in call_args[0]

    @pytest.mark.asyncio
    async def test_initialize_schema_index_already_exists(self):
        """Test schema initialization when index already exists."""
        with patch('src.memorygraph.backends.memgraph_backend.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()

            async def execute_write_side_effect(fn, *args):
                # Simulate "already exists" error
                raise DatabaseConnectionError("Index already exists")

            mock_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
            mock_session.close = AsyncMock()
            mock_driver.session = Mock(return_value=mock_session)
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            backend = MemgraphBackend(uri="bolt://test:7687")
            await backend.connect()

            # Should not raise - should handle "already exists" gracefully
            await backend.initialize_schema()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
