"""
Tests for code simplification changes to config.py and factory.py.

Tests cover:
- TOOL_PROFILES deduplication (core subset of extended)
- _UNSET sentinel pattern in factory _create_* methods
- Dispatch table in create_backend() and is_backend_configured()
- _parse_falkordb_uri() helper
- Legacy aliases for backward compatibility
"""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from memorygraph.backends.factory import _UNSET, BackendFactory
from memorygraph.config import _CORE_TOOLS, _EXTENDED_EXTRA_TOOLS, TOOL_PROFILES, Config
from memorygraph.models import DatabaseConnectionError


@contextmanager
def patch_config(**kwargs):
    """Temporarily patch Config class attributes, restoring descriptors on exit."""
    original_values = {}
    for key, value in kwargs.items():
        if key in Config.__dict__:
            original_values[key] = Config.__dict__[key]
        setattr(Config, key, value)
    try:
        yield
    finally:
        for key, value in original_values.items():
            setattr(Config, key, value)


class TestToolProfilesDeduplication:
    """Test that TOOL_PROFILES is correctly built from _CORE_TOOLS + _EXTENDED_EXTRA_TOOLS."""

    def test_core_profile_matches_core_tools(self):
        """Core profile should be exactly _CORE_TOOLS."""
        assert TOOL_PROFILES["core"] is _CORE_TOOLS

    def test_extended_profile_includes_all_core_tools(self):
        """Extended profile must contain every core tool."""
        for tool in _CORE_TOOLS:
            assert tool in TOOL_PROFILES["extended"], f"Core tool {tool!r} missing from extended"

    def test_extended_profile_includes_extra_tools(self):
        """Extended profile must contain all extra tools."""
        for tool in _EXTENDED_EXTRA_TOOLS:
            assert tool in TOOL_PROFILES["extended"], f"Extra tool {tool!r} missing from extended"

    def test_extended_profile_is_core_plus_extra(self):
        """Extended profile should be exactly core + extra (no duplicates, correct order)."""
        assert TOOL_PROFILES["extended"] == _CORE_TOOLS + _EXTENDED_EXTRA_TOOLS

    def test_core_tools_count(self):
        """Core should have 9 tools."""
        assert len(_CORE_TOOLS) == 9

    def test_extended_tools_count(self):
        """Extended should have 12 tools (9 core + 3 extra)."""
        assert len(TOOL_PROFILES["extended"]) == 12

    def test_no_duplicates_in_extended(self):
        """Extended profile should have no duplicate tool names."""
        extended = TOOL_PROFILES["extended"]
        assert len(extended) == len(set(extended))


class TestUnsetSentinel:
    """Test the _UNSET sentinel pattern in factory methods."""

    def test_unset_is_unique_object(self):
        """_UNSET should be a unique sentinel, not None or False."""
        assert _UNSET is not None
        assert _UNSET is not False
        assert _UNSET != 0
        assert _UNSET != ""

    @pytest.mark.asyncio
    async def test_create_sqlite_uses_config_when_no_args(self):
        """_create_sqlite() without args should read Config.SQLITE_PATH."""
        with patch_config(SQLITE_PATH="/tmp/test_config_path.db"):
            with patch("memorygraph.backends.sqlite_fallback.SQLiteFallbackBackend") as mock_sqlite_cls:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_instance.initialize_schema = AsyncMock()
                mock_sqlite_cls.return_value = mock_instance

                await BackendFactory._create_sqlite()

                mock_sqlite_cls.assert_called_once_with(db_path="/tmp/test_config_path.db")

    @pytest.mark.asyncio
    async def test_create_sqlite_uses_explicit_arg(self):
        """_create_sqlite(db_path=...) should use provided path, not Config."""
        with patch_config(SQLITE_PATH="/tmp/test_config_path.db"):
            with patch("memorygraph.backends.sqlite_fallback.SQLiteFallbackBackend") as mock_sqlite_cls:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_instance.initialize_schema = AsyncMock()
                mock_sqlite_cls.return_value = mock_instance

                await BackendFactory._create_sqlite(db_path="/tmp/test_explicit_path.db")

                mock_sqlite_cls.assert_called_once_with(db_path="/tmp/test_explicit_path.db")

    @pytest.mark.asyncio
    async def test_create_sqlite_explicit_none_passes_none(self):
        """_create_sqlite(db_path=None) should pass None, not fall back to Config."""
        with patch_config(SQLITE_PATH="/tmp/test_config_path.db"):
            with patch("memorygraph.backends.sqlite_fallback.SQLiteFallbackBackend") as mock_sqlite_cls:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_instance.initialize_schema = AsyncMock()
                mock_sqlite_cls.return_value = mock_instance

                await BackendFactory._create_sqlite(db_path=None)

                mock_sqlite_cls.assert_called_once_with(db_path=None)

    @pytest.mark.asyncio
    async def test_create_neo4j_uses_config_when_no_args(self):
        """_create_neo4j() without args should read Config.NEO4J_*."""
        with patch_config(NEO4J_URI="bolt://cfg:7687", NEO4J_USER="cfg-user", NEO4J_PASSWORD="cfg-pass"):
            with patch("memorygraph.backends.neo4j_backend.Neo4jBackend") as mock_neo4j_cls:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_neo4j_cls.return_value = mock_instance

                await BackendFactory._create_neo4j()

                mock_neo4j_cls.assert_called_once_with(uri="bolt://cfg:7687", user="cfg-user", password="cfg-pass")

    @pytest.mark.asyncio
    async def test_create_neo4j_explicit_args_override_config(self):
        """_create_neo4j(uri=..., user=..., password=...) should override Config."""
        with patch_config(NEO4J_URI="bolt://cfg:7687", NEO4J_USER="cfg-user", NEO4J_PASSWORD="cfg-pass"):
            with patch("memorygraph.backends.neo4j_backend.Neo4jBackend") as mock_neo4j_cls:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_neo4j_cls.return_value = mock_instance

                await BackendFactory._create_neo4j(
                    uri="bolt://explicit:7687",
                    user="explicit-user",
                    password="explicit-pass",
                )

                mock_neo4j_cls.assert_called_once_with(
                    uri="bolt://explicit:7687", user="explicit-user", password="explicit-pass"
                )

    @pytest.mark.asyncio
    async def test_create_cloud_uses_config_when_no_args(self):
        """_create_cloud() without args should read Config.MEMORYGRAPH_*."""
        with patch_config(
            MEMORYGRAPH_API_KEY="cfg-key", MEMORYGRAPH_API_URL="https://cfg.api", MEMORYGRAPH_TIMEOUT=45
        ):
            with patch("memorygraph.backends.cloud_backend.CloudRESTAdapter") as mock_cloud_cls:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_cloud_cls.return_value = mock_instance

                await BackendFactory._create_cloud()

                mock_cloud_cls.assert_called_once_with(api_key="cfg-key", api_url="https://cfg.api", timeout=45)


class TestDispatchTable:
    """Test the dispatch-table pattern in create_backend()."""

    @pytest.mark.asyncio
    async def test_create_backend_dispatches_sqlite(self):
        """create_backend() should dispatch to _create_sqlite for 'sqlite' backend."""
        from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend

        with patch_config(BACKEND="sqlite"):
            with patch.object(SQLiteFallbackBackend, "connect", new=AsyncMock()):
                with patch.object(SQLiteFallbackBackend, "initialize_schema", new=AsyncMock()):
                    backend = await BackendFactory.create_backend()
                    assert isinstance(backend, SQLiteFallbackBackend)

    @pytest.mark.asyncio
    async def test_create_backend_dispatches_cloud(self):
        """create_backend() should dispatch to _create_cloud for 'cloud' backend."""
        with patch_config(BACKEND="cloud", MEMORYGRAPH_API_KEY="test-key"):
            with patch("memorygraph.backends.cloud_backend.CloudRESTAdapter") as mock_cloud_cls:
                mock_instance = MagicMock()
                mock_instance.connect = AsyncMock()
                mock_cloud_cls.return_value = mock_instance

                backend = await BackendFactory.create_backend()
                assert backend is mock_instance

    @pytest.mark.asyncio
    async def test_create_backend_raises_for_unknown(self):
        """create_backend() should raise for unknown backend type."""
        with patch_config(BACKEND="nonexistent"):
            with pytest.raises(DatabaseConnectionError, match="Unknown backend type"):
                await BackendFactory.create_backend()

    @pytest.mark.asyncio
    async def test_create_backend_auto_delegates(self):
        """create_backend() with 'auto' should delegate to _auto_select_backend."""
        with patch_config(BACKEND="auto"):
            with patch.object(BackendFactory, "_auto_select_backend", new_callable=AsyncMock) as mock_auto:
                mock_auto.return_value = MagicMock()
                await BackendFactory.create_backend()
                mock_auto.assert_called_once()


class TestBackendConfiguredLookup:
    """Test is_backend_configured() lookup-table pattern."""

    def test_known_backends_return_correct_values(self):
        """is_backend_configured should return correct values for each backend type."""
        with patch_config(NEO4J_PASSWORD="pass"):
            assert BackendFactory.is_backend_configured("neo4j") is True
        with patch_config(NEO4J_PASSWORD=None):
            assert BackendFactory.is_backend_configured("neo4j") is False

        with patch_config(MEMGRAPH_URI="bolt://localhost:7687"):
            assert BackendFactory.is_backend_configured("memgraph") is True
        with patch_config(MEMGRAPH_URI=None):
            assert BackendFactory.is_backend_configured("memgraph") is False

        assert BackendFactory.is_backend_configured("sqlite") is True
        assert BackendFactory.is_backend_configured("falkordblite") is True

        with patch_config(MEMORYGRAPH_API_KEY="key"):
            assert BackendFactory.is_backend_configured("cloud") is True
        with patch_config(MEMORYGRAPH_API_KEY=None):
            assert BackendFactory.is_backend_configured("cloud") is False

    def test_unknown_backend_returns_false(self):
        """Unknown backend types should return False."""
        assert BackendFactory.is_backend_configured("unknown") is False
        assert BackendFactory.is_backend_configured("") is False


class TestParseFalkordbUri:
    """Test _parse_falkordb_uri() helper."""

    def test_valid_uri(self):
        """Valid redis:// URI should parse correctly."""
        host, port = BackendFactory._parse_falkordb_uri("redis://myhost:6380")
        assert host == "myhost"
        assert port == 6380

    def test_localhost_default_port(self):
        """Standard localhost URI should parse correctly."""
        host, port = BackendFactory._parse_falkordb_uri("redis://localhost:6379")
        assert host == "localhost"
        assert port == 6379

    def test_none_uri_raises(self):
        """None URI should raise DatabaseConnectionError."""
        with pytest.raises(DatabaseConnectionError, match="FalkorDB requires URI"):
            BackendFactory._parse_falkordb_uri(None)

    def test_empty_uri_raises(self):
        """Empty string URI should raise DatabaseConnectionError."""
        with pytest.raises(DatabaseConnectionError, match="FalkorDB requires URI"):
            BackendFactory._parse_falkordb_uri("")

    def test_invalid_format_raises(self):
        """Non-redis:// URI should raise DatabaseConnectionError."""
        with pytest.raises(DatabaseConnectionError, match="Invalid FalkorDB URI format"):
            BackendFactory._parse_falkordb_uri("http://invalid:6379")


class TestLegacyAliases:
    """Test that legacy _create_*_with_* aliases work for backward compatibility."""

    def test_sqlite_alias(self):
        """_create_sqlite_with_path should be the same function as _create_sqlite."""
        assert BackendFactory._create_sqlite_with_path is BackendFactory._create_sqlite

    def test_neo4j_alias(self):
        """_create_neo4j_with_config should be the same function as _create_neo4j."""
        assert BackendFactory._create_neo4j_with_config is BackendFactory._create_neo4j

    def test_memgraph_alias(self):
        """_create_memgraph_with_config should be the same function as _create_memgraph."""
        assert BackendFactory._create_memgraph_with_config is BackendFactory._create_memgraph

    def test_cloud_alias(self):
        """_create_cloud_with_config should be the same function as _create_cloud."""
        assert BackendFactory._create_cloud_with_config is BackendFactory._create_cloud

    def test_turso_alias(self):
        """_create_turso_with_config should be the same function as _create_turso."""
        assert BackendFactory._create_turso_with_config is BackendFactory._create_turso

    def test_falkordblite_alias(self):
        """_create_falkordblite_with_path should be the same function as _create_falkordblite."""
        assert BackendFactory._create_falkordblite_with_path is BackendFactory._create_falkordblite

    def test_ladybugdb_alias(self):
        """_create_ladybugdb_with_path should be the same function as _create_ladybugdb."""
        assert BackendFactory._create_ladybugdb_with_path is BackendFactory._create_ladybugdb

    def test_falkordb_alias(self):
        """_create_falkordb_with_config should be the same function as _create_falkordb."""
        assert BackendFactory._create_falkordb_with_config is BackendFactory._create_falkordb

    @pytest.mark.asyncio
    async def test_legacy_alias_callable_with_args(self):
        """Legacy aliases should accept the same arguments as the original methods."""
        with patch("memorygraph.backends.sqlite_fallback.SQLiteFallbackBackend") as mock_sqlite_cls:
            mock_instance = MagicMock()
            mock_instance.connect = AsyncMock()
            mock_instance.initialize_schema = AsyncMock()
            mock_sqlite_cls.return_value = mock_instance

            await BackendFactory._create_sqlite_with_path("/tmp/legacy_path.db")

            mock_sqlite_cls.assert_called_once_with(db_path="/tmp/legacy_path.db")


class TestBackendNamesCompleteness:
    """Test that _BACKEND_NAMES covers all non-auto backend types."""

    def test_all_backend_types_have_names(self):
        """Every backend in _create_backend_by_type dispatch should have a display name."""
        from memorygraph.config import BackendType

        for bt in BackendType:
            if bt == BackendType.AUTO:
                continue
            assert bt.value in BackendFactory._BACKEND_NAMES, (
                f"BackendType.{bt.name} ({bt.value}) missing from _BACKEND_NAMES"
            )
