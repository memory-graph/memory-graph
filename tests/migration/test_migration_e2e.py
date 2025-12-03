"""
End-to-end migration tests.
"""

import os
import tempfile
import pytest
from pathlib import Path

from src.memorygraph.migration.manager import MigrationManager
from src.memorygraph.migration.models import BackendConfig, MigrationOptions
from src.memorygraph.config import BackendType
from src.memorygraph.backends.factory import BackendFactory
from src.memorygraph.sqlite_database import SQLiteMemoryDatabase
from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.models import Memory, MemoryType, RelationshipType, RelationshipProperties


@pytest.mark.asyncio
async def test_sqlite_to_sqlite_migration():
    """Test basic SQLite to SQLite migration."""
    # Create temp databases
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "source.db")
        target_path = os.path.join(tmpdir, "target.db")

        # Set up source database with test data
        os.environ["MEMORY_BACKEND"] = "sqlite"
        os.environ["MEMORY_SQLITE_PATH"] = source_path

        source_backend = await BackendFactory.create_backend()
        if isinstance(source_backend, SQLiteFallbackBackend):
            source_db = SQLiteMemoryDatabase(source_backend)
        else:
            source_db = SQLiteMemoryDatabase(source_backend)  # For SQLite, always use SQLiteMemoryDatabase
        await source_db.initialize_schema()

        # Add test memories
        test_memory_ids = []
        for i in range(5):
            memory = Memory(
                type=MemoryType.SOLUTION,
                title=f"Test Memory {i}",
                content=f"Test content {i}",
                tags=["test"],
                importance=0.5
            )
            memory_id = await source_db.store_memory(memory)
            test_memory_ids.append(memory_id)

        # Add test relationships
        await source_db.create_relationship(
            from_memory_id=test_memory_ids[0],
            to_memory_id=test_memory_ids[1],
            relationship_type=RelationshipType.SOLVES,
            properties=RelationshipProperties()
        )

        await source_backend.disconnect()

        # Perform migration
        source_config = BackendConfig(
            backend_type=BackendType.SQLITE,
            path=source_path
        )

        target_config = BackendConfig(
            backend_type=BackendType.SQLITE,
            path=target_path
        )

        options = MigrationOptions(
            dry_run=False,
            verbose=False,
            skip_duplicates=True,
            verify=True,
            rollback_on_failure=True
        )

        manager = MigrationManager()
        result = await manager.migrate(source_config, target_config, options)

        # Verify migration succeeded
        assert result.success is True
        assert result.imported_memories == 5
        assert result.imported_relationships >= 1  # At least the one we created
        assert result.verification_result is not None
        assert result.verification_result.valid is True
        assert result.verification_result.source_count == 5
        assert result.verification_result.target_count == 5


@pytest.mark.asyncio
async def test_migration_dry_run():
    """Test dry-run mode doesn't write data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(tmpdir, "source.db")
        target_path = os.path.join(tmpdir, "target.db")

        # Set up source database
        os.environ["MEMORY_BACKEND"] = "sqlite"
        os.environ["MEMORY_SQLITE_PATH"] = source_path

        source_backend = await BackendFactory.create_backend()
        if isinstance(source_backend, SQLiteFallbackBackend):
            source_db = SQLiteMemoryDatabase(source_backend)
        else:
            source_db = SQLiteMemoryDatabase(source_backend)  # For SQLite, always use SQLiteMemoryDatabase
        await source_db.initialize_schema()

        # Add one test memory
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test Memory",
            content="Test content",
            tags=["test"]
        )
        await source_db.store_memory(memory)
        await source_backend.disconnect()

        # Perform dry-run migration
        source_config = BackendConfig(
            backend_type=BackendType.SQLITE,
            path=source_path
        )

        target_config = BackendConfig(
            backend_type=BackendType.SQLITE,
            path=target_path
        )

        options = MigrationOptions(dry_run=True)

        manager = MigrationManager()
        result = await manager.migrate(source_config, target_config, options)

        # Verify dry-run succeeded
        assert result.success is True
        assert result.dry_run is True
        assert result.imported_memories == 0  # Nothing imported in dry-run

        # Note: target database file may exist from validation check,
        # but should contain no data
        if os.path.exists(target_path):
            # Verify it's empty
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = target_path
            target_backend = await BackendFactory.create_backend()
            if isinstance(target_backend, SQLiteFallbackBackend):
                target_db = SQLiteMemoryDatabase(target_backend)
            else:
                target_db = SQLiteMemoryDatabase(target_backend)

            # Check it has no memories
            from src.memorygraph.models import SearchQuery
            query = SearchQuery(query="", limit=1000, offset=0, match_mode="any")
            memories = await target_db.search_memories(query)
            assert len(memories) == 0, "Dry-run should not import any data"

            await target_backend.disconnect()


@pytest.mark.asyncio
async def test_migration_validation_failure():
    """Test migration fails with invalid source config."""
    source_config = BackendConfig(
        backend_type=BackendType.SQLITE,
        path="/nonexistent/path.db"
    )

    target_config = BackendConfig(
        backend_type=BackendType.SQLITE,
        path="/tmp/target.db"
    )

    options = MigrationOptions()

    manager = MigrationManager()
    result = await manager.migrate(source_config, target_config, options)

    # Migration should fail
    assert result.success is False
    assert len(result.errors) > 0
