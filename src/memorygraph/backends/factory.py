"""
Backend factory for automatic backend selection.

This module provides a factory class that automatically selects the best available
graph database backend based on environment configuration and availability.
"""

import logging
import re
from typing import Optional, Union

from ..config import Config
from ..models import DatabaseConnectionError
from .base import GraphBackend

logger = logging.getLogger(__name__)

# Valid backend types for error messages
_VALID_BACKENDS = "neo4j, memgraph, falkordb, falkordblite, sqlite, turso, ladybugdb, cloud, auto"

# Sentinel to distinguish "argument not provided" from "explicitly passed None"
_UNSET = object()


class BackendFactory:
    """
    Factory class for creating and selecting graph database backends.

    Default: SQLite (zero-config)

    Selection priority:
    1. If MEMORY_BACKEND env var is set, use that specific backend
    2. Default to SQLite for frictionless installation
    3. "auto" mode tries: Neo4j -> Memgraph -> SQLite
    """

    # Backend display names for logging
    _BACKEND_NAMES = {
        "neo4j": "Neo4j",
        "memgraph": "Memgraph",
        "falkordb": "FalkorDB",
        "falkordblite": "FalkorDBLite",
        "sqlite": "SQLite",
        "turso": "Turso",
        "cloud": "Cloud (MemoryGraph Cloud)",
        "ladybugdb": "LadybugDB",
    }

    @staticmethod
    async def create_backend() -> Union[GraphBackend, "CloudRESTAdapter"]:
        """
        Create and connect to the best available backend.

        Returns:
            Connected GraphBackend or CloudRESTAdapter instance

        Raises:
            DatabaseConnectionError: If no backend can be connected

        Selection logic:
        - Default: SQLite (zero-config, no external dependencies)
        - Explicit: Use MEMORY_BACKEND env var if set (neo4j, memgraph, falkordb, falkordblite, sqlite, ladybugdb, cloud, auto)
        - Auto: Try backends in order until one connects successfully

        Schema Initialization:
        - SQLite/Turso: Schema auto-initialized by factory (safe for first-time use)
        - Neo4j/Memgraph/FalkorDB/FalkorDBLite/LadybugDB: Schema must be created externally before use
        - Cloud: Schema managed by cloud service (no local initialization needed)
        - All initialize_schema() methods are idempotent (safe to call multiple times)
        """
        backend_type = Config.BACKEND.lower()

        if backend_type == "auto":
            logger.info("Auto-selecting backend...")
            return await BackendFactory._auto_select_backend()

        display_name = BackendFactory._BACKEND_NAMES.get(backend_type)
        if display_name is None:
            raise DatabaseConnectionError(
                f"Unknown backend type: {backend_type}. "
                f"Valid options: {_VALID_BACKENDS}"
            )

        logger.info("Explicit backend selection: %s", display_name)
        return await BackendFactory._create_backend_by_type(backend_type)

    @staticmethod
    async def _create_backend_by_type(backend_type: str) -> Union[GraphBackend, "CloudRESTAdapter"]:
        """Dispatch to the appropriate _create_* method by backend type."""
        creators = {
            "neo4j": BackendFactory._create_neo4j,
            "memgraph": BackendFactory._create_memgraph,
            "falkordb": BackendFactory._create_falkordb,
            "falkordblite": BackendFactory._create_falkordblite,
            "sqlite": BackendFactory._create_sqlite,
            "turso": BackendFactory._create_turso,
            "cloud": BackendFactory._create_cloud,
            "ladybugdb": BackendFactory._create_ladybugdb,
        }
        return await creators[backend_type]()

    @staticmethod
    async def _auto_select_backend() -> GraphBackend:
        """
        Automatically select the best available backend.

        Returns:
            Connected GraphBackend instance

        Raises:
            DatabaseConnectionError: If no backend can be connected
        """
        # Try Neo4j first (if password is explicitly configured)
        if Config.is_env_set("NEO4J_PASSWORD"):
            try:
                logger.info("Attempting to connect to Neo4j...")
                backend = await BackendFactory._create_neo4j()
                logger.info("Successfully connected to Neo4j backend")
                return backend
            except DatabaseConnectionError as e:
                logger.warning("Neo4j connection failed: %s", e)

        # Try Memgraph (only if URI is explicitly configured)
        if Config.is_env_set("MEMGRAPH_URI"):
            try:
                logger.info("Attempting to connect to Memgraph...")
                backend = await BackendFactory._create_memgraph()
                logger.info("Successfully connected to Memgraph backend")
                return backend
            except DatabaseConnectionError as e:
                logger.warning("Memgraph connection failed: %s", e)

        # Fall back to SQLite
        try:
            logger.info("Falling back to SQLite backend...")
            backend = await BackendFactory._create_sqlite()
            logger.info("Successfully connected to SQLite backend")
            return backend
        except DatabaseConnectionError as e:
            logger.error("SQLite backend failed: %s", e)
            raise DatabaseConnectionError(
                "Could not connect to any backend. "
                "Please configure Neo4j, Memgraph, or ensure NetworkX is installed for SQLite fallback."
            ) from e

    @staticmethod
    async def _create_neo4j(
        uri=_UNSET,
        user=_UNSET,
        password=_UNSET,
    ) -> GraphBackend:
        """
        Create and connect to Neo4j backend.

        When called without arguments, reads from Config. Explicit arguments
        override Config values for thread-safe usage via create_from_config().

        Raises:
            DatabaseConnectionError: If password is missing or connection fails
        """
        from .neo4j_backend import Neo4jBackend

        using_config = password is _UNSET
        uri = Config.NEO4J_URI if uri is _UNSET else uri
        user = Config.NEO4J_USER if user is _UNSET else user
        password = Config.NEO4J_PASSWORD if password is _UNSET else password

        if not password:
            if using_config:
                raise DatabaseConnectionError(
                    "Neo4j password not configured. "
                    "Set MEMORY_NEO4J_PASSWORD or NEO4J_PASSWORD environment variable."
                )
            raise DatabaseConnectionError("Neo4j password is required")

        backend = Neo4jBackend(uri=uri, user=user, password=password)
        await backend.connect()
        return backend

    @staticmethod
    async def _create_memgraph(
        uri=_UNSET,
        user=_UNSET,
        password=_UNSET,
    ) -> GraphBackend:
        """
        Create and connect to Memgraph backend.

        When called without arguments, reads from Config. Explicit arguments
        override Config values for thread-safe usage via create_from_config().
        """
        from .memgraph_backend import MemgraphBackend

        uri = Config.MEMGRAPH_URI if uri is _UNSET else uri
        user = Config.MEMGRAPH_USER if user is _UNSET else user
        password = Config.MEMGRAPH_PASSWORD if password is _UNSET else password

        backend = MemgraphBackend(uri=uri, user=user, password=password)
        await backend.connect()
        return backend

    @staticmethod
    async def _create_falkordb(
        host=_UNSET,
        port=_UNSET,
        password=_UNSET,
    ) -> GraphBackend:
        """
        Create and connect to FalkorDB backend.

        When called without arguments, reads from Config. Explicit arguments
        override Config values for thread-safe usage via create_from_config().
        """
        from .falkordb_backend import FalkorDBBackend

        host = Config.FALKORDB_HOST if host is _UNSET else host
        port = Config.FALKORDB_PORT if port is _UNSET else port
        password = Config.FALKORDB_PASSWORD if password is _UNSET else password

        backend = FalkorDBBackend(host=host, port=port, password=password)
        await backend.connect()
        return backend

    @staticmethod
    async def _create_falkordblite(
        db_path=_UNSET,
    ) -> GraphBackend:
        """
        Create and connect to FalkorDBLite backend.

        When called without arguments, reads from Config. Explicit db_path
        overrides Config for thread-safe usage via create_from_config().
        """
        from .falkordblite_backend import FalkorDBLiteBackend

        db_path = Config.FALKORDBLITE_PATH if db_path is _UNSET else db_path

        backend = FalkorDBLiteBackend(db_path=db_path)
        await backend.connect()
        return backend

    @staticmethod
    async def _create_ladybugdb(
        db_path=_UNSET,
    ) -> GraphBackend:
        """
        Create and connect to LadybugDB backend.

        When called without arguments, reads from Config. Explicit db_path
        overrides Config for thread-safe usage via create_from_config().

        NOTE: Unlike SQLite/Turso, LadybugDB schema is not auto-initialized.
        """
        from .ladybugdb_backend import LadybugDBBackend

        db_path = Config.LADYBUGDB_PATH if db_path is _UNSET else db_path

        backend = LadybugDBBackend(db_path=db_path)
        await backend.connect()
        return backend

    @staticmethod
    async def _create_sqlite(
        db_path=_UNSET,
    ) -> GraphBackend:
        """
        Create and connect to SQLite fallback backend.

        When called without arguments, reads from Config. Explicit db_path
        overrides Config for thread-safe usage via create_from_config().

        Schema is auto-initialized (safe for first-time users).
        """
        from .sqlite_fallback import SQLiteFallbackBackend

        db_path = Config.SQLITE_PATH if db_path is _UNSET else db_path

        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        await backend.initialize_schema()
        return backend

    @staticmethod
    async def _create_turso(
        db_path=_UNSET,
        sync_url=_UNSET,
        auth_token=_UNSET,
    ) -> GraphBackend:
        """
        Create and connect to Turso backend.

        When called without arguments, reads from Config. Explicit arguments
        override Config values for thread-safe usage via create_from_config().

        Schema is auto-initialized (safe for first-time users).
        """
        from .turso import TursoBackend

        db_path = Config.TURSO_PATH if db_path is _UNSET else db_path
        sync_url = Config.TURSO_DATABASE_URL if sync_url is _UNSET else sync_url
        auth_token = Config.TURSO_AUTH_TOKEN if auth_token is _UNSET else auth_token

        backend = TursoBackend(
            db_path=db_path,
            sync_url=sync_url,
            auth_token=auth_token,
        )
        await backend.connect()
        await backend.initialize_schema()
        return backend

    @staticmethod
    async def _create_cloud(
        api_key=_UNSET,
        api_url=_UNSET,
        timeout=_UNSET,
    ) -> "CloudRESTAdapter":
        """
        Create and connect to MemoryGraph Cloud backend.

        When called without arguments, reads from Config. Explicit arguments
        override Config values for thread-safe usage via create_from_config().

        Raises:
            DatabaseConnectionError: If API key is missing or connection fails
        """
        from .cloud_backend import CloudRESTAdapter

        using_config = api_key is _UNSET
        api_key = Config.MEMORYGRAPH_API_KEY if api_key is _UNSET else api_key
        api_url = Config.MEMORYGRAPH_API_URL if api_url is _UNSET else api_url
        timeout = Config.MEMORYGRAPH_TIMEOUT if timeout is _UNSET else timeout

        if not api_key:
            if using_config:
                raise DatabaseConnectionError(
                    "MEMORYGRAPH_API_KEY is required for cloud backend. "
                    "Get your API key at https://app.memorygraph.dev"
                )
            raise DatabaseConnectionError("MEMORYGRAPH_API_KEY is required for cloud backend")

        backend = CloudRESTAdapter(
            api_key=api_key,
            api_url=api_url,
            timeout=timeout,
        )
        await backend.connect()
        return backend

    @staticmethod
    async def create_from_config(config: 'BackendConfig') -> Union[GraphBackend, "CloudRESTAdapter"]:
        """
        Create backend from explicit configuration without using environment variables.

        This is a thread-safe alternative to create_backend() that doesn't mutate
        global environment variables.

        Args:
            config: BackendConfig with backend type and connection details

        Returns:
            Connected GraphBackend instance

        Raises:
            DatabaseConnectionError: If backend creation or connection fails

        Example:
            config = BackendConfig(
                backend_type=BackendType.SQLITE,
                path="/path/to/db.sqlite"
            )
            backend = await BackendFactory.create_from_config(config)
        """
        from ..migration.models import BackendConfig  # Import here to avoid circular dependency

        backend_type = config.backend_type.value

        try:
            if backend_type == "sqlite":
                return await BackendFactory._create_sqlite(db_path=config.path)

            if backend_type == "falkordblite":
                return await BackendFactory._create_falkordblite(db_path=config.path)

            if backend_type == "ladybugdb":
                return await BackendFactory._create_ladybugdb(db_path=config.path)

            if backend_type == "neo4j":
                return await BackendFactory._create_neo4j(
                    uri=config.uri,
                    user=config.username,
                    password=config.password,
                )

            if backend_type == "memgraph":
                return await BackendFactory._create_memgraph(
                    uri=config.uri,
                    user=config.username or "",
                    password=config.password or "",
                )

            if backend_type == "falkordb":
                host, port = BackendFactory._parse_falkordb_uri(config.uri)
                return await BackendFactory._create_falkordb(
                    host=host,
                    port=port,
                    password=config.password,
                )

            if backend_type == "turso":
                return await BackendFactory._create_turso(
                    db_path=config.path,
                    sync_url=config.uri,
                    auth_token=config.password,
                )

            if backend_type == "cloud":
                return await BackendFactory._create_cloud(
                    api_key=config.password,  # Use password field for API key
                    api_url=config.uri,
                    timeout=None,
                )

            raise DatabaseConnectionError(
                f"Unknown backend type: {backend_type}. "
                f"Valid options: neo4j, memgraph, falkordb, falkordblite, sqlite, turso, cloud"
            )

        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error("Failed to create backend from config: %s", e)
            raise DatabaseConnectionError(f"Failed to create backend: {e}") from e

    @staticmethod
    def _parse_falkordb_uri(uri: Optional[str]) -> tuple[str, int]:
        """Parse host and port from a FalkorDB Redis URI (redis://host:port)."""
        if not uri:
            raise DatabaseConnectionError("FalkorDB requires URI")

        match = re.match(r'redis://([^:]+):(\d+)', uri)
        if not match:
            raise DatabaseConnectionError(f"Invalid FalkorDB URI format: {uri}")

        host, port_str = match.groups()
        return host, int(port_str)

    # Legacy aliases for backward compatibility with tests that call
    # the old _create_*_with_* methods directly.
    _create_sqlite_with_path = _create_sqlite
    _create_falkordblite_with_path = _create_falkordblite
    _create_ladybugdb_with_path = _create_ladybugdb
    _create_neo4j_with_config = _create_neo4j
    _create_memgraph_with_config = _create_memgraph
    _create_falkordb_with_config = _create_falkordb
    _create_turso_with_config = _create_turso
    _create_cloud_with_config = _create_cloud

    @staticmethod
    def get_configured_backend_type() -> str:
        """
        Get the configured backend type without connecting.

        Returns:
            Backend type string: "neo4j", "memgraph", "sqlite", or "auto"
        """
        return Config.BACKEND.lower()

    # Lookup for is_backend_configured checks.
    # Callables return True if the backend appears configured.
    # True means the backend is always available (embedded).
    _BACKEND_CONFIGURED_CHECKS = {
        "neo4j": lambda: Config.is_env_set("NEO4J_PASSWORD"),
        "memgraph": lambda: Config.is_env_set("MEMGRAPH_URI"),
        "falkordb": lambda: Config.is_env_set("FALKORDB_HOST"),
        "falkordblite": lambda: True,
        "sqlite": lambda: True,
        "turso": lambda: Config.is_env_set("TURSO_DATABASE_URL") or Config.is_env_set("TURSO_PATH"),
        "cloud": lambda: Config.is_env_set("MEMORYGRAPH_API_KEY"),
        "ladybugdb": lambda: True,
    }

    @staticmethod
    def is_backend_configured(backend_type: str) -> bool:
        """
        Check if a specific backend is configured via environment variables.

        Args:
            backend_type: Backend type to check ("neo4j", "memgraph", "falkordb", "falkordblite", "sqlite")

        Returns:
            True if backend appears to be configured
        """
        check = BackendFactory._BACKEND_CONFIGURED_CHECKS.get(backend_type)
        if check is None:
            return False
        return check()
