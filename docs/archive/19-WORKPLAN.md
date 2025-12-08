# Workplan 19: Context Window Optimization & Marketing

> ❌ **STATUS: ARCHIVED** (2025-12-08)
>
> This workplan is archived because:
> 1. Context optimization was completed in WP12-13 (removed 29 vaporware tools, ~40-45k tokens saved)
> 2. Tool profile cleanup complete (Core: 9 tools, Extended: 12 tools)
> 3. ADR-017 documents the context budget constraint
>
> **Outcome**: Goals achieved through WP12-13 implementation.

**Version Target**: v0.9.7
**Priority**: ~~HIGH~~ ARCHIVED
**Prerequisites**: None
**Estimated Effort**: 8-12 hours

---

## Overview

Audit and optimize MemoryGraph's tool descriptions for minimal context window footprint, then market this advantage against competitors like Byterover Cipher who have abandoned MCP due to context bloat.

**Background**: Byterover published "[A deep dive into our move from MCP to CLI](https://www.byterover.dev/blog/byterover-cli-a-deep-dive-into-our-move-from-mcp-to-cli)" explaining they moved away from MCP because:
- 3 MCP servers ate 26% of context window
- 40+ tools pre-loaded is inefficient
- CLI provides "progressive disclosure"

**Our Position**: MemoryGraph has only 9-11 tools (Core: 9, Extended: 11), which is dramatically leaner than the 40+ tool scenarios Byterover describes. Our graph relationships provide value that flat CLI storage cannot match.

---

## Goal

1. Audit and reduce tool description verbosity
2. Measure and document actual context footprint
3. Add context footprint metrics to website and docs
4. Publish thought leadership article positioning MemoryGraph's approach

---

## Success Criteria

- [ ] All 11 tool descriptions audited and optimized
- [ ] Context footprint reduced by 20%+ (if possible)
- [ ] Context metrics added to memorygraph.dev website
- [ ] Context metrics added to GitHub README
- [ ] Blog article published explaining our approach
- [ ] Competitive comparison table created

---

## Section 1: Tool Description Audit

### 1.1 Current Tool Descriptions Analysis

**File**: `src/memorygraph/tools/*.py`

**Audit each tool for**:
- Redundant explanations
- Excessive examples in docstrings
- Repeated information across tools
- Fields that can be shortened

**Current Tools (Core - 9)**:
1. `store_memory` - Store a new memory
2. `get_memory` - Retrieve by ID
3. `search_memories` - Advanced search
4. `update_memory` - Update existing memory
5. `delete_memory` - Delete memory
6. `create_relationship` - Link memories
7. `get_related_memories` - Traverse graph
8. `recall_memories` - Natural language search (recommended)
9. `get_recent_activity` - Session briefing

**Extended Tools (+2)**:
10. `get_memory_statistics` - Database stats
11. `search_relationships_by_context` - Complex queries

**Tasks**:
- [ ] Count current token usage per tool description
- [ ] Identify verbose descriptions
- [ ] Propose shortened versions
- [ ] Review MCP tool description best practices
- [ ] Implement optimized descriptions

### 1.2 Description Optimization Guidelines

**Principles**:
1. **One sentence summary** - What the tool does
2. **When to use** - Brief trigger guidance
3. **Key parameters only** - Don't document every field
4. **No examples in schema** - Put in docs instead
5. **Use common abbreviations** - "ID" not "identifier"

**Before (verbose)**:
```python
"""
Store a new memory with context and metadata.

This tool is used when you want to capture solutions to problems,
record important decisions and rationale, document errors and their
causes, note patterns or learnings from work, save technology choices
and trade-offs, or record project context and state.

Examples:
- Solved a bug: store_memory(type="solution", title="Fixed Redis timeout")
- Learned a pattern: store_memory(type="pattern", title="Use exponential backoff")
...
"""
```

**After (concise)**:
```python
"""
Store a new memory. Use for solutions, decisions, errors, patterns.
Returns memory_id for linking with create_relationship.
"""
```

**Tasks**:
- [ ] Create optimization guidelines document
- [ ] Apply to all 11 tools
- [ ] Test tools still work correctly
- [ ] Verify Claude still understands tool purpose

### 1.3 Token Count Measurement

**Script**: `scripts/measure_context.py`

```python
"""Measure MCP tool context footprint."""
import tiktoken
from memorygraph.server import create_server

def count_tool_tokens():
    """Count tokens used by tool definitions."""
    encoder = tiktoken.get_encoding("cl100k_base")
    server = create_server(profile="extended")
    
    total_tokens = 0
    for tool in server.tools:
        schema_text = str(tool.inputSchema)
        description = tool.description or ""
        
        tool_tokens = len(encoder.encode(schema_text + description))
        print(f"{tool.name}: {tool_tokens} tokens")
        total_tokens += tool_tokens
    
    print(f"\nTotal: {total_tokens} tokens")
    print(f"Estimated context %: {total_tokens / 100000 * 100:.2f}% (of 100K)")
    
if __name__ == "__main__":
    count_tool_tokens()
```

**Tasks**:
- [ ] Create measurement script
- [ ] Measure BEFORE optimization
- [ ] Measure AFTER optimization
- [ ] Document improvement percentage

---

## Section 2: Context Footprint Documentation

### 2.1 Add to README.md

**Location**: After "Why MemoryGraph?" section

```markdown
## Context Window Efficiency

MemoryGraph is designed for minimal context window impact:

| Metric | Core Mode | Extended Mode |
|--------|-----------|---------------|
| Tools | 9 | 11 |
| Total Tokens | ~800 | ~1,000 |
| Context % (100K) | ~0.8% | ~1.0% |

**Comparison**: Some MCP servers load 40+ tools, consuming 20%+ of context.
MemoryGraph provides full graph-based memory in under 1% of context.

### Why This Matters

Every token used by tool definitions is a token NOT available for your actual work.
Heavy MCP servers force trade-offs between capabilities and context space.
MemoryGraph gives you powerful graph relationships without the bloat.
```

**Tasks**:
- [ ] Measure actual token counts
- [ ] Add section to README
- [ ] Include comparison data
- [ ] Add to Quick Start section as benefit

### 2.2 Add to Website (memorygraph.dev)

**Location**: Homepage features section

**Content**:
```
🪶 Lightweight
~800 tokens | 9 tools | <1% context

MemoryGraph provides powerful graph-based memory without bloating your
context window. While some memory solutions consume 20%+ of context,
we keep it under 1%.
```

**Tasks**:
- [ ] Add to homepage features
- [ ] Create detailed "Performance" page
- [ ] Add comparison chart
- [ ] Include in marketing materials

### 2.3 Add to Documentation

**File**: `docs/CONTEXT_EFFICIENCY.md`

**Content**:
- Why context efficiency matters
- How we measured our footprint
- Comparison with alternatives
- Optimization techniques we use
- Tips for users with multiple MCP servers

**Tasks**:
- [ ] Create context efficiency doc
- [ ] Add to docs index
- [ ] Link from README

---

## Section 3: Blog Article

### 3.1 Article: "Staying Lean in the Age of MCP Tool Bloat"

**See**: `/mnt/user-data/outputs/memorygraph-context-efficiency-article.md`

**Distribution**:
- memorygraph.dev/blog
- dev.to
- Medium
- LinkedIn article
- Twitter/X thread

**Tasks**:
- [ ] Write article (see deliverable below)
- [ ] Create diagrams
- [ ] Get peer review
- [ ] Publish to blog
- [ ] Create social media posts

---

## Section 4: Competitive Comparison

### 4.1 Context Footprint Comparison Table

| Solution | Tools | Tokens | Context % | Notes |
|----------|-------|--------|-----------|-------|
| **MemoryGraph Core** | 9 | ~800 | 0.8% | Graph relationships |
| **MemoryGraph Extended** | 11 | ~1,000 | 1.0% | + Statistics |
| **Byterover (old MCP)** | 40+ | ~5,000+ | 5%+ | Moved to CLI |
| **Typical 3 MCP combo** | 60+ | ~26,000 | 26% | From Byterover blog |

### 4.2 Value Comparison

| Feature | MemoryGraph | Byterover CLI | Flat Storage |
|---------|-------------|---------------|--------------|
| Context Footprint | ~1% | 0% (CLI) | ~0.5% |
| Graph Relationships | ✅ 35+ types | ❌ | ❌ |
| Multi-hop Queries | ✅ | ❌ | ❌ |
| Temporal Reasoning | ✅ | Limited | ❌ |
| Session Briefings | ✅ | ❌ | ❌ |
| MCP Integration | ✅ Native | ❌ Abandoned | ✅ |

**Tasks**:
- [ ] Verify competitor tool counts
- [ ] Create comparison table for docs
- [ ] Create visual chart for website
- [ ] Update competitive analysis doc

---

## Deliverables

1. **Optimized tool descriptions** in `src/memorygraph/tools/`
2. **Context measurement script** in `scripts/measure_context.py`
3. **README update** with context efficiency section
4. **New doc**: `docs/CONTEXT_EFFICIENCY.md`
5. **Blog article**: `memorygraph-context-efficiency-article.md`
6. **Website update**: Homepage features + Performance page

---

## Estimated Timeline

| Section | Effort | Dependencies |
|---------|--------|--------------|
| Section 1: Tool Audit | 3-4 hours | None |
| Section 2: Documentation | 2-3 hours | Measurements done |
| Section 3: Blog Article | 2-3 hours | Analysis complete |
| Section 4: Comparison | 1-2 hours | Research done |
| **Total** | **8-12 hours** | Sequential |

---

## Notes for Coding Agent

**Critical Implementation Details**:

1. **Don't break tool functionality**: Shortening descriptions shouldn't make tools unusable. Test after changes.

2. **Keep key guidance**: Tools like `recall_memories` need the hint that it's the "recommended starting point".

3. **Measure before/after**: Document the improvement precisely.

4. **Marketing tone**: The article should be thought leadership, not attack piece. Acknowledge CLI approach is valid, position our approach as different.

5. **Use real numbers**: Don't estimate. Run the measurement script and use actual token counts.

---

## References

- **Byterover Blog**: https://www.byterover.dev/blog/byterover-cli-a-deep-dive-into-our-move-from-mcp-to-cli
- **Anthropic Code Execution Blog**: https://www.anthropic.com/engineering/code-execution-with-mcp
- **TOOL_PROFILES.md**: Current tool inventory
- **MCP Specification**: Tool description best practices

---

**Last Updated**: 2025-12-07
**Status**: NOT STARTED
**Next Step**: Section 1.3 (Measure current token usage)
