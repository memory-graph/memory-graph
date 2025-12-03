"""
Comprehensive tests for MigrationManager covering edge cases and error paths.

Tests cover the 36% uncovered code in manager.py:
- Export/import error handling
- Validation edge cases
- Verification sampling and error detection
- Rollback functionality
- Backend creation error paths
- Helper method edge cases
"""

import os
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.memorygraph.migration.manager import MigrationManager, MigrationError
from src.memorygraph.migration.models import (
    BackendConfig,
    BackendType,
    MigrationOptions,
    ValidationResult,
    VerificationResult
)
from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from src.memorygraph.sqlite_database import SQLiteMemoryDatabase
from src.memorygraph.models import Memory, MemoryType, RelationshipType, RelationshipProperties


class TestMigrationManagerValidation:
    """Test validation phase edge cases."""

    @pytest.mark.asyncio
    async def test_validate_source_with_invalid_config(self):
        """Test validation fails with invalid source config."""
        manager = MigrationManager()
        config = BackendConfig(backend_type=BackendType.SQLITE)  # Missing path

        with pytest.raises(MigrationError) as exc_info:
            await manager._validate_source(config)

        assert "Invalid source configuration" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_source_with_empty_database_warning(self, caplog):
        """Test validation warns when source is empty."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "empty.db")
            config = BackendConfig(backend_type=BackendType.SQLITE, path=source_path)

            # Create empty database
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = source_path
            backend = await manager._create_backend(config)
            await backend.initialize_schema()
            await backend.disconnect()

            # Validate should warn
            await manager._validate_source(config)
            assert "Source backend is empty" in caplog.text

    @pytest.mark.asyncio
    async def test_validate_source_unreachable_backend(self):
        """Test validation fails with unreachable backend."""
        manager = MigrationManager()
        config = BackendConfig(
            backend_type=BackendType.NEO4J,
            uri="bolt://nonexistent:7687",
            username="neo4j",
            password="password"
        )

        with pytest.raises(MigrationError) as exc_info:
            await manager._validate_source(config)

        # Error message may vary by backend, just check it failed
        assert "Failed to create backend" in str(exc_info.value) or "not accessible" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_target_with_existing_data_warning(self, caplog):
        """Test validation warns when target already has data."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = os.path.join(tmpdir, "target.db")
            config = BackendConfig(backend_type=BackendType.SQLITE, path=target_path)

            # Create database with data
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = target_path
            backend = await manager._create_backend(config)
            await backend.initialize_schema()

            # Add a memory
            db = SQLiteMemoryDatabase(backend)
            memory = Memory(
                type=MemoryType.SOLUTION,
                title="Existing",
                content="Content",
                importance=0.5
            )
            await db.store_memory(memory)
            await backend.disconnect()

            # Validate should warn
            await manager._validate_target(config)
            assert "already contains" in caplog.text


class TestMigrationManagerExportValidation:
    """Test export validation edge cases."""

    @pytest.mark.asyncio
    async def test_validate_export_missing_file(self):
        """Test validation fails when export file doesn't exist."""
        manager = MigrationManager()
        result = await manager._validate_export(Path("/nonexistent/file.json"))

        assert result.valid is False
        assert "not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_export_invalid_json(self):
        """Test validation fails with invalid JSON."""
        manager = MigrationManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            export_path = Path(f.name)

        try:
            result = await manager._validate_export(export_path)

            assert result.valid is False
            assert "Invalid JSON" in result.errors[0]
        finally:
            export_path.unlink()

    @pytest.mark.asyncio
    async def test_validate_export_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        manager = MigrationManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"some": "data"}, f)  # Missing memories and relationships
            export_path = Path(f.name)

        try:
            result = await manager._validate_export(export_path)

            assert result.valid is False
            assert any("missing 'memories'" in err for err in result.errors)
            assert any("missing 'relationships'" in err for err in result.errors)
        finally:
            export_path.unlink()

    @pytest.mark.asyncio
    async def test_validate_export_missing_version(self):
        """Test validation fails when version info is missing."""
        manager = MigrationManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "memories": [],
                "relationships": []
            }, f)
            export_path = Path(f.name)

        try:
            result = await manager._validate_export(export_path)

            assert result.valid is False
            assert any("version" in err.lower() for err in result.errors)
        finally:
            export_path.unlink()

    @pytest.mark.asyncio
    async def test_validate_export_empty_memories_warning(self):
        """Test validation warns when export has zero memories."""
        manager = MigrationManager()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "format_version": "2.0",
                "memories": [],
                "relationships": []
            }, f)
            export_path = Path(f.name)

        try:
            result = await manager._validate_export(export_path)

            assert result.valid is True  # Valid but with warnings
            assert any("zero memories" in warn for warn in result.warnings)
        finally:
            export_path.unlink()


class TestMigrationManagerVerification:
    """Test verification phase edge cases."""

    @pytest.mark.asyncio
    async def test_verify_migration_count_mismatch(self):
        """Test verification detects count mismatches."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "source.db")
            target_path = os.path.join(tmpdir, "target.db")

            # Create source with 5 memories
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = source_path
            source_backend = await manager._create_backend(
                BackendConfig(backend_type=BackendType.SQLITE, path=source_path)
            )
            source_db = SQLiteMemoryDatabase(source_backend)
            await source_db.initialize_schema()

            for i in range(5):
                memory = Memory(
                    type=MemoryType.SOLUTION,
                    title=f"Memory {i}",
                    content=f"Content {i}",
                    importance=0.5
                )
                await source_db.store_memory(memory)

            await source_backend.disconnect()

            # Create target with only 3 memories
            os.environ["MEMORY_SQLITE_PATH"] = target_path
            target_backend = await manager._create_backend(
                BackendConfig(backend_type=BackendType.SQLITE, path=target_path)
            )
            target_db = SQLiteMemoryDatabase(target_backend)
            await target_db.initialize_schema()

            for i in range(3):
                memory = Memory(
                    type=MemoryType.SOLUTION,
                    title=f"Memory {i}",
                    content=f"Content {i}",
                    importance=0.5
                )
                await target_db.store_memory(memory)

            await target_backend.disconnect()

            # Create dummy export
            export_path = Path(tmpdir) / "export.json"
            export_path.write_text('{"format_version": "2.0", "memories": [], "relationships": []}')

            # Verify should detect mismatch
            result = await manager._verify_migration(
                BackendConfig(backend_type=BackendType.SQLITE, path=source_path),
                BackendConfig(backend_type=BackendType.SQLITE, path=target_path),
                export_path
            )

            assert result.valid is False
            assert result.source_count == 5
            assert result.target_count == 3
            assert any("count mismatch" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_verify_migration_sample_content_mismatch(self):
        """Test verification detects content mismatches in sample."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "source.db")
            target_path = os.path.join(tmpdir, "target.db")

            # Create source and target with same IDs but different content
            memory_id = "test-memory-123"

            # Source
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = source_path
            source_backend = await manager._create_backend(
                BackendConfig(backend_type=BackendType.SQLITE, path=source_path)
            )
            source_db = SQLiteMemoryDatabase(source_backend)
            await source_db.initialize_schema()

            source_memory = Memory(
                id=memory_id,
                type=MemoryType.SOLUTION,
                title="Test",
                content="Original content",
                importance=0.5
            )
            await source_db.store_memory(source_memory)
            await source_backend.disconnect()

            # Target with different content
            os.environ["MEMORY_SQLITE_PATH"] = target_path
            target_backend = await manager._create_backend(
                BackendConfig(backend_type=BackendType.SQLITE, path=target_path)
            )
            target_db = SQLiteMemoryDatabase(target_backend)
            await target_db.initialize_schema()

            target_memory = Memory(
                id=memory_id,
                type=MemoryType.SOLUTION,
                title="Test",
                content="Different content",  # Different!
                importance=0.5
            )
            await target_db.store_memory(target_memory)
            await target_backend.disconnect()

            # Create dummy export
            export_path = Path(tmpdir) / "export.json"
            export_path.write_text('{"format_version": "2.0", "memories": [], "relationships": []}')

            # Verify should detect content mismatch
            result = await manager._verify_migration(
                BackendConfig(backend_type=BackendType.SQLITE, path=source_path),
                BackendConfig(backend_type=BackendType.SQLITE, path=target_path),
                export_path
            )

            assert result.valid is False
            assert any("content mismatch" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_verify_migration_missing_memory(self):
        """Test verification detects missing memories."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "source.db")
            target_path = os.path.join(tmpdir, "target.db")

            memory_id = "test-memory-123"

            # Create source with memory
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = source_path
            source_backend = await manager._create_backend(
                BackendConfig(backend_type=BackendType.SQLITE, path=source_path)
            )
            source_db = SQLiteMemoryDatabase(source_backend)
            await source_db.initialize_schema()

            memory = Memory(
                id=memory_id,
                type=MemoryType.SOLUTION,
                title="Test",
                content="Content",
                importance=0.5
            )
            await source_db.store_memory(memory)
            await source_backend.disconnect()

            # Create empty target
            os.environ["MEMORY_SQLITE_PATH"] = target_path
            target_backend = await manager._create_backend(
                BackendConfig(backend_type=BackendType.SQLITE, path=target_path)
            )
            target_db = SQLiteMemoryDatabase(target_backend)
            await target_db.initialize_schema()
            await target_backend.disconnect()

            export_path = Path(tmpdir) / "export.json"
            export_path.write_text('{"format_version": "2.0", "memories": [], "relationships": []}')

            result = await manager._verify_migration(
                BackendConfig(backend_type=BackendType.SQLITE, path=source_path),
                BackendConfig(backend_type=BackendType.SQLITE, path=target_path),
                export_path
            )

            assert result.valid is False
            assert any("not found in target" in err for err in result.errors)


class TestMigrationManagerRollback:
    """Test rollback functionality."""

    @pytest.mark.asyncio
    async def test_rollback_target_clears_data(self):
        """Test rollback deletes all data from target."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            target_path = os.path.join(tmpdir, "target.db")
            config = BackendConfig(backend_type=BackendType.SQLITE, path=target_path)

            # Create target with data
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = target_path
            backend = await manager._create_backend(config)
            db = SQLiteMemoryDatabase(backend)
            await db.initialize_schema()

            # Add memories and track IDs
            memory_ids = []
            for i in range(5):
                memory = Memory(
                    type=MemoryType.SOLUTION,
                    title=f"Memory {i}",
                    content=f"Content {i}",
                    importance=0.5
                )
                mem_id = await db.store_memory(memory)
                memory_ids.append(mem_id)

            await backend.disconnect()

            # Verify data exists before rollback
            backend = await manager._create_backend(config)
            db = SQLiteMemoryDatabase(backend)
            from src.memorygraph.models import SearchQuery
            query = SearchQuery(query="", limit=1000, offset=0, match_mode="any")
            memories_before = await db.search_memories(query)
            assert len(memories_before) == 5
            await backend.disconnect()

            # Rollback should clear all data
            await manager._rollback_target(config)

            # Verify target is empty
            backend = await manager._create_backend(config)
            db = SQLiteMemoryDatabase(backend)
            query = SearchQuery(query="", limit=1000, offset=0, match_mode="any")
            memories_after = await db.search_memories(query)

            # Rollback uses delete_memory which should work
            assert len(memories_after) == 0, f"Expected 0 memories after rollback, got {len(memories_after)}"

            await backend.disconnect()


class TestMigrationManagerHelpers:
    """Test helper methods."""

    @pytest.mark.asyncio
    async def test_count_memories_with_pagination(self):
        """Test counting memories using pagination."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = db_path

            backend = SQLiteFallbackBackend(db_path)
            await backend.connect()
            await backend.initialize_schema()
            db = SQLiteMemoryDatabase(backend)
            await db.initialize_schema()

            # Add 15 memories
            for i in range(15):
                memory = Memory(
                    type=MemoryType.SOLUTION,
                    title=f"Memory {i}",
                    content=f"Content {i}",
                    importance=0.5
                )
                await db.store_memory(memory)

            count = await manager._count_memories(db)
            assert count == 15

            await backend.disconnect()

    @pytest.mark.asyncio
    async def test_count_relationships_deduplication(self):
        """Test relationship counting with deduplication."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = db_path

            backend = SQLiteFallbackBackend(db_path)
            await backend.connect()
            await backend.initialize_schema()
            db = SQLiteMemoryDatabase(backend)
            await db.initialize_schema()

            # Create 2 memories with relationship
            mem1 = Memory(
                type=MemoryType.SOLUTION,
                title="Solution",
                content="Content",
                importance=0.5
            )
            mem1_id = await db.store_memory(mem1)

            mem2 = Memory(
                type=MemoryType.PROBLEM,
                title="Problem",
                content="Content",
                importance=0.5
            )
            mem2_id = await db.store_memory(mem2)

            await db.create_relationship(
                from_memory_id=mem1_id,
                to_memory_id=mem2_id,
                relationship_type=RelationshipType.SOLVES,
                properties=RelationshipProperties()
            )

            count = await manager._count_relationships(db)
            assert count == 1

            await backend.disconnect()

    @pytest.mark.asyncio
    async def test_get_random_sample(self):
        """Test random sampling of memories."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = db_path

            backend = SQLiteFallbackBackend(db_path)
            await backend.connect()
            await backend.initialize_schema()
            db = SQLiteMemoryDatabase(backend)
            await db.initialize_schema()

            # Add 20 memories
            for i in range(20):
                memory = Memory(
                    type=MemoryType.SOLUTION,
                    title=f"Memory {i}",
                    content=f"Content {i}",
                    importance=0.5
                )
                await db.store_memory(memory)

            # Get sample of 10
            sample = await manager._get_random_sample(db, 10)
            assert len(sample) == 10

            # Get sample larger than available
            sample_all = await manager._get_random_sample(db, 50)
            assert len(sample_all) == 20

            await backend.disconnect()

    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self):
        """Test cleanup of temporary files and directories."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / "migration_temp"
            temp_dir.mkdir()
            export_path = temp_dir / "export.json"
            export_path.write_text("{}")

            assert export_path.exists()
            assert temp_dir.exists()

            await manager._cleanup_temp_files(export_path)

            assert not export_path.exists()
            assert not temp_dir.exists()  # Empty dir should be removed

    def test_report_progress(self, caplog):
        """Test progress reporting callback."""
        import logging
        manager = MigrationManager()

        # Set log level to INFO to capture progress messages
        with caplog.at_level(logging.INFO):
            manager._report_progress(50, 100)

        assert "Progress: 50/100 (50.0%)" in caplog.text


class TestMigrationManagerBackendCreation:
    """Test backend creation error paths."""

    @pytest.mark.asyncio
    async def test_create_backend_invalid_type(self):
        """Test backend creation with invalid type."""
        manager = MigrationManager()

        # Create config with unsupported backend (if any)
        config = BackendConfig(
            backend_type=BackendType.NEO4J,
            uri="bolt://nonexistent:7687",
            username="neo4j",
            password="password"
        )

        with pytest.raises(MigrationError):
            await manager._create_backend(config)

    @pytest.mark.asyncio
    async def test_create_backend_restores_environment(self):
        """Test that backend creation restores environment variables."""
        manager = MigrationManager()

        original_backend = os.getenv("MEMORY_BACKEND")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            config = BackendConfig(backend_type=BackendType.SQLITE, path=db_path)

            backend = await manager._create_backend(config)
            await backend.disconnect()

            # Environment should be restored
            assert os.getenv("MEMORY_BACKEND") == original_backend


class TestMigrationManagerIntegration:
    """Integration tests for complete migration scenarios."""

    @pytest.mark.asyncio
    async def test_migration_with_verification_failure_and_rollback(self):
        """Test that verification failure triggers rollback."""
        manager = MigrationManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, "source.db")
            target_path = os.path.join(tmpdir, "target.db")

            # Create source with data
            os.environ["MEMORY_BACKEND"] = "sqlite"
            os.environ["MEMORY_SQLITE_PATH"] = source_path
            source_backend = await manager._create_backend(
                BackendConfig(backend_type=BackendType.SQLITE, path=source_path)
            )
            source_db = SQLiteMemoryDatabase(source_backend)
            await source_db.initialize_schema()

            memory = Memory(
                type=MemoryType.SOLUTION,
                title="Test",
                content="Content",
                importance=0.5
            )
            await source_db.store_memory(memory)
            await source_backend.disconnect()

            # Prepare configs
            source_config = BackendConfig(backend_type=BackendType.SQLITE, path=source_path)
            target_config = BackendConfig(backend_type=BackendType.SQLITE, path=target_path)

            # Mock verification to fail
            with patch.object(manager, '_verify_migration') as mock_verify:
                mock_verify.return_value = VerificationResult(
                    valid=False,
                    errors=["Verification failed intentionally"],
                    source_count=1,
                    target_count=0
                )

                options = MigrationOptions(
                    verify=True,
                    rollback_on_failure=True
                )

                result = await manager.migrate(source_config, target_config, options)

                # Migration should fail
                assert result.success is False
                assert "Verification failed" in result.errors[0]
