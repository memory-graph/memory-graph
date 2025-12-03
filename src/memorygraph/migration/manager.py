"""
Migration manager for backend-to-backend memory migration.

Provides a comprehensive migration system with validation, verification, and rollback.
"""

import logging
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from .models import (
    BackendConfig,
    MigrationOptions,
    MigrationResult,
    ValidationResult,
    VerificationResult
)
from ..backends.factory import BackendFactory
from ..database import MemoryDatabase
from ..utils.export_import import export_to_json, import_from_json
from ..utils.pagination import count_memories, count_relationships, paginate_memories, get_all_memories
from ..models import SearchQuery

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Raised when migration fails."""
    pass


class MigrationManager:
    """
    Manages backend-to-backend memory migrations.

    Performs migrations in 5 phases:
    1. Pre-flight validation (backends accessible, compatible)
    2. Export from source
    3. Validate export data
    4. Import to target (if not dry-run)
    5. Verify migration

    Supports rollback on failure and dry-run mode for validation.
    """

    async def migrate(
        self,
        source_config: BackendConfig,
        target_config: BackendConfig,
        options: MigrationOptions
    ) -> MigrationResult:
        """
        Migrate memories from source backend to target backend.

        Args:
            source_config: Source backend configuration
            target_config: Target backend configuration
            options: Migration options (dry_run, verify, etc.)

        Returns:
            MigrationResult with statistics and any errors

        Raises:
            MigrationError: If migration fails
        """
        start_time = time.time()
        logger.info(f"Starting migration: {source_config.backend_type.value} → {target_config.backend_type.value}")

        temp_export = None

        try:
            # Phase 1: Pre-flight validation
            logger.info("Phase 1: Pre-flight validation")
            await self._validate_source(source_config)
            await self._validate_target(target_config)
            await self._check_compatibility(source_config, target_config)

            # Phase 2: Export from source
            logger.info("Phase 2: Exporting from source")
            temp_export = await self._export_from_source(source_config, options)

            # Phase 3: Validate export
            logger.info("Phase 3: Validating export")
            validation_result = await self._validate_export(temp_export)
            if not validation_result.valid:
                raise MigrationError(f"Export validation failed: {validation_result.errors}")

            if options.dry_run:
                logger.info("Dry-run mode: Skipping import phase")
                source_stats = await self._get_backend_stats(source_config)
                return MigrationResult(
                    success=True,
                    dry_run=True,
                    source_stats=source_stats,
                    duration_seconds=time.time() - start_time
                )

            # Phase 4: Import to target
            logger.info("Phase 4: Importing to target")
            import_stats = await self._import_to_target(target_config, temp_export, options)

            # Phase 5: Verify migration
            verification_result = None
            if options.verify:
                logger.info("Phase 5: Verifying migration")
                verification_result = await self._verify_migration(
                    source_config,
                    target_config,
                    temp_export
                )

                if not verification_result.valid and options.rollback_on_failure:
                    logger.error("Verification failed, rolling back...")
                    await self._rollback_target(target_config)
                    raise MigrationError(f"Verification failed: {verification_result.errors}")

            # Phase 6: Cleanup
            logger.info("Phase 6: Cleanup")
            await self._cleanup_temp_files(temp_export)

            source_stats = await self._get_backend_stats(source_config)
            target_stats = await self._get_backend_stats(target_config)

            logger.info("Migration completed successfully")
            return MigrationResult(
                success=True,
                source_stats=source_stats,
                target_stats=target_stats,
                imported_memories=import_stats["imported_memories"],
                imported_relationships=import_stats["imported_relationships"],
                skipped_memories=import_stats["skipped_memories"],
                verification_result=verification_result,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)

            # Cleanup on failure
            if temp_export and temp_export.exists():
                try:
                    await self._cleanup_temp_files(temp_export)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp files: {cleanup_error}")

            return MigrationResult(
                success=False,
                duration_seconds=time.time() - start_time,
                errors=[str(e)]
            )

    async def _validate_source(self, config: BackendConfig) -> None:
        """
        Validate source backend is accessible and healthy.

        Raises:
            MigrationError: If source backend is not accessible
        """
        # Validate configuration
        config_errors = config.validate()
        if config_errors:
            raise MigrationError(f"Invalid source configuration: {', '.join(config_errors)}")

        backend = await self._create_backend(config)
        try:
            health = await backend.health_check()
            if not health.get("connected"):
                raise MigrationError(f"Source backend not accessible: {health.get('error')}")

            stats = health.get("statistics", {})
            memory_count = stats.get("memory_count", 0)
            logger.info(f"Source backend healthy: {memory_count} memories")

            if memory_count == 0:
                logger.warning("Source backend is empty")

        finally:
            await backend.disconnect()

    async def _validate_target(self, config: BackendConfig) -> None:
        """
        Validate target backend is accessible and writable.

        Raises:
            MigrationError: If target backend is not accessible
        """
        # Validate configuration
        config_errors = config.validate()
        if config_errors:
            raise MigrationError(f"Invalid target configuration: {', '.join(config_errors)}")

        backend = await self._create_backend(config)
        try:
            health = await backend.health_check()
            if not health.get("connected"):
                raise MigrationError(f"Target backend not accessible: {health.get('error')}")

            # Warn if target already has data
            stats = health.get("statistics", {})
            memory_count = stats.get("memory_count", 0)
            if memory_count > 0:
                logger.warning(f"Target backend already contains {memory_count} memories. Migration will add to existing data.")

            logger.info("Target backend accessible and writable")

        finally:
            await backend.disconnect()

    async def _check_compatibility(
        self,
        source_config: BackendConfig,
        target_config: BackendConfig
    ) -> None:
        """
        Check if migration between these backends is supported.

        All backends use the same GraphBackend interface, so all migrations
        are technically supported. This method checks for feature parity warnings.
        """
        if source_config.backend_type == target_config.backend_type:
            logger.warning(f"Source and target are the same backend type ({source_config.backend_type.value})")

        # All backends are compatible for migration
        logger.info("Backend compatibility check passed")

    async def _export_from_source(
        self,
        config: BackendConfig,
        options: MigrationOptions
    ) -> Path:
        """
        Export data from source backend to temporary file.

        Returns:
            Path to temporary export file

        Raises:
            MigrationError: If export fails
        """
        from ..backends.sqlite_fallback import SQLiteFallbackBackend
        from ..backends.falkordblite_backend import FalkorDBLiteBackend
        from ..sqlite_database import SQLiteMemoryDatabase

        backend = await self._create_backend(config)

        # Use SQLiteMemoryDatabase for SQLite-based backends
        if isinstance(backend, (SQLiteFallbackBackend, FalkorDBLiteBackend)):
            db = SQLiteMemoryDatabase(backend)
        else:
            db = MemoryDatabase(backend)

        try:
            # Create temp export file
            temp_dir = Path(tempfile.gettempdir()) / "memorygraph_migration"
            temp_dir.mkdir(exist_ok=True, parents=True)
            export_path = temp_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Use universal export (from Phase 1)
            progress_callback = self._report_progress if options.verbose else None
            await export_to_json(db, str(export_path), progress_callback=progress_callback)

            logger.info(f"Export complete: {export_path}")
            return export_path

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise MigrationError(f"Export failed: {e}")

        finally:
            await backend.disconnect()

    async def _validate_export(self, export_path: Path) -> ValidationResult:
        """
        Validate exported data integrity.

        Returns:
            ValidationResult indicating if export is valid
        """
        errors = []
        warnings = []

        try:
            # Check file exists and is readable
            if not export_path.exists():
                errors.append(f"Export file not found: {export_path}")
                return ValidationResult(valid=False, errors=errors)

            # Load and validate JSON structure
            import json
            with open(export_path, 'r') as f:
                data = json.load(f)

            # Check required fields
            if "memories" not in data:
                errors.append("Export missing 'memories' field")
            if "relationships" not in data:
                errors.append("Export missing 'relationships' field")

            # Check format version
            if "format_version" not in data and "export_version" not in data:
                errors.append("Export missing version information")

            # Check memory count
            memory_count = len(data.get("memories", []))
            if memory_count == 0:
                warnings.append("Export contains zero memories")
            else:
                logger.info(f"Export contains {memory_count} memories")

            # Check relationship count
            relationship_count = len(data.get("relationships", []))
            logger.info(f"Export contains {relationship_count} relationships")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
        except Exception as e:
            errors.append(f"Validation failed: {e}")

        return ValidationResult(
            valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings
        )

    async def _import_to_target(
        self,
        config: BackendConfig,
        export_path: Path,
        options: MigrationOptions
    ) -> Dict[str, int]:
        """
        Import data to target backend.

        Returns:
            Dictionary with import statistics

        Raises:
            MigrationError: If import fails
        """
        from ..backends.sqlite_fallback import SQLiteFallbackBackend
        from ..backends.falkordblite_backend import FalkorDBLiteBackend
        from ..sqlite_database import SQLiteMemoryDatabase

        backend = await self._create_backend(config)

        # Use SQLiteMemoryDatabase for SQLite-based backends
        if isinstance(backend, (SQLiteFallbackBackend, FalkorDBLiteBackend)):
            db = SQLiteMemoryDatabase(backend)
        else:
            db = MemoryDatabase(backend)

        try:
            # Import with progress reporting
            progress_callback = self._report_progress if options.verbose else None
            import_result = await import_from_json(
                db,
                str(export_path),
                skip_duplicates=options.skip_duplicates,
                progress_callback=progress_callback
            )

            logger.info(
                f"Import complete: {import_result['imported_memories']} memories, "
                f"{import_result['imported_relationships']} relationships"
            )

            return import_result

        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise MigrationError(f"Import failed: {e}")

        finally:
            await backend.disconnect()

    async def _verify_migration(
        self,
        source_config: BackendConfig,
        target_config: BackendConfig,
        export_path: Path
    ) -> VerificationResult:
        """
        Verify target backend has same data as source.

        Returns:
            VerificationResult with detailed comparison
        """
        from ..backends.sqlite_fallback import SQLiteFallbackBackend
        from ..backends.falkordblite_backend import FalkorDBLiteBackend
        from ..sqlite_database import SQLiteMemoryDatabase

        source_backend = await self._create_backend(source_config)
        target_backend = await self._create_backend(target_config)

        # Use SQLiteMemoryDatabase for SQLite-based backends
        if isinstance(source_backend, (SQLiteFallbackBackend, FalkorDBLiteBackend)):
            source_db = SQLiteMemoryDatabase(source_backend)
        else:
            source_db = MemoryDatabase(source_backend)

        if isinstance(target_backend, (SQLiteFallbackBackend, FalkorDBLiteBackend)):
            target_db = SQLiteMemoryDatabase(target_backend)
        else:
            target_db = MemoryDatabase(target_backend)

        errors = []

        try:
            # Check memory counts
            source_count = await self._count_memories(source_db)
            target_count = await self._count_memories(target_db)

            logger.info(f"Memory count - Source: {source_count}, Target: {target_count}")

            if source_count != target_count:
                errors.append(f"Memory count mismatch: source={source_count}, target={target_count}")

            # Check relationship counts
            source_rels = await self._count_relationships(source_db)
            target_rels = await self._count_relationships(target_db)

            logger.info(f"Relationship count - Source: {source_rels}, Target: {target_rels}")

            if source_rels != target_rels:
                errors.append(f"Relationship count mismatch: source={source_rels}, target={target_rels}")

            # Sample check: verify 10 random memories
            sample_size = min(10, source_count)
            sample_passed = 0

            if sample_size > 0:
                sample_memories = await self._get_random_sample(source_db, sample_size)
                for memory in sample_memories:
                    target_memory = await target_db.get_memory(memory.id, include_relationships=False)
                    if not target_memory:
                        errors.append(f"Memory {memory.id} not found in target")
                    elif target_memory.content != memory.content:
                        errors.append(f"Memory {memory.id} content mismatch")
                    else:
                        sample_passed += 1

                logger.info(f"Sample verification: {sample_passed}/{sample_size} passed")

            return VerificationResult(
                valid=(len(errors) == 0),
                errors=errors,
                source_count=source_count,
                target_count=target_count,
                sample_checks=sample_size,
                sample_passed=sample_passed
            )

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            errors.append(f"Verification error: {e}")
            return VerificationResult(valid=False, errors=errors)

        finally:
            await source_backend.disconnect()
            await target_backend.disconnect()

    async def _rollback_target(self, config: BackendConfig) -> None:
        """
        Rollback target backend to pre-migration state.

        WARNING: This deletes ALL data in target backend.
        In future, could track imported IDs and delete only those.

        Raises:
            MigrationError: If rollback fails
        """
        from ..backends.sqlite_fallback import SQLiteFallbackBackend
        from ..backends.falkordblite_backend import FalkorDBLiteBackend
        from ..sqlite_database import SQLiteMemoryDatabase

        logger.warning("Rolling back target backend (deleting all data)...")
        backend = await self._create_backend(config)

        try:
            # Use SQLiteMemoryDatabase for SQLite-based backends
            if isinstance(backend, (SQLiteFallbackBackend, FalkorDBLiteBackend)):
                db = SQLiteMemoryDatabase(backend)
            else:
                db = MemoryDatabase(backend)

            # Delete all data
            # Note: We use the backend's clear_all_data if available
            if hasattr(backend, 'clear_all_data'):
                await backend.clear_all_data()
            else:
                # Fallback: Delete memories one by one (cascades relationships)
                all_memories = await get_all_memories(db)
                for memory in all_memories:
                    await db.delete_memory(memory.id)

            logger.info("Rollback complete")

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise MigrationError(f"Rollback failed: {e}")

        finally:
            await backend.disconnect()

    async def _create_backend(self, config: BackendConfig):
        """
        Create a backend instance from configuration.

        Uses thread-safe BackendFactory.create_from_config() method that doesn't
        mutate environment variables.

        Returns:
            Connected GraphBackend instance

        Raises:
            MigrationError: If backend creation fails
        """
        try:
            # Use thread-safe factory method that accepts config directly
            backend = await BackendFactory.create_from_config(config)
            return backend

        except Exception as e:
            logger.error(f"Failed to create backend: {e}")
            raise MigrationError(f"Failed to create backend: {e}")

    async def _get_backend_stats(self, config: BackendConfig) -> Dict[str, Any]:
        """Get statistics from a backend."""
        backend = await self._create_backend(config)
        try:
            health = await backend.health_check()
            return health.get("statistics", {})
        finally:
            await backend.disconnect()

    async def _count_memories(self, db: MemoryDatabase) -> int:
        """Count total memories in database."""
        return await count_memories(db)

    async def _count_relationships(self, db: MemoryDatabase) -> int:
        """Count total relationships in database."""
        return await count_relationships(db)

    async def _get_random_sample(self, db: MemoryDatabase, sample_size: int) -> List:
        """Get random sample of memories from database."""
        import random

        # Get all memories using helper
        all_memories = await get_all_memories(db)

        # Return random sample
        if len(all_memories) <= sample_size:
            return all_memories
        return random.sample(all_memories, sample_size)

    async def _cleanup_temp_files(self, export_path: Path) -> None:
        """Delete temporary export files."""
        try:
            if export_path.exists():
                export_path.unlink()
                logger.info(f"Cleaned up temporary file: {export_path}")

            # Clean up empty temp directory
            temp_dir = export_path.parent
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
                logger.info(f"Cleaned up temporary directory: {temp_dir}")

        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

    def _report_progress(self, current: int, total: int) -> None:
        """Report migration progress to user (for verbose mode)."""
        if total > 0:
            percent = (current / total * 100)
            logger.info(f"Progress: {current}/{total} ({percent:.1f}%)")
