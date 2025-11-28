# Claude Code Memory Server - Active Workplan

> **Status**: Phase 8 (Deployment & Production Readiness) - Ready to Execute
> **Previous Phases**: See [archive/completed_phases.md](archive/completed_phases.md)
> **Last Updated**: November 28, 2025

## Quick Status

**Completed**: Phases 0-7 (see archive)
**Current Phase**: Phase 8 - Deployment & Production Readiness
**Architecture Health**: A+ (98/100)
**Test Coverage**: 93% (409 tests passing)
**Total MCP Tools**: 44 tools (8 core + 7 relationship + 7 intelligence + 11 integration + 11 proactive)
**Backends**: 3 (Neo4j, Memgraph, SQLite)

---

## Phase 8: Deployment & Production Readiness

**Target**: December 2025
**Priority**: CRITICAL - Ship and enable adoption
**Goal**: Make the server as easy to install as `pip install claude-code-memory` while preserving all advanced features

### Strategy Overview

**Two-Tier Deployment Approach**:
1. **Tier 1 "Zero Config"** (80% of users): SQLite default, 8 core tools, `pip install` simplicity
2. **Tier 2 "Full Power"** (20% power users): Neo4j/Memgraph, all 44 tools, Docker deployment

---

## 8.0 Pre-flight Validation (Priority: CRITICAL)

**Goal**: Verify current state before deployment changes

### 8.0.1 Tool Inventory Audit
- [ ] Count total MCP tools in server.py
  - File: `src/claude_memory/server.py`
  - Expected: 44 tools total
  - Verify: Core (8), Relationship (7), Intelligence (7), Integration (11), Proactive (11)
  - Document: Create tool inventory list

### 8.0.2 Categorize Tools by Profile
- [ ] Document "lite" profile (8 core tools)
  - Tools: store_memory, get_memory, search_memories, update_memory, delete_memory, create_relationship, get_related_memories, get_memory_statistics
- [ ] Document "standard" profile (15 tools)
  - Lite + basic intelligence: find_similar_solutions, suggest_patterns, get_context, get_project_summary
- [ ] Document "full" profile (all 44 tools)
  - All proactive, analytics, and advanced features

### 8.0.3 Baseline Testing
- [ ] Run full test suite to establish baseline
  - Command: `pytest tests/ -v --cov=claude_memory`
  - Expected: 409 tests passing, 93% coverage
  - Document: Record baseline metrics in DEPLOYMENT.md

---

## 8.1 Package Configuration (Priority: CRITICAL)

**Goal**: Prepare for PyPI publication and correct repository attribution

### 8.1.1 Update Repository URLs
- [ ] Update pyproject.toml URLs from viralvoodoo to gregorydickson
  - File: `src/claude_memory/pyproject.toml`
  - Lines: 46-48 (approximate)
  - Change: `https://github.com/ViralV00d00/` → `https://github.com/gregorydickson/`
  - Update: homepage, repository, issues URLs
  - Verify: All links work in browser

### 8.1.2 Add Missing Dependencies
- [ ] Add NetworkX to dependencies for SQLite backend
  - File: `src/claude_memory/pyproject.toml`
  - Section: `[project.dependencies]`
  - Add: `networkx>=3.0.0`
  - Reason: Required for SQLite graph operations

- [ ] Verify optional dependencies structure
  - Section: `[project.optional-dependencies]`
  - Verify `sqlite = ["networkx>=3.0"]` exists
  - Verify `intelligence = ["sentence-transformers>=2.0.0", "spacy>=3.0.0"]` exists
  - Verify `dev = ["pytest", "pytest-asyncio", "pytest-cov", "ruff", "mypy"]` exists

### 8.1.3 Configure CLI Entry Point
- [ ] Verify CLI entry point in pyproject.toml
  - Section: `[project.scripts]`
  - Entry: `claude-memory = "claude_memory.cli:main"`
  - If missing, add it
  - Note: CLI implementation is in 8.2

### 8.1.4 Update Version and Metadata
- [ ] Set version to 1.0.0 for production release
  - File: `src/claude_memory/pyproject.toml`
  - Line: version field
  - Change: current version → `"1.0.0"`
  - Update: `src/claude_memory/__init__.py` __version__ to match

- [ ] Verify package metadata
  - Description: "Graph-based MCP memory server for Claude Code with intelligent relationship tracking"
  - Keywords: MCP, Claude, memory, graph, Neo4j, SQLite
  - Python requirement: `>=3.9`
  - License: Verify correct (MIT or other)

---

## 8.2 Default to SQLite (Priority: CRITICAL)

**Goal**: Make SQLite the zero-config default instead of Neo4j

### 8.2.1 Change Backend Factory Default
- [ ] Update factory.py to default to SQLite
  - File: `src/claude_memory/backends/factory.py`
  - Method: `BackendFactory.create_backend()`
  - Change: `backend_type = os.getenv("MEMORY_BACKEND", "auto")` → `"sqlite"`
  - Alternative: Keep "auto" but change priority order to SQLite first
  - Reason: Frictionless installation

### 8.2.2 Update Configuration Defaults
- [ ] Set SQLite as default in config.py
  - File: `src/claude_memory/config.py`
  - Variable: Default backend configuration
  - Ensure: `MEMORY_SQLITE_PATH` defaults to `~/.claude-memory/memory.db`
  - Ensure: Directory creation is automatic

### 8.2.3 Test SQLite-First Flow
- [ ] Test clean installation with no env vars
  - Remove all MEMORY_* environment variables
  - Run: `python -m claude_memory.server`
  - Verify: SQLite backend selected automatically
  - Verify: Database created at `~/.claude-memory/memory.db`
  - Verify: All 8 core tools work

---

## 8.3 Tool Profiling System (Priority: HIGH)

**Goal**: Allow users to choose tool complexity (lite/standard/full)

### 8.3.1 Define Tool Profiles in Config
- [ ] Create tool profile definitions
  - File: `src/claude_memory/config.py`
  - Add constant:
    ```python
    TOOL_PROFILES = {
        "lite": [
            "store_memory", "get_memory", "search_memories",
            "update_memory", "delete_memory", "create_relationship",
            "get_related_memories", "get_memory_statistics"
        ],
        "standard": [
            # lite + basic intelligence
            *TOOL_PROFILES["lite"],
            "find_similar_solutions", "suggest_patterns_for_context",
            "get_intelligent_context", "get_project_summary"
        ],
        "full": None  # None means all tools
    }
    ```

### 8.3.2 Implement Profile Selection
- [ ] Add profile selection function
  - File: `src/claude_memory/config.py`
  - Function: `get_enabled_tools() -> list[str] | None`
  - Logic: Read `MEMORY_TOOL_PROFILE` env var (default: "lite")
  - Return: List of tool names or None for all tools

### 8.3.3 Filter Tools in Server
- [ ] Implement tool filtering in MCP server
  - File: `src/claude_memory/server.py`
  - Location: Tool registration section
  - Logic: Check if tool name in enabled_tools list
  - Skip registration if tool not in profile
  - Log: Which profile is active and tool count

### 8.3.4 Test Tool Profiles
- [ ] Test lite profile (8 tools)
  - Set: `MEMORY_TOOL_PROFILE=lite`
  - Verify: Only core 8 tools registered
  - Verify: Server starts successfully

- [ ] Test standard profile (15 tools)
  - Set: `MEMORY_TOOL_PROFILE=standard`
  - Verify: 15 tools registered
  - Verify: Intelligence tools available

- [ ] Test full profile (44 tools)
  - Set: `MEMORY_TOOL_PROFILE=full`
  - Verify: All 44 tools registered
  - Verify: All features work

---

## 8.4 CLI Implementation (Priority: HIGH)

**Goal**: Create `claude-memory` command for easy server startup

### 8.4.1 Create CLI Module
- [ ] Create CLI entry point
  - File: `src/claude_memory/cli.py`
  - Use: Click library for CLI framework
  - Command: `claude-memory`
  - Options: --backend, --profile, --host, --port, --log-level

### 8.4.2 Implement CLI Commands
- [ ] Implement main command
  - Function: `main(backend, profile, host, port, log_level)`
  - Actions:
    - Set environment variables based on args
    - Configure logging
    - Import and start MCP server
    - Handle graceful shutdown

- [ ] Add helpful CLI features
  - Option: `--version` shows version
  - Option: `--health` runs health check
  - Option: `--init` creates config file
  - Validation: Check dependencies based on backend choice

### 8.4.3 Test CLI Installation Flow
- [ ] Test pip install and CLI
  - Install: `pip install -e .` (editable mode)
  - Run: `claude-memory --backend sqlite`
  - Verify: Server starts with SQLite
  - Verify: Logs show correct backend and profile
  - Test: Ctrl+C shutdown works gracefully

---

## 8.5 Documentation Updates (Priority: HIGH)

**Goal**: Rewrite documentation to emphasize simplicity

### 8.5.1 Rewrite README.md
- [ ] Create new Quick Start section (top of README)
  - Title: "Quick Start (30 seconds)"
  - Option 1: pip install (recommended, show one-liner)
  - Option 2: Docker (show docker compose command)
  - Claude Code config: Show .claude/mcp.json snippet
  - Emphasize: "That's it! Memory stored in ~/.claude-memory/memory.db"

- [ ] Add "Choose Your Mode" comparison table
  - Columns: Feature, Lite (Default), Standard, Full
  - Rows: Memory ops, Relationships, Patterns, Briefings, Suggestions, Analytics, Backend, Tools, Setup time
  - Show command: How to switch between modes

- [ ] Add feature badges
  - Badge: One-Line Install (blue)
  - Badge: Zero Config (green)
  - Badge: SQLite Default (orange)
  - Badge: 3 Backends (purple)

- [ ] Update architecture section
  - Keep technical details but move lower in README
  - Lead with simplicity, follow with power
  - Link to docs/ for deep dives

### 8.5.2 Create FULL_MODE.md
- [ ] Document advanced features (full mode)
  - File: `docs/FULL_MODE.md`
  - Section 1: Why use full mode?
  - Section 2: Neo4j vs Memgraph vs SQLite
  - Section 3: Docker deployment instructions
  - Section 4: All 44 tools documented
  - Section 5: Performance tuning
  - Section 6: Advanced queries and analytics

### 8.5.3 Create DEPLOYMENT.md
- [ ] Document deployment options
  - File: `docs/DEPLOYMENT.md`
  - Section 1: pip installation (production)
  - Section 2: Docker deployment (all compose files)
  - Section 3: Environment variables reference
  - Section 4: Health checks and monitoring
  - Section 5: Troubleshooting guide
  - Section 6: Migration from SQLite to Neo4j

### 8.5.4 Update CLAUDE_CODE_SETUP.md
- [ ] Create Claude Code integration guide
  - File: `docs/CLAUDE_CODE_SETUP.md`
  - Section 1: Installation (pip or Docker)
  - Section 2: MCP configuration (show mcp.json examples)
  - Section 3: Verifying connection
  - Section 4: First memory storage walkthrough
  - Section 5: Upgrading to full mode
  - Section 6: Troubleshooting MCP issues

---

## 8.6 Docker Support (Priority: MEDIUM)

**Goal**: Enable Docker deployment for all modes

### 8.6.1 Create Base Dockerfile
- [ ] Create minimal Dockerfile
  - File: `docker/Dockerfile`
  - Base: `python:3.11-slim`
  - Copy: pyproject.toml and src/
  - Install: `pip install -e .`
  - Default ENV: `MEMORY_BACKEND=sqlite`, `MEMORY_SQLITE_PATH=/data/memory.db`
  - Entrypoint: `["python", "-m", "claude_memory.server"]`
  - Note: Should work for stdio MCP transport

### 8.6.2 Create docker-compose.yml (SQLite mode)
- [ ] Create simple compose file
  - File: `docker/docker-compose.yml`
  - Service: memory-server
  - Build: From local Dockerfile
  - Environment: MEMORY_BACKEND=sqlite
  - Volume: memory_data:/data
  - Note: stdin_open and tty for MCP stdio

### 8.6.3 Create docker-compose.full.yml (Memgraph mode)
- [ ] Create full power compose file
  - File: `docker/docker-compose.full.yml`
  - Service 1: memgraph (memgraph/memgraph-platform)
  - Ports: 7687 (Bolt), 3000 (Memgraph Lab)
  - Service 2: memory-server (depends on memgraph)
  - Environment: MEMORY_BACKEND=memgraph, full tool profile
  - Network: Share network for service communication

### 8.6.4 Create docker-compose.neo4j.yml (Neo4j mode)
- [ ] Create Neo4j compose file
  - File: `docker/docker-compose.neo4j.yml`
  - Service 1: neo4j (neo4j:5-community)
  - Ports: 7474 (Browser), 7687 (Bolt)
  - Environment: NEO4J_AUTH=neo4j/password
  - Service 2: memory-server (depends on neo4j)
  - Environment: MEMORY_BACKEND=neo4j, credentials
  - Volumes: neo4j_data for persistence

### 8.6.5 Test Docker Deployments
- [ ] Test SQLite mode
  - Build: `docker compose -f docker/docker-compose.yml build`
  - Start: `docker compose -f docker/docker-compose.yml up -d`
  - Verify: Server starts, SQLite database created
  - Test: Store and retrieve memory via MCP

- [ ] Test Memgraph mode
  - Build and start: `docker compose -f docker/docker-compose.full.yml up -d`
  - Verify: Memgraph running, Lab accessible at :3000
  - Verify: Memory server connects to Memgraph
  - Test: Graph operations work

- [ ] Test Neo4j mode
  - Build and start: `docker compose -f docker/docker-compose.neo4j.yml up -d`
  - Verify: Neo4j Browser accessible at :7474
  - Verify: Memory server connects with credentials
  - Test: All 44 tools work

---

## 8.7 PyPI Publishing (Priority: CRITICAL)

**Goal**: Publish to PyPI for `pip install claude-code-memory`

### 8.7.1 PyPI Account Setup
- [ ] Create PyPI account (if not exists)
  - URL: https://pypi.org/account/register/
  - Enable: Two-factor authentication
  - Create: API token for automated publishing

### 8.7.2 Build Package
- [ ] Install build tools
  - Command: `pip install build twine`
  - Verify: Installed successfully

- [ ] Build distribution
  - Command: `python -m build`
  - Output: `dist/` directory with .tar.gz and .whl
  - Verify: Files created correctly
  - Check: Package size reasonable

### 8.7.3 Test Package Locally
- [ ] Test installation from built package
  - Create: Fresh Python virtual environment
  - Install: `pip install dist/claude_code_memory-1.0.0-*.whl`
  - Test: `claude-memory --version`
  - Test: `claude-memory --backend sqlite`
  - Verify: Works without errors

### 8.7.4 Publish to Test PyPI
- [ ] Upload to Test PyPI first
  - Command: `twine upload --repository testpypi dist/*`
  - URL: https://test.pypi.org/
  - Verify: Package appears on Test PyPI
  - Test install: `pip install --index-url https://test.pypi.org/simple/ claude-code-memory`

### 8.7.5 Publish to Production PyPI
- [ ] Upload to production PyPI
  - Command: `twine upload dist/*`
  - Verify: Package appears at https://pypi.org/project/claude-code-memory/
  - Test: `pip install claude-code-memory`
  - Verify: Installation works from PyPI

### 8.7.6 Create GitHub Release
- [ ] Tag release in git
  - Command: `git tag -a v1.0.0 -m "Release v1.0.0: Production-ready deployment"`
  - Push: `git push origin v1.0.0`

- [ ] Create GitHub release
  - URL: https://github.com/gregorydickson/claude-code-memory/releases/new
  - Tag: v1.0.0
  - Title: "v1.0.0 - Production Release"
  - Description: Release notes with features, installation instructions
  - Attach: Built wheel and source distribution

---

## 8.8 Testing & Validation (Priority: HIGH)

**Goal**: Comprehensive testing before public release

### 8.8.1 Integration Testing
- [ ] Test complete installation flow (pip)
  - Fresh environment: Create new Python 3.9, 3.10, 3.11 venvs
  - Install: `pip install claude-code-memory`
  - Configure: Claude Code MCP config
  - Test: Store, retrieve, search, relationships
  - Verify: All core tools work

- [ ] Test complete installation flow (Docker)
  - Fresh system: Clean Docker environment
  - Deploy: SQLite mode
  - Deploy: Memgraph mode
  - Deploy: Neo4j mode
  - Test: All modes work correctly

### 8.8.2 Migration Testing
- [ ] Test backend migration (SQLite to Neo4j)
  - Start: SQLite with sample data
  - Export: Data from SQLite
  - Import: Into Neo4j
  - Verify: All relationships preserved
  - Document: Migration procedure in DEPLOYMENT.md

### 8.8.3 Performance Benchmarking
- [ ] Benchmark SQLite performance
  - Test: 1,000 memories with relationships
  - Test: 10,000 memories with relationships
  - Measure: Query response times
  - Measure: Memory usage
  - Document: Performance characteristics

- [ ] Benchmark Neo4j/Memgraph performance
  - Test: Same datasets
  - Compare: vs SQLite
  - Measure: Graph traversal speed
  - Document: When to upgrade from SQLite

### 8.8.4 Cross-Platform Testing
- [ ] Test on macOS
  - Version: Latest macOS
  - Architecture: Intel and Apple Silicon
  - Verify: pip install works
  - Verify: Docker works (if applicable)

- [ ] Test on Linux
  - Distro: Ubuntu 22.04 LTS
  - Verify: pip install works
  - Verify: Docker works

- [ ] Test on Windows (WSL)
  - Environment: WSL2 Ubuntu
  - Verify: pip install works
  - Verify: Docker works

---

## 8.9 Release Preparation (Priority: MEDIUM)

**Goal**: Marketing and community engagement

### 8.9.1 Update Marketing Materials
- [ ] Review marketing-plan.md
  - File: `docs/marketing-plan.md`
  - Update: With actual PyPI install instructions
  - Update: With Docker deployment info
  - Add: Community links (Discord, GitHub Discussions)

### 8.9.2 Create Announcement Content
- [ ] Write launch announcement
  - Platform: GitHub Discussions
  - Platform: MCP community channels
  - Highlight: Zero-config SQLite default
  - Highlight: 44 tools, 3 backends, 93% test coverage
  - Include: Quick start instructions

### 8.9.3 Prepare Demo Materials
- [ ] Create demo video/GIF
  - Show: `pip install claude-code-memory`
  - Show: Adding to Claude Code config
  - Show: Storing and retrieving memories
  - Show: Relationship queries
  - Length: 2-3 minutes max

### 8.9.4 Community Engagement Plan
- [ ] Submit to MCP server registry
  - Registry: Official MCP server list
  - Category: Memory/Context servers
  - Description: Graph-based memory with relationships

- [ ] Share on social platforms
  - Twitter/X: Announcement thread
  - Reddit: r/ClaudeAI, r/programming
  - Hacker News: Show HN post
  - LinkedIn: Professional announcement

---

## Success Criteria

### Installation & Setup
- [ ] `pip install claude-code-memory` works on Python 3.9-3.11
- [ ] SQLite default requires zero configuration
- [ ] First memory stored in <30 seconds after install
- [ ] Docker deployment works with one command
- [ ] Claude Code integration takes <5 minutes

### Functionality
- [ ] All 409 tests passing (93%+ coverage maintained)
- [ ] Tool profiles (lite/standard/full) work correctly
- [ ] All 3 backends (SQLite, Neo4j, Memgraph) functional
- [ ] Backend migration (SQLite → Neo4j) documented and tested

### Performance
- [ ] SQLite handles 10,000+ memories without degradation
- [ ] Query response times <100ms for memory operations
- [ ] Context retrieval <500ms for typical queries
- [ ] Relationship traversal efficient on all backends

### Documentation
- [ ] README emphasizes simplicity (quick start at top)
- [ ] FULL_MODE.md documents all 44 tools
- [ ] DEPLOYMENT.md covers all deployment scenarios
- [ ] CLAUDE_CODE_SETUP.md provides step-by-step integration

### Publication
- [ ] Package published on PyPI (v1.0.0)
- [ ] GitHub release created with binaries
- [ ] Docker images available on Docker Hub (optional)
- [ ] Listed in MCP server registry

---

## Next Steps After Phase 8

### Post-Release Monitoring (Week 1-2)
- Monitor PyPI downloads
- Track GitHub issues for installation problems
- Respond to community feedback
- Fix critical bugs quickly

### Future Enhancements (v1.1+)
- Web visualization dashboard (optional)
- Enhanced embedding support (sentence-transformers)
- Additional backend support (e.g., PostgreSQL with pg_graph)
- Advanced analytics dashboard
- Workflow automation features

---

## Implementation Notes

### For Coding Agents

**Before Starting**:
1. Read current file before editing
2. Run tests after changes
3. Update this workplan as you complete tasks
4. Commit with conventional commit messages

**Testing**:
- Run `pytest tests/ -v --cov=claude_memory` after each section
- Maintain 93%+ coverage
- All tests must pass before marking section complete

**Priorities**:
- CRITICAL: Must complete for v1.0 release
- HIGH: Important for quality user experience
- MEDIUM: Nice to have, can defer if needed
- LOW: Polish, can be v1.1

**Dependencies**:
- 8.1, 8.2, 8.3 can be done in parallel
- 8.4 depends on 8.3 (tool profiles)
- 8.5 can be done in parallel with code changes
- 8.6 can be done in parallel with 8.1-8.4
- 8.7 must wait for 8.1, 8.2, 8.3, 8.4 to complete
- 8.8 should run after 8.7 (test the published package)
- 8.9 is final step after everything else

---

**Active Phase**: Phase 8 - Deployment & Production Readiness
**Previous Phases**: See [archive/completed_phases.md](archive/completed_phases.md)
**Questions**: Create GitHub issue or check docs/FAQ.md
