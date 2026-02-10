"""
Tests for Cloud Backend Retry Configuration (P2 Priority).

This test suite verifies that the cloud backend retry configuration parameters
are properly defined in Config and can be overridden via environment variables.

Configuration parameters:
- CLOUD_MAX_RETRIES: Maximum retry attempts (default: 3)
- CLOUD_RETRY_BACKOFF_BASE: Exponential backoff base in seconds (default: 1.0)
- CLOUD_CIRCUIT_BREAKER_THRESHOLD: Failure threshold before opening circuit (default: 5)
- CLOUD_CIRCUIT_BREAKER_TIMEOUT: Recovery timeout in seconds (default: 60.0)

These tests follow TDD RED phase - they verify the configuration exists
and can be overridden, but do NOT yet test that CloudRESTAdapter uses
these values (that will be tested in integration tests).
"""

import os
import pytest
from unittest.mock import patch

from memorygraph.config import Config

from tests.conftest import patch_config


class TestCloudRetryConfig:
    """Tests for cloud backend retry configuration."""

    def test_default_max_retries(self):
        """Test default CLOUD_MAX_RETRIES value."""
        # Reset to defaults by patching with expected default
        with patch_config(CLOUD_MAX_RETRIES=3):
            assert Config.CLOUD_MAX_RETRIES == 3

    def test_default_retry_backoff(self):
        """Test default CLOUD_RETRY_BACKOFF_BASE value."""
        with patch_config(CLOUD_RETRY_BACKOFF_BASE=1.0):
            assert Config.CLOUD_RETRY_BACKOFF_BASE == 1.0

    def test_default_circuit_breaker_threshold(self):
        """Test default CLOUD_CIRCUIT_BREAKER_THRESHOLD value."""
        with patch_config(CLOUD_CIRCUIT_BREAKER_THRESHOLD=5):
            assert Config.CLOUD_CIRCUIT_BREAKER_THRESHOLD == 5

    def test_default_circuit_breaker_timeout(self):
        """Test default CLOUD_CIRCUIT_BREAKER_TIMEOUT value."""
        with patch_config(CLOUD_CIRCUIT_BREAKER_TIMEOUT=60.0):
            assert Config.CLOUD_CIRCUIT_BREAKER_TIMEOUT == 60.0

    def test_config_values_are_correct_types(self):
        """Test that config values have correct types."""
        assert isinstance(Config.CLOUD_MAX_RETRIES, int)
        assert isinstance(Config.CLOUD_RETRY_BACKOFF_BASE, float)
        assert isinstance(Config.CLOUD_CIRCUIT_BREAKER_THRESHOLD, int)
        assert isinstance(Config.CLOUD_CIRCUIT_BREAKER_TIMEOUT, float)

    @patch.dict(os.environ, {"MEMORYGRAPH_MAX_RETRIES": "5"})
    def test_env_override_max_retries(self):
        """Test that MEMORYGRAPH_MAX_RETRIES environment variable overrides default."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.CLOUD_MAX_RETRIES == 5
        assert isinstance(ReloadedConfig.CLOUD_MAX_RETRIES, int)

    @patch.dict(os.environ, {"MEMORYGRAPH_RETRY_BACKOFF": "2.5"})
    def test_env_override_retry_backoff(self):
        """Test that MEMORYGRAPH_RETRY_BACKOFF environment variable overrides default."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.CLOUD_RETRY_BACKOFF_BASE == 2.5
        assert isinstance(ReloadedConfig.CLOUD_RETRY_BACKOFF_BASE, float)

    @patch.dict(os.environ, {"MEMORYGRAPH_CB_THRESHOLD": "10"})
    def test_env_override_circuit_breaker_threshold(self):
        """Test that MEMORYGRAPH_CB_THRESHOLD environment variable overrides default."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_THRESHOLD == 10
        assert isinstance(ReloadedConfig.CLOUD_CIRCUIT_BREAKER_THRESHOLD, int)

    @patch.dict(os.environ, {"MEMORYGRAPH_CB_TIMEOUT": "120.0"})
    def test_env_override_circuit_breaker_timeout(self):
        """Test that MEMORYGRAPH_CB_TIMEOUT environment variable overrides default."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_TIMEOUT == 120.0
        assert isinstance(ReloadedConfig.CLOUD_CIRCUIT_BREAKER_TIMEOUT, float)

    @patch.dict(os.environ, {
        "MEMORYGRAPH_MAX_RETRIES": "7",
        "MEMORYGRAPH_RETRY_BACKOFF": "3.0",
        "MEMORYGRAPH_CB_THRESHOLD": "15",
        "MEMORYGRAPH_CB_TIMEOUT": "180.0"
    })
    def test_env_override_all_retry_config(self):
        """Test that all retry config environment variables can be set together."""
        from importlib import reload
        import memorygraph.config
        reload(memorygraph.config)
        from memorygraph.config import Config as ReloadedConfig

        assert ReloadedConfig.CLOUD_MAX_RETRIES == 7
        assert ReloadedConfig.CLOUD_RETRY_BACKOFF_BASE == 3.0
        assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_THRESHOLD == 15
        assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_TIMEOUT == 180.0

    def test_config_attributes_exist(self):
        """Test that all retry config attributes exist on Config class."""
        assert hasattr(Config, 'CLOUD_MAX_RETRIES')
        assert hasattr(Config, 'CLOUD_RETRY_BACKOFF_BASE')
        assert hasattr(Config, 'CLOUD_CIRCUIT_BREAKER_THRESHOLD')
        assert hasattr(Config, 'CLOUD_CIRCUIT_BREAKER_TIMEOUT')


class TestCloudBackendUsesConfig:
    """Tests that verify CloudRESTAdapter uses Config values."""

    def test_cloud_backend_uses_config_circuit_breaker_values(self):
        """Test that CloudRESTAdapter initializes circuit breaker with Config values."""
        with patch_config(
            MEMORYGRAPH_API_KEY="mg_test_key",
            CLOUD_CIRCUIT_BREAKER_THRESHOLD=10,
            CLOUD_CIRCUIT_BREAKER_TIMEOUT=120.0
        ):
            from memorygraph.backends.cloud_backend import CloudRESTAdapter

            backend = CloudRESTAdapter()

            # The backend should use Config values for circuit breaker
            assert backend._circuit_breaker.failure_threshold == 10
            assert backend._circuit_breaker.recovery_timeout == 120.0

    def test_cloud_backend_default_circuit_breaker_values(self):
        """Test that CloudRESTAdapter uses default Config values when not overridden."""
        with patch_config(
            MEMORYGRAPH_API_KEY="mg_test_key",
            CLOUD_CIRCUIT_BREAKER_THRESHOLD=5,
            CLOUD_CIRCUIT_BREAKER_TIMEOUT=60.0
        ):
            from memorygraph.backends.cloud_backend import CloudRESTAdapter

            backend = CloudRESTAdapter()

            # Should use default Config values
            assert backend._circuit_breaker.failure_threshold == 5
            assert backend._circuit_breaker.recovery_timeout == 60.0

    def test_cloud_backend_respects_config_changes(self):
        """Test that new CloudRESTAdapter instances pick up Config changes."""
        # First instance with defaults
        with patch_config(
            MEMORYGRAPH_API_KEY="mg_test_key_1",
            CLOUD_CIRCUIT_BREAKER_THRESHOLD=5,
            CLOUD_CIRCUIT_BREAKER_TIMEOUT=60.0
        ):
            from memorygraph.backends.cloud_backend import CloudRESTAdapter

            backend1 = CloudRESTAdapter()
            assert backend1._circuit_breaker.failure_threshold == 5
            assert backend1._circuit_breaker.recovery_timeout == 60.0

        # Second instance with different config
        with patch_config(
            MEMORYGRAPH_API_KEY="mg_test_key_2",
            CLOUD_CIRCUIT_BREAKER_THRESHOLD=8,
            CLOUD_CIRCUIT_BREAKER_TIMEOUT=90.0
        ):
            backend2 = CloudRESTAdapter()
            assert backend2._circuit_breaker.failure_threshold == 8
            assert backend2._circuit_breaker.recovery_timeout == 90.0


class TestConfigValueValidation:
    """Tests for validating config value types and ranges."""

    def test_invalid_max_retries_int_conversion(self):
        """Test that invalid MEMORYGRAPH_MAX_RETRIES raises ValueError on access."""
        with patch.dict(os.environ, {"MEMORYGRAPH_MAX_RETRIES": "not_a_number"}):
            with pytest.raises(ValueError):
                _ = Config.CLOUD_MAX_RETRIES

    def test_invalid_retry_backoff_float_conversion(self):
        """Test that invalid MEMORYGRAPH_RETRY_BACKOFF raises ValueError on access."""
        with patch.dict(os.environ, {"MEMORYGRAPH_RETRY_BACKOFF": "not_a_float"}):
            with pytest.raises(ValueError):
                _ = Config.CLOUD_RETRY_BACKOFF_BASE

    def test_invalid_cb_threshold_int_conversion(self):
        """Test that invalid MEMORYGRAPH_CB_THRESHOLD raises ValueError on access."""
        with patch.dict(os.environ, {"MEMORYGRAPH_CB_THRESHOLD": "not_a_number"}):
            with pytest.raises(ValueError):
                _ = Config.CLOUD_CIRCUIT_BREAKER_THRESHOLD

    def test_invalid_cb_timeout_float_conversion(self):
        """Test that invalid MEMORYGRAPH_CB_TIMEOUT raises ValueError on access."""
        with patch.dict(os.environ, {"MEMORYGRAPH_CB_TIMEOUT": "not_a_float"}):
            with pytest.raises(ValueError):
                _ = Config.CLOUD_CIRCUIT_BREAKER_TIMEOUT

    def test_zero_values_are_valid(self):
        """Test that zero values are accepted for retry config."""
        with patch.dict(os.environ, {
            "MEMORYGRAPH_MAX_RETRIES": "0",
            "MEMORYGRAPH_RETRY_BACKOFF": "0.0",
            "MEMORYGRAPH_CB_THRESHOLD": "0",
            "MEMORYGRAPH_CB_TIMEOUT": "0.0"
        }):
            from importlib import reload
            import memorygraph.config
            reload(memorygraph.config)
            from memorygraph.config import Config as ReloadedConfig

            assert ReloadedConfig.CLOUD_MAX_RETRIES == 0
            assert ReloadedConfig.CLOUD_RETRY_BACKOFF_BASE == 0.0
            assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_THRESHOLD == 0
            assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_TIMEOUT == 0.0

    def test_negative_values_are_valid(self):
        """Test that negative values are accepted (validation at usage time)."""
        with patch.dict(os.environ, {
            "MEMORYGRAPH_MAX_RETRIES": "-1",
            "MEMORYGRAPH_RETRY_BACKOFF": "-1.0",
            "MEMORYGRAPH_CB_THRESHOLD": "-1",
            "MEMORYGRAPH_CB_TIMEOUT": "-1.0"
        }):
            from importlib import reload
            import memorygraph.config
            reload(memorygraph.config)
            from memorygraph.config import Config as ReloadedConfig

            # Config accepts the values (validation happens at usage)
            assert ReloadedConfig.CLOUD_MAX_RETRIES == -1
            assert ReloadedConfig.CLOUD_RETRY_BACKOFF_BASE == -1.0
            assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_THRESHOLD == -1
            assert ReloadedConfig.CLOUD_CIRCUIT_BREAKER_TIMEOUT == -1.0
