"""
Backend factory for automatic backend selection.

This module provides a factory class that automatically selects the best available
graph database backend based on environment configuration and availability.
"""

import logging
import os
from typing import Optional, Union

from .base import GraphBackend
from ..models import DatabaseConnectionError

logger = logging.getLogger(__name__)


class BackendFactory:
    """
    Factory class for creating and selecting graph database backends.

    Default: SQLite (zero-config)

    Selection priority:
    1. If MEMORY_BACKEND env var is set, use that specific backend
    2. Default to SQLite for frictionless installation
    3. "auto" mode tries: Neo4j → Memgraph → SQLite
    """

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
        backend_type = os.getenv("MEMORY_BACKEND", "sqlite").lower()

        if backend_type == "neo4j":
            logger.info("Explicit backend selection: Neo4j")
            return await BackendFactory._create_neo4j()

        elif backend_type == "memgraph":
            logger.info("Explicit backend selection: Memgraph")
            return await BackendFactory._create_memgraph()

        elif backend_type == "falkordb":
            logger.info("Explicit backend selection: FalkorDB")
            return await BackendFactory._create_falkordb()

        elif backend_type == "falkordblite":
            logger.info("Explicit backend selection: FalkorDBLite")
            return await BackendFactory._create_falkordblite()

        elif backend_type == "sqlite":
            logger.info("Explicit backend selection: SQLite")
            return await BackendFactory._create_sqlite()

        elif backend_type == "turso":
            logger.info("Explicit backend selection: Turso")
            return await BackendFactory._create_turso()

        elif backend_type == "cloud":
            logger.info("Explicit backend selection: Cloud (MemoryGraph Cloud)")
            return await BackendFactory._create_cloud()

        elif backend_type == "ladybugdb":
            logger.info("Explicit backend selection: LadybugDB")
            return await BackendFactory._create_ladybugdb()

        elif backend_type == "auto":
            logger.info("Auto-selecting backend...")
            return await BackendFactory._auto_select_backend()

        else:
            raise DatabaseConnectionError(
                f"Unknown backend type: {backend_type}. "
                f"Valid options: neo4j, memgraph, falkordb, falkordblite, sqlite, turso, ladybugdb, cloud, auto"
            )

    @staticmethod
    async def _auto_select_backend() -> GraphBackend:
        """
        Automatically select the best available backend.

        Returns:
            Connected GraphBackend instance

        Raises:
            DatabaseConnectionError: If no backend can be connected
        """
        # Try Neo4j first (if password is configured)
        neo4j_password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
        if neo4j_password:
            try:
                logger.info("Attempting to connect to Neo4j...")
                backend = await BackendFactory._create_neo4j()
                logger.info("✓ Successfully connected to Neo4j backend")
                return backend
            except DatabaseConnectionError as e:
                logger.warning(f"Neo4j connection failed: {e}")

        # Try Memgraph (Community Edition typically has no auth)
        memgraph_uri = os.getenv("MEMORY_MEMGRAPH_URI")
        if memgraph_uri:
            try:
                logger.info("Attempting to connect to Memgraph...")
                backend = await BackendFactory._create_memgraph()
                logger.info("✓ Successfully connected to Memgraph backend")
                return backend
            except DatabaseConnectionError as e:
                logger.warning(f"Memgraph connection failed: {e}")

        # Fall back to SQLite
        try:
            logger.info("Falling back to SQLite backend...")
            backend = await BackendFactory._create_sqlite()
            logger.info("✓ Successfully connected to SQLite backend")
            return backend
        except DatabaseConnectionError as e:
            logger.error(f"SQLite backend failed: {e}")
            raise DatabaseConnectionError(
                "Could not connect to any backend. "
                "Please configure Neo4j, Memgraph, or ensure NetworkX is installed for SQLite fallback."
            )

    @staticmethod
    async def _create_neo4j() -> GraphBackend:
        """
        Create and connect to Neo4j backend.

        Returns:
            Connected Neo4jBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import - only load neo4j backend when needed
        from .neo4j_backend import Neo4jBackend

        uri = os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI")
        user = os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER")
        password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

        if not password:
            raise DatabaseConnectionError(
                "Neo4j password not configured. "
                "Set MEMORY_NEO4J_PASSWORD or NEO4J_PASSWORD environment variable."
            )

        backend = Neo4jBackend(uri=uri, user=user, password=password)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_memgraph() -> GraphBackend:
        """
        Create and connect to Memgraph backend.

        Returns:
            Connected MemgraphBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import - only load memgraph backend when needed
        from .memgraph_backend import MemgraphBackend

        uri = os.getenv("MEMORY_MEMGRAPH_URI")
        user = os.getenv("MEMORY_MEMGRAPH_USER", "")
        password = os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

        backend = MemgraphBackend(uri=uri, user=user, password=password)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_falkordb() -> GraphBackend:
        """
        Create and connect to FalkorDB backend.

        Returns:
            Connected FalkorDBBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import - only load falkordb backend when needed
        from .falkordb_backend import FalkorDBBackend

        host = os.getenv("MEMORY_FALKORDB_HOST") or os.getenv("FALKORDB_HOST")
        port_str = os.getenv("MEMORY_FALKORDB_PORT") or os.getenv("FALKORDB_PORT")
        port = int(port_str) if port_str else None
        password = os.getenv("MEMORY_FALKORDB_PASSWORD") or os.getenv("FALKORDB_PASSWORD")

        backend = FalkorDBBackend(host=host, port=port, password=password)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_falkordblite() -> GraphBackend:
        """
        Create and connect to FalkorDBLite backend.

        Returns:
            Connected FalkorDBLiteBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import - only load falkordblite backend when needed
        from .falkordblite_backend import FalkorDBLiteBackend

        db_path = os.getenv("MEMORY_FALKORDBLITE_PATH") or os.getenv("FALKORDBLITE_PATH")

        backend = FalkorDBLiteBackend(db_path=db_path)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_ladybugdb() -> GraphBackend:
        """
        Create and connect to LadybugDB backend.

        Returns:
            Connected LadybugDBBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import - only load ladybugdb backend when needed
        from .ladybugdb_backend import LadybugDBBackend

        db_path = os.getenv("MEMORY_LADYBUGDB_PATH")

        backend = LadybugDBBackend(db_path=db_path)
        await backend.connect()
        # Initialize schema for LadybugDB (required for proper table creation)
        await backend.initialize_schema()
        return backend

    @staticmethod
    async def _create_sqlite() -> GraphBackend:
        """
        Create and connect to SQLite fallback backend.

        Returns:
            Connected SQLiteFallbackBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import - only load sqlite backend when needed
        from .sqlite_fallback import SQLiteFallbackBackend

        db_path = os.getenv("MEMORY_SQLITE_PATH")
        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        # Schema auto-initialized - safe for first-time users
        await backend.initialize_schema()
        return backend

    @staticmethod
    async def _create_turso() -> GraphBackend:
        """
        Create and connect to Turso backend.

        Returns:
            Connected TursoBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import - only load turso backend when needed
        from .turso import TursoBackend

        db_path = os.getenv("MEMORY_TURSO_PATH")
        sync_url = os.getenv("TURSO_DATABASE_URL") or os.getenv("MEMORYGRAPH_TURSO_URL")
        auth_token = os.getenv("TURSO_AUTH_TOKEN") or os.getenv("MEMORYGRAPH_TURSO_TOKEN")

        backend = TursoBackend(
            db_path=db_path,
            sync_url=sync_url,
            auth_token=auth_token
        )
        await backend.connect()
        # Schema auto-initialized - safe for first-time users
        await backend.initialize_schema()
        return backend

    @staticmethod
    async def _create_cloud() -> "CloudRESTAdapter":
        """
        Create and connect to MemoryGraph Cloud backend.

        Returns:
            Connected CloudRESTAdapter instance

        Raises:
            DatabaseConnectionError: If connection fails or API key not configured
        """
        # Lazy import - only load cloud backend when needed
        from .cloud_backend import CloudRESTAdapter

        api_key = os.getenv("MEMORYGRAPH_API_KEY")
        api_url = os.getenv("MEMORYGRAPH_API_URL")
        timeout_str = os.getenv("MEMORYGRAPH_TIMEOUT")
        timeout = int(timeout_str) if timeout_str else None

        if not api_key:
            raise DatabaseConnectionError(
                "MEMORYGRAPH_API_KEY is required for cloud backend. "
                "Get your API key at https://app.memorygraph.dev"
            )

        backend = CloudRESTAdapter(
            api_key=api_key,
            api_url=api_url,
            timeout=timeout
        )
        await backend.connect()
        # Schema managed by cloud service - no local initialization needed
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
                return await BackendFactory._create_sqlite_with_path(config.path)

            elif backend_type == "falkordblite":
                return await BackendFactory._create_falkordblite_with_path(config.path)

            elif backend_type == "ladybugdb":
                return await BackendFactory._create_ladybugdb_with_path(config.path)

            elif backend_type == "neo4j":
                return await BackendFactory._create_neo4j_with_config(
                    uri=config.uri,
                    user=config.username,
                    password=config.password
                )

            elif backend_type == "memgraph":
                return await BackendFactory._create_memgraph_with_config(
                    uri=config.uri,
                    user=config.username or "",
                    password=config.password or ""
                )

            elif backend_type == "falkordb":
                # Parse host and port from URI (format: redis://host:port)
                import re
                if config.uri:
                    match = re.match(r'redis://([^:]+):(\d+)', config.uri)
                    if match:
                        host, port_str = match.groups()
                        port = int(port_str)
                    else:
                        raise DatabaseConnectionError(f"Invalid FalkorDB URI format: {config.uri}")
                else:
                    raise DatabaseConnectionError("FalkorDB requires URI")

                return await BackendFactory._create_falkordb_with_config(
                    host=host,
                    port=port,
                    password=config.password
                )

            elif backend_type == "turso":
                return await BackendFactory._create_turso_with_config(
                    db_path=config.path,
                    sync_url=config.uri,
                    auth_token=config.password
                )

            elif backend_type == "cloud":
                return await BackendFactory._create_cloud_with_config(
                    api_key=config.password,  # Use password field for API key
                    api_url=config.uri
                )

            else:
                raise DatabaseConnectionError(
                    f"Unknown backend type: {backend_type}. "
                    f"Valid options: neo4j, memgraph, falkordb, falkordblite, sqlite, turso, cloud"
                )

        except Exception as e:
            logger.error(f"Failed to create backend from config: {e}")
            raise DatabaseConnectionError(f"Failed to create backend: {e}")

    @staticmethod
    async def _create_sqlite_with_path(db_path: Optional[str] = None) -> GraphBackend:
        """Create SQLite backend with explicit path (thread-safe)."""
        from .sqlite_fallback import SQLiteFallbackBackend

        backend = SQLiteFallbackBackend(db_path=db_path)
        await backend.connect()
        # Schema auto-initialized - safe for first-time users
        await backend.initialize_schema()
        return backend

    @staticmethod
    async def _create_falkordblite_with_path(db_path: Optional[str] = None) -> GraphBackend:
        """Create FalkorDBLite backend with explicit path (thread-safe)."""
        from .falkordblite_backend import FalkorDBLiteBackend

        backend = FalkorDBLiteBackend(db_path=db_path)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_ladybugdb_with_path(db_path: Optional[str] = None) -> GraphBackend:
        """Create LadybugDB backend with explicit path (thread-safe)."""
        from .ladybugdb_backend import LadybugDBBackend

        backend = LadybugDBBackend(db_path=db_path)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_neo4j_with_config(
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ) -> GraphBackend:
        """Create Neo4j backend with explicit config (thread-safe)."""
        from .neo4j_backend import Neo4jBackend

        if not password:
            raise DatabaseConnectionError("Neo4j password is required")

        backend = Neo4jBackend(uri=uri, user=user, password=password)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_memgraph_with_config(
        uri: Optional[str] = None,
        user: str = "",
        password: str = ""
    ) -> GraphBackend:
        """Create Memgraph backend with explicit config (thread-safe)."""
        from .memgraph_backend import MemgraphBackend

        backend = MemgraphBackend(uri=uri, user=user, password=password)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_falkordb_with_config(
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None
    ) -> GraphBackend:
        """Create FalkorDB backend with explicit config (thread-safe)."""
        from .falkordb_backend import FalkorDBBackend

        backend = FalkorDBBackend(host=host, port=port, password=password)
        await backend.connect()
        # Schema managed externally - assumes database is already configured
        return backend

    @staticmethod
    async def _create_turso_with_config(
        db_path: Optional[str] = None,
        sync_url: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> GraphBackend:
        """Create Turso backend with explicit config (thread-safe)."""
        from .turso import TursoBackend

        backend = TursoBackend(
            db_path=db_path,
            sync_url=sync_url,
            auth_token=auth_token
        )
        await backend.connect()
        # Schema auto-initialized - safe for first-time users
        await backend.initialize_schema()
        return backend

    @staticmethod
    async def _create_cloud_with_config(
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> "CloudRESTAdapter":
        """Create Cloud backend with explicit config (thread-safe)."""
        from .cloud_backend import CloudRESTAdapter

        if not api_key:
            raise DatabaseConnectionError("MEMORYGRAPH_API_KEY is required for cloud backend")

        backend = CloudRESTAdapter(
            api_key=api_key,
            api_url=api_url,
            timeout=timeout
        )
        await backend.connect()
        # Schema managed by cloud service - no local initialization needed
        return backend

    @staticmethod
    def get_configured_backend_type() -> str:
        """
        Get the configured backend type without connecting.

        Returns:
            Backend type string: "neo4j", "memgraph", "sqlite", or "auto"
        """
        return os.getenv("MEMORY_BACKEND", "auto").lower()

    @staticmethod
    def is_backend_configured(backend_type: str) -> bool:
        """
        Check if a specific backend is configured via environment variables.

        Args:
            backend_type: Backend type to check ("neo4j", "memgraph", "falkordb", "falkordblite", "sqlite")

        Returns:
            True if backend appears to be configured
        """
        if backend_type == "neo4j":
            return bool(
                os.getenv("MEMORY_NEO4J_PASSWORD") or
                os.getenv("NEO4J_PASSWORD")
            )
        elif backend_type == "memgraph":
            return bool(os.getenv("MEMORY_MEMGRAPH_URI"))
        elif backend_type == "falkordb":
            return bool(
                os.getenv("MEMORY_FALKORDB_HOST") or
                os.getenv("FALKORDB_HOST")
            )
        elif backend_type == "falkordblite":
            return True  # FalkorDBLite is always available (embedded, like SQLite)
        elif backend_type == "sqlite":
            return True  # SQLite is always available if NetworkX is installed
        elif backend_type == "turso":
            return bool(
                os.getenv("TURSO_DATABASE_URL") or
                os.getenv("MEMORYGRAPH_TURSO_URL") or
                os.getenv("MEMORY_TURSO_PATH")
            )
        elif backend_type == "cloud":
            return bool(os.getenv("MEMORYGRAPH_API_KEY"))
        else:
            return False
