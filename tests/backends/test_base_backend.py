"""
Tests for src/memorygraph/backends/base.py

Following TDD approach to achieve 100% coverage of GraphBackend ABC.
"""
import pytest
from typing import Any, Optional

from memorygraph.backends.base import GraphBackend


class MockGraphBackend(GraphBackend):
    """Mock implementation of GraphBackend for testing."""

    def __init__(self):
        self.connected = False
        self.connect_called = False
        self.disconnect_called = False
        self.query_calls = []

    async def connect(self) -> bool:
        """Mock connect implementation."""
        self.connect_called = True
        self.connected = True
        return True

    async def disconnect(self) -> None:
        """Mock disconnect implementation."""
        self.disconnect_called = True
        self.connected = False

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False,
    ) -> list[dict[str, Any]]:
        """Mock execute_query implementation."""
        self.query_calls.append({"query": query, "parameters": parameters, "write": write})
        return [{"result": "mock_data"}]

    async def initialize_schema(self) -> None:
        """Mock initialize_schema implementation."""
        pass

    async def health_check(self) -> dict[str, Any]:
        """Mock health_check implementation."""
        return {
            "connected": self.connected,
            "backend_type": "mock",
            "version": "1.0.0",
        }

    def backend_name(self) -> str:
        """Mock backend_name implementation."""
        return "mock"

    def supports_fulltext_search(self) -> bool:
        """Mock supports_fulltext_search implementation."""
        return True

    def supports_transactions(self) -> bool:
        """Mock supports_transactions implementation."""
        return True

    def is_cypher_capable(self) -> bool:
        """Mock is_cypher_capable implementation."""
        return True


class TestGraphBackendABC:
    """Test GraphBackend abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that GraphBackend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GraphBackend()

    def test_mock_backend_instantiates(self):
        """Test that a concrete implementation can be instantiated."""
        backend = MockGraphBackend()
        assert backend is not None
        assert isinstance(backend, GraphBackend)


class TestGraphBackendContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_calls_connect(self):
        """Test that __aenter__ calls connect."""
        backend = MockGraphBackend()
        assert backend.connect_called is False

        async with backend as ctx:
            assert backend.connect_called is True
            assert ctx is backend

    @pytest.mark.asyncio
    async def test_context_manager_calls_disconnect(self):
        """Test that __aexit__ calls disconnect."""
        backend = MockGraphBackend()

        async with backend:
            assert backend.disconnect_called is False

        # After exiting context, disconnect should be called
        assert backend.disconnect_called is True

    @pytest.mark.asyncio
    async def test_context_manager_full_lifecycle(self):
        """Test complete async context manager lifecycle."""
        backend = MockGraphBackend()
        assert backend.connected is False

        async with backend:
            assert backend.connected is True
            assert backend.connect_called is True

        assert backend.connected is False
        assert backend.disconnect_called is True

    @pytest.mark.asyncio
    async def test_context_manager_returns_false_on_exit(self):
        """Test that __aexit__ returns False (doesn't suppress exceptions)."""
        backend = MockGraphBackend()

        # __aexit__ should return False, meaning exceptions are not suppressed
        result = await backend.__aexit__(None, None, None)
        assert result is False

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self):
        """Test that exceptions in context are not suppressed."""
        backend = MockGraphBackend()

        with pytest.raises(ValueError, match="test exception"):
            async with backend:
                raise ValueError("test exception")

        # Disconnect should still be called even with exception
        assert backend.disconnect_called is True


class TestGraphBackendCompatibilityMethods:
    """Test compatibility wrapper methods."""

    @pytest.mark.asyncio
    async def test_execute_write_query_calls_execute_query_with_write_true(self):
        """Test execute_write_query wrapper."""
        backend = MockGraphBackend()
        await backend.connect()

        query = "CREATE (n:Node {name: $name})"
        params = {"name": "test"}

        result = await backend.execute_write_query(query, params)

        # Should have called execute_query with write=True
        assert len(backend.query_calls) == 1
        assert backend.query_calls[0]["query"] == query
        assert backend.query_calls[0]["parameters"] == params
        assert backend.query_calls[0]["write"] is True
        assert result == [{"result": "mock_data"}]

    @pytest.mark.asyncio
    async def test_execute_read_query_calls_execute_query_with_write_false(self):
        """Test execute_read_query wrapper."""
        backend = MockGraphBackend()
        await backend.connect()

        query = "MATCH (n:Node) RETURN n"
        params = {"limit": 10}

        result = await backend.execute_read_query(query, params)

        # Should have called execute_query with write=False
        assert len(backend.query_calls) == 1
        assert backend.query_calls[0]["query"] == query
        assert backend.query_calls[0]["parameters"] == params
        assert backend.query_calls[0]["write"] is False
        assert result == [{"result": "mock_data"}]

    @pytest.mark.asyncio
    async def test_execute_write_query_without_parameters(self):
        """Test execute_write_query with no parameters."""
        backend = MockGraphBackend()

        result = await backend.execute_write_query("CREATE (n:Node)")

        assert len(backend.query_calls) == 1
        assert backend.query_calls[0]["parameters"] is None
        assert backend.query_calls[0]["write"] is True

    @pytest.mark.asyncio
    async def test_execute_read_query_without_parameters(self):
        """Test execute_read_query with no parameters."""
        backend = MockGraphBackend()

        result = await backend.execute_read_query("MATCH (n) RETURN n")

        assert len(backend.query_calls) == 1
        assert backend.query_calls[0]["parameters"] is None
        assert backend.query_calls[0]["write"] is False

    @pytest.mark.asyncio
    async def test_close_calls_disconnect(self):
        """Test that close() wrapper calls disconnect()."""
        backend = MockGraphBackend()
        await backend.connect()

        assert backend.disconnect_called is False

        await backend.close()

        assert backend.disconnect_called is True
        assert backend.connected is False


class TestGraphBackendAbstractMethods:
    """Test that all abstract methods are defined."""

    def test_abstract_methods_exist(self):
        """Test that GraphBackend defines all expected abstract methods."""
        abstract_methods = [
            "connect",
            "disconnect",
            "execute_query",
            "initialize_schema",
            "health_check",
            "backend_name",
            "supports_fulltext_search",
            "supports_transactions",
            "is_cypher_capable",
        ]

        for method_name in abstract_methods:
            assert hasattr(GraphBackend, method_name), f"Missing method: {method_name}"

    def test_concrete_methods_exist(self):
        """Test that GraphBackend defines expected concrete methods."""
        concrete_methods = [
            "__aenter__",
            "__aexit__",
            "execute_write_query",
            "execute_read_query",
            "close",
        ]

        for method_name in concrete_methods:
            assert hasattr(GraphBackend, method_name), f"Missing method: {method_name}"


class TestMockBackendImplementation:
    """Test the mock backend implementation."""

    @pytest.mark.asyncio
    async def test_mock_backend_health_check(self):
        """Test mock backend health check."""
        backend = MockGraphBackend()
        await backend.connect()

        health = await backend.health_check()

        assert health["connected"] is True
        assert health["backend_type"] == "mock"
        assert health["version"] == "1.0.0"

    def test_mock_backend_capabilities(self):
        """Test mock backend capability flags."""
        backend = MockGraphBackend()

        assert backend.backend_name() == "mock"
        assert backend.supports_fulltext_search() is True
        assert backend.supports_transactions() is True
        assert backend.is_cypher_capable() is True

    @pytest.mark.asyncio
    async def test_mock_backend_initialize_schema(self):
        """Test mock backend schema initialization."""
        backend = MockGraphBackend()

        # Should not raise
        await backend.initialize_schema()
