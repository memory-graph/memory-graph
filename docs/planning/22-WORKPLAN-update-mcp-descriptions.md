# Workplan 22: Update MCP Tool Descriptions for Retrieval Optimization

**Status:** Completed
**Goal:** Improve tool descriptions to guide LLMs on when to use `recall_memories` vs `search_memories`
**Triggered By:** User testing revealed `recall_memories` underperforms for acronyms/proper nouns
**Related:** memorygraph.dev WP19 (Memory Retrieval Optimization)
**Last Updated:** 2025-12-23

---

## Problem Statement

Testing revealed that `recall_memories` (fuzzy/natural language) struggles with:
- Acronyms (DCAD, MCR2, JWT, API)
- Proper nouns (Dallas County, Stripe, FalkorDB)
- Technical abbreviations

While `search_memories` with tags filter found the same memory reliably.

### Test Results

| Method | Query | Found Target? |
|--------|-------|---------------|
| `recall_memories` | "DCAD owner lookup workflow Dallas County property" | No (ranked too low) |
| `search_memories` | tags=["dcad"] | Yes (#2 result) |
| `recall_memories` | "owner name resolution property address" | Yes (#9 result) |

**Conclusion:** Tag-based search outperforms natural language for technical terms.

---

## Progress Summary

- [x] Task 1: Update `recall_memories` tool description
- [x] Task 2: Update `search_memories` tool description
- [x] Task 3: Update `store_memory` tool description (tagging guidance)
- [x] Task 4: Run tests and verify descriptions render correctly
- [ ] Task 5: Publish new version to PyPI (ready for release)

---

## Task 1: Update `recall_memories` Tool Description

**Priority:** P0
**Effort:** Low
**File:** `src/memorygraph/server.py:108-120`

### Current Description

```python
description="""Primary tool for finding past memories using natural language queries.

Optimized for fuzzy matching - handles plurals, tenses, and case variations automatically.
Prefer this over search_memories for most queries.

EXAMPLES:
- recall_memories(query="timeout fix") - find timeout-related solutions
- recall_memories(query="Redis", memory_types=["solution"]) - Redis solutions only
- recall_memories(project_path="/app") - memories from specific project

For exact matching or boolean queries, use search_memories instead."""
```

### Proposed Description

```python
description="""Primary tool for finding past memories using natural language queries.

Optimized for fuzzy matching - handles plurals, tenses, and case variations automatically.

BEST FOR:
- Conceptual queries ("how does X work")
- General exploration ("what do we know about authentication")
- Fuzzy/approximate matching

LESS EFFECTIVE FOR:
- Acronyms (DCAD, JWT, API) - use search_memories with tags instead
- Proper nouns (company names, services)
- Exact technical terms

EXAMPLES:
- recall_memories(query="timeout fix") - find timeout-related solutions
- recall_memories(query="how does auth work") - conceptual query
- recall_memories(project_path="/app") - memories from specific project

FALLBACK: If recall returns no relevant results, try search_memories with tags filter."""
```

---

## Task 2: Update `search_memories` Tool Description

**Priority:** P0
**Effort:** Low
**File:** `src/memorygraph/server.py:228-240`

### Current Description

```python
description="""Advanced search with fine-grained filters. Use recall_memories first for simple queries.

Use this when you need: exact matching (search_tolerance="strict"), tag filtering, importance thresholds, or multi-term boolean queries.

Params: query, memory_types, tags, min_importance, search_tolerance (strict/normal/fuzzy), match_mode (any/all)

EXAMPLES:
- search_memories(query="timeout", memory_types=["solution"]) - timeout solutions
- search_memories(tags=["redis"], min_importance=0.7) - important Redis memories
- search_memories(query="auth", search_tolerance="strict") - exact match only"""
```

### Proposed Description

```python
description="""Advanced search with fine-grained filters for precise retrieval.

USE THIS TOOL FIRST (not recall) when searching for:
- Acronyms: DCAD, JWT, MCR2, API, etc.
- Proper nouns: Company names, service names, project names
- Known tags: When you know the tag from previous memories
- Technical terms: Exact matches needed

PARAMETERS:
- tags: Filter by exact tag match (most reliable for acronyms)
- memory_types: Filter by type (solution, problem, etc.)
- min_importance: Filter by importance threshold
- search_tolerance: strict/normal/fuzzy
- match_mode: any/all for multiple terms

EXAMPLES:
- search_memories(tags=["jwt", "auth"]) - find JWT-related memories
- search_memories(tags=["dcad"]) - find DCAD memories by tag
- search_memories(query="timeout", memory_types=["solution"]) - timeout solutions
- search_memories(tags=["redis"], min_importance=0.7) - important Redis memories

For conceptual/natural language queries, use recall_memories instead."""
```

---

## Task 3: Update `store_memory` Tool Description

**Priority:** P1
**Effort:** Low
**File:** `src/memorygraph/server.py:153-204`

### Changes Required

Add tagging guidance to the description to encourage including acronyms as tags:

### Current Description (partial)

```python
description="""Store a new memory with context and metadata.

Required: type, title, content. Optional: tags, importance (0-1), context.
...
```

### Proposed Addition

Add after "Optional: tags, importance (0-1), context.":

```python
TAGGING BEST PRACTICE:
- Always include acronyms AS TAGS (e.g., tags=["jwt", "auth"])
- Fuzzy search struggles with acronyms in content
- Tags provide exact match fallback for reliable retrieval
```

---

## Task 4: Run Tests and Verify

**Priority:** P0
**Effort:** Low

### Verification Steps

1. Run existing tests:
   ```bash
   pytest tests/ -v
   ```

2. Verify tool descriptions render correctly:
   ```bash
   memorygraph --health
   ```

3. Manual verification:
   - Start MCP server
   - Check tool descriptions in MCP inspector or Claude Code

---

## Task 5: Publish New Version

**Priority:** P0
**Effort:** Low

### Steps

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md with description improvements
3. Build and publish:
   ```bash
   python -m build
   twine upload dist/*
   ```

---

## File Reference

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| recall_memories description | `src/memorygraph/server.py` | 108-120 | Natural language search guidance |
| search_memories description | `src/memorygraph/server.py` | 228-240 | Tag/exact search guidance |
| store_memory description | `src/memorygraph/server.py` | 153-204 | Tagging best practices |
| Tool handlers | `src/memorygraph/tools/search_tools.py` | - | Implementation (no changes needed) |

---

## Success Criteria

### Minimum Viable
- [x] `recall_memories` description updated with limitations
- [x] `search_memories` description updated with "use first for acronyms"
- [x] Tests pass

### Complete
- [x] All tool descriptions updated
- [x] `store_memory` includes tagging guidance
- [ ] New version published to PyPI (ready for `python -m build && twine upload dist/*`)
- [ ] User testing confirms improved LLM tool selection

---

## Testing Plan

After implementation, verify LLM behavior with these prompts:

| Prompt | Expected Tool Selection |
|--------|------------------------|
| "Find memories about JWT authentication" | `search_memories(tags=["jwt"])` |
| "How does the auth system work" | `recall_memories(query="auth system")` |
| "Store a memory about DCAD lookup" | `store_memory(tags=["dcad", ...])` |
| "Find DCAD related memories" | `search_memories(tags=["dcad"])` |

---

## Next Steps

1. Implement Task 1 (recall_memories description)
2. Implement Task 2 (search_memories description)
3. Implement Task 3 (store_memory tagging guidance)
4. Run tests (Task 4)
5. Publish (Task 5)
