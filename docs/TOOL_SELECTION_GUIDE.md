# Tool Selection Guide for Claude

**Date**: December 1, 2025
**Purpose**: Guide Claude's tool selection for optimal memory operations
**Audience**: Internal reference for Claude and developers

---

## Tool Hierarchy

Claude should follow this decision tree when working with memories:

```
User Request
│
├─ Recall/Search Query? → START WITH recall_memories
│  ├─ Results found? → Use get_memory or get_related_memories for details
│  └─ No results? → Try search_memories with different parameters
│
├─ Store New Information? → START WITH store_memory
│  └─ After storing? → Use create_relationship to link related memories
│
├─ Explore Connections? → START WITH get_related_memories
│  └─ For specific memory ID
│
├─ Update/Delete? → get_memory first, then update_memory or delete_memory
│
└─ Overview/Stats? → get_memory_statistics
```

---

## Primary Tools (Use First)

### 1. recall_memories 🎯 RECOMMENDED FIRST CHOICE

**Use for**:
- Any recall or search query from user
- "What did we learn about X?"
- "Show me solutions for Y"
- "Catch me up on this project"

**Why first**:
- Optimized defaults (fuzzy matching, relationships included)
- Simpler interface for natural language queries
- Best results for common use cases

**When to skip**:
- Need exact match only → use search_memories with search_tolerance="strict"
- Need advanced boolean queries → use search_memories
- Need multi-term queries → use search_memories (when Phase 2.D complete)

### 2. store_memory

**Use for**:
- Capturing new solutions, problems, errors, decisions
- Recording patterns or learnings
- Documenting technology choices

**Always follow with**:
- create_relationship to link to related memories

### 3. create_relationship

**Use for**:
- After storing a solution → link to problem it solves
- After documenting an error → link to its fix
- Connecting decisions to what they improve

**Common patterns**:
- solution SOLVES problem
- fix ADDRESSES error
- decision IMPROVES previous_approach
- pattern APPLIES_TO project

---

## Secondary Tools (Drill-Down)

### 4. search_memories

**Use when recall_memories isn't suitable**:
- Need strict exact matching (search_tolerance="strict")
- Need to search with specific tags
- Need to filter by importance threshold
- Advanced queries requiring fine control

**Don't use when**:
- Starting a search (use recall_memories instead)
- Unless you need specific search parameters

### 5. get_memory

**Use for**:
- Getting full details when you have a specific ID
- Verifying memory before update/delete
- Drilling down from search results

**Don't use for**:
- Initial search (use recall_memories instead)
- When you don't have an ID

### 6. get_related_memories

**Use for**:
- After finding a memory, explore what connects to it
- "What caused this problem?"
- "What solutions exist for this?"
- Following chains of reasoning

**Filter by relationship types** when you know what you're looking for:
- relationship_types=["SOLVES"] → Find solutions
- relationship_types=["CAUSES", "TRIGGERS"] → Find causes
- relationship_types=["USED_IN"] → Find where pattern applies

### 7. search_relationships_by_context (Advanced)

**Use for**:
- Complex conditional queries
- Finding relationships with specific context (scope, conditions, evidence)
- Advanced graph queries

**Don't use for**:
- Simple recall queries
- Unless you specifically need structured context filtering

---

## Utility Tools (Supporting)

### 8. update_memory

**Use for**:
- Corrections or enrichments
- Adding tags or updating importance

**Always**:
- Use get_memory first to verify contents
- Only update necessary fields

### 9. delete_memory

**Use for**:
- Removing obsolete or incorrect memories

**Warning**:
- Deletes all relationships too (cascade)
- Irreversible
- Prefer update_memory for corrections

### 10. get_memory_statistics

**Use for**:
- Overview of memory database
- "Catch me up" on what's been stored
- Understanding memory distribution by type

---

## Common User Patterns

### Pattern: User Asks "What did we learn about X?"

**Decision Tree**:
1. **Start**: recall_memories(query="X")
2. **Results found?**
   - Yes → Present results, offer to explore connections
   - No → Try search_memories with different terms or broader filters
3. **User wants details?** → get_memory(memory_id="...")
4. **User wants connections?** → get_related_memories(memory_id="...")

**Example**:
```
User: "What timeouts have we fixed?"

Step 1: recall_memories(query="timeout", memory_types=["solution", "fix"])
Step 2: [Present results]
Step 3 (if user asks): get_memory(memory_id="timeout-solution-123")
Step 4 (if user asks): get_related_memories(memory_id="timeout-solution-123", relationship_types=["SOLVES"])
```

---

### Pattern: User Solves a Problem

**Decision Tree**:
1. **Store solution**: store_memory(type="solution", title="...", content="...")
2. **Search for related problem**: recall_memories(query="related problem terms")
3. **Create link**: create_relationship(from_memory_id="solution", to_memory_id="problem", relationship_type="SOLVES")

**Example**:
```
User: "I fixed the Redis timeout by increasing connection timeout to 5 seconds"

Step 1: store_memory(
    type="solution",
    title="Fixed Redis timeout with 5s connection timeout",
    content="...",
    tags=["redis", "timeout", "connection"]
)
→ Returns memory_id: "sol-123"

Step 2: recall_memories(query="Redis timeout", memory_types=["problem", "error"])
→ Finds memory_id: "prob-456" (Redis timeout problem)

Step 3: create_relationship(
    from_memory_id="sol-123",
    to_memory_id="prob-456",
    relationship_type="SOLVES"
)
```

---

### Pattern: User Asks "Why did we choose X?"

**Decision Tree**:
1. **Search for decision**: recall_memories(query="X decision", memory_types=["decision"])
2. **Get details**: get_memory(memory_id="decision-123")
3. **Explore context**: get_related_memories(memory_id="decision-123")
   - Look for IMPROVES relationships (what it improved)
   - Look for REPLACES relationships (what it replaced)

---

### Pattern: User Asks "Catch me up"

**Decision Tree**:
1. **Get stats**: get_memory_statistics()
2. **Get recent activity**: recall_memories(project_path="/current/project", limit=10)
3. **For each recent item**: Show title, type, context_summary

**Future Enhancement (Phase 2.E)**:
- get_recent_activity(days=7, project="/current") will replace steps 1-2

---

## Tool Selection Metrics

### Success Metrics

After Phase 2.C implementation, measure:

- **Tool selection accuracy**: >90% (Claude uses correct tool first try)
- **Tools per recall**: 1-2 average (down from 3-4 currently)
- **Failed searches**: <10% (searches return no results)
- **User satisfaction**: Fewer "Claude couldn't find it" reports

### Anti-Patterns to Avoid

**❌ Don't**:
- Use search_memories when recall_memories would work
- Call get_memory without an ID
- Create memory without considering relationships
- Use exact match search as default

**✅ Do**:
- Start with recall_memories for all searches
- Use create_relationship after storing related memories
- Filter by memory_types for precision
- Use get_related_memories to explore context

---

## Tool Profiles and Availability

MemoryGraph supports three tool profiles:

### Core Profile (9 tools)
- recall_memories ✅
- store_memory ✅
- get_memory ✅
- search_memories ✅
- update_memory ✅
- delete_memory ✅
- create_relationship ✅
- get_related_memories ✅

**Best for**: Most users, covers 90% of use cases

### Extended Profile (11 tools)
- All lite tools
- get_memory_statistics ✅
- search_relationships_by_context ✅
- Advanced relationship tools (7 tools)

**Best for**: Power users needing advanced queries

### Extended Profile (11 tools)
- All standard tools
- Intelligence tools (7 tools)
- Integration tools (11 tools)
- Proactive tools (9 tools)

**Best for**: Enterprise users, complex workflows, advanced automation

---

## Future Enhancements

### Phase 2.D: Multi-Term Search (In Progress)

When complete, search_memories will support:
- Multiple search terms: `terms=["Redis", "timeout", "fix"]`
- Match modes: `match_mode="all"` (AND) or `match_mode="any"` (OR)
- Boolean operators: `query="Redis AND timeout NOT OAuth"`
- Relationship filters: `relationship_filter="SOLVES"`

**Impact on tool selection**:
- recall_memories remains primary tool
- search_memories becomes more powerful for complex queries

### Phase 2.E: Session Briefing (Planned)

New tool: `get_recent_activity(days=7, project="/path")`

**Impact on tool selection**:
- Preferred over get_memory_statistics for "catch me up" queries
- Auto-detects project context
- Focuses on what's relevant now

---

## Implementation Notes

### For Developers

**Tool descriptions follow this format**:
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

RETURNS:
- [What the tool returns]
```

**Adding new tools**:
1. Follow the description format
2. Place in appropriate hierarchy (primary/secondary/utility)
3. Update this guide
4. Add usage examples
5. Test with Claude in realistic scenarios

### For Claude

**Key principles**:
1. **Start simple**: Use recall_memories unless there's a specific reason not to
2. **Follow chains**: Store → Link → Recall
3. **Provide context**: Always show relationship context in results
4. **Offer next steps**: After presenting results, suggest how to explore further

---

## Related Documentation

- `/docs/TOOL_DESCRIPTION_AUDIT.md` - Detailed audit of all tool descriptions
- `/docs/planning/WORKPLAN.md` - Phase 2.C implementation details
- `/docs/PRODUCT_ROADMAP.md` - "Claude as Semantic Layer" architecture
- `/README.md` - User-facing tool documentation

---

**Last Updated**: December 1, 2025
**Version**: 1.0 (Phase 2.C completion)
**Next Review**: After Phase 2.D completion (multi-term search)
