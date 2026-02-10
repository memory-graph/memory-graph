"""
Tests to verify that remaining backend files use Config class instead of os.getenv().

This test file implements the RED phase of TDD for WP33 (Config as Single Source of Truth).
These tests should FAIL initially because backends currently read from os.environ directly,
then PASS after implementation when backends read from Config.

Files tested:
- src/memorygraph/backends/falkordb_backend.py (lines 54-56)
- src/memorygraph/backends/falkordblite_backend.py (line 53)
- src/memorygraph/backends/ladybugdb_backend.py (line 63)
- src/memorygraph/backends/cloud_backend.py (lines 170-176)
- src/memorygraph/database.py (lines 52-54)
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from src.memorygraph.config import Config
from src.memorygraph.backends.falkordb_backend import FalkorDBBackend
from src.memorygraph.backends.falkordblite_backend import FalkorDBLiteBackend
from src.memorygraph.backends.ladybugdb_backend import LadybugDBBackend
from src.memorygraph.backends.cloud_backend import CloudRESTAdapter
from src.memorygraph.database import Neo4jConnection

from tests.conftest import patch_config


class TestFalkorDBBackendConfig:
    """Test that FalkorDBBackend reads from Config instead of os.environ."""

    def test_falkordb_reads_host_from_config_not_env(self):
        """FalkorDBBackend should read host from Config.FALKORDB_HOST, not os.environ."""
        with patch_config(FALKORDB_HOST="config-host"):
            # Set a DIFFERENT value in environment
            os.environ["FALKORDB_HOST"] = "env-host"
            try:
                backend = FalkorDBBackend()
                assert backend.host == "config-host", \
                    f"Expected 'config-host' from Config.FALKORDB_HOST but got '{backend.host}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("FALKORDB_HOST", None)

    def test_falkordb_reads_port_from_config_not_env(self):
        """FalkorDBBackend should read port from Config.FALKORDB_PORT, not os.environ."""
        with patch_config(FALKORDB_PORT=9999):
            # Set a DIFFERENT value in environment
            os.environ["FALKORDB_PORT"] = "8888"
            try:
                backend = FalkorDBBackend()
                assert backend.port == 9999, \
                    f"Expected 9999 from Config.FALKORDB_PORT but got {backend.port} from os.environ"
            finally:
                # Clean up
                os.environ.pop("FALKORDB_PORT", None)

    def test_falkordb_reads_password_from_config_not_env(self):
        """FalkorDBBackend should read password from Config.FALKORDB_PASSWORD, not os.environ."""
        with patch_config(FALKORDB_PASSWORD="config-secret"):
            # Set a DIFFERENT value in environment
            os.environ["FALKORDB_PASSWORD"] = "env-secret"
            try:
                backend = FalkorDBBackend()
                assert backend.password == "config-secret", \
                    f"Expected 'config-secret' from Config.FALKORDB_PASSWORD but got '{backend.password}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("FALKORDB_PASSWORD", None)

    def test_falkordb_uses_default_when_config_is_none(self):
        """FalkorDBBackend should use defaults when Config values are None."""
        with patch_config(FALKORDB_HOST=None, FALKORDB_PORT=None, FALKORDB_PASSWORD=None):
            # Clear environment variables
            os.environ.pop("FALKORDB_HOST", None)
            os.environ.pop("FALKORDB_PORT", None)
            os.environ.pop("FALKORDB_PASSWORD", None)

            backend = FalkorDBBackend()

            # Should use documented defaults
            assert backend.host == "localhost", \
                f"Expected default 'localhost' but got '{backend.host}'"
            assert backend.port == 6379, \
                f"Expected default 6379 but got {backend.port}"
            assert backend.password is None, \
                f"Expected default None but got '{backend.password}'"

    def test_falkordb_constructor_params_override_config(self):
        """FalkorDBBackend constructor parameters should override Config values."""
        with patch_config(FALKORDB_HOST="config-host", FALKORDB_PORT=9999, FALKORDB_PASSWORD="config-secret"):
            backend = FalkorDBBackend(host="param-host", port=7777, password="param-secret")

            # Constructor params take precedence
            assert backend.host == "param-host", \
                "Constructor parameters should override Config"
            assert backend.port == 7777, \
                "Constructor parameters should override Config"
            assert backend.password == "param-secret", \
                "Constructor parameters should override Config"


class TestFalkorDBLiteBackendConfig:
    """Test that FalkorDBLiteBackend reads from Config instead of os.environ."""

    def test_falkordblite_reads_path_from_config_not_env(self):
        """FalkorDBLiteBackend should read db_path from Config.FALKORDBLITE_PATH, not os.environ."""
        with patch_config(FALKORDBLITE_PATH="/config/path/falkordblite.db"):
            # Set a DIFFERENT value in environment
            os.environ["FALKORDBLITE_PATH"] = "/env/path/falkordblite.db"
            try:
                backend = FalkorDBLiteBackend()
                assert backend.db_path == "/config/path/falkordblite.db", \
                    f"Expected '/config/path/falkordblite.db' from Config.FALKORDBLITE_PATH but got '{backend.db_path}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("FALKORDBLITE_PATH", None)

    def test_falkordblite_uses_default_when_config_is_none(self):
        """FalkorDBLiteBackend should use ~/.memorygraph/falkordblite.db when Config is None."""
        with patch_config(FALKORDBLITE_PATH=None):
            # Clear environment variable
            os.environ.pop("FALKORDBLITE_PATH", None)

            backend = FalkorDBLiteBackend()

            # Should use default path
            expected_default = str(Path.home() / ".memorygraph" / "falkordblite.db")
            assert backend.db_path == expected_default, \
                f"Expected default '{expected_default}' but got '{backend.db_path}'"

    def test_falkordblite_constructor_param_overrides_config(self):
        """FalkorDBLiteBackend constructor db_path parameter should override Config."""
        with patch_config(FALKORDBLITE_PATH="/config/path/falkordblite.db"):
            backend = FalkorDBLiteBackend(db_path="/param/path/falkordblite.db")

            # Constructor param takes precedence
            assert backend.db_path == "/param/path/falkordblite.db", \
                "Constructor parameter should override Config"


class TestLadybugDBBackendConfig:
    """Test that LadybugDBBackend reads from Config instead of os.environ."""

    def test_ladybugdb_reads_path_from_config_not_env(self):
        """LadybugDBBackend should read db_path from Config.LADYBUGDB_PATH, not os.environ."""
        with patch_config(LADYBUGDB_PATH="/config/path/ladybugdb.db"):
            # Set a DIFFERENT value in environment
            os.environ["LADYBUGDB_PATH"] = "/env/path/ladybugdb.db"
            try:
                # Note: LadybugDBBackend constructor checks for package availability
                # We need to mock the import check or skip if not installed
                try:
                    backend = LadybugDBBackend()
                    assert backend.db_path == "/config/path/ladybugdb.db", \
                        f"Expected '/config/path/ladybugdb.db' from Config.LADYBUGDB_PATH but got '{backend.db_path}' from os.environ"
                except ImportError:
                    # LadybugDB not installed, skip this test
                    pytest.skip("LadybugDB (real_ladybug) not installed")
            finally:
                # Clean up
                os.environ.pop("LADYBUGDB_PATH", None)

    def test_ladybugdb_uses_default_when_config_is_none(self):
        """LadybugDBBackend should use ~/.memorygraph/ladybugdb.db when Config is None."""
        with patch_config(LADYBUGDB_PATH=None):
            # Clear environment variable
            os.environ.pop("LADYBUGDB_PATH", None)

            try:
                backend = LadybugDBBackend()

                # Should use default path
                expected_default = str(Path.home() / ".memorygraph" / "ladybugdb.db")
                assert backend.db_path == expected_default, \
                    f"Expected default '{expected_default}' but got '{backend.db_path}'"
            except ImportError:
                # LadybugDB not installed, skip this test
                pytest.skip("LadybugDB (real_ladybug) not installed")

    def test_ladybugdb_constructor_param_overrides_config(self):
        """LadybugDBBackend constructor db_path parameter should override Config."""
        with patch_config(LADYBUGDB_PATH="/config/path/ladybugdb.db"):
            try:
                backend = LadybugDBBackend(db_path="/param/path/ladybugdb.db")

                # Constructor param takes precedence
                assert backend.db_path == "/param/path/ladybugdb.db", \
                    "Constructor parameter should override Config"
            except ImportError:
                # LadybugDB not installed, skip this test
                pytest.skip("LadybugDB (real_ladybug) not installed")


class TestCloudRESTAdapterConfig:
    """Test that CloudRESTAdapter reads from Config instead of os.environ."""

    def test_cloud_reads_api_key_from_config_not_env(self):
        """CloudRESTAdapter should read api_key from Config.MEMORYGRAPH_API_KEY, not os.environ."""
        with patch_config(MEMORYGRAPH_API_KEY="mg_config_key_12345"):
            # Set a DIFFERENT value in environment
            os.environ["MEMORYGRAPH_API_KEY"] = "mg_env_key_67890"
            try:
                adapter = CloudRESTAdapter()
                assert adapter.api_key == "mg_config_key_12345", \
                    f"Expected 'mg_config_key_12345' from Config.MEMORYGRAPH_API_KEY but got '{adapter.api_key}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("MEMORYGRAPH_API_KEY", None)

    def test_cloud_reads_api_url_from_config_not_env(self):
        """CloudRESTAdapter should read api_url from Config.MEMORYGRAPH_API_URL, not os.environ."""
        with patch_config(MEMORYGRAPH_API_KEY="mg_key", MEMORYGRAPH_API_URL="https://config.example.com"):
            # Set a DIFFERENT value in environment
            os.environ["MEMORYGRAPH_API_URL"] = "https://env.example.com"
            os.environ["MEMORYGRAPH_API_KEY"] = "mg_env_key"  # Set env key too
            try:
                adapter = CloudRESTAdapter()
                assert adapter.api_url == "https://config.example.com", \
                    f"Expected 'https://config.example.com' from Config.MEMORYGRAPH_API_URL but got '{adapter.api_url}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("MEMORYGRAPH_API_URL", None)
                os.environ.pop("MEMORYGRAPH_API_KEY", None)

    def test_cloud_reads_timeout_from_config_not_env(self):
        """CloudRESTAdapter should read timeout from Config.MEMORYGRAPH_TIMEOUT, not os.environ."""
        with patch_config(MEMORYGRAPH_API_KEY="mg_key", MEMORYGRAPH_TIMEOUT=60):
            # Set a DIFFERENT value in environment
            os.environ["MEMORYGRAPH_TIMEOUT"] = "90"
            os.environ["MEMORYGRAPH_API_KEY"] = "mg_env_key"  # Set env key too
            try:
                adapter = CloudRESTAdapter()
                assert adapter.timeout == 60, \
                    f"Expected 60 from Config.MEMORYGRAPH_TIMEOUT but got {adapter.timeout} from os.environ"
            finally:
                # Clean up
                os.environ.pop("MEMORYGRAPH_TIMEOUT", None)
                os.environ.pop("MEMORYGRAPH_API_KEY", None)

    def test_cloud_uses_default_url_when_config_is_none(self):
        """CloudRESTAdapter should use default URL when Config is None."""
        with patch_config(MEMORYGRAPH_API_KEY="mg_key", MEMORYGRAPH_API_URL=None):
            # Clear environment variables
            os.environ.pop("MEMORYGRAPH_API_URL", None)
            os.environ.pop("MEMORYGRAPH_API_KEY", None)

            adapter = CloudRESTAdapter()

            # Should use default URL
            assert adapter.api_url == "https://graph-api.memorygraph.dev", \
                f"Expected default URL but got '{adapter.api_url}'"

    def test_cloud_uses_default_timeout_when_config_is_none(self):
        """CloudRESTAdapter should use default timeout (30s) when Config is None."""
        with patch_config(MEMORYGRAPH_API_KEY="mg_key", MEMORYGRAPH_TIMEOUT=None):
            # Clear environment variables
            os.environ.pop("MEMORYGRAPH_TIMEOUT", None)
            os.environ.pop("MEMORYGRAPH_API_KEY", None)

            # Need to handle the case where timeout is None
            # CloudRESTAdapter should default to 30
            adapter = CloudRESTAdapter()

            # Should use default timeout of 30
            assert adapter.timeout == 30, \
                f"Expected default timeout 30 but got {adapter.timeout}"

    def test_cloud_constructor_params_override_config(self):
        """CloudRESTAdapter constructor parameters should override Config values."""
        with patch_config(
            MEMORYGRAPH_API_KEY="mg_config_key",
            MEMORYGRAPH_API_URL="https://config.example.com",
            MEMORYGRAPH_TIMEOUT=60
        ):
            adapter = CloudRESTAdapter(
                api_key="mg_param_key",
                api_url="https://param.example.com",
                timeout=120
            )

            # Constructor params take precedence
            assert adapter.api_key == "mg_param_key", \
                "Constructor parameters should override Config"
            assert adapter.api_url == "https://param.example.com", \
                "Constructor parameters should override Config"
            assert adapter.timeout == 120, \
                "Constructor parameters should override Config"

    def test_cloud_raises_error_when_api_key_missing(self):
        """CloudRESTAdapter should raise DatabaseConnectionError when api_key is missing."""
        from src.memorygraph.models import DatabaseConnectionError

        with patch_config(MEMORYGRAPH_API_KEY=None):
            # Clear environment variable
            os.environ.pop("MEMORYGRAPH_API_KEY", None)

            with pytest.raises(DatabaseConnectionError, match="MEMORYGRAPH_API_KEY is required"):
                CloudRESTAdapter()


class TestNeo4jConnectionConfig:
    """Test that Neo4jConnection reads from Config instead of os.environ."""

    def test_neo4j_reads_uri_from_config_not_env(self):
        """Neo4jConnection should read uri from Config.NEO4J_URI, not os.environ."""
        with patch_config(NEO4J_URI="bolt://config-host:7687", NEO4J_PASSWORD="password"):
            # Set a DIFFERENT value in environment
            os.environ["NEO4J_URI"] = "bolt://env-host:7687"
            try:
                conn = Neo4jConnection()
                assert conn.uri == "bolt://config-host:7687", \
                    f"Expected 'bolt://config-host:7687' from Config.NEO4J_URI but got '{conn.uri}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("NEO4J_URI", None)

    def test_neo4j_reads_user_from_config_not_env(self):
        """Neo4jConnection should read user from Config.NEO4J_USER, not os.environ."""
        with patch_config(NEO4J_USER="config_user", NEO4J_PASSWORD="password"):
            # Set a DIFFERENT value in environment
            os.environ["NEO4J_USER"] = "env_user"
            try:
                conn = Neo4jConnection()
                assert conn.user == "config_user", \
                    f"Expected 'config_user' from Config.NEO4J_USER but got '{conn.user}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("NEO4J_USER", None)

    def test_neo4j_reads_password_from_config_not_env(self):
        """Neo4jConnection should read password from Config.NEO4J_PASSWORD, not os.environ."""
        with patch_config(NEO4J_PASSWORD="config_password"):
            # Set a DIFFERENT value in environment
            os.environ["NEO4J_PASSWORD"] = "env_password"
            try:
                conn = Neo4jConnection()
                assert conn.password == "config_password", \
                    f"Expected 'config_password' from Config.NEO4J_PASSWORD but got '{conn.password}' from os.environ"
            finally:
                # Clean up
                os.environ.pop("NEO4J_PASSWORD", None)

    def test_neo4j_uses_default_uri_when_config_is_none(self):
        """Neo4jConnection should use bolt://localhost:7687 when Config.NEO4J_URI is None."""
        with patch_config(NEO4J_URI=None, NEO4J_PASSWORD="password"):
            # Clear environment variable
            os.environ.pop("NEO4J_URI", None)

            conn = Neo4jConnection()

            # Should use default URI
            assert conn.uri == "bolt://localhost:7687", \
                f"Expected default 'bolt://localhost:7687' but got '{conn.uri}'"

    def test_neo4j_uses_default_user_when_config_is_none(self):
        """Neo4jConnection should use 'neo4j' when Config.NEO4J_USER is None."""
        with patch_config(NEO4J_USER=None, NEO4J_PASSWORD="password"):
            # Clear environment variable
            os.environ.pop("NEO4J_USER", None)

            conn = Neo4jConnection()

            # Should use default user
            assert conn.user == "neo4j", \
                f"Expected default 'neo4j' but got '{conn.user}'"

    def test_neo4j_constructor_params_override_config(self):
        """Neo4jConnection constructor parameters should override Config values."""
        with patch_config(
            NEO4J_URI="bolt://config-host:7687",
            NEO4J_USER="config_user",
            NEO4J_PASSWORD="config_password"
        ):
            conn = Neo4jConnection(
                uri="bolt://param-host:7687",
                user="param_user",
                password="param_password"
            )

            # Constructor params take precedence
            assert conn.uri == "bolt://param-host:7687", \
                "Constructor parameters should override Config"
            assert conn.user == "param_user", \
                "Constructor parameters should override Config"
            assert conn.password == "param_password", \
                "Constructor parameters should override Config"

    def test_neo4j_raises_error_when_password_missing(self):
        """Neo4jConnection should raise DatabaseConnectionError when password is missing."""
        from src.memorygraph.models import DatabaseConnectionError

        with patch_config(NEO4J_PASSWORD=None):
            # Clear environment variable
            os.environ.pop("NEO4J_PASSWORD", None)

            with pytest.raises(DatabaseConnectionError, match="password must be provided"):
                Neo4jConnection()


class TestConfigIntegrity:
    """Test that Config values remain consistent and don't leak between tests."""

    def test_patch_config_restores_original_values(self):
        """patch_config should restore original Config values after context exits."""
        original_host = Config.FALKORDB_HOST

        with patch_config(FALKORDB_HOST="temporary-value"):
            assert Config.FALKORDB_HOST == "temporary-value"

        # After context exits, original value should be restored
        assert Config.FALKORDB_HOST == original_host

    def test_multiple_patch_config_contexts_are_isolated(self):
        """Multiple patch_config contexts should not interfere with each other."""
        original_host = Config.FALKORDB_HOST

        with patch_config(FALKORDB_HOST="value1"):
            assert Config.FALKORDB_HOST == "value1"

            with patch_config(FALKORDB_HOST="value2"):
                assert Config.FALKORDB_HOST == "value2"

            # After inner context, should restore to outer context value
            assert Config.FALKORDB_HOST == "value1"

        # After all contexts, should restore to original
        assert Config.FALKORDB_HOST == original_host
