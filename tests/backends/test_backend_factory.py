"""
Tests for backend factory and auto-selection logic.

These tests verify that the backend factory correctly selects and initializes
the appropriate backend based on configuration and availability.
"""

import importlib.util
import pytest
import os
from unittest.mock import AsyncMock, patch

from src.memorygraph.backends.factory import BackendFactory
from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.models import DatabaseConnectionError

# Check if neo4j is available before importing backends
neo4j_available = importlib.util.find_spec("neo4j") is not None

if neo4j_available:
    from src.memorygraph.backends.neo4j_backend import Neo4jBackend
    from src.memorygraph.backends.memgraph_backend import MemgraphBackend
else:
    Neo4jBackend = None
    MemgraphBackend = None

# Skip entire module if neo4j not available
pytestmark = pytest.mark.skipif(
    not neo4j_available,
    reason="neo4j package not installed"
)


class TestBackendFactoryExplicitSelection:
    """Test explicit backend selection via MEMORY_BACKEND env var."""

    @pytest.mark.asyncio
    async def test_create_neo4j_explicit(self):
        """Test creating Neo4j backend when explicitly requested."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "neo4j",
            "MEMORY_NEO4J_PASSWORD": "test"
        }):
            with patch.object(Neo4jBackend, 'connect', new=AsyncMock()):
                backend = await BackendFactory.create_backend()

                assert isinstance(backend, Neo4jBackend)

    @pytest.mark.asyncio
    async def test_create_memgraph_explicit(self):
        """Test creating Memgraph backend when explicitly requested."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "memgraph",
            "MEMORY_MEMGRAPH_URI": "bolt://test:7687"
        }):
            with patch.object(MemgraphBackend, 'connect', new=AsyncMock()):
                backend = await BackendFactory.create_backend()

                assert isinstance(backend, MemgraphBackend)

    @pytest.mark.asyncio
    async def test_create_sqlite_explicit(self):
        """Test creating SQLite backend when explicitly requested."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "sqlite"
        }):
            with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                    backend = await BackendFactory.create_backend()

                    assert isinstance(backend, SQLiteFallbackBackend)

    @pytest.mark.asyncio
    async def test_invalid_backend_type_raises_error(self):
        """Test that invalid backend type raises error."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "invalid_backend"
        }):
            with pytest.raises(DatabaseConnectionError, match="Unknown backend type"):
                await BackendFactory.create_backend()


class TestBackendFactoryAutoSelection:
    """Test automatic backend selection logic."""

    @pytest.mark.asyncio
    async def test_auto_select_neo4j_when_configured(self):
        """Test auto-selection chooses Neo4j when password is configured."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "auto",
            "MEMORY_NEO4J_PASSWORD": "test"
        }, clear=True):
            with patch.object(Neo4jBackend, 'connect', new=AsyncMock()):
                backend = await BackendFactory.create_backend()

                assert isinstance(backend, Neo4jBackend)

    @pytest.mark.asyncio
    async def test_auto_select_memgraph_when_neo4j_fails(self):
        """Test auto-selection falls back to Memgraph when Neo4j fails."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "auto",
            "MEMORY_NEO4J_PASSWORD": "test",
            "MEMORY_MEMGRAPH_URI": "bolt://test:7687"
        }, clear=True):
            # Neo4j connection fails
            with patch.object(Neo4jBackend, 'connect', side_effect=DatabaseConnectionError("Failed")):
                # Memgraph succeeds
                with patch.object(MemgraphBackend, 'connect', new=AsyncMock()):
                    backend = await BackendFactory.create_backend()

                    assert isinstance(backend, MemgraphBackend)

    @pytest.mark.asyncio
    async def test_auto_select_sqlite_when_all_fail(self):
        """Test auto-selection falls back to SQLite when all others fail."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "auto",
            "MEMORY_NEO4J_PASSWORD": "test",
            "MEMORY_MEMGRAPH_URI": "bolt://test:7687"
        }, clear=True):
            # Both Neo4j and Memgraph fail
            with patch.object(Neo4jBackend, 'connect', side_effect=DatabaseConnectionError("Failed")):
                with patch.object(MemgraphBackend, 'connect', side_effect=DatabaseConnectionError("Failed")):
                    # SQLite succeeds
                    with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                        with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                            backend = await BackendFactory.create_backend()

                            assert isinstance(backend, SQLiteFallbackBackend)

    @pytest.mark.asyncio
    async def test_auto_select_sqlite_directly_when_no_others_configured(self):
        """Test auto-selection chooses SQLite when no other backend is configured."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "auto"
        }, clear=True):
            with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                    backend = await BackendFactory.create_backend()

                    assert isinstance(backend, SQLiteFallbackBackend)

    @pytest.mark.asyncio
    async def test_auto_select_raises_when_all_fail(self):
        """Test auto-selection raises error when all backends fail."""
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "auto",
            "MEMORY_NEO4J_PASSWORD": "test"
        }, clear=True):
            # All backends fail
            with patch.object(Neo4jBackend, 'connect', side_effect=DatabaseConnectionError("Failed")):
                with patch.object(SQLiteFallbackBackend, 'connect', side_effect=DatabaseConnectionError("Failed")):
                    with pytest.raises(DatabaseConnectionError, match="Could not connect to any backend"):
                        await BackendFactory.create_backend()


class TestBackendFactoryHelpers:
    """Test helper methods in BackendFactory."""

    def test_get_configured_backend_type(self):
        """Test getting configured backend type."""
        with patch.dict(os.environ, {"MEMORY_BACKEND": "neo4j"}):
            assert BackendFactory.get_configured_backend_type() == "neo4j"

        with patch.dict(os.environ, {}, clear=True):
            assert BackendFactory.get_configured_backend_type() == "auto"

    def test_is_backend_configured_neo4j(self):
        """Test checking if Neo4j is configured."""
        with patch.dict(os.environ, {"MEMORY_NEO4J_PASSWORD": "test"}):
            assert BackendFactory.is_backend_configured("neo4j") is True

        with patch.dict(os.environ, {}, clear=True):
            assert BackendFactory.is_backend_configured("neo4j") is False

    def test_is_backend_configured_memgraph(self):
        """Test checking if Memgraph is configured."""
        with patch.dict(os.environ, {"MEMORY_MEMGRAPH_URI": "bolt://test:7687"}):
            assert BackendFactory.is_backend_configured("memgraph") is True

        with patch.dict(os.environ, {}, clear=True):
            assert BackendFactory.is_backend_configured("memgraph") is False

    def test_is_backend_configured_sqlite(self):
        """Test checking if SQLite is configured (always True)."""
        assert BackendFactory.is_backend_configured("sqlite") is True

    def test_is_backend_configured_invalid(self):
        """Test checking if invalid backend type returns False."""
        assert BackendFactory.is_backend_configured("invalid_type") is False


class TestBackendFactoryPrivateMethods:
    """Test private factory methods for creating specific backends."""

    @pytest.mark.asyncio
    async def test_create_neo4j_missing_password_raises_error(self):
        """Test that creating Neo4j without password raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DatabaseConnectionError, match="password not configured"):
                await BackendFactory._create_neo4j()

    @pytest.mark.asyncio
    async def test_create_neo4j_with_password(self):
        """Test creating Neo4j backend with password."""
        with patch.dict(os.environ, {
            "MEMORY_NEO4J_PASSWORD": "test"
        }):
            with patch.object(Neo4jBackend, 'connect', new=AsyncMock()):
                backend = await BackendFactory._create_neo4j()

                assert isinstance(backend, Neo4jBackend)
                assert backend.password == "test"

    @pytest.mark.asyncio
    async def test_create_memgraph(self):
        """Test creating Memgraph backend."""
        with patch.dict(os.environ, {
            "MEMORY_MEMGRAPH_URI": "bolt://test:7687"
        }):
            with patch.object(MemgraphBackend, 'connect', new=AsyncMock()):
                backend = await BackendFactory._create_memgraph()

                assert isinstance(backend, MemgraphBackend)
                assert backend.uri == "bolt://test:7687"

    @pytest.mark.asyncio
    async def test_create_sqlite(self):
        """Test creating SQLite backend."""
        with patch.dict(os.environ, {
            "MEMORY_SQLITE_PATH": "/tmp/test.db"
        }):
            with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                    backend = await BackendFactory._create_sqlite()

                    assert isinstance(backend, SQLiteFallbackBackend)
                    assert backend.db_path == "/tmp/test.db"
