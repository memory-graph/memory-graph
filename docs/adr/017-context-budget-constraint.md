# ADR 017: Context Budget as First-Class Architectural Constraint

**Status**: Accepted
**Date**: 2025-12-07
**Deciders**: Architecture Review
**Priority**: CRITICAL

---

## Context

During an architectural review, we discovered that MemoryGraph's MCP tool set had grown to include 44 documented tools, but only 13 were actually implemented and tested. The remaining 31 "vaporware" tools existed in code but:

1. Were never registered as working MCP tools
2. Lacked backend implementations
3. Had no tests
4. Consumed ~35-45k context tokens
5. Created confusion about available functionality

**The Problem**: Context budget is a scarce resource in LLM interactions. Every token of tool description competes with:
- User conversation history
- Code context
- Memory search results
- Actual work to be done

**The Discovery**: By removing vaporware and deferring low-usage tools, we could save ~40-45k tokens (~20-25% of typical context budget) with zero loss of functionality.

---

## Decision

We establish **context budget as a first-class architectural constraint** for MemoryGraph.

### Core Principle

**Every MCP tool must justify its context cost through demonstrated value.**

### Rules for Tool Management

#### 1. Tool Addition Rules

New tools must satisfy ALL of:
- **Implemented**: Full backend implementation exists
- **Tested**: 90%+ test coverage on critical paths
- **Documented**: Clear use cases and examples
- **Cost justified**: Context cost (usually ~1-1.5k tokens) is justified by expected usage frequency

**Decision Framework**:
```
Expected Usage Frequency × Value per Use ≥ Context Cost

Where:
- Daily use → High value (always justify ~1.5k tokens)
- Weekly use → Medium value (justify if unique functionality)
- Monthly use → Low value (must be exceptional to justify)
- Rare use → Defer (use Python API instead)
```

#### 2. Tool Profile Strategy

Maintain TWO profiles only:
- **Core** (default): Essential daily operations (9 tools)
- **Extended**: Core + analytics + advanced queries (12 tools)

**No "Full" profile**: Forces deliberate tool selection rather than "give me everything."

#### 3. Low-Usage Tool Policy

Tools with <5% session usage should be:
1. Available via **Python API** (no functionality lost)
2. **Not exposed as MCP tools** (save context)
3. **Documented in ADMIN_TOOLS.md** (discoverable)

Examples: Migration tools, temporal point-in-time queries.

#### 4. Vaporware Policy

Unimplemented or untested tools:
1. **Remove from active codebase** (move to `experimental/`)
2. **Document removal** (preserve institutional knowledge)
3. **May be completed later** (if justified)
4. **Never documented as available** (honesty with users)

---

## Implementation

### Immediate Actions Taken

1. **Removed 29 vaporware tools** (~35-45k tokens saved):
   - 7 intelligence tools → `experimental/intelligence_tools.py`
   - 11 integration tools → `experimental/integration_tools.py`
   - 11 proactive tools → `experimental/proactive_tools.py`

2. **Deferred 3 temporal MCP tools** (~3k tokens saved):
   - `query_as_of` → Backend method only
   - `get_relationship_history` → Backend method only
   - `what_changed` → Backend method only
   - Rationale: <5% expected usage, Python API sufficient

3. **Fixed Extended profile**:
   - Added missing `contextual_search` (was implemented but not in profile)
   - Now correctly advertises 12 tools (9 core + 3 advanced)

4. **Created documentation**:
   - `docs/ADMIN_TOOLS.md` - Documents admin-only tools
   - `experimental/README.md` - Explains moved tools
   - Updated `docs/TOOL_PROFILES.md` - Accurate tool counts

### Result

**Before**:
- 44 documented tools (31 vaporware)
- ~60-70k context tokens for tool descriptions
- Confusion about what's actually available

**After**:
- 12 implemented, tested, production-ready tools
- ~15-20k context tokens for tool descriptions
- Clear documentation of what works

**Net Savings**: ~40-45k context tokens (~60-70% reduction)

---

## Alternatives Considered

### Alternative 1: Implement All 44 Tools

**Rejected** because:
- Would require ~200-300 hours of development
- Many tools have unclear value propositions
- Would still consume ~60-70k tokens
- Better to focus on proven, high-value tools

### Alternative 2: Keep Tools But Don't Register Them

**Rejected** because:
- Code maintenance burden without benefit
- Creates confusion (code exists but doesn't work)
- Violates "working software over comprehensive documentation"

### Alternative 3: Single Profile With All Tools

**Rejected** because:
- Forces all users to pay context cost for tools they don't need
- 95% of users only need core operations
- Power users can opt into Extended profile

### Alternative 4: Dynamic Tool Loading

**Rejected** because:
- Adds complexity to tool system
- MCP protocol expects static tool list
- Savings are one-time (at connection initialization)

---

## Consequences

### Positive

1. **Dramatic context savings**: ~40-45k tokens freed for actual work
2. **Faster tool loading**: Fewer tools to process and understand
3. **Clearer documentation**: Only document what actually works
4. **Better user experience**: No confusion about vaporware
5. **Architectural discipline**: Forces cost-benefit analysis for new tools
6. **Focus on quality**: Better to have 12 great tools than 44 mediocre ones

### Negative

1. **Reduced feature surface**: Some planned features indefinitely delayed
2. **Migration effort**: Moving tools to experimental/, updating docs
3. **User communication**: Need to explain why tools were removed
4. **Future decisions**: Every new tool faces higher scrutiny

### Neutral

1. **No functionality lost**: All removed tools were non-functional
2. **Python API preserved**: Temporal tools still available programmatically
3. **Can be reversed**: Experimental tools can be completed if justified

---

## Metrics

### Context Budget Impact

| Category | Before | After | Savings |
|----------|--------|-------|---------|
| Vaporware tools | 31 tools (~35-45k tokens) | 0 tools | ~35-45k |
| Temporal MCP tools | 3 tools (~3k tokens) | 0 tools | ~3k |
| **Total Savings** | - | - | **~38-48k tokens** |

### Tool Count Impact

| Profile | Before (Documented) | Before (Working) | After | Change |
|---------|---------------------|------------------|-------|--------|
| Core | "9" (actually 9) | 9 | 9 | ✅ Same |
| Extended | "11" (missing contextual_search) | 11 | 12 | ✅ Fixed |
| Full | "44" (31 vaporware) | 13 | N/A | ❌ Removed |

### Code Quality Impact

| Metric | Before | After |
|--------|--------|-------|
| Test coverage (core tools) | 90%+ | 90%+ |
| Test coverage (all tools) | ~30% (31 untested) | 90%+ |
| Working/Documented ratio | 29% (13/44) | 100% (12/12) |

---

## Decision Framework for Future Tools

When proposing a new MCP tool, ask:

### 1. Is it implemented and tested?
- ❌ No → Don't document, don't add to profiles
- ✅ Yes → Continue to next question

### 2. What's the expected usage frequency?
- 📅 Daily (>50% of sessions) → Strong candidate
- 📅 Weekly (>20% of sessions) → Good candidate if unique value
- 📅 Monthly (>5% of sessions) → Weak candidate, needs exceptional value
- 📅 Rare (<5% of sessions) → Consider Python API only

### 3. Can existing tools handle this?
- ✅ Yes → Don't add (use existing tool or extend it)
- ❌ No → Continue to next question

### 4. What's the context cost?
- Simple tool (~500-800 tokens) → Lower bar
- Standard tool (~1-1.5k tokens) → Normal bar
- Complex tool (~2-3k tokens) → Higher bar, needs strong justification

### 5. Which profile should include it?
- Essential for 95% of users → **Core**
- Analytics/advanced queries → **Extended**
- Admin/rare operations → **Admin-only** (Python API)

### Example Application

**Proposed Tool**: `find_circular_dependencies`

1. ✅ Implemented and tested
2. 📅 Monthly usage (~8% of sessions)
3. ❌ Can't be done with existing tools
4. ~1.2k tokens (standard)
5. Analytics → **Extended profile**

**Decision**: **ACCEPT** for Extended profile (analytics use case, can't be done otherwise)

---

**Proposed Tool**: `export_to_graphml`

1. ✅ Implemented and tested
2. 📅 Rare usage (<2% of sessions)
3. ❌ Can't be done with existing tools
4. ~1.5k tokens (standard)
5. Admin operation → **Admin-only**

**Decision**: **ACCEPT** as Python API only, document in ADMIN_TOOLS.md (saves 1.5k tokens)

---

## Related ADRs

- [ADR-001: Multi-Backend Architecture](001-multi-backend-architecture.md) - Why we support multiple backends
- [ADR-015: Tool Profiles](015-tool-profiles.md) - Core/Extended/Full strategy (Full now removed)
- [ADR-016: Bi-Temporal Tracking](016-bi-temporal-tracking.md) - Why temporal tools exist (deferred as MCP)

---

## References

- [Architect Review Report](../reviews/2025-12-07-context-budget-review.md) - Detailed findings
- [TOOL_PROFILES.md](../TOOL_PROFILES.md) - Final tool inventory
- [ADMIN_TOOLS.md](../ADMIN_TOOLS.md) - Admin-only tools documentation
- [experimental/README.md](../../experimental/README.md) - Vaporware tools explanation

---

**Last Updated**: 2025-12-07
**Next Review**: 2026-01-07 (1 month) - Evaluate if any experimental tools should be completed
**Status**: ✅ Accepted and Implemented
