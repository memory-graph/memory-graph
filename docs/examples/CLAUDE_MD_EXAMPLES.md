# CLAUDE.md Configuration Examples for MemoryGraph

Ready-to-use CLAUDE.md snippets for configuring Claude to proactively use MemoryGraph.

---

## Quick Start (Minimal)

Add this to `~/.claude/CLAUDE.md` for basic memory functionality:

```markdown
## Memory Protocol
After completing significant tasks, store a memory with:
- Type: solution, problem, code_pattern, etc.
- Title: Brief description
- Content: What was accomplished, key decisions made
- Tags: Relevant keywords
- Relationships: Link to related memories

Before starting work, use `recall_memories` to check for past learnings.
```

---

## Recommended (Comprehensive)

Add this to `~/.claude/CLAUDE.md` for full proactive memory usage:

```markdown
## Memory Protocol

### When to Store Memories
After completing significant work, store a memory using the `store_memory` tool:
- **Solutions**: Working fixes, implementations
- **Problems**: Issues encountered, blockers
- **Patterns**: Reusable code patterns
- **Decisions**: Architecture choices, trade-offs
- **Errors & Fixes**: Bugs and their resolutions

### Memory Storage Format
Always include:
- **Type**: solution, problem, code_pattern, decision, error, fix, task, technology
- **Title**: Brief, descriptive (e.g., "Fixed Redis timeout with connection pooling")
- **Content**:
  - What was accomplished
  - Why this approach was chosen
  - Key decisions and trade-offs
  - Context for future reuse
- **Tags**: Technology, domain, pattern name
- **Relationships**: Link related memories using `create_relationship`

### Common Relationship Patterns
- Solutions SOLVE problems
- Fixes ADDRESS errors
- Patterns APPLY_TO projects
- Decisions IMPROVE previous approaches
- Errors TRIGGER problems
- Changes CAUSE issues

### Recall Before Work
Before starting on a topic, use `recall_memories` to check for:
- Past solutions to similar problems
- Known issues and their fixes
- Established patterns and conventions
- Previous decisions and rationale

### Session Management
At the end of each session:
1. Use `store_memory` with type=task to summarize what was accomplished
2. Include what's next in the content
3. Tag with project name and date
```

---

## Project-Specific Configuration

Add this to `.claude/CLAUDE.md` in your project root for project-specific memory:

```markdown
## Project: [Your Project Name]

### Memory Storage Protocol
This project uses MemoryGraph for team knowledge sharing.

When working on this project:
1. Before starting: "What do you remember about [component]?"
2. After solving issues: Store the problem and solution, link them
3. After implementing features: Store the pattern used
4. At session end: Store a task summary

### Tagging Convention
Always tag memories with:
- `project:[project-name]`
- `component:[auth|api|database|frontend|etc]`
- `type:[fix|feature|optimization|refactor]`
- Relevant technologies: `fastapi`, `react`, `postgresql`, etc.

### Memory Types for This Project
- **solution**: Working implementations (API endpoints, features)
- **problem**: Issues we encountered (performance, bugs)
- **code_pattern**: Reusable patterns (error handling, validation)
- **decision**: Architecture choices (why we chose X over Y)
- **task**: Sprint work, feature completion

### Example Memory Flow
When fixing a bug:
1. Store problem: type=problem, title="API timeout under load"
2. Store solution: type=solution, title="Fixed with connection pooling"
3. Link them: solution SOLVES problem
4. Both tagged: `project:myapp`, `component:api`, `postgresql`
```

---

## Advanced: Team Collaboration

For teams using shared memory, add this to `~/.claude/CLAUDE.md`:

```markdown
## Team Memory Protocol

### Shared Memory Guidelines
This team uses MemoryGraph for collective knowledge. Follow these practices:

#### Storage Standards
- **Be descriptive**: Others will search for your memories
- **Include context**: Why decisions were made, not just what
- **Tag consistently**: Use agreed-upon tags (see below)
- **Link everything**: Create relationships between related memories

#### Team Tagging Convention
Required tags for all team memories:
- `team:[team-name]` - Which team stored this
- `project:[project-name]` - Which project it applies to
- `component:[component-name]` - Which part of the system
- Technology tags: `python`, `fastapi`, `postgresql`, `react`, etc.

#### Memory Ownership
- Add your name or initials in tags: `author:[yourname]`
- Update existing memories if you discover new information
- Leave a comment in the content explaining changes

#### Session Routine
**Start of day**:
- "What did the team work on yesterday?"
- "Recall any issues in [component] I should know about"

**During work**:
- Store solutions to non-trivial problems
- Link to existing problems when you solve them
- Update memories if approach changes

**End of day**:
- "Store a summary of what I accomplished today"
- Tag with `daily-summary` and current date

#### Common Memory Flows
**Bug fixing**:
1. Check: "Have we seen [error] before?"
2. Store: Problem (if new) + Solution
3. Link: solution SOLVES problem
4. Tag: `bug-fix`, component, technologies

**Feature development**:
1. Check: "What patterns have we used for [use case]?"
2. Store: Implementation as code_pattern
3. Link: pattern APPLIES_TO project
4. Tag: `feature`, component, pattern-name

**Architecture decisions**:
1. Store: Decision with full rationale
2. Link: decision IMPROVES previous_approach (if applicable)
3. Tag: `architecture`, `decision`, affected components

### Sprint Workflows
**Sprint planning**:
- "Recall problems from last sprint"
- "What technical debt did we identify?"

**Sprint retro**:
- "What solutions worked well this sprint?"
- Store top improvements as decision memories

**Onboarding**:
- New team members: "Catch me up on [project/component]"
- Returns: Decisions, patterns, known issues
```

---

## Domain-Specific Examples

### Web Development

```markdown
## Memory Protocol - Web Development

### Store These Patterns
- **API Design**: Endpoint structure, error handling, validation
- **Authentication**: JWT flows, session management, OAuth patterns
- **Database**: Query optimization, migration patterns, schema decisions
- **Frontend**: Component patterns, state management, performance tricks
- **Deployment**: CI/CD configs, environment setup, rollback procedures

### Common Relationships
- API endpoint patterns APPLY_TO projects
- Performance optimizations IMPROVE slow_queries
- Security fixes ADDRESS vulnerabilities
- New patterns REPLACE deprecated_patterns

### Typical Session Flow
1. Start: "Recall API patterns for [feature]"
2. Develop: [Implementation]
3. Store: "Store this error handling pattern"
4. Link: pattern APPLIES_TO this_project
5. End: "Store feature completion summary"
```

### Data Science / ML

```markdown
## Memory Protocol - Data Science

### Store These Patterns
- **Model Training**: Hyperparameters, architectures, training tricks
- **Data Pipeline**: ETL patterns, preprocessing steps, validation
- **Experiments**: Results, what worked/didn't, insights
- **Deployment**: Serving patterns, monitoring, drift detection

### Common Relationships
- Model improvements IMPROVE baseline_model
- Feature engineering SOLVES data_quality_problem
- Experiment results CONFIRM hypothesis
- New approach CONTRADICTS previous_assumption

### Experiment Tracking
After each experiment:
1. Store: Results with type=solution or type=problem
2. Tag: `experiment`, model-type, dataset-name
3. Link: If improvement, link: new_model IMPROVES previous_model
4. Include: Metrics, parameters, insights in content
```

### DevOps / Infrastructure

```markdown
## Memory Protocol - DevOps

### Store These Patterns
- **Deployment**: CI/CD configs, rollback procedures
- **Monitoring**: Alert configurations, runbook procedures
- **Incidents**: Root causes, resolutions, preventions
- **Infrastructure**: IaC patterns, networking configs, security setups

### Common Relationships
- Incident resolution SOLVES incident
- Infrastructure change CAUSES issue (if it breaks)
- Runbook procedure ADDRESSES alert_type
- New config IMPROVES previous_config

### Incident Response Flow
1. Alert fires: "Recall similar incidents for [service]"
2. Debug: [Investigation]
3. Store incident: type=problem with root cause
4. Store resolution: type=solution with fix steps
5. Link: solution SOLVES incident
6. Update runbook: Store updated procedure
```

---

## Testing Your Configuration

After adding memory protocols to CLAUDE.md, verify they work:

### Test 1: Check Protocol Recognition
```
You: "What's our memory protocol?"
Expected: Claude should reference the protocol from your CLAUDE.md
```

### Test 2: Proactive Storage
```
You: [Fix a bug together]
Expected: Claude should suggest storing the solution or ask if you want to store it
```

### Test 3: Proactive Recall
```
You: "Let's work on authentication"
Expected: Claude should proactively check: "What do you remember about authentication?"
```

### Test 4: Relationship Creation
```
You: "Store this solution: [description]"
Expected: Claude should ask if it relates to any existing memories or search for related problems
```

### Test 5: Session Wrap-Up
```
You: "Let's wrap up"
Expected: Claude should suggest storing a session summary
```

---

## Troubleshooting

### Claude Isn't Using Memory Tools

**Issue**: Claude doesn't proactively store or recall memories.

**Solutions**:
1. **Verify CLAUDE.md is loaded**: Ask "What's in my CLAUDE.md?" - Claude should see your memory protocol
2. **Be explicit initially**: Use trigger phrases like "Store this..." until the habit forms
3. **Check file location**:
   - Global: `~/.claude/CLAUDE.md`
   - Project: `.claude/CLAUDE.md` in project root
4. **Restart Claude Code**: After editing CLAUDE.md, restart for changes to take effect

### Claude Stores Too Many/Few Memories

**Too many**: Make protocol more specific about what to store:
```markdown
### Storage Criteria
Only store memories when:
- Solution is non-trivial (not a simple one-liner)
- Problem is likely to recur
- Pattern is reusable across contexts
- Decision has long-term impact
```

**Too few**: Make protocol more proactive:
```markdown
### Proactive Storage
After ANY of these events, ALWAYS store a memory:
- Solving a bug that took >30 minutes
- Implementing a new feature
- Making an architecture decision
- Discovering a useful pattern
- Encountering an error and fixing it
```

### Memories Aren't Well-Formatted

Add formatting requirements to your protocol:

```markdown
### Memory Content Template
Always structure content like this:

**What**: Brief description of what was done
**Why**: Reasoning and context
**How**: Key implementation details
**Trade-offs**: What was considered and why this was chosen
**Related**: Links to docs, PRs, or other resources
```

---

## Migration from Other Systems

### From CLAUDE.md Static Notes

If you've been storing knowledge in CLAUDE.md as static text:

**Before** (in CLAUDE.md):
```markdown
## Known Issues
- Redis timeout: increase connection pool to 50
- API rate limiting: use exponential backoff
```

**After** (using MemoryGraph):
```markdown
## Memory Protocol
[Memory protocol from examples above]

## Static Knowledge (Keep for rules/preferences)
- Code style: 2-space indentation
- Commit messages: conventional commits format
```

**Migration**:
1. Ask Claude: "Convert these known issues to memory entries"
2. Claude will use `store_memory` for each
3. Create relationships between related issues
4. Remove from CLAUDE.md (now in memory graph)
5. Keep only static rules/preferences in CLAUDE.md

### From Notion/Confluence/Docs

If your team has external documentation:

**Strategy**:
1. Keep docs for: Long-form guides, API docs, architecture diagrams
2. Move to MemoryGraph: Solutions, problems, decisions, patterns, incidents
3. Link them: Store memory with link to doc in content

**Example**:
```markdown
Content: "Use repository pattern for database access. See full guide: https://docs.company.com/db-patterns"
Type: code_pattern
Tags: database, pattern, architecture
```

---

## Related Documentation

- [README.md](../../README.md#memory-best-practices) - Quick start and best practices
- [CLAUDE_CODE_SETUP.md](../CLAUDE_CODE_SETUP.md#configuring-proactive-memory-creation) - Full configuration guide
- [CONFIGURATION.md](../CONFIGURATION.md) - MCP configuration reference
- [TOOL_SELECTION_GUIDE.md](../TOOL_SELECTION_GUIDE.md) - How Claude chooses which tools to use

---

**Last Updated**: December 1, 2025
**Version**: 1.0
