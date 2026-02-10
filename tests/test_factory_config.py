"""
Tests for BackendFactory Config integration (WP33 Phase 1).

This test suite verifies that BackendFactory reads configuration from the Config
class instead of calling os.getenv() directly. These tests follow TDD RED phase -
they MUST fail against the current implementation that uses os.getenv().

Tests cover:
- Factory reads Config.BACKEND instead of os.getenv("MEMORY_BACKEND")
- Factory reads Config.NEO4J_* instead of os.getenv("MEMORY_NEO4J_*")
- Factory reads Config.MEMGRAPH_* instead of os.getenv("MEMORY_MEMGRAPH_*")
- Factory reads Config.SQLITE_PATH instead of os.getenv("MEMORY_SQLITE_PATH")
- Factory reads Config.TURSO_* instead of os.getenv("MEMORY_TURSO_*")
- Factory reads Config.MEMORYGRAPH_API_KEY instead of os.getenv("MEMORYGRAPH_API_KEY")
- Factory reads Config.FALKORDB_* instead of os.getenv("MEMORY_FALKORDB_*")
- Factory reads Config.FALKORDBLITE_* instead of os.getenv("MEMORY_FALKORDBLITE_*")
- Factory reads Config.LADYBUGDB_* instead of os.getenv("MEMORY_LADYBUGDB_*")
- get_configured_backend_type() reads Config
- is_backend_configured() reads Config
- Auto-selection logic reads Config
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Check for optional dependencies
try:
    import neo4j  # noqa: F401
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

try:
    import mgclient  # noqa: F401
    HAS_MEMGRAPH = True
except ImportError:
    HAS_MEMGRAPH = False

from memorygraph.backends.factory import BackendFactory
from memorygraph.config import Config
from memorygraph.models import DatabaseConnectionError


class TestFactoryReadsConfig:
    """
    Tests that BackendFactory reads from Config class, not os.getenv().

    Pattern: Set Config attribute to one value, set os.environ to a DIFFERENT
    value, then verify factory uses the Config value (not env var).

    Config descriptors are restored by the autouse ``reset_config`` fixture
    in conftest.py; environment variables are cleaned up via ``monkeypatch``.
    """

    def test_factory_reads_config_backend_not_env_var(self, monkeypatch):
        """
        Factory should read Config.BACKEND, not os.getenv('MEMORY_BACKEND').

        This test sets:
        - Config.BACKEND = "cloud"
        - os.environ["MEMORY_BACKEND"] = "sqlite" (different!)

        Expected: Factory should attempt to create cloud backend (from Config),
        not SQLite backend (from env var).

        MUST FAIL: Current factory.py line 52 uses os.getenv("MEMORY_BACKEND")
        """
        # Set Config to cloud
        Config.BACKEND = "cloud"

        # Set env var to sqlite (conflicting value)
        monkeypatch.setenv("MEMORY_BACKEND", "sqlite")

        # Mock cloud backend creation to verify it's called
        with patch.object(BackendFactory, "_create_cloud", new_callable=AsyncMock) as mock_cloud:
            mock_cloud.return_value = MagicMock()

            # get_configured_backend_type should return "cloud" from Config
            backend_type = BackendFactory.get_configured_backend_type()

            # This assertion WILL FAIL with current implementation
            # Current code returns "sqlite" (from env var)
            # Expected: "cloud" (from Config)
            assert backend_type == "cloud", (
                f"Expected 'cloud' from Config.BACKEND, got '{backend_type}' from env var"
            )

    @pytest.mark.asyncio
    async def test_factory_reads_config_sqlite_path(self, monkeypatch):
        """
        Factory should read Config.SQLITE_PATH, not os.getenv('MEMORY_SQLITE_PATH').

        MUST FAIL: Current factory.py line 275 uses os.getenv("MEMORY_SQLITE_PATH")
        """
        # Set Config to custom path
        custom_path = "/custom/config/path.db"
        Config.SQLITE_PATH = custom_path
        Config.BACKEND = "sqlite"

        # Set env var to different path
        monkeypatch.setenv("MEMORY_SQLITE_PATH", "/wrong/env/path.db")
        monkeypatch.setenv("MEMORY_BACKEND", "sqlite")

        # Mock SQLite backend to capture initialization (lazy import)
        with patch("memorygraph.backends.sqlite_fallback.SQLiteFallbackBackend") as mock_backend_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_instance.initialize_schema = AsyncMock()
            mock_backend_class.return_value = mock_instance

            # Create backend
            await BackendFactory._create_sqlite()

            # Verify SQLiteFallbackBackend was initialized with Config path
            mock_backend_class.assert_called_once()
            call_kwargs = mock_backend_class.call_args[1] if mock_backend_class.call_args[1] else {}
            actual_path = call_kwargs.get("db_path")

            # This assertion WILL FAIL with current implementation
            # Current code passes "/wrong/env/path.db" (from os.getenv)
            # Expected: custom_path (from Config.SQLITE_PATH)
            assert actual_path == custom_path, (
                f"Expected '{custom_path}' from Config.SQLITE_PATH, "
                f"got '{actual_path}' from env var"
            )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    async def test_factory_reads_config_neo4j_credentials(self, monkeypatch):
        """
        Factory should read Config.NEO4J_* values, not os.getenv('MEMORY_NEO4J_*').

        MUST FAIL: Current factory.py lines 156-158 use os.getenv()
        """
        # Set Config values
        Config.NEO4J_URI = "bolt://config-host:7687"
        Config.NEO4J_USER = "config-user"
        Config.NEO4J_PASSWORD = "config-password"
        Config.BACKEND = "neo4j"

        # Set env vars to different values
        monkeypatch.setenv("MEMORY_NEO4J_URI", "bolt://env-host:7687")
        monkeypatch.setenv("MEMORY_NEO4J_USER", "env-user")
        monkeypatch.setenv("MEMORY_NEO4J_PASSWORD", "env-password")
        monkeypatch.setenv("MEMORY_BACKEND", "neo4j")

        # Mock Neo4j backend (lazy import)
        with patch("memorygraph.backends.neo4j_backend.Neo4jBackend") as mock_backend_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_backend_class.return_value = mock_instance

            # Create backend
            await BackendFactory._create_neo4j()

            # Verify Neo4jBackend was initialized with Config values
            mock_backend_class.assert_called_once()
            call_kwargs = mock_backend_class.call_args[1]

            # These assertions WILL FAIL with current implementation
            assert call_kwargs["uri"] == "bolt://config-host:7687", (
                "Should use Config.NEO4J_URI, not env var"
            )
            assert call_kwargs["user"] == "config-user", (
                "Should use Config.NEO4J_USER, not env var"
            )
            assert call_kwargs["password"] == "config-password", (
                "Should use Config.NEO4J_PASSWORD, not env var"
            )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_MEMGRAPH, reason="memgraph (mgclient) package not installed")
    async def test_factory_reads_config_memgraph_credentials(self, monkeypatch):
        """
        Factory should read Config.MEMGRAPH_* values, not os.getenv('MEMORY_MEMGRAPH_*').

        MUST FAIL: Current factory.py lines 185-187 use os.getenv()
        """
        # Set Config values
        Config.MEMGRAPH_URI = "bolt://config-memgraph:7687"
        Config.MEMGRAPH_USER = "config-memgraph-user"
        Config.MEMGRAPH_PASSWORD = "config-memgraph-pass"
        Config.BACKEND = "memgraph"

        # Set env vars to different values
        monkeypatch.setenv("MEMORY_MEMGRAPH_URI", "bolt://env-memgraph:7687")
        monkeypatch.setenv("MEMORY_MEMGRAPH_USER", "env-memgraph-user")
        monkeypatch.setenv("MEMORY_MEMGRAPH_PASSWORD", "env-memgraph-pass")
        monkeypatch.setenv("MEMORY_BACKEND", "memgraph")

        # Mock Memgraph backend (lazy import)
        with patch("memorygraph.backends.memgraph_backend.MemgraphBackend") as mock_backend_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_backend_class.return_value = mock_instance

            # Create backend
            await BackendFactory._create_memgraph()

            # Verify MemgraphBackend was initialized with Config values
            mock_backend_class.assert_called_once()
            call_kwargs = mock_backend_class.call_args[1]

            # These assertions WILL FAIL with current implementation
            assert call_kwargs["uri"] == "bolt://config-memgraph:7687", (
                "Should use Config.MEMGRAPH_URI, not env var"
            )
            assert call_kwargs["user"] == "config-memgraph-user", (
                "Should use Config.MEMGRAPH_USER, not env var"
            )
            assert call_kwargs["password"] == "config-memgraph-pass", (
                "Should use Config.MEMGRAPH_PASSWORD, not env var"
            )

    @pytest.mark.asyncio
    async def test_factory_reads_config_turso_settings(self, monkeypatch):
        """
        Factory should read Config.TURSO_* values, not os.getenv('TURSO_*').

        MUST FAIL: Current factory.py lines 296-298 use os.getenv()
        """
        # Set Config values
        Config.TURSO_PATH = "/config/turso.db"
        Config.TURSO_DATABASE_URL = "libsql://config.turso.io"
        Config.TURSO_AUTH_TOKEN = "config-token-123"
        Config.BACKEND = "turso"

        # Set env vars to different values
        monkeypatch.setenv("MEMORY_TURSO_PATH", "/env/turso.db")
        monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://env.turso.io")
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "env-token-456")
        monkeypatch.setenv("MEMORY_BACKEND", "turso")

        # Mock Turso backend (lazy import)
        with patch("memorygraph.backends.turso.TursoBackend") as mock_backend_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_instance.initialize_schema = AsyncMock()
            mock_backend_class.return_value = mock_instance

            # Create backend
            await BackendFactory._create_turso()

            # Verify TursoBackend was initialized with Config values
            mock_backend_class.assert_called_once()
            call_kwargs = mock_backend_class.call_args[1]

            # These assertions WILL FAIL with current implementation
            assert call_kwargs["db_path"] == "/config/turso.db", (
                "Should use Config.TURSO_PATH, not env var"
            )
            assert call_kwargs["sync_url"] == "libsql://config.turso.io", (
                "Should use Config.TURSO_DATABASE_URL, not env var"
            )
            assert call_kwargs["auth_token"] == "config-token-123", (
                "Should use Config.TURSO_AUTH_TOKEN, not env var"
            )

    @pytest.mark.asyncio
    async def test_factory_reads_config_cloud_api_key(self, monkeypatch):
        """
        Factory should read Config.MEMORYGRAPH_API_KEY, not os.getenv('MEMORYGRAPH_API_KEY').

        MUST FAIL: Current factory.py lines 324-326 use os.getenv()
        """
        # Set Config values
        Config.MEMORYGRAPH_API_KEY = "config-api-key-abc"
        Config.MEMORYGRAPH_API_URL = "https://config-api.memorygraph.dev"
        Config.MEMORYGRAPH_TIMEOUT = 60
        Config.BACKEND = "cloud"

        # Set env vars to different values
        monkeypatch.setenv("MEMORYGRAPH_API_KEY", "env-api-key-xyz")
        monkeypatch.setenv("MEMORYGRAPH_API_URL", "https://env-api.memorygraph.dev")
        monkeypatch.setenv("MEMORYGRAPH_TIMEOUT", "30")
        monkeypatch.setenv("MEMORY_BACKEND", "cloud")

        # Mock Cloud backend (lazy import)
        with patch("memorygraph.backends.cloud_backend.CloudRESTAdapter") as mock_backend_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_backend_class.return_value = mock_instance

            # Create backend
            await BackendFactory._create_cloud()

            # Verify CloudRESTAdapter was initialized with Config values
            mock_backend_class.assert_called_once()
            call_kwargs = mock_backend_class.call_args[1]

            # These assertions WILL FAIL with current implementation
            assert call_kwargs["api_key"] == "config-api-key-abc", (
                "Should use Config.MEMORYGRAPH_API_KEY, not env var"
            )
            assert call_kwargs["api_url"] == "https://config-api.memorygraph.dev", (
                "Should use Config.MEMORYGRAPH_API_URL, not env var"
            )
            assert call_kwargs["timeout"] == 60, (
                "Should use Config.MEMORYGRAPH_TIMEOUT, not env var"
            )

    @pytest.mark.asyncio
    async def test_factory_reads_config_falkordb_settings(self, monkeypatch):
        """
        Factory should read Config.FALKORDB_* values from Config class.

        Note: Config doesn't have FALKORDB_* yet, but factory should be refactored
        to add them and use them.

        MUST FAIL: Current factory.py lines 208-211 use os.getenv()
        """
        # This test documents the expected behavior even though Config doesn't
        # have FALKORDB_* attributes yet. The refactor should add them.

        # For now, test that factory at least doesn't use hardcoded env vars
        monkeypatch.setenv("MEMORY_FALKORDB_HOST", "localhost")
        monkeypatch.setenv("MEMORY_FALKORDB_PORT", "6379")
        monkeypatch.setenv("MEMORY_FALKORDB_PASSWORD", "test-password")

        with patch("memorygraph.backends.falkordb_backend.FalkorDBBackend") as mock_backend_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_backend_class.return_value = mock_instance

            await BackendFactory._create_falkordb()

            # Current implementation will work, but after refactor should use Config
            # This is a placeholder test that will need updating in Phase 2
            mock_backend_class.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    async def test_factory_auto_select_reads_config_neo4j_password(self, monkeypatch):
        """
        Factory auto-selection should check Config.NEO4J_PASSWORD, not env var.

        MUST FAIL: Current factory.py line 108 uses os.getenv()
        """
        # Set Config to have Neo4j password
        Config.NEO4J_PASSWORD = "config-neo4j-pass"
        Config.NEO4J_URI = "bolt://localhost:7687"
        Config.NEO4J_USER = "neo4j"

        # Clear env var
        monkeypatch.delenv("MEMORY_NEO4J_PASSWORD", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        # Mock _create_neo4j to track if it's called
        mock_instance = AsyncMock()
        with patch.object(BackendFactory, "_create_neo4j", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_instance

            # Auto-select should try Neo4j because Config.NEO4J_PASSWORD is set
            await BackendFactory._auto_select_backend()

            # Should call _create_neo4j() because Config has password
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_MEMGRAPH, reason="memgraph (mgclient) package not installed")
    async def test_factory_auto_select_reads_config_memgraph_uri(self, monkeypatch):
        """
        Factory auto-selection should check Config.MEMGRAPH_URI, not env var.

        MUST FAIL: Current factory.py line 119 uses os.getenv()
        """
        # Set Config to have Memgraph URI, but no Neo4j password
        Config.NEO4J_PASSWORD = None
        Config.MEMGRAPH_URI = "bolt://config-memgraph:7687"
        Config.MEMGRAPH_USER = ""
        Config.MEMGRAPH_PASSWORD = ""

        # Clear env var
        monkeypatch.delenv("MEMORY_MEMGRAPH_URI", raising=False)
        monkeypatch.delenv("MEMORY_NEO4J_PASSWORD", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        # Mock Memgraph backend (lazy import)
        with patch("memorygraph.backends.memgraph_backend.MemgraphBackend") as mock_backend_class:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_backend_class.return_value = mock_instance

            # Mock _create_memgraph to track if it's called
            with patch.object(BackendFactory, "_create_memgraph", new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_instance

                # Auto-select should try Memgraph because Config.MEMGRAPH_URI is set
                await BackendFactory._auto_select_backend()

                # This assertion WILL FAIL with current implementation
                # Current code checks os.getenv(), which is None, so skips Memgraph
                # Expected: Should call _create_memgraph() because Config has URI
                mock_create.assert_called_once()

    def test_is_backend_configured_reads_config_neo4j(self, monkeypatch):
        """
        is_backend_configured() should check Config.NEO4J_PASSWORD, not env var.

        MUST FAIL: Current factory.py lines 576-579 use os.getenv()
        """
        # Set Config to have Neo4j password
        Config.NEO4J_PASSWORD = "config-password"

        # Clear env vars
        monkeypatch.delenv("MEMORY_NEO4J_PASSWORD", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        # Check if Neo4j is configured
        is_configured = BackendFactory.is_backend_configured("neo4j")

        # This assertion WILL FAIL with current implementation
        # Current code checks os.getenv(), which is None, returns False
        # Expected: Should return True because Config.NEO4J_PASSWORD is set
        assert is_configured is True, (
            "Should return True when Config.NEO4J_PASSWORD is set"
        )

    def test_is_backend_configured_reads_config_memgraph(self, monkeypatch):
        """
        is_backend_configured() should check Config.MEMGRAPH_URI, not env var.

        MUST FAIL: Current factory.py line 581 uses os.getenv()
        """
        # Set Config to have Memgraph URI
        Config.MEMGRAPH_URI = "bolt://config-memgraph:7687"

        # Clear env var
        monkeypatch.delenv("MEMORY_MEMGRAPH_URI", raising=False)

        # Check if Memgraph is configured
        is_configured = BackendFactory.is_backend_configured("memgraph")

        # This assertion WILL FAIL with current implementation
        # Current code checks os.getenv(), which is None, returns False
        # Expected: Should return True because Config.MEMGRAPH_URI is set
        assert is_configured is True, (
            "Should return True when Config.MEMGRAPH_URI is set"
        )

    def test_is_backend_configured_reads_config_cloud(self, monkeypatch):
        """
        is_backend_configured() should check Config.MEMORYGRAPH_API_KEY, not env var.

        MUST FAIL: Current factory.py line 598 uses os.getenv()
        """
        # Set Config to have API key
        Config.MEMORYGRAPH_API_KEY = "config-api-key"

        # Clear env var
        monkeypatch.delenv("MEMORYGRAPH_API_KEY", raising=False)

        # Check if Cloud is configured
        is_configured = BackendFactory.is_backend_configured("cloud")

        # This assertion WILL FAIL with current implementation
        # Current code checks os.getenv(), which is None, returns False
        # Expected: Should return True because Config.MEMORYGRAPH_API_KEY is set
        assert is_configured is True, (
            "Should return True when Config.MEMORYGRAPH_API_KEY is set"
        )

    @pytest.mark.asyncio
    async def test_create_backend_reads_config_for_backend_selection(self, monkeypatch):
        """
        create_backend() should read Config.BACKEND for backend type selection.

        MUST FAIL: Current factory.py line 52 uses os.getenv("MEMORY_BACKEND")
        """
        # Set Config to neo4j
        Config.BACKEND = "neo4j"
        Config.NEO4J_URI = "bolt://localhost:7687"
        Config.NEO4J_USER = "neo4j"
        Config.NEO4J_PASSWORD = "test-pass"

        # Set env var to different backend
        monkeypatch.setenv("MEMORY_BACKEND", "sqlite")

        # Mock Neo4j backend
        with patch.object(BackendFactory, "_create_neo4j", new_callable=AsyncMock) as mock_neo4j:
            mock_neo4j.return_value = MagicMock()

            # Create backend - should use Config.BACKEND ("neo4j"), not env var ("sqlite")
            await BackendFactory.create_backend()

            # This assertion WILL FAIL with current implementation
            # Current code reads os.getenv(), which is "sqlite", so doesn't call _create_neo4j
            # Expected: Should call _create_neo4j() because Config.BACKEND is "neo4j"
            mock_neo4j.assert_called_once()


class TestFactoryConfigEdgeCases:
    """Test edge cases and error conditions for Config-based factory.

    Config descriptors are restored by the autouse ``reset_config`` fixture
    in conftest.py; environment variables are cleaned up via ``monkeypatch``.
    """

    @pytest.mark.asyncio
    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j package not installed")
    async def test_factory_raises_error_when_neo4j_password_missing_in_config(self, monkeypatch):
        """
        Factory should check Config.NEO4J_PASSWORD and raise error if missing.

        Current implementation checks os.getenv(), so this might pass accidentally.
        After refactor, should explicitly check Config.
        """
        # Set Config to Neo4j but no password
        Config.BACKEND = "neo4j"
        Config.NEO4J_PASSWORD = None

        # Ensure env var is also not set
        monkeypatch.delenv("MEMORY_NEO4J_PASSWORD", raising=False)
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

        # Should raise error about missing password
        with pytest.raises(DatabaseConnectionError, match="password not configured"):
            await BackendFactory._create_neo4j()

    @pytest.mark.asyncio
    async def test_factory_raises_error_when_cloud_api_key_missing_in_config(self, monkeypatch):
        """
        Factory should check Config.MEMORYGRAPH_API_KEY and raise error if missing.
        """
        # Set Config to Cloud but no API key
        Config.BACKEND = "cloud"
        Config.MEMORYGRAPH_API_KEY = None

        # Ensure env var is also not set
        monkeypatch.delenv("MEMORYGRAPH_API_KEY", raising=False)

        # Should raise error about missing API key
        with pytest.raises(DatabaseConnectionError, match="API key"):
            await BackendFactory._create_cloud()

    def test_config_backend_case_insensitive(self, monkeypatch):
        """
        Config.BACKEND should be case-insensitive (lowercased before use).
        """
        # Set Config with mixed case
        Config.BACKEND = "NeO4J"
        monkeypatch.setenv("MEMORY_BACKEND", "sqlite")  # Different, to ensure Config is used

        # get_configured_backend_type should return lowercase
        backend_type = BackendFactory.get_configured_backend_type()

        # Should be lowercase version of Config value
        # This might fail if factory uses env var instead of Config
        assert backend_type.lower() == "neo4j"


class TestFactoryConfigIntegration:
    """
    Integration tests verifying end-to-end Config usage.

    These tests verify that changing Config values affects factory behavior,
    confirming that Config is the source of truth.

    Config descriptors are restored by the autouse ``reset_config`` fixture
    in conftest.py; environment variables are cleaned up via ``monkeypatch``.
    """

    @pytest.mark.asyncio
    async def test_changing_config_backend_changes_factory_behavior(self, monkeypatch):
        """
        Changing Config.BACKEND should change which backend factory creates.

        This is an integration test verifying Config is the source of truth.
        """
        # Configure for SQLite in Config
        Config.BACKEND = "sqlite"
        Config.SQLITE_PATH = "/test/path.db"

        # Conflicting env var
        monkeypatch.setenv("MEMORY_BACKEND", "neo4j")

        with patch("memorygraph.backends.sqlite_fallback.SQLiteFallbackBackend") as mock_sqlite:
            mock_instance = AsyncMock()
            mock_instance.connect = AsyncMock()
            mock_instance.initialize_schema = AsyncMock()
            mock_sqlite.return_value = mock_instance

            # Should create SQLite (from Config), not Neo4j (from env)
            await BackendFactory.create_backend()

            # WILL FAIL: current code uses env var, creates Neo4j
            # Expected: creates SQLite from Config
            mock_sqlite.assert_called_once()

    @pytest.mark.asyncio
    async def test_config_values_override_env_vars_consistently(self, monkeypatch):
        """
        Config values should consistently override environment variables across all backends.

        This is a comprehensive integration test.
        """
        # Set all Config values
        Config.BACKEND = "sqlite"
        Config.SQLITE_PATH = "/config/test.db"
        Config.NEO4J_PASSWORD = "config-pass"
        Config.MEMGRAPH_URI = "bolt://config:7687"

        # Set conflicting env vars
        monkeypatch.setenv("MEMORY_BACKEND", "neo4j")
        monkeypatch.setenv("MEMORY_SQLITE_PATH", "/env/test.db")
        monkeypatch.setenv("MEMORY_NEO4J_PASSWORD", "env-pass")
        monkeypatch.setenv("MEMORY_MEMGRAPH_URI", "bolt://env:7687")

        # Test 1: Backend selection uses Config
        backend_type = BackendFactory.get_configured_backend_type()
        assert backend_type == "sqlite", "Should use Config.BACKEND"

        # Test 2: is_backend_configured uses Config
        # (These will fail with current implementation)
        Config.NEO4J_PASSWORD = "has-password"
        assert BackendFactory.is_backend_configured("neo4j") is True

        Config.MEMGRAPH_URI = "bolt://localhost:7687"
        assert BackendFactory.is_backend_configured("memgraph") is True


# Tests for WP33 Phase 1 - Factory Config Refactor (TDD RED phase)
