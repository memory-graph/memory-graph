"""
Data models for backend migration.

Provides configuration, options, and result models for migrating memories
between different backend types.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from ..config import BackendType


@dataclass
class BackendConfig:
    """
    Configuration for a backend connection.

    For SQLite/FalkorDBLite backends, use path.
    For Neo4j/Memgraph/FalkorDB backends, use uri, username, password.
    """
    backend_type: BackendType
    path: Optional[str] = None  # For SQLite/FalkorDBLite
    uri: Optional[str] = None  # For Neo4j/Memgraph/FalkorDB
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None

    @classmethod
    def from_env(cls) -> "BackendConfig":
        """
        Create config from current environment variables.

        Reads MEMORY_BACKEND and related env vars to construct config.
        Note: Reads env vars directly to ensure fresh values.
        """
        import os

        # Read backend type directly from env to get current value
        backend_str = os.getenv("MEMORY_BACKEND", "sqlite")
        backend_type = BackendType(backend_str)

        # Determine URI and credentials based on backend type
        uri = None
        username = None
        password = None
        path = None

        if backend_type == BackendType.NEO4J:
            uri = os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
            username = os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

        elif backend_type == BackendType.MEMGRAPH:
            uri = os.getenv("MEMORY_MEMGRAPH_URI", "bolt://localhost:7687")
            username = os.getenv("MEMORY_MEMGRAPH_USER", "")
            password = os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

        elif backend_type == BackendType.FALKORDB:
            # FalkorDB uses Redis protocol, construct URI from host:port
            host = os.getenv("MEMORY_FALKORDB_HOST") or os.getenv("FALKORDB_HOST", "localhost")
            port = os.getenv("MEMORY_FALKORDB_PORT") or os.getenv("FALKORDB_PORT", "6379")
            uri = f"redis://{host}:{port}"
            password = os.getenv("MEMORY_FALKORDB_PASSWORD") or os.getenv("FALKORDB_PASSWORD")

        elif backend_type == BackendType.SQLITE:
            path = os.getenv("MEMORY_SQLITE_PATH", os.path.expanduser("~/.memorygraph/memory.db"))

        elif backend_type == BackendType.FALKORDBLITE:
            path = os.getenv("MEMORY_FALKORDBLITE_PATH") or os.getenv("FALKORDBLITE_PATH", os.path.expanduser("~/.memorygraph/falkordblite.db"))

        return cls(
            backend_type=backend_type,
            path=path,
            uri=uri,
            username=username,
            password=password
        )

    def validate(self) -> List[str]:
        """
        Validate configuration has required fields for backend type.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.backend_type in (BackendType.SQLITE, BackendType.FALKORDBLITE):
            if not self.path:
                errors.append(f"{self.backend_type.value} backend requires 'path' parameter")

        elif self.backend_type in (BackendType.NEO4J, BackendType.MEMGRAPH, BackendType.FALKORDB):
            if not self.uri:
                errors.append(f"{self.backend_type.value} backend requires 'uri' parameter")

        return errors


@dataclass
class MigrationOptions:
    """Options for migration operation."""
    dry_run: bool = False
    verbose: bool = False
    skip_duplicates: bool = True
    verify: bool = True
    rollback_on_failure: bool = True
    since: Optional[str] = None  # Timestamp for incremental migration (future feature)


@dataclass
class ValidationResult:
    """Result of validation checks."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Result of post-migration verification."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    source_count: int = 0
    target_count: int = 0
    sample_checks: int = 0
    sample_passed: int = 0


@dataclass
class MigrationResult:
    """Result of migration operation."""
    success: bool
    dry_run: bool = False
    source_stats: Optional[Dict[str, Any]] = None
    target_stats: Optional[Dict[str, Any]] = None
    imported_memories: int = 0
    imported_relationships: int = 0
    skipped_memories: int = 0
    verification_result: Optional[VerificationResult] = None
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
