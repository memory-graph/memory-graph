"""
Tests for migration data models.
"""

import os
import pytest
from unittest.mock import patch
from src.memorygraph.migration.models import (
    BackendType,
    BackendConfig,
    MigrationOptions,
    ValidationResult,
    VerificationResult,
    MigrationResult
)


class TestBackendConfig:
    """Tests for BackendConfig model."""

    def test_sqlite_config_validation(self):
        """Test SQLite config requires path."""
        config = BackendConfig(backend_type=BackendType.SQLITE)
        errors = config.validate()
        assert len(errors) > 0
        assert "path" in errors[0].lower()

    def test_sqlite_config_valid(self):
        """Test valid SQLite config."""
        config = BackendConfig(
            backend_type=BackendType.SQLITE,
            path="/tmp/test.db"
        )
        errors = config.validate()
        assert len(errors) == 0

    def test_neo4j_config_validation(self):
        """Test Neo4j config requires URI."""
        config = BackendConfig(backend_type=BackendType.NEO4J)
        errors = config.validate()
        assert len(errors) > 0
        assert "uri" in errors[0].lower()

    def test_neo4j_config_valid(self):
        """Test valid Neo4j config."""
        config = BackendConfig(
            backend_type=BackendType.NEO4J,
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        errors = config.validate()
        assert len(errors) == 0

    @patch.dict(os.environ, {
        "MEMORY_BACKEND": "sqlite",
        "MEMORY_SQLITE_PATH": "/tmp/test.db"
    }, clear=False)
    def test_from_env_sqlite(self):
        """Test creating config from environment for SQLite."""
        config = BackendConfig.from_env()
        assert config.backend_type == BackendType.SQLITE
        assert config.path == "/tmp/test.db"

    @patch.dict(os.environ, {
        "MEMORY_BACKEND": "neo4j",
        "MEMORY_NEO4J_URI": "bolt://localhost:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "password"
    }, clear=False)
    def test_from_env_neo4j(self):
        """Test creating config from environment for Neo4j."""
        config = BackendConfig.from_env()
        assert config.backend_type == BackendType.NEO4J
        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
        assert config.password == "password"


class TestMigrationOptions:
    """Tests for MigrationOptions model."""

    def test_default_options(self):
        """Test default migration options."""
        options = MigrationOptions()
        assert options.dry_run is False
        assert options.verbose is False
        assert options.skip_duplicates is True
        assert options.verify is True
        assert options.rollback_on_failure is True

    def test_custom_options(self):
        """Test custom migration options."""
        options = MigrationOptions(
            dry_run=True,
            verbose=True,
            skip_duplicates=False,
            verify=False,
            rollback_on_failure=False
        )
        assert options.dry_run is True
        assert options.verbose is True
        assert options.skip_duplicates is False
        assert options.verify is False
        assert options.rollback_on_failure is False


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_invalid_result(self):
        """Test invalid validation result."""
        result = ValidationResult(
            valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"]
        )
        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


class TestVerificationResult:
    """Tests for VerificationResult model."""

    def test_valid_verification(self):
        """Test valid verification result."""
        result = VerificationResult(
            valid=True,
            source_count=100,
            target_count=100,
            sample_checks=10,
            sample_passed=10
        )
        assert result.valid is True
        assert result.source_count == 100
        assert result.target_count == 100
        assert result.sample_checks == 10
        assert result.sample_passed == 10

    def test_invalid_verification(self):
        """Test invalid verification result."""
        result = VerificationResult(
            valid=False,
            errors=["Count mismatch"],
            source_count=100,
            target_count=95
        )
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.source_count == 100
        assert result.target_count == 95


class TestMigrationResult:
    """Tests for MigrationResult model."""

    def test_successful_migration(self):
        """Test successful migration result."""
        result = MigrationResult(
            success=True,
            imported_memories=100,
            imported_relationships=200,
            skipped_memories=5,
            duration_seconds=10.5
        )
        assert result.success is True
        assert result.imported_memories == 100
        assert result.imported_relationships == 200
        assert result.skipped_memories == 5
        assert result.duration_seconds == 10.5

    def test_failed_migration(self):
        """Test failed migration result."""
        result = MigrationResult(
            success=False,
            errors=["Connection failed", "Timeout"],
            duration_seconds=5.0
        )
        assert result.success is False
        assert len(result.errors) == 2
        assert result.duration_seconds == 5.0

    def test_dry_run_migration(self):
        """Test dry-run migration result."""
        result = MigrationResult(
            success=True,
            dry_run=True,
            source_stats={"memory_count": 100},
            duration_seconds=2.0
        )
        assert result.success is True
        assert result.dry_run is True
        assert result.source_stats["memory_count"] == 100
