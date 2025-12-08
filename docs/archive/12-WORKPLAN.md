# Workplan 12: Semantic Navigation Tools (v0.10.0)

**Version Target**: v0.10.0
**Priority**: HIGH (Competitive Gap)
**Prerequisites**: Workplans 1-5 complete ✅
**Status**: ✅ COMPLETE (with scope reduction for context efficiency)

---

## Context Budget Decision (2025-12-07)

### Problem
Initial implementation added 6 navigation tools, consuming significant context overhead:
- Each MCP tool definition costs ~1-1.5k tokens
- 6 tools × ~1.2k tokens = ~7.2k tokens overhead
- Benefits did not justify context cost for most tools

### Decision
**Cut 5 tools, keep 1** based on value/context ratio:

| Tool | Tokens | Value | Decision |
|------|--------|-------|----------|
| browse_memory_types | ~1.2k | Low - rarely used | ❌ CUT |
| browse_by_project | ~1.2k | Low - search handles this | ❌ CUT |
| browse_domains | ~1.2k | Low - expensive clustering | ❌ CUT |
| find_chain | ~1.2k | Medium - get_related_memories covers | ❌ CUT |
| trace_dependencies | ~1.2k | Medium - get_related_memories covers | ❌ CUT |
| contextual_search | ~1.0k | High - unique scoped search | ✅ KEEP |

### Outcome
- **Removed**: 5 tools, 2 files (browse_tools.py, chain_tools.py), 25 tests
- **Kept**: contextual_search (Extended profile), 10 tests
- **Context saved**: ~5.5k tokens
- **Tests passing**: 1,338

### Lesson Learned
> **Every MCP tool must justify its context cost.** Features that duplicate existing functionality or have low usage should be cut aggressively.

---

## Overview

Implement enhanced navigation tools that enable Claude to semantically traverse the knowledge graph without embeddings. This validates our graph-first approach (confirmed by Cipher's pivot away from vectors in v0.3.1).

**Philosophy**: Claude already understands language semantically. We don't need embeddings—we need better tools for LLM-driven graph navigation.

**Reference**: PRODUCT_ROADMAP.md Phase 2.3 (Semantic Navigation)

---

## Goal

Enable Claude to navigate memories using natural language intent by providing specialized MCP tools for:
- ~~Browsing memory types and domains~~ (CUT - low value)
- ~~Traversing relationship chains automatically~~ (CUT - get_related_memories covers this)
- ~~Finding solutions to problems via graph traversal~~ (CUT - existing tools sufficient)
- ✅ Contextual search within related memories (KEPT - unique value)

---

## Success Criteria

- [x] ~~6 new navigation tools~~ → 1 navigation tool implemented (contextual_search)
- [x] Navigation queries <50ms p95 latency
- [x] Zero vector/embedding dependencies
- [x] 10 tests passing for contextual_search
- [x] Context overhead minimized (<2k tokens for new tools)
- [ ] Demo video showing semantic navigation (deferred)
- [ ] Documentation with navigation examples (deferred)

---

## Implemented: contextual_search

### Tool: `contextual_search`

**Purpose**: Search only within related memories (scoped search)

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/tools/search_tools.py`

**Profile**: Extended (12 tools total)

**Why Kept**: Provides unique value that existing tools don't cover:
1. Two-phase search (traverse → filter) is genuinely different
2. Enables semantic scoping without embeddings
3. No duplication with recall_memories or search_memories

**Implementation**:
```python
def contextual_search(
    memory_id: str,
    query: str,
    max_depth: int = 2,
    backend: Backend
) -> dict:
    """
    Search within the context of a given memory.

    1. Find all memories related to memory_id (up to max_depth)
    2. Search query only within those related memories

    This provides semantic scoping without embeddings.
    """
```

**Tasks**:
- [x] Implement two-phase search (traverse → filter)
- [x] Reuse get_related_memories for traversal
- [x] Apply text search only to related set
- [x] Register as MCP tool (Extended profile)
- [x] Add tests for contextual search (10 tests)

---

## Removed Tools (Context Optimization)

The following tools were implemented but removed to reduce context overhead:

### ❌ browse_memory_types
- **Reason**: Low usage frequency, information available via search
- **Alternative**: Use `search_memories` with memory_types filter

### ❌ browse_by_project
- **Reason**: Duplicates functionality of search_memories with project filter
- **Alternative**: Use `search_memories(project_path="...")`

### ❌ browse_domains
- **Reason**: Expensive in-memory clustering, limited practical value
- **Alternative**: Use tags for organization

### ❌ find_chain
- **Reason**: get_related_memories with relationship_types achieves same result
- **Alternative**: Use `get_related_memories(memory_id, relationship_types=["SOLVES"], max_depth=3)`

### ❌ trace_dependencies
- **Reason**: Specialized case of find_chain/get_related_memories
- **Alternative**: Use `get_related_memories(memory_id, relationship_types=["DEPENDS_ON", "REQUIRES"])`

---

## Files Changed

### Deleted
- `/src/memorygraph/tools/browse_tools.py` (3 tools)
- `/src/memorygraph/tools/chain_tools.py` (2 tools)
- `/tests/tools/test_browse_tools.py` (12 tests)
- `/tests/tools/test_chain_tools.py` (13 tests)

### Updated
- `/src/memorygraph/tools/__init__.py` - removed imports
- `/src/memorygraph/server.py` - removed tool definitions and handlers
- `/docs/TOOL_PROFILES.md` - Extended now 12 tools

### Kept
- `/src/memorygraph/tools/search_tools.py` - contextual_search (lines 262-377)
- `/tests/tools/test_contextual_search.py` - 10 tests

---

## Context Budget Principles (for future workplans)

### Before Adding MCP Tools

1. **Estimate context cost**: ~1-1.5k tokens per tool
2. **Evaluate uniqueness**: Does this duplicate existing functionality?
3. **Assess frequency**: How often will this be used?
4. **Calculate ROI**: value_delivered / context_consumed

### Threshold for New Tools

- **Must exceed**: 0.5 value/1k tokens ratio
- **Unique capability**: Cannot be achieved by existing tools
- **Expected usage**: At least 1 in 10 sessions

### When to Remove Tools

- Usage < 5% of sessions
- Can be replicated with existing tools
- Context cost exceeds benefit
- Overlaps significantly with another tool

---

## Acceptance Criteria Summary

### Functional
- [x] contextual_search implemented and working
- [x] Tool integrates with Extended profile
- [x] No vector/embedding dependencies
- [x] Scoped search works correctly

### Context Efficiency
- [x] Only 1 new tool added (vs 6 originally planned)
- [x] Context overhead ~1k tokens (vs ~7.2k originally)
- [x] 83% context reduction achieved

### Quality
- [x] 10 tests passing for contextual_search
- [x] All existing tests still pass (1,338 total)
- [x] Edge cases handled (empty results, etc.)

---

## References

- **PRODUCT_ROADMAP.md**: Phase 2.3 (Semantic Navigation)
- **ADR-012**: Cycle detection implementation
- **Cipher v0.3.1**: Validation of non-vector approach
- **TOOL_PROFILES.md**: Profile documentation

---

**Last Updated**: 2025-12-07
**Status**: ✅ COMPLETE (scope reduced for context efficiency)
**Lesson**: Context overhead is a first-class concern. Cut aggressively.
