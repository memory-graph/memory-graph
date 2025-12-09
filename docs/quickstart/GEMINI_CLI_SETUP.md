# MemoryGraph Setup for Gemini CLI

Get persistent memory working with Google's Gemini CLI.

## Prerequisites

- **Gemini CLI** installed ([Installation Guide](https://github.com/google-gemini/gemini-cli))
- **Google AI API key** or Google Cloud credentials
- Python 3.10+
- pipx installed (`pip install --user pipx && pipx ensurepath`)

## Choose Your Backend

MemoryGraph supports two backend options:

| Feature | Local (SQLite) | Cloud |
|---------|---------------|-------|
| **Setup** | Zero-config | API key required |
| **Data Location** | `~/.memorygraph/` | memorygraph.dev |
| **Multi-device** | No | Yes |
| **Team sharing** | No | Yes |
| **Offline** | Yes | No |
| **Cost** | Free | Free tier available |

**New users**: We recommend starting with **Cloud** for multi-device sync, or **Local** for single-machine use.

---

## Quick Start (Local Backend)

### 1. Install MemoryGraph

```bash
pipx install memorygraphMCP
```

Verify installation:
```bash
memorygraph --version
```

### 2. Configure Gemini CLI

Gemini CLI supports MCP servers via configuration file.

**Create or edit** `~/.gemini/config.json`:

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

### 3. Verify Setup

Start Gemini CLI and check for MCP tools:

```bash
gemini
```

Then ask:

```
What MCP tools do you have available?
```

## First Memory

Store a memory:

```
Store this for later: The main database is PostgreSQL on port 5432
```

Retrieve it:

```
What database does this project use?
```

---

## Quick Start (Cloud Backend)

Cloud backend syncs memories across all your devices and enables team collaboration.

### 1. Get Your API Key

1. Sign up at [app.memorygraph.dev](https://app.memorygraph.dev)
2. Copy your API key (starts with `mg_`)

### 2. Install MemoryGraph

```bash
pipx install memorygraphMCP
```

### 3. Configure Gemini CLI with Cloud Backend

Edit `~/.gemini/config.json`:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "cloud"],
      "env": {
        "MEMORYGRAPH_API_KEY": "mg_your_api_key_here"
      }
    }
  }
}
```

### 4. Verify Setup

Start Gemini CLI and ask about available memory tools.

---

## Migrating from Local to Cloud

Already using local SQLite and want to switch to cloud?

### Step 1: Export Local Memories

```bash
memorygraph export --output memories-backup.json
```

### Step 2: Import to Cloud

```bash
export MEMORYGRAPH_API_KEY=mg_your_key_here
memorygraph import --backend cloud --input memories-backup.json
```

### Step 3: Update Gemini CLI Configuration

Update `~/.gemini/config.json`:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--backend", "cloud"],
      "env": {
        "MEMORYGRAPH_API_KEY": "mg_your_api_key_here"
      }
    }
  }
}
```

### Step 4: Restart Gemini CLI

Restart to apply the new configuration.

See [CLOUD_BACKEND.md](../CLOUD_BACKEND.md) for detailed migration options.

---

## Configuration Options

### Extended Mode (More Tools)

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended"]
    }
  }
}
```

### Custom Database Path

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "env": {
        "MEMORY_SQLITE_PATH": "/path/to/memory.db"
      }
    }
  }
}
```

### Full Path (Recommended)

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

Find your path: `which memorygraph`

## Troubleshooting

### MCP Server Not Loading

1. **Check Gemini CLI version** - Ensure you have MCP support
2. **Verify config location**: `~/.gemini/config.json`
3. **Check JSON syntax** - Use a JSON validator

### Command Not Found

```bash
# Check if memorygraph is installed
which memorygraph

# If not found
pipx ensurepath
# Restart terminal
```

### Test Server Manually

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}' | memorygraph
```

### View Logs

Check Gemini CLI output for MCP-related errors:

```bash
gemini --verbose
```

## Tips for Gemini CLI Users

1. **Leverage the 1M context window** - Gemini can process large codebases
2. **Store key insights** - Remember important findings from large file analysis
3. **Track patterns** - Use memory to build up project knowledge
4. **Query before analysis** - Check what you already know about a topic

## Recommended: Memory Protocol

Add this to `GEMINI.md` or your project's instructions file for automatic memory usage:

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
- **Project-specific**: `GEMINI.md` in project root
- **Global**: `~/.gemini/instructions.md`

## Gemini-Specific Use Cases

Gemini CLI's large context window pairs well with MemoryGraph:

### Large Codebase Analysis

```
Analyze all the files in src/ and store key architectural patterns you find
```

### Cross-File Patterns

```
Search the codebase for authentication patterns and remember what you find
```

### Incremental Learning

```
What have we learned about this codebase so far?
```

## Combining with Gemini's Strengths

| Gemini Strength | MemoryGraph Enhancement |
|-----------------|------------------------|
| 1M token context | Store insights from large analyses |
| Fast inference | Quick memory queries |
| Code understanding | Persist code patterns |
| Multi-modal | Store context about diagrams/images discussed |

## Configuration File Location

Default location: `~/.gemini/config.json`

Alternative locations may be supported - check Gemini CLI documentation for your version.

## Limitations

- MCP support in Gemini CLI may vary by version
- Check Google's documentation for current MCP capabilities
- Some features may require specific Gemini API tiers

## Next Steps

- [Full Configuration Reference](../CONFIGURATION.md)
- [All Tool Profiles](../TOOL_PROFILES.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)
- [Gemini CLI Documentation](https://github.com/google-gemini/gemini-cli)

---

**Works with**: Gemini CLI (with MCP support)
**Transport**: stdio
**Profiles**: core (9 tools), extended (11 tools)
**Note**: MCP support may vary by Gemini CLI version
