# Marketing & Distribution Plan - Claude Code Memory

> **Last Updated**: November 29, 2025
> **Package Status**: v1.0.0 built and ready for PyPI publication
> **Reorganization**: Prioritized by impact on adoption

---

## Executive Summary

This plan is organized by priority: **Must Do** tasks that block adoption and drive initial users, and **Nice to Have** tasks that support growth over time.

### Current Status
- ✅ Package built (v1.0.0) and validated
- ✅ Documentation complete (README, DEPLOYMENT, FULL_MODE, CLAUDE_CODE_SETUP)
- ✅ CLI working (`memorygraph` command)
- ✅ Docker deployment files ready
- ⏳ PyPI publication pending (blocker for most distribution)
- ⏳ Marketing materials ready, awaiting publication

### Critical Path to Launch
1. Publish to PyPI (enables pip install)
2. Submit to Smithery (largest MCP registry)
3. Submit to key awesome lists (GitHub visibility)
4. Post launch announcement (Reddit, GitHub Discussions)
5. Monitor and respond to early users

---

## MUST DO (Critical for Launch)

These tasks directly block adoption or provide maximum ROI for effort invested.

### 1. Package Distribution (BLOCKER)

**PyPI Publication** - Status: ⏳ Ready, awaiting approval
- [ ] Publish to PyPI
  - Package name: `claude-code-memory`
  - Enables: `pip install memorygraphMCP` or `uvx memorygraph`
  - **BLOCKER**: Nothing else works until this is done
  - Package built: `claude_code_memory-1.0.0-py3-none-any.whl` (112KB)
  - Twine validation: PASSED
  - Action required: User needs PyPI credentials

**GitHub Release** - Status: ⏳ Ready
- [ ] Tag and release v1.0.0
  - Command: `git tag -a v1.0.0 -m "Release v1.0.0: Production-ready deployment"`
  - Push tag: `git push origin v1.0.0`
  - Create release on GitHub with changelog
  - Attach: wheel and source distribution
  - Status: Release notes ready in `docs/RELEASE_NOTES_v1.0.0.md`

**Docker Hub** - Status: ⏳ Optional but valuable
- [ ] Publish Docker images
  - Image: `gregorydickson/memorygraph:1.0.0` and `:latest`
  - Enables: `docker pull gregorydickson/memorygraph`
  - Three variants: sqlite (default), neo4j, memgraph
  - Dockerfiles ready, just need to build and push
  - Note: Can defer if time-constrained

---

### 2. Primary Discovery (Maximum Visibility)

**Smithery (Primary Registry)** - Status: ⏳ Blocked by PyPI
- [ ] Publish to **Smithery** at https://smithery.ai/new
  - **Why critical**: Largest MCP registry (2000+ servers), one-click install
  - **Dependency**: Must publish to PyPI first
  - **Python servers**: Smithery auto-generates uvx commands from PyPI
  - Steps:
    1. ✅ Ensure package published to PyPI
    2. Go to https://smithery.ai/new
    3. Connect GitHub account
    4. Select repository: `gregorydickson/claude-code-memory`
    5. Configure (Smithery detects Python package automatically)
    6. Publish (generates uvx installation for users)
  - Estimated time: 15 minutes

**Official MCP Repository** - Status: ⏳ Not started
- [ ] Submit PR to **modelcontextprotocol/servers**
  - URL: https://github.com/modelcontextprotocol/servers
  - **Why critical**: Official Anthropic repository, highest trust
  - Add to community servers section in README
  - Use PR template (section 7.6 below)
  - Estimated time: 30 minutes

**Top Awesome List** - Status: ⏳ Not started
- [ ] Submit PR to **appcypher/awesome-mcp-servers**
  - URL: https://github.com/appcypher/awesome-mcp-servers
  - **Why critical**: Most starred (7000+), highest visibility
  - Add under "Memory" or "Knowledge Graph" section
  - Use PR template (section 7.6 below)
  - Estimated time: 20 minutes

---

### 3. Core Documentation (Already Complete ✅)

**GitHub Repository** - Status: ✅ Complete
- [x] Comprehensive README with quick start
- [x] Add repository topics/tags: `mcp`, `mcp-server`, `claude-code`, `memory`, `neo4j`, `memgraph`, `graph-database`, `ai-agents`, `python`, `sqlite`
- [ ] Add social preview image (optional but nice)
- [x] Badges showing version, tests, coverage
- [x] Clear installation instructions (pip, Docker, source)

**Installation Guides** - Status: ✅ Complete
- [x] `docs/CLAUDE_CODE_SETUP.md` - Step-by-step MCP integration
- [x] `docs/DEPLOYMENT.md` - All deployment scenarios
- [x] `docs/FULL_MODE.md` - Advanced features guide

---

### 4. Launch Announcement (First Week)

**Reddit (Targeted Communities)** - Status: ⏳ Not started
- [ ] Post to **r/ClaudeAI**
  - **Why critical**: Direct audience of Claude users
  - Title: "I built a graph-based memory server for Claude Code (zero-config SQLite)"
  - Include: Quick start, demo GIF, GitHub link
  - Emphasize: One-line install, works in 30 seconds
  - Best time: Tuesday-Thursday, 9am-12pm EST
  - Estimated time: 1 hour (write post, respond to comments)

- [ ] Post to **r/mcp**
  - Dedicated MCP subreddit
  - Focus on technical advantages (graph vs vector)
  - Cross-reference with other memory servers
  - Estimated time: 30 minutes

**GitHub Discussions** - Status: ⏳ Not started
- [ ] Create launch announcement in Discussions
  - Pin the announcement
  - Content ready: `docs/RELEASE_NOTES_v1.0.0.md`
  - Enable discussion for questions
  - Estimated time: 15 minutes

**Twitter/X (Optional)** - Status: ⏳ Not started
- [ ] Create announcement thread (if you use Twitter)
  - Tag @AnthropicAI (maybe)
  - Hashtags: #MCP #ClaudeCode #AIAgents #GraphDatabase
  - Include demo GIF or screenshot
  - Estimated time: 30 minutes

---

### 5. Monitoring & Support (First Month)

**Issue Tracking** - Status: ⏳ Ongoing post-launch
- [ ] Monitor GitHub issues daily
- [ ] Respond to installation problems within 24 hours
- [ ] Fix critical bugs in v1.0.1 if needed
- [ ] Track common questions for FAQ

**Analytics** - Status: ⏳ Post-launch
- [ ] Monitor PyPI download stats
- [ ] Track GitHub stars/forks
- [ ] Monitor Smithery installation count
- [ ] Collect user testimonials

---

## NICE TO HAVE (Post-Launch Growth)

These tasks enhance visibility and adoption but aren't blockers. Can be done over weeks/months.

### 6. Additional Directories

**Secondary Awesome Lists** - Status: ⏳ Not started
- [ ] Submit PR to **punkpeye/awesome-mcp-servers**
  - URL: https://github.com/punkpeye/awesome-mcp-servers
  - Has companion website

- [ ] Submit PR to **serpvault/awesome-mcp-servers**
  - URL: https://github.com/serpvault/awesome-mcp-servers
  - "Biggest Database of MCP Servers"

**Directory Websites** - Status: ⏳ Not started
- [ ] Submit to **mcpservers.org**
- [ ] Submit to **mcp.so**
- [ ] Submit to **mcpindex.net**
- [ ] Submit to **mcpserverfinder.com**
- [ ] Submit to **mcp-server-directory.com** (https://www.mcp-server-directory.com/submit)
- [ ] Submit to **mcpserve.com** (https://mcpserve.com/submit)
- [ ] Submit to **LobeHub MCP directory** (https://lobehub.com/mcp)

**Note**: These are lower priority because most users discover through Smithery, GitHub, or Reddit.

---

### 7. Community Expansion

**Additional Reddit Posts** - Status: ⏳ Not started
- [ ] Post to **r/LocalLLaMA** (if supporting other LLMs)
- [ ] Post to **r/Cursor** (if Cursor integration works)
- [ ] Post to **r/programming** (for broader audience)

**Discord/Slack** - Status: ⏳ Not started
- [ ] Join MCP Discord communities
- [ ] Anthropic Discord (if exists)
- [ ] AI developer Slack workspaces
- [ ] Share when appropriate (don't spam)

**Hacker News** - Status: ⏳ Consider for v1.1
- [ ] Submit "Show HN" post when ready
  - Title: "Show HN: Graph-based memory for Claude Code with pattern recognition"
  - Best on Tuesday-Thursday, 9-11am EST
  - Wait until v1.0 is stable and has some users
  - Include demo video or compelling use case

---

### 8. Enhanced Content

**Demo Materials** - Status: ❌ Not created
- [ ] Create 2-3 minute demo video
  - Show: pip install, MCP config, basic usage
  - Show: Relationship queries and pattern matching
  - Upload to YouTube
  - Embed in README

- [ ] Create animated GIF for README
  - Quick installation flow
  - Memory storage and retrieval
  - 10-15 seconds max

**Blog Posts** - Status: ❌ Not started
- [ ] Write launch blog post
  - Title: "Why I built a graph-based memory server for Claude Code"
  - Content: Technical deep-dive, comparison with alternatives
  - Post to: dev.to, Medium, Hashnode

- [ ] Write comparison post
  - "Graph Memory vs Vector Memory for AI Agents"
  - Technical advantages of relationships
  - Use cases where graph wins

**Documentation Site** - Status: ❌ Not started
- [ ] Create GitHub Pages site (optional)
  - Nicer presentation than markdown
  - Search functionality
  - Can wait until v1.1+

---

### 9. Integration Testing

**IDE/Editor Support** - Status: ⏳ Not tested beyond Claude Code
- [ ] Test Cursor integration
- [ ] Test VS Code + Continue integration
- [ ] Test Windsurf integration
- [ ] Document all supported clients

**LLM Client Support** - Status: ⏳ Not tested
- [ ] Test with Claude Desktop
- [ ] Test with OpenAI Agents SDK (if MCP support exists)
- [ ] Document compatibility matrix

**Note**: Focus on Claude Code first (primary audience). Other integrations can wait.

---

### 10. Advanced Features (v1.1+)

These are future enhancements, not launch requirements:

- [ ] Web visualization dashboard
- [ ] Enhanced embedding support
- [ ] Additional backend support (PostgreSQL + pg_graph)
- [ ] Advanced analytics dashboard
- [ ] Workflow automation features
- [ ] Export/import functionality

---

## PR Template for Awesome Lists

Use this when submitting to GitHub awesome lists:

```markdown
## Add claude-code-memory to Memory section

### Description
Claude Code Memory is a graph-based MCP memory server that provides intelligent,
relationship-aware memory for Claude Code and other MCP clients. Unlike vector-based
memory, it uses graph databases (Neo4j, Memgraph, or SQLite) to capture how
information connects.

### Key Features
- **Zero-config installation**: `pip install memorygraphMCP` with SQLite default
- **Three deployment modes**: lite (8 tools), standard (17 tools), full (44 tools)
- **Graph-based storage**: Captures relationships between memories
- **Pattern recognition**: Learns from past solutions and decisions
- **Multi-backend support**: SQLite (default), Neo4j, Memgraph
- **Docker deployment**: One-command setup for all modes
- **93% test coverage**: Production-ready with 401 passing tests

### Why Add This?
This server uses graph relationships to understand *how* information connects,
enabling queries like:
- "What solutions worked for similar problems?"
- "What decisions led to this outcome?"
- "What patterns exist across my projects?"

Perfect for developers using Claude Code who want persistent, intelligent memory.

### Links
- Repository: https://github.com/gregorydickson/claude-code-memory
- PyPI: https://pypi.org/project/memorygraphMCP/ (or claude-code-memory)
- Documentation: See README and docs/ folder
- Installation: `pip install memorygraphMCP`
```

---

## Launch Timeline

### Week 1 (Launch Week)
- **Day 1**: Publish to PyPI + GitHub release
- **Day 1**: Submit to Smithery
- **Day 2**: Submit to official MCP repo + top awesome list
- **Day 3**: Post to r/ClaudeAI and r/mcp
- **Day 4-7**: Monitor issues, respond to users, fix critical bugs

### Week 2-4 (Growth)
- Submit to secondary awesome lists
- Submit to directory websites
- Create demo video/GIF
- Write launch blog post
- Collect testimonials

### Month 2+ (Expansion)
- Additional community engagement
- Integration testing with other clients
- Plan v1.1 features based on feedback
- Consider Hacker News if traction is good

---

## Success Metrics

### Launch Success (Week 1)
- [ ] Package published on PyPI
- [ ] Listed on Smithery
- [ ] 1-2 GitHub PRs merged (awesome lists)
- [ ] 50+ GitHub stars
- [ ] 10+ PyPI downloads
- [ ] Zero critical installation bugs

### Growth Success (Month 1)
- [ ] 200+ GitHub stars
- [ ] 100+ PyPI downloads
- [ ] Listed on 5+ directories
- [ ] 5+ testimonials or positive comments
- [ ] No unresolved critical issues

### Long-term Success (Month 3+)
- [ ] 500+ GitHub stars
- [ ] 500+ PyPI downloads
- [ ] Active community engagement
- [ ] Feature requests for v1.1
- [ ] Other projects referencing it

---

## Task Status Legend

- ✅ **Complete**: Task finished and verified
- ⏳ **Ready**: Task ready to execute, awaiting action
- 🚧 **In Progress**: Currently working on
- ⏸️ **Blocked**: Waiting on dependency
- ❌ **Skipped**: Not applicable or decided against

---

## Quick Action Checklist (Next Steps)

Before you can do ANYTHING else:

1. [ ] **BLOCKER**: Publish package to PyPI
   - Requires: PyPI account + API token
   - Time: 30 minutes
   - Impact: Unblocks everything

After PyPI publication:

2. [ ] Submit to Smithery (15 min)
3. [ ] Submit to official MCP repo (30 min)
4. [ ] Submit to top awesome list (20 min)
5. [ ] Post to r/ClaudeAI (1 hour)
6. [ ] Create GitHub release (15 min)

**Total time for critical launch tasks**: ~3 hours after PyPI

---

## Notes

### PyPI Package Name
- Current: `claude-code-memory`
- Alternative: `memorygraphMCP` or `mcp-memory-graph`
- Verify availability before publishing

### uvx Support
- ✅ Package already supports uvx (no additional work needed)
- ✅ Existing CLI entry point works with uvx
- ⏳ Works once published to PyPI
- Smithery will auto-generate uvx commands

### Docker Publishing
- Optional but recommended for full-mode users
- Three images: sqlite, neo4j, memgraph variants
- Can defer to v1.0.1 if time-constrained

---

**Last Updated**: November 29, 2025
**Next Review**: After v1.0.0 PyPI publication
