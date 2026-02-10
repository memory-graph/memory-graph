# Test Results: WP33 Remaining Backend Config Migration (RED Phase)

## Summary

Successfully completed RED phase (failing tests) for WP33 (Config as Single Source of Truth).

**Test File:** `/Users/gregorydickson/memory-graph/tests/test_remaining_backend_config.py`

**Test Results:**
- 14 FAILED (expected - RED phase)
- 10 PASSED (constructor overrides and defaults work correctly)
- 3 SKIPPED (LadybugDB not installed)

## Failing Tests (Expected - RED Phase)

These tests SHOULD FAIL because backends currently read from `os.getenv()` directly:

### FalkorDBBackend (3 failing tests)
- `test_falkordb_reads_host_from_config_not_env` - Currently reads from `os.getenv("FALKORDB_HOST")`
- `test_falkordb_reads_port_from_config_not_env` - Currently reads from `os.getenv("FALKORDB_PORT")`
- `test_falkordb_reads_password_from_config_not_env` - Currently reads from `os.getenv("FALKORDB_PASSWORD")`

**File:** `src/memorygraph/backends/falkordb_backend.py` lines 54-56

### FalkorDBLiteBackend (1 failing test)
- `test_falkordblite_reads_path_from_config_not_env` - Currently reads from `os.getenv("FALKORDBLITE_PATH")`

**File:** `src/memorygraph/backends/falkordblite_backend.py` line 53

### CloudRESTAdapter (5 failing tests)
- `test_cloud_reads_api_key_from_config_not_env` - Currently reads from `os.getenv("MEMORYGRAPH_API_KEY")`
- `test_cloud_reads_api_url_from_config_not_env` - Currently reads from `os.getenv("MEMORYGRAPH_API_URL")`
- `test_cloud_reads_timeout_from_config_not_env` - Currently reads from `os.getenv("MEMORYGRAPH_TIMEOUT")`
- `test_cloud_uses_default_url_when_config_is_none` - Config lookup not implemented
- `test_cloud_uses_default_timeout_when_config_is_none` - Config lookup not implemented

**File:** `src/memorygraph/backends/cloud_backend.py` lines 170-176

### Neo4jConnection (5 failing tests)
- `test_neo4j_reads_uri_from_config_not_env` - Currently reads from `os.getenv("NEO4J_URI")`
- `test_neo4j_reads_user_from_config_not_env` - Currently reads from `os.getenv("NEO4J_USER")`
- `test_neo4j_reads_password_from_config_not_env` - Currently reads from `os.getenv("NEO4J_PASSWORD")`
- `test_neo4j_uses_default_uri_when_config_is_none` - Config lookup not implemented
- `test_neo4j_uses_default_user_when_config_is_none` - Config lookup not implemented

**File:** `src/memorygraph/database.py` lines 52-54

## Passing Tests (Expected)

These tests pass because the backends properly handle constructor parameters and defaults:

- `test_falkordb_uses_default_when_config_is_none` - Default values work correctly
- `test_falkordb_constructor_params_override_config` - Constructor params override Config
- `test_falkordblite_uses_default_when_config_is_none` - Default path works correctly
- `test_falkordblite_constructor_param_overrides_config` - Constructor param overrides Config
- `test_cloud_constructor_params_override_config` - Constructor params override Config
- `test_cloud_raises_error_when_api_key_missing` - Error handling works correctly
- `test_neo4j_constructor_params_override_config` - Constructor params override Config
- `test_neo4j_raises_error_when_password_missing` - Error handling works correctly
- `test_patch_config_restores_original_values` - Helper function works correctly
- `test_multiple_patch_config_contexts_are_isolated` - Helper function isolation works

## Test Pattern

The tests use the shared `patch_config()` context manager from `tests/_helpers.py` to temporarily override Config class attributes:

```python
from tests._helpers import patch_config
```

### Test Structure

Each test:
1. Sets a value in Config (e.g., `Config.FALKORDB_HOST = "config-host"`)
2. Sets a DIFFERENT value in os.environ (e.g., `os.environ["FALKORDB_HOST"] = "env-host"`)
3. Creates the backend instance
4. Asserts it uses the CONFIG value, not the environment variable value

Example:
```python
def test_falkordb_reads_host_from_config_not_env(self):
    """FalkorDBBackend should read host from Config.FALKORDB_HOST, not os.environ."""
    with patch_config(FALKORDB_HOST="config-host"):
        os.environ["FALKORDB_HOST"] = "env-host"
        try:
            backend = FalkorDBBackend()
            assert backend.host == "config-host", \
                "Should use Config.FALKORDB_HOST, not os.environ"
        finally:
            os.environ.pop("FALKORDB_HOST", None)
```

## Implementation Requirements

To make these tests pass (GREEN phase), each backend needs to change from:

```python
# CURRENT (reads from os.environ directly)
self.host = host or os.getenv("FALKORDB_HOST", "localhost")
```

To:

```python
# REQUIRED (reads from Config)
from ..config import Config

self.host = host or Config.FALKORDB_HOST or "localhost"
```

## Files to Modify

1. `src/memorygraph/backends/falkordb_backend.py` - Lines 54-56
2. `src/memorygraph/backends/falkordblite_backend.py` - Line 53
3. `src/memorygraph/backends/ladybugdb_backend.py` - Line 63
4. `src/memorygraph/backends/cloud_backend.py` - Lines 170-176
5. `src/memorygraph/database.py` - Lines 52-54

## Config Values Available

From `src/memorygraph/config.py`:

```python
# FalkorDB
Config.FALKORDB_HOST: Optional[str]
Config.FALKORDB_PORT: Optional[int]
Config.FALKORDB_PASSWORD: Optional[str]

# FalkorDBLite
Config.FALKORDBLITE_PATH: Optional[str]

# LadybugDB
Config.LADYBUGDB_PATH: Optional[str]

# Cloud
Config.MEMORYGRAPH_API_KEY: Optional[str]
Config.MEMORYGRAPH_API_URL: str
Config.MEMORYGRAPH_TIMEOUT: int

# Neo4j
Config.NEO4J_URI: str
Config.NEO4J_USER: str
Config.NEO4J_PASSWORD: Optional[str]
```

## Next Steps (GREEN Phase)

Hand off to `implement` agent to:
1. Update each backend file to read from Config instead of os.getenv()
2. Maintain backward compatibility (constructor parameters override Config)
3. Maintain default values when Config is None
4. Run tests to verify they all pass (GREEN phase)

## TDD Status

✅ **RED Phase Complete** - Tests fail as expected (14 failing tests)
⏳ **GREEN Phase** - Awaiting implementation
⏳ **REFACTOR Phase** - After GREEN phase passes
