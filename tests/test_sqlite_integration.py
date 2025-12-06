"""
End-to-end integration test for SQLite backend with the server.

This test verifies that the full stack works:
- BackendFactory creates SQLite backend
- Server initializes with SQLiteMemoryDatabase
- Memory storage actually persists to disk
"""

import pytest
import tempfile
import os
from pathlib import Path

from memorygraph.backends.factory import BackendFactory
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.models import Memory, MemoryType


class TestSQLiteIntegration:
    """Test end-to-end SQLite integration."""

    @pytest.mark.asyncio
    async def test_backend_factory_creates_sqlite(self, monkeypatch):
        """Test that BackendFactory creates SQLite backend by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            monkeypatch.setenv("MEMORY_SQLITE_PATH", db_path)
            monkeypatch.setenv("MEMORY_BACKEND", "sqlite")

            backend = await BackendFactory.create_backend()

            # Use backend_name() method instead of isinstance to avoid
            # issues with module reloading during test runs
            assert backend.backend_name() == "sqlite"
            assert hasattr(backend, 'conn')  # SQLite-specific attribute

            await backend.disconnect()

    @pytest.mark.asyncio
    async def test_sqlite_memory_database_with_factory(self, monkeypatch):
        """Test that SQLiteMemoryDatabase works with factory-created backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            monkeypatch.setenv("MEMORY_SQLITE_PATH", db_path)
            monkeypatch.setenv("MEMORY_BACKEND", "sqlite")

            # Create backend via factory
            backend = await BackendFactory.create_backend()

            # Create database
            db = SQLiteMemoryDatabase(backend)
            await db.initialize_schema()

            # Store a memory
            memory = Memory(
                type=MemoryType.GENERAL,
                title="Test Memory",
                content="This is a test"
            )

            memory_id = await db.store_memory(memory)
            assert memory_id is not None

            # Retrieve it
            retrieved = await db.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.title == "Test Memory"

            await backend.disconnect()

    @pytest.mark.asyncio
    async def test_memory_persists_to_disk(self, monkeypatch):
        """Test that memories actually persist to the SQLite database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "persistence_test.db")
            monkeypatch.setenv("MEMORY_SQLITE_PATH", db_path)
            monkeypatch.setenv("MEMORY_BACKEND", "sqlite")

            # Create and store a memory
            backend1 = await BackendFactory.create_backend()
            db1 = SQLiteMemoryDatabase(backend1)
            await db1.initialize_schema()

            memory = Memory(
                type=MemoryType.SOLUTION,
                title="Persistent Memory",
                content="This should persist"
            )

            memory_id = await db1.store_memory(memory)
            await backend1.disconnect()

            # Verify file exists and has content
            assert os.path.exists(db_path)
            assert os.path.getsize(db_path) > 0

            # Reconnect and verify data is still there
            backend2 = await BackendFactory.create_backend()
            db2 = SQLiteMemoryDatabase(backend2)

            retrieved = await db2.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.title == "Persistent Memory"
            assert retrieved.content == "This should persist"

            await backend2.disconnect()

    @pytest.mark.asyncio
    async def test_default_backend_is_sqlite(self, monkeypatch):
        """Test that SQLite is the default backend when no env vars are set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Clear any existing backend env vars and set SQLite path
            monkeypatch.delenv("MEMORY_BACKEND", raising=False)
            monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
            monkeypatch.delenv("MEMORY_NEO4J_PASSWORD", raising=False)
            monkeypatch.setenv("MEMORY_SQLITE_PATH", os.path.join(tmpdir, "default.db"))

            backend = await BackendFactory.create_backend()

            # Should be SQLite by default - use backend_name() to avoid
            # isinstance issues with module reloading
            assert backend.backend_name() == "sqlite"

            await backend.disconnect()

    @pytest.mark.asyncio
    async def test_server_initialization_with_sqlite(self, monkeypatch):
        """Test that the server initializes correctly with SQLite backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "server_test.db")
            monkeypatch.setenv("MEMORY_SQLITE_PATH", db_path)
            monkeypatch.setenv("MEMORY_BACKEND", "sqlite")

            # Reload server module to get fresh imports (avoids issues with
            # module reloading from other tests)
            import importlib
            import memorygraph.server
            importlib.reload(memorygraph.server)
            from memorygraph.server import ClaudeMemoryServer

            server = ClaudeMemoryServer()
            await server.initialize()

            # Verify we have a SQLite backend - the important thing is that
            # the underlying connection uses SQLite, not the specific class type
            # (which can be affected by module reloading during test runs)
            assert server.db_connection is not None
            assert server.db_connection.backend_name() == "sqlite"
            assert server.memory_db is not None

            # Test storing a memory via the server's database
            memory = Memory(
                type=MemoryType.TASK,
                title="Server Test",
                content="Testing server integration"
            )

            memory_id = await server.memory_db.store_memory(memory)
            assert memory_id is not None

            # Retrieve and verify
            retrieved = await server.memory_db.get_memory(memory_id)
            assert retrieved is not None
            assert retrieved.title == "Server Test"

            await server.cleanup()
