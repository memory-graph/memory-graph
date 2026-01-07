"""
Tests for Backend Classes Config Integration (WP33 Phase 2).

This test suite verifies that backend classes (Neo4jBackend, MemgraphBackend,
SQLiteFallbackBackend, TursoBackend) read configuration from the Config class
instead of calling os.getenv() directly.

These tests follow TDD RED phase - they MUST fail against the current implementation
that uses os.getenv() in __init__ methods.

Current os.getenv() calls to replace:
1. neo4j_backend.py lines 45-47: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
2. memgraph_backend.py lines 47-49: MEMGRAPH_URI, MEMGRAPH_USER, MEMGRAPH_PASSWORD
3. sqlite_fallback.py line 52: SQLITE_PATH
4. turso.py lines 66-68: TURSO_PATH, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN

Pattern:
- Set Config attribute to one value
- Set os.environ to a DIFFERENT value
- Backend __init__ should use Config value (not env var)

After refactoring, backends will read from Config in __init__, making Config
the single source of truth for all configuration.
"""

import os
import pytest
import importlib.util
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from memorygraph.config import Config
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

# Check for optional dependencies
HAS_NEO4J = importlib.util.find_spec("neo4j") is not None
HAS_MEMGRAPH = importlib.util.find_spec("mgclient") is not None
HAS_LIBSQL = importlib.util.find_spec("libsql_experimental") is not None


@contextmanager
def patch_config(**kwargs):
    """
    Context manager to temporarily patch Config attributes.

    Usage:
        with patch_config(NEO4J_URI="bolt://test:7687", NEO4J_PASSWORD="test"):
            backend = Neo4jBackend()
            assert backend.uri == "bolt://test:7687"

    Args:
        **kwargs: Config attributes to patch (e.g., NEO4J_URI="value")
    """
    original_values = {}
    for key, value in kwargs.items():
        if hasattr(Config, key):
            original_values[key] = getattr(Config, key)
        setattr(Config, key, value)

    try:
        yield
    finally:
        for key, value in original_values.items():
            setattr(Config, key, value)


class TestNeo4jBackendReadsConfig:
    """
    Tests that Neo4jBackend reads from Config class, not os.getenv().

    Current implementation (neo4j_backend.py lines 45-47):
        self.uri = uri or os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

    Expected after refactor:
        self.uri = uri or Config.NEO4J_URI
        self.user = user or Config.NEO4J_USER
        self.password = password or Config.NEO4J_PASSWORD
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables around each test."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    def test_neo4j_backend_reads_config_uri_not_env_var(self):
        """
        Neo4jBackend should read Config.NEO4J_URI, not os.getenv("MEMORY_NEO4J_URI").

        MUST FAIL: Current neo4j_backend.py line 45 uses os.getenv()
        """
        from memorygraph.backends.neo4j_backend import Neo4jBackend

        # Set Config to one URI
        with patch_config(
            NEO4J_URI="bolt://config-host:7687",
            NEO4J_USER="neo4j",
            NEO4J_PASSWORD="config-password"
        ):
            # Set env vars to different values
            os.environ["MEMORY_NEO4J_URI"] = "bolt://env-host:7687"
            os.environ["NEO4J_URI"] = "bolt://env-host-fallback:7687"
            os.environ["MEMORY_NEO4J_USER"] = "env-user"
            os.environ["NEO4J_USER"] = "env-user-fallback"
            os.environ["MEMORY_NEO4J_PASSWORD"] = "env-password"
            os.environ["NEO4J_PASSWORD"] = "env-password-fallback"

            # Create backend without explicit parameters (should use Config)
            backend = Neo4jBackend()

            # This assertion WILL FAIL with current implementation
            # Current code reads os.getenv(), returns "bolt://env-host:7687"
            # Expected: "bolt://config-host:7687" from Config
            assert backend.uri == "bolt://config-host:7687", (
                f"Expected Config.NEO4J_URI 'bolt://config-host:7687', "
                f"got '{backend.uri}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    def test_neo4j_backend_reads_config_user_not_env_var(self):
        """
        Neo4jBackend should read Config.NEO4J_USER, not os.getenv("MEMORY_NEO4J_USER").

        MUST FAIL: Current neo4j_backend.py line 46 uses os.getenv()
        """
        from memorygraph.backends.neo4j_backend import Neo4jBackend

        with patch_config(
            NEO4J_URI="bolt://localhost:7687",
            NEO4J_USER="config-user",
            NEO4J_PASSWORD="test-password"
        ):
            os.environ["MEMORY_NEO4J_USER"] = "env-user"
            os.environ["NEO4J_USER"] = "env-user-fallback"
            os.environ["MEMORY_NEO4J_PASSWORD"] = "test-password"

            backend = Neo4jBackend()

            # WILL FAIL: current code returns "env-user" from os.getenv()
            assert backend.user == "config-user", (
                f"Expected Config.NEO4J_USER 'config-user', "
                f"got '{backend.user}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    def test_neo4j_backend_reads_config_password_not_env_var(self):
        """
        Neo4jBackend should read Config.NEO4J_PASSWORD, not os.getenv("MEMORY_NEO4J_PASSWORD").

        MUST FAIL: Current neo4j_backend.py line 47 uses os.getenv()
        """
        from memorygraph.backends.neo4j_backend import Neo4jBackend

        with patch_config(
            NEO4J_URI="bolt://localhost:7687",
            NEO4J_USER="neo4j",
            NEO4J_PASSWORD="config-password-123"
        ):
            os.environ["MEMORY_NEO4J_PASSWORD"] = "env-password-456"
            os.environ["NEO4J_PASSWORD"] = "env-password-fallback"

            backend = Neo4jBackend()

            # WILL FAIL: current code returns "env-password-456" from os.getenv()
            assert backend.password == "config-password-123", (
                f"Expected Config.NEO4J_PASSWORD 'config-password-123', "
                f"got '{backend.password}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    def test_neo4j_backend_explicit_params_override_config(self):
        """
        Explicit __init__ parameters should still override Config values.

        This should PASS even with current implementation.
        After refactor, verify this behavior is preserved.
        """
        from memorygraph.backends.neo4j_backend import Neo4jBackend

        with patch_config(
            NEO4J_URI="bolt://config:7687",
            NEO4J_USER="config-user",
            NEO4J_PASSWORD="config-password"
        ):
            os.environ["MEMORY_NEO4J_URI"] = "bolt://env:7687"

            # Explicit parameters should take precedence
            backend = Neo4jBackend(
                uri="bolt://explicit:7687",
                user="explicit-user",
                password="explicit-password"
            )

            assert backend.uri == "bolt://explicit:7687"
            assert backend.user == "explicit-user"
            assert backend.password == "explicit-password"


class TestMemgraphBackendReadsConfig:
    """
    Tests that MemgraphBackend reads from Config class, not os.getenv().

    Current implementation (memgraph_backend.py lines 47-49):
        self.uri = uri or os.getenv("MEMORY_MEMGRAPH_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("MEMORY_MEMGRAPH_USER", "")
        self.password = password or os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

    Expected after refactor:
        self.uri = uri or Config.MEMGRAPH_URI
        self.user = user or Config.MEMGRAPH_USER
        self.password = password or Config.MEMGRAPH_PASSWORD
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.mark.skipif(not HAS_MEMGRAPH, reason="memgraph (mgclient) package not installed")
    def test_memgraph_backend_reads_config_uri_not_env_var(self):
        """
        MemgraphBackend should read Config.MEMGRAPH_URI, not os.getenv("MEMORY_MEMGRAPH_URI").

        MUST FAIL: Current memgraph_backend.py line 47 uses os.getenv()
        """
        from memorygraph.backends.memgraph_backend import MemgraphBackend

        with patch_config(
            MEMGRAPH_URI="bolt://config-memgraph:7688",
            MEMGRAPH_USER="config-user",
            MEMGRAPH_PASSWORD="config-pass"
        ):
            os.environ["MEMORY_MEMGRAPH_URI"] = "bolt://env-memgraph:7688"
            os.environ["MEMORY_MEMGRAPH_USER"] = "env-user"
            os.environ["MEMORY_MEMGRAPH_PASSWORD"] = "env-pass"

            backend = MemgraphBackend()

            # WILL FAIL: current code returns "bolt://env-memgraph:7688" from os.getenv()
            assert backend.uri == "bolt://config-memgraph:7688", (
                f"Expected Config.MEMGRAPH_URI 'bolt://config-memgraph:7688', "
                f"got '{backend.uri}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_MEMGRAPH, reason="memgraph (mgclient) package not installed")
    def test_memgraph_backend_reads_config_user_not_env_var(self):
        """
        MemgraphBackend should read Config.MEMGRAPH_USER, not os.getenv("MEMORY_MEMGRAPH_USER").

        MUST FAIL: Current memgraph_backend.py line 48 uses os.getenv()
        """
        from memorygraph.backends.memgraph_backend import MemgraphBackend

        with patch_config(
            MEMGRAPH_URI="bolt://localhost:7688",
            MEMGRAPH_USER="config-memgraph-user",
            MEMGRAPH_PASSWORD=""
        ):
            os.environ["MEMORY_MEMGRAPH_USER"] = "env-memgraph-user"

            backend = MemgraphBackend()

            # WILL FAIL: current code returns "env-memgraph-user" from os.getenv()
            assert backend.user == "config-memgraph-user", (
                f"Expected Config.MEMGRAPH_USER 'config-memgraph-user', "
                f"got '{backend.user}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_MEMGRAPH, reason="memgraph (mgclient) package not installed")
    def test_memgraph_backend_reads_config_password_not_env_var(self):
        """
        MemgraphBackend should read Config.MEMGRAPH_PASSWORD, not os.getenv("MEMORY_MEMGRAPH_PASSWORD").

        MUST FAIL: Current memgraph_backend.py line 49 uses os.getenv()
        """
        from memorygraph.backends.memgraph_backend import MemgraphBackend

        with patch_config(
            MEMGRAPH_URI="bolt://localhost:7688",
            MEMGRAPH_USER="",
            MEMGRAPH_PASSWORD="config-memgraph-secret"
        ):
            os.environ["MEMORY_MEMGRAPH_PASSWORD"] = "env-memgraph-secret"

            backend = MemgraphBackend()

            # WILL FAIL: current code returns "env-memgraph-secret" from os.getenv()
            assert backend.password == "config-memgraph-secret", (
                f"Expected Config.MEMGRAPH_PASSWORD 'config-memgraph-secret', "
                f"got '{backend.password}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_MEMGRAPH, reason="memgraph (mgclient) package not installed")
    def test_memgraph_backend_explicit_params_override_config(self):
        """
        Explicit __init__ parameters should override Config values.

        This should PASS even with current implementation.
        """
        from memorygraph.backends.memgraph_backend import MemgraphBackend

        with patch_config(
            MEMGRAPH_URI="bolt://config:7688",
            MEMGRAPH_USER="config-user",
            MEMGRAPH_PASSWORD="config-pass"
        ):
            os.environ["MEMORY_MEMGRAPH_URI"] = "bolt://env:7688"

            backend = MemgraphBackend(
                uri="bolt://explicit:7688",
                user="explicit-user",
                password="explicit-pass"
            )

            assert backend.uri == "bolt://explicit:7688"
            assert backend.user == "explicit-user"
            assert backend.password == "explicit-pass"


class TestSQLiteBackendReadsConfig:
    """
    Tests that SQLiteFallbackBackend reads from Config class, not os.getenv().

    Current implementation (sqlite_fallback.py line 52):
        resolved_path = db_path or os.getenv("MEMORY_SQLITE_PATH", default_path)

    Expected after refactor:
        resolved_path = db_path or Config.SQLITE_PATH
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_sqlite_backend_reads_config_path_not_env_var(self):
        """
        SQLiteFallbackBackend should read Config.SQLITE_PATH, not os.getenv("MEMORY_SQLITE_PATH").

        MUST FAIL: Current sqlite_fallback.py line 52 uses os.getenv()
        """
        with patch_config(SQLITE_PATH="/tmp/config/custom/memory.db"):
            os.environ["MEMORY_SQLITE_PATH"] = "/tmp/env/wrong/memory.db"

            backend = SQLiteFallbackBackend()

            # WILL FAIL: current code returns "/tmp/env/wrong/memory.db" from os.getenv()
            assert backend.db_path == "/tmp/config/custom/memory.db", (
                f"Expected Config.SQLITE_PATH '/tmp/config/custom/memory.db', "
                f"got '{backend.db_path}' from os.getenv()"
            )

    def test_sqlite_backend_explicit_path_overrides_config(self):
        """
        Explicit db_path parameter should override Config.SQLITE_PATH.

        This should PASS even with current implementation.
        """
        with patch_config(SQLITE_PATH="/tmp/config/memory.db"):
            os.environ["MEMORY_SQLITE_PATH"] = "/tmp/env/memory.db"

            backend = SQLiteFallbackBackend(db_path="/tmp/explicit/memory.db")

            assert backend.db_path == "/tmp/explicit/memory.db"

    def test_sqlite_backend_uses_config_default_when_no_env_var(self):
        """
        When no explicit path or env var, should use Config.SQLITE_PATH default.

        This verifies Config is the single source of truth for defaults.
        """
        # Clear env var
        os.environ.pop("MEMORY_SQLITE_PATH", None)

        # Config should have its default value
        expected_path = Config.SQLITE_PATH

        backend = SQLiteFallbackBackend()

        # Should match Config's default (which comes from Config initialization)
        assert backend.db_path == expected_path, (
            f"Expected Config.SQLITE_PATH default '{expected_path}', "
            f"got '{backend.db_path}'"
        )


class TestTursoBackendReadsConfig:
    """
    Tests that TursoBackend reads from Config class, not os.getenv().

    Current implementation (turso.py lines 66-68):
        self.db_path = db_path or os.getenv("MEMORY_TURSO_PATH", default_path)
        self.sync_url = sync_url or os.getenv("TURSO_DATABASE_URL")
        self.auth_token = auth_token or os.getenv("TURSO_AUTH_TOKEN")

    Expected after refactor:
        self.db_path = db_path or Config.TURSO_PATH
        self.sync_url = sync_url or Config.TURSO_DATABASE_URL
        self.auth_token = auth_token or Config.TURSO_AUTH_TOKEN
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.mark.skipif(not HAS_LIBSQL, reason="libsql-experimental package not installed")
    def test_turso_backend_reads_config_path_not_env_var(self):
        """
        TursoBackend should read Config.TURSO_PATH, not os.getenv("MEMORY_TURSO_PATH").

        MUST FAIL: Current turso.py line 66 uses os.getenv()
        """
        from memorygraph.backends.turso import TursoBackend

        with patch_config(
            TURSO_PATH="/config/turso/memory.db",
            TURSO_DATABASE_URL="libsql://config.turso.io",
            TURSO_AUTH_TOKEN="config-token-abc"
        ):
            os.environ["MEMORY_TURSO_PATH"] = "/env/turso/memory.db"
            os.environ["TURSO_DATABASE_URL"] = "libsql://env.turso.io"
            os.environ["TURSO_AUTH_TOKEN"] = "env-token-xyz"

            backend = TursoBackend()

            # WILL FAIL: current code returns "/env/turso/memory.db" from os.getenv()
            assert backend.db_path == "/config/turso/memory.db", (
                f"Expected Config.TURSO_PATH '/config/turso/memory.db', "
                f"got '{backend.db_path}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_LIBSQL, reason="libsql-experimental package not installed")
    def test_turso_backend_reads_config_sync_url_not_env_var(self):
        """
        TursoBackend should read Config.TURSO_DATABASE_URL, not os.getenv("TURSO_DATABASE_URL").

        MUST FAIL: Current turso.py line 67 uses os.getenv()
        """
        from memorygraph.backends.turso import TursoBackend

        with patch_config(
            TURSO_PATH=os.path.expanduser("~/.memorygraph/memory.db"),
            TURSO_DATABASE_URL="libsql://config-database.turso.io",
            TURSO_AUTH_TOKEN="token"
        ):
            os.environ["TURSO_DATABASE_URL"] = "libsql://env-database.turso.io"

            backend = TursoBackend()

            # WILL FAIL: current code returns "libsql://env-database.turso.io" from os.getenv()
            assert backend.sync_url == "libsql://config-database.turso.io", (
                f"Expected Config.TURSO_DATABASE_URL 'libsql://config-database.turso.io', "
                f"got '{backend.sync_url}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_LIBSQL, reason="libsql-experimental package not installed")
    def test_turso_backend_reads_config_auth_token_not_env_var(self):
        """
        TursoBackend should read Config.TURSO_AUTH_TOKEN, not os.getenv("TURSO_AUTH_TOKEN").

        MUST FAIL: Current turso.py line 68 uses os.getenv()
        """
        from memorygraph.backends.turso import TursoBackend

        with patch_config(
            TURSO_PATH=os.path.expanduser("~/.memorygraph/memory.db"),
            TURSO_DATABASE_URL="libsql://test.turso.io",
            TURSO_AUTH_TOKEN="config-secret-token-123"
        ):
            os.environ["TURSO_AUTH_TOKEN"] = "env-secret-token-456"

            backend = TursoBackend()

            # WILL FAIL: current code returns "env-secret-token-456" from os.getenv()
            assert backend.auth_token == "config-secret-token-123", (
                f"Expected Config.TURSO_AUTH_TOKEN 'config-secret-token-123', "
                f"got '{backend.auth_token}' from os.getenv()"
            )

    @pytest.mark.skipif(not HAS_LIBSQL, reason="libsql-experimental package not installed")
    def test_turso_backend_explicit_params_override_config(self):
        """
        Explicit __init__ parameters should override Config values.

        This should PASS even with current implementation.
        """
        from memorygraph.backends.turso import TursoBackend

        with patch_config(
            TURSO_PATH="/config/memory.db",
            TURSO_DATABASE_URL="libsql://config.turso.io",
            TURSO_AUTH_TOKEN="config-token"
        ):
            os.environ["TURSO_DATABASE_URL"] = "libsql://env.turso.io"

            backend = TursoBackend(
                db_path="/explicit/memory.db",
                sync_url="libsql://explicit.turso.io",
                auth_token="explicit-token"
            )

            assert backend.db_path == "/explicit/memory.db"
            assert backend.sync_url == "libsql://explicit.turso.io"
            assert backend.auth_token == "explicit-token"


class TestBackendConfigIntegration:
    """
    Integration tests verifying Config is the single source of truth across backends.

    These tests verify that changing Config values affects backend initialization,
    confirming consistent behavior across all backend implementations.
    """

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_sqlite_backend_respects_config_changes(self):
        """
        Changing Config.SQLITE_PATH should change SQLiteFallbackBackend.db_path.

        This is an integration test verifying Config is the source of truth.
        """
        # Set conflicting env var
        os.environ["MEMORY_SQLITE_PATH"] = "/tmp/env/should/not/be/used.db"

        # First backend with Config path 1
        with patch_config(SQLITE_PATH="/tmp/first/config/path.db"):
            backend1 = SQLiteFallbackBackend()
            # WILL FAIL if reads env var instead of Config
            assert backend1.db_path == "/tmp/first/config/path.db"

        # Second backend with Config path 2
        with patch_config(SQLITE_PATH="/tmp/second/config/path.db"):
            backend2 = SQLiteFallbackBackend()
            # Should use new Config value
            assert backend2.db_path == "/tmp/second/config/path.db"

        # Paths should be different (proving Config controls behavior)
        assert backend1.db_path != backend2.db_path

    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    def test_neo4j_backend_respects_config_changes(self):
        """
        Changing Config.NEO4J_* values should change Neo4jBackend attributes.
        """
        from memorygraph.backends.neo4j_backend import Neo4jBackend

        # Set conflicting env vars
        os.environ["MEMORY_NEO4J_URI"] = "bolt://env:7687"
        os.environ["MEMORY_NEO4J_USER"] = "env-user"
        os.environ["MEMORY_NEO4J_PASSWORD"] = "env-pass"

        # First backend with Config credentials 1
        with patch_config(
            NEO4J_URI="bolt://first:7687",
            NEO4J_USER="first-user",
            NEO4J_PASSWORD="first-pass"
        ):
            backend1 = Neo4jBackend()
            assert backend1.uri == "bolt://first:7687"
            assert backend1.user == "first-user"
            assert backend1.password == "first-pass"

        # Second backend with Config credentials 2
        with patch_config(
            NEO4J_URI="bolt://second:7687",
            NEO4J_USER="second-user",
            NEO4J_PASSWORD="second-pass"
        ):
            backend2 = Neo4jBackend()
            assert backend2.uri == "bolt://second:7687"
            assert backend2.user == "second-user"
            assert backend2.password == "second-pass"

        # Credentials should be different (proving Config controls behavior)
        assert backend1.uri != backend2.uri


class TestBackendConfigEdgeCases:
    """Test edge cases and boundary conditions for Config-based backends."""

    @pytest.fixture(autouse=True)
    def save_and_restore_env(self):
        """Save and restore environment variables."""
        original_env = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original_env)

    def test_sqlite_backend_handles_none_config_path(self):
        """
        SQLiteFallbackBackend should handle None in Config.SQLITE_PATH gracefully.

        Should fall back to default path when Config value is None.
        """
        with patch_config(SQLITE_PATH=None):
            # Clear env var
            os.environ.pop("MEMORY_SQLITE_PATH", None)

            backend = SQLiteFallbackBackend()

            # Should have some path (default), not None
            assert backend.db_path is not None
            assert isinstance(backend.db_path, str)

    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    def test_neo4j_backend_preserves_fallback_behavior(self):
        """
        After refactor, Neo4jBackend should still support fallback values.

        Config.NEO4J_URI has a default; backend should use it when not explicitly set.
        """
        from memorygraph.backends.neo4j_backend import Neo4jBackend

        # Don't override Config, use its defaults
        # Clear env vars to ensure Config defaults are used
        os.environ.pop("MEMORY_NEO4J_URI", None)
        os.environ.pop("NEO4J_URI", None)
        os.environ.pop("MEMORY_NEO4J_USER", None)
        os.environ.pop("NEO4J_USER", None)

        # Set password in Config (required)
        with patch_config(NEO4J_PASSWORD="test-pass"):
            backend = Neo4jBackend()

            # Should use Config's default URI
            assert backend.uri == Config.NEO4J_URI
            # Should use Config's default user
            assert backend.user == Config.NEO4J_USER
            # Should use Config's provided password
            assert backend.password == "test-pass"


# Tests for WP33 Phase 2 - Backend Config Refactor (TDD RED phase)
