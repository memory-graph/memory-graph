# Experimental Tools

This directory contains tool modules that were documented but not fully implemented or tested in production.

## Moved Files

These files were moved from `src/memorygraph/` to `experimental/` as part of the context budget optimization (ADR-017):

- `intelligence_tools.py` - 7 intelligence/pattern recognition tools
- `integration_tools.py` - 11 Claude Code integration tools
- `proactive_tools.py` - 11 proactive/predictive analytics tools

**Total**: 29 tools consuming approximately 35-45k context tokens

## Why Moved

These tools were:
1. Documented in the codebase but never registered as working MCP tools
2. Missing critical backend implementations
3. Consuming significant context budget without providing value
4. Creating confusion about which tools are actually available

## Status

These tools are considered **vaporware** - they exist in code form but are not functional or tested. They may be:
- Completed and moved back to core in future releases
- Deleted if not needed
- Used as reference implementations for future work

## Context Budget Impact

Removing these from the active codebase saves ~35-45k context tokens, allowing:
- Faster tool loading
- Better focus on implemented, tested tools
- Clearer documentation for users

## See Also

- `/docs/adr/017-context-budget-constraint.md` - Decision rationale
- `/docs/TOOL_PROFILES.md` - Actual implemented tools
