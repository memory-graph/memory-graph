"""
Additional tests for FalkorDBLite backend to achieve high coverage.

These tests focus on error handling, edge cases, and conditional paths
that are not covered by the main test suite.

Note: This file does NOT mock sys.modules to avoid interfering with other tests.
It only tests non-connection-dependent functionality.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone

# Import without mocking - the backend can be tested without connecting
from memorygraph.backends.falkordblite_backend import FalkorDBLiteBackend
from memorygraph.models import (
    Memory,
    MemoryType,
    DatabaseConnectionError,
    SchemaError,
)
from memorygraph.config import Config


# Note: Import error testing is complex due to module loading and mocking.
# The import error path (lines 79-80) is tested implicitly when the package
# is not installed, which is the real-world scenario we care about.


class TestFalkorDBLiteQueryErrors:
    """Test query execution error handling."""

    @pytest.mark.asyncio
    async def test_execute_query_with_exception(self):
        """Test that execute_query handles exceptions properly (lines 144-146)."""
        backend = FalkorDBLiteBackend(db_path="/tmp/test.db")

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


class TestFalkorDBLiteSchemaErrorHandling:
    """Test schema initialization error handling."""

    @pytest.mark.asyncio
    async def test_initialize_schema_constraint_errors(self):
        """Test that schema initialization continues on constraint errors (line 187, 189)."""
        backend = FalkorDBLiteBackend(db_path="/tmp/test.db")

        # Mock the execute_query to fail for constraints
        call_count = [0]

        async def mock_execute_query(query, parameters=None, write=False):
            call_count[0] += 1
            if "CONSTRAINT" in query:
                # Simulate constraint creation failure
                raise Exception("Constraint already exists")
            # Let indexes succeed
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        # Should not raise, just log the error
        await backend.initialize_schema()

        # Verify queries were attempted
        assert call_count[0] > 0

    @pytest.mark.asyncio
    async def test_initialize_schema_index_errors(self):
        """Test that schema initialization continues on index errors (lines 195, 197)."""
        backend = FalkorDBLiteBackend(db_path="/tmp/test.db")

        # Mock the execute_query to fail for indexes
        call_count = [0]

        async def mock_execute_query(query, parameters=None, write=False):
            call_count[0] += 1
            if "INDEX" in query and "CREATE INDEX" in query:
                # Simulate index creation failure
                raise Exception("Index already exists")
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        # Should not raise, just log the error
        await backend.initialize_schema()

        # Verify queries were attempted
        assert call_count[0] > 0


class TestFalkorDBLiteMultiTenantMode:
    """Test multi-tenant mode specific code paths."""

    @pytest.mark.asyncio
    async def test_initialize_schema_with_multitenant_mode(self):
        """Test schema initialization in multi-tenant mode (lines 172, 179-180)."""
        backend = FalkorDBLiteBackend(db_path="/tmp/test.db")

        queries_executed = []

        async def mock_execute_query(query, parameters=None, write=False):
            queries_executed.append(query)
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        # Enable multi-tenant mode
        with patch.object(Config, 'is_multi_tenant_mode', return_value=True):
            await backend.initialize_schema()

        # Check that multi-tenant indexes were created
        index_queries = [q for q in queries_executed if "CREATE INDEX" in q]

        # Should have tenant-specific indexes
        tenant_indexes = [q for q in index_queries if any(
            field in q for field in ['context_tenant_id', 'context_team_id', 'context_visibility', 'context_created_by', 'version']
        )]

        assert len(tenant_indexes) >= 5, "Should create multi-tenant indexes"

    @pytest.mark.asyncio
    async def test_initialize_schema_without_multitenant_mode(self):
        """Test schema initialization without multi-tenant mode."""
        backend = FalkorDBLiteBackend(db_path="/tmp/test.db")

        queries_executed = []

        async def mock_execute_query(query, parameters=None, write=False):
            queries_executed.append(query)
            return []

        backend.execute_query = mock_execute_query
        backend._connected = True

        # Disable multi-tenant mode
        with patch.object(Config, 'is_multi_tenant_mode', return_value=False):
            await backend.initialize_schema()

        # Check that NO multi-tenant indexes were created
        tenant_indexes = [q for q in queries_executed if any(
            field in q for field in ['context_tenant_id', 'context_team_id']
        )]

        assert len(tenant_indexes) == 0, "Should not create multi-tenant indexes"


class TestFalkorDBLiteConnectionEdgeCases:
    """Test edge cases in connection handling."""

    # Connection exception testing removed - it's covered by integration tests
    # and requires complex import mocking

    def test_backend_initialization_with_default_path(self):
        """Test backend initialization uses Config default path."""
        backend = FalkorDBLiteBackend()

        # Config.FALKORDBLITE_PATH provides the default
        assert backend.db_path == Config.FALKORDBLITE_PATH
        assert '.memorygraph' in backend.db_path
        assert 'falkordblite.db' in backend.db_path

    def test_backend_initialization_with_config_path(self):
        """Test backend initialization with config path."""
        test_path = "/custom/path/db.rdb"
        with patch.object(Config, 'FALKORDBLITE_PATH', test_path):
            backend = FalkorDBLiteBackend()

            assert backend.db_path == test_path

    def test_backend_initialization_with_explicit_path(self):
        """Test backend initialization with explicit path parameter."""
        test_path = "/explicit/path/db.rdb"
        backend = FalkorDBLiteBackend(db_path=test_path)

        assert backend.db_path == test_path


class TestFalkorDBLiteContextManagerAndCleanup:
    """Test context manager and cleanup operations."""

    @pytest.mark.asyncio
    async def test_disconnect_with_client(self):
        """Test disconnect when client exists."""
        backend = FalkorDBLiteBackend(db_path="/tmp/test.db")

        mock_client = Mock()
        backend.client = mock_client
        backend._connected = True

        await backend.disconnect()

        # Verify client was set to None and _connected is False
        assert backend.client is None
        assert backend.graph is None
        assert backend._connected is False

    @pytest.mark.asyncio
    async def test_disconnect_without_client(self):
        """Test disconnect when no client exists."""
        backend = FalkorDBLiteBackend(db_path="/tmp/test.db")
        backend.client = None
        backend._connected = False

        # Should not raise
        await backend.disconnect()

        assert backend._connected is False
