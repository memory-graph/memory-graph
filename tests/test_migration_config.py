"""
Tests for Migration Module Config Integration (WP33 Phase 3).

This test suite verifies that BackendConfig.from_env() in the migration module
reads configuration from the Config class instead of calling os.getenv() directly.

These tests follow TDD RED phase - they MUST fail against the current implementation
that uses os.getenv() in the from_env() classmethod.

Current os.getenv() calls to replace in migration/models.py BackendConfig.from_env():
1. Line 40: backend_str = os.getenv("MEMORY_BACKEND", "sqlite")
2. Lines 50-52: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (with fallbacks)
3. Lines 55-57: MEMGRAPH_URI, MEMGRAPH_USER, MEMGRAPH_PASSWORD
4. Lines 61-64: FALKORDB_HOST, FALKORDB_PORT, FALKORDB_PASSWORD (with fallbacks)
5. Line 67: SQLITE_PATH
6. Line 70: FALKORDBLITE_PATH (with fallback)

Pattern:
- Set Config attribute to one value
- Set os.environ to a DIFFERENT value
- BackendConfig.from_env() should use Config value (not env var)

After refactoring, BackendConfig.from_env() will read from Config, making Config
the single source of truth for all configuration.
"""

import os
import pytest
from memorygraph.config import Config, BackendType
from memorygraph.migration.models import BackendConfig

from tests.conftest import patch_config


class TestBackendConfigReadsBackendType:
    """
    Tests that BackendConfig.from_env() reads backend type from Config.BACKEND.

    Current implementation (migration/models.py line 40):
        backend_str = os.getenv("MEMORY_BACKEND", "sqlite")

    Expected after refactor:
        backend_str = Config.BACKEND
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables around each test."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_reads_config_backend_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.BACKEND, not os.getenv("MEMORY_BACKEND").

        MUST FAIL: Current migration/models.py line 40 uses os.getenv()
        """
        # Set Config to neo4j
        with patch_config(
            BACKEND="neo4j",
            NEO4J_URI="bolt://localhost:7687",
            NEO4J_USER="neo4j",
            NEO4J_PASSWORD="test-pass"
        ):
            # Set env var to different backend
            os.environ["MEMORY_BACKEND"] = "sqlite"

            # Create config from environment
            config = BackendConfig.from_env()

            # WILL FAIL: current code returns BackendType.SQLITE from os.getenv()
            # Expected: BackendType.NEO4J from Config.BACKEND
            assert config.backend_type == BackendType.NEO4J, (
                f"Expected Config.BACKEND 'neo4j', "
                f"got '{config.backend_type.value}' from os.getenv()"
            )

    def test_from_env_reads_config_backend_sqlite(self):
        """
        BackendConfig.from_env() should read Config.BACKEND for SQLite backend.

        MUST FAIL: Current implementation uses os.getenv()
        """
        with patch_config(
            BACKEND="sqlite",
            SQLITE_PATH="/config/memory.db"
        ):
            os.environ["MEMORY_BACKEND"] = "neo4j"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns BackendType.NEO4J from os.getenv()
            assert config.backend_type == BackendType.SQLITE, (
                f"Expected Config.BACKEND 'sqlite', "
                f"got '{config.backend_type.value}' from os.getenv()"
            )


class TestBackendConfigReadsNeo4jConfig:
    """
    Tests that BackendConfig.from_env() reads Neo4j config from Config class.

    Current implementation (migration/models.py lines 50-52):
        uri = os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

    Expected after refactor:
        uri = Config.NEO4J_URI
        username = Config.NEO4J_USER
        password = Config.NEO4J_PASSWORD
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_neo4j_reads_config_uri_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.NEO4J_URI for Neo4j backend.

        MUST FAIL: Current migration/models.py line 50 uses os.getenv()
        """
        with patch_config(
            BACKEND="neo4j",
            NEO4J_URI="bolt://config-neo4j:7687",
            NEO4J_USER="neo4j",
            NEO4J_PASSWORD="config-password"
        ):
            # Set env vars to different values
            os.environ["MEMORY_NEO4J_URI"] = "bolt://env-neo4j:7687"
            os.environ["NEO4J_URI"] = "bolt://env-neo4j-fallback:7687"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "bolt://env-neo4j:7687" from os.getenv()
            assert config.uri == "bolt://config-neo4j:7687", (
                f"Expected Config.NEO4J_URI 'bolt://config-neo4j:7687', "
                f"got '{config.uri}' from os.getenv()"
            )

    def test_from_env_neo4j_reads_config_user_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.NEO4J_USER for Neo4j backend.

        MUST FAIL: Current migration/models.py line 51 uses os.getenv()
        """
        with patch_config(
            BACKEND="neo4j",
            NEO4J_URI="bolt://localhost:7687",
            NEO4J_USER="config-user",
            NEO4J_PASSWORD="test-pass"
        ):
            os.environ["MEMORY_NEO4J_USER"] = "env-user"
            os.environ["NEO4J_USER"] = "env-user-fallback"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "env-user" from os.getenv()
            assert config.username == "config-user", (
                f"Expected Config.NEO4J_USER 'config-user', "
                f"got '{config.username}' from os.getenv()"
            )

    def test_from_env_neo4j_reads_config_password_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.NEO4J_PASSWORD for Neo4j backend.

        MUST FAIL: Current migration/models.py line 52 uses os.getenv()
        """
        with patch_config(
            BACKEND="neo4j",
            NEO4J_URI="bolt://localhost:7687",
            NEO4J_USER="neo4j",
            NEO4J_PASSWORD="config-secret-123"
        ):
            os.environ["MEMORY_NEO4J_PASSWORD"] = "env-secret-456"
            os.environ["NEO4J_PASSWORD"] = "env-secret-fallback"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "env-secret-456" from os.getenv()
            assert config.password == "config-secret-123", (
                f"Expected Config.NEO4J_PASSWORD 'config-secret-123', "
                f"got '{config.password}' from os.getenv()"
            )


class TestBackendConfigReadsMemgraphConfig:
    """
    Tests that BackendConfig.from_env() reads Memgraph config from Config class.

    Current implementation (migration/models.py lines 55-57):
        uri = os.getenv("MEMORY_MEMGRAPH_URI", "bolt://localhost:7687")
        username = os.getenv("MEMORY_MEMGRAPH_USER", "")
        password = os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

    Expected after refactor:
        uri = Config.MEMGRAPH_URI
        username = Config.MEMGRAPH_USER
        password = Config.MEMGRAPH_PASSWORD
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_memgraph_reads_config_uri_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.MEMGRAPH_URI for Memgraph backend.

        MUST FAIL: Current migration/models.py line 55 uses os.getenv()
        """
        with patch_config(
            BACKEND="memgraph",
            MEMGRAPH_URI="bolt://config-memgraph:7688",
            MEMGRAPH_USER="config-user",
            MEMGRAPH_PASSWORD="config-pass"
        ):
            os.environ["MEMORY_MEMGRAPH_URI"] = "bolt://env-memgraph:7688"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "bolt://env-memgraph:7688" from os.getenv()
            assert config.uri == "bolt://config-memgraph:7688", (
                f"Expected Config.MEMGRAPH_URI 'bolt://config-memgraph:7688', "
                f"got '{config.uri}' from os.getenv()"
            )

    def test_from_env_memgraph_reads_config_user_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.MEMGRAPH_USER for Memgraph backend.

        MUST FAIL: Current migration/models.py line 56 uses os.getenv()
        """
        with patch_config(
            BACKEND="memgraph",
            MEMGRAPH_URI="bolt://localhost:7688",
            MEMGRAPH_USER="config-memgraph-user",
            MEMGRAPH_PASSWORD=""
        ):
            os.environ["MEMORY_MEMGRAPH_USER"] = "env-memgraph-user"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "env-memgraph-user" from os.getenv()
            assert config.username == "config-memgraph-user", (
                f"Expected Config.MEMGRAPH_USER 'config-memgraph-user', "
                f"got '{config.username}' from os.getenv()"
            )

    def test_from_env_memgraph_reads_config_password_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.MEMGRAPH_PASSWORD for Memgraph backend.

        MUST FAIL: Current migration/models.py line 57 uses os.getenv()
        """
        with patch_config(
            BACKEND="memgraph",
            MEMGRAPH_URI="bolt://localhost:7688",
            MEMGRAPH_USER="",
            MEMGRAPH_PASSWORD="config-memgraph-secret"
        ):
            os.environ["MEMORY_MEMGRAPH_PASSWORD"] = "env-memgraph-secret"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "env-memgraph-secret" from os.getenv()
            assert config.password == "config-memgraph-secret", (
                f"Expected Config.MEMGRAPH_PASSWORD 'config-memgraph-secret', "
                f"got '{config.password}' from os.getenv()"
            )


class TestBackendConfigReadsFalkorDBConfig:
    """
    Tests that BackendConfig.from_env() reads FalkorDB config from Config class.

    Current implementation (migration/models.py lines 61-64):
        host = os.getenv("MEMORY_FALKORDB_HOST") or os.getenv("FALKORDB_HOST", "localhost")
        port = os.getenv("MEMORY_FALKORDB_PORT") or os.getenv("FALKORDB_PORT", "6379")
        uri = f"redis://{host}:{port}"
        password = os.getenv("MEMORY_FALKORDB_PASSWORD") or os.getenv("FALKORDB_PASSWORD")

    Expected after refactor:
        host = Config.FALKORDB_HOST or "localhost"
        port = Config.FALKORDB_PORT or 6379
        uri = f"redis://{host}:{port}"
        password = Config.FALKORDB_PASSWORD
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_falkordb_reads_config_host_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.FALKORDB_HOST for FalkorDB backend.

        MUST FAIL: Current migration/models.py line 61 uses os.getenv()
        """
        with patch_config(
            BACKEND="falkordb",
            FALKORDB_HOST="config-falkordb-host",
            FALKORDB_PORT=7000,
            FALKORDB_PASSWORD="config-pass"
        ):
            os.environ["MEMORY_FALKORDB_HOST"] = "env-falkordb-host"
            os.environ["FALKORDB_HOST"] = "env-falkordb-fallback"

            config = BackendConfig.from_env()

            # WILL FAIL: current code constructs URI from os.getenv() host
            # Expected: redis://config-falkordb-host:7000
            # Actual: redis://env-falkordb-host:7000
            assert config.uri == "redis://config-falkordb-host:7000", (
                f"Expected URI with Config.FALKORDB_HOST 'redis://config-falkordb-host:7000', "
                f"got '{config.uri}' from os.getenv()"
            )

    def test_from_env_falkordb_reads_config_port_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.FALKORDB_PORT for FalkorDB backend.

        MUST FAIL: Current migration/models.py line 62 uses os.getenv()
        """
        with patch_config(
            BACKEND="falkordb",
            FALKORDB_HOST="localhost",
            FALKORDB_PORT=7777,
            FALKORDB_PASSWORD="test"
        ):
            os.environ["MEMORY_FALKORDB_PORT"] = "8888"
            os.environ["FALKORDB_PORT"] = "9999"

            config = BackendConfig.from_env()

            # WILL FAIL: current code constructs URI from os.getenv() port
            # Expected: redis://localhost:7777
            # Actual: redis://localhost:8888
            assert config.uri == "redis://localhost:7777", (
                f"Expected URI with Config.FALKORDB_PORT 'redis://localhost:7777', "
                f"got '{config.uri}' from os.getenv()"
            )

    def test_from_env_falkordb_reads_config_password_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.FALKORDB_PASSWORD for FalkorDB backend.

        MUST FAIL: Current migration/models.py line 64 uses os.getenv()
        """
        with patch_config(
            BACKEND="falkordb",
            FALKORDB_HOST="localhost",
            FALKORDB_PORT=6379,
            FALKORDB_PASSWORD="config-falkordb-secret"
        ):
            os.environ["MEMORY_FALKORDB_PASSWORD"] = "env-falkordb-secret"
            os.environ["FALKORDB_PASSWORD"] = "env-falkordb-fallback"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "env-falkordb-secret" from os.getenv()
            assert config.password == "config-falkordb-secret", (
                f"Expected Config.FALKORDB_PASSWORD 'config-falkordb-secret', "
                f"got '{config.password}' from os.getenv()"
            )


class TestBackendConfigReadsSQLiteConfig:
    """
    Tests that BackendConfig.from_env() reads SQLite config from Config class.

    Current implementation (migration/models.py line 67):
        path = os.getenv("MEMORY_SQLITE_PATH", os.path.expanduser("~/.memorygraph/memory.db"))

    Expected after refactor:
        path = Config.SQLITE_PATH
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_sqlite_reads_config_path_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.SQLITE_PATH for SQLite backend.

        MUST FAIL: Current migration/models.py line 67 uses os.getenv()
        """
        with patch_config(
            BACKEND="sqlite",
            SQLITE_PATH="/config/custom/memory.db"
        ):
            os.environ["MEMORY_SQLITE_PATH"] = "/env/wrong/memory.db"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "/env/wrong/memory.db" from os.getenv()
            assert config.path == "/config/custom/memory.db", (
                f"Expected Config.SQLITE_PATH '/config/custom/memory.db', "
                f"got '{config.path}' from os.getenv()"
            )


class TestBackendConfigReadsFalkorDBLiteConfig:
    """
    Tests that BackendConfig.from_env() reads FalkorDBLite config from Config class.

    Current implementation (migration/models.py line 70):
        path = os.getenv("MEMORY_FALKORDBLITE_PATH") or os.getenv("FALKORDBLITE_PATH", ...)

    Expected after refactor:
        path = Config.FALKORDBLITE_PATH or os.path.expanduser("~/.memorygraph/falkordblite.db")
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_falkordblite_reads_config_path_not_env_var(self):
        """
        BackendConfig.from_env() should read Config.FALKORDBLITE_PATH for FalkorDBLite backend.

        MUST FAIL: Current migration/models.py line 70 uses os.getenv()
        """
        with patch_config(
            BACKEND="falkordblite",
            FALKORDBLITE_PATH="/config/custom/falkordblite.db"
        ):
            os.environ["MEMORY_FALKORDBLITE_PATH"] = "/env/wrong/falkordblite.db"
            os.environ["FALKORDBLITE_PATH"] = "/env/wrong/fallback/falkordblite.db"

            config = BackendConfig.from_env()

            # WILL FAIL: current code returns "/env/wrong/falkordblite.db" from os.getenv()
            assert config.path == "/config/custom/falkordblite.db", (
                f"Expected Config.FALKORDBLITE_PATH '/config/custom/falkordblite.db', "
                f"got '{config.path}' from os.getenv()"
            )


class TestBackendConfigIntegration:
    """
    Integration tests verifying Config is the single source of truth for migration.

    These tests verify that changing Config values affects BackendConfig.from_env(),
    confirming consistent behavior across all backend types.
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_respects_config_changes_for_sqlite(self):
        """
        Changing Config.SQLITE_PATH should change BackendConfig.from_env().path for SQLite.

        This is an integration test verifying Config is the source of truth.
        """
        # Set conflicting env var
        os.environ["MEMORY_SQLITE_PATH"] = "/tmp/env/should/not/be/used.db"

        # First config with path 1
        with patch_config(BACKEND="sqlite", SQLITE_PATH="/tmp/first/config.db"):
            config1 = BackendConfig.from_env()
            # WILL FAIL if reads env var instead of Config
            assert config1.path == "/tmp/first/config.db"

        # Second config with path 2
        with patch_config(BACKEND="sqlite", SQLITE_PATH="/tmp/second/config.db"):
            config2 = BackendConfig.from_env()
            assert config2.path == "/tmp/second/config.db"

        # Paths should be different (proving Config controls behavior)
        assert config1.path != config2.path

    def test_from_env_respects_config_changes_for_neo4j(self):
        """
        Changing Config.NEO4J_* values should change BackendConfig.from_env() for Neo4j.
        """
        # Set conflicting env vars
        os.environ["MEMORY_NEO4J_URI"] = "bolt://env:7687"
        os.environ["MEMORY_NEO4J_USER"] = "env-user"
        os.environ["MEMORY_NEO4J_PASSWORD"] = "env-pass"

        # First config with credentials 1
        with patch_config(
            BACKEND="neo4j",
            NEO4J_URI="bolt://first:7687",
            NEO4J_USER="first-user",
            NEO4J_PASSWORD="first-pass"
        ):
            config1 = BackendConfig.from_env()
            assert config1.uri == "bolt://first:7687"
            assert config1.username == "first-user"
            assert config1.password == "first-pass"

        # Second config with credentials 2
        with patch_config(
            BACKEND="neo4j",
            NEO4J_URI="bolt://second:7687",
            NEO4J_USER="second-user",
            NEO4J_PASSWORD="second-pass"
        ):
            config2 = BackendConfig.from_env()
            assert config2.uri == "bolt://second:7687"
            assert config2.username == "second-user"
            assert config2.password == "second-pass"

        # Credentials should be different (proving Config controls behavior)
        assert config1.uri != config2.uri


class TestBackendConfigEdgeCases:
    """Test edge cases and boundary conditions for Config-based migration."""

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_handles_default_backend_from_config(self):
        """
        BackendConfig.from_env() should use Config.BACKEND's default when env not set.

        After refactor, Config.BACKEND determines default backend type.
        """
        # Explicitly set Config.BACKEND to avoid test pollution
        with patch_config(BACKEND="sqlite", SQLITE_PATH="/tmp/default.db"):
            # Clear env var
            os.environ.pop("MEMORY_BACKEND", None)

            # Config.BACKEND should be used
            config = BackendConfig.from_env()

            # Should match the explicitly set Config value
            assert config.backend_type == BackendType.SQLITE, (
                f"Expected backend 'sqlite' from Config.BACKEND, "
                f"got '{config.backend_type.value}'"
            )

    def test_from_env_handles_none_config_values(self):
        """
        BackendConfig.from_env() should handle None values in Config gracefully.

        Config values can be None; from_env() should apply appropriate defaults.
        """
        with patch_config(
            BACKEND="sqlite",
            SQLITE_PATH=None
        ):
            # Clear env var
            os.environ.pop("MEMORY_SQLITE_PATH", None)

            config = BackendConfig.from_env()

            # Should have backend type set
            assert config.backend_type == BackendType.SQLITE
            # Path might be None (depending on implementation)
            # This test documents behavior with None Config values


class TestBackendConfigMultipleBackends:
    """
    Tests verifying from_env() correctly handles all backend types.

    These tests ensure Config is consistently used across all backends.
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_all_backends_use_config_not_env(self):
        """
        All backend types should read from Config, not os.getenv().

        This comprehensive test verifies consistent Config usage.
        """
        # Set env vars that should NOT be used
        os.environ.update({
            "MEMORY_BACKEND": "sqlite",
            "MEMORY_SQLITE_PATH": "/env/wrong.db",
            "MEMORY_NEO4J_URI": "bolt://env:7687",
            "MEMORY_MEMGRAPH_URI": "bolt://env:7688",
            "MEMORY_FALKORDB_HOST": "env-host",
            "MEMORY_FALKORDBLITE_PATH": "/env/wrong/falkordblite.db"
        })

        # Test SQLite
        with patch_config(BACKEND="sqlite", SQLITE_PATH="/config/sqlite.db"):
            config = BackendConfig.from_env()
            # WILL FAIL if uses os.getenv()
            assert config.backend_type == BackendType.SQLITE
            assert config.path == "/config/sqlite.db"

        # Test Neo4j
        with patch_config(
            BACKEND="neo4j",
            NEO4J_URI="bolt://config:7687",
            NEO4J_USER="config-user",
            NEO4J_PASSWORD="config-pass"
        ):
            config = BackendConfig.from_env()
            assert config.backend_type == BackendType.NEO4J
            assert config.uri == "bolt://config:7687"

        # Test Memgraph
        with patch_config(
            BACKEND="memgraph",
            MEMGRAPH_URI="bolt://config:7688",
            MEMGRAPH_USER="",
            MEMGRAPH_PASSWORD=""
        ):
            config = BackendConfig.from_env()
            assert config.backend_type == BackendType.MEMGRAPH
            assert config.uri == "bolt://config:7688"

        # Test FalkorDB
        with patch_config(
            BACKEND="falkordb",
            FALKORDB_HOST="config-host",
            FALKORDB_PORT=6379,
            FALKORDB_PASSWORD=None
        ):
            config = BackendConfig.from_env()
            assert config.backend_type == BackendType.FALKORDB
            assert "config-host" in config.uri

        # Test FalkorDBLite
        with patch_config(
            BACKEND="falkordblite",
            FALKORDBLITE_PATH="/config/falkordblite.db"
        ):
            config = BackendConfig.from_env()
            assert config.backend_type == BackendType.FALKORDBLITE
            assert config.path == "/config/falkordblite.db"


# Tests for WP33 Phase 3 - Migration Config Refactor (TDD RED phase)
