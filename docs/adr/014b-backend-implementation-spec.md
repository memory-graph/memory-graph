# Turso Backend Implementation Specification

## Overview

This document provides technical specifications for implementing the Turso backend as defined in ADR-001.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  BackendFactory                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ create_backend() → TursoBackend                 │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              TursoBackend (GraphBackend)                 │
│  ┌────────────────────────────────────────────────┐    │
│  │ Mode 1: Local-only (libsql + local file)       │    │
│  │         - No network, like SQLite               │    │
│  │         - Fast, private, offline                 │    │
│  ├────────────────────────────────────────────────┤    │
│  │ Mode 2: Embedded Replica (libsql + sync)       │    │
│  │         - Local file + remote primary           │    │
│  │         - Auto/manual sync                       │    │
│  │         - Multi-device, cloud backup             │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  libsql Client                           │
│  ┌────────────────────────────────────────────────┐    │
│  │ libsql.connect(path, sync_url, auth_token)     │    │
│  │ conn.execute(sql, params)                       │    │
│  │ conn.sync()  # Embedded replica only            │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐
    │  Local File      │  │  Turso Primary   │
    │  memory.db       │  │  (Edge Cloud)    │
    └──────────────────┘  └──────────────────┘
```

## File Structure

```
src/memorygraph/backends/
├── __init__.py
├── base.py
├── factory.py              # Modified: add Turso
├── turso_backend.py        # NEW
├── sqlite_fallback.py
├── neo4j_backend.py
├── memgraph_backend.py
├── falkordb_backend.py
└── falkordblite_backend.py

src/memorygraph/
├── config.py               # Modified: add Turso config
└── ...

tests/backends/
├── test_turso_backend.py   # NEW
└── ...

docs/
├── quickstart-turso.md     # NEW
└── architecture/
    ├── ADR-001-turso-backend-evaluation.md
    └── turso-backend-implementation-spec.md  # This file
```

## Class Definition

### TursoBackend

**File:** `/src/memorygraph/backends/turso_backend.py`

```python
"""
Turso backend implementation for MemoryGraph.

This module provides a Turso/libSQL backend with optional embedded replica
support for multi-device sync and cloud backup.
"""

import logging
import os
import json
from typing import Any, Optional
from pathlib import Path

from .base import GraphBackend
from ..models import DatabaseConnectionError, SchemaError

logger = logging.getLogger(__name__)


class TursoBackend(GraphBackend):
    """
    Turso/libSQL implementation of the GraphBackend interface.

    Supports two modes:
    1. Local-only: Standard SQLite-compatible local database
    2. Embedded Replica: Local database synced with remote Turso primary

    The mode is determined by presence of sync_url and auth_token.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        sync_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        auto_sync: bool = True,
        sync_interval: int = 300
    ):
        """
        Initialize Turso backend.

        Args:
            db_path: Path to local database file
                     (defaults to ~/.memorygraph/memory.db)
            sync_url: Turso database URL for embedded replica mode
                      (e.g., libsql://your-db.turso.io)
            auth_token: Turso authentication token
            auto_sync: Whether to auto-sync on connect (default: True)
            sync_interval: Seconds between auto-syncs (default: 300)

        Raises:
            DatabaseConnectionError: If libsql is not installed
        """
        # Validate libsql availability
        try:
            import libsql
            self._libsql = libsql
        except ImportError:
            raise DatabaseConnectionError(
                "libsql is required for Turso backend. "
                "Install with: pip install libsql"
            )

        # Path resolution
        default_path = os.path.expanduser("~/.memorygraph/memory.db")
        resolved_path = db_path or os.getenv("MEMORY_TURSO_PATH", default_path)
        self.db_path: str = resolved_path if resolved_path else default_path

        # Sync configuration
        self.sync_url = sync_url or os.getenv("TURSO_DATABASE_URL")
        self.auth_token = auth_token or os.getenv("TURSO_AUTH_TOKEN")
        self.auto_sync = auto_sync
        self.sync_interval = sync_interval

        # Connection state
        self.conn = None
        self._connected = False
        self._is_embedded_replica = bool(self.sync_url and self.auth_token)

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Turso backend initialized: "
            f"path={self.db_path}, "
            f"replica={self._is_embedded_replica}"
        )

    async def connect(self) -> bool:
        """
        Establish connection to Turso database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            if self._is_embedded_replica:
                # Embedded replica mode
                logger.info(f"Connecting to Turso with embedded replica: {self.sync_url}")
                self.conn = self._libsql.connect(
                    self.db_path,
                    sync_url=self.sync_url,
                    auth_token=self.auth_token
                )

                # Initial sync if auto_sync enabled
                if self.auto_sync:
                    logger.info("Performing initial sync...")
                    self.conn.sync()
            else:
                # Local-only mode
                logger.info(f"Connecting to local Turso database: {self.db_path}")
                self.conn = self._libsql.connect(self.db_path)

            self._connected = True
            logger.info("Successfully connected to Turso database")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Turso: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Turso: {e}")

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self.conn:
            # Final sync before closing (if embedded replica)
            if self._is_embedded_replica and self.auto_sync:
                try:
                    logger.info("Performing final sync before disconnect...")
                    self.conn.sync()
                except Exception as e:
                    logger.warning(f"Final sync failed: {e}")

            self.conn.close()
            self.conn = None
            self._connected = False
            logger.info("Turso connection closed")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False
    ) -> list[dict[str, Any]]:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            parameters: Query parameters (dict for named, list for positional)
            write: Whether this is a write operation

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseConnectionError: If not connected
            Exception: For query execution errors
        """
        if not self._connected or not self.conn:
            raise DatabaseConnectionError(
                "Not connected to Turso. Call connect() first."
            )

        try:
            cursor = self.conn.cursor()

            # Execute query with parameters
            if parameters:
                # Convert dict to list for positional placeholders
                if isinstance(parameters, dict):
                    # For named parameters, libsql uses same syntax as SQLite
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            # Commit write operations
            if write:
                self.conn.commit()

                # Sync after writes (if embedded replica and auto_sync)
                if self._is_embedded_replica and self.auto_sync:
                    # TODO: Consider async background sync instead of blocking
                    self.conn.sync()

            # Fetch results
            results = []
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

            return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        Raises:
            SchemaError: If schema initialization fails
        """
        logger.info("Initializing Turso schema for MemoryGraph...")

        if not self.conn:
            raise SchemaError("Not connected to database")

        cursor = self.conn.cursor()

        try:
            # Create nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    from_id TEXT NOT NULL,
                    to_id TEXT NOT NULL,
                    rel_type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_id) REFERENCES nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES nodes(id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_created ON nodes(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(from_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships(to_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(rel_type)")

            # Create FTS5 virtual table for full-text search
            try:
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
                        id,
                        title,
                        content,
                        summary,
                        content='nodes',
                        content_rowid='rowid'
                    )
                """)
                logger.debug("Created FTS5 table for full-text search")
            except Exception as e:
                logger.warning(f"Could not create FTS5 table: {e}")

            self.conn.commit()
            logger.info("Schema initialization completed")

            # Sync schema changes (if embedded replica)
            if self._is_embedded_replica:
                logger.info("Syncing schema to primary...")
                self.conn.sync()

        except Exception as e:
            self.conn.rollback()
            raise SchemaError(f"Failed to initialize schema: {e}")

    async def sync(self) -> None:
        """
        Manually sync embedded replica with primary database.

        This is a Turso-specific method not in the GraphBackend interface.
        Only works in embedded replica mode.

        Raises:
            DatabaseConnectionError: If not connected or not in replica mode
        """
        if not self._connected or not self.conn:
            raise DatabaseConnectionError("Not connected to Turso")

        if not self._is_embedded_replica:
            logger.warning("Sync called but not in embedded replica mode")
            return

        try:
            logger.info("Syncing embedded replica with primary...")
            self.conn.sync()
            logger.info("Sync completed successfully")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise DatabaseConnectionError(f"Sync failed: {e}")

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "turso",
            "db_path": self.db_path,
            "replica_mode": self._is_embedded_replica
        }

        if self._is_embedded_replica:
            health_info["sync_url"] = self.sync_url
            health_info["auto_sync"] = self.auto_sync

        if self._connected and self.conn:
            try:
                cursor = self.conn.cursor()

                # Get memory count
                cursor.execute("SELECT COUNT(*) FROM nodes WHERE label = 'Memory'")
                count = cursor.fetchone()[0]

                health_info["statistics"] = {
                    "memory_count": count
                }

                # Get database size
                if os.path.exists(self.db_path):
                    db_size = os.path.getsize(self.db_path)
                    health_info["database_size_bytes"] = db_size

            except Exception as e:
                logger.warning(f"Could not get detailed health info: {e}")
                health_info["warning"] = str(e)

        return health_info

    def backend_name(self) -> str:
        """Return the name of this backend implementation."""
        return "turso"

    def supports_fulltext_search(self) -> bool:
        """
        Check if this backend supports full-text search.

        Returns:
            True if FTS5 is available
        """
        if not self.conn:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type='table' AND name='nodes_fts'"
            )
            result = cursor.fetchone()
            return bool(result[0] > 0) if result else False
        except Exception:
            return False

    def supports_transactions(self) -> bool:
        """Check if this backend supports ACID transactions."""
        return True  # libsql/SQLite supports transactions

    @classmethod
    async def create(
        cls,
        db_path: Optional[str] = None,
        sync_url: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> "TursoBackend":
        """
        Factory method to create and connect to a Turso backend.

        Args:
            db_path: Path to local database file
            sync_url: Turso database URL (optional)
            auth_token: Turso auth token (optional)

        Returns:
            Connected TursoBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        backend = cls(db_path, sync_url, auth_token)
        await backend.connect()
        return backend
```

## Configuration Changes

### config.py

Add to `Config` class:

```python
# Turso Configuration
TURSO_PATH: str = os.getenv(
    "MEMORY_TURSO_PATH",
    os.path.expanduser("~/.memorygraph/memory.db")
)
TURSO_DATABASE_URL: Optional[str] = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN: Optional[str] = os.getenv("TURSO_AUTH_TOKEN")
TURSO_AUTO_SYNC: bool = os.getenv("MEMORY_TURSO_AUTO_SYNC", "true").lower() == "true"
TURSO_SYNC_INTERVAL: int = int(os.getenv("MEMORY_TURSO_SYNC_INTERVAL", "300"))
```

Add method:

```python
@classmethod
def is_turso_configured(cls) -> bool:
    """Check if Turso backend is configured."""
    return True  # Always available (local-only mode)
```

### factory.py

Add to `BackendFactory.create_backend()`:

```python
elif backend_type == "turso":
    logger.info("Explicit backend selection: Turso")
    return await BackendFactory._create_turso()
```

Add factory method:

```python
@staticmethod
async def _create_turso() -> GraphBackend:
    """
    Create and connect to Turso backend.

    Returns:
        Connected TursoBackend instance

    Raises:
        DatabaseConnectionError: If connection fails
    """
    from .turso_backend import TursoBackend

    db_path = os.getenv("MEMORY_TURSO_PATH")
    sync_url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")

    backend = TursoBackend(
        db_path=db_path,
        sync_url=sync_url,
        auth_token=auth_token
    )
    await backend.connect()
    await backend.initialize_schema()
    return backend
```

Update `is_backend_configured()`:

```python
elif backend_type == "turso":
    return True  # Always available (local-only mode works without config)
```

## Environment Variables

### Local-Only Mode

```bash
MEMORY_BACKEND=turso
MEMORY_TURSO_PATH=/path/to/memory.db  # Optional, defaults to ~/.memorygraph/memory.db
```

### Embedded Replica Mode

```bash
MEMORY_BACKEND=turso
MEMORY_TURSO_PATH=~/.memorygraph/memory.db
TURSO_DATABASE_URL=libsql://your-database.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...
MEMORY_TURSO_AUTO_SYNC=true  # Optional, defaults to true
MEMORY_TURSO_SYNC_INTERVAL=300  # Optional, seconds between syncs
```

### Getting Turso Credentials

```bash
# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Login
turso auth login

# Create database
turso db create memorygraph

# Get URL
turso db show memorygraph --url

# Get auth token
turso db tokens create memorygraph
```

## Testing Strategy

### Unit Tests

**File:** `/tests/backends/test_turso_backend.py`

```python
import pytest
from memorygraph.backends.turso_backend import TursoBackend
from memorygraph.models import DatabaseConnectionError, SchemaError


@pytest.mark.asyncio
async def test_turso_local_only_mode():
    """Test Turso backend in local-only mode (no sync)."""
    backend = TursoBackend(db_path=":memory:")  # In-memory for tests
    await backend.connect()

    assert backend._connected
    assert backend.backend_name() == "turso"
    assert not backend._is_embedded_replica

    await backend.disconnect()
    assert not backend._connected


@pytest.mark.asyncio
async def test_turso_initialize_schema():
    """Test schema initialization."""
    backend = TursoBackend(db_path=":memory:")
    await backend.connect()
    await backend.initialize_schema()

    # Verify tables created
    results = await backend.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    table_names = [r["name"] for r in results]

    assert "nodes" in table_names
    assert "relationships" in table_names

    await backend.disconnect()


@pytest.mark.asyncio
async def test_turso_execute_query():
    """Test query execution."""
    backend = TursoBackend(db_path=":memory:")
    await backend.connect()
    await backend.initialize_schema()

    # Insert node
    await backend.execute_query(
        "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
        parameters=["test-1", "Memory", '{"title": "Test"}'],
        write=True
    )

    # Query node
    results = await backend.execute_query(
        "SELECT * FROM nodes WHERE id = ?",
        parameters=["test-1"]
    )

    assert len(results) == 1
    assert results[0]["id"] == "test-1"

    await backend.disconnect()


@pytest.mark.asyncio
async def test_turso_transactions():
    """Test transaction support."""
    backend = TursoBackend(db_path=":memory:")
    await backend.connect()
    await backend.initialize_schema()

    assert backend.supports_transactions()

    await backend.disconnect()


@pytest.mark.asyncio
async def test_turso_fulltext_search():
    """Test FTS5 support."""
    backend = TursoBackend(db_path=":memory:")
    await backend.connect()
    await backend.initialize_schema()

    # FTS5 should be available
    assert backend.supports_fulltext_search()

    await backend.disconnect()


@pytest.mark.asyncio
async def test_turso_health_check():
    """Test health check."""
    backend = TursoBackend(db_path=":memory:")
    await backend.connect()
    await backend.initialize_schema()

    health = await backend.health_check()

    assert health["connected"] is True
    assert health["backend_type"] == "turso"
    assert health["replica_mode"] is False
    assert "statistics" in health

    await backend.disconnect()
```

### Integration Tests (Requires Turso Account)

Mark with `@pytest.mark.integration` and skip in CI:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_turso_embedded_replica_sync(turso_credentials):
    """Test embedded replica sync (requires Turso account)."""
    backend = TursoBackend(
        db_path="/tmp/test_replica.db",
        sync_url=turso_credentials["url"],
        auth_token=turso_credentials["token"]
    )
    await backend.connect()
    await backend.initialize_schema()

    # Write data
    await backend.execute_query(
        "INSERT INTO nodes (id, label, properties) VALUES (?, ?, ?)",
        parameters=["sync-test", "Memory", '{"title": "Sync Test"}'],
        write=True
    )

    # Manually trigger sync
    await backend.sync()

    await backend.disconnect()
```

### Mock Tests

Use `unittest.mock` to mock libsql for CI:

```python
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_turso_with_mocked_libsql():
    """Test with mocked libsql (no actual connection)."""
    with patch("memorygraph.backends.turso_backend.libsql") as mock_libsql:
        mock_conn = MagicMock()
        mock_libsql.connect.return_value = mock_conn

        backend = TursoBackend(db_path=":memory:")
        await backend.connect()

        mock_libsql.connect.assert_called_once_with(":memory:")
        await backend.disconnect()
```

## Success Criteria

### Phase 1 (MVP)

- [ ] TursoBackend class implemented
- [ ] Local-only mode functional
- [ ] Schema initialization works
- [ ] Basic CRUD operations pass tests
- [ ] Health check returns accurate info
- [ ] Factory integration complete
- [ ] Unit tests pass (80%+ coverage)
- [ ] Documentation complete

### Phase 2 (Embedded Replica)

- [ ] Embedded replica mode functional
- [ ] Auto-sync on connect/disconnect
- [ ] Manual sync() method works
- [ ] Auth token configuration secure
- [ ] Integration tests pass (with Turso account)
- [ ] Sync performance acceptable (<100ms)
- [ ] Multi-device sync validated

### Phase 3 (Advanced)

- [ ] Background periodic sync (optional)
- [ ] Conflict detection (if needed)
- [ ] Migration tool (SQLite → Turso)
- [ ] Vector search exploration
- [ ] Performance benchmarks vs SQLite

## Migration Path

### From SQLite to Turso

Users can migrate by:

1. **Copy database file**:
   ```bash
   cp ~/.memorygraph/memory.db ~/.memorygraph/memory-turso.db
   ```

2. **Update configuration**:
   ```bash
   export MEMORY_BACKEND=turso
   export MEMORY_TURSO_PATH=~/.memorygraph/memory-turso.db
   ```

3. **Optional: Enable sync**:
   ```bash
   # Create Turso database
   turso db create memorygraph

   # Get credentials
   export TURSO_DATABASE_URL=$(turso db show memorygraph --url)
   export TURSO_AUTH_TOKEN=$(turso db tokens create memorygraph)
   ```

4. **First run auto-syncs** local data to Turso primary

### From Turso Back to SQLite

```bash
export MEMORY_BACKEND=sqlite
export MEMORY_SQLITE_PATH=~/.memorygraph/memory-turso.db  # Reuse same file
```

No data loss—both use same SQLite file format.

## Documentation Deliverables

1. **Quickstart Guide** (`/docs/quickstart-turso.md`)
   - Installation steps
   - Local-only setup
   - Embedded replica setup
   - Getting Turso credentials

2. **Multi-Device Guide** (`/docs/guides/multi-device-sync.md`)
   - Sync workflow
   - Conflict scenarios
   - Best practices

3. **API Reference** (update existing)
   - TursoBackend class
   - sync() method
   - Configuration options

4. **FAQ** (add to existing)
   - Turso vs SQLite?
   - Cost considerations?
   - Privacy implications?
   - Offline support?

## Open Questions

1. **Async sync**: Should sync() be non-blocking (background task)?
2. **Conflict resolution**: How to handle write conflicts in embedded replicas?
3. **Periodic sync**: Implement timer-based auto-sync or leave to user?
4. **Retry logic**: Should failed syncs auto-retry?
5. **Metrics**: Track sync frequency, latency, failure rate?

## References

- ADR-001: Turso Backend Evaluation
- Turso Python SDK: https://docs.turso.tech/sdk/python/quickstart
- libsql Python: https://github.com/tursodatabase/libsql-python
- Current SQLite Backend: `/src/memorygraph/backends/sqlite_fallback.py`
- GraphBackend Interface: `/src/memorygraph/backends/base.py`
