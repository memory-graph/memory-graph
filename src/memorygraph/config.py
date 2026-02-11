"""
Configuration management for MemoryGraph.

This module centralizes all configuration options and environment variable handling
for the multi-backend memory server.

Config attributes are dynamic descriptors that read environment variables on each
access. This ensures tests using patch.dict(os.environ) and direct Config attribute
overrides both work correctly.
"""

import os
from enum import Enum


class BackendType(Enum):
    """Supported backend types."""

    NEO4J = "neo4j"
    MEMGRAPH = "memgraph"
    SQLITE = "sqlite"
    TURSO = "turso"
    CLOUD = "cloud"
    FALKORDB = "falkordb"
    FALKORDBLITE = "falkordblite"
    AUTO = "auto"


_CORE_TOOLS = [
    "store_memory",
    "get_memory",
    "search_memories",
    "update_memory",
    "delete_memory",
    "create_relationship",
    "get_related_memories",
    "recall_memories",
    "get_recent_activity",
]

_EXTENDED_EXTRA_TOOLS = [
    "get_memory_statistics",
    "search_relationships_by_context",
    "contextual_search",
]

TOOL_PROFILES = {
    "core": _CORE_TOOLS,
    "extended": _CORE_TOOLS + _EXTENDED_EXTRA_TOOLS,
}


class _EnvVar:
    """Descriptor that reads environment variables dynamically on each access.

    When accessed as a class attribute (e.g., Config.BACKEND), invokes __get__
    which reads from os.environ at call time. This makes Config reactive to
    env var changes (e.g., via patch.dict(os.environ) in tests).

    Direct assignment (e.g., Config.BACKEND = "neo4j") replaces the descriptor
    with a static value, which is useful for tests that patch Config directly.
    """

    def __init__(self, *env_names: str, default: object = None, cast: object = None):
        """
        Args:
            env_names: Environment variable names to check in priority order.
                       Uses ``is not None`` check: only unset env vars fall
                       through. An explicitly set empty string is returned
                       (consistent with ``is_set()``).
            default: Default value if no env var is set (already the final type).
            cast: Optional type converter (int, float). Use bool for
                  "true"/"false" string parsing.
        """
        self.env_names = env_names
        self.default = default
        self.cast = cast

    def __get__(self, obj: object, objtype: type = None) -> object:
        for name in self.env_names:
            val = os.getenv(name)
            if val is not None:
                return self._convert(val)
        return self.default

    def _convert(self, val: str) -> object:
        if self.cast is None:
            return val
        if self.cast is bool:
            return val.lower() == "true"
        return self.cast(val)  # type: ignore[operator]

    def is_set(self) -> bool:
        """Return True if any of the env var names are explicitly set in os.environ.

        Uses membership testing (``in os.environ``), not truthiness.
        This distinguishes "user explicitly configured" from "using default".
        """
        return any(name in os.environ for name in self.env_names)

    def __repr__(self) -> str:
        return f"_EnvVar({', '.join(repr(n) for n in self.env_names)}, default={self.default!r})"


_DEFAULT_DB_PATH = os.path.expanduser("~/.memorygraph/memory.db")
_DEFAULT_FALKORDBLITE_PATH = os.path.expanduser("~/.memorygraph/falkordblite.db")
_DEFAULT_LADYBUGDB_PATH = os.path.expanduser("~/.memorygraph/ladybugdb.db")


class Config:
    """
    Configuration class for the memory server.

    All attributes are dynamic descriptors that read from environment variables
    on each access. This makes Config the single source of truth for configuration
    while remaining reactive to runtime env var changes.

    Attributes can be overridden via direct assignment (e.g., Config.BACKEND = "neo4j")
    for testing or programmatic configuration.

    Environment Variables:
        MEMORY_BACKEND: Backend type (neo4j|memgraph|sqlite|turso|cloud|falkordb|falkordblite|auto) [default: sqlite]

        Neo4j Configuration:
            MEMORY_NEO4J_URI or NEO4J_URI: Connection URI [default: bolt://localhost:7687]
            MEMORY_NEO4J_USER or NEO4J_USER: Username [default: neo4j]
            MEMORY_NEO4J_PASSWORD or NEO4J_PASSWORD: Password [required for Neo4j]

        Memgraph Configuration:
            MEMORY_MEMGRAPH_URI: Connection URI [default: bolt://localhost:7687]
            MEMORY_MEMGRAPH_USER: Username [default: ""]
            MEMORY_MEMGRAPH_PASSWORD: Password [default: ""]

        SQLite Configuration:
            MEMORY_SQLITE_PATH: Database file path [default: ~/.memorygraph/memory.db]

        Turso Configuration:
            MEMORY_TURSO_PATH: Local database file path [default: ~/.memorygraph/memory.db]
            TURSO_DATABASE_URL: Turso database URL (e.g., libsql://your-db.turso.io)
            TURSO_AUTH_TOKEN: Turso authentication token

        Cloud Configuration:
            MEMORYGRAPH_API_KEY: API key for MemoryGraph Cloud (required for cloud backend)
            MEMORYGRAPH_API_URL: Cloud API base URL [default: https://graph-api.memorygraph.dev]
            MEMORYGRAPH_TIMEOUT: Request timeout in seconds [default: 30]

        Tool Profile Configuration:
            MEMORY_TOOL_PROFILE: Tool profile (core|extended) [default: core]

        Logging Configuration:
            MEMORY_LOG_LEVEL: Log level (DEBUG|INFO|WARNING|ERROR) [default: INFO]

        Multi-Tenancy Configuration (Phase 1):
            MEMORY_MULTI_TENANT_MODE: Enable multi-tenant features [default: false]
            MEMORY_DEFAULT_TENANT: Default tenant ID for single-tenant mode [default: default]
            MEMORY_REQUIRE_AUTH: Require authentication for operations [default: false]

        Authentication Configuration (Future - Phase 3):
            MEMORY_AUTH_PROVIDER: Authentication provider (none|jwt|oauth2) [default: none]
            MEMORY_JWT_SECRET: JWT signing secret (required if auth_provider=jwt)
            MEMORY_JWT_ALGORITHM: JWT algorithm [default: HS256]

        Audit Configuration (Future - Phase 4):
            MEMORY_ENABLE_AUDIT_LOG: Log all access events [default: false]
    """

    BACKEND = _EnvVar("MEMORY_BACKEND", default="sqlite")

    NEO4J_URI = _EnvVar(
        "MEMORY_NEO4J_URI", "NEO4J_URI", default="bolt://localhost:7687"
    )
    NEO4J_USER = _EnvVar("MEMORY_NEO4J_USER", "NEO4J_USER", default="neo4j")
    NEO4J_PASSWORD = _EnvVar("MEMORY_NEO4J_PASSWORD", "NEO4J_PASSWORD", default=None)
    NEO4J_DATABASE = _EnvVar("MEMORY_NEO4J_DATABASE", default="neo4j")

    MEMGRAPH_URI = _EnvVar("MEMORY_MEMGRAPH_URI", default="bolt://localhost:7687")
    MEMGRAPH_USER = _EnvVar("MEMORY_MEMGRAPH_USER", default="")
    MEMGRAPH_PASSWORD = _EnvVar("MEMORY_MEMGRAPH_PASSWORD", default="")

    SQLITE_PATH = _EnvVar("MEMORY_SQLITE_PATH", default=_DEFAULT_DB_PATH)

    TURSO_PATH = _EnvVar("MEMORY_TURSO_PATH", default=_DEFAULT_DB_PATH)
    TURSO_DATABASE_URL = _EnvVar("TURSO_DATABASE_URL", default=None)
    TURSO_AUTH_TOKEN = _EnvVar("TURSO_AUTH_TOKEN", default=None)

    MEMORYGRAPH_API_KEY = _EnvVar("MEMORYGRAPH_API_KEY", default=None)
    MEMORYGRAPH_API_URL = _EnvVar(
        "MEMORYGRAPH_API_URL", default="https://graph-api.memorygraph.dev"
    )
    MEMORYGRAPH_TIMEOUT = _EnvVar("MEMORYGRAPH_TIMEOUT", default=30, cast=int)

    CLOUD_MAX_RETRIES = _EnvVar("MEMORYGRAPH_MAX_RETRIES", default=3, cast=int)
    CLOUD_RETRY_BACKOFF_BASE = _EnvVar(
        "MEMORYGRAPH_RETRY_BACKOFF", default=1.0, cast=float
    )
    CLOUD_CIRCUIT_BREAKER_THRESHOLD = _EnvVar(
        "MEMORYGRAPH_CB_THRESHOLD", default=5, cast=int
    )
    CLOUD_CIRCUIT_BREAKER_TIMEOUT = _EnvVar(
        "MEMORYGRAPH_CB_TIMEOUT", default=60.0, cast=float
    )

    FALKORDB_HOST = _EnvVar(
        "MEMORY_FALKORDB_HOST", "FALKORDB_HOST", default="localhost"
    )
    FALKORDB_PORT = _EnvVar(
        "MEMORY_FALKORDB_PORT", "FALKORDB_PORT", default=6379, cast=int
    )
    FALKORDB_PASSWORD = _EnvVar(
        "MEMORY_FALKORDB_PASSWORD", "FALKORDB_PASSWORD", default=None
    )

    FALKORDBLITE_PATH = _EnvVar(
        "MEMORY_FALKORDBLITE_PATH",
        "FALKORDBLITE_PATH",
        default=_DEFAULT_FALKORDBLITE_PATH,
    )

    LADYBUGDB_PATH = _EnvVar(
        "MEMORY_LADYBUGDB_PATH", "LADYBUGDB_PATH", default=_DEFAULT_LADYBUGDB_PATH
    )

    TOOL_PROFILE = _EnvVar("MEMORY_TOOL_PROFILE", default="core")

    LOG_LEVEL = _EnvVar("MEMORY_LOG_LEVEL", default="INFO")

    AUTO_EXTRACT_ENTITIES = _EnvVar(
        "MEMORY_AUTO_EXTRACT_ENTITIES", default=True, cast=bool
    )
    SESSION_BRIEFING = _EnvVar("MEMORY_SESSION_BRIEFING", default=True, cast=bool)
    BRIEFING_VERBOSITY = _EnvVar("MEMORY_BRIEFING_VERBOSITY", default="standard")
    BRIEFING_RECENCY_DAYS = _EnvVar("MEMORY_BRIEFING_RECENCY_DAYS", default=7, cast=int)

    ALLOW_RELATIONSHIP_CYCLES = _EnvVar("MEMORY_ALLOW_CYCLES", default=False, cast=bool)

    MULTI_TENANT_MODE = _EnvVar("MEMORY_MULTI_TENANT_MODE", default=False, cast=bool)
    DEFAULT_TENANT = _EnvVar("MEMORY_DEFAULT_TENANT", default="default")
    REQUIRE_AUTH = _EnvVar("MEMORY_REQUIRE_AUTH", default=False, cast=bool)

    AUTH_PROVIDER = _EnvVar("MEMORY_AUTH_PROVIDER", default="none")
    JWT_SECRET = _EnvVar("MEMORY_JWT_SECRET", default=None)
    JWT_ALGORITHM = _EnvVar("MEMORY_JWT_ALGORITHM", default="HS256")

    ENABLE_AUDIT_LOG = _EnvVar("MEMORY_ENABLE_AUDIT_LOG", default=False, cast=bool)

    @classmethod
    def get_backend_type(cls) -> BackendType:
        """Get the configured backend type, falling back to AUTO for unknown values."""
        backend_str = cls.BACKEND.lower()
        try:
            return BackendType(backend_str)
        except ValueError:
            return BackendType.AUTO

    @classmethod
    def is_env_set(cls, attr_name: str) -> bool:
        """Check if a Config attribute's underlying env var is explicitly set.

        When the attribute is still an ``_EnvVar`` descriptor, delegates to
        ``_EnvVar.is_set()`` which checks ``os.environ`` membership (not
        truthiness).  If the descriptor has been replaced by direct assignment
        (e.g. in tests via ``Config.X = val``), returns ``True`` since the
        caller explicitly configured it.
        """
        descriptor = cls.__dict__.get(attr_name)
        if hasattr(descriptor, "is_set"):
            return descriptor.is_set()
        return attr_name in cls.__dict__

    @classmethod
    def is_neo4j_configured(cls) -> bool:
        """Check if Neo4j backend is properly configured."""
        return cls.is_env_set("NEO4J_PASSWORD")

    @classmethod
    def is_memgraph_configured(cls) -> bool:
        """Check if Memgraph backend is configured."""
        return cls.is_env_set("MEMGRAPH_URI")

    @classmethod
    def is_multi_tenant_mode(cls) -> bool:
        """Check if multi-tenant mode is enabled."""
        return cls.MULTI_TENANT_MODE

    @classmethod
    def get_default_tenant(cls) -> str:
        """Get default tenant ID for single-tenant mode."""
        return cls.DEFAULT_TENANT

    @classmethod
    def get_enabled_tools(cls) -> list[str]:
        """Get the list of enabled tools based on the configured profile.

        Legacy profile names (lite, standard, full) are mapped to their
        modern equivalents. Unrecognized profiles fall back to core.
        """
        profile = cls.TOOL_PROFILE.lower()
        legacy_map = {"lite": "core", "standard": "extended", "full": "extended"}
        profile = legacy_map.get(profile, profile)
        return TOOL_PROFILES.get(profile, TOOL_PROFILES["core"])

    @classmethod
    def get_config_summary(cls) -> dict:
        """Get a summary of current configuration (without sensitive data)."""
        return {
            "backend": cls.BACKEND,
            "neo4j": {
                "uri": cls.NEO4J_URI,
                "user": cls.NEO4J_USER,
                "password_configured": bool(cls.NEO4J_PASSWORD),
                "database": cls.NEO4J_DATABASE,
            },
            "memgraph": {
                "uri": cls.MEMGRAPH_URI,
                "user": cls.MEMGRAPH_USER,
                "password_configured": bool(cls.MEMGRAPH_PASSWORD),
            },
            "sqlite": {"path": cls.SQLITE_PATH},
            "turso": {
                "path": cls.TURSO_PATH,
                "database_url": cls.TURSO_DATABASE_URL,
                "auth_token_configured": bool(cls.TURSO_AUTH_TOKEN),
            },
            "cloud": {
                "api_url": cls.MEMORYGRAPH_API_URL,
                "api_key_configured": bool(cls.MEMORYGRAPH_API_KEY),
                "timeout": cls.MEMORYGRAPH_TIMEOUT,
            },
            "falkordb": {
                "host": cls.FALKORDB_HOST,
                "port": cls.FALKORDB_PORT,
                "password_configured": bool(cls.FALKORDB_PASSWORD),
            },
            "falkordblite": {
                "path": cls.FALKORDBLITE_PATH,
            },
            "logging": {"level": cls.LOG_LEVEL},
            "features": {
                "auto_extract_entities": cls.AUTO_EXTRACT_ENTITIES,
                "session_briefing": cls.SESSION_BRIEFING,
                "briefing_verbosity": cls.BRIEFING_VERBOSITY,
                "briefing_recency_days": cls.BRIEFING_RECENCY_DAYS,
            },
            "relationships": {"allow_cycles": cls.ALLOW_RELATIONSHIP_CYCLES},
            "multi_tenancy": {
                "enabled": cls.MULTI_TENANT_MODE,
                "default_tenant": cls.DEFAULT_TENANT,
                "require_auth": cls.REQUIRE_AUTH,
                "auth_provider": cls.AUTH_PROVIDER,
                "jwt_secret_configured": bool(cls.JWT_SECRET),
                "audit_log_enabled": cls.ENABLE_AUDIT_LOG,
            },
        }
