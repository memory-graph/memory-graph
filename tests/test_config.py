"""
Tests for configuration management and multi-tenancy configuration.

This module tests the Config class and its multi-tenancy related methods,
ensuring proper environment variable handling and backward compatibility.
"""

import os
import pytest
from unittest import mock

from memorygraph.config import Config, _EnvVar

from tests.conftest import patch_config


class TestConfigMultiTenancy:
    """Test multi-tenancy configuration settings."""

    def test_default_configuration_is_single_tenant(self):
        """Test that default configuration is single-tenant mode."""
        # By default, multi-tenant mode should be disabled
        assert Config.MULTI_TENANT_MODE is False
        assert Config.is_multi_tenant_mode() is False

    def test_default_tenant_value(self):
        """Test default tenant ID."""
        assert Config.DEFAULT_TENANT == "default"
        assert Config.get_default_tenant() == "default"

    def test_default_auth_disabled(self):
        """Test that authentication is disabled by default."""
        assert Config.REQUIRE_AUTH is False
        assert Config.AUTH_PROVIDER == "none"
        assert Config.JWT_SECRET is None

    def test_default_audit_disabled(self):
        """Test that audit logging is disabled by default."""
        assert Config.ENABLE_AUDIT_LOG is False

    @mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "true"})
    def test_multi_tenant_mode_enabled_via_env(self):
        """Test enabling multi-tenant mode via environment variable."""
        # Need to reload the Config class to pick up new env var
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.MULTI_TENANT_MODE is True
        assert ReloadedConfig.is_multi_tenant_mode() is True

    @mock.patch.dict(os.environ, {"MEMORY_DEFAULT_TENANT": "acme-corp"})
    def test_custom_default_tenant(self):
        """Test setting custom default tenant via environment variable."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.DEFAULT_TENANT == "acme-corp"
        assert ReloadedConfig.get_default_tenant() == "acme-corp"

    @mock.patch.dict(os.environ, {"MEMORY_REQUIRE_AUTH": "true"})
    def test_require_auth_enabled(self):
        """Test enabling authentication requirement via environment variable."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.REQUIRE_AUTH is True

    @mock.patch.dict(os.environ, {
        "MEMORY_AUTH_PROVIDER": "jwt",
        "MEMORY_JWT_SECRET": "test-secret-key",
        "MEMORY_JWT_ALGORITHM": "HS512"
    })
    def test_jwt_configuration(self):
        """Test JWT authentication configuration."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.AUTH_PROVIDER == "jwt"
        assert ReloadedConfig.JWT_SECRET == "test-secret-key"
        assert ReloadedConfig.JWT_ALGORITHM == "HS512"

    @mock.patch.dict(os.environ, {"MEMORY_ENABLE_AUDIT_LOG": "true"})
    def test_audit_log_enabled(self):
        """Test enabling audit logging via environment variable."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.ENABLE_AUDIT_LOG is True

    def test_config_summary_includes_multi_tenancy(self):
        """Test that config summary includes multi-tenancy settings."""
        summary = Config.get_config_summary()

        assert "multi_tenancy" in summary
        assert "enabled" in summary["multi_tenancy"]
        assert "default_tenant" in summary["multi_tenancy"]
        assert "require_auth" in summary["multi_tenancy"]
        assert "auth_provider" in summary["multi_tenancy"]
        assert "jwt_secret_configured" in summary["multi_tenancy"]
        assert "audit_log_enabled" in summary["multi_tenancy"]

    def test_config_summary_hides_jwt_secret(self):
        """Test that config summary doesn't expose JWT secret value."""
        summary = Config.get_config_summary()

        # Should only show whether secret is configured, not the actual value
        assert "jwt_secret_configured" in summary["multi_tenancy"]
        assert "jwt_secret" not in summary["multi_tenancy"]

    def test_config_summary_includes_falkordb(self):
        """Test that config summary includes FalkorDB details."""
        summary = Config.get_config_summary()

        assert "falkordb" in summary
        assert "host" in summary["falkordb"]
        assert "port" in summary["falkordb"]
        assert "password_configured" in summary["falkordb"]

    def test_config_summary_includes_falkordblite(self):
        """Test that config summary includes FalkorDBLite details."""
        summary = Config.get_config_summary()

        assert "falkordblite" in summary
        assert "path" in summary["falkordblite"]


class TestConfigBackwardCompatibility:
    """Test backward compatibility of configuration."""

    def test_single_tenant_mode_is_default(self):
        """Test that single-tenant mode is the default (backward compatible)."""
        assert Config.MULTI_TENANT_MODE is False
        assert Config.is_multi_tenant_mode() is False

    def test_no_env_vars_set_works(self):
        """Test that config works with no multi-tenancy env vars set."""
        # This simulates an existing deployment with no new env vars
        assert Config.MULTI_TENANT_MODE is False
        assert Config.DEFAULT_TENANT == "default"
        assert Config.REQUIRE_AUTH is False
        assert Config.AUTH_PROVIDER == "none"

    def test_existing_config_values_unchanged(self):
        """Test that existing config values are not affected by multi-tenancy."""
        # Verify that existing configuration still works
        assert hasattr(Config, "BACKEND")
        assert hasattr(Config, "NEO4J_URI")
        assert hasattr(Config, "SQLITE_PATH")
        assert hasattr(Config, "LOG_LEVEL")
        assert hasattr(Config, "AUTO_EXTRACT_ENTITIES")
        assert hasattr(Config, "SESSION_BRIEFING")


class TestConfigValidation:
    """Test configuration validation."""

    @mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "false"})
    def test_false_string_parsed_correctly(self):
        """Test that 'false' string is parsed as boolean False."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.MULTI_TENANT_MODE is False

    @mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "False"})
    def test_false_case_insensitive(self):
        """Test that 'False' (capitalized) is parsed correctly."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.MULTI_TENANT_MODE is False

    @mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "TRUE"})
    def test_true_case_insensitive(self):
        """Test that 'TRUE' (uppercase) is parsed correctly."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.MULTI_TENANT_MODE is True

    @mock.patch.dict(os.environ, {"MEMORY_MULTI_TENANT_MODE": "yes"})
    def test_invalid_boolean_defaults_to_false(self):
        """Test that invalid boolean string defaults to False."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        # 'yes' is not 'true', so should be False
        assert ReloadedConfig.MULTI_TENANT_MODE is False


class TestEnvVarIsSet:
    """Tests for _EnvVar.is_set() — checks os.environ membership, not truthiness."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Remove test env vars before and after each test."""
        keys = [
            "TEST_IS_SET_VAR", "TEST_IS_SET_ALT",
            "MEMORY_MEMGRAPH_URI", "MEMORY_FALKORDB_HOST", "FALKORDB_HOST",
            "MEMORY_NEO4J_PASSWORD", "NEO4J_PASSWORD",
        ]
        saved = {k: os.environ.pop(k, None) for k in keys}
        yield
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def test_is_set_returns_false_when_env_var_not_set(self):
        """is_set() returns False when no env var is in os.environ."""
        desc = _EnvVar("TEST_IS_SET_VAR", default="some-default")
        assert desc.is_set() is False

    def test_is_set_returns_true_when_env_var_set(self):
        """is_set() returns True when the env var exists in os.environ."""
        os.environ["TEST_IS_SET_VAR"] = "anything"
        desc = _EnvVar("TEST_IS_SET_VAR", default="some-default")
        assert desc.is_set() is True

    def test_is_set_returns_true_for_empty_string_value(self):
        """is_set() returns True even for empty string — presence matters, not truthiness."""
        os.environ["TEST_IS_SET_VAR"] = ""
        desc = _EnvVar("TEST_IS_SET_VAR", default="fallback")
        assert desc.is_set() is True

    def test_is_set_checks_all_env_names(self):
        """is_set() returns True if any of the priority env var names is set."""
        desc = _EnvVar("TEST_IS_SET_VAR", "TEST_IS_SET_ALT", default="x")
        assert desc.is_set() is False

        os.environ["TEST_IS_SET_ALT"] = "val"
        assert desc.is_set() is True

    def test_is_set_independent_of_default(self):
        """is_set() ignores the default value entirely."""
        desc_with_truthy = _EnvVar("TEST_IS_SET_VAR", default="bolt://localhost:7687")
        desc_with_none = _EnvVar("TEST_IS_SET_VAR", default=None)

        # Neither should be True when env var isn't set
        assert desc_with_truthy.is_set() is False
        assert desc_with_none.is_set() is False

    def test_memgraph_uri_not_set_by_default(self):
        """Reproduce the bug: MEMGRAPH_URI default is truthy but env var is not set."""
        desc = Config.__dict__["MEMGRAPH_URI"]
        if isinstance(desc, _EnvVar):
            # Without MEMORY_MEMGRAPH_URI set, is_set() should be False
            assert desc.is_set() is False
            # But the resolved value is truthy (the default)
            assert Config.MEMGRAPH_URI == "bolt://localhost:7687"

    def test_falkordb_host_not_set_by_default(self):
        """Reproduce the bug: FALKORDB_HOST default is truthy but env var is not set."""
        desc = Config.__dict__["FALKORDB_HOST"]
        if isinstance(desc, _EnvVar):
            assert desc.is_set() is False
            assert Config.FALKORDB_HOST == "localhost"


class TestConfigIsEnvSet:
    """Tests for Config.is_env_set() classmethod."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Remove test env vars before and after each test."""
        keys = [
            "MEMORY_NEO4J_PASSWORD", "NEO4J_PASSWORD",
            "MEMORY_MEMGRAPH_URI",
            "MEMORY_FALKORDB_HOST", "FALKORDB_HOST",
            "MEMORYGRAPH_API_KEY",
            "TURSO_DATABASE_URL", "MEMORY_TURSO_PATH",
        ]
        saved = {k: os.environ.pop(k, None) for k in keys}
        yield
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def test_is_env_set_false_for_unconfigured_backend(self):
        """Config.is_env_set returns False when no env var is present."""
        assert Config.is_env_set("MEMGRAPH_URI") is False
        assert Config.is_env_set("FALKORDB_HOST") is False
        assert Config.is_env_set("NEO4J_PASSWORD") is False

    def test_is_env_set_true_when_env_var_present(self):
        """Config.is_env_set returns True when the env var exists."""
        os.environ["MEMORY_MEMGRAPH_URI"] = "bolt://myhost:7687"
        assert Config.is_env_set("MEMGRAPH_URI") is True

    def test_is_env_set_true_for_alternate_env_name(self):
        """Config.is_env_set returns True for any of the priority env var names."""
        # NEO4J_PASSWORD checks MEMORY_NEO4J_PASSWORD and NEO4J_PASSWORD
        os.environ["NEO4J_PASSWORD"] = "secret"
        assert Config.is_env_set("NEO4J_PASSWORD") is True

    def test_is_env_set_true_after_direct_assignment(self):
        """When Config attribute is directly assigned, is_env_set returns True."""
        with patch_config(MEMGRAPH_URI="bolt://patched:7687"):
            assert Config.is_env_set("MEMGRAPH_URI") is True

    def test_is_env_set_false_for_unknown_attribute(self):
        """Config.is_env_set returns False for attributes that don't exist."""
        assert Config.is_env_set("NONEXISTENT_ATTR") is False

    def test_is_neo4j_configured_uses_is_env_set(self):
        """Config.is_neo4j_configured() should use is_env_set, not truthiness."""
        assert Config.is_neo4j_configured() is False
        os.environ["MEMORY_NEO4J_PASSWORD"] = "secret"
        assert Config.is_neo4j_configured() is True

    def test_is_memgraph_configured_uses_is_env_set(self):
        """Config.is_memgraph_configured() should use is_env_set, not truthiness."""
        # Without env var: False (despite truthy default)
        assert Config.is_memgraph_configured() is False
        os.environ["MEMORY_MEMGRAPH_URI"] = "bolt://memgraph:7687"
        assert Config.is_memgraph_configured() is True


class TestBackendAutoDetectionFix:
    """Tests that auto-detection no longer falsely detects unconfigured backends."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Remove backend env vars before and after each test."""
        keys = [
            "MEMORY_BACKEND",
            "MEMORY_NEO4J_PASSWORD", "NEO4J_PASSWORD",
            "MEMORY_MEMGRAPH_URI",
            "MEMORY_FALKORDB_HOST", "FALKORDB_HOST",
            "MEMORYGRAPH_API_KEY",
            "TURSO_DATABASE_URL", "MEMORY_TURSO_PATH",
        ]
        saved = {k: os.environ.pop(k, None) for k in keys}
        yield
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def test_memgraph_not_configured_by_default(self):
        """Memgraph should NOT appear configured when only defaults are active."""
        from memorygraph.backends.factory import BackendFactory
        assert BackendFactory.is_backend_configured("memgraph") is False

    def test_memgraph_configured_when_env_set(self):
        """Memgraph should appear configured when env var is explicitly set."""
        from memorygraph.backends.factory import BackendFactory
        os.environ["MEMORY_MEMGRAPH_URI"] = "bolt://memgraph:7687"
        assert BackendFactory.is_backend_configured("memgraph") is True

    def test_falkordb_not_configured_by_default(self):
        """FalkorDB should NOT appear configured when only defaults are active."""
        from memorygraph.backends.factory import BackendFactory
        assert BackendFactory.is_backend_configured("falkordb") is False

    def test_falkordb_configured_when_env_set(self):
        """FalkorDB should appear configured when env var is explicitly set."""
        from memorygraph.backends.factory import BackendFactory
        os.environ["MEMORY_FALKORDB_HOST"] = "redis-host"
        assert BackendFactory.is_backend_configured("falkordb") is True

    def test_neo4j_not_configured_by_default(self):
        """Neo4j should NOT appear configured without password env var."""
        from memorygraph.backends.factory import BackendFactory
        assert BackendFactory.is_backend_configured("neo4j") is False

    def test_neo4j_configured_when_password_set(self):
        """Neo4j should appear configured when password env var is set."""
        from memorygraph.backends.factory import BackendFactory
        os.environ["MEMORY_NEO4J_PASSWORD"] = "secret"
        assert BackendFactory.is_backend_configured("neo4j") is True

    def test_cloud_not_configured_by_default(self):
        """Cloud should NOT appear configured without API key env var."""
        from memorygraph.backends.factory import BackendFactory
        assert BackendFactory.is_backend_configured("cloud") is False

    def test_sqlite_always_configured(self):
        """SQLite is always considered configured (embedded, zero-config)."""
        from memorygraph.backends.factory import BackendFactory
        assert BackendFactory.is_backend_configured("sqlite") is True

    def test_falkordblite_always_configured(self):
        """FalkorDBLite is always considered configured (embedded)."""
        from memorygraph.backends.factory import BackendFactory
        assert BackendFactory.is_backend_configured("falkordblite") is True

    def test_turso_not_configured_by_default(self):
        """Turso should NOT appear configured without explicit env vars."""
        from memorygraph.backends.factory import BackendFactory
        assert BackendFactory.is_backend_configured("turso") is False

    def test_turso_configured_when_url_set(self):
        """Turso should appear configured when database URL is set."""
        from memorygraph.backends.factory import BackendFactory
        os.environ["TURSO_DATABASE_URL"] = "libsql://test.turso.io"
        assert BackendFactory.is_backend_configured("turso") is True
