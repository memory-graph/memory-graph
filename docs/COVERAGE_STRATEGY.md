# Test Coverage Improvement Strategy

## Executive Summary

**Current Coverage: 71%** (was reported as 41% due to measurement issue)
**Target Coverage: 75%+**
**Gap: 4 percentage points**

## Phase 1: Root Cause Analysis - COMPLETED

### Finding: Coverage Measurement Issue (Not a Real Regression)

The reported 41% coverage was due to running coverage without proper source path specification. When running:
- `pytest --cov=src/memorygraph`: **71% coverage** (correct)
- Without explicit source: May give inconsistent results

**Actual Status**: Coverage is healthy at 71%, not regressed. The .coveragerc file is properly configured.

### Coverage Breakdown by Module

| Module | Lines | Coverage | Missing | Priority |
|--------|-------|----------|---------|----------|
| **Critical Path (Need Improvement)** |
| intelligence_tools.py | 161 | 10% | 145 | HIGH |
| proactive_tools.py | 198 | 12% | 174 | HIGH |
| integration_tools.py | 157 | 15% | 133 | HIGH |
| advanced_tools.py | 103 | 17% | 85 | HIGH |
| backends/memgraph_backend.py | 113 | 28% | 81 | MEDIUM |
| server.py | 248 | 58% | 105 | MEDIUM |
| database.py | 315 | 66% | 106 | MEDIUM |
| **Well Tested** |
| intelligence/context_retrieval.py | 91 | 100% | 0 | - |
| backends/factory.py | 90 | 100% | 0 | - |
| models.py | 190 | 97% | 5 | - |
| relationships.py | 106 | 97% | 3 | - |
| cli.py | 79 | 95% | 4 | - |

## Phase 2: Strategic Analysis

### Why Tool Modules Have Low Coverage

The `*_tools.py` modules are **MCP tool handler wrappers** that:
1. Define MCP tool schemas
2. Parse and validate tool inputs
3. Call underlying business logic (which IS well-tested)
4. Format responses as MCP TextContent

**Current testing approach**: Tests focus on the underlying modules (which have good coverage).
**Gap**: The MCP tool handler layer itself is not tested.

### Coverage Impact Analysis

If we add tests for the 4 tool handler modules (618 lines total with 487 missing):
- Adding 70% coverage to these modules = ~340 lines
- Impact on overall coverage: 340/3767 = ~9% increase
- **New total: 71% + 9% = 80%** (exceeds target)

### Alternative: Pragmatic Approach

The tool handlers are thin wrappers around well-tested business logic. We could:
1. Focus on critical business logic coverage gaps
2. Add integration tests that exercise tools end-to-end
3. Accept that some wrapper code has lower coverage

This would be more maintainable and practical.

## Phase 3: Recommended Strategy

### Option A: Comprehensive (Target 80% coverage)

**Estimated Effort: 2-3 hours**

1. Create test files for all tool modules:
   - `tests/test_advanced_tools.py`
   - `tests/test_integration_tools.py`
   - `tests/test_intelligence_tools.py`
   - `tests/test_proactive_tools.py`

2. Test patterns for each tool:
   - Input validation and schema compliance
   - Successful execution path
   - Error handling
   - Response format validation

3. Improve backend coverage:
   - Add memgraph-specific tests (if memgraph is available)
   - Add error path tests for neo4j backend

4. Improve server.py coverage:
   - Test error handlers
   - Test tool routing logic
   - Test lifecycle methods

**Result: ~80% coverage**

### Option B: Pragmatic (Target 75% coverage)

**Estimated Effort: 1 hour**

1. Add integration tests that exercise tools through server
2. Focus on critical uncovered paths in:
   - database.py (error handling, edge cases)
   - server.py (error handlers, lifecycle)
   - backends (connection error handling)

3. Strategic unit tests for:
   - Complex business logic in tool handlers
   - Error paths in critical modules

**Result: ~75% coverage with better quality**

## Phase 4: Implementation Plan

### Recommended: Option B (Pragmatic)

#### Priority 1: Database Coverage (66% -> 80%)
- Test error paths in create/update/delete operations
- Test edge cases in search and filtering
- Test transaction rollback scenarios
- **Impact: +5% overall**

#### Priority 2: Server Coverage (58% -> 75%)
- Test MCP protocol error handling
- Test tool not found scenarios
- Test lifecycle methods (startup/shutdown)
- Test resource cleanup
- **Impact: +4% overall**

#### Priority 3: Backend Coverage
- Test connection failures and retries
- Test transaction error handling in SQLite
- Test query execution errors
- **Impact: +2% overall**

#### Priority 4: Integration Tests
- Create end-to-end tests that exercise tools through server
- These provide practical coverage of tool handlers
- **Impact: +2% overall**

**Total Expected: 71% + 5% + 4% + 2% + 2% = 84%**

## Phase 5: Execution Order

1. **Fix database.py coverage** (30 min)
   - Add error path tests
   - Add edge case tests
   - Quick win, high impact

2. **Fix server.py coverage** (30 min)
   - Add error handler tests
   - Add lifecycle tests
   - Critical path coverage

3. **Fix backend coverage** (20 min)
   - Add connection error tests
   - Add transaction error tests
   - Defensive coding coverage

4. **Add selective tool handler tests** (40 min)
   - Pick 2-3 most complex tools per module
   - Test validation and error handling
   - Practical over comprehensive

## Phase 6: Quality Gates

After each priority:
1. Run full test suite: `python3 -m pytest --cov=src/memorygraph --cov-report=term`
2. Verify all tests pass
3. Check coverage improvement
4. Commit incrementally

## Success Criteria

- [ ] Overall coverage >= 75%
- [ ] All critical paths (database, server) >= 75%
- [ ] All tests passing
- [ ] No decrease in existing coverage
- [ ] Tests are maintainable and meaningful

## Notes

- **Don't test for coverage percentage**: Test for quality and critical paths
- **Avoid brittle tests**: Don't mock excessively
- **Focus on behavior**: Test what the code does, not how it does it
- **Error paths matter**: Most uncovered code is error handling
