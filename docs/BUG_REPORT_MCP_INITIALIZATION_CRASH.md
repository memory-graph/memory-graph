# Bug Report: MCP Server Initialization Crash

**Status**: 🔴 CRITICAL - Server fails to start
**Severity**: HIGH - Blocks all MCP server functionality
**Component**: `src/memorygraph/server.py`
**Affected Version**: 1.0.0
**Date Reported**: 2025-12-01
**Reporter**: Automated system diagnostic

---

## Executive Summary

The memorygraph MCP server crashes immediately on startup with an `AttributeError` in the `main()` function when calling `server.server.get_capabilities()`. The server attempts to pass a `NotificationOptions()` object, but the `get_capabilities()` method receives `None` for the `notification_options` parameter, causing an attribute access error.

---

## Error Details

### Primary Error
```
AttributeError: 'NoneType' object has no attribute 'tools_changed'
```

### Full Stack Trace
```python
ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
+-+---------------- 1 ----------------
  | Traceback (most recent call last):
  |   File "/venv/lib/python3.12/site-packages/mcp/server/stdio.py", line 88, in stdio_server
  |     yield read_stream, write_stream
  |   File "/venv/lib/python3.12/site-packages/memorygraph/server.py", line 853, in main
  |     capabilities=server.server.get_capabilities(
  |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "/venv/lib/python3.12/site-packages/mcp/server/lowlevel/server.py", line 212, in get_capabilities
  |     tools_capability = types.ToolsCapability(listChanged=notification_options.tools_changed)
  |                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  | AttributeError: 'NoneType' object has no attribute 'tools_changed'
  +------------------------------------
```

### Error Location
- **File**: `src/memorygraph/server.py`
- **Line**: 999-1002 (in `main()` function)
- **Function**: `main()`

---

## Reproduction Steps

### Prerequisites
```bash
# Environment
Python: 3.12.8
mcp: 1.22.0
memorygraphMCP: 0.5.0
OS: macOS (Darwin 23.6.0)
```

### Steps to Reproduce
```bash
# 1. Install memorygraph
pip install memorygraph

# 2. Attempt to start the server
memorygraph

# 3. Observe crash with AttributeError
```

### Expected Behavior
Server should initialize successfully and listen for MCP requests on stdio.

### Actual Behavior
Server crashes immediately with `AttributeError: 'NoneType' object has no attribute 'tools_changed'`

---

## Root Cause Analysis

### Problem Code (server.py:983-1013)

```python
async def main():
    """Main entry point for the MCP server."""
    server = ClaudeMemoryServer()

    try:
        # Initialize the server
        await server.initialize()

        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-memory",
                    server_version=__version__,
                    capabilities=server.server.get_capabilities(
                        notification_options=NotificationOptions(),  # ⚠️ ISSUE HERE
                        experimental_capabilities={},
                    ),
                ),
            )

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.cleanup()
```

### Analysis

**What's happening:**
1. Code creates `NotificationOptions()` instance at line 1000
2. Passes it to `server.server.get_capabilities(notification_options=NotificationOptions(), ...)`
3. Inside `get_capabilities()`, the parameter `notification_options` is `None` (not the passed object)
4. Code tries to access `notification_options.tools_changed` → crashes

**Why notification_options is None:**
This is likely due to one of these issues:
1. **Scope issue**: The `NotificationOptions()` object is being garbage collected before use
2. **MCP library incompatibility**: The `mcp` library version 1.22.0 may have changed how `get_capabilities()` works
3. **Threading/async issue**: The object is not properly passed through async contexts
4. **Import issue**: Wrong `NotificationOptions` class being imported

### MCP Library Signature (v1.22.0)

```python
def get_capabilities(
    self,
    notification_options: NotificationOptions,  # ← Required, not optional
    experimental_capabilities: dict[str, dict[str, Any]],
) -> types.ServerCapabilities:
    """Convert existing handlers to a ServerCapabilities object."""
    # ...
    tools_capability = types.ToolsCapability(
        listChanged=notification_options.tools_changed  # ← Crashes here if None
    )
```

The method signature shows `notification_options` is **required** (not Optional), so passing `None` is invalid.

---

## Investigation Steps for Coding Agent

### Step 1: Verify Import
```python
# File: src/memorygraph/server.py, line 15
from mcp.server import Server, NotificationOptions

# ✅ TODO: Confirm NotificationOptions is the correct class
# Check if there's a different NotificationOptions in mcp.types or mcp.server.models
```

### Step 2: Check MCP Library Version Compatibility
```bash
# Current version
pip show mcp  # 1.22.0

# ✅ TODO: Check if version 1.22.0 changed NotificationOptions initialization
# Compare with earlier versions or check changelog
```

### Step 3: Inspect NotificationOptions Initialization
```python
# ✅ TODO: Add debug logging to understand what's happening
from mcp.server import NotificationOptions
import logging

logger.info(f"NotificationOptions class: {NotificationOptions}")
options = NotificationOptions()
logger.info(f"Created options: {options}")
logger.info(f"Options type: {type(options)}")
logger.info(f"Options dict: {vars(options) if hasattr(options, '__dict__') else 'N/A'}")
```

### Step 4: Check for Alternative Initialization Patterns
```python
# ✅ TODO: Try different initialization approaches

# Option 1: Explicit parameters
notification_options=NotificationOptions(
    prompts_changed=False,
    resources_changed=False,
    tools_changed=False
)

# Option 2: Use Server's default
# Some MCP server implementations don't pass capabilities at initialization
# Let Server.run() handle capability negotiation

# Option 3: Check if InitializationOptions should NOT include capabilities
InitializationOptions(
    server_name="claude-memory",
    server_version=__version__,
    # capabilities=... ← Maybe remove this?
)
```

---

## Proposed Solutions

### Solution 1: Remove Capabilities from InitializationOptions (RECOMMENDED)

**Hypothesis**: Modern MCP protocol may handle capability negotiation after initialization, not during.

**Implementation**:
```python
# File: src/memorygraph/server.py
# Line: 993-1004

async def main():
    """Main entry point for the MCP server."""
    server = ClaudeMemoryServer()

    try:
        await server.initialize()

        async with stdio_server() as (read_stream, write_stream):
            # CHANGE: Remove capabilities from InitializationOptions
            await server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-memory",
                    server_version=__version__,
                    # ✅ REMOVED: capabilities parameter
                ),
            )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.cleanup()
```

**Rationale**:
- MCP protocol version 1.22.0 may have changed initialization flow
- Capabilities might be auto-registered when handlers are added
- Server.run() may handle capability negotiation internally

**Risk**: LOW - If this doesn't work, the error message will be clear

---

### Solution 2: Explicit NotificationOptions Initialization

**Implementation**:
```python
# File: src/memorygraph/server.py
# Line: 993-1004

async def main():
    """Main entry point for the MCP server."""
    server = ClaudeMemoryServer()

    try:
        await server.initialize()

        async with stdio_server() as (read_stream, write_stream):
            # CHANGE: Create NotificationOptions with explicit values
            notification_opts = NotificationOptions(
                prompts_changed=True,
                resources_changed=True,
                tools_changed=True
            )

            await server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-memory",
                    server_version=__version__,
                    capabilities=server.server.get_capabilities(
                        notification_options=notification_opts,
                        experimental_capabilities={},
                    ),
                ),
            )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.cleanup()
```

**Risk**: MEDIUM - Requires understanding NotificationOptions schema

---

### Solution 3: Downgrade MCP Library (TEMPORARY WORKAROUND)

**Implementation**:
```bash
# Find last known working version
pip install mcp==1.0.0  # or other stable version

# Update requirements.txt
mcp>=1.0.0,<1.22.0
```

**Risk**: HIGH - May lose new features or security fixes

---

## Testing Instructions

### Test 1: Verify Server Starts
```bash
# After applying fix
cd ~/claude-code-memory
source .venv/bin/activate
memorygraph

# Expected output:
# ✅ "Starting MemoryGraph MCP Server v1.0.0"
# ✅ "Backend: sqlite"
# ✅ No crashes
```

### Test 2: Verify MCP Connection
```bash
# From another terminal
claude mcp list

# Expected output:
# ✅ memorygraph: memorygraph - ✓ Connected
```

### Test 3: Verify Tool Registration
```bash
# After server starts, send MCP request
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | memorygraph

# Expected: JSON response with list of tools (no crash)
```

### Test 4: Integration Test
```bash
# Run pytest suite
cd ~/claude-code-memory
pytest tests/test_server.py -v -k "test_server_initialization"
```

---

## Related Files

### Primary
- `src/memorygraph/server.py` (lines 983-1013) - Main function with bug
- `src/memorygraph/server.py` (lines 1-50) - Imports

### Secondary
- `pyproject.toml` - MCP version specification
- `requirements.txt` - Dependency versions
- `src/memorygraph/__init__.py` - Version definition

### Test Files
- `tests/test_server.py` - Server initialization tests
- `tests/test_server_init.py` - Initialization tests
- `tests/test_server_main_initialization.py` - Main function tests

---

## Acceptance Criteria

**Fix is complete when:**
- ✅ Server starts without crashing
- ✅ No `AttributeError` in logs
- ✅ MCP connection succeeds (`claude mcp list` shows Connected)
- ✅ All existing tests pass
- ✅ Can create and retrieve memories via MCP tools

---

## Additional Context

### Environment Details
```
OS: macOS Darwin 23.6.0
Python: 3.12.8
mcp: 1.22.0
memorygraphMCP: 0.5.0
Installation: pip (virtualenv)
Working Directory: /Users/gregorydickson/claude-code-memory
```

### MCP Configuration (User Scope)
```json
{
  "memorygraph": {
    "type": "stdio",
    "command": "memorygraph",
    "args": [],
    "env": {}
  }
}
```

### Server Log Output (Full)
```
2025-12-01 07:14:50,955 - memorygraph.server - INFO - Tool profile: LITE - 8/44 tools enabled
2025-12-01 07:14:50,955 - memorygraph.backends.factory - INFO - Explicit backend selection: SQLite
2025-12-01 07:14:51,042 - memorygraph.backends.sqlite_fallback - INFO - Successfully connected to SQLite database at /Users/gregorydickson/.memorygraph/memory.db
2025-12-01 07:14:51,042 - memorygraph.database - INFO - Initializing Neo4j schema for Claude Memory...
2025-12-01 07:14:51,042 - memorygraph.database - INFO - Schema initialization completed
2025-12-01 07:14:51,042 - memorygraph.server - INFO - Claude Memory Server initialized successfully
2025-12-01 07:14:51,042 - memorygraph.server - INFO - Backend: <bound method SQLiteFallbackBackend.backend_name of <memorygraph.backends.sqlite_fallback.SQLiteFallbackBackend object at 0x103ab3800>>
2025-12-01 07:14:51,042 - memorygraph.server - INFO - Tool profile: LITE (8 tools enabled)
2025-12-01 07:14:51,044 - memorygraph.server - ERROR - Server error: unhandled errors in a TaskGroup (1 sub-exception)
2025-12-01 07:14:51,044 - memorygraph.backends.sqlite_fallback - INFO - SQLite connection closed
2025-12-01 07:14:51,044 - memorygraph.server - INFO - Claude Memory Server cleanup completed
```

**Note**: Server initializes successfully (tools registered, database connected) but crashes during MCP protocol initialization.

---

## Priority & Impact

**Priority**: P0 (Critical)
**Impact**: Complete feature blockage - MCP server unusable
**Users Affected**: All users attempting to use memorygraph as MCP server
**Workaround Available**: No (server cannot start)

---

## Next Actions for Coding Agent

1. **Immediate**: Try Solution 1 (remove capabilities from InitializationOptions)
2. **If Solution 1 fails**: Try Solution 2 (explicit NotificationOptions)
3. **Debug**: Add logging to understand NotificationOptions state
4. **Research**: Check MCP 1.22.0 changelog for breaking changes
5. **Test**: Run full test suite after fix
6. **Document**: Update CHANGELOG.md with fix details

---

## References

- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP Specification: https://spec.modelcontextprotocol.io/
- Issue Tracker: (Create GitHub issue if not already exists)

---

**END OF REPORT**
