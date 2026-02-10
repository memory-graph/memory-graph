"""
Additional tests for FalkorDB backend to achieve high coverage.

These tests focus on error handling, edge cases, and conditional paths
that are not covered by the main test suite.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from memorygraph.backends.falkordb_backend import FalkorDBBackend
from memorygraph.models import DatabaseConnectionError
from memorygraph.config import Config


class TestFalkorDBQueryErrors:
    """Test query execution error handling."""

    @pytest.mark.asyncio
    async def test_execute_query_with_exception(self):
        """Test that execute_query handles exceptions properly."""
        backend = FalkorDBBackend(host="localhost", port=6379)

        # Mock client and graph
        mock_client = Mock()
        mock_graph = Mock()
        mock_graph.query.side_effect = Exception("Database error")
        mock_client.select_graph.return_value = mock_graph

        backend.client = mock_client
        backend.graph = mock_graph
        backend._connected = True

        # Should raise DatabaseConnectionError when query fails
        with pytest.raises(DatabaseConnectionError, match="Query execution failed"):
            await backend.execute_query("MATCH (n) RETURN n")


class TestFalkorDBSchemaErrorHandling:
    """Test schema initialization error handling."""

    @pytest.mark.asyncio
    async def test_initialize_schema_constraint_errors(self):
        """Test that schema initialization continues on constraint errors."""
        backend = FalkorDBBackend(host="localhost", port=6379)

        call_count = [0]

        async def mock_execute_query(query, parameters=None, write=False):
            call_count[0] += 1
            if "CONSTRAINT" in query:
                raise Exception("Constraint already exists")
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        await backend.initialize_schema()
        assert call_count[0] > 0

    @pytest.mark.asyncio
    async def test_initialize_schema_index_errors(self):
        """Test that schema initialization continues on index errors."""
        backend = FalkorDBBackend(host="localhost", port=6379)

        call_count = [0]

        async def mock_execute_query(query, parameters=None, write=False):
            call_count[0] += 1
            if "INDEX" in query and "CREATE INDEX" in query:
                raise Exception("Index already exists")
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        await backend.initialize_schema()
        assert call_count[0] > 0


class TestFalkorDBMultiTenantMode:
    """Test multi-tenant mode specific code paths."""

    @pytest.mark.asyncio
    async def test_initialize_schema_with_multitenant_mode(self):
        """Test schema initialization in multi-tenant mode."""
        backend = FalkorDBBackend(host="localhost", port=6379)

        queries_executed = []

        async def mock_execute_query(query, parameters=None, write=False):
            queries_executed.append(query)
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        with patch.object(Config, 'is_multi_tenant_mode', return_value=True):
            await backend.initialize_schema()

        # Check that multi-tenant indexes were created
        index_queries = [q for q in queries_executed if "CREATE INDEX" in q]
        tenant_indexes = [q for q in index_queries if any(
            field in q for field in ['context_tenant_id', 'context_team_id', 'context_visibility']
        )]

        assert len(tenant_indexes) >= 3, "Should create multi-tenant indexes"

    @pytest.mark.asyncio
    async def test_initialize_schema_without_multitenant_mode(self):
        """Test schema initialization without multi-tenant mode."""
        backend = FalkorDBBackend(host="localhost", port=6379)

        queries_executed = []

        async def mock_execute_query(query, parameters=None, write=False):
            queries_executed.append(query)
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        with patch.object(Config, 'is_multi_tenant_mode', return_value=False):
            await backend.initialize_schema()

        tenant_indexes = [q for q in queries_executed if 'context_tenant_id' in q]
        assert len(tenant_indexes) == 0, "Should not create multi-tenant indexes"


class TestFalkorDBConnectionEdgeCases:
    """Test edge cases in connection handling."""

    def test_backend_initialization_with_defaults(self):
        """Test backend initialization uses Config defaults directly."""
        backend = FalkorDBBackend()

        assert backend.host == Config.FALKORDB_HOST
        assert backend.port == Config.FALKORDB_PORT
        assert backend.password == Config.FALKORDB_PASSWORD

    def test_backend_initialization_with_config(self):
        """Test backend initialization with config values."""
        with patch.object(Config, 'FALKORDB_HOST', "custom-host"):
            with patch.object(Config, 'FALKORDB_PORT', 7000):
                with patch.object(Config, 'FALKORDB_PASSWORD', "secret"):
                    backend = FalkorDBBackend()

                    assert backend.host == "custom-host"
                    assert backend.port == 7000
                    assert backend.password == "secret"

    def test_backend_initialization_with_explicit_params(self):
        """Test backend initialization with explicit parameters."""
        backend = FalkorDBBackend(host="explicit-host", port=8000, password="explicit-pass")

        assert backend.host == "explicit-host"
        assert backend.port == 8000
        assert backend.password == "explicit-pass"


class TestFalkorDBContextManagerAndCleanup:
    """Test context manager and cleanup operations."""

    @pytest.mark.asyncio
    async def test_disconnect_with_client(self):
        """Test disconnect when client exists."""
        backend = FalkorDBBackend(host="localhost", port=6379)

        mock_client = Mock()
        backend.client = mock_client
        backend._connected = True

        await backend.disconnect()

        # Verify client was set to None
        assert backend.client is None
        assert backend.graph is None
        assert backend._connected is False

    @pytest.mark.asyncio
    async def test_disconnect_without_client(self):
        """Test disconnect when no client exists."""
        backend = FalkorDBBackend(host="localhost", port=6379)
        backend.client = None
        backend._connected = False

        await backend.disconnect()

        assert backend._connected is False
