# Tool Profiles Reference

This document provides a complete inventory of all implemented MCP tools in MemoryGraph, organized by profile tier.

## Profile Overview

| Profile | Tool Count | Description | Use Case |
|---------|------------|-------------|----------|
| **core** | 9 | Essential memory operations | Default for 95% of users, zero-config |
| **extended** | 12 | Core + analytics + contextual search | Power users needing stats & scoped queries |

**Note**: As of v0.10.0+, 29 unimplemented "vaporware" tools and 3 temporal MCP tools were removed from the active codebase, saving ~40-45k context tokens. See [ADR-017](adr/017-context-budget-constraint.md) for details.

## Quick Comparison

| Feature | Core (Default) | Extended |
|---------|----------------|----------|
| Memory CRUD | ✅ 5 tools | ✅ 5 tools |
| Relationships | ✅ 2 tools | ✅ 2 tools |
| Discovery | ✅ 2 tools | ✅ 2 tools |
| Database Stats | ❌ | ✅ 1 tool |
| Complex Queries | ❌ | ✅ 1 tool |
| Contextual Search | ❌ | ✅ 1 tool |
| Setup | Zero-config | Zero-config |
| Backend | SQLite | SQLite |

---

## Core Profile (9 tools) - DEFAULT

**Zero-config default**. Provides all essential memory operations for daily use.

### Essential Memory Operations (5 tools)

1. **store_memory** - Store a new memory with context and metadata
   - Capture solutions, problems, errors, patterns, decisions
   - Add tags, importance scores, project context
   - Returns memory_id for future reference

2. **get_memory** - Retrieve a specific memory by ID with full details
   - Get complete memory information
   - Optionally include relationships
   - Use after finding a memory in search

3. **search_memories** - Advanced search with fine-grained control
   - Full-text search across title, content, summary
   - Filter by memory types, tags, importance
   - Strict or fuzzy matching modes
   - Boolean queries (any/all terms)

4. **update_memory** - Update an existing memory
   - Modify title, content, summary, tags
   - Update importance scores
   - Requires memory_id

5. **delete_memory** - Delete a memory and all its relationships
   - Permanent removal
   - Cascades to delete relationships
   - Requires memory_id

### Essential Relationship Operations (2 tools)

6. **create_relationship** - Create a relationship between two memories
   - 35+ relationship types (SOLVES, CAUSES, REQUIRES, etc.)
   - Optional strength and confidence scores
   - Natural language context auto-extracted
   - Enables "What solved X?" queries

7. **get_related_memories** - Find memories related to a specific memory
   - Traverse relationships by type
   - Control depth (1-5 levels)
   - Explore knowledge graph connections
   - Filter by relationship types

### Discovery and Navigation (2 tools)

8. **recall_memories** - Primary search with fuzzy matching (RECOMMENDED)
   - Optimized for natural language queries
   - Automatic fuzzy matching (handles plurals, tenses)
   - Always includes relationship context
   - Best starting point for recall queries
   - Match quality hints and suggestions

9. **get_recent_activity** - Session briefing and progress tracking
   - Summary of recent memories (last N days)
   - Breakdown by type (solutions, problems, etc.)
   - Unresolved problems highlighted
   - Project-scoped activity
   - "Catch me up" functionality

---

## Extended Profile (12 tools)

**Core + advanced analytics + contextual search**. For power users who need database statistics, complex relationship queries, and scoped search.

### All Core Tools (9)
- All tools from Core profile above

### Advanced Analytics (2 additional)

10. **get_memory_statistics** - Get comprehensive database statistics
    - Total memories and relationships
    - Breakdown by memory type
    - Average importance and confidence scores
    - Graph metrics overview

11. **search_relationships_by_context** - Complex relationship queries
    - Search by structured context fields (scope, conditions, evidence)
    - Filter by implementation scope (partial/full/conditional)
    - Find relationships with specific evidence types
    - Query by components and temporal information
    - Advanced relationship analytics

### Contextual Search (1 additional)

12. **contextual_search** - Scoped search within related memories
    - Two-phase search: find related memories, then search within that set
    - Semantic scoping without embeddings
    - Search within a specific problem context
    - Find solutions in related knowledge
    - No leakage outside context boundary

---

## Tool Categories

### By Functionality

| Category | Tools | Count | Profile |
|----------|-------|-------|---------|
| Memory CRUD | store_memory, get_memory, search_memories, update_memory, delete_memory | 5 | core |
| Relationships | create_relationship, get_related_memories | 2 | core |
| Discovery | recall_memories, get_recent_activity | 2 | core |
| Statistics | get_memory_statistics | 1 | extended |
| Advanced Queries | search_relationships_by_context | 1 | extended |
| Contextual Search | contextual_search | 1 | extended |

### By Use Case

| Use Case | Recommended Tools | Profile |
|----------|-------------------|---------|
| Store learnings | store_memory, create_relationship | core |
| Find past solutions | recall_memories, get_related_memories | core |
| Session briefing | get_recent_activity | core |
| Advanced search | search_memories, search_relationships_by_context | core, extended |
| Database insights | get_memory_statistics | extended |
| Complex analytics | search_relationships_by_context, get_memory_statistics | extended |
| Scoped discovery | contextual_search | extended |

---

## Choosing Your Profile

### Use **Core** Profile If:
- ✅ You're getting started
- ✅ You need basic memory storage and retrieval
- ✅ You want zero configuration
- ✅ You're a typical user (95% of use cases)
- ✅ You want the simplest setup

### Use **Extended** Profile If:
- ✅ You need database statistics
- ✅ You want advanced relationship queries
- ✅ You're analyzing patterns across large memory sets
- ✅ You need scope/evidence-based relationship filtering
- ✅ You want contextual/scoped search within related memories
- ✅ You're a power user who wants all capabilities

---

## Profile Configuration

### Environment Variable

```bash
# Core (default)
export MEMORY_TOOL_PROFILE=core

# Extended
export MEMORY_TOOL_PROFILE=extended
```

### CLI Flag

```bash
# Core (default)
memorygraph

# Extended
memorygraph --profile extended
```

### MCP Configuration

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "extended"],
      "env": {
        "MEMORY_BACKEND": "sqlite"
      }
    }
  }
}
```

---

## Backend Compatibility

| Backend | Compatible Tools | Notes |
|---------|------------------|-------|
| **SQLite** | All 12 tools | Default backend, zero configuration |
| **Neo4j** | All 12 tools | Requires setup, optimal for large graphs |
| **Memgraph** | All 12 tools | Requires setup, fastest analytics |

All profiles work with all backends. The profile controls *which tools are exposed*, not *which backend is used*.

---

## Migration from Legacy Profiles

Previous versions used three profiles (lite/standard/full). The system now uses two profiles (core/extended).

**Automatic Migration:**
- `lite` → `core` (9 tools)
- `standard` → `extended` (11 tools)
- `full` → `extended` (11 tools)

Legacy profile names are still supported but will be automatically mapped to the new profiles.

**What Changed:**
- **Removed**: 29 unimplemented "vaporware" tools (intelligence/integration/proactive) → moved to `experimental/`
- **Deferred**: 3 temporal MCP tools (still available via Python API) → saves ~3k tokens
- **Kept**: All 12 actually implemented and tested tools (9 core + 3 extended)
- **Fixed**: Added missing `contextual_search` to Extended profile
- **Simplified**: From 3 tiers to 2 tiers (Core/Extended)
- **Focused**: Core mode is now the default, works for 95% of users
- **Context Savings**: ~40-45k tokens (~60-70% reduction)

---

## Implementation Status

**Current Status (v0.10.0+)**
- ✅ All 12 tools fully implemented and tested
- ✅ 1,068 tests passing (29 vaporware tool tests moved to experimental/)
- ✅ Profile filtering system working
- ✅ Core/Extended profiles defined
- ✅ Legacy profile compatibility (lite/standard/full → core/extended)
- ✅ Context budget optimization complete (~40-45k tokens saved)

**Tools Removed/Deferred**
- **Removed (moved to experimental/)**: 29 vaporware tools
  - 7 intelligence tools (intelligence_tools.py)
  - 11 integration tools (integration_tools.py)
  - 11 proactive tools (proactive_tools.py)
- **Deferred (Python API only)**: 3 temporal MCP tools
  - query_as_of (backend method available)
  - get_relationship_history (backend method available)
  - what_changed (backend method available)
- **Retained in Extended**: contextual_search for scoped search use cases
- **Focus**: Stable, tested, production-ready tools only

---

## Tool Selection Guide

### For Search and Recall

**Primary tool**: `recall_memories`
- Best for: "What did we learn about X?"
- Features: Fuzzy matching, relationship context, match quality hints
- Use when: You want natural language search with smart defaults

**Secondary tool**: `search_memories`
- Best for: Exact matching, multi-term boolean queries
- Features: Full control, strict/normal/fuzzy modes, advanced filters
- Use when: You need precise control or recall_memories didn't find what you need

### For Relationships

**Primary tool**: `create_relationship`
- Creates links between memories (solution SOLVES problem, etc.)
- 35+ relationship types across 7 categories

**Secondary tool**: `get_related_memories`
- Explores connections by traversing relationships
- Filter by type, control depth

### For Session Context

**Primary tool**: `get_recent_activity`
- "Catch me up" functionality
- Shows recent work, unresolved problems
- Project-scoped summaries

### For Analytics (Extended only)

**Primary tool**: `get_memory_statistics`
- Database overview and metrics
- Breakdown by type, importance, etc.

**Secondary tool**: `search_relationships_by_context`
- Complex relationship queries
- Scope/evidence/condition filtering

---

**Last Updated**: December 7, 2025
**Total Implemented Tools**: 12 (9 core + 3 extended)
**Admin-Only Tools**: 5 (2 migration + 3 temporal backend methods)
**Profiles**: 2 (core/extended)
**Default Profile**: core
**Backends**: 3 (SQLite/Neo4j/Memgraph)
**Context Budget Impact**: ~40-45k tokens saved (60-70% reduction from previous 44 tools)
