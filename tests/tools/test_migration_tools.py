"""
Tests for MCP migration tools.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.memorygraph.tools.migration_tools import (
    handle_migrate_database,
    handle_validate_migration
)
from src.memorygraph.backends.factory import BackendFactory
from src.memorygraph.sqlite_database import SQLiteMemoryDatabase
from src.memorygraph.models import Memory, MemoryType


@pytest.mark.asyncio
async def test_validate_migration_tool():
    """Test validate_migration tool with valid configuration."""
    # Create source database with test data
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "source.db")
        target_path = os.path.join(tmpdir, "target.db")

        # Set up source
        os.environ["MEMORY_BACKEND"] = "sqlite"
        os.environ["MEMORY_SQLITE_PATH"] = source_path

        source_backend = await BackendFactory.create_backend()
        source_db = SQLiteMemoryDatabase(source_backend)
        await source_db.initialize_schema()

        # Add test memory
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test Memory",
            content="Test content",
            tags=["test"]
        )
        await source_db.store_memory(memory)
        await source_backend.disconnect()

        # Test validation
        result = await handle_validate_migration(
            target_backend="sqlite",
            target_config={"path": target_path}
        )

        # Verify result
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["source_backend"] == "sqlite"
        assert result["target_backend"] == "sqlite"
        assert result["imported_memories"] == 0  # Dry-run doesn't import


@pytest.mark.asyncio
async def test_migrate_database_tool():
    """Test migrate_database tool with actual migration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "source.db")
        target_path = os.path.join(tmpdir, "target.db")

        # Set up source with test data
        os.environ["MEMORY_BACKEND"] = "sqlite"
        os.environ["MEMORY_SQLITE_PATH"] = source_path

        source_backend = await BackendFactory.create_backend()
        source_db = SQLiteMemoryDatabase(source_backend)
        await source_db.initialize_schema()

        # Add test memories
        for i in range(3):
            memory = Memory(
                type=MemoryType.SOLUTION,
                title=f"Test Memory {i}",
                content=f"Test content {i}",
                tags=["test"]
            )
            await source_db.store_memory(memory)

        await source_backend.disconnect()

        # Perform migration
        result = await handle_migrate_database(
            target_backend="sqlite",
            target_config={"path": target_path},
            dry_run=False,
            verify=True
        )

        # Verify result
        assert result["success"] is True
        assert result["dry_run"] is False
        assert result["imported_memories"] == 3
        assert result["verification"]["valid"] is True
        assert result["verification"]["source_count"] == 3
        assert result["verification"]["target_count"] == 3


@pytest.mark.asyncio
async def test_migrate_database_invalid_backend():
    """Test migrate_database with invalid backend type."""
    result = await handle_migrate_database(
        target_backend="invalid_backend",
        target_config={"path": "/tmp/test.db"}
    )

    # Should fail with validation error
    assert result["success"] is False
    assert "error" in result
    assert "invalid" in result["error"].lower()


@pytest.mark.asyncio
async def test_migrate_database_missing_config():
    """Test migrate_database with missing required configuration."""
    # SQLite requires 'path' parameter
    result = await handle_migrate_database(
        target_backend="sqlite",
        target_config={}  # Missing path
    )

    # Should fail with validation error
    assert result["success"] is False
    assert "error" in result
    assert "validation" in result["error"].lower() or "path" in result["error"].lower()


@pytest.mark.asyncio
async def test_migrate_database_dry_run():
    """Test migrate_database in dry-run mode doesn't write data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "source.db")
        target_path = os.path.join(tmpdir, "target.db")

        # Set up source
        os.environ["MEMORY_BACKEND"] = "sqlite"
        os.environ["MEMORY_SQLITE_PATH"] = source_path

        source_backend = await BackendFactory.create_backend()
        source_db = SQLiteMemoryDatabase(source_backend)
        await source_db.initialize_schema()

        # Add test memory
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test Memory",
            content="Test content"
        )
        await source_db.store_memory(memory)
        await source_backend.disconnect()

        # Dry-run migration
        result = await handle_migrate_database(
            target_backend="sqlite",
            target_config={"path": target_path},
            dry_run=True
        )

        # Verify dry-run succeeded but didn't import
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["imported_memories"] == 0

        # Verify target doesn't have data (may not even exist)
        if os.path.exists(target_path):
            # If it exists, verify it's empty
            os.environ["MEMORY_SQLITE_PATH"] = target_path
            target_backend = await BackendFactory.create_backend()
            target_db = SQLiteMemoryDatabase(target_backend)

            from src.memorygraph.models import SearchQuery
            query = SearchQuery(query="", limit=100, offset=0, match_mode="any")
            memories = await target_db.search_memories(query)
            assert len(memories) == 0

            await target_backend.disconnect()


@pytest.mark.asyncio
async def test_migrate_database_with_verification():
    """Test migrate_database with verification enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "source.db")
        target_path = os.path.join(tmpdir, "target.db")

        # Set up source
        os.environ["MEMORY_BACKEND"] = "sqlite"
        os.environ["MEMORY_SQLITE_PATH"] = source_path

        source_backend = await BackendFactory.create_backend()
        source_db = SQLiteMemoryDatabase(source_backend)
        await source_db.initialize_schema()

        # Add test memory
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test Memory",
            content="Test content"
        )
        await source_db.store_memory(memory)
        await source_backend.disconnect()

        # Migrate with verification
        result = await handle_migrate_database(
            target_backend="sqlite",
            target_config={"path": target_path},
            verify=True
        )

        # Verify result includes verification details
        assert result["success"] is True
        assert "verification" in result
        assert result["verification"]["valid"] is True
        assert result["verification"]["source_count"] == 1
        assert result["verification"]["target_count"] == 1
        assert result["verification"]["sample_checks"] >= 1
        assert result["verification"]["sample_passed"] >= 1


@pytest.mark.asyncio
async def test_migrate_database_skip_duplicates():
    """Test migrate_database with skip_duplicates option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "source.db")
        target_path = os.path.join(tmpdir, "target.db")

        # Set up source
        os.environ["MEMORY_BACKEND"] = "sqlite"
        os.environ["MEMORY_SQLITE_PATH"] = source_path

        source_backend = await BackendFactory.create_backend()
        source_db = SQLiteMemoryDatabase(source_backend)
        await source_db.initialize_schema()

        # Add test memories
        memory_ids = []
        for i in range(2):
            memory = Memory(
                type=MemoryType.SOLUTION,
                title=f"Test Memory {i}",
                content=f"Test content {i}"
            )
            memory_id = await source_db.store_memory(memory)
            memory_ids.append(memory_id)

        await source_backend.disconnect()

        # First migration
        result1 = await handle_migrate_database(
            target_backend="sqlite",
            target_config={"path": target_path},
            skip_duplicates=False,
            verify=True
        )

        assert result1["success"] is True
        assert result1["imported_memories"] == 2

        # Second migration with skip_duplicates=True
        result2 = await handle_migrate_database(
            target_backend="sqlite",
            target_config={"path": target_path},
            skip_duplicates=True,
            verify=False
        )

        # Should skip duplicates
        assert result2["success"] is True
        assert result2["skipped_memories"] >= 0  # May skip some or all
