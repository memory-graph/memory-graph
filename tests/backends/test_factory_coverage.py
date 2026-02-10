"""
Comprehensive tests for BackendFactory to improve coverage from 33% to 90%+.

This test suite covers:
- All backend type detection paths (lines 54-91)
- Backend creation methods for all 8 backends
- Error handling for missing configurations
- Helper methods (create_from_config, _create_*_with_* methods)
- Configuration validation

NOTE: After WP33 refactor, factory reads from Config class, not os.getenv().
Tests must patch Config.* values in addition to os.environ for full coverage.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from src.memorygraph.models import DatabaseConnectionError
from src.memorygraph.config import Config

from tests.conftest import patch_config


# Helper function to patch lazily imported backends
def patch_backend(module_path, class_name):
    """
    Patch a backend that is lazily imported in the factory.

    Args:
        module_path: The module where the backend is defined (e.g., 'src.memorygraph.backends.neo4j_backend')
        class_name: The class name to patch (e.g., 'Neo4jBackend')
    """
    full_path = f"{module_path}.{class_name}"
    return patch(full_path)




# Mock modules that have optional dependencies before any tests run
@pytest.fixture(scope='module', autouse=True)
def mock_optional_backends():
    """Mock optional backend modules to avoid import errors."""
    import sys
    from unittest.mock import MagicMock

    # Save original module references so we can restore them on cleanup.
    # Deleting from sys.modules would cause re-imports to create NEW classes,
    # breaking isinstance/except checks in already-imported backend modules.
    saved_modules = {}
    for mod_name in ['neo4j', 'neo4j.exceptions', 'gqlalchemy']:
        if mod_name in sys.modules:
            saved_modules[mod_name] = sys.modules[mod_name]

    # Create comprehensive mock for neo4j package
    neo4j_mock = MagicMock()
    neo4j_mock.AsyncGraphDatabase = MagicMock()
    neo4j_mock.AsyncDriver = MagicMock()

    # Mock neo4j.exceptions module
    neo4j_exceptions_mock = MagicMock()
    neo4j_exceptions_mock.ServiceUnavailable = type('ServiceUnavailable', (Exception,), {})
    neo4j_exceptions_mock.AuthError = type('AuthError', (Exception,), {})
    neo4j_exceptions_mock.Neo4jError = type('Neo4jError', (Exception,), {})
    neo4j_mock.exceptions = neo4j_exceptions_mock

    sys.modules['neo4j'] = neo4j_mock
    sys.modules['neo4j.exceptions'] = neo4j_exceptions_mock

    # Mock gqlalchemy for memgraph
    memgraph_mock = MagicMock()
    sys.modules['gqlalchemy'] = memgraph_mock

    yield

    # Restore original modules (or remove mocks if they weren't present before)
    for mod_name in ['neo4j', 'neo4j.exceptions', 'gqlalchemy']:
        if mod_name in saved_modules:
            sys.modules[mod_name] = saved_modules[mod_name]
        elif mod_name in sys.modules:
            del sys.modules[mod_name]


class TestBackendTypeDetection:
    """Test backend type detection from environment configuration."""

    @pytest.mark.asyncio
    async def test_detect_sqlite_from_env(self):
        """Test SQLite detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with patch_config(BACKEND='sqlite'):
            with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                    backend = await BackendFactory.create_backend()
                    assert isinstance(backend, SQLiteFallbackBackend)

    @pytest.mark.asyncio
    async def test_detect_neo4j_from_env(self):
        """Test Neo4j detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='neo4j', NEO4J_PASSWORD='test_password'):
            # Patch the Neo4jBackend where it's imported (in the method)
            with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockNeo4j.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is not None
                MockNeo4j.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_memgraph_from_env(self):
        """Test Memgraph detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='memgraph', MEMGRAPH_URI='bolt://localhost:7687'):
            with patch('src.memorygraph.backends.memgraph_backend.MemgraphBackend') as MockMemgraph:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockMemgraph.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is not None
                MockMemgraph.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_falkordb_from_env(self):
        """Test FalkorDB detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='falkordb', FALKORDB_HOST='localhost'):
            with patch('src.memorygraph.backends.falkordb_backend.FalkorDBBackend') as MockFalkorDB:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockFalkorDB.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is not None
                MockFalkorDB.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_falkordblite_from_env(self):
        """Test FalkorDBLite detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='falkordblite'):
            with patch('src.memorygraph.backends.falkordblite_backend.FalkorDBLiteBackend') as MockFalkorDBLite:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockFalkorDBLite.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is not None
                MockFalkorDBLite.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_turso_from_env(self):
        """Test Turso detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='turso'):
            with patch('src.memorygraph.backends.turso.TursoBackend') as MockTurso:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_instance.initialize_schema = AsyncMock()
                MockTurso.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is not None
                MockTurso.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_cloud_from_env(self):
        """Test cloud backend detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='cloud', MEMORYGRAPH_API_KEY='test_api_key'):
            with patch('src.memorygraph.backends.cloud_backend.CloudRESTAdapter') as MockCloud:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockCloud.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is not None
                MockCloud.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_ladybugdb_from_env(self):
        """Test LadybugDB detection from environment."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='ladybugdb'):
            with patch('src.memorygraph.backends.ladybugdb_backend.LadybugDBBackend') as MockLadybugDB:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockLadybugDB.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is not None
                MockLadybugDB.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_auto_from_env(self):
        """Test auto-selection mode from environment."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with patch_config(BACKEND='auto'):
            with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                    backend = await BackendFactory.create_backend()
                    # Should fall back to SQLite when no other backends configured
                    assert isinstance(backend, SQLiteFallbackBackend)


class TestBackendCreation:
    """Test backend creation paths for all supported backends."""

    @pytest.mark.asyncio
    async def test_create_neo4j_with_all_env_vars(self):
        """Test Neo4j backend creation with all environment variables."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(NEO4J_URI='bolt://test:7687', NEO4J_USER='testuser', NEO4J_PASSWORD='testpass'):
            with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockNeo4j.return_value = mock_instance

                backend = await BackendFactory._create_neo4j()

                MockNeo4j.assert_called_once_with(
                    uri='bolt://test:7687',
                    user='testuser',
                    password='testpass'
                )
                mock_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_neo4j_with_fallback_env_vars(self):
        """Test Neo4j creation with fallback environment variable names."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(NEO4J_URI='bolt://fallback:7687', NEO4J_USER='fallbackuser', NEO4J_PASSWORD='fallbackpass'):
            with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockNeo4j.return_value = mock_instance

                backend = await BackendFactory._create_neo4j()

                MockNeo4j.assert_called_once_with(
                    uri='bolt://fallback:7687',
                    user='fallbackuser',
                    password='fallbackpass'
                )

    @pytest.mark.asyncio
    async def test_create_memgraph_with_credentials(self):
        """Test Memgraph backend creation with credentials."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(MEMGRAPH_URI='bolt://memgraph:7687', MEMGRAPH_USER='memuser', MEMGRAPH_PASSWORD='mempass'):
            with patch('src.memorygraph.backends.memgraph_backend.MemgraphBackend') as MockMemgraph:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockMemgraph.return_value = mock_instance

                backend = await BackendFactory._create_memgraph()

                MockMemgraph.assert_called_once_with(
                    uri='bolt://memgraph:7687',
                    user='memuser',
                    password='mempass'
                )

    @pytest.mark.asyncio
    async def test_create_falkordb_with_all_env_vars(self):
        """Test FalkorDB creation with all environment variables."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(FALKORDB_HOST='falkorhost', FALKORDB_PORT=6380, FALKORDB_PASSWORD='falkorpass'):
            with patch('src.memorygraph.backends.falkordb_backend.FalkorDBBackend') as MockFalkorDB:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockFalkorDB.return_value = mock_instance

                backend = await BackendFactory._create_falkordb()

                MockFalkorDB.assert_called_once_with(
                    host='falkorhost',
                    port=6380,
                    password='falkorpass'
                )

    @pytest.mark.asyncio
    async def test_create_falkordb_with_fallback_env_vars(self):
        """Test FalkorDB creation with fallback environment variables."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(FALKORDB_HOST='fallbackhost', FALKORDB_PORT=6381, FALKORDB_PASSWORD='fallbackpass'):
            with patch('src.memorygraph.backends.falkordb_backend.FalkorDBBackend') as MockFalkorDB:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockFalkorDB.return_value = mock_instance

                backend = await BackendFactory._create_falkordb()

                MockFalkorDB.assert_called_once_with(
                    host='fallbackhost',
                    port=6381,
                    password='fallbackpass'
                )

    @pytest.mark.asyncio
    async def test_create_falkordblite_with_path(self):
        """Test FalkorDBLite creation with path."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(FALKORDBLITE_PATH='/path/to/falkordblite.db'):
            with patch('src.memorygraph.backends.falkordblite_backend.FalkorDBLiteBackend') as MockFalkorDBLite:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockFalkorDBLite.return_value = mock_instance

                backend = await BackendFactory._create_falkordblite()

                MockFalkorDBLite.assert_called_once_with(db_path='/path/to/falkordblite.db')

    @pytest.mark.asyncio
    async def test_create_ladybugdb_with_path(self):
        """Test LadybugDB creation with path."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(LADYBUGDB_PATH='/path/to/ladybug.db'):
            with patch('src.memorygraph.backends.ladybugdb_backend.LadybugDBBackend') as MockLadybugDB:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockLadybugDB.return_value = mock_instance

                backend = await BackendFactory._create_ladybugdb()

                MockLadybugDB.assert_called_once_with(db_path='/path/to/ladybug.db')

    @pytest.mark.asyncio
    async def test_create_sqlite_with_path(self):
        """Test SQLite creation with custom path."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with patch_config(SQLITE_PATH='/tmp/custom_path_sqlite.db'):
            with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                    backend = await BackendFactory._create_sqlite()

                    assert backend.db_path == '/tmp/custom_path_sqlite.db'

    @pytest.mark.asyncio
    async def test_create_turso_with_all_config(self):
        """Test Turso creation with full configuration."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(TURSO_PATH='/path/to/turso.db', TURSO_DATABASE_URL='libsql://example.turso.io', TURSO_AUTH_TOKEN='test_token'):
            with patch('src.memorygraph.backends.turso.TursoBackend') as MockTurso:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_instance.initialize_schema = AsyncMock()
                MockTurso.return_value = mock_instance

                backend = await BackendFactory._create_turso()

                MockTurso.assert_called_once_with(
                    db_path='/path/to/turso.db',
                    sync_url='libsql://example.turso.io',
                    auth_token='test_token'
                )

    @pytest.mark.asyncio
    async def test_create_cloud_with_all_config(self):
        """Test Cloud backend creation with full configuration."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(MEMORYGRAPH_API_KEY='test_api_key', MEMORYGRAPH_API_URL='https://api.memorygraph.dev', MEMORYGRAPH_TIMEOUT=60):
            with patch('src.memorygraph.backends.cloud_backend.CloudRESTAdapter') as MockCloud:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockCloud.return_value = mock_instance

                backend = await BackendFactory._create_cloud()

                MockCloud.assert_called_once_with(
                    api_key='test_api_key',
                    api_url='https://api.memorygraph.dev',
                    timeout=60
                )


class TestBackendCreationErrors:
    """Test error handling in backend creation."""

    @pytest.mark.asyncio
    async def test_invalid_backend_type(self):
        """Test error on invalid backend type."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='invalid_type'):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                await BackendFactory.create_backend()

            assert "Unknown backend type: invalid_type" in str(exc_info.value)
            assert "Valid options:" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_neo4j_missing_password(self):
        """Test error when Neo4j password is missing."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(NEO4J_PASSWORD=None):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                await BackendFactory._create_neo4j()

            assert "password not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cloud_missing_api_key(self):
        """Test error when cloud API key is missing."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(MEMORYGRAPH_API_KEY=None):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                await BackendFactory._create_cloud()

            assert "MEMORYGRAPH_API_KEY is required" in str(exc_info.value)


class TestAutoSelectionPaths:
    """Test automatic backend selection paths."""

    @pytest.mark.asyncio
    async def test_auto_select_neo4j_when_configured(self):
        """Test auto-selection tries Neo4j first when password configured."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(NEO4J_PASSWORD='test'):
            with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                MockNeo4j.return_value = mock_instance

                backend = await BackendFactory._auto_select_backend()

                MockNeo4j.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_select_memgraph_when_neo4j_fails(self):
        """Test auto-selection falls back to Memgraph when Neo4j fails."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(NEO4J_PASSWORD='test', MEMGRAPH_URI='bolt://localhost:7687'):
            with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
                MockNeo4j.return_value.connect = AsyncMock(
                    side_effect=DatabaseConnectionError("Neo4j failed")
                )

                with patch('src.memorygraph.backends.memgraph_backend.MemgraphBackend') as MockMemgraph:
                    mock_instance = MagicMock()
                    mock_instance.connect = AsyncMock()
                    MockMemgraph.return_value = mock_instance

                    backend = await BackendFactory._auto_select_backend()

                    MockMemgraph.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_select_sqlite_when_all_fail(self):
        """Test auto-selection falls back to SQLite when all others fail."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with patch_config(NEO4J_PASSWORD='test', MEMGRAPH_URI='bolt://localhost:7687'):
            with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
                MockNeo4j.return_value.connect = AsyncMock(
                    side_effect=DatabaseConnectionError("Neo4j failed")
                )

                with patch('src.memorygraph.backends.memgraph_backend.MemgraphBackend') as MockMemgraph:
                    MockMemgraph.return_value.connect = AsyncMock(
                        side_effect=DatabaseConnectionError("Memgraph failed")
                    )

                    with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
                        with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                            backend = await BackendFactory._auto_select_backend()

                            assert isinstance(backend, SQLiteFallbackBackend)

    @pytest.mark.asyncio
    async def test_auto_select_error_when_all_fail(self):
        """Test auto-selection raises error when all backends fail including SQLite."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with patch_config(NEO4J_PASSWORD='test'):
            with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
                MockNeo4j.return_value.connect = AsyncMock(
                    side_effect=DatabaseConnectionError("Neo4j failed")
                )

                with patch.object(SQLiteFallbackBackend, 'connect',
                                side_effect=DatabaseConnectionError("SQLite failed")):
                    with pytest.raises(DatabaseConnectionError) as exc_info:
                        await BackendFactory._auto_select_backend()

                    assert "Could not connect to any backend" in str(exc_info.value)


class TestHelperMethods:
    """Test factory helper methods for create_from_config."""

    @pytest.mark.asyncio
    async def test_create_sqlite_with_path_helper(self):
        """Test _create_sqlite_with_path helper."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
            with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                backend = await BackendFactory._create_sqlite_with_path('/tmp/test_path.db')

                assert isinstance(backend, SQLiteFallbackBackend)
                assert backend.db_path == '/tmp/test_path.db'

    @pytest.mark.asyncio
    async def test_create_falkordblite_with_path_helper(self):
        """Test _create_falkordblite_with_path helper."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch('src.memorygraph.backends.falkordblite_backend.FalkorDBLiteBackend') as MockFalkorDBLite:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockFalkorDBLite.return_value = mock_instance

            backend = await BackendFactory._create_falkordblite_with_path('/test/falkor.db')

            MockFalkorDBLite.assert_called_once_with(db_path='/test/falkor.db')

    @pytest.mark.asyncio
    async def test_create_ladybugdb_with_path_helper(self):
        """Test _create_ladybugdb_with_path helper."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch('src.memorygraph.backends.ladybugdb_backend.LadybugDBBackend') as MockLadybugDB:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockLadybugDB.return_value = mock_instance

            backend = await BackendFactory._create_ladybugdb_with_path('/test/ladybug.db')

            MockLadybugDB.assert_called_once_with(db_path='/test/ladybug.db')

    @pytest.mark.asyncio
    async def test_create_neo4j_with_config_helper(self):
        """Test _create_neo4j_with_config helper."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockNeo4j.return_value = mock_instance

            backend = await BackendFactory._create_neo4j_with_config(
                uri='bolt://test:7687',
                user='testuser',
                password='testpass'
            )

            MockNeo4j.assert_called_once_with(
                uri='bolt://test:7687',
                user='testuser',
                password='testpass'
            )

    @pytest.mark.asyncio
    async def test_create_neo4j_with_config_missing_password(self):
        """Test _create_neo4j_with_config raises error when password missing."""
        from src.memorygraph.backends.factory import BackendFactory

        with pytest.raises(DatabaseConnectionError) as exc_info:
            await BackendFactory._create_neo4j_with_config(
                uri='bolt://test:7687',
                user='testuser',
                password=None
            )

        assert "password is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_memgraph_with_config_helper(self):
        """Test _create_memgraph_with_config helper."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch('src.memorygraph.backends.memgraph_backend.MemgraphBackend') as MockMemgraph:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockMemgraph.return_value = mock_instance

            backend = await BackendFactory._create_memgraph_with_config(
                uri='bolt://memgraph:7687',
                user='memuser',
                password='mempass'
            )

            MockMemgraph.assert_called_once_with(
                uri='bolt://memgraph:7687',
                user='memuser',
                password='mempass'
            )

    @pytest.mark.asyncio
    async def test_create_falkordb_with_config_helper(self):
        """Test _create_falkordb_with_config helper."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch('src.memorygraph.backends.falkordb_backend.FalkorDBBackend') as MockFalkorDB:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockFalkorDB.return_value = mock_instance

            backend = await BackendFactory._create_falkordb_with_config(
                host='falkorhost',
                port=6380,
                password='falkorpass'
            )

            MockFalkorDB.assert_called_once_with(
                host='falkorhost',
                port=6380,
                password='falkorpass'
            )

    @pytest.mark.asyncio
    async def test_create_turso_with_config_helper(self):
        """Test _create_turso_with_config helper."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch('src.memorygraph.backends.turso.TursoBackend') as MockTurso:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            mock_instance.initialize_schema = AsyncMock()
            MockTurso.return_value = mock_instance

            backend = await BackendFactory._create_turso_with_config(
                db_path='/path/to/turso.db',
                sync_url='libsql://example.turso.io',
                auth_token='test_token'
            )

            MockTurso.assert_called_once_with(
                db_path='/path/to/turso.db',
                sync_url='libsql://example.turso.io',
                auth_token='test_token'
            )

    @pytest.mark.asyncio
    async def test_create_cloud_with_config_helper(self):
        """Test _create_cloud_with_config helper."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch('src.memorygraph.backends.cloud_backend.CloudRESTAdapter') as MockCloud:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockCloud.return_value = mock_instance

            backend = await BackendFactory._create_cloud_with_config(
                api_key='test_key',
                api_url='https://test.api',
                timeout=30
            )

            MockCloud.assert_called_once_with(
                api_key='test_key',
                api_url='https://test.api',
                timeout=30
            )

    @pytest.mark.asyncio
    async def test_create_cloud_with_config_missing_api_key(self):
        """Test _create_cloud_with_config raises error when API key missing."""
        from src.memorygraph.backends.factory import BackendFactory

        with pytest.raises(DatabaseConnectionError) as exc_info:
            await BackendFactory._create_cloud_with_config(
                api_key=None,
                api_url='https://test.api'
            )

        assert "MEMORYGRAPH_API_KEY is required" in str(exc_info.value)


class TestCreateFromConfig:
    """Test create_from_config method for all backend types."""

    @pytest.mark.asyncio
    async def test_create_from_config_sqlite(self):
        """Test creating SQLite backend from config."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.SQLITE,
            path='/tmp/test_config.db'
        )

        with patch.object(SQLiteFallbackBackend, 'connect', new=AsyncMock()):
            with patch.object(SQLiteFallbackBackend, 'initialize_schema', new=AsyncMock()):
                backend = await BackendFactory.create_from_config(config)

                assert isinstance(backend, SQLiteFallbackBackend)
                assert backend.db_path == '/tmp/test_config.db'

    @pytest.mark.asyncio
    async def test_create_from_config_neo4j(self):
        """Test creating Neo4j backend from config."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.NEO4J,
            uri='bolt://config:7687',
            username='configuser',
            password='configpass'
        )

        with patch('src.memorygraph.backends.neo4j_backend.Neo4jBackend') as MockNeo4j:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockNeo4j.return_value = mock_instance

            backend = await BackendFactory.create_from_config(config)

            MockNeo4j.assert_called_once_with(
                uri='bolt://config:7687',
                user='configuser',
                password='configpass'
            )

    @pytest.mark.asyncio
    async def test_create_from_config_memgraph(self):
        """Test creating Memgraph backend from config."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.MEMGRAPH,
            uri='bolt://memconfig:7687',
            username='memuser',
            password='mempass'
        )

        with patch('src.memorygraph.backends.memgraph_backend.MemgraphBackend') as MockMemgraph:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockMemgraph.return_value = mock_instance

            backend = await BackendFactory.create_from_config(config)

            MockMemgraph.assert_called_once_with(
                uri='bolt://memconfig:7687',
                user='memuser',
                password='mempass'
            )

    @pytest.mark.asyncio
    async def test_create_from_config_falkordb(self):
        """Test creating FalkorDB backend from config with URI parsing."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.FALKORDB,
            uri='redis://falkorhost:6380',
            password='falkorpass'
        )

        with patch('src.memorygraph.backends.falkordb_backend.FalkorDBBackend') as MockFalkorDB:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockFalkorDB.return_value = mock_instance

            backend = await BackendFactory.create_from_config(config)

            MockFalkorDB.assert_called_once_with(
                host='falkorhost',
                port=6380,
                password='falkorpass'
            )

    @pytest.mark.asyncio
    async def test_create_from_config_falkordb_invalid_uri(self):
        """Test FalkorDB config with invalid URI format."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.FALKORDB,
            uri='invalid://format',
            password='pass'
        )

        with pytest.raises(DatabaseConnectionError) as exc_info:
            await BackendFactory.create_from_config(config)

        assert "Invalid FalkorDB URI format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_from_config_falkordb_missing_uri(self):
        """Test FalkorDB config with missing URI."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.FALKORDB,
            uri=None,
            password='pass'
        )

        with pytest.raises(DatabaseConnectionError) as exc_info:
            await BackendFactory.create_from_config(config)

        assert "FalkorDB requires URI" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_from_config_falkordblite(self):
        """Test creating FalkorDBLite backend from config."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.FALKORDBLITE,
            path='/test/falkordblite.db'
        )

        with patch('src.memorygraph.backends.falkordblite_backend.FalkorDBLiteBackend') as MockFalkorDBLite:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockFalkorDBLite.return_value = mock_instance

            backend = await BackendFactory.create_from_config(config)

            MockFalkorDBLite.assert_called_once_with(db_path='/test/falkordblite.db')

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_create_from_config_turso(self):
        """Test creating Turso backend from config."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.TURSO,
            path='/test/turso.db',
            uri='libsql://example.turso.io',
            password='turso_token'
        )

        with patch('src.memorygraph.backends.turso.TursoBackend') as MockTurso:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            mock_instance.initialize_schema = AsyncMock()
            MockTurso.return_value = mock_instance

            backend = await BackendFactory.create_from_config(config)

            MockTurso.assert_called_once_with(
                db_path='/test/turso.db',
                sync_url='libsql://example.turso.io',
                auth_token='turso_token'
            )

    @pytest.mark.asyncio
    async def test_create_from_config_cloud(self):
        """Test creating Cloud backend from config."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from src.memorygraph.config import BackendType

        config = BackendConfig(
            backend_type=BackendType.CLOUD,
            uri='https://api.memorygraph.dev',
            password='api_key_from_config'
        )

        with patch('src.memorygraph.backends.cloud_backend.CloudRESTAdapter') as MockCloud:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            MockCloud.return_value = mock_instance

            backend = await BackendFactory.create_from_config(config)

            MockCloud.assert_called_once_with(
                api_key='api_key_from_config',
                api_url='https://api.memorygraph.dev',
                timeout=None
            )


    @pytest.mark.asyncio
    async def test_create_from_config_unknown_backend(self):
        """Test create_from_config with unknown backend type."""
        from src.memorygraph.backends.factory import BackendFactory
        from src.memorygraph.migration.models import BackendConfig
        from unittest.mock import MagicMock
        
        # Create a mock backend type that doesn't exist
        config = MagicMock()
        config.backend_type.value = "unknown_backend_type"
        
        with pytest.raises(DatabaseConnectionError) as exc_info:
            await BackendFactory.create_from_config(config)
        
        assert "Unknown backend type" in str(exc_info.value)


class TestEdgeCases:
    """Test edge cases and error paths."""
    
    def test_is_backend_configured_neo4j_with_fallback_var(self):
        """Test is_backend_configured for Neo4j using fallback NEO4J_PASSWORD."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(NEO4J_PASSWORD='test'):
            assert BackendFactory.is_backend_configured('neo4j') is True
    
    def test_is_backend_configured_memgraph_false(self):
        """Test is_backend_configured for Memgraph returns False when not configured.

        is_backend_configured now checks if the env var is explicitly set
        (via _EnvVar.is_set), not whether the resolved value is truthy.
        """
        from src.memorygraph.backends.factory import BackendFactory

        # Without MEMORY_MEMGRAPH_URI set in env, Memgraph is not configured
        assert BackendFactory.is_backend_configured('memgraph') is False
    
    def test_is_backend_configured_sqlite_always_true(self):
        """Test is_backend_configured for SQLite always returns True."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(SQLITE_PATH=None):
            # SQLite is always available
            assert BackendFactory.is_backend_configured('sqlite') is True


class TestConfigurationHelpers:
    """Test configuration helper methods."""

    def test_get_configured_backend_type_default(self):
        """Test get_configured_backend_type returns default."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='auto'):
            assert BackendFactory.get_configured_backend_type() == 'auto'

    def test_get_configured_backend_type_custom(self):
        """Test get_configured_backend_type returns custom value."""
        from src.memorygraph.backends.factory import BackendFactory

        with patch_config(BACKEND='NEO4J'):
            # Should be lowercased
            assert BackendFactory.get_configured_backend_type() == 'neo4j'

    def test_is_backend_configured_falkordb(self):
        """Test is_backend_configured for FalkorDB.

        is_backend_configured now checks if the env var is explicitly set.
        """
        from src.memorygraph.backends.factory import BackendFactory

        with patch.dict(os.environ, {"MEMORY_FALKORDB_HOST": "localhost"}):
            assert BackendFactory.is_backend_configured('falkordb') is True

        # Without env var set, FalkorDB is not configured (despite truthy default)
        assert BackendFactory.is_backend_configured('falkordb') is False

    def test_is_backend_configured_falkordblite(self):
        """Test is_backend_configured for FalkorDBLite (always True)."""
        from src.memorygraph.backends.factory import BackendFactory

        # FalkorDBLite is embedded, always available
        assert BackendFactory.is_backend_configured('falkordblite') is True

    def test_is_backend_configured_turso(self):
        """Test is_backend_configured for Turso.

        is_backend_configured now checks if env vars are explicitly set.
        """
        from src.memorygraph.backends.factory import BackendFactory

        with patch.dict(os.environ, {"TURSO_DATABASE_URL": "libsql://test"}):
            assert BackendFactory.is_backend_configured('turso') is True

        with patch.dict(os.environ, {"MEMORY_TURSO_PATH": "/path"}):
            assert BackendFactory.is_backend_configured('turso') is True

        # Without env vars set, Turso is not configured
        assert BackendFactory.is_backend_configured('turso') is False

    def test_is_backend_configured_cloud(self):
        """Test is_backend_configured for Cloud.

        is_backend_configured now checks if env var is explicitly set.
        """
        from src.memorygraph.backends.factory import BackendFactory

        with patch.dict(os.environ, {"MEMORYGRAPH_API_KEY": "test_key"}):
            assert BackendFactory.is_backend_configured('cloud') is True

        # Without env var set, Cloud is not configured
        assert BackendFactory.is_backend_configured('cloud') is False

    def test_is_backend_configured_unknown_type(self):
        """Test is_backend_configured for unknown backend type."""
        from src.memorygraph.backends.factory import BackendFactory

        assert BackendFactory.is_backend_configured('unknown_backend') is False
