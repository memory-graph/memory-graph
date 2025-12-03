# MemoryGraph Setup for Claude Desktop

Get persistent memory working in Claude Desktop in under 2 minutes.

## Prerequisites

- Claude Desktop app (latest version)
- Python 3.10+
- pipx installed (`pip install --user pipx && pipx ensurepath`)

## Quick Start

### 1. Install MemoryGraph

```bash
pipx install memorygraphMCP
```

Verify installation:
```bash
memorygraph --version
```

### 2. Choose Your Installation Method

**IMPORTANT**: Claude Desktop has a limited PATH that only includes system directories like `/usr/local/bin`. You have two options:

#### Option A: Use Full Path (Recommended - No sudo required)

Find where memorygraph is installed:
```bash
which memorygraph
```

This typically returns:
- macOS/Linux: `/Users/yourname/.local/bin/memorygraph`
- If using pip: `/Users/yourname/Library/Python/3.x/bin/memorygraph`

**Copy this full path** - you'll need it in step 3.

#### Option B: Create Symlink (Cleaner config - Requires sudo once)

Create a symlink to make memorygraph available in a system directory:

```bash
sudo ln -s ~/.local/bin/memorygraph /usr/local/bin/memorygraph
```

This allows you to use just `memorygraph` instead of the full path in your config.

**Verify the symlink works**:
```bash
/usr/local/bin/memorygraph --version
```

### 3. Configure Claude Desktop

Open Claude Desktop's configuration file:

**macOS**:
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux**:
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Add or update the file with your memorygraph command:

**If using Option A (full path)**:
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/yourname/.local/bin/memorygraph",
      "args": []
    }
  }
}
```
Replace `/Users/yourname/.local/bin/memorygraph` with your actual path from step 2.

**If using Option B (symlink)**:
```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": []
    }
  }
}
```

### 4. Restart Claude Desktop

Completely quit and restart Claude Desktop (not just close the window).

### 5. Verify Connection

In a new conversation, ask:

```
What memory tools do you have available?
```

You should see MemoryGraph tools like `store_memory`, `recall_memories`, `search_memories`, etc.

## First Memory

Try storing your first memory:

```
Store this for later: This project uses TypeScript with strict mode enabled
```

Then retrieve it:

```
What do you know about this project's TypeScript setup?
```

## Configuration Options

### Extended Mode (Pattern Recognition)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/yourname/.local/bin/memorygraph",
      "args": ["--profile", "extended"]
    }
  }
}
```

Adds pattern recognition and 11 total tools.

### Custom Database Location

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/yourname/.local/bin/memorygraph",
      "args": [],
      "env": {
        "MEMORY_SQLITE_PATH": "/path/to/your/memory.db"
      }
    }
  }
}
```

### Extended Mode with Neo4j

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/yourname/.local/bin/memorygraph",
      "args": ["--profile", "extended", "--backend", "neo4j"],
      "env": {
        "MEMORY_NEO4J_URI": "bolt://localhost:7687",
        "MEMORY_NEO4J_USER": "neo4j",
        "MEMORY_NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
```

## Troubleshooting

### "spawn memorygraph ENOENT" Error

This is the most common error and means Claude Desktop cannot find the memorygraph command.

**Solution 1: Use the FULL PATH** (recommended, no sudo required)

```bash
# Find your path
which memorygraph

# Use the full path in config
{
  "command": "/Users/yourname/.local/bin/memorygraph"  # Use full path
}
```

**Solution 2: Create a symlink** (cleaner config, requires sudo once)

```bash
# Create symlink to system directory
sudo ln -s ~/.local/bin/memorygraph /usr/local/bin/memorygraph

# Now you can use just "memorygraph" in config
{
  "command": "memorygraph"
}
```

### Why PATH Issues Occur

Claude Desktop runs with a restricted PATH that only includes:
- `/usr/local/bin`
- `/opt/homebrew/bin`
- `/usr/bin`
- `/bin`
- `/usr/sbin`
- `/sbin`

The `~/.local/bin` directory (where pipx installs commands) is NOT in this PATH.

**This is why you must use the full path.**

### Server Not Connecting

1. **Verify memorygraph is installed**:
   ```bash
   which memorygraph
   memorygraph --version
   ```

2. **Check your config file has correct JSON syntax**:
   ```bash
   # On macOS
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

   # Validate JSON syntax at https://jsonlint.com
   ```

3. **Ensure you're using the absolute path**:
   ```json
   {
     "command": "/Users/yourname/.local/bin/memorygraph"  # ✅ Absolute path
   }
   ```

   Not:
   ```json
   {
     "command": "memorygraph"  # ❌ Will fail
   }
   ```

4. **Restart Claude Desktop completely**:
   - Quit Claude Desktop (Cmd+Q on macOS, not just close window)
   - Wait a few seconds
   - Reopen Claude Desktop

### Tools Not Appearing

1. **Check Claude Desktop logs** (macOS):
   ```bash
   # View logs
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

2. **Test server manually**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | /Users/yourname/.local/bin/memorygraph
   ```

   Replace with your actual path. You should see a JSON response.

3. **Verify config file location**:
   ```bash
   # macOS - should exist
   ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

### Permission Issues

On macOS, you may need to grant Claude Desktop permissions:

1. System Settings > Privacy & Security > Full Disk Access
2. Add Claude Desktop to the list
3. Restart Claude Desktop

### Still Not Working?

1. **Try reinstalling**:
   ```bash
   pipx uninstall memorygraphMCP
   pipx install memorygraphMCP
   which memorygraph  # Note the path
   ```

2. **Check Python version**:
   ```bash
   python3 --version  # Must be 3.10+
   ```

3. **Use debug mode**:
   ```json
   {
     "mcpServers": {
       "memorygraph": {
         "command": "/Users/yourname/.local/bin/memorygraph",
         "args": ["--log-level", "DEBUG"],
         "env": {
           "MEMORY_LOG_LEVEL": "DEBUG"
         }
       }
     }
   }
   ```

## Tips for Claude Desktop Users

1. **Use full paths always** - Claude Desktop's PATH is restricted
2. **Restart after config changes** - Changes require full restart
3. **Store context between sessions** - Build up project knowledge
4. **Query before starting** - Check if you've solved similar problems
5. **Save successful patterns** - Remember what works

## Recommended: Memory Protocol

Add this to your global CLAUDE.md for automatic memory usage. On macOS, create or edit:

```bash
nano ~/.claude/CLAUDE.md
```

Add this content:

```markdown
## Memory Protocol

### REQUIRED: Before Starting Work
You MUST use `recall_memories` before any task. Query by project, tech, or task type.

### REQUIRED: Automatic Storage Triggers
Store memories on ANY of:
- **Git commit** → what was fixed/added
- **Bug fix** → problem + solution
- **Version release** → summarize changes
- **Architecture decision** → choice + rationale
- **Pattern discovered** → reusable approach

### Timing Mode (default: on-commit)
`memory_mode: immediate | on-commit | session-end`

### Memory Fields
- **Type**: solution | problem | code_pattern | fix | error | workflow
- **Title**: Specific, searchable (not generic)
- **Content**: Accomplishment, decisions, patterns
- **Tags**: project, tech, category (REQUIRED)
- **Importance**: 0.8+ critical, 0.5-0.7 standard, 0.3-0.4 minor
- **Relationships**: Link related memories when they exist

Do NOT wait to be asked. Memory storage is automatic.
```

**File locations:**
- **Global**: `~/.claude/CLAUDE.md`
- **Project-specific**: `.claude/CLAUDE.md` in project root

## Configuration File Locations

For reference, Claude Desktop stores its configuration at:

**macOS**:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux**:
```
~/.config/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

## Example Full Configuration

Here's a complete working example (macOS):

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "/Users/john/.local/bin/memorygraph",
      "args": ["--profile", "extended"],
      "env": {
        "MEMORY_SQLITE_PATH": "/Users/john/.memorygraph/memory.db",
        "MEMORY_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Remember to:
1. Replace `/Users/john` with your actual home directory path
2. Use the path from `which memorygraph`
3. Ensure valid JSON syntax (commas, quotes, braces)

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [Claude Desktop Documentation](https://claude.ai/desktop)

---

**Works with**: Claude Desktop (macOS, Linux, Windows)
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
**Key Requirement**: Must use absolute path to memorygraph executable
