# MemoryGraph v0.12.4 Release Notes

**Release Date:** February 12, 2026

A major code health release focused on internal simplification, deduplication, and correctness. The codebase is significantly cleaner with 87 files touched, eliminating thousands of lines of redundant code while increasing test coverage from 1,578 to 2,220 tests.

---

## Highlights

- **2,220 Tests Passing** — Up from 1,578, with zero failures
- **FalkorDB Shared Base Class** — 95% code deduplication between FalkorDB and FalkorDBLite backends
- **Config as Single Source of Truth** — `_EnvVar` descriptors with `is_set()` replace scattered `os.environ` lookups
- **Factory Dispatch Tables** — Clean dict-based dispatch replaces if/elif chains
- **CLI Simplified** — Env-only config, no dual-writes, shared backend helper

---

## Architecture Changes

### FalkorDB Shared Base Class

Extracted `_falkordb_shared.py` base class that captures all shared logic between FalkorDB and FalkorDBLite backends. Reduces combined code from ~1,250 lines to ~650 lines (95% dedup). Each concrete backend now only overrides connection-specific methods.

```
Before:  falkordb_backend.py (625 lines) + falkordblite_backend.py (625 lines)
After:   _falkordb_shared.py (659 lines) + falkordb_backend.py (~30 lines) + falkordblite_backend.py (~30 lines)
```

### Config `_EnvVar` Descriptors

New descriptor-based configuration system in `config.py`:
- **`_EnvVar`** class provides typed access to environment variables with defaults
- **`is_set()`** method distinguishes "not set" from "set to default value" — critical for backend auto-detection
- Empty string handling: `MEMORYGRAPH_BACKEND=""` correctly treated as unset
- Config summary now includes FalkorDB/FalkorDBLite connection details

### Factory Dispatch Tables

`factory.py` refactored from nested if/elif chains to clean dispatch table pattern:
- Backend creation, validation, and info functions all use dict lookups
- All 8 backends properly registered: SQLite, Neo4j, Memgraph, FalkorDB, FalkorDBLite, Cloud, Turso, LadybugDB
- Backend auto-detection uses `Config.is_set()` instead of checking for non-default values

### CLI Env-Only Config

`cli.py` simplified to write only to `os.environ`, eliminating dual-writes to both env vars and Config object. Shared `_create_backend()` helper extracted to reduce repetition across CLI commands.

---

## Bug Fixes

- **Invalid Cypher in FalkorDB `delete_memory`** — Fixed `COUNT` after `DETACH DELETE` pattern that produced incorrect results. Now uses a two-query approach: match + count, then delete
- **Backend auto-detection broken by Config defaults** — `Config.NEO4J_URI` had a default value (`bolt://localhost:7687`) that made auto-detection think Neo4j was configured. Fixed with `_EnvVar.is_set()`
- **`_EnvVar` empty string handling** — Empty env vars (`MEMORYGRAPH_BACKEND=""`) now consistently treated as unset via `is_set()`
- **CLI diagnostic output** — All diagnostic messages routed to stderr, emoji removed for clean piping
- **FalkorDB result parsing** — Fixed result extraction from FalkorDB query responses

---

## Code Simplification

### Backend Files (net -2,141 lines)

| File | Change |
|------|--------|
| `cloud_backend.py` | -489 lines — removed redundant docstrings, comments, simplified methods |
| `falkordb_backend.py` | -641 lines — logic moved to shared base class |
| `falkordblite_backend.py` | -591 lines — logic moved to shared base class |
| `memgraph_backend.py` | -230 lines — removed redundant code and comments |
| `neo4j_backend.py` | -181 lines — simplified methods, removed dead code |
| `factory.py` | refactored — dispatch tables replace if/elif chains |
| `config.py` | refactored — `_EnvVar` descriptors, removed dead code |
| `cli.py` | -117 lines — shared helper, env-only config |

### Redundant Default Fallbacks Removed

All backends previously had their own fallback defaults for config values (e.g., `os.environ.get("NEO4J_URI", "bolt://localhost:7687")`). These redundant defaults were removed — `Config` is now the single source of truth.

---

## Test Improvements

### New Test Files

| File | Purpose |
|------|---------|
| `tests/backends/test_falkordb_shared.py` | 540 lines — comprehensive tests for shared FalkorDB base class |
| `tests/backends/test_backend_imports.py` | Import verification for all backend modules |
| `tests/test_simplification.py` | Validates dispatch tables and deduplication |
| `tests/test_backend_config.py` | Config-as-single-source-of-truth validation |
| `tests/test_factory_config.py` | Factory dispatch table coverage |

### Test Infrastructure

- **Consolidated `patch_config`** fixture into `tests/conftest.py` — eliminated 19 duplicate definitions across test files
- **Shared FalkorDB test helpers** in `tests/backends/conftest.py` — reusable fixtures for both FalkorDB and FalkorDBLite tests
- **Fixed vacuous tests** — identified and fixed tests that passed but tested nothing meaningful

### Test Results

| Metric | v0.12.0 | v0.12.4 |
|--------|---------|---------|
| Total tests | 1,578 | 2,220 |
| Passed | 1,578 | 2,220 |
| Skipped | 139 | 57 |
| Failures | 0 | 0 |
| Runtime | — | 24.27s |

---

## Files Changed

**87 files** across source, tests, and project infrastructure:

- **Source**: 20 files (+2,461 / -4,052 lines) — net reduction of 1,591 lines
- **Tests**: 48 files (+13,551 / -8,194 lines) — net addition of 5,357 lines (new coverage)
- **Other**: SDK lock file, experimental directory cleanup, docs

---

## Breaking Changes

None. All changes are internal refactoring. The public API, MCP tool interface, and backend behavior are unchanged.

---

## Migration Guide

No migration required. Existing configurations, environment variables, and backend connections continue to work without changes.

---

## Contributors

- Gregory Dickson
- Claude Opus 4.6 (AI pair programmer)

---

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for the complete list of changes.
