# README Reorganization Plan

## Current Issues

1. **Redundant Installation Content**: Quick Start (lines 15-165) duplicates Installation section (lines 541-628)
2. **Configuration Examples Scattered**: Basic config in Quick Start, detailed examples later (lines 630-782)
3. **Mixed Audiences**: Getting-started mixed with architecture details and memory option comparisons
4. **Feature Documentation Too Deep**: Automatic Context Extraction (lines 341-485) is advanced content too early
5. **Troubleshooting Bloat**: Very detailed troubleshooting (lines 1009-1135) could be shortened with link to docs

## Proposed Structure

```
1. Header + Badges (keep)
2. One-liner description (keep)
3. Quick Start (SIMPLIFIED)
   - Claude Code CLI only (primary audience)
   - 3 commands max
   - "Verify it works" snippet
   - Link to other clients
4. What is MemoryGraph? (condensed)
   - Brief architecture explanation
   - Why MCP?
5. Why MemoryGraph? (key differentiator)
   - Graph relationships vs flat (the ASCII diagram)
   - Decision guide (simplified)
6. Choose Your Mode (keep - it's a good overview)
7. Features (condensed bullet list, link to docs)
8. Installation Options (consolidated)
   - pipx (recommended)
   - pip
   - Docker
   - uvx
   - Comparison table
9. Configuration Reference (consolidated)
   - Move detailed JSON examples to docs/CONFIGURATION.md
   - Keep 2-3 essential examples here
10. Usage Examples (brief)
    - Move detailed examples to docs/examples/
11. Development (for contributors)
12. Troubleshooting (SHORT - link to docs)
13. Contributing / Roadmap / License / Support
```

## Content to Move to Separate Docs

| Section | Move To | Reason |
|---------|---------|--------|
| Automatic Context Extraction (lines 341-485) | docs/CONTEXT_EXTRACTION.md | Advanced feature, clutters quick understanding |
| Detailed Configuration Examples (lines 630-782) | docs/CONFIGURATION.md | Reference material |
| Memory Options Comparison (lines 197-267) | docs/MEMORY_OPTIONS_COMPARISON.md | Detailed comparison for researchers |
| Detailed Troubleshooting (lines 1009-1135) | docs/TROUBLESHOOTING.md | Keep README short |

## Key Changes

### 1. Simplify Quick Start
**Before**: 80+ lines with alternatives, verification steps, expand sections
**After**:
```markdown
### Quick Start (30 seconds)

1. Install: `pipx install memorygraphMCP`
2. Add to Claude Code: `claude mcp add --scope user memorygraph -- memorygraph`
3. Restart Claude Code

Done! Try: "Store this memory: Use pytest for Python testing"

> Other clients? See [Installation Guide](docs/DEPLOYMENT.md)
```

### 2. Consolidate Installation
- Remove duplication between Quick Start and Installation sections
- Keep comparison table
- Single source of truth

### 3. Shorten Feature Description
- Bullet points instead of detailed tables
- Link to TOOL_PROFILES.md for details

### 4. Create Reference Docs
- docs/CONFIGURATION.md - All JSON examples
- docs/CONTEXT_EXTRACTION.md - Advanced extraction feature
- docs/TROUBLESHOOTING.md - Detailed solutions

## Implementation Steps

- [x] 1. Create docs/CONTEXT_EXTRACTION.md (move from README)
- [x] 2. Create docs/CONFIGURATION.md (consolidate examples)
- [x] 3. Create docs/TROUBLESHOOTING.md (expand from README)
- [x] 4. Rewrite Quick Start section (simplified)
- [x] 5. Consolidate Installation section (remove redundancy)
- [x] 6. Shorten "What is This" section
- [x] 7. Condense Memory Options Comparison (keep Decision Guide)
- [x] 8. Trim Troubleshooting to essentials + link
- [x] 9. Verify all links work
- [x] 10. Review final structure matches plan

## Target Length
- Current README: ~1200 lines
- Target README: ~500-600 lines (50% reduction)
- Detailed content preserved in docs/

## Success Criteria
1. New user can get started in <2 minutes reading
2. All detailed information still accessible via docs links
3. No content lost, just reorganized
4. Clear hierarchy: Quick Start → Why Use It → How to Use It → Reference
