# ADR-001: Turso DB Backend Evaluation

## Status: Proposed

## Context

The claude-code-memory project currently supports multiple graph database backends (SQLite, Neo4j, FalkorDB, FalkorDBLite, Memgraph) through a unified `GraphBackend` interface. Turso DB has emerged as a potential backend option that could provide unique value for memory graph use cases.

### What is Turso?

Turso is a distributed database built on **libSQL**, an open-source fork of SQLite. Key characteristics:

- **SQLite-compatible**: Uses SQLite file format and SQL syntax
- **Edge deployment**: Distributed databases across 100+ global edge locations
- **Embedded replicas**: Local-first architecture with automatic sync
- **libSQL foundation**: Extends SQLite with replication and modern async APIs
- **Low latency**: Sub-40ms query times globally via edge proximity

### Current Backend Architecture

The project uses a clean abstraction layer:

```python
class GraphBackend(ABC):
    async def connect() -> bool
    async def disconnect() -> None
    async def execute_query(query: str, parameters: dict, write: bool) -> list
    async def initialize_schema() -> None
    async def health_check() -> dict
    def backend_name() -> str
    def supports_fulltext_search() -> bool
    def supports_transactions() -> bool
```

Backends are selected via `BackendFactory` using `MEMORY_BACKEND` environment variable:
- `sqlite` (default): Local SQLite + NetworkX for graph operations
- `neo4j`: Native graph database with Cypher
- `memgraph`: In-memory graph database
- `falkordb` / `falkordblite`: Redis-based graph databases
- `auto`: Automatic selection

### Current SQLite Backend Implementation

The `SQLiteFallbackBackend`:
- Uses standard `sqlite3` module
- Stores graph in tables (`nodes`, `relationships`)
- Loads graph into NetworkX for traversal
- Supports FTS5 full-text search
- Single-file, local-only storage
- No replication or sync capabilities

## Research Findings: Turso Capabilities

### Python SDK (`libsql` package)

**Installation:**
```bash
pip install libsql
```

**Connection Modes:**

1. **Local-only** (like current SQLite):
```python
import libsql
conn = libsql.connect("memory.db")
```

2. **Remote-only** (cloud-hosted):
```python
conn = libsql.connect(
    database_url=os.getenv("TURSO_DATABASE_URL"),
    auth_token=os.getenv("TURSO_AUTH_TOKEN")
)
```

3. **Embedded Replica** (local + sync):
```python
conn = libsql.connect(
    "local.db",
    sync_url=os.getenv("TURSO_DATABASE_URL"),
    auth_token=os.getenv("TURSO_AUTH_TOKEN")
)
conn.sync()  # Sync local with primary
```

**Key Features:**
- **Async support**: Native async/await API (though docs show sync API)
- **SQLite compatibility**: Standard SQL, FTS5, same file format
- **Transactions & batches**: Full ACID transaction support
- **Placeholders**: Positional and named parameters
- **Sync method**: `conn.sync()` for embedded replicas
- **No external server required** for local-only mode

### Turso-Specific Features

1. **Embedded Replicas**
   - Local SQLite file + remote primary database
   - Writes forwarded to primary, then propagated to replicas
   - Reads from local replica (ultra-low latency)
   - Manual sync control via `sync()` method

2. **Multi-device Sync**
   - Multiple clients can sync with same primary
   - Enables memory graph sharing across devices
   - Conflict resolution handled by primary

3. **Edge Deployment**
   - Primary database deployed to nearest edge location
   - Sub-40ms latency globally
   - No infrastructure management

4. **Vector Search** (native)
   - Built-in similarity search
   - No extensions required
   - Relevant for semantic memory search

5. **Modern async design**
   - io_uring support (Linux)
   - Better concurrency than traditional SQLite

### SQLite Compatibility

- **100% compatible** with SQLite file format
- Can migrate existing SQLite databases
- Supports all SQLite features (FTS5, JSON, etc.)
- Same SQL dialect
- Can fall back to standard sqlite3 if Turso unavailable

## Architectural Analysis

### Integration Approach: Option A - Extend SQLiteFallbackBackend

**Concept:** Add Turso sync capabilities to existing SQLite backend

```python
class SQLiteFallbackBackend(GraphBackend):
    def __init__(self, db_path: str, sync_url: str = None, auth_token: str = None):
        self.db_path = db_path
        self.sync_url = sync_url
        self.auth_token = auth_token

        if sync_url:
            # Use libsql with embedded replica
            self.conn = libsql.connect(db_path, sync_url=sync_url, auth_token=auth_token)
        else:
            # Use standard sqlite3
            self.conn = sqlite3.connect(db_path)
```

**Pros:**
- Minimal code changes
- Backward compatible (local-only still works)
- Optional Turso features (opt-in)
- Single backend handles both cases

**Cons:**
- Mixes two different client libraries (sqlite3 vs libsql)
- Conditional logic complicates implementation
- Not clear to users when Turso features are active
- Hard to test both paths

### Integration Approach: Option B - Separate TursoBackend

**Concept:** New dedicated backend for Turso-specific features

```python
class TursoBackend(GraphBackend):
    def __init__(
        self,
        db_path: str,
        sync_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        auto_sync: bool = True
    ):
        self.db_path = db_path
        self.sync_url = sync_url
        self.auth_token = auth_token
        self.auto_sync = auto_sync
        self.conn = None

    async def connect(self) -> bool:
        import libsql

        if self.sync_url:
            # Embedded replica mode
            self.conn = libsql.connect(
                self.db_path,
                sync_url=self.sync_url,
                auth_token=self.auth_token
            )
        else:
            # Local-only mode
            self.conn = libsql.connect(self.db_path)

        if self.auto_sync and self.sync_url:
            self.conn.sync()

        return True

    async def sync(self) -> None:
        """Sync embedded replica with primary (Turso-specific)"""
        if self.conn and self.sync_url:
            self.conn.sync()
```

**Configuration:**
```bash
# Local-only (like SQLite)
MEMORY_BACKEND=turso
MEMORY_TURSO_PATH=/path/to/memory.db

# With cloud sync
MEMORY_BACKEND=turso
MEMORY_TURSO_PATH=/path/to/memory.db
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-token
MEMORY_TURSO_AUTO_SYNC=true
```

**Pros:**
- Clean separation of concerns
- Turso-specific features clearly exposed
- Easier to maintain and test
- Can add Turso-only optimizations (vector search, etc.)
- No impact on existing SQLite backend

**Cons:**
- Code duplication with SQLiteFallbackBackend
- More files to maintain
- Users must choose between `sqlite` and `turso`

### Integration Approach: Option C - Hybrid with Feature Detection

**Concept:** SQLite backend auto-detects libsql and upgrades features

```python
class SQLiteFallbackBackend(GraphBackend):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.sync_url = os.getenv("TURSO_DATABASE_URL")
        self.auth_token = os.getenv("TURSO_AUTH_TOKEN")
        self.use_libsql = False

    async def connect(self) -> bool:
        try:
            import libsql
            self.use_libsql = True

            if self.sync_url and self.auth_token:
                self.conn = libsql.connect(
                    self.db_path,
                    sync_url=self.sync_url,
                    auth_token=self.auth_token
                )
                logger.info("Using Turso with embedded replica")
            else:
                self.conn = libsql.connect(self.db_path)
                logger.info("Using libsql (local-only)")
        except ImportError:
            import sqlite3
            self.conn = sqlite3.connect(self.db_path)
            logger.info("Using standard SQLite")

        return True
```

**Pros:**
- Seamless upgrade path (install libsql, get Turso features)
- No breaking changes
- Single backend to maintain
- Auto-detects capabilities

**Cons:**
- Complex conditional logic
- Hard to predict behavior
- Mixing concerns (sync + local + fallback)
- Testing complexity (3 modes)

## New Capabilities Enabled by Turso

### 1. Multi-Device Memory Sync

**Use Case:** Developer uses multiple machines (laptop, desktop, cloud VM)

**How:**
- Each device has embedded replica (local.db)
- All sync with single Turso primary database
- Memories created on laptop appear on desktop after sync
- Fast local reads, automatic background sync

**Implementation:**
```python
# On each device
MEMORY_BACKEND=turso
MEMORY_TURSO_PATH=~/.memorygraph/memory.db
TURSO_DATABASE_URL=libsql://shared-memory.turso.io
TURSO_AUTH_TOKEN=<shared-token>
```

**Value:** Unified memory graph across all development environments

### 2. Cloud Backup Without Export

**Use Case:** Automatic backup to cloud without manual export

**How:**
- Embedded replica (local.db) for fast access
- Turso primary database serves as continuous backup
- No manual export/import needed
- Point-in-time recovery via Turso platform

**Value:** Peace of mind, disaster recovery

### 3. Team Memory Sharing

**Use Case:** Team shares learned patterns and solutions

**How:**
- Shared Turso database
- Each team member has local replica
- Team memories propagate to all members
- Privacy control via separate projects/tags

**Value:** Collective knowledge base, onboarding acceleration

### 4. Edge Deployment for Global Teams

**Use Case:** Distributed team across continents

**How:**
- Turso primary deployed to optimal edge location
- Low-latency access from all regions
- No VPN or complex infrastructure

**Value:** Consistent performance globally

### 5. Offline-First Development

**Use Case:** Work without internet, sync later

**How:**
- Embedded replica always available locally
- Create memories offline
- Sync when connected via `conn.sync()`

**Value:** Uninterrupted workflow, mobile development

## Trade-offs

### Turso vs Current SQLite Backend

| Aspect | SQLite Backend | Turso Backend |
|--------|---------------|---------------|
| **Setup** | Zero config | Requires Turso account (for sync) |
| **Dependencies** | sqlite3 (built-in) + NetworkX | libsql package |
| **Latency** | Local file access | Local file access (same) |
| **Sync** | None | Optional embedded replicas |
| **Multi-device** | Manual export/import | Automatic sync |
| **Cloud backup** | Manual | Automatic (if configured) |
| **Cost** | Free | Free tier + paid for scale |
| **Privacy** | Fully local | Local + optional cloud |
| **Portability** | Standard SQLite | libsql (SQLite fork) |

### Concerns

1. **External Dependency**: Requires Turso service (mitigated by local-only mode)
2. **Authentication**: Requires auth tokens for sync (added complexity)
3. **Vendor Lock-in**: Turso-specific features (mitigated by SQLite compatibility)
4. **Migration Path**: Users must choose sync vs local-only upfront
5. **Testing**: Need Turso test instances or mocks

## Alternatives Considered

### Alternative 1: Keep SQLite, Add Manual Sync Tools

**Approach:** Provide export/import scripts for manual sync

**Rejected because:**
- Poor UX (manual process)
- No real-time sync
- Error-prone (forget to sync)

### Alternative 2: Use Git for Memory Sync

**Approach:** Store memory.db in git, sync via commits

**Rejected because:**
- Binary file conflicts
- Not designed for database sync
- Complex merge resolution

### Alternative 3: Custom WebSocket Sync

**Approach:** Build custom sync protocol over WebSocket

**Rejected because:**
- Reinventing the wheel
- Maintenance burden
- Less reliable than Turso

### Alternative 4: Use Litestream

**Approach:** Use Litestream for SQLite replication

**Rejected because:**
- Streaming replication (not embedded replicas)
- Requires separate service
- More complex than Turso
- No built-in edge deployment

## Decision: Recommendation

### Recommended Approach: **Option B - Separate TursoBackend**

**Rationale:**
1. **Clear separation**: Turso features explicit, not hidden
2. **User choice**: Users consciously opt-in to sync features
3. **Maintainability**: Easier to test and debug
4. **Future-proof**: Can add Turso-specific optimizations (vector search)
5. **No regression risk**: Existing SQLite backend untouched

### Implementation Plan

#### Phase 1: Core Backend (MVP)

1. Create `/src/memorygraph/backends/turso_backend.py`
2. Implement `TursoBackend` class extending `GraphBackend`
3. Support local-only mode (no sync) first
4. Reuse SQLite schema initialization
5. Add to `BackendFactory`
6. Configuration via environment variables:
   - `MEMORY_BACKEND=turso`
   - `MEMORY_TURSO_PATH=~/.memorygraph/memory.db`

#### Phase 2: Embedded Replica Support

1. Add sync URL and auth token configuration
2. Implement `sync()` method (Turso-specific)
3. Auto-sync on connect (configurable)
4. Periodic sync (optional background task)
5. Configuration:
   - `TURSO_DATABASE_URL=libsql://...`
   - `TURSO_AUTH_TOKEN=...`
   - `MEMORY_TURSO_AUTO_SYNC=true|false`

#### Phase 3: Advanced Features

1. Health check includes sync status
2. Manual sync tool/command
3. Conflict detection (if applicable)
4. Vector search integration (future)
5. Migration tool (SQLite → Turso)

### Configuration Design

```python
# config.py additions
class Config:
    # Turso Configuration
    TURSO_PATH: str = os.getenv(
        "MEMORY_TURSO_PATH",
        os.path.expanduser("~/.memorygraph/memory.db")
    )
    TURSO_DATABASE_URL: Optional[str] = os.getenv("TURSO_DATABASE_URL")
    TURSO_AUTH_TOKEN: Optional[str] = os.getenv("TURSO_AUTH_TOKEN")
    TURSO_AUTO_SYNC: bool = os.getenv("MEMORY_TURSO_AUTO_SYNC", "true").lower() == "true"
    TURSO_SYNC_INTERVAL: int = int(os.getenv("MEMORY_TURSO_SYNC_INTERVAL", "300"))  # 5 min
```

### Backend Factory Addition

```python
# factory.py
class BackendFactory:
    @staticmethod
    async def create_backend() -> GraphBackend:
        backend_type = os.getenv("MEMORY_BACKEND", "sqlite").lower()

        # ... existing backends ...

        elif backend_type == "turso":
            logger.info("Explicit backend selection: Turso")
            return await BackendFactory._create_turso()

    @staticmethod
    async def _create_turso() -> GraphBackend:
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

### Dependencies

```toml
# pyproject.toml
[project.optional-dependencies]
turso = [
    "libsql>=0.4.0",
]
```

Installation:
```bash
pip install memorygraphMCP[turso]
```

## Consequences

### Positive

1. **Multi-device workflow**: Seamless memory sync across machines
2. **Cloud backup**: Automatic, continuous backup to Turso
3. **Team collaboration**: Shared memory graphs for teams
4. **Zero infrastructure**: No database server to manage
5. **Fast local access**: Same performance as SQLite
6. **Offline capability**: Work disconnected, sync later
7. **Migration path**: Easy upgrade from SQLite (same schema)
8. **Future features**: Vector search, analytics on cloud data

### Negative

1. **New dependency**: libsql package required
2. **Configuration complexity**: More environment variables
3. **Cost**: Turso paid tiers for high usage (free tier generous)
4. **External service**: Requires Turso account for sync features
5. **Testing overhead**: Need Turso test instances or mocks
6. **Documentation**: Need guides for setup and sync workflows

### Neutral

1. **Optional feature**: Local-only mode requires no Turso account
2. **Backward compatible**: Doesn't affect existing backends
3. **Standard SQL**: Same queries as SQLite backend

### Risks

1. **Turso service availability**: Mitigated by local-first design (embedded replicas)
2. **Data privacy**: User data sent to Turso (mitigated by local-only option)
3. **Vendor dependency**: Mitigated by SQLite compatibility (can export)
4. **Breaking changes**: Turso/libsql API changes (mitigated by versioning)

## Follow-up Work

### Documentation

1. **Setup guide**: How to configure Turso backend
2. **Sync guide**: Using embedded replicas for multi-device
3. **Team guide**: Sharing memory graphs across team
4. **Migration guide**: SQLite → Turso conversion
5. **Troubleshooting**: Common sync issues

### Testing

1. **Unit tests**: TursoBackend in local-only mode
2. **Integration tests**: Embedded replica sync (requires Turso account)
3. **Mock tests**: Mock libsql for CI/CD
4. **Performance tests**: Compare SQLite vs Turso latency

### Future Enhancements

1. **Vector search**: Leverage Turso's native vector search for semantic memory
2. **Analytics**: Query memory graph via Turso Platform API
3. **Branching**: Use Turso database branching for experiments
4. **Point-in-time recovery**: Restore memory graph to previous state
5. **Read replicas**: Multiple edge replicas for global teams

## References

- [Turso Documentation](https://docs.turso.tech/)
- [Turso Python SDK](https://docs.turso.tech/sdk/python/quickstart)
- [libSQL Python Bindings](https://github.com/tursodatabase/libsql-python)
- [libSQL (SQLite Fork)](https://github.com/tursodatabase/libsql)
- [Turso Platform](https://turso.tech/)

## Decision Date

2025-12-03

## Decision Makers

- Gregory Dickson (Architect)

## Review Date

To be determined (after implementation and user feedback)
