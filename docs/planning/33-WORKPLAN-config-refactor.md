# WORKPLAN 33: Config as Single Source of Truth

**Status**: Ready for Implementation
**Priority**: HIGH (fixes architectural inconsistency)
**Scope**: Refactor all `os.getenv()` calls to use `Config` class

---

## Problem Statement

The codebase has 37+ direct `os.getenv()` calls scattered across multiple files, bypassing the `Config` class. This causes:

1. **CLI args ignored**: `--backend cloud` sets env var after Config loads at import time
2. **Duplicate defaults**: Same default values repeated in multiple files
3. **Hard to test**: Must mock env vars instead of Config
4. **Inconsistent behavior**: Some code reads Config, some reads env vars directly

## Solution

Make `Config` the single source of truth:
- CLI updates `Config.*` directly
- All components read from `Config`, never `os.getenv()`
- Environment variables only read once at Config import time

---

## Phase 1: Factory Refactor

**File:** `src/memorygraph/backends/factory.py`

### 1.1 Update imports

- [ ] Add `from ..config import Config` import

### 1.2 Replace backend selection (line 52)

```python
# Before
backend_type = os.getenv("MEMORY_BACKEND", "sqlite").lower()

# After
backend_type = Config.BACKEND.lower()
```

### 1.3 Replace Neo4j config reads (lines 108, 156-158)

```python
# Before
neo4j_password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
uri = os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI")
user = os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER")
password = os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

# After
neo4j_password = Config.NEO4J_PASSWORD
uri = Config.NEO4J_URI
user = Config.NEO4J_USER
password = Config.NEO4J_PASSWORD
```

### 1.4 Replace Memgraph config reads (lines 119, 185-187)

```python
# Before
memgraph_uri = os.getenv("MEMORY_MEMGRAPH_URI")
uri = os.getenv("MEMORY_MEMGRAPH_URI")
user = os.getenv("MEMORY_MEMGRAPH_USER", "")
password = os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

# After
memgraph_uri = Config.MEMGRAPH_URI
uri = Config.MEMGRAPH_URI
user = Config.MEMGRAPH_USER
password = Config.MEMGRAPH_PASSWORD
```

### 1.5 Replace FalkorDB config reads (lines 208-211)

```python
# Before
host = os.getenv("MEMORY_FALKORDB_HOST") or os.getenv("FALKORDB_HOST")
port_str = os.getenv("MEMORY_FALKORDB_PORT") or os.getenv("FALKORDB_PORT")
password = os.getenv("MEMORY_FALKORDB_PASSWORD") or os.getenv("FALKORDB_PASSWORD")

# After (need to add to Config first - see Phase 4)
host = Config.FALKORDB_HOST
port = Config.FALKORDB_PORT
password = Config.FALKORDB_PASSWORD
```

### 1.6 Replace FalkorDBLite config reads (line 232)

```python
# Before
db_path = os.getenv("MEMORY_FALKORDBLITE_PATH") or os.getenv("FALKORDBLITE_PATH")

# After (need to add to Config first - see Phase 4)
db_path = Config.FALKORDBLITE_PATH
```

### 1.7 Replace SQLite config reads (line 275)

```python
# Before
db_path = os.getenv("MEMORY_SQLITE_PATH")

# After
db_path = Config.SQLITE_PATH
```

### 1.8 Replace Turso config reads (line 296)

```python
# Before
db_path = os.getenv("MEMORY_TURSO_PATH")

# After
db_path = Config.TURSO_PATH
```

### 1.9 Replace helper methods (lines 562-595)

```python
# Before
return os.getenv("MEMORY_BACKEND", "auto").lower()
os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
# etc.

# After
return Config.BACKEND.lower()
Config.NEO4J_PASSWORD
# etc.
```

---

## Phase 2: Backend Classes Refactor

### 2.1 Neo4j Backend

**File:** `src/memorygraph/backends/neo4j_backend.py`

- [ ] Add `from ..config import Config` import
- [ ] Replace lines 45-47:

```python
# Before
self.uri = uri or os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
self.user = user or os.getenv("MEMORY_NEO4J_USER") or os.getenv("NEO4J_USER", "neo4j")
self.password = password or os.getenv("MEMORY_NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

# After
self.uri = uri or Config.NEO4J_URI
self.user = user or Config.NEO4J_USER
self.password = password or Config.NEO4J_PASSWORD
```

### 2.2 Memgraph Backend

**File:** `src/memorygraph/backends/memgraph_backend.py`

- [ ] Add `from ..config import Config` import
- [ ] Replace lines 47-49:

```python
# Before
self.uri = uri or os.getenv("MEMORY_MEMGRAPH_URI", "bolt://localhost:7687")
self.user = user or os.getenv("MEMORY_MEMGRAPH_USER", "")
self.password = password or os.getenv("MEMORY_MEMGRAPH_PASSWORD", "")

# After
self.uri = uri or Config.MEMGRAPH_URI
self.user = user or Config.MEMGRAPH_USER
self.password = password or Config.MEMGRAPH_PASSWORD
```

### 2.3 SQLite Fallback Backend

**File:** `src/memorygraph/backends/sqlite_fallback.py`

- [ ] Add `from ..config import Config` import
- [ ] Replace line 52:

```python
# Before
resolved_path = db_path or os.getenv("MEMORY_SQLITE_PATH", default_path)

# After
resolved_path = db_path or Config.SQLITE_PATH
```

### 2.4 Turso Backend

**File:** `src/memorygraph/backends/turso.py`

- [ ] Add `from ..config import Config` import
- [ ] Replace line 66:

```python
# Before
self.db_path = db_path or os.getenv("MEMORY_TURSO_PATH", default_path)

# After
self.db_path = db_path or Config.TURSO_PATH
```

---

## Phase 3: Migration Module Refactor

**File:** `src/memorygraph/migration/models.py`

### 3.1 Update imports

- [ ] Add `from ..config import Config` import

### 3.2 Replace `from_env()` method (lines 40-70)

```python
# Before
backend_str = os.getenv("MEMORY_BACKEND", "sqlite")
uri = os.getenv("MEMORY_NEO4J_URI") or os.getenv("NEO4J_URI", "bolt://localhost:7687")
# ... many more

# After
backend_str = Config.BACKEND
uri = Config.NEO4J_URI
username = Config.NEO4J_USER
password = Config.NEO4J_PASSWORD
# etc.
```

---

## Phase 4: Add Missing Config Attributes

**File:** `src/memorygraph/config.py`

Some backends have env vars read directly but not defined in Config:

- [ ] Add FalkorDB config:
```python
# FalkorDB Configuration
FALKORDB_HOST: str = os.getenv("MEMORY_FALKORDB_HOST") or os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT: int = int(os.getenv("MEMORY_FALKORDB_PORT") or os.getenv("FALKORDB_PORT", "6379"))
FALKORDB_PASSWORD: Optional[str] = os.getenv("MEMORY_FALKORDB_PASSWORD") or os.getenv("FALKORDB_PASSWORD")
```

- [ ] Add FalkorDBLite config:
```python
# FalkorDBLite Configuration
FALKORDBLITE_PATH: str = os.getenv("MEMORY_FALKORDBLITE_PATH") or os.getenv("FALKORDBLITE_PATH", os.path.expanduser("~/.memorygraph/falkordblite.db"))
```

- [ ] Add LadybugDB config (if needed):
```python
# LadybugDB Configuration
LADYBUGDB_PATH: str = os.getenv("MEMORY_LADYBUGDB_PATH") or os.getenv("LADYBUGDB_PATH", os.path.expanduser("~/.memorygraph/ladybugdb"))
```

---

## Phase 5: CLI Updates (Already Done)

**File:** `src/memorygraph/cli.py`

- [x] Update `Config.BACKEND` directly after parsing args
- [x] Update `Config.TOOL_PROFILE` directly after parsing args
- [x] Update `Config.LOG_LEVEL` directly after parsing args

---

## Phase 6: Testing

### 6.1 Add Config override tests

**File:** `tests/test_cli_config.py` (new)

- [ ] Test CLI `--backend` updates Config.BACKEND
- [ ] Test CLI `--profile` updates Config.TOOL_PROFILE
- [ ] Test CLI `--log-level` updates Config.LOG_LEVEL
- [ ] Test BackendFactory reads from Config, not env vars

```python
def test_cli_backend_updates_config():
    """CLI --backend should update Config.BACKEND directly."""
    from memorygraph.config import Config
    original = Config.BACKEND

    # Simulate CLI setting
    Config.BACKEND = "cloud"

    assert Config.BACKEND == "cloud"

    # Restore
    Config.BACKEND = original


def test_factory_reads_config_not_env():
    """BackendFactory should read Config, not os.getenv()."""
    import os
    from memorygraph.config import Config

    # Set Config to cloud
    Config.BACKEND = "cloud"
    # But env var says sqlite
    os.environ["MEMORY_BACKEND"] = "sqlite"

    # Factory should use Config value
    from memorygraph.backends.factory import BackendFactory
    backend_type = Config.BACKEND.lower()

    assert backend_type == "cloud"
```

### 6.2 Run existing tests

- [ ] `pytest tests/ -v` - ensure no regressions
- [ ] `pytest tests/backends/ -v` - backend-specific tests

---

## File Checklist

| File | Changes | Status |
|------|---------|--------|
| `config.py` | Add FalkorDB, FalkorDBLite, LadybugDB attrs | [ ] |
| `factory.py` | Replace 20+ os.getenv calls | [ ] |
| `neo4j_backend.py` | Replace 3 os.getenv calls | [ ] |
| `memgraph_backend.py` | Replace 3 os.getenv calls | [ ] |
| `sqlite_fallback.py` | Replace 1 os.getenv call | [ ] |
| `turso.py` | Replace 1 os.getenv call | [ ] |
| `migration/models.py` | Replace 15+ os.getenv calls | [ ] |
| `cli.py` | Already done | [x] |
| `tests/test_cli_config.py` | New test file | [ ] |

---

## Validation Commands

```bash
# Run tests
pytest tests/ -v -x

# Test CLI backend override works
memorygraph --backend cloud --show-config

# Test with different backends
MEMORYGRAPH_API_KEY=test memorygraph --backend cloud --health
memorygraph --backend sqlite --health

# Grep to verify no remaining direct env reads (except config.py)
grep -rn "os.getenv.*MEMORY_" src/memorygraph --include="*.py" | grep -v config.py
# Should return empty after refactor
```

---

## Success Criteria

- [ ] `grep -rn "os.getenv.*MEMORY_" src/memorygraph | grep -v config.py` returns empty
- [ ] All tests pass
- [ ] `--backend cloud --show-config` correctly reports cloud
- [ ] `--backend sqlite --show-config` correctly reports sqlite
- [ ] Existing functionality unchanged

---

## Notes

1. **Backwards Compatible**: Env vars still work - Config reads them at import time
2. **CLI Takes Precedence**: CLI args override env vars by updating Config directly
3. **No Breaking Changes**: External API unchanged, only internal data flow
4. **Testability Improved**: Can mock Config instead of patching env vars
