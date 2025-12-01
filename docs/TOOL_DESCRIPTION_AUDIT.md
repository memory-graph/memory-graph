# Tool Description Audit

**Date**: December 1, 2025
**Purpose**: Evaluate current MCP tool descriptions and identify improvements for Claude's tool selection and usage.

## Audit Criteria

Each tool description should answer:
1. **When to use**: Clear scenarios where Claude should select this tool
2. **How to use**: Guidance on constructing parameters
3. **What to expect**: Result format and typical outcomes
4. **Examples**: Concrete usage examples with user queries

---

## Core Tools (Basic - High Priority)

### 1. store_memory

**Current Description**: "Store a new memory with context and metadata"

**Issues**:
- Too generic, doesn't indicate when to use
- No guidance on what context is or when to include it
- Missing examples

**Improvement Priority**: 🔴 CRITICAL
**Recommended Changes**:
- Add "When to use" section (capture learnings, solutions, patterns)
- Explain context parameter with examples
- Add usage scenarios

---

### 2. get_memory

**Current Description**: "Retrieve a specific memory by ID"

**Issues**:
- Adequate but minimal
- Doesn't explain when you'd have an ID to retrieve
- Missing context about include_relationships parameter

**Improvement Priority**: 🟡 MEDIUM
**Recommended Changes**:
- Explain when you'd use this vs search
- Clarify include_relationships benefit
- Add example

---

### 3. search_memories ⭐ PRIMARY TOOL

**Current Description**: "Search for memories based on various criteria"

**Issues**:
- Doesn't emphasize this is the PRIMARY recall tool
- No mention of fuzzy matching capabilities (Phase 2.A)
- No mention of enriched results with relationships (Phase 2.B)
- Missing guidance on when to use different search_tolerance modes
- No examples of effective queries

**Improvement Priority**: 🔴 CRITICAL (Most used tool)
**Recommended Changes**:
- Mark as primary tool for recall
- Explain search_tolerance modes (strict/normal/fuzzy)
- Note that it searches title, content, summary
- Mention relationship enrichment
- Add multiple examples
- Explain when to filter by type/tags/importance

---

### 4. update_memory

**Current Description**: "Update an existing memory"

**Issues**:
- Generic, no indication when to update vs create new
- Missing guidance on partial updates

**Improvement Priority**: 🟢 LOW
**Recommended Changes**:
- Explain when to update (corrections, enrichment)
- Note that only provided fields are updated
- Add example

---

### 5. delete_memory

**Current Description**: "Delete a memory and all its relationships"

**Issues**:
- Adequate but could emphasize cascade behavior

**Improvement Priority**: 🟢 LOW
**Recommended Changes**:
- Emphasize that relationships are also deleted
- Add warning about irreversibility
- Suggest when to delete vs update

---

### 6. create_relationship

**Current Description**: "Create a relationship between two memories"

**Issues**:
- Doesn't explain available relationship types
- No guidance on choosing appropriate relationship type
- No mention of automatic context extraction (Phase 2)
- Missing examples

**Improvement Priority**: 🟡 MEDIUM
**Recommended Changes**:
- List common relationship types with use cases
- Explain context parameter and auto-extraction
- Add examples for different scenarios
- Note default strength/confidence values

---

### 7. get_related_memories

**Current Description**: "Find memories related to a specific memory"

**Issues**:
- Doesn't explain depth traversal clearly
- No guidance on when to filter by relationship type
- Missing examples

**Improvement Priority**: 🟡 MEDIUM
**Recommended Changes**:
- Explain depth parameter (1=immediate, 2=second-degree, etc.)
- Show example of filtering by relationship type
- Explain when to use this vs search

---

### 8. get_memory_statistics

**Current Description**: "Get statistics about the memory database"

**Issues**:
- Adequate for simple tool
- Could mention use cases

**Improvement Priority**: 🟢 LOW
**Recommended Changes**:
- Add use cases (overview, catch up, monitor growth)
- List what statistics are included

---

### 9. search_relationships_by_context ⭐ ADVANCED SEARCH

**Current Description**: "Search relationships by their structured context fields (scope, conditions, evidence, components)"

**Issues**:
- Good technical description but lacks "when to use"
- Parameter meanings unclear without examples
- Missing typical use cases

**Improvement Priority**: 🟡 MEDIUM
**Recommended Changes**:
- Explain when to use (finding conditional implementations, verified solutions)
- Add examples for each filter type
- Note SQLite-only limitation

---

## Tool Selection Strategy

Based on audit, here's the recommended tool hierarchy Claude should follow:

### Primary Tools (Use First)
1. **search_memories** - For any recall query ("What did we learn about X?")
2. **store_memory** - For capturing new learnings, solutions, problems
3. **get_related_memories** - After finding a memory, to understand connections

### Secondary Tools (Drill-down)
4. **get_memory** - When you have a specific ID from search results
5. **create_relationship** - When connecting two known memories
6. **search_relationships_by_context** - For complex conditional queries

### Utility Tools (Supporting)
7. **update_memory** - Corrections or enrichment
8. **delete_memory** - Cleanup
9. **get_memory_statistics** - Overview and catch-up

---

## Recommendations

### Phase 2.C.2: Core Tool Rewrites

**Priority 1 - Rewrite immediately**:
- `search_memories` (most critical)
- `store_memory` (most used)
- `create_relationship` (enables graph features)

**Priority 2 - Rewrite next**:
- `get_related_memories`
- `search_relationships_by_context`
- `get_memory`

### Phase 2.C.3: New Tool - recall_memories

**Purpose**: High-level convenience tool that wraps search_memories with optimal defaults

**Why Needed**:
- Claude should have a simple "go-to" tool for natural language recall
- Reduces cognitive load of choosing between search tools
- Applies best practices automatically (fuzzy matching, relationships included)

**Implementation**: Wrapper around search_memories with:
- search_tolerance: "normal" (fuzzy matching enabled)
- include_relationships: true (always get context)
- Intelligent term extraction from natural language queries
- Result ranking by relevance

**Tool Description Template**:
```
recall_memories - Primary tool for recalling past memories and learnings

WHEN TO USE:
- User asks about past work ("What did we learn about X?")
- Looking for solutions to similar problems
- Understanding past decisions and patterns
- Catching up on project context

HOW TO USE:
- Pass natural language query (e.g., "Redis timeout issues")
- Optionally filter by memory type for precision
- Results include relationship context automatically

EXAMPLES:
- User: "What timeouts have we fixed?" → recall_memories(query="timeout fix")
- User: "Show me Redis solutions" → recall_memories(query="Redis", memory_types=["solution"])
- User: "What did we learn last week?" → recall_memories(query="", project_path="/current/project")

RETURNS:
- Memories with match quality hints
- Immediate relationships (what solves what, what caused what)
- Context summaries for quick scanning
```

---

## Advanced Tools (Lower Priority)

The advanced relationship tools (find_memory_path, analyze_memory_clusters, etc.) are less frequently used. Their descriptions are adequate for specialized use cases. Focus optimization efforts on the core 9 tools above.

---

## Success Metrics

After rewriting tool descriptions:
- Claude's tool selection accuracy: >90% (uses correct tool first try)
- Tool calls per recall: 1-2 average (down from 3-4)
- User satisfaction: Fewer "Claude couldn't find it" reports

---

## Next Steps

1. ✅ Complete this audit (Task 2.C.1)
2. ⏳ Rewrite core tools (Task 2.C.2) - search_memories, store_memory, create_relationship
3. ⏳ Create recall_memories tool (Task 2.C.3)
4. ⏳ Add examples to all tools (Task 2.C.4)
5. ⏳ Create tool selection guide (Task 2.C.5)
