"""
Tests for configuration management and multi-tenancy configuration.

This module tests the Config class and its multi-tenancy related methods,
ensuring proper environment variable handling and backward compatibility.
"""

import os
import pytest
from unittest import mock

from memorygraph.config import Config, BackendType


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
