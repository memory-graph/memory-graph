# Documentation Archive

This directory contains historical documentation that has been superseded by more current documents but is preserved for reference.

## Active Documents

**For current project status and active work**, see:
- `/docs/WORKPLAN.md` - Current Phase 8 tasks and execution plan
- `/docs/` - Current documentation (API, architecture, guides)

## Archived Documents

### completed_phases.md
**Archived**: November 28, 2025
**Purpose**: Complete history of Phases 0-7 implementation
**Supersedes**: Individual phase documentation from enhancement-plan.md
**Contents**:
- Phase 0: Project Management Setup
- Phase 1: Foundation Setup
- Phase 2: Core Memory Operations
- Phase 2.5: Technical Debt Resolution
- Phase 3: Multi-Backend Support
- Phase 4: Advanced Relationship System
- Phase 5: Intelligence Layer
- Phase 6: Claude Code Integration
- Phase 7: Proactive Features & Advanced Analytics

**Why archived**: All phases complete, now historical reference only.

### enhancement-plan.md
**Archived**: November 28, 2025 (automatically by user request)
**Purpose**: Original comprehensive 8-phase implementation plan
**Superseded by**:
- Phases 0-7: `completed_phases.md` (historical record)
- Phase 8: `/docs/WORKPLAN.md` (active tasks)

**Contents**:
- All 8 phases with detailed task breakdowns
- 1,838 lines of comprehensive planning
- Original source of truth for project roadmap

**Why archived**:
- Document already had archive notice (lines 3-10)
- Content fully duplicated in better-organized documents
- Potential source of confusion with multiple planning documents
- Preserved for historical reference and architecture decisions

### deployment_strategy.md
**Archived**: November 28, 2025 (automatically by user request)
**Purpose**: Strategic analysis of deployment friction and two-tier approach
**Superseded by**: `/docs/WORKPLAN.md` Phase 8 (lines 20-28, deployment strategy section)

**Contents**:
- Friction point analysis
- Two-tier deployment strategy (Zero Config vs Full Power)
- Immediate action plan for PyPI publishing
- Tool profiling recommendations

**Why archived**:
- All actionable tasks merged into WORKPLAN.md Phase 8
- Strategic rationale now documented in active workplan
- Zero references from other documents
- Preserved for strategic thinking reference

### PHASE4_RELATIONSHIP_SYSTEM.md
**Status**: Archived (completed phase documentation)
**Purpose**: Detailed Phase 4 completion report
**Reference**: Links updated to point to `completed_phases.md#phase-4`

## Using This Archive

### When to Use Archived Docs
- Understanding historical design decisions
- Reviewing completed phase implementations
- Researching original planning rationale
- Comparing original plan vs actual implementation

### When NOT to Use Archived Docs
- **Current work**: Use `/docs/WORKPLAN.md` instead
- **Feature documentation**: Use main `/docs` directory
- **API reference**: Use current API docs
- **Setup guides**: Use current setup documentation

## Archive Index

| Document | Archived Date | Lines | Superseded By | Reason |
|----------|---------------|-------|---------------|--------|
| `completed_phases.md` | 2025-11-28 | 803 | N/A (historical) | Phase completion archive |
| `enhancement-plan.md` | 2025-11-28 | 1,838 | WORKPLAN.md + completed_phases.md | Duplicate content |
| `deployment_strategy.md` | 2025-11-28 | 339 | WORKPLAN.md Phase 8 | Strategy merged |
| `PHASE4_RELATIONSHIP_SYSTEM.md` | 2025-11-28 | 391 | completed_phases.md | Completion report |

## Document Lifecycle

```
Planning Document → Active Workplan → Completion Archive
        ↓                ↓                    ↓
enhancement-plan.md  WORKPLAN.md      completed_phases.md
deployment_strategy  (Phase 8)        (Phases 0-7)
```

## Navigation

- **Current work**: [../WORKPLAN.md](../WORKPLAN.md)
- **Main docs**: [../ (docs/)](../)
- **Project root**: [../../README.md](../../README.md)

---

**Last Updated**: November 28, 2025
**Maintainer**: Archive created during Phase 8 documentation cleanup
