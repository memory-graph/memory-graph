# Tool Profiles Reference

This document provides a complete inventory of all 44 MCP tools in the Claude Code Memory Server, organized by profile tier.

## Profile Overview

| Profile | Tool Count | Description | Use Case |
|---------|------------|-------------|----------|
| **lite** | 8 | Core memory operations | Quick setup, basic memory needs |
| **standard** | 15 | Core + basic intelligence | Most users, balanced features |
| **full** | 44 | All features | Power users, advanced analytics |

---

## Lite Profile (8 tools)

**Zero-config default**. Provides essential memory operations with no external dependencies.

### Core Memory Operations (8 tools)

1. **store_memory** - Store a new memory with context and metadata
2. **get_memory** - Retrieve a specific memory by ID
3. **search_memories** - Search for memories based on various criteria
4. **update_memory** - Update an existing memory
5. **delete_memory** - Delete a memory and all its relationships

### Core Relationship Operations (3 tools)

6. **create_relationship** - Create a relationship between two memories
7. **get_related_memories** - Find memories related to a specific memory
8. **get_memory_statistics** - Get statistics about the memory database

---

## Standard Profile (15 tools)

**Lite + basic intelligence**. Adds pattern recognition and context retrieval without heavy dependencies.

### All Lite Tools (8)
- (See above)

### Intelligence Tools (7 additional)

9. **find_similar_solutions** - Find similar solutions to a given problem
10. **suggest_patterns_for_context** - Suggest patterns based on current context
11. **get_intelligent_context** - Get intelligent context for a query with token limiting
12. **get_project_summary** - Get a summary of project-related memories
13. **get_session_briefing** - Get a briefing of the current session
14. **get_memory_history** - Get the history of a memory over time
15. **track_entity_timeline** - Track timeline of entities across memories

---

## Full Profile (44 tools)

**All features enabled**. Requires Neo4j or Memgraph for full graph analytics capabilities.

### All Standard Tools (15)
- (See above)

### Advanced Relationship Tools (7 additional)

16. **find_memory_path** - Find the shortest path between two memories through relationships
17. **analyze_memory_clusters** - Detect clusters of densely connected memories
18. **find_bridge_memories** - Find memories that connect different clusters (knowledge bridges)
19. **suggest_relationship_type** - Get intelligent suggestions for relationship types between two memories
20. **reinforce_relationship** - Reinforce a relationship based on successful usage
21. **get_relationship_types_by_category** - List all relationship types in a specific category
22. **analyze_graph_metrics** - Get comprehensive graph analytics and metrics

### Integration Tools (11 additional)

23. **detect_project** - Detect project information from a directory
24. **analyze_project** - Analyze codebase structure and dependencies
25. **track_file_changes** - Track file changes in a project
26. **identify_patterns** - Identify code patterns in files
27. **capture_task** - Capture context about a task being worked on
28. **capture_command** - Capture command execution with results
29. **track_error_solution** - Track error patterns and their solutions
30. **track_workflow** - Track workflow actions in a session
31. **suggest_workflow** - Suggest workflow based on history
32. **optimize_workflow** - Optimize workflow based on performance data
33. **get_session_state** - Get current session state and suggestions

### Proactive Tools (11 additional)

34. **get_session_briefing** - Get AI-generated session briefing (duplicate name, proactive version)
35. **check_for_issues** - Check for potential issues in current context
36. **get_suggestions** - Get proactive suggestions for current work
37. **predict_solution_effectiveness** - Predict effectiveness of a solution
38. **find_similar_solutions** - Find similar solutions (duplicate name, proactive version)
39. **suggest_related_memories** - Suggest related memories proactively
40. **identify_knowledge_gaps** - Identify gaps in knowledge graph
41. **recommend_learning_paths** - Recommend learning paths based on goals
42. **record_outcome** - Record the outcome of an action for learning
43. **track_memory_roi** - Track return on investment for memories
44. **get_graph_visualization** - Get graph visualization data for frontend

---

## Tool Categories

### By Functionality

| Category | Tools | Profile |
|----------|-------|---------|
| Memory CRUD | 5 | lite |
| Relationships | 3 | lite |
| Statistics | 1 | lite |
| Pattern Recognition | 4 | standard |
| Context Retrieval | 3 | standard |
| Graph Analytics | 7 | full |
| Project Integration | 11 | full |
| Proactive Intelligence | 11 | full |

### By Backend Compatibility

| Backend | Compatible Tools | Notes |
|---------|------------------|-------|
| **SQLite** | All 44 tools | Some analytics may be slower on large graphs |
| **Neo4j** | All 44 tools | Optimal performance for graph operations |
| **Memgraph** | All 44 tools | Fastest graph analytics, best for full mode |

---

## Choosing Your Profile

### Use **Lite** Profile If:
- You want zero configuration
- You need basic memory storage and retrieval
- You're just getting started
- You have simple relationship tracking needs
- You prefer SQLite backend

### Use **Standard** Profile If:
- You need pattern recognition
- You want intelligent context suggestions
- You work on projects and want summaries
- You need session briefings
- You want more than basic search

### Use **Full** Profile If:
- You need advanced graph analytics
- You want workflow automation
- You need proactive suggestions
- You want to track code patterns
- You need project integration features
- You want visualization capabilities
- You're using Neo4j or Memgraph

---

## Profile Configuration

### Environment Variable

```bash
# Default (lite)
export MEMORY_TOOL_PROFILE=lite

# Standard
export MEMORY_TOOL_PROFILE=standard

# Full power
export MEMORY_TOOL_PROFILE=full
```

### CLI Flag

```bash
# Default (lite)
memorygraph

# Standard
memorygraph --profile standard

# Full
memorygraph --profile full --backend neo4j
```

### MCP Configuration

```json
{
  "mcpServers": {
    "memorygraph": {
      "command": "memorygraph",
      "args": ["--profile", "standard"],
      "env": {
        "MEMORY_BACKEND": "sqlite"
      }
    }
  }
}
```

---

## Implementation Status

**Phase 8.0 - Pre-flight Validation**
- ✅ Tool inventory complete (44 tools identified)
- ✅ Tool categories documented
- ✅ Profile tiers defined (lite/standard/full)
- ⏳ Currently only 15 tools registered in server.py (8 core + 7 advanced relationship)
- ⏳ Integration and proactive tools defined but not yet registered
- ⏳ Tool profiling system to be implemented in Phase 8.3

**Next Steps**
- Phase 8.3 will implement the profiling system
- All 44 tools will be registered with filtering
- Profile selection via env var or CLI flag

---

**Last Updated**: November 28, 2025
**Total Tools**: 44
**Profiles**: 3 (lite/standard/full)
**Backends**: 3 (SQLite/Neo4j/Memgraph)
