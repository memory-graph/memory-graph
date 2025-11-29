# Development Setup Guide

This guide helps you set up MemoryGraph for development.

## Prerequisites

- Python 3.10 or higher
- Neo4j database (local or cloud)
- Git
- GitHub CLI (for issue management)

## Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/gregorydickson/memory-graph.git
cd memory-graph

# Install in development mode
pip install -e ".[dev]"
```

### 2. Set Up Neo4j

#### Option A: Docker (Recommended)
```bash
# Start Neo4j with Docker
docker run \
    --name memorygraph-neo4j \
    -p 7474:7474 -p 7687:7687 \
    -d \
    -e NEO4J_AUTH=neo4j/memory123 \
    neo4j:latest

# Wait for Neo4j to start, then visit http://localhost:7474
```

#### Option B: Neo4j Aura (Cloud)
1. Create account at https://neo4j.com/aura/
2. Create new database instance
3. Note the connection URI and credentials

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Neo4j credentials
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=memory123
```

### 4. Test the Installation

```bash
# Run tests to verify setup
pytest

# Start the MCP server
python -m claude_memory
```

## Development Workflow

### Project Structure
```
memory-graph/
├── src/claude_memory/       # Main source code
│   ├── __init__.py
│   ├── models.py           # Data models
│   ├── database.py         # Neo4j operations
│   ├── server.py           # MCP server
│   └── __main__.py         # Entry point
├── tests/                  # Test suite
├── docs/                   # Documentation
└── scripts/               # Utility scripts
```

### Code Style

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=claude_memory

# Run specific test file
pytest tests/test_models.py
```

### GitHub Issues Workflow

```bash
# List current issues
gh issue list

# Create new issue
gh issue create --title "New feature" --body "Description"

# Work on issue #42
git checkout -b feature/issue-42
# ... make changes ...
git commit -m "feat: implement feature (closes #42)"
git push -u origin feature/issue-42

# Create pull request
gh pr create --title "Implement feature" --body "Closes #42"
```

## MCP Integration with Claude Code

### 1. Add to Claude Code Configuration

Add to your Claude Code MCP configuration file:

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "python",
      "args": ["-m", "claude_memory"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "memory123"
      }
    }
  }
}
```

### 2. Test MCP Tools

In Claude Code, you can now use:

```
# Store a memory
store_memory({
  "type": "task", 
  "title": "Setup Database",
  "content": "Configured Neo4j for memory storage",
  "tags": ["setup", "database"]
})

# Search memories
search_memories({
  "query": "database setup",
  "memory_types": ["task"],
  "limit": 5
})
```

## Database Management

### Schema Initialization
The schema is automatically created when the server starts. To manually reinitialize:

```python
from claude_memory.database import Neo4jConnection, MemoryDatabase
import asyncio

async def init_schema():
    conn = Neo4jConnection()
    conn.connect()
    db = MemoryDatabase(conn)
    await db.initialize_schema()
    conn.close()

asyncio.run(init_schema())
```

### Database Backup
```bash
# Backup Neo4j database
docker exec memorygraph-neo4j neo4j-admin dump --database=neo4j --to=/backups/
```

### Viewing Data
- **Neo4j Browser**: http://localhost:7474
- **Cypher queries**: Access through Neo4j Browser or Python scripts

## Debugging

### Enable Debug Logging

```bash
export MEMORY_LOG_LEVEL=DEBUG
python -m claude_memory
```

### Common Issues

**Connection Failed**
- Check Neo4j is running: `docker ps`
- Verify credentials in .env file
- Test connection: `bolt://localhost:7687`

**MCP Server Won't Start**
- Check Python version: `python --version`
- Verify dependencies: `pip list | grep mcp`
- Review error logs

**Memory Storage Issues**
- Check Neo4j disk space
- Verify schema initialization
- Review constraint violations

### Performance Monitoring

```python
# Get database statistics
from claude_memory.database import MemoryDatabase
stats = memory_db.get_memory_statistics()
print(stats)
```

## Contributing

### Before Making Changes
1. Check existing issues: `gh issue list`
2. Create issue if needed: `gh issue create`
3. Create feature branch: `git checkout -b feature/issue-XX`

### Code Requirements
- All new code must have tests
- Pass linting: `ruff check src/ tests/`
- Pass type checking: `mypy src/`
- Update documentation for new features

### Pull Request Process
1. Create PR: `gh pr create`
2. Ensure CI passes
3. Request review
4. Update based on feedback
5. Merge after approval

## Advanced Development

### Custom Memory Types
Add new memory types in `models.py`:

```python
class MemoryType(str, Enum):
    # ... existing types ...
    CUSTOM_TYPE = "custom_type"
```

### Custom Relationship Types
Add new relationships in `models.py`:

```python
class RelationshipType(str, Enum):
    # ... existing types ...
    CUSTOM_RELATION = "CUSTOM_RELATION"
```

### Performance Optimization
- Monitor query performance in Neo4j Browser
- Add indexes for new query patterns
- Use connection pooling for high load

## Getting Help

- **Issues**: https://github.com/gregorydickson/memory-graph/issues
- **Discussions**: https://github.com/gregorydickson/memory-graph/discussions
- **Documentation**: `/docs` folder in repository