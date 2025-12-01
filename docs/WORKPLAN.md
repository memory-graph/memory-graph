# MemoryGraph - Active Workplan

> **Last Updated**: December 1, 2025
> **Status**: v0.7.1 - Production ready, focusing on search excellence
> **Current Focus**: Search & recall improvements, then marketing
> **Related**: See `/docs/PRODUCT_ROADMAP.md` for strategic context

---

## Core Architecture Principles

**Claude as the Semantic Layer**: We leverage Claude's natural language understanding rather than building competing semantic search. Our job is to provide forgiving, composable tools that return rich, relationship-aware results. Claude interprets user intent, we store and retrieve efficiently.

**What This Means for Development**:
- Prioritize forgiving search (fuzzy matching, case-insensitive)
- Always include relationship context in results
- Optimize tool descriptions to help Claude use them effectively
- Composable tools over monolithic "answer everything" tools

See PRODUCT_ROADMAP.md section "Core Architecture: Claude as the Semantic Layer" for details.

---

## Quick Status

### What's Complete ✅
- ✅ Package published to PyPI (memorygraphMCP v0.7.1)
- ✅ GitHub release v0.7.1 created
- ✅ SQLite-based memory storage (zero-config)
- ✅ Context extraction Phase 1 & 2 (pattern-based structured queries)
- ✅ Tool profiling system (lite/standard/full modes)
- ✅ Comprehensive documentation
- ✅ 707 tests passing (85% coverage)

### What's Blocked ⏸️
- ⏸️ Smithery submission (requires HTTP transport, not stdio)
  - Decision: Deferred to future version
  - Workaround: Users install via PyPI/uvx

### What's Active 🎯
- 🎯 Search & recall improvements (Phase 2 from roadmap)
- 🎯 Tool description optimization for Claude
- 🎯 Marketing and distribution (prepared, awaiting Phase 2 completion)

---

## Phase 1: Marketing & Distribution (Active)

**Goal**: Maximize discoverability and adoption of MemoryGraph MCP server.

### 1.1 Primary Discovery Channels

**Priority: CRITICAL** - Must complete for successful launch

#### Official MCP Repository

- [ ] Submit PR to https://github.com/modelcontextprotocol/servers
- [ ] Add to community servers section
- [ ] Use template from section 1.4 below

**Why critical**: Official Anthropic repository, highest trust and visibility.
**Estimated time**: 30 minutes

#### Top Awesome List

- [ ] Submit PR to https://github.com/appcypher/awesome-mcp-servers
- [ ] Add under "Memory" or "Knowledge Graph" section
- [ ] Use template from section 1.4 below

**Why critical**: Most starred awesome list (7000+ stars), high developer visibility.
**Estimated time**: 20 minutes

### 1.2 Launch Announcements

**Priority: HIGH** - Important for initial momentum

#### Reddit Posts

- [ ] Post to r/ClaudeAI
  - **Title**: "I built a graph-based memory server for Claude Code (zero-config SQLite)"
  - **Content**: Quick start guide, PyPI link, GitHub link
  - **Emphasis**: One-line install, works in 30 seconds
  - **Best time**: Tuesday-Thursday, 9am-12pm EST

- [ ] Post to r/mcp
  - **Focus**: Technical advantages (graph vs vector memory)
  - **Audience**: Technical MCP developers
  - **Cross-reference**: Compare with other memory servers

**Estimated time**: 1-2 hours total (writing + responding to comments)

#### Twitter/X (Optional)

- [ ] Create announcement thread
  - Tag @AnthropicAI
  - Hashtags: #MCP #ClaudeCode #AIAgents #GraphDatabase
  - Include demo GIF or screenshot
  - Best time: Tuesday-Thursday, 9-11am EST

**Estimated time**: 30 minutes
**Priority**: Optional (nice to have)

### 1.3 Monitoring & Support

**Priority: HIGH** - Critical for user retention

#### Issue Management

- [ ] Monitor GitHub issues daily
- [ ] Respond to installation problems within 24 hours
- [ ] Fix critical bugs in patch releases as needed
- [ ] Track common questions for FAQ updates

#### Analytics Tracking

- [ ] Monitor PyPI download statistics weekly
- [ ] Track GitHub stars/forks growth
- [ ] Collect user testimonials and feedback
- [ ] Document common use cases from community

**Ongoing**: First month post-launch

### 1.4 PR Template for Awesome Lists

Use this template when submitting to GitHub awesome lists:

```markdown
## Add MemoryGraph to Memory/Knowledge Graph section

### Description
MemoryGraph is a graph-based MCP memory server that provides intelligent,
relationship-aware memory for Claude Code and other MCP clients. Unlike
vector-based memory, it uses graph databases (Neo4j, Memgraph, or SQLite)
to capture how information connects.

### Key Features
- **Zero-config installation**: `pip install memorygraphMCP` with SQLite default
- **Three deployment modes**: lite (8 tools), standard (17 tools), full (44 tools)
- **Graph-based storage**: Captures relationships between memories
- **Pattern recognition**: Learns from past solutions and decisions
- **Automatic context extraction**: Extracts structure from natural language
- **Multi-backend support**: SQLite (default), Neo4j, Memgraph
- **Docker deployment**: One-command setup for all modes
- **Comprehensive testing**: 689 passing tests

### Why This Server?
This server uses graph relationships to understand *how* information connects,
enabling queries like:
- "What solutions worked for similar problems?"
- "What decisions led to this outcome?"
- "What patterns exist across my projects?"

Perfect for developers using Claude Code who want persistent, intelligent memory
that learns from context and understands relationships.

### Links
- Repository: https://github.com/gregorydickson/claude-code-memory
- PyPI: https://pypi.org/project/memorygraphMCP/
- Documentation: See README and docs/ folder
- Installation: `pip install memorygraphMCP`
- Quick start: `memorygraph` CLI for setup
```

---

## Phase 1.6: Multi-Client Documentation (NEW)

**Goal**: Provide quick start guides for all major MCP-compatible AI coding tools.
**Priority**: HIGH - Expands addressable market beyond Claude Code
**Status**: ✅ COMPLETED - December 1, 2025

### 1.6.1 Documentation for Major MCP Clients

**Context**: MemoryGraph is compatible with any MCP-compliant client. Currently, documentation focuses on Claude Code CLI. We need quick start guides for other popular tools to maximize adoption.

**MCP Client Ecosystem (2025)**:
- ✅ **Claude Code** (CLI, VS Code, Desktop) - Full support, documented
- ✅ **Cursor AI** - Full MCP support, SSE protocol, widely used
- ✅ **Windsurf** - Full MCP support, SSE protocol, feature-rich
- ✅ **VS Code with GitHub Copilot** - GA in v1.102+, agent mode
- ✅ **Continue.dev** - VS Code/JetBrains extension, open-source
- ✅ **Cline** - VS Code extension, autonomous agent
- ✅ **Gemini CLI** - Google's CLI tool with 1M context window

#### Task 1.6.1.A: Create Cursor AI Quick Start Guide ✅

- [x] **Research Cursor MCP configuration**
  - **File to create**: `/Users/gregorydickson/claude-code-memory/docs/quickstart/CURSOR_SETUP.md`
  - **Investigation**:
    - Cursor supports both stdio and SSE transports
    - Configuration via Settings > Features > MCP or `.cursor/mcp.json`
    - One-click installation available for some servers
    - Agent mode required for MCP usage
  - **Content sections**:
    1. Prerequisites (Cursor version, Python 3.10+)
    2. Installation methods (pipx recommended)
    3. Configuration (JSON config for .cursor/mcp.json)
    4. Verification steps (check MCP server list)
    5. First memory example
    6. Troubleshooting (common issues)
  - **Configuration format**:
    ```json
    {
      "mcpServers": {
        "memorygraph": {
          "command": "memorygraph",
          "args": [],
          "env": {}
        }
      }
    }
    ```
  - **Success criteria**: User can configure MemoryGraph in Cursor in <2 minutes
  - **Dependencies**: None
  - **Estimated effort**: 2-3 hours

#### Task 1.6.1.B: Create Windsurf Quick Start Guide ✅

- [x] **Document Windsurf MCP integration**
  - **File to create**: `/Users/gregorydickson/claude-code-memory/docs/quickstart/WINDSURF_SETUP.md`
  - **Investigation**:
    - Windsurf supports SSE protocol
    - Curated MCP servers available in settings
    - More features/settings than Cursor
    - Configuration similar to Cursor
  - **Content sections**:
    1. Prerequisites (Windsurf version, Python 3.10+)
    2. Installation (pipx recommended)
    3. Configuration (Settings > MCP or config file)
    4. Enable MemoryGraph server
    5. Verification and testing
    6. Usage tips specific to Windsurf
  - **Success criteria**: Clear setup path documented
  - **Dependencies**: None
  - **Estimated effort**: 2-3 hours

#### Task 1.6.1.C: Create VS Code + Copilot Quick Start Guide ✅

- [x] **Document VS Code Copilot MCP setup**
  - **File to create**: `/Users/gregorydickson/claude-code-memory/docs/quickstart/VSCODE_COPILOT_SETUP.md`
  - **Investigation**:
    - Requires VS Code v1.102+ (GA release)
    - MCP available in GitHub Copilot agent mode
    - Enterprise policy management available
    - Configuration via `.vscode/mcp.json`
    - Max 128 tools per chat request
  - **Content sections**:
    1. Prerequisites (VS Code 1.102+, Copilot license)
    2. Enterprise policy requirements (if applicable)
    3. Installation (pipx recommended)
    4. Configuration (.vscode/mcp.json format)
    5. Starting MCP servers (click "Start" button)
    6. Using with Copilot agent mode
    7. Security considerations
    8. Troubleshooting
  - **Configuration format**:
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
  - **Success criteria**: VS Code users can enable MemoryGraph with Copilot
  - **Dependencies**: None
  - **Estimated effort**: 3-4 hours (includes enterprise/security notes)

#### Task 1.6.1.D: Create Continue.dev Quick Start Guide ✅

- [x] **Document Continue.dev MCP integration**
  - **File to create**: `/Users/gregorydickson/claude-code-memory/docs/quickstart/CONTINUE_SETUP.md`
  - **Investigation**:
    - Open-source extension for VS Code and JetBrains
    - MCP only works in agent mode
    - Configuration via YAML or JSON in `.continue/mcpServers/`
    - Can copy JSON configs from Claude/Cursor/Cline
    - Supports stdio and SSE transports
  - **Content sections**:
    1. Prerequisites (Continue extension installed)
    2. Installation (pipx recommended)
    3. Configuration (YAML format preferred)
    4. Using "@MCP" in agent mode
    5. Verification steps
    6. Troubleshooting
  - **Configuration format** (YAML):
    ```yaml
    mcpServers:
      - name: MemoryGraph
        command: memorygraph
        args: []
    ```
  - **Success criteria**: Continue users can access MemoryGraph
  - **Dependencies**: None
  - **Estimated effort**: 2 hours

#### Task 1.6.1.E: Create Cline Quick Start Guide ✅

- [x] **Document Cline MCP setup**
  - **File to create**: `/Users/gregorydickson/claude-code-memory/docs/quickstart/CLINE_SETUP.md`
  - **Investigation**:
    - VS Code extension, autonomous coding agent
    - Popular with OpenRouter users (free models)
    - Can create/edit files, run commands
    - Custom MCP tool support
  - **Content sections**:
    1. Prerequisites (Cline extension)
    2. Installation (pipx)
    3. Configuration (Cline settings)
    4. Integration with autonomous workflows
    5. Custom tool creation (if applicable)
    6. Verification
  - **Success criteria**: Cline users can integrate MemoryGraph
  - **Dependencies**: None
  - **Estimated effort**: 2 hours

#### Task 1.6.1.F: Create Gemini CLI Quick Start Guide ✅

- [x] **Document Gemini CLI MCP integration**
  - **File to create**: `/Users/gregorydickson/claude-code-memory/docs/quickstart/GEMINI_CLI_SETUP.md`
  - **Investigation**:
    - Google's CLI tool with 1M token context
    - MCP support for external tools
    - Good for large codebase queries
    - CLI-based workflow
  - **Content sections**:
    1. Prerequisites (Gemini CLI installed)
    2. Google API setup (if needed)
    3. Installation (pipx)
    4. Configuration for Gemini CLI
    5. Usage patterns with large contexts
    6. Verification
  - **Success criteria**: Gemini CLI users can use MemoryGraph
  - **Dependencies**: None
  - **Estimated effort**: 2-3 hours

### 1.6.2 Update Main Documentation

**After creating quick start guides, update central documentation:**

#### Task 1.6.2.A: Update README.md ✅

- [x] **Expand "Installation Options" section**
  - **File**: `/Users/gregorydickson/claude-code-memory/README.md`
  - **Changes**:
    - Add section "Supported MCP Clients"
    - List all supported clients with links to quick start guides
    - Update "Other MCP clients?" callout with specific links
    - Add comparison table of client features/requirements
  - **Table format**:
    | Client | Type | MCP Support | Quick Start |
    |--------|------|-------------|-------------|
    | Claude Code | CLI/IDE | Full | [Setup Guide](docs/CLAUDE_CODE_SETUP.md) |
    | Cursor AI | IDE | Full (SSE) | [Setup Guide](docs/quickstart/CURSOR_SETUP.md) |
    | ... | ... | ... | ... |
  - **Success criteria**: Users can quickly find their client's setup guide
  - **Dependencies**: Tasks 1.6.1.A-F (at least 2-3 completed)
  - **Estimated effort**: 1 hour

#### Task 1.6.2.B: Create Multi-Client Overview Page ✅

- [x] **Create comprehensive client compatibility guide**
  - **File to create**: `/Users/gregorydickson/claude-code-memory/docs/MCP_CLIENT_COMPATIBILITY.md`
  - **Content sections**:
    1. MCP Protocol Overview (brief)
    2. Supported Clients Matrix
    3. Transport Protocol Support (stdio vs SSE)
    4. Feature Comparison (which clients support which features)
    5. Configuration File Formats (JSON/YAML examples)
    6. Migration Guide (switching between clients)
    7. Troubleshooting by Client
  - **Purpose**: Central reference for multi-client support
  - **Success criteria**: Comprehensive client compatibility documented
  - **Dependencies**: Tasks 1.6.1.A-F completed
  - **Estimated effort**: 3-4 hours

#### Task 1.6.2.C: Update DEPLOYMENT.md

- [ ] **Add multi-client deployment considerations**
  - **File**: `/Users/gregorydickson/claude-code-memory/docs/DEPLOYMENT.md`
  - **Changes**:
    - Add "Deploying for Multiple Clients" section
    - Document transport protocol differences
    - Add configuration sharing tips
    - Include security considerations per client type
  - **Success criteria**: Deployment guide covers multi-client scenarios
  - **Dependencies**: Tasks 1.6.1.A-F completed
  - **Estimated effort**: 1-2 hours

### 1.6.3 Community Engagement for Multi-Client Support

**Announce multi-client compatibility to expand reach:**

#### Task 1.6.3.A: Reddit Posts for Client-Specific Communities

- [ ] **Post to r/cursor** (if exists) or r/programming
  - **Title**: "MemoryGraph: Graph-based memory server now with Cursor AI quick start guide"
  - **Focus**: Cursor-specific benefits (SSE support, agent mode)
  - **Include**: Direct link to Cursor setup guide
  - **Dependencies**: Task 1.6.1.A completed
  - **Estimated time**: 30 minutes

- [ ] **Post to r/vscode** (for Copilot users)
  - **Title**: "Add graph-based memory to VS Code Copilot with MemoryGraph MCP server"
  - **Focus**: VS Code 1.102+ integration, enterprise support
  - **Include**: Direct link to VS Code setup guide
  - **Dependencies**: Task 1.6.1.C completed
  - **Estimated time**: 30 minutes

#### Task 1.6.3.B: Update Awesome Lists with Multi-Client Support

- [ ] **Update PR descriptions**
  - **Action**: When submitting to awesome lists, emphasize multi-client compatibility
  - **Messaging**: "Works with Claude Code, Cursor, Windsurf, VS Code Copilot, Continue, and more"
  - **Dependencies**: At least 3-4 quick start guides completed
  - **Estimated time**: 15 minutes (updating existing template)

### 1.6.4 Success Metrics for Multi-Client Documentation

**Measure effectiveness of multi-client support:**

- [x] Quick start guides created for 6+ major MCP clients
- [ ] Each guide tested by at least one user of that client
- [ ] Installation success rate >90% across all clients
- [ ] GitHub issues tracked by client type (identify client-specific problems)
- [ ] Download metrics show adoption across multiple client types
- [ ] Community feedback indicates multi-client support is valuable

**Estimated Total Effort for Phase 1.6**: 18-24 hours (2-3 days)
**Priority**: HIGH - Execute after Phase 2 completion, parallel with Phase 1 marketing
**Impact**: Significantly expands addressable market beyond Claude Code users

---

## Phase 2: Search & Recall Excellence (Active Priority)

**Timeline**: Weeks 4-7 (from PRODUCT_ROADMAP.md)
**Goal**: Make memory recall natural and delightful. Enable Claude to find and synthesize memories effectively.
**Status**: IN PROGRESS - Critical path before marketing push

**Architecture Context**: This phase implements the "Claude as Semantic Layer" approach. We make our search tools forgiving and rich, allowing Claude's natural language understanding to do the semantic heavy lifting.

### 2.A Improve Search Forgiveness

**Current Problem**: Search requires exact or near-exact matches. Users report frustration when searches fail.

**Goal**: Return relevant results even with partial matches, typos, and variations.

**Tasks**:

- [ ] **Task 2.A.1**: Add fuzzy text matching to `search_nodes` tool
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Implementation**: Use SQLite FTS5 with prefix matching OR implement trigram similarity
  - **Expected outcome**: "timeout" matches "timeouts", "timed out", "timing out"
  - **Test file**: `/Users/gregorydickson/claude-code-memory/tests/test_search_fuzzy.py`
  - **Success criteria**: 80%+ success rate on fuzzy match test suite

- [ ] **Task 2.A.2**: Implement case-insensitive search by default
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/sqlite_database.py`
  - **Implementation**: Normalize queries and stored text to lowercase before comparison
  - **Expected outcome**: "Timeout" finds "timeout", "TIMEOUT", "TimeOut"
  - **Dependencies**: None
  - **Success criteria**: All searches case-insensitive, no breaking changes

- [ ] **Task 2.A.3**: Search across all text fields (names, types, observations)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/sqlite_database.py`
  - **Current**: Search only entity names
  - **After**: Search entity names, types, observations, relationship contexts
  - **Expected outcome**: "Redis timeout" finds entities with "Redis" in name and "timeout" in observations
  - **Dependencies**: None
  - **Success criteria**: Search result relevance improves (measure via user testing)

- [ ] **Task 2.A.4**: Add `search_tolerance` parameter (strict/normal/fuzzy)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Implementation**: Add parameter to `search_nodes` tool schema
  - **Values**:
    - `strict`: Exact substring match (current behavior)
    - `normal`: Case-insensitive + common variations (default)
    - `fuzzy`: Trigram similarity with 0.3+ threshold
  - **Expected outcome**: Claude can adjust search forgiveness based on result quality
  - **Dependencies**: Task 2.A.1, 2.A.2
  - **Success criteria**: All three modes work correctly, documented in tool description

- [ ] **Task 2.A.5**: Test and validate search improvements
  - **File**: `/Users/gregorydickson/claude-code-memory/tests/test_search_fuzzy.py`
  - **Create test cases**:
    - Typos: "tmeout" → "timeout"
    - Plurals: "error" → "errors"
    - Tense: "retry" → "retrying", "retried"
    - Case variations: "API" → "api", "Api"
    - Partial matches: "time" → "timeout", "timestamp"
  - **Success criteria**: 90%+ of test cases return relevant results

**Estimated Effort**: 3-4 days
**Priority**: 🔴 CRITICAL - Blocks marketing effectiveness

### 2.B Enrich Search Results

**Current Problem**: Search returns entities but Claude needs relationship context to evaluate relevance and synthesize answers.

**Goal**: Include immediate relationships in search results so Claude can understand how memories connect.

**Tasks**:

- [ ] **Task 2.B.1**: Include immediate relationships in `search_nodes` results
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/sqlite_database.py`
  - **Implementation**: For each matching entity, query its relationships (SOLVES, CAUSES, USED_IN, etc.)
  - **Result format change**:
    ```json
    {
      "name": "RetryWithBackoff",
      "type": "Solution",
      "observations": ["Exponential backoff pattern"],
      "relationships": {
        "solves": ["TimeoutError", "APIRateLimiting"],
        "used_in": ["ProjectAlpha"],
        "related_to": ["ErrorHandling"]
      }
    }
    ```
  - **Expected outcome**: Claude can immediately see what a solution solved, what a problem caused, etc.
  - **Dependencies**: None
  - **Success criteria**: All search results include relationship context, <100ms overhead

- [ ] **Task 2.B.2**: Add `include_relationships` parameter (default: true)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Implementation**: Boolean parameter in `search_nodes` tool
  - **Purpose**: Allow disabling for performance if needed (though should be fast)
  - **Expected outcome**: Claude can toggle relationship inclusion
  - **Dependencies**: Task 2.B.1
  - **Success criteria**: Parameter works, documented

- [ ] **Task 2.B.3**: Add match quality hints to results
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/sqlite_database.py`
  - **Implementation**: Return which fields matched and how (name match, observation match, etc.)
  - **Result format**:
    ```json
    {
      "name": "RetryWithBackoff",
      "match_info": {
        "matched_fields": ["observations"],
        "matched_terms": ["timeout", "retry"],
        "match_quality": "high"
      }
    }
    ```
  - **Expected outcome**: Claude can better rank and filter results
  - **Dependencies**: Task 2.A.1-2.A.3
  - **Success criteria**: Match quality hints accurate, Claude uses them effectively

- [ ] **Task 2.B.4**: Summarize relationship context in results
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/sqlite_database.py`
  - **Implementation**: Add `context_summary` field with natural language summary
  - **Example**: "Solution that solved TimeoutError in ProjectAlpha"
  - **Expected outcome**: Claude can quickly understand memory relevance
  - **Dependencies**: Task 2.B.1
  - **Success criteria**: Summaries accurate, <50 characters, human-readable

- [ ] **Task 2.B.5**: Test enriched results with Claude
  - **Method**: User testing with realistic queries
  - **Test queries**:
    - "What fixed the timeout issue?"
    - "How did we handle API rate limiting?"
    - "What approaches did we try for caching?"
  - **Success criteria**: Claude finds correct answer in 1-2 tool calls (down from 3-4)

**Estimated Effort**: 2-3 days
**Priority**: 🔴 CRITICAL - Core value proposition

### 2.C Optimize Tool Descriptions for Claude

**Current Problem**: Claude may not know the best tool to use or how to construct effective queries.

**Goal**: Rewrite tool descriptions to guide Claude's tool selection and usage.

**Tasks**:

- [ ] **Task 2.C.1**: Audit all MCP tool descriptions
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Review each tool description** for:
    - When to use this tool
    - How to construct parameters
    - What results to expect
    - Examples of usage
  - **Create audit document**: `/Users/gregorydickson/claude-code-memory/docs/TOOL_DESCRIPTION_AUDIT.md`
  - **Dependencies**: None
  - **Success criteria**: All tools audited, improvement areas identified

- [ ] **Task 2.C.2**: Rewrite core tool descriptions (store, search, recall)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Tools to rewrite**:
    - `store_memory` / `create_node`
    - `search_nodes`
    - `get_memory` / `get_node`
    - `search_relationships_by_context`
  - **Description format** (see PRODUCT_ROADMAP.md section 2.3):
    ```
    [Brief summary]

    WHEN TO USE:
    - [Scenario 1]
    - [Scenario 2]

    HOW TO USE:
    - [Step 1]
    - [Step 2]

    EXAMPLES:
    - User: "[query]" → [tool usage]
    ```
  - **Expected outcome**: Claude uses tools correctly on first attempt
  - **Dependencies**: None
  - **Success criteria**: Tool selection accuracy >90% (measure via user testing)

- [ ] **Task 2.C.3**: Create `recall_memories` convenience tool
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Purpose**: High-level tool Claude uses first for natural language queries
  - **Implementation**: Wraps `search_nodes` with:
    - Automatic term extraction
    - Fuzzy matching enabled
    - Relationships included
    - Result ranking by relevance
  - **Tool description**: "Primary tool for recalling past memories. Use when user asks about past work, solutions, problems, or learnings."
  - **Expected outcome**: Claude's go-to tool for memory recall
  - **Dependencies**: Task 2.A.* (search improvements), Task 2.B.* (enriched results)
  - **Success criteria**: 80%+ of recall queries use this tool successfully

- [ ] **Task 2.C.4**: Add usage examples to all tool descriptions
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **For each tool**, add 2-3 concrete examples
  - **Format**: `User: "[request]" → [tool call with parameters]`
  - **Expected outcome**: Claude learns usage patterns from examples
  - **Dependencies**: Task 2.C.1 (audit)
  - **Success criteria**: All tools have examples, examples tested

- [ ] **Task 2.C.5**: Document tool selection logic
  - **File**: `/Users/gregorydickson/claude-code-memory/docs/TOOL_SELECTION_GUIDE.md`
  - **Content**:
    - Decision tree for tool selection
    - Primary tools (Claude uses first)
    - Secondary tools (drill-down)
    - Power tools (complex queries)
  - **Purpose**: Internal reference and basis for tool descriptions
  - **Dependencies**: Task 2.C.1 (audit)
  - **Success criteria**: Guide complete, tools categorized

**Estimated Effort**: 2-3 days
**Priority**: 🔴 CRITICAL - Enables effective Claude usage

### 2.D Multi-Term Search Support

**Current Problem**: Complex queries may require multiple search calls.

**Goal**: Support multi-term and boolean search in a single call.

**Tasks**:

- [ ] **Task 2.D.1**: Add `terms` parameter accepting list of search terms
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Schema change**: `terms: List[str]` in `search_nodes` tool
  - **Implementation**: Search for each term, aggregate results
  - **Expected outcome**: Claude can pass `["timeout", "retry", "API"]` in one call
  - **Dependencies**: None
  - **Success criteria**: Multi-term search works, results ranked by match count

- [ ] **Task 2.D.2**: Add `match_mode` parameter (any/all)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Values**:
    - `any`: Return entities matching ANY term (OR logic)
    - `all`: Return entities matching ALL terms (AND logic)
  - **Default**: `any` (more forgiving)
  - **Expected outcome**: Claude can control precision vs recall
  - **Dependencies**: Task 2.D.1
  - **Success criteria**: Both modes work correctly, documented

- [ ] **Task 2.D.3**: Add `relationship_filter` parameter
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Implementation**: Filter results by relationship type (SOLVES, CAUSES, USED_IN, etc.)
  - **Example**: `search_nodes(terms=["timeout"], relationship_filter="SOLVES")`
  - **Expected outcome**: "What solved timeout issues?" → direct answer
  - **Dependencies**: Task 2.B.1 (relationships in results)
  - **Success criteria**: Filter works, all relationship types supported

- [ ] **Task 2.D.4**: Support basic query operators (OR/AND/NOT)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/sqlite_database.py`
  - **Implementation**: Simple query parser for expressions like:
    - `"timeout OR retry"`
    - `"authentication AND NOT OAuth"`
  - **Expected outcome**: Claude can express complex queries naturally
  - **Dependencies**: Task 2.D.1, 2.D.2
  - **Success criteria**: Query parser works, handles edge cases, documented

- [ ] **Task 2.D.5**: Test multi-term search with real queries
  - **File**: `/Users/gregorydickson/claude-code-memory/tests/test_multi_term_search.py`
  - **Test cases**:
    - Multiple terms with OR: "timeout OR error"
    - Multiple terms with AND: "Redis AND caching"
    - Negation: "authentication NOT OAuth"
    - Relationship filter: terms=["timeout"], relationship_filter="SOLVES"
  - **Success criteria**: 90%+ accuracy on test queries

**Estimated Effort**: 2-3 days
**Priority**: 🟡 HIGH - Improves search power, not blocking

### 2.E Session Briefing & Context

**Goal**: Enable "catch me up" functionality and project-aware briefings.

**Tasks**:

- [ ] **Task 2.E.1**: Improve "catch me up" functionality
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Create tool**: `get_recent_activity(days: int = 7, project: Optional[str] = None)`
  - **Returns**:
    - Count of memories by type (solutions, problems, decisions)
    - Recent memories (last N)
    - Unresolved problems (no SOLVES relationship)
  - **Expected outcome**: User asks "What have we been working on?" → clear summary
  - **Dependencies**: Task 2.B.1 (relationships)
  - **Success criteria**: Briefing accurate, actionable

- [ ] **Task 2.E.2**: Auto-detect project context
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/context_extraction.py`
  - **Implementation**: Extract project name from:
    - Current working directory
    - Git repository name
    - Frequently mentioned project names in recent memories
  - **Expected outcome**: Briefings automatically scoped to current project
  - **Dependencies**: None
  - **Success criteria**: 80%+ accuracy on project detection

- [ ] **Task 2.E.3**: Show recent activity relevant to current work
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Implementation**: In `get_recent_activity`, prioritize memories from detected project
  - **Expected outcome**: Briefing focuses on what's relevant now
  - **Dependencies**: Task 2.E.1, 2.E.2
  - **Success criteria**: User feedback confirms relevance

- [ ] **Task 2.E.4**: Add time-based filtering (last 7 days, 30 days)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/server.py`
  - **Implementation**: Add `timeframe` parameter to search tools
  - **Expected outcome**: "What did we work on last week?" → accurate results
  - **Dependencies**: Task 2.E.1
  - **Success criteria**: Time filtering accurate, supports common timeframes

**Estimated Effort**: 2 days
**Priority**: 🟡 HIGH - High user value

### 2.F Data Portability

**Goal**: Users can backup, restore, and export their memories.

**Tasks**:

- [ ] **Task 2.F.1**: JSON export (full backup)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`
  - **Command**: `memorygraph export --format json --output backup.json`
  - **Implementation**: Export all entities and relationships to structured JSON
  - **Expected outcome**: Complete backup of all data
  - **Dependencies**: None
  - **Success criteria**: Export/import round-trip preserves all data

- [ ] **Task 2.F.2**: JSON import (restore)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`
  - **Command**: `memorygraph import --format json --input backup.json`
  - **Implementation**: Restore entities and relationships from JSON
  - **Conflict handling**: Skip duplicates or overwrite (user choice)
  - **Expected outcome**: Users can restore from backup
  - **Dependencies**: Task 2.F.1
  - **Success criteria**: Import works, handles conflicts gracefully

- [ ] **Task 2.F.3**: Markdown export (human-readable)
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`
  - **Command**: `memorygraph export --format markdown --output memories/`
  - **Implementation**: Export memories as Markdown files (one per entity)
  - **Format**: Frontmatter + observations + relationships
  - **Expected outcome**: Users can browse memories in any editor
  - **Dependencies**: None
  - **Success criteria**: Markdown export readable, organized

- [ ] **Task 2.F.4**: Export command in CLI
  - **File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/cli.py`
  - **Implementation**: Integrate export/import into `memorygraph` CLI
  - **Help text**: Clear examples and format options
  - **Expected outcome**: Users can easily backup data
  - **Dependencies**: Task 2.F.1, 2.F.2, 2.F.3
  - **Success criteria**: CLI documented, tested

**Estimated Effort**: 1.5 days
**Priority**: 🟡 HIGH - User security/trust

### 2.G User Feedback Loop

**Goal**: Establish feedback channels and iterate based on user input.

**Tasks**:

- [ ] **Task 2.G.1**: Add feedback mechanism (GitHub issue template)
  - **File**: `/Users/gregorydickson/claude-code-memory/.github/ISSUE_TEMPLATE/feedback.yml`
  - **Template fields**:
    - What were you trying to do?
    - What happened?
    - What did you expect?
    - Satisfaction (1-5 scale)
  - **Expected outcome**: Structured feedback for analysis
  - **Dependencies**: None
  - **Success criteria**: Template created, linked from README

- [ ] **Task 2.G.2**: Weekly review of Discord feedback
  - **Process**: Review #feedback and #support channels weekly
  - **Action**: Document patterns, prioritize issues
  - **Expected outcome**: Rapid response to user needs
  - **Dependencies**: Phase 1 (Discord setup)
  - **Success criteria**: Review process established, documented

- [ ] **Task 2.G.3**: User interviews (5-10 users)
  - **Method**: 30-minute video calls with active users
  - **Questions**:
    - How do you use memory-graph?
    - What works well?
    - What's frustrating?
    - What's missing?
  - **Expected outcome**: Deep insights into usage patterns
  - **Dependencies**: Phase 1 (user base)
  - **Success criteria**: 5+ interviews completed, insights documented

- [ ] **Task 2.G.4**: Feature request voting
  - **Platform**: GitHub Discussions or dedicated voting tool
  - **Implementation**: Users can propose and vote on features
  - **Expected outcome**: Community-driven roadmap
  - **Dependencies**: None
  - **Success criteria**: Voting system set up, promoted

**Estimated Effort**: 1 day (ongoing)
**Priority**: 🟡 MEDIUM - Continuous improvement

---

### Phase 2 Success Metrics

**Before starting marketing push (Phase 1), we must achieve:**

**Search Quality**:
- [ ] 80%+ of fuzzy match test cases return relevant results
- [ ] Failed searches (no results) <10%
- [ ] Search result relevance: 80%+ relevant in top 5 (measured via user testing)

**Tool Usage**:
- [ ] Tool calls per recall: 1-2 average (down from 3-4 currently)
- [ ] Claude tool selection accuracy: >90% (uses correct tool first try)

**User Satisfaction**:
- [ ] 5+ user interviews completed
- [ ] Clear understanding of top 3 pain points addressed
- [ ] NPS score >40 (from early user surveys)

**Completeness**:
- [ ] All Phase 2.A tasks completed (Search Forgiveness)
- [ ] All Phase 2.B tasks completed (Enrich Results)
- [ ] All Phase 2.C tasks completed (Tool Descriptions)
- [ ] Phase 2.D tasks 80%+ completed (Multi-Term Search)
- [ ] Phase 2.E-2.G tasks: 60%+ completed (nice-to-have)

---

## Phase 1: Marketing & Distribution (Prepared, Awaiting Phase 2)

**Timeline**: After Phase 2 completion
**Goal**: Maximize discoverability and adoption once product experience is excellent.

**Status**: ⏸️ PAUSED - Waiting for Phase 2 search improvements to complete

**Rationale**: Marketing is most effective when the product delivers on promises. Phase 2 ensures memory recall is delightful before we drive traffic.

### Post-Phase-2 Marketing Tasks

**Note**: All marketing tasks from original Phase 1 preserved here. Execute after Phase 2 completion.

### 1.1 Primary Discovery Channels

**Priority: CRITICAL** - Must complete for successful launch

#### Official MCP Repository

- [ ] Submit PR to https://github.com/modelcontextprotocol/servers
- [ ] Add to community servers section
- [ ] Use template from section 1.4 below

**Why critical**: Official Anthropic repository, highest trust and visibility.
**Estimated time**: 30 minutes

#### Top Awesome List

- [ ] Submit PR to https://github.com/appcypher/awesome-mcp-servers
- [ ] Add under "Memory" or "Knowledge Graph" section
- [ ] Use template from section 1.4 below

**Why critical**: Most starred awesome list (7000+ stars), high developer visibility.
**Estimated time**: 20 minutes

### 1.2 Launch Announcements

**Priority: HIGH** - Important for initial momentum

#### Reddit Posts

- [ ] Post to r/ClaudeAI
  - **Title**: "I built a graph-based memory server for Claude Code (zero-config SQLite)"
  - **Content**: Quick start guide, PyPI link, GitHub link
  - **Emphasis**: One-line install, works in 30 seconds
  - **Best time**: Tuesday-Thursday, 9am-12pm EST

- [ ] Post to r/mcp
  - **Focus**: Technical advantages (graph vs vector memory)
  - **Audience**: Technical MCP developers
  - **Cross-reference**: Compare with other memory servers

**Estimated time**: 1-2 hours total (writing + responding to comments)

#### Twitter/X (Optional)

- [ ] Create announcement thread
  - Tag @AnthropicAI
  - Hashtags: #MCP #ClaudeCode #AIAgents #GraphDatabase
  - Include demo GIF or screenshot
  - Best time: Tuesday-Thursday, 9-11am EST

**Estimated time**: 30 minutes
**Priority**: Optional (nice to have)

### 1.3 Monitoring & Support

**Priority: HIGH** - Critical for user retention

#### Issue Management

- [ ] Monitor GitHub issues daily
- [ ] Respond to installation problems within 24 hours
- [ ] Fix critical bugs in patch releases as needed
- [ ] Track common questions for FAQ updates

#### Analytics Tracking

- [ ] Monitor PyPI download statistics weekly
- [ ] Track GitHub stars/forks growth
- [ ] Collect user testimonials and feedback
- [ ] Document common use cases from community

**Ongoing**: First month post-launch

### 1.4 PR Template for Awesome Lists

Use this template when submitting to GitHub awesome lists:

```markdown
## Add MemoryGraph to Memory/Knowledge Graph section

### Description
MemoryGraph is a graph-based MCP memory server that provides intelligent,
relationship-aware memory for Claude Code and other MCP clients. Unlike
vector-based memory, it uses graph databases (Neo4j, Memgraph, or SQLite)
to capture how information connects.

### Key Features
- **Zero-config installation**: `pip install memorygraphMCP` with SQLite default
- **Three deployment modes**: lite (8 tools), standard (17 tools), full (44 tools)
- **Graph-based storage**: Captures relationships between memories
- **Pattern recognition**: Learns from past solutions and decisions
- **Automatic context extraction**: Extracts structure from natural language
- **Multi-backend support**: SQLite (default), Neo4j, Memgraph
- **Docker deployment**: One-command setup for all modes
- **Comprehensive testing**: 707 passing tests, 85% coverage

### Why This Server?
This server uses graph relationships to understand *how* information connects,
enabling queries like:
- "What solutions worked for similar problems?"
- "What decisions led to this outcome?"
- "What patterns exist across my projects?"

Perfect for developers using Claude Code who want persistent, intelligent memory
that learns from context and understands relationships.

### Links
- Repository: https://github.com/gregorydickson/claude-code-memory
- PyPI: https://pypi.org/project/memorygraphMCP/
- Documentation: See README and docs/ folder
- Installation: `pip install memorygraphMCP`
- Quick start: `memorygraph` CLI for setup
```

---

### 1.5 Secondary Directories (Post-Launch)

**Priority: MEDIUM**

#### Secondary Awesome Lists

- [ ] Submit to https://github.com/punkpeye/awesome-mcp-servers
- [ ] Submit to https://github.com/serpvault/awesome-mcp-servers

**Estimated time**: 15 minutes each

#### Directory Websites

- [ ] Submit to https://www.mcp-server-directory.com/submit
- [ ] Submit to https://mcpserve.com/submit
- [ ] Submit to https://lobehub.com/mcp (LobeHub MCP directory)
- [ ] Submit to mcpservers.org (if available)
- [ ] Submit to mcp.so (if available)

**Estimated time**: 10-15 minutes each
**Total time**: ~2 hours

### 2.2 Community Expansion

**Priority: LOW**

#### Additional Reddit Communities

- [ ] Post to r/LocalLLaMA (if supporting other LLMs in future)
- [ ] Post to r/Cursor (if Cursor integration validated)
- [ ] Post to r/programming (broader developer audience)

**Status**: Defer until Phase 1 complete and initial traction gained.

#### Discord/Slack Engagement

- [ ] Join MCP Discord communities
- [ ] Join Anthropic Discord
- [ ] Share in relevant AI developer Slack workspaces
- [ ] Participate authentically (don't spam)

**Status**: Ongoing, low-priority

#### Hacker News

- [ ] Submit "Show HN" post
  - **Title**: "Show HN: Graph-based memory for Claude Code with pattern recognition"
  - **Timing**: Tuesday-Thursday, 9-11am EST
  - **Prerequisite**: Wait until stable with some user testimonials
  - **Include**: Demo video or compelling use case

**Status**: Consider for v1.1+ when have proven traction

### 2.3 Enhanced Content

**Priority: LOW** - Defer until post-launch

#### Demo Materials

- [ ] Create 2-3 minute demo video
  - Show: pip install, MCP config, basic usage
  - Show: Relationship queries and pattern matching
  - Upload to YouTube, embed in README

- [ ] Create animated GIF for README
  - Quick installation flow
  - Memory storage and retrieval
  - 10-15 seconds max

**Estimated time**: 3-4 hours total

#### Blog Posts

- [ ] Write launch blog post
  - **Title**: "Why I built a graph-based memory server for Claude Code"
  - **Content**: Technical deep-dive, comparison with alternatives
  - **Publish**: dev.to, Medium, Hashnode

- [ ] Write comparison post
  - **Title**: "Graph Memory vs Vector Memory for AI Agents"
  - **Content**: Technical advantages of relationships, use cases

**Estimated time**: 4-6 hours per post

---

## Phase 3: Testing & Quality Assurance (Deferred)

**Timeline**: After Phase 2 completion
**Goal**: Achieve comprehensive test coverage across all critical components.
**Status**: ⏸️ DEFERRED - Execute after Phase 2 and Phase 1 (marketing) launch

**Rationale**: Current test coverage (85%, 707 passing tests) is sufficient for launch. Expand testing based on user feedback and bug reports.

**Current Coverage Status**:
- ✅ SQLite backend: 95%+ coverage
- ✅ Core server: 80%+ coverage
- ✅ Context extraction: 100% coverage (74 tests)
- ⚠️ Tool handlers: Variable coverage (0-50%)
- ⚠️ Memgraph backend: No tests
- ⚠️ Neo4j backend: Needs verification

### 3.1 Critical Testing Gaps (Week 1 - 5 days)

**Priority: HIGH** - Execute after marketing launch

#### 3.1.1 Fix Coverage Measurement

**Goal**: Accurate coverage reporting for all modules

- [ ] Update pytest configuration to fix import timing issue
- [ ] Add `[tool.coverage.run]` section to `pyproject.toml` with `source = ["src/memorygraph"]`
- [ ] Run coverage report and verify accurate measurement
- [ ] Document baseline coverage percentage in test documentation
- [ ] Create coverage report generation script for CI

**Effort**: 0.5 days
**Success criteria**: Coverage measurement accurate for all modules, core modules no longer showing 0%

**Note**: Detailed testing plans (97+ tests across tool handlers, backends, models, relationships, transactions, integrations, analytics, performance, security, compatibility) moved to archive. Execute based on user feedback and bug reports.

**Recommended Testing Priority** (post-launch):
1. Tool handlers for frequently-used tools (based on usage metrics)
2. Cross-platform testing (Linux, Windows WSL2)
3. Backend-specific tests (Memgraph, Neo4j) if users request
4. Performance testing if users report slowness
5. Security audit before enterprise features

### 3.2 Advanced Features (v1.1+)

**Status**: Future enhancements based on user demand.

See `/docs/SCALING_FEATURES_WORKPLAN.md` for detailed implementation plans for:

1. **Access Pattern Tracking** - Track memory usage, last accessed times
2. **Decay-Based Pruning** - Automatically archive old/unused memories
3. **Memory Consolidation** - Merge similar memories automatically
4. **Semantic Clustering** - Group related memories (requires embeddings)
5. **Progressive Loading** - Pagination and lazy loading for large datasets
6. **Performance Enhancements** - Caching, indexing, batch operations

**When to implement**: When users report scaling issues (10k+ memories) or request these features.

**Estimated complexity**: High (4-6 weeks total for all features)

### 3.3 Documentation Improvements

**Priority: LOW** - As needed based on user feedback

#### uvx Support Documentation

- [ ] Update README.md with uvx installation option
- [ ] Add installation method comparison table
- [ ] Update DEPLOYMENT.md with uvx use cases
- [ ] Update CLAUDE_CODE_SETUP.md with uvx MCP config
- [ ] Test uvx execution locally

**Status**: Package already supports uvx. This is documentation-only enhancement.

**Note**: uvx support works now (`uvx memorygraph`), just not explicitly documented.

**Estimated time**: 1-2 hours

---

## Success Metrics

### Phase 2 Success (Search & Recall Excellence)

**Must achieve before marketing launch**:

**Search Quality**:
- [ ] 80%+ of fuzzy match test cases return relevant results
- [ ] Failed searches (no results) <10%
- [ ] Search result relevance: 80%+ relevant in top 5

**Tool Usage**:
- [ ] Tool calls per recall: 1-2 average (down from 3-4)
- [ ] Claude tool selection accuracy: >90%

**User Validation**:
- [ ] 5+ user interviews completed
- [ ] Clear understanding of top 3 pain points addressed
- [ ] NPS score >40 (early users)

### Launch Success (Phase 1 - Post Phase 2)

Target metrics for evaluating initial launch:

- [x] Package published on PyPI ✅
- [ ] Listed on official MCP repository
- [ ] Listed on top awesome list (appcypher/awesome-mcp-servers)
- [ ] 100+ GitHub stars (revised up from 50)
- [ ] 1,000+ PyPI downloads (revised up from 20)
- [ ] Zero critical installation bugs
- [ ] 50+ Discord members

### Growth Success (Month 1 Post-Launch)

Target metrics for evaluating first month after marketing:

- [ ] 250+ GitHub stars
- [ ] 3,000+ PyPI downloads
- [ ] Listed on 5+ directories/awesome lists
- [ ] 10+ user testimonials or positive comments
- [ ] No unresolved critical issues
- [ ] Active community engagement (issues, discussions)
- [ ] <5% uninstall rate
- [ ] 50%+ weekly active users

### Long-term Success (Month 3+ Post-Launch)

Target metrics for evaluating product-market fit:

- [ ] 500+ GitHub stars
- [ ] 7,000+ PyPI downloads
- [ ] Active community contributions
- [ ] Feature requests for v1.1
- [ ] Other projects referencing/using it
- [ ] Positive sentiment in MCP community
- [ ] NPS score >40 maintained

---

## Package Information

**Package Name**: memorygraphMCP
**Current Version**: 0.6.0
**PyPI**: https://pypi.org/project/memorygraphMCP/
**GitHub**: https://github.com/gregorydickson/claude-code-memory
**License**: MIT

### Installation

```bash
# Standard installation
pip install memorygraphMCP

# Using uvx (recommended for MCP)
uvx memorygraph

# From source
git clone https://github.com/gregorydickson/claude-code-memory.git
cd claude-code-memory
poetry install
```

### Tool Profiles

- **lite** (default): 8 core tools, SQLite, zero config
- **standard**: 15 tools, adds intelligence features
- **full**: All 44 tools, requires Neo4j/Memgraph

### Deployment Options

1. **pip install** (recommended for 80% of users)
   - Zero configuration
   - SQLite backend (automatic)
   - Handles 10k+ memories

2. **Docker** (for advanced users)
   - Full-featured with Neo4j/Memgraph
   - Production-grade setup
   - Scales to 100k+ memories

3. **From source** (for contributors)
   - Development setup
   - Latest features
   - Contribution workflow

---

## Execution Notes

### For Marketing Tasks

1. **Prioritize official channels first**: MCP repo > top awesome list > Reddit
2. **Write authentic, helpful content**: Focus on solving problems, not self-promotion
3. **Engage with community**: Respond to questions, incorporate feedback
4. **Track what works**: Monitor which channels drive adoption
5. **Be patient**: Community growth takes time, focus on quality over quantity

### For Development Tasks

1. **Run tests before changes**: `python3 -m pytest tests/ -v`
2. **Maintain test coverage**: Keep above 85%
3. **Update workplan as tasks complete**: Mark [x] and document results
4. **Use conventional commits**: `feat:`, `fix:`, `docs:`, `test:`, etc.
5. **Check backward compatibility**: Verify existing users unaffected

### For Issue Support

1. **Response time**: Reply to issues within 24 hours
2. **Triage urgency**: Critical bugs first, features later
3. **Ask for details**: Get reproduction steps, environment info
4. **Fix and release**: Critical bugs get patch releases same day
5. **Close the loop**: Confirm fix with reporter before closing

---

## Current Phase Summary

**Phase**: Search & Recall Excellence (Phase 2)
**Started**: December 1, 2025
**Target Completion**: December 28, 2025 (4 weeks)
**Next Phase**: Marketing & Distribution (Phase 1) after Phase 2 completion

**Critical Path (Must Complete Before Marketing)**:
1. **Phase 2.A**: Search Forgiveness (3-4 days) - fuzzy matching, case-insensitive, multi-field search
2. **Phase 2.B**: Enrich Results (2-3 days) - relationships in results, match quality hints
3. **Phase 2.C**: Tool Descriptions (2-3 days) - rewrite for Claude, add recall_memories tool
4. **Phase 2.D**: Multi-Term Search (2-3 days) - multiple terms, boolean operators (80% completion acceptable)

**High Value (Complete if time allows)**:
5. **Phase 2.E**: Session Briefing (2 days) - catch me up, project context
6. **Phase 2.F**: Data Portability (1.5 days) - export/import/backup
7. **Phase 2.G**: User Feedback (1 day) - interviews, feedback loops

**Total Estimated Effort**: 12-16 days (critical path) + 4-5 days (high value) = 16-21 days

**Success Criteria**: See "Phase 2 Success Metrics" above - must achieve 80%+ search quality metrics and user validation before launching marketing.

**Rationale for Phase Order**: Product experience must be excellent before driving traffic. Phase 2 ensures Claude can effectively use our memory tools, then Phase 1 marketing amplifies adoption.

---

## Deferred Testing Plan (Archived)

**Note**: Detailed testing workplan (originally Phase 4) has been moved to archive consideration. The original plan included 97+ new tests across:
- Tool handlers (advanced, intelligence, integration, proactive tools)
- Backend implementations (Memgraph)
- Model validation edge cases
- Relationship scenarios (circular, cascade delete)
- Database transactions and error recovery
- Integration testing (end-to-end, MCP protocol, Docker)
- Analytics and metrics
- Performance and load testing
- Security auditing
- Compatibility testing (cross-platform, Python versions)

**Current testing status is sufficient for launch** (707 tests, 85% coverage). Execute additional testing based on:
1. User-reported bugs
2. Usage patterns (test heavily-used features first)
3. Enterprise requirements (security audit, compliance)
4. Scaling needs (performance testing when users hit limits)

See Phase 3 above for prioritized testing tasks.

---

## Archive References

### Completed Work

See `/docs/archive/` for completed tasks:

- **`COMPLETED_TASKS_2025-11-30.md`** - All completed tasks across all workplans
- **`CONTEXT_EXTRACTION_PHASE1_COMPLETION.md`** - Detailed Phase 1 completion report
- **`completed-tasks-2025-01.md`** - January 2025 completed tasks
- **`completed_phases.md`** - Historical phase completions

### Context Extraction Work (Completed)

- ✅ **Phase 1**: Pattern-based context extraction (74 tests)
- ✅ **Phase 2**: Structured querying of relationship contexts (18 tests)
- ✅ Total: 92 context extraction tests, all passing
- ✅ Documentation: README.md "Structured Query Support" section

**Status**: Context extraction fully implemented and tested (November 30, 2025)

### Superseded Documents

The following workplan documents have been consolidated into this file:

- ~~`CONTEXT_EXTRACTION_WORKPLAN.md`~~ - Archived. Phase 1 & 2 complete
- Active tasks moved to this consolidated workplan
- See archive for completed Phase details and original workplan

### Related Documentation

- `/README.md` - User-facing documentation
- `/docs/DEPLOYMENT.md` - Deployment guide
- `/docs/CLAUDE_CODE_SETUP.md` - Claude Code integration
- `/docs/FULL_MODE.md` - Full mode features
- `/docs/SCALING_FEATURES_WORKPLAN.md` - Future scaling features (reference)
- `/docs/PRODUCT_ROADMAP.md` - Strategic product roadmap (v2.1)
## Archive References

### Completed Work

See `/docs/archive/` for completed tasks:

- **`COMPLETED_TASKS_2025-11-30.md`** - All completed tasks across all workplans
- **`CONTEXT_EXTRACTION_PHASE1_COMPLETION.md`** - Detailed Phase 1 completion report
- **`completed-tasks-2025-01.md`** - January 2025 completed tasks
- **`completed_phases.md`** - Historical phase completions

### Superseded Documents

The following workplan documents have been consolidated into this file:

- ~~`CONTEXT_EXTRACTION_WORKPLAN.md`~~ - Archived. Phase 1 & 2 complete (November 30, 2025)
- Active tasks moved to this consolidated workplan
- See archive for completed Phase details and original workplan

### Related Documentation

- `/docs/PRODUCT_ROADMAP.md` - Strategic product roadmap (v2.1) **← Primary strategic reference**
- `/README.md` - User-facing documentation
- `/docs/DEPLOYMENT.md` - Deployment guide
- `/docs/CLAUDE_CODE_SETUP.md` - Claude Code integration
- `/docs/FULL_MODE.md` - Full mode features
- `/docs/SCALING_FEATURES_WORKPLAN.md` - Future scaling features (reference)

---

**Last Updated**: December 1, 2025
**Next Review**: Weekly during Phase 2 execution
