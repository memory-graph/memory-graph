# MemoryGraph Workplan Index

**Last Updated**: 2025-12-08
**Current Version**: v0.10.0 (ready for release)
**Test Status**: 1,068 tests passing
**Purpose**: Central index for all workplans organized by priority and dependency

> **Note**: Completed and deprecated workplans have been moved to `/docs/archive/` for reference.

---

## ⚠️ Context Budget Principle (2025-12-07)

**Every MCP tool must justify its context overhead.**

| Metric | Budget |
|--------|--------|
| MCP tool definition | ~1-1.5k tokens each |
| Current total (Core) | ~9.6k tokens (9 tools) |
| Current total (Extended) | ~11k tokens (12 tools) |
| Target overhead | <15% of context window |

### Before Adding New MCP Tools

1. **Estimate cost**: ~1-1.5k tokens per tool
2. **Evaluate uniqueness**: Does this duplicate existing functionality?
3. **Assess frequency**: Expected usage > 10% of sessions?
4. **Calculate ROI**: value / context_cost > 0.5

### Recent Decisions

- **12-WORKPLAN**: Cut 5/6 navigation tools (saved ~5.5k tokens)
- **13-WORKPLAN**: MCP tools deferred pending usage review

---

## Overview

Workplans are numbered and organized for sequential execution by coding agents. Each workplan is designed to be:
- **Readable in one session** (~130-500 lines)
- **Self-contained** with clear prerequisites
- **Actionable** with markdown checkboxes
- **File-specific** with absolute paths where relevant
- **Context-aware** with MCP tool budgets considered

---

## Workplan Structure

### Marketing & Distribution

**[0-WORKPLAN-MARKETING.md](0-WORKPLAN-MARKETING.md)** - Marketing & Distribution (180 lines)
- Submit to official MCP servers repo
- Submit to awesome-mcp-servers lists
- Reddit/Twitter/HN launch announcements
- Community monitoring and engagement
- **Priority**: HIGH (can run parallel with development)
- **Prerequisites**: None
- **Tasks**: 25+

### Foundation (v0.9.x) - ARCHIVED ✅

> **All foundation workplans (1-5, 8-13) completed and moved to `/docs/archive/`**

| Workplan | Title | Status | Completed |
|----------|-------|--------|-----------|
| [1-WORKPLAN](../archive/1-WORKPLAN.md) | Critical Fixes | ✅ COMPLETE | 2025-12-04 |
| [2-WORKPLAN](../archive/2-WORKPLAN.md) | Test Coverage | ✅ COMPLETE | 2025-12-04 |
| [3-WORKPLAN](../archive/3-WORKPLAN.md) | Code Quality | ✅ COMPLETE | 2025-12-04 |
| [4-WORKPLAN](../archive/4-WORKPLAN.md) | Server Refactoring | ✅ COMPLETE | 2025-12-04 |
| [5-WORKPLAN](../archive/5-WORKPLAN.md) | Pagination & Cycles | ✅ COMPLETE | 2025-12-04 |
| [8-WORKPLAN](../archive/8-WORKPLAN.md) | Claude Code Web | ✅ COMPLETE | 2025-12-03 |
| [9-WORKPLAN](../archive/9-WORKPLAN.md) | Universal Export | ✅ COMPLETE | 2025-12-04 |
| [10-WORKPLAN](../archive/10-WORKPLAN.md) | Migration Manager | ✅ COMPLETE | 2025-12-04 |
| [11-WORKPLAN](../archive/11-WORKPLAN.md) | MCP Migration Tools | ✅ COMPLETE | 2025-12-04 |
| [12-WORKPLAN](../archive/12-WORKPLAN.md) | Semantic Navigation | ✅ COMPLETE | 2025-12-07 |
| [13-WORKPLAN](../archive/13-WORKPLAN.md) | Bi-Temporal Schema | ✅ COMPLETE | 2025-12-07 |

### Deprecated Workplans - ARCHIVED ❌

> **Moved to memorygraph.dev repository or superseded**

| Workplan | Title | Status | Reason |
|----------|-------|--------|--------|
| [7-WEBSITE-WORKPLAN](../archive/7-WEBSITE-WORKPLAN.md) | Website | ❌ DEPRECATED | Merged into 17 |
| [14-WORKPLAN](../archive/14-WORKPLAN.md) | Cloud Infrastructure | ❌ DEPRECATED | → memorygraph.dev |
| [15-WORKPLAN](../archive/15-WORKPLAN.md) | Authentication | ❌ DEPRECATED | → memorygraph.dev |
| [17-WORKPLAN](../archive/17-WORKPLAN.md) | Marketing Site | ❌ DEPRECATED | → memorygraph.dev |
| [18-WORKPLAN](../archive/18-WORKPLAN.md) | Team Sync | ❌ DEPRECATED | → memorygraph.dev |

### Active Workplans

> **Note**: Cloud infrastructure is managed in the separate **memorygraph.dev** repository.

**[20-WORKPLAN-cloud-backend.md](20-WORKPLAN-cloud-backend.md)** - MCP Cloud Backend Adaptation - **IMPLEMENTATION COMPLETE** ✅
- Cloud backend fully implemented (`src/memorygraph/backends/cloud_backend.py`)
- Integrates with Graph API at `https://graph-api.memorygraph.dev`
- Comprehensive test suite (unit, integration, e2e)
- Release preparation pending (PyPI, Docker, documentation updates)
- **Status**: IMPLEMENTATION COMPLETE (Sections 1-6), RELEASE PENDING (Sections 7-8)
- **Prerequisites**: Graph Service deployed (memorygraph.dev)
- **Reference**: Moved from memorygraph.dev/docs/planning/5-WORKPLAN-mcp-integration.md
- **Tasks**: 100+ (core implementation complete)

**[16-WORKPLAN.md](16-WORKPLAN.md)** - SDK Development (v1.0.0) - ⏸️ **DEFERRED**
- Create memorygraphsdk Python package
- LangChain, CrewAI, AutoGen integrations
- Publish to PyPI
- **Priority**: HIGH (Competitive Differentiation vs Cipher) - DEFERRED
- **Status**: Deferred pending v0.10.0 release and WP20 completion
- **Prerequisites**: memorygraph.dev Graph Service complete, WP20 release
- **Reference**: PRODUCT_ROADMAP.md Phase 3.4, memorygraph.dev Workplan 8-10
- **Tasks**: 60+ (across 8 sections)
- **Note**: Aligns with memorygraph.dev SDK workplans (8-10)

### Future (Strategic Features)

**[6-WORKPLAN.md](6-WORKPLAN.md)** - Multi-Tenancy Phase 1
- Implement schema enhancement for multi-tenant support
- Add optional tenant_id, team_id, visibility fields
- Maintain 100% backward compatibility
- **Priority**: FUTURE (not yet started)
- **Prerequisites**: 1-4 completed ✅, ADR 009 approved
- **Reference**: [ADR 009](../adr/009-multi-tenant-team-memory-sharing.md)
- **Tasks**: 25

### Deprecated Workplans

**[7-WEBSITE-WORKPLAN.md](7-WEBSITE-WORKPLAN.md)** - ❌ **DEPRECATED**
- Website design and planning
- **Status**: Content merged into 17-WORKPLAN.md
- **Do not use**: Refer to 17-WORKPLAN.md instead

**[8-WORKPLAN.md](8-WORKPLAN.md)** - Claude Code Web Support via Project Hooks - **COMPLETE** ✅
- Auto-install MemoryGraph in remote environments
- Project hooks for Claude Code Web
- Cloud backend detection
- **Status**: COMPLETE (implementation exists)
- **Prerequisites**: Cloud backend when available
- **Tasks**: Complete

---

## Execution Recommendations

### For Coding Agents

**v0.10.0 Track (Competitive Features)**:
1. Start with **12-WORKPLAN** (Semantic Navigation) - validates our graph-first approach
2. Then **13-WORKPLAN** (Bi-Temporal Schema) - learn from Graphiti
3. Release v0.10.0 with both features

**v1.0.0 Track (Cloud Launch)**:
1. Start with **14-WORKPLAN** (Cloud Infrastructure) - foundation for everything
2. Then **15-WORKPLAN** (Authentication) - critical for cloud
3. Parallel: **16-WORKPLAN** (SDK) and **17-WORKPLAN** (Website)
4. Release v1.0.0 with cloud platform live

**v1.1.0 Track (Team Features)**:
1. After v1.0.0 launched, work on **18-WORKPLAN** (Team Sync)
2. Release v1.1.0 with real-time collaboration

**Parallel Execution**:
- **0-WORKPLAN-MARKETING**: Can run in parallel with ALL development work
- **16-WORKPLAN** and **17-WORKPLAN**: Can be worked on in parallel
- **6-WORKPLAN**: Defer until multi-tenancy is needed (enterprise customers)

---

## Dependency Graph

```
0-WORKPLAN-MARKETING (parallel track, ongoing)
        │
        ├────────────────────────────────────────────────────┐
        │                                                    │
1-WORKPLAN (Critical Fixes) ✅ COMPLETE                      │
    ↓                                                        │
    ├─→ 2-WORKPLAN (Test Coverage) ✅ COMPLETE               │
    │       ↓                                                │
    ├─→ 3-WORKPLAN (Code Quality) ✅ SUBSTANTIALLY COMPLETE  │
    │       ↓                                                │
    └─────→ 4-WORKPLAN (Refactoring) ✅ COMPLETE             │
                ↓                                            │
            5-WORKPLAN (New Features) ✅ COMPLETE ←──────────┘
                ↓
                ├─→ 9-WORKPLAN (Universal Export) ✅ SUBSTANTIALLY COMPLETE
                │       ↓
                │   10-WORKPLAN (Migration Manager) ✅ CORE COMPLETE
                │       ↓
                │   11-WORKPLAN (MCP Tools) ✅ TOOLS COMPLETE
                │
                ├─→ 12-WORKPLAN (Semantic Navigation) [v0.10.0] NEW
                │       ↓
                │   13-WORKPLAN (Bi-Temporal Schema) [v0.10.0] NEW
                │
                ├─→ 14-WORKPLAN (Cloud Infrastructure) [v1.0.0] ❌ DEPRECATED
                │       ↓
                │   15-WORKPLAN (Authentication) [v1.0.0] ❌ DEPRECATED
                │       ↓
                │   ├─→ 20-WORKPLAN (MCP Cloud Backend) [v1.0.0] ✅ IMPLEMENTATION COMPLETE
                │   │
                │   ├─→ 16-WORKPLAN (SDK Development) [v1.0.0] NEW
                │   │
                │   ├─→ 17-WORKPLAN (Website) [v1.0.0] ❌ DEPRECATED
                │   │
                │   └─→ 18-WORKPLAN (Team Sync) [v1.1.0] NEW
                │
                └─→ 6-WORKPLAN (Multi-Tenancy) [FUTURE]
```

---

## Version Roadmap

### v0.9.6 (Current - Released)
- Foundation complete (1-5, 9-11)
- 1,200 tests passing
- Migration system working
- **Status**: ✅ Released

### v0.10.0 (Next - Competitive Features)
- **12-WORKPLAN**: Semantic Navigation Tools ✅ COMPLETE
- **13-WORKPLAN**: Bi-Temporal Schema ✅ COMPLETE
- **Target**: Q1 2026
- **Focus**: Close gaps with Cipher and Graphiti
- **Status**: Ready for release (both workplans complete)

### v1.0.0 (Cloud Launch)
- **20-WORKPLAN**: MCP Cloud Backend Adaptation ✅ IMPLEMENTATION COMPLETE
- **16-WORKPLAN**: SDK Development
- **14-WORKPLAN**: Cloud Infrastructure ❌ DEPRECATED (see memorygraph.dev)
- **15-WORKPLAN**: Authentication & API Keys ❌ DEPRECATED (see memorygraph.dev)
- **17-WORKPLAN**: Website ❌ DEPRECATED (see memorygraph.dev)
- **Target**: Q2 2026 (cloud backend ready, release pending)
- **Focus**: MCP cloud integration and SDK development

### v1.1.0 (Team Features)
- **18-WORKPLAN**: Real-Time Team Sync ❌ DEPRECATED (moved to memorygraph.dev)
- **Target**: Q3 2026
- **Focus**: Enterprise collaboration (server-side implementation in memorygraph.dev)

### v1.2.0+ (Future)
- **6-WORKPLAN**: Multi-Tenancy
- Additional features based on user feedback

---

## Metrics Summary

### Total Work Status (as of 2025-12-07)
- **Total Workplans**: 19 active + 4 deprecated
- **Completed Workplans**: 11 (1-5, 8-13, 20 core implementation)
- **New Workplans**: 8 (12-13, 16, 18, 20)
- **Test Suite**: 1,338 tests passing (up from 890)
- **Coverage**: Maintained/improved (server.py significantly improved)
- **v0.10.0 Status**: Ready for release (12-13 complete)
- **Cloud Backend Status**: Implementation complete, release pending (20 complete)

### Priority Breakdown - UPDATED
- **Marketing** (parallel): 25+ tasks (0-WORKPLAN-MARKETING) - IN PROGRESS
- **Foundation** (COMPLETE ✅): 130+ tasks (1-5, 9-11 WORKPLAN)
- **v0.10.0 Features** (COMPLETE ✅): 130+ tasks (12-13 WORKPLAN)
- **v1.0.0 Cloud Backend** (IMPLEMENTATION COMPLETE ✅): 100+ tasks (20 WORKPLAN)
- **v1.0.0 SDK** (NEW): 60+ tasks (16 WORKPLAN)
- **v1.1.0 Features** (NEW): 80+ tasks (18 WORKPLAN)
- **Future** (NOT STARTED): 25 tasks (6-WORKPLAN)
- **Deprecated**: 7-WEBSITE-WORKPLAN (merged into 17), 14-15, 17 (superseded by memorygraph.dev)

### Estimated Effort
- **v0.10.0**: 20-28 hours (12-13 WORKPLAN) - ✅ COMPLETE (~22 hours actual)
- **v1.0.0 Cloud Backend**: ~20 hours (20 WORKPLAN) - ✅ IMPLEMENTATION COMPLETE (~18 hours actual)
- **v1.0.0 SDK**: 12-16 hours (16 WORKPLAN)
- **v1.1.0**: 16-24 hours (18 WORKPLAN)
- **Total remaining work**: 28-40 hours (SDK development + team sync)

---

## Strategic Context

### Product Roadmap Alignment

These workplans align with [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md):
- **Phase 0: Competitive Response** (NEW): Marketing, differentiation (0-WORKPLAN)
- **Phase 1-2** (COMPLETE ✅): Quality and testing (1-5 workplans)
- **Phase 2.5** (SUBSTANTIALLY COMPLETE ✅): Universal export and migration (9-11 workplans)
- **Phase 2 (NEW)**: Semantic Navigation + Bi-Temporal (12-13 workplans)
- **Phase 3 (NEW)**: Cloud Launch (14-17 workplans)
- **Phase 4 (NEW)**: Team Features (18 workplan)
- **Phase 5 (FUTURE)**: Multi-tenancy (6 workplan)

### Architecture Decision Records

Implemented ADRs:
- [ADR 010](../adr/010-server-refactoring.md): Server refactoring approach (4-WORKPLAN) ✅
- [ADR 011](../adr/011-pagination-design.md): Pagination design (5-WORKPLAN) ✅
- [ADR 012](../adr/012-cycle-detection.md): Cycle detection strategy (5-WORKPLAN) ✅
- [ADR 015](../adr/015-universal-export-migration.md): Universal export and backend migration (9-11 WORKPLAN) ✅

Planned ADRs:
- [ADR 016](../adr/016-bi-temporal-tracking.md): Bi-temporal tracking (13-WORKPLAN) - TO BE CREATED
- [ADR 009](../adr/009-multi-tenant-team-memory-sharing.md): Multi-Tenant Team Memory Sharing (6-WORKPLAN) - FUTURE

---

## Completion Summary (2025-12-07 Update)

### What Was Accomplished (v0.9.x)

**Foundation (Workplans 1-5)** - ALL COMPLETE ✅
1. ✅ Fixed 2,379 datetime deprecation warnings
2. ✅ Implemented health check system
3. ✅ Increased test coverage to 1,200 tests (+35%)
4. ✅ Created exception hierarchy and error handling framework
5. ✅ Improved type hints across codebase
6. ✅ Standardized on Google-style docstrings
7. ✅ Refactored server.py (1,502 → 873 lines, 42% reduction)
8. ✅ Implemented pagination with offset/limit
9. ✅ Implemented cycle detection for relationships

**Migration System (Workplans 9-11)** - CORE COMPLETE ✅
1. ✅ Refactored export/import to be backend-agnostic
2. ✅ Implemented MigrationManager with validation/verification/rollback
3. ✅ Added CLI `migrate` command
4. ✅ Created MCP tools: `migrate_database`, `validate_migration`
5. ✅ 7 migration tool tests passing
6. ✅ SQLite backend fully tested

**Claude Code Web Support (Workplan 8)** - COMPLETE ✅
1. ✅ Project hooks for auto-installation
2. ✅ Cloud backend detection

### What's New (2025-12-07)

**v0.10.0 Features Complete** ✅:
1. ✅ 12-WORKPLAN: Semantic Navigation Tools (contextual_search) - COMPLETE
2. ✅ 13-WORKPLAN: Bi-Temporal Schema - COMPLETE

**8 New Workplans Created (2025-12-05/07)**:
1. ✅ 12-WORKPLAN: Semantic Navigation Tools (v0.10.0) - COMPLETE
2. ✅ 13-WORKPLAN: Bi-Temporal Schema (v0.10.0) - COMPLETE
3. ✅ 14-WORKPLAN: Cloud Infrastructure - DEPRECATED (see memorygraph.dev)
4. ✅ 15-WORKPLAN: Authentication & API Keys - DEPRECATED (see memorygraph.dev)
5. ✅ 16-WORKPLAN: SDK Development (v1.0.0)
6. ✅ 17-WORKPLAN: memorygraph.dev Website - DEPRECATED (see memorygraph.dev)
7. ✅ 18-WORKPLAN: Real-Time Team Sync (v1.1.0) - DEPRECATED (see memorygraph.dev)
8. ✅ 20-WORKPLAN: MCP Cloud Backend Adaptation (v1.0.0) - IMPLEMENTATION COMPLETE

**Workplans Deprecated**:
- ❌ 7-WEBSITE-WORKPLAN: Content merged into 17-WORKPLAN
- ❌ 14-WORKPLAN: Cloud infrastructure managed in memorygraph.dev repo
- ❌ 15-WORKPLAN: Auth service already deployed in memorygraph.dev
- ❌ 17-WORKPLAN: Marketing site already live at memorygraph.dev

**Workplans Moved**:
- 20-WORKPLAN: Moved from memorygraph.dev/docs/planning/5-WORKPLAN-mcp-integration.md (2025-12-07)

### Current State

**Version**: v0.10.0 (ready for release)
**Test Count**: 1,338 tests passing (+138 from v0.9.6)
**Code Quality**: Significantly improved
**Migration**: Core functionality ready for production use
**v0.10.0 Status**: ✅ Ready for release (12-13 complete)
**Cloud Backend Status**: ✅ Implementation complete (20 complete, release pending)
**Next Focus**: v1.0.0 SDK development (16-WORKPLAN)
**Cloud Infrastructure**: Already deployed at memorygraph.dev
**Graph API**: Live at https://graph-api.memorygraph.dev

---

## Recommendations for Next Steps

Based on the current state and [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md):

### ✅ Completed (v0.10.0)
1. **12-WORKPLAN**: Semantic Navigation Tools ✅
   - Validated our graph-first approach (Cipher abandoned vectors)
   - 1 navigation tool (contextual_search) - 5 others cut for context budget
   - No embedding dependencies

2. **13-WORKPLAN**: Bi-Temporal Schema ✅
   - Learned from Graphiti's proven model
   - Track knowledge evolution
   - Point-in-time queries via Python API
   - MCP tools deferred per ADR-017 (context budget)

### Immediate (Next)
1. **20-WORKPLAN**: Cloud Backend Release (Sections 7-8)
   - Update Claude Code setup documentation
   - Release v0.10.0 to PyPI
   - Update Docker images
   - **Status**: Implementation complete, release pending

2. **16-WORKPLAN**: SDK Development
   - LangChain, CrewAI, AutoGen integrations
   - Differentiate from Cipher (MCP-only)
   - Python package: memorygraphsdk
   - Publish to PyPI

**Note**: Cloud infrastructure (14, 15, 17) already deployed in memorygraph.dev repo

### Medium-term (v1.1.0)
1. **18-WORKPLAN**: Real-Time Team Sync ❌ DEPRECATED
   - **Status**: Moved to memorygraph.dev repository (server-side)
   - Cloud-native sync (vs Cipher's manual pull)
   - Team workspaces
   - Activity feed

### Long-term (v1.2.0+)
1. **6-WORKPLAN**: Multi-Tenancy
   - Enterprise features
   - When needed based on customer demand

---

## Archived Workplans

Old workplans moved to `/docs/archive/`:
- `WORKPLAN_2025-12-02.md` (75KB, comprehensive original)
- `2-WORKPLAN_CODE_QUALITY_2025-12-02.md` (21KB, code review findings)

These are superseded by the new numbered workplans.

---

## Usage Notes

### For Project Managers
- Use this index to understand scope and priorities
- Track progress by checking completion of workplans
- Adjust priority based on business needs
- v0.10.0 focuses on competitive features
- v1.0.0 focuses on cloud launch
- v1.1.0 focuses on team collaboration

### For Developers
- Start with workplan prerequisites
- Update checkboxes as you complete tasks
- Run full test suite between workplans
- Create feature branches for major work
- All file paths are absolute for clarity
- Test before committing

### For Contributors
- Refer to individual workplans for detailed task lists
- All file paths are absolute for clarity
- Tests should be written before implementation (TDD approach)
- Each workplan has clear acceptance criteria
- New workplans are optimized for coding agents

---

## Questions?

- **Not sure where to start?** Begin with 12-WORKPLAN.md (Semantic Navigation)
- **Need strategic context?** Review [PRODUCT_ROADMAP.md](PRODUCT_ROADMAP.md)
- **Want to understand multi-tenancy?** Read [ADR 009](../adr/009-multi-tenant-team-memory-sharing.md)
- **Looking for completed work?** Check `/docs/archive/`
- **Website content?** See 17-WORKPLAN.md (7-WEBSITE-WORKPLAN deprecated)

---

**Last Updated**: 2025-12-07
**Maintainer**: Gregory Dickson
**Status**: v0.10.0 ready for release (12-13 complete), SDK development next (16)
**Cloud**: Already deployed at memorygraph.dev
**Next Focus**: SDK integrations (LangChain, CrewAI, AutoGen)
