# Context Budget Guidelines

**Created**: 2025-12-07
**Purpose**: Ensure MCP tool additions justify their context overhead

---

## Why Context Budget Matters

Every MCP tool consumes context tokens that could be used for:
- Conversation history
- File contents
- Reasoning about problems

Claude Code's context window is 200k tokens. At 50% utilization:
- 100k tokens available
- MCP tools currently use ~11k tokens (11%)
- Each new tool adds ~1-1.5k tokens

**Goal**: Keep total MCP overhead under 15% of context window.

---

## Current Tool Inventory

### Core Profile (9 tools, ~9.6k tokens)

| Tool | Tokens | Purpose |
|------|--------|---------|
| store_memory | ~1.2k | Store memories |
| get_memory | ~0.8k | Retrieve by ID |
| search_memories | ~1.5k | Advanced search |
| update_memory | ~0.7k | Update memories |
| delete_memory | ~0.6k | Delete memories |
| create_relationship | ~1.5k | Link memories |
| get_related_memories | ~1.2k | Traverse graph |
| recall_memories | ~1.2k | Natural language search |
| get_recent_activity | ~1.0k | Session briefing |

### Extended Profile (+3 tools, ~11k total)

| Tool | Tokens | Purpose |
|------|--------|---------|
| get_memory_statistics | ~0.8k | Database stats |
| search_relationships_by_context | ~0.9k | Complex queries |
| contextual_search | ~1.0k | Scoped search |

---

## Decision Framework

### Before Adding a New MCP Tool

```
1. ESTIMATE COST
   - Tool definition: ~1-1.5k tokens
   - New total: current + new tool
   - % of context: total / 200k

2. EVALUATE UNIQUENESS
   □ Can existing tools achieve this?
   □ Would a parameter on existing tool work?
   □ Is this truly new functionality?

3. ASSESS USAGE FREQUENCY
   □ Expected usage: >10% of sessions?
   □ Who benefits: all users or niche?
   □ Is this core workflow or edge case?

4. CALCULATE ROI
   Value score (1-10) / Token cost (k)
   - Must exceed 0.5 to proceed
   - 1.0+ = strong candidate
   - <0.5 = reject or defer
```

### Decision Matrix

| ROI Score | Uniqueness | Frequency | Decision |
|-----------|------------|-----------|----------|
| >1.0 | High | >20% | ✅ Add to Core |
| 0.7-1.0 | High | >10% | ✅ Add to Extended |
| 0.5-0.7 | Medium | >10% | ⚠️ Review carefully |
| <0.5 | Any | Any | ❌ Reject/Defer |
| Any | Low | <5% | ❌ Reject |

---

## Alternatives to New Tools

### 1. Add Parameter to Existing Tool
**Cost**: 0 tokens (description update only)

Example: Instead of `query_as_of` tool, add `as_of` parameter to `get_related_memories`.

### 2. Backend-Only Implementation
**Cost**: 0 tokens

Implement feature in Python API but don't expose as MCP tool. Available for programmatic use.

### 3. Combine with Existing Tool
**Cost**: ~0.2k tokens (description expansion)

Extend an existing tool's functionality rather than creating new one.

### 4. Documentation-Only
**Cost**: 0 tokens

Show users how to achieve result with existing tools via CLAUDE.md examples.

---

## Case Studies

### ❌ Rejected: browse_memory_types

| Criterion | Score | Notes |
|-----------|-------|-------|
| Token cost | 1.2k | Standard tool size |
| Uniqueness | Low | `search_memories` with type filter achieves same |
| Frequency | ~5% | Rarely needed |
| ROI | 0.3 | Value (4) / Cost (1.2k) |

**Decision**: Cut. Users can use `search_memories(memory_types=["solution"])`.

### ❌ Rejected: find_chain

| Criterion | Score | Notes |
|-----------|-------|-------|
| Token cost | 1.2k | Standard tool size |
| Uniqueness | Medium | `get_related_memories` with types achieves similar |
| Frequency | ~8% | Occasional use |
| ROI | 0.5 | Borderline |

**Decision**: Cut. Users can use `get_related_memories(relationship_types=["SOLVES"], max_depth=3)`.

### ✅ Kept: contextual_search

| Criterion | Score | Notes |
|-----------|-------|-------|
| Token cost | 1.0k | Slightly smaller |
| Uniqueness | High | Two-phase search is truly different |
| Frequency | ~15% | Regular use for scoped exploration |
| ROI | 0.9 | Good value |

**Decision**: Keep in Extended profile. Unique capability justifies cost.

---

## Review Triggers

Re-evaluate existing tools when:

1. **Usage data available**: If tool used <5% of sessions, consider removal
2. **New tool overlaps**: If new tool makes old one redundant
3. **Context pressure**: If users hitting context limits frequently
4. **Profile expansion**: Before adding to Core profile

---

## Workplan Integration

Every workplan proposing new MCP tools MUST include:

```markdown
## ⚠️ Context Budget Review

### Proposed Tools

| Tool | Est. Tokens | Unique? | Frequency | ROI |
|------|-------------|---------|-----------|-----|
| tool_name | ~X.Xk | H/M/L | X% | X.X |

### Alternatives Considered
- [ ] Parameter on existing tool?
- [ ] Backend-only?
- [ ] Combined with existing?

### Decision
[APPROVE/DEFER/REJECT with rationale]
```

---

## Historical Decisions

| Date | Workplan | Action | Tokens Saved |
|------|----------|--------|--------------|
| 2025-12-07 | 12 | Cut 5/6 navigation tools | ~5.5k |
| 2025-12-07 | 13 | Defer 3 temporal tools | ~3k (pending) |

---

**Remember**: The best tool is often no new tool at all.
