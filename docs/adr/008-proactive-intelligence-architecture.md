# ADR 008: Proactive Intelligence Architecture

**Status**: Accepted
**Date**: 2025-11-28
**Phase**: Phase 7 - Proactive Features & Advanced Analytics

## Context

As the memory server accumulates knowledge, it becomes valuable to proactively surface relevant information rather than waiting for explicit queries. Users benefit from:

- Automatic session briefings when starting work
- Predictive suggestions based on current context
- Warnings about deprecated approaches or known issues
- Learning from solution outcomes to improve recommendations
- Advanced analytics to understand knowledge patterns

The challenge is to implement these features in a way that is:
- Non-intrusive (helpful without being annoying)
- Evidence-based (all suggestions backed by data)
- Transparent (clear why suggestions are made)
- Backend-agnostic (works across Neo4j, Memgraph, SQLite)
- Performant (doesn't slow down development)

## Decision

We implement a layered proactive intelligence architecture with four main components:

### 1. Session Start Intelligence (`proactive/session_briefing.py`)

**Purpose**: Automatically provide relevant context when Claude Code starts

**Key Features**:
- Project detection (reuses Phase 6 integration)
- Recent activity summary (last 7 days by default)
- Unresolved problems identification
- Relevant pattern suggestions
- Deprecation warnings
- Configurable verbosity (minimal/standard/detailed)

**Implementation**:
```python
async def generate_session_briefing(
    backend: GraphBackend,
    project_dir: str,
    recency_days: int = 7,
    max_activities: int = 10,
) -> Optional[SessionBriefing]
```

**MCP Integration**:
- Tool: `get_session_briefing`
- Resource: `memory://session/briefing/{project_name}`

### 2. Predictive Suggestions (`proactive/predictive.py`)

**Purpose**: Suggest relevant information based on current work context

**Key Features**:
- Entity-based suggestion matching
- Pattern relevance scoring
- Related context discovery
- Issue warnings (deprecated approaches, known problems)

**Algorithms**:
```python
# Relevance scoring
relevance = (
    base_score +                              # Entity confidence
    (effectiveness * 0.3) +                    # Historical effectiveness
    min(usage_count / 10.0, 0.2) +            # Usage popularity
    min(effectiveness_links / 5.0, 0.2)        # Relationship evidence
)

# Capped at 1.0
relevance = min(relevance, 1.0)
```

**MCP Tools**:
- `get_suggestions` - Proactive suggestions
- `check_for_issues` - Issue warnings
- `suggest_related_memories` - "You might also want to know..."

### 3. Outcome Learning (`proactive/outcome_learning.py`)

**Purpose**: Track solution effectiveness and learn from outcomes

**Key Features**:
- Outcome recording (success/failure)
- Effectiveness score updates using Bayesian updating
- Pattern effectiveness propagation
- Designed decay mechanism (not yet implemented)

**Scoring Updates**:
```python
# Weighted average: recent outcome weighted by impact
if total_outcomes > 0:
    success_rate = successful_outcomes / total_outcomes
    new_effectiveness = (
        (success_rate * (1 - impact)) +
        (1.0 if success else 0.0) * impact
    )

# Confidence increases with more outcomes
confidence = min(0.9, 0.3 + (total_outcomes / 20.0) * 0.6)
```

**Pattern Propagation**:
- Solutions propagate to related patterns with dampening (30% rate)
- Prevents over-reaction to individual failures
- Builds pattern confidence over time

**MCP Tool**:
- `record_outcome` - Record solution results

### 4. Advanced Analytics (`analytics/advanced_queries.py`)

**Purpose**: Provide insights into the knowledge graph structure

**Key Features**:
- Graph visualization data (D3/vis.js compatible)
- Solution similarity analysis (Jaccard similarity)
- Solution effectiveness prediction
- Learning path recommendations
- Knowledge gap identification
- Memory ROI tracking

**MCP Tools**:
- `get_graph_visualization` - Export graph for visualization
- `find_similar_solutions` - Find similar approaches
- `predict_solution_effectiveness` - Predict success rate
- `recommend_learning_paths` - Suggest learning sequences
- `identify_knowledge_gaps` - Find documentation gaps
- `track_memory_roi` - Track memory value

## Architecture Principles

### 1. Evidence-Based Suggestions

All suggestions must be backed by concrete data:
- Entity matches from entity extraction (Phase 5)
- Relationship strengths from graph analytics (Phase 4)
- Historical effectiveness from outcome tracking
- Usage statistics from memory access patterns

### 2. Transparent Reasoning

Each suggestion includes:
- `relevance_score` - Numeric score (0.0-1.0)
- `reason` - Human-readable explanation
- `evidence` - Source memories or relationships

Example:
```python
Suggestion(
    title="JWT authentication pattern",
    relevance_score=0.85,
    reason="Related to technology: JWT",
    evidence=["mem_123", "mem_456"],
)
```

### 3. Configurable Intrusiveness

Users control how proactive the system is:
- `min_relevance` threshold filters low-confidence suggestions
- `severity_threshold` controls warning sensitivity
- `verbosity` level (minimal/standard/detailed) for briefings

### 4. Performance Considerations

- Session briefings limited to recent data (default 7 days)
- Query result limits (max_suggestions, max_activities)
- Entity extraction limits (top 10 entities)
- Graph traversal depth limits

### 5. Backend Agnostic

All features work across all backends:
- Use `GraphBackend.execute_query()` exclusively
- No Neo4j-specific syntax
- Graceful handling of missing features
- Consistent Cypher queries

## Module Organization

```
src/claude_memory/
├── proactive/
│   ├── __init__.py
│   ├── session_briefing.py      # Session start intelligence
│   ├── predictive.py             # Predictive suggestions
│   └── outcome_learning.py       # Outcome tracking
├── analytics/
│   ├── __init__.py
│   └── advanced_queries.py       # Advanced analytics
└── proactive_tools.py            # MCP tool handlers
```

## Integration Points

### With Phase 5 (Intelligence Layer)
- Reuses entity extraction for context matching
- Uses pattern recognition for suggestions
- Leverages context retrieval for briefings

### With Phase 6 (Claude Code Integration)
- Reuses `detect_project()` for project identification
- Builds on workflow tracking for activity summaries
- Extends context capture with outcome learning

### With Phase 4 (Relationships)
- Uses relationship strength for relevance scoring
- Leverages DEPRECATED_BY for warnings
- Analyzes relationship patterns for suggestions

## Future Enhancements

### Implemented in Phase 7
- ✅ Session briefing generation
- ✅ Predictive suggestions
- ✅ Outcome learning
- ✅ Advanced analytics queries
- ✅ Graph visualization data export

### Designed But Not Implemented
- ⏳ Effectiveness decay mechanism (documented in code)
- ⏳ ML-based suggestion ranking
- ⏳ Automatic pattern mining
- ⏳ Real-time issue prediction

### Future Phases
- Team analytics (multi-user)
- A/B testing for patterns
- Advanced visualization APIs
- Recommendation engine tuning

## Performance Impact

**Benchmarks** (estimated):
- Session briefing: <500ms (typical project)
- Prediction needs: <200ms per query
- Record outcome: <100ms
- Graph visualization: <1s for 100 nodes

**Optimizations**:
- Query result limits prevent unbounded growth
- Entity extraction capped at top 10
- Pattern matching uses indexed queries
- Effectiveness updates batched per outcome

## Testing Strategy

**Coverage**: 87% (55 tests passing)

**Test Categories**:
1. Unit tests for models (Pydantic validation)
2. Function tests for algorithms (mocked backend)
3. Integration tests for workflows (end-to-end)
4. Edge case tests (empty results, errors)

**Key Test Areas**:
- Session briefing with various project states
- Suggestion relevance filtering
- Outcome effectiveness updates
- Analytics query accuracy

## Consequences

### Positive

1. **Improved Developer Experience**: Automatic context reduces cognitive load
2. **Learning System**: Gets smarter over time with outcome tracking
3. **Proactive Help**: Catches issues before they become problems
4. **Knowledge Discovery**: Analytics reveal patterns in the graph
5. **Evidence-Based**: All suggestions backed by data

### Negative

1. **Complexity**: Additional moving parts to maintain
2. **Performance**: Extra queries on session start
3. **Tuning Required**: Thresholds may need adjustment per project
4. **False Positives**: May suggest irrelevant information

### Mitigations

- Configurable thresholds allow tuning
- Query limits prevent performance degradation
- Transparent scoring allows debugging
- Can disable proactive features if too intrusive

## Related ADRs

- [ADR 006](006-intelligence-layer-architecture.md) - Entity extraction foundation
- [ADR 007](007-claude-code-integration-architecture.md) - Project detection
- [ADR 004](004-advanced-relationship-system.md) - Relationship strength

## References

- Phase 7 implementation: `src/claude_memory/proactive/`
- Tests: `tests/proactive/`, `tests/analytics/`
- MCP tools: `src/claude_memory/proactive_tools.py`
- Enhancement plan: `docs/enhancement-plan.md` (Phase 7)
