# Troubleshooting Guide

Solutions for common MemoryGraph issues.

## Quick Diagnostics

```bash
# Check installation
which memorygraph
memorygraph --version

# Verify configuration
memorygraph --show-config

# Run health check (v0.9.0+)
memorygraph --health

# Health check with JSON output for scripting
memorygraph --health --health-json

# Check MCP status in Claude Code
claude mcp list
```

### Understanding Health Check Output

The health check command provides comprehensive diagnostics:

```bash
memorygraph --health
```

**Output**:
- **Status**: ✅ Healthy or ❌ Unhealthy
- **Backend**: Type of backend (sqlite, neo4j, etc.)
- **Connected**: Whether the backend is accessible
- **Version**: Backend version (if available)
- **Statistics**: Memory count and other metrics
- **Database Size**: Size of the database file (SQLite)
- **Error**: Detailed error message if unhealthy

**Exit codes**:
- `0` - Healthy (backend connected and operational)
- `1` - Unhealthy (connection failed or error detected)

**Common health check failures**:
```bash
# Timeout (backend not responding)
Error: Health check timed out after 5.0 seconds
# Solution: Check if backend is running, increase timeout with --health-timeout 10.0

# Connection refused (backend not accessible)
Error: Connection refused
# Solution: Verify backend is running and credentials are correct

# Database locked (SQLite)
Error: database is locked
# Solution: Close other connections or kill stale processes
```

## Common Issues

### Command not found: memorygraph

```bash
# If using pipx
pipx ensurepath
# Then restart your terminal

# If using pip, check if Python bin is in PATH
python3 -m pip show memorygraphMCP | grep Location

# Find the executable
python3 -c "import shutil; print(shutil.which('memorygraph') or 'Not in PATH')"

# Option 1: Add to PATH (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Option 2: Add to PATH (zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Option 3: Use full path in MCP config (recommended for Claude Desktop)
claude mcp add --transport stdio memorygraph -- /full/path/to/memorygraph

# Option 4: Create symlink for system-wide access (requires sudo)
sudo ln -s ~/.local/bin/memorygraph /usr/local/bin/memorygraph
# Then use simple command
claude mcp add memorygraph -- memorygraph
```

### MCP Server Connection Failed

If `claude mcp list` shows "Failed to connect":

```bash
# 1. Test the MCP server manually
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph

# 2. If you see "AttributeError: 'NoneType' object..."
# You have an old version. Upgrade:
pipx upgrade memorygraphMCP

# 3. Check which version is being used
which memorygraph
memorygraph --version

# 4. Verify pipx installation
pipx list | grep -A 3 memorygraph
```

### Multiple Installation Conflict

When global upgrade doesn't take effect:

```bash
# Problem: Project venv has old cached version

# Check project venv version
pip show memorygraphMCP

# Solution 1: Update project installation
cd ~/your-project
pip uninstall -y memorygraphMCP
pip install -e .

# Solution 2: Use full path in MCP config (recommended)
# Find your pipx path:
which memorygraph  # outside any venv

# Update MCP config to use full path:
# "command": "/Users/yourname/.local/bin/memorygraph"
```

### Server won't start

```bash
# Check configuration
memorygraph --show-config

# Enable debug logging
MEMORY_LOG_LEVEL=DEBUG memorygraph

# Verify database connection
memorygraph --health
```

### SQLite database locked

```bash
# Check for running processes
ps aux | grep memorygraph

# Kill stale processes
pkill -f memorygraph

# Remove lock file if safe
rm ~/.memorygraph/memory.db-lock

# Restart Claude Code
```

### Neo4j connection refused

```bash
# Verify Neo4j is running
docker ps | grep neo4j

# Test connection manually
cypher-shell -a bolt://localhost:7687 -u neo4j -p your-password

# Check credentials
memorygraph --backend neo4j --show-config

# Check Neo4j logs
docker logs neo4j-container
```

### Memgraph connection issues

```bash
# Verify Memgraph is running
docker ps | grep memgraph

# Test connection
mgconsole --host 127.0.0.1 --port 7687

# Check Memgraph logs
docker logs memgraph-container
```

### FalkorDBLite issues

**libomp error on macOS**:
```bash
# Error: Library not loaded: libomp.dylib
brew install libomp

# Restart your terminal after installation
```

**Database file permissions**:
```bash
# Check permissions
ls -la ~/.memorygraph/falkordblite.db

# Fix permissions if needed
chmod 644 ~/.memorygraph/falkordblite.db
```

**Import error**:
```bash
# Install FalkorDBLite
pip install "memorygraphMCP[falkordblite]"

# Verify installation
python -c "import falkordblite; print('FalkorDBLite installed')"
```

### FalkorDB connection issues

**Connection refused**:
```bash
# Verify FalkorDB is running
docker ps | grep falkordb

# Check if port is accessible
nc -zv localhost 6379

# Check FalkorDB logs
docker logs falkordb

# Restart FalkorDB if needed
docker restart falkordb
```

**Wrong host/port**:
```bash
# Verify configuration
memorygraph --show-config | grep FALKORDB

# Test connection manually
redis-cli -h localhost -p 6379 ping
```

**Import error**:
```bash
# Install FalkorDB client
pip install "memorygraphMCP[falkordb]"

# Verify installation
python -c "import falkordb; print('FalkorDB client installed')"
```

### Import/Export issues

```bash
# Export memories to backup
memorygraph --export backup.json

# Import to new backend
memorygraph --backend neo4j --import backup.json

# Verify import
memorygraph --backend neo4j --show-config
```

## Cycle Detection Errors

### Error: "Cannot create relationship ... Would create a cycle"

**Cause**: You're trying to create a circular relationship chain (e.g., A → B → C → A). By default, MemoryGraph prevents cycles to avoid infinite loops during relationship traversal.

**Solutions**:

1. **Review your relationship chain**: Check if the cycle is intentional or a mistake
   ```
   # Example cycle: memory_1 → memory_2 → memory_3 → memory_1
   # This would be blocked
   ```

2. **Use a different relationship type**: Some relationship types may not imply ordering
   ```python
   # Instead of: A CAUSES B, B CAUSES C, C CAUSES A (cycle)
   # Consider: A RELATED_TO B, B RELATED_TO C, C RELATED_TO A
   ```

3. **Enable cycles** (use with caution):
   ```bash
   export MEMORY_ALLOW_CYCLES=true
   ```
   Warning: Enabling cycles may cause infinite loops in `get_related_memories()` with high depth values.

**Configuration**: Set `MEMORY_ALLOW_CYCLES=true` environment variable to allow circular relationships.

## MCP Configuration Issues

### Server appears in list but tools don't work

1. Check that server shows "Connected" in `claude mcp list`
2. Restart Claude Code completely (exit and restart)
3. Check for permission issues in settings

### Tools not appearing

```bash
# Verify profile setting
memorygraph --show-config | grep profile

# Core mode: 9 tools
# Extended mode: 11 tools
# Extended mode: 11 tools
```

## Getting Help

1. **Check logs**: `MEMORY_LOG_LEVEL=DEBUG memorygraph`
2. **Verify config**: `memorygraph --show-config`
3. **GitHub Issues**: [Report bugs](https://github.com/gregorydickson/memorygraph/issues)
4. **Discussions**: [Ask questions](https://github.com/gregorydickson/memorygraph/discussions)
