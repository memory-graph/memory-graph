# memory-graph Product Roadmap

**Document Version**: 2.1
**Last Updated**: December 2025
**Author**: Gregory Dickson
**Status**: Strategic Plan

---

## Executive Summary

memory-graph is a lightweight memory server for AI coding agents. It helps coding assistants like Claude Code remember what worked, avoid past mistakes, and maintain context across sessions.

### Vision Statement

> **"Never re-explain your project to your AI again."**

### Value Proposition

| User Pain | memory-graph Solution | Outcome |
|-----------|----------------------|---------|
| "I keep re-explaining my architecture" | Persistent project context | Pick up where you left off |
| "Claude forgot what we tried yesterday" | Solution memory | Know what worked and what didn't |
| "We solved this before but I can't find it" | Searchable knowledge | Find past solutions instantly |
| "My teammate figured this out already" | Team sharing (paid) | Learn from each other |
| "I work on multiple machines" | Cloud sync (paid) | Same memory everywhere |

### What We're NOT

- ❌ Not a general-purpose note-taking app
- ❌ Not an Obsidian replacement
- ❌ Not a complex enterprise knowledge management system
- ❌ Not trying to replace CLAUDE.md (we complement it)

### What We ARE

- ✅ Lightweight memory for coding agents
- ✅ Zero-config by default, powerful when needed
- ✅ Local-first, privacy-respecting
- ✅ Coding-workflow optimized

---

## Target Users

### Primary: Individual Developers Using Claude Code

**Profile**: Professional developers who use Claude Code daily for coding tasks.

**Pain Points**:
- Waste time re-explaining project context every session
- Forget solutions that worked in the past
- Repeat mistakes because lessons aren't captured
- CLAUDE.md is static and gets stale

**What They'll Pay For**:
- Sync across machines (laptop, desktop, cloud IDE)
- Not losing their memory data
- Visual way to browse what they know

### Secondary: Development Teams

**Profile**: Teams of 3-20 developers using AI coding assistants.

**Pain Points**:
- Tribal knowledge locked in individual heads
- Team members re-solve the same problems
- No way to share learnings across the team
- Onboarding is painful

**What They'll Pay For**:
- Shared team memory
- See what teammates have learned
- Team-wide search across all knowledge

---

## Competitive Landscape

### How We Compare

| Solution | Strengths | Weaknesses | Our Opportunity |
|----------|-----------|------------|-----------------|
| **CLAUDE.md** | Built-in, always loaded | Static, manual, no search | Dynamic, searchable, auto-updating |
| **basic-memory** | Human-readable Markdown, Obsidian | PKM-focused, not coding-specific | Purpose-built for coding workflows |
| **mcp-memory-keeper** | Simple checkpoints | No semantic search | Smarter recall, knows what solved what |
| **No memory (status quo)** | Zero setup | Session amnesia | Frictionless upgrade path |

### Our Position

```
                     General Purpose
                           │
         basic-memory ●    │
                           │
    ───────────────────────┼───────────────────────
    Complex Setup          │          Zero Config
                           │
                           │    ● memory-graph
                           │
                     Coding-Specific
```

**We win by being**: Simple to start, coding-specific, lightweight, with a clear upgrade path.

---

## Core Architecture: Claude as the Semantic Layer

### The Central Insight

Rather than building a competing semantic search engine, we leverage what's already present: **Claude is the semantic search layer**. Our job is to provide Claude with tools that are forgiving, composable, and rich enough that Claude can find and synthesize memories effectively.

This approach requires zero new infrastructure while delivering the natural-language query experience users expect.

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                 │
│         "How did we fix that timeout thing?"                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       CLAUDE                                │
│                                                             │
│  • Understands natural language                             │
│  • Interprets "timeout thing" → timeout, error, API, fix    │
│  • Knows synonyms, context, intent                          │
│  • Already has semantic understanding built-in              │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Tool Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY-GRAPH                             │
│                                                             │
│  • Stores structured knowledge                              │
│  • Provides forgiving search tools                          │
│  • Returns rich results with relationships                  │
│  • Lets Claude do the semantic heavy lifting                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**We are the knowledge store. Claude is the semantic interface.**

### What We Don't Need to Build

| Traditional Semantic Search | Our Approach |
|-----------------------------|--------------|
| Embedding model integration | Claude already understands language |
| Vector database | SQLite text search + fuzzy matching |
| Similarity scoring | Claude evaluates relevance |
| Query expansion | Claude interprets intent |
| Synonym handling | Claude knows synonyms |
| Context understanding | Claude has conversation context |

### What We Do Need to Build

1. **Forgiving search tools** - return results even with partial matches
2. **Rich result context** - include relationships so Claude can reason
3. **Composable tool design** - let Claude chain searches effectively
4. **Good tool descriptions** - help Claude know when/how to use each tool

### Tool Design Philosophy

#### Principles

1. **Claude interprets, we store and retrieve**
   - Don't try to understand user intent—Claude does that
   - Provide rich, structured data for Claude to reason over

2. **Forgiving by default**
   - Partial matches are better than no matches
   - Return more results and let Claude filter

3. **Relationships are our superpower**
   - Always include relationship context
   - This is what semantic-search-only tools can't do

4. **Composable over monolithic**
   - Simple tools that Claude can chain
   - Rather than one complex "answer my question" tool

#### Tool Hierarchy

```
Primary (Claude uses first):
  └── recall_memories     # Natural language search, returns rich context

Secondary (Claude uses to drill down):
  ├── search_nodes        # Structured search with filters
  ├── get_entity         # Get specific entity details
  └── get_related        # Traverse relationships

Power Tools (Complex queries):
  ├── graph_query         # Advanced relationship traversal
  └── find_solutions_for  # Find what SOLVED a specific problem
```

### Competitive Positioning

#### vs. Semantic Search Tools (basic-memory, etc.)

| They Have | We Have |
|-----------|---------|
| Embeddings + vector similarity | Claude's semantic understanding |
| Flat document retrieval | Relationship-enriched results |
| "Here's what you said" | "Here's what worked and why" |
| Similarity scores | Causal chains |

**Our message**: "We don't just find similar text—we find solutions and explain how they connect."

#### Why This is Defensible

1. **Claude is already there** - No extra cost or infrastructure
2. **Relationships are unique** - Semantic search alone can't do SOLVES/CAUSES
3. **Simpler stack** - No embedding model to maintain, no vector DB
4. **Privacy preserved** - No text sent to embedding APIs

### Future Considerations

If user feedback indicates we still need true semantic search:

1. **Lightweight option**: `sqlite-vec` extension for local embeddings
2. **Hybrid approach**: Semantic search for discovery, graph for enrichment
3. **Optional cloud**: Embedding API for users who opt-in

But the Claude-as-interface approach should be tried first—it may be sufficient and keeps the stack simple.

---

## Product Tiers

### Free Tier: Local Memory
**Price**: $0 forever
**Goal**: Drive adoption, build habit, create upgrade desire

**Includes**:
- Local SQLite storage (single file, portable)
- All memory tools (store, recall, search, relationships)
- Unlimited memories
- Works offline
- Full privacy (data never leaves your machine)

**Limitations**:
- Single machine only
- No cloud backup
- No team sharing
- Community support only

### Pro Tier: Sync & Dashboard
**Price**: $8/month (early supporters: $6/month forever)
**Goal**: Convert individual power users

**Includes Everything in Free, Plus**:
- ☁️ **Cloud sync** - Same memories on all your machines
- 🖥️ **Web dashboard** - Browse and search your memory visually
- 💾 **Cloud backup** - Never lose your data
- 📧 **Priority support** - Get help when you need it
- 📊 **10GB storage**

**Why Users Pay**:
- "I use Claude Code on my work laptop AND home desktop"
- "I don't want to lose years of learned knowledge if my disk crashes"
- "I want to browse my memories without being in Claude Code"

### Team Tier: Shared Knowledge
**Price**: $12/user/month (early adopters: $9/user/month for first year)
**Goal**: Land team accounts, expand within organizations

**Includes Everything in Pro, Plus**:
- 👥 **Shared team memory** - Search what anyone on the team learned
- 🏷️ **Knowledge attribution** - See who discovered what
- 📈 **Team dashboard** - Bird's-eye view of team knowledge
- 🔐 **Admin controls** - Manage team members and permissions
- 📊 **50GB shared storage**

**Why Teams Pay**:
- "My teammate solved this exact problem last month"
- "New hires can search what the team has learned"
- "Stop re-solving the same problems across the team"

### Enterprise Tier: Custom
**Price**: Contact sales
**Goal**: Large organizations with compliance needs

**Includes Everything in Team, Plus**:
- 🏢 **Self-hosted option** - Run on your infrastructure
- 🔒 **SSO/SAML** - Enterprise authentication
- 📋 **Audit logs** - Compliance and security
- 📞 **Dedicated support** - SLA guarantees
- ♾️ **Unlimited storage**

---

## Roadmap Phases

## Phase 1: Launch & Community
**Timeline**: Weeks 1-3
**Goal**: Establish presence, validate messaging, build community

### 1.1 Simplify Messaging

| Task | Priority | Status |
|------|----------|--------|
| Rewrite README with value-first language | 🔴 High | ⬜ TODO |
| Remove "graph-based" technical jargon | 🔴 High | ⬜ TODO |
| Lead with "Never re-explain your project" | 🔴 High | ⬜ TODO |
| Add clear "What You Get" section | 🔴 High | ⬜ TODO |
| Simplify installation to absolute minimum steps | 🔴 High | ⬜ TODO |

**README Structure**:
```
1. One-sentence value prop
2. 30-second install
3. GIF showing it working
4. "What You Can Do" (5 examples)
5. Advanced options (collapsed)
```

### 1.2 Visual Demo

| Task | Priority | Status |
|------|----------|--------|
| Record asciinema demo (< 60 seconds) | 🔴 High | ⬜ TODO |
| Show: install → store memory → recall it | 🔴 High | ⬜ TODO |
| Convert to GIF for README | 🔴 High | ⬜ TODO |
| Screenshot: Claude Code with memory-graph connected | 🔴 High | ⬜ TODO |

**Demo Script** (45 seconds):
```
1. pip install memorygraphMCP (5s)
2. claude mcp add memorygraph (5s)
3. "Remember: retry with backoff fixed the timeout" (10s)
4. [New session] "What fixed timeout issues?" (10s)
5. Claude recalls the solution (10s)
6. End card: "Never forget what worked" (5s)
```

### 1.3 Community Infrastructure

| Task | Priority | Status |
|------|----------|--------|
| Create Discord server | 🔴 High | ⬜ TODO |
| Create #general, #support, #feedback, #showcase channels | 🔴 High | ⬜ TODO |
| Add Discord link to README | 🔴 High | ⬜ TODO |
| Set up GitHub Discussions | 🟡 Medium | ⬜ TODO |
| Create issue templates | 🟡 Medium | ⬜ TODO |

### 1.4 Launch Campaign

| Task | Priority | Status |
|------|----------|--------|
| Finalize Hacker News post | 🔴 High | ⬜ TODO |
| Post to HN (Monday-Wednesday, 8-10am PT) | 🔴 High | ⬜ TODO |
| Reddit r/ClaudeAI post | 🔴 High | ⬜ TODO |
| LinkedIn post | 🔴 High | ✅ DRAFTED |
| Respond to all comments within 2 hours | 🔴 High | ⬜ TODO |

**Hacker News Post**:
```
Title: Show HN: memory-graph – Memory for Claude Code that remembers what worked

Comment:
I got tired of re-explaining my project architecture to Claude Code
every session. And re-discovering solutions we'd already found.

memory-graph is an MCP server that gives Claude Code persistent memory.
Store what works, recall it later, never repeat the same mistakes.

Install in 30 seconds:
  pip install memorygraphMCP
  claude mcp add memorygraph

Then just talk naturally:
  "Remember: retry with exponential backoff fixed the API timeouts"

Next session:
  "What fixed the timeout issues?"
  → Claude recalls the solution

Local SQLite by default. Your data stays on your machine.
Works offline. Zero config.

https://github.com/gregorydickson/memory-graph

What's your approach to maintaining context across coding sessions?
```

### 1.5 Installation Experience

| Task | Priority | Status |
|------|----------|--------|
| One-line install script | 🔴 High | ⬜ TODO |
| Auto-detect Claude Code and offer to configure | 🔴 High | ⬜ TODO |
| Verify installation command | 🟡 Medium | ⬜ TODO |
| Smithery integration | 🟡 Medium | ⬜ TODO |

**Install Script**:
```bash
curl -LsSf https://memorygraph.dev/install.sh | sh
```

Script behavior:
1. Check for Python 3.10+
2. Install via pipx (or pip if pipx unavailable)
3. Detect if Claude Code is installed
4. Offer to run `claude mcp add memorygraph`
5. Verify with `memorygraph --version`
6. Print success message with next steps

### Phase 1 Success Metrics
- [ ] 100+ GitHub stars
- [ ] 50+ Discord members
- [ ] 1,000+ PyPI downloads
- [ ] HN post with 50+ points
- [ ] 10+ organic testimonials/comments

---

## Phase 2: Search & Recall Excellence
**Timeline**: Weeks 4-7
**Goal**: Make memory recall natural and delightful

### 2.1 Improve Search Forgiveness

Current limitation: Search requires exact or near-exact matches.

| Task | Priority | Status |
|------|----------|--------|
| Add fuzzy matching option to search_nodes tool | 🔴 High | ⬜ TODO |
| Implement case-insensitive search by default | 🔴 High | ⬜ TODO |
| Search observations content, not just entity names | 🔴 High | ⬜ TODO |
| Add search_tolerance parameter (strict/normal/fuzzy) | 🟡 Medium | ⬜ TODO |
| Search across all text fields (names, types, observations) | 🔴 High | ⬜ TODO |

**Technical Enhancements:**

#### 1. Fuzzy Text Matching

```python
# Before: Exact substring match
WHERE observation LIKE '%timeout%'

# After: Fuzzy matching with tolerance
# Option A: SQLite FTS5 with prefix matching
WHERE observations MATCH 'time*'  # Matches timeout, timer, timestamp

# Option B: Trigram similarity (if adding extension)
WHERE similarity(observation, 'timeout') > 0.3

# Option C: Multiple term search with OR
WHERE observation LIKE '%timeout%'
   OR observation LIKE '%time%out%'
   OR observation LIKE '%timed%'
```

#### 2. Case-Insensitive and Normalized Search

```python
# Normalize both query and stored text
# - Lowercase
# - Strip punctuation
# - Handle common variations (retry/retries, error/errors)
```

### 2.2 Enrich Search Results

Current limitation: Search returns entities but Claude needs context to evaluate relevance.

| Task | Priority | Status |
|------|----------|--------|
| Include immediate relationships in search results | 🔴 High | ⬜ TODO |
| Add include_relationships parameter (default: true) | 🔴 High | ⬜ TODO |
| Return match quality hints (which terms matched where) | 🟡 Medium | ⬜ TODO |
| Summarize relationship context in results | 🔴 High | ⬜ TODO |

**Result Format Enhancement:**

```json
// Before: Just the entity
{
  "name": "RetryWithBackoff",
  "type": "Solution",
  "observations": ["Exponential backoff pattern"]
}

// After: Entity with relationship context
{
  "name": "RetryWithBackoff",
  "type": "Solution",
  "observations": ["Exponential backoff pattern"],
  "relationships": {
    "solves": ["TimeoutError", "APIRateLimiting"],
    "used_in": ["ProjectAlpha", "PaymentService"],
    "related_to": ["ErrorHandling", "Resilience"]
  },
  "context_summary": "Solution that solved TimeoutError in ProjectAlpha"
}
```

### 2.3 Optimize Tool Descriptions for Claude

Current limitation: Claude may not know the best tool to use or how to construct effective queries.

| Task | Priority | Status |
|------|----------|--------|
| Rewrite all tool descriptions with Claude-focused guidance | 🔴 High | ⬜ TODO |
| Add usage examples in tool descriptions | 🔴 High | ⬜ TODO |
| Create recall_memories convenience tool | 🔴 High | ⬜ TODO |
| Document recommended tool selection logic | 🟡 Medium | ⬜ TODO |

**Improved Tool Description Example:**

```python
# Before
"search_nodes": "Search for nodes in the knowledge graph"

# After
"search_nodes": """
Search memories using keywords or natural language.
Claude should extract key terms from user queries and search for them.

WHEN TO USE:
- User asks about past solutions, decisions, or learnings
- User references something discussed in previous sessions
- User asks "how did we..." or "what was..." questions

HOW TO USE:
- Extract 2-4 key terms from the user's question
- Start broad, narrow if too many results
- Use relationship filters to find solutions (type=SOLVES) or problems (type=CAUSED_BY)

EXAMPLES:
- User: "How did we fix the timeout issue?" → search "timeout error fix solution"
- User: "What approach did we use for caching?" → search "caching approach"
- User: "That authentication bug" → search "authentication bug error"

Returns entities with their relationships for context.
"""
```

### 2.4 Multi-Term Search Support

Current limitation: Search may require multiple calls for multi-concept queries.

| Task | Priority | Status |
|------|----------|--------|
| Add terms parameter accepting list of search terms | 🔴 High | ⬜ TODO |
| Add match_mode parameter (any/all) | 🔴 High | ⬜ TODO |
| Add relationship_filter parameter | 🟡 Medium | ⬜ TODO |
| Support basic OR/AND/NOT in query strings | 🟡 Medium | ⬜ TODO |

**Enhanced Search API:**

```python
# Allow Claude to pass multiple terms
search_nodes(terms=["timeout", "retry", "API"], match_mode="any")
search_nodes(terms=["authentication", "OAuth"], match_mode="all")

# Simple query language Claude can use
search_nodes(query="timeout OR retry", include_relationships=True)
search_nodes(query="authentication AND NOT OAuth")

# Relationship-filtered search
search_nodes(query="timeout", relationship_filter="SOLVES")
search_nodes(query="error", project="ProjectAlpha", relationship_filter="CAUSED_BY")
```

### 2.5 Session Briefing

| Task | Priority | Status |
|------|----------|--------|
| Improve "catch me up" functionality | 🔴 High | ⬜ TODO |
| Auto-detect project context | 🔴 High | ⬜ TODO |
| Show recent activity relevant to current work | 🟡 Medium | ⬜ TODO |
| Time-based filtering (last 7 days, 30 days) | 🟡 Medium | ⬜ TODO |

**User Experience**:
```
User: "What have we been working on?"

Claude: Based on your memory-graph:

Recent Activity (last 7 days):
• 3 solutions stored for auth-service
• 2 problems tracked in payment-api
• Key insight: "Redis connection pooling fixed timeout issues"

Unresolved Problems:
• payment-api: Intermittent 502 errors (no solution stored yet)

Would you like details on any of these?
```

### 2.6 "What Worked / What Failed" Queries

| Task | Priority | Status |
|------|----------|--------|
| Optimize solution finding queries | 🔴 High | ⬜ TODO |
| Include context of WHY it worked | 🔴 High | ⬜ TODO |
| Surface failed approaches to avoid | 🟡 Medium | ⬜ TODO |
| Rank by recency and relevance | 🟡 Medium | ⬜ TODO |

**User Experience**:
```
User: "What have we tried for the caching issue?"

Claude: From your memory:

✅ What Worked:
• Redis with 5-minute TTL (stored 2 weeks ago)
  - "Reduced DB load by 80%"

❌ What Didn't Work:
• In-memory cache (stored 3 weeks ago)
  - "Caused memory issues in production"
• Memcached (stored 1 month ago)
  - "Too complex for our use case"

The Redis approach seems most successful. Want me to recall the implementation details?
```

### 2.7 Data Portability

| Task | Priority | Status |
|------|----------|--------|
| JSON export (full backup) | 🔴 High | ⬜ TODO |
| JSON import (restore) | 🔴 High | ⬜ TODO |
| Markdown export (human-readable) | 🟡 Medium | ⬜ TODO |
| Export command in CLI | 🔴 High | ⬜ TODO |

**Commands**:
```bash
# Full backup
memorygraph export --format json --output backup.json

# Human-readable export
memorygraph export --format markdown --output memories/

# Restore from backup
memorygraph import --format json --input backup.json
```

### 2.8 Tool Value Audit

Review each MCP tool and ensure it provides clear value:

| Tool Category | User Value | Priority |
|---------------|-----------|----------|
| **Store/Create** | "Remember this for later" | 🔴 Essential |
| **Search/Recall** | "What do I know about X?" | 🔴 Essential |
| **Find Solutions** | "What solved this problem?" | 🔴 Essential |
| **Find Problems** | "What went wrong with X?" | 🔴 Essential |
| **Context/Briefing** | "Catch me up on this project" | 🔴 Essential |
| **Relationships** | "How are these connected?" | 🟡 Valuable |
| **Cleanup** | "Remove outdated memories" | 🟡 Valuable |
| **Export** | "Back up my data" | 🟡 Valuable |

**Action**: Document the value of each tool. If a tool doesn't have a clear "user story," consider simplifying or removing it.

### 2.9 User Feedback Loop

| Task | Priority | Status |
|------|----------|--------|
| Add feedback mechanism (GitHub issue template) | 🔴 High | ⬜ TODO |
| Weekly review of Discord feedback | 🔴 High | ⬜ TODO |
| User interviews (5-10 users) | 🟡 Medium | ⬜ TODO |
| Feature request voting | 🟢 Low | ⬜ TODO |

### Phase 2 Success Metrics
- [ ] NPS score > 40 (from user surveys)
- [ ] <5% uninstall rate
- [ ] 50%+ weekly active users (of installers)
- [ ] 3+ unsolicited testimonials
- [ ] Clear understanding of top 3 feature requests
- [ ] Search result relevance: 80%+ relevant in top 5 (user feedback)
- [ ] Tool calls per recall: 1-2 average (down from 3-4)
- [ ] Failed searches (no results): <10%

---

## Phase 3: Cloud Sync & Monetization
**Timeline**: Weeks 8-14
**Goal**: Launch paid tier, generate revenue

### 3.1 Cloud Infrastructure

**Recommended Stack**: Turso (Distributed SQLite)

| Why Turso | Benefit |
|-----------|---------|
| Same SQLite schema | Zero migration effort |
| Edge-replicated | Fast everywhere |
| Generous free tier | Low cost to start |
| Simple SDK | Fast implementation |

| Task | Priority | Status |
|------|----------|--------|
| Set up Turso account and database | 🔴 High | ⬜ TODO |
| Implement sync protocol | 🔴 High | ⬜ TODO |
| Conflict resolution (last-write-wins or merge) | 🔴 High | ⬜ TODO |
| Offline queue for sync | 🔴 High | ⬜ TODO |
| End-to-end encryption option | 🟡 Medium | ⬜ TODO |

### 3.2 Authentication & Accounts

| Task | Priority | Status |
|------|----------|--------|
| Choose auth provider (Clerk or Auth0) | 🔴 High | ⬜ TODO |
| Implement `memorygraph login` | 🔴 High | ⬜ TODO |
| Implement `memorygraph logout` | 🔴 High | ⬜ TODO |
| Token storage and refresh | 🔴 High | ⬜ TODO |
| Account settings page (web) | 🟡 Medium | ⬜ TODO |

**CLI Flow**:
```bash
$ memorygraph login
Opening browser for authentication...
✓ Logged in as greg@example.com
✓ Cloud sync enabled

$ memorygraph sync status
Last sync: 2 minutes ago
Local memories: 142
Cloud memories: 142
Status: In sync
```

### 3.3 Billing & Subscriptions

| Task | Priority | Status |
|------|----------|--------|
| Stripe integration | 🔴 High | ⬜ TODO |
| Subscription creation flow | 🔴 High | ⬜ TODO |
| Usage tracking | 🔴 High | ⬜ TODO |
| Upgrade/downgrade handling | 🔴 High | ⬜ TODO |
| Cancellation flow (keep data for 30 days) | 🔴 High | ⬜ TODO |
| Invoice emails | 🟡 Medium | ⬜ TODO |

**Pricing Implementation**:
```
Pro: $8/month or $80/year (2 months free)
Early Supporter: $6/month forever (first 100 users)
```

### 3.4 Web Dashboard

| Task | Priority | Status |
|------|----------|--------|
| Design simple dashboard UI | 🔴 High | ⬜ TODO |
| Memory list view with search | 🔴 High | ⬜ TODO |
| Memory detail view | 🔴 High | ⬜ TODO |
| Basic filtering (by project, type, date) | 🟡 Medium | ⬜ TODO |
| Simple graph visualization | 🟢 Low | ⬜ TODO |

**Dashboard MVP Features**:
1. Login/logout
2. List all memories (paginated)
3. Search memories
4. View memory details
5. Filter by project
6. Account/billing settings

### 3.5 Landing Page (memorygraph.dev)

| Task | Priority | Status |
|------|----------|--------|
| Register domain | 🔴 High | ⬜ TODO |
| Design landing page | 🔴 High | ⬜ TODO |
| Build with Astro/Next.js | 🔴 High | ⬜ TODO |
| Deploy to Vercel/Cloudflare | 🔴 High | ⬜ TODO |
| Pricing page | 🔴 High | ⬜ TODO |
| Documentation section | 🟡 Medium | ⬜ TODO |

**Landing Page Sections**:
1. Hero: "Never re-explain your project to your AI again"
2. Problem: The session amnesia pain
3. Solution: How memory-graph works (with GIF)
4. Social proof: Testimonials, GitHub stars
5. Pricing: Free / Pro / Team
6. CTA: "Get Started Free"

### 3.6 Launch Pro Tier

| Task | Priority | Status |
|------|----------|--------|
| Early supporter email campaign | 🔴 High | ⬜ TODO |
| Product Hunt launch | 🟡 Medium | ⬜ TODO |
| Blog post: "Introducing memory-graph Pro" | 🔴 High | ⬜ TODO |
| Discord announcement | 🔴 High | ⬜ TODO |

### Phase 3 Success Metrics
- [ ] 50+ Pro subscribers
- [ ] $400+ MRR
- [ ] <5% monthly churn
- [ ] Landing page: 2,000+ unique visitors
- [ ] Conversion rate: 2%+ (visitor → free install)
- [ ] Upgrade rate: 5%+ (free → pro)

---

## Phase 4: Team Features
**Timeline**: Weeks 15-22
**Goal**: Enable team collaboration, expand revenue

### 4.1 Shared Team Memory

| Task | Priority | Status |
|------|----------|--------|
| Team creation and management | 🔴 High | ⬜ TODO |
| Invite team members | 🔴 High | ⬜ TODO |
| Shared memory namespace | 🔴 High | ⬜ TODO |
| Personal vs team memory toggle | 🔴 High | ⬜ TODO |
| Team-wide search | 🔴 High | ⬜ TODO |

**User Experience**:
```bash
$ memorygraph team create "Acme Engineering"
✓ Team created. Invite link: https://memorygraph.dev/join/abc123

$ memorygraph team switch acme-engineering
✓ Now using team memory: Acme Engineering

# In Claude Code:
User: "Has anyone on the team solved Redis connection issues?"

Claude: Found 2 relevant memories from your team:

From @sarah (2 weeks ago):
"Redis connection pooling with max 10 connections fixed timeout issues"

From @mike (1 month ago):
"Setting TCP keepalive to 60s resolved dropped connections"
```

### 4.2 Knowledge Attribution

| Task | Priority | Status |
|------|----------|--------|
| Track who created each memory | 🔴 High | ⬜ TODO |
| Display attribution in search results | 🔴 High | ⬜ TODO |
| "Memories by [person]" filter | 🟡 Medium | ⬜ TODO |
| Activity feed (team level) | 🟡 Medium | ⬜ TODO |

### 4.3 Team Dashboard

| Task | Priority | Status |
|------|----------|--------|
| Team overview page | 🔴 High | ⬜ TODO |
| Member management | 🔴 High | ⬜ TODO |
| Team activity feed | 🟡 Medium | ⬜ TODO |
| Knowledge coverage view | 🟢 Low | ⬜ TODO |

### 4.4 Admin Controls

| Task | Priority | Status |
|------|----------|--------|
| Role-based permissions (admin, member) | 🔴 High | ⬜ TODO |
| Remove team members | 🔴 High | ⬜ TODO |
| Data retention settings | 🟡 Medium | ⬜ TODO |
| Billing management for team | 🔴 High | ⬜ TODO |

### Phase 4 Success Metrics
- [ ] 10+ team subscriptions
- [ ] 50+ team users
- [ ] $1,500+ MRR
- [ ] Average team size: 4+ users
- [ ] 1+ case study published

---

## Phase 5: Scale & Enterprise
**Timeline**: Weeks 23-32
**Goal**: Enterprise readiness, sustainable growth

### 5.1 Enterprise Features

| Task | Priority | Status |
|------|----------|--------|
| SSO (SAML/OIDC) | 🔴 High | ⬜ TODO |
| Audit logging | 🔴 High | ⬜ TODO |
| Self-hosted deployment option | 🟡 Medium | ⬜ TODO |
| SLA guarantees | 🔴 High | ⬜ TODO |
| Dedicated support | 🔴 High | ⬜ TODO |

### 5.2 Security & Compliance

| Task | Priority | Status |
|------|----------|--------|
| Security audit | 🔴 High | ⬜ TODO |
| SOC 2 Type I | 🟡 Medium | ⬜ TODO |
| GDPR compliance documentation | 🔴 High | ⬜ TODO |
| Data processing agreements | 🔴 High | ⬜ TODO |

### 5.3 Scale Infrastructure

| Task | Priority | Status |
|------|----------|--------|
| Performance optimization | 🟡 Medium | ⬜ TODO |
| Multi-region deployment | 🟡 Medium | ⬜ TODO |
| 99.9% uptime SLA | 🔴 High | ⬜ TODO |
| Disaster recovery plan | 🔴 High | ⬜ TODO |

### Phase 5 Success Metrics
- [ ] 3+ enterprise customers
- [ ] $5,000+ MRR
- [ ] 99.9% uptime achieved
- [ ] Security audit passed
- [ ] 1+ enterprise case study

---

## Financial Projections

### Revenue Model

| Tier | Price | Target Users (Y1) | MRR |
|------|-------|-------------------|-----|
| Free | $0 | 5,000 | $0 |
| Pro | $8/mo | 200 | $1,600 |
| Team | $12/user/mo | 100 users (20 teams) | $1,200 |
| Enterprise | Custom | 2 | $1,000 |
| **Total** | | | **$3,800** |

### Year 1 Milestones

| Month | Target MRR | Key Milestone |
|-------|------------|---------------|
| 3 | $0 | Launch, community building |
| 6 | $500 | Pro tier launch |
| 9 | $1,500 | Team tier launch |
| 12 | $3,800 | Enterprise pilots |

### Cost Structure (Monthly)

| Item | Phase 1-2 | Phase 3-4 | Phase 5 |
|------|-----------|-----------|---------|
| Infrastructure | $0 | $50 | $200 |
| Turso | $0 | $20 | $100 |
| Auth (Clerk) | $0 | $25 | $100 |
| Stripe fees | $0 | ~3% | ~3% |
| Domain/hosting | $20 | $20 | $50 |
| **Total** | **$20** | **~$120** | **~$450** |

---

## Risk Assessment

### Product Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users don't see value | Medium | High | User interviews, iterate on UX |
| Too complex to use | Medium | High | Simplify, reduce cognitive load |
| Free tier too generous | Low | Medium | Monitor conversion, adjust limits |
| Technical issues at scale | Low | High | Load testing, monitoring |

### Market Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Claude builds native memory | Medium | High | Support multiple AI agents |
| basic-memory dominates | Medium | Medium | Differentiate on coding-specific value |
| MCP protocol changes | Low | Medium | Abstract MCP layer, stay updated |
| Low willingness to pay | Medium | Medium | Validate pricing early, adjust |

### Mitigation Strategies

1. **Validate early**: Get 10 paying users before building team features
2. **Stay lightweight**: Don't over-engineer; ship fast, iterate
3. **Listen to users**: Weekly feedback review, act on patterns
4. **Multiple AI support**: Don't depend solely on Claude Code

---

## Success Metrics Summary

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|--------|---------|---------|---------|---------|---------|
| GitHub Stars | 100 | 250 | 500 | 1,000 | 2,000 |
| PyPI Downloads | 1,000 | 3,000 | 7,000 | 15,000 | 30,000 |
| Discord Members | 50 | 150 | 300 | 500 | 1,000 |
| Free Users | 100 | 500 | 2,000 | 4,000 | 5,000 |
| Pro Subscribers | - | - | 50 | 150 | 200 |
| Team Users | - | - | - | 50 | 100 |
| MRR | $0 | $0 | $500 | $1,500 | $3,800 |

---

## Immediate Next Steps

### This Week
- [ ] Create Discord server and add link to README
- [ ] Record 45-second asciinema demo
- [ ] Rewrite README intro with value-first language
- [ ] Prepare HN post for Monday/Tuesday launch

### Next Week
- [ ] Post to Hacker News
- [ ] Cross-post to Reddit (r/ClaudeAI, r/LocalLLaMA)
- [ ] Publish LinkedIn post
- [ ] Engage with all comments and feedback

### This Month
- [ ] Complete Phase 1 tasks
- [ ] Register memorygraph.dev domain
- [ ] Begin user interviews
- [ ] Start planning Phase 2 search improvements

---

## Appendix A: Tool Value Assessment

Each tool in memory-graph should answer "yes" to at least one:

1. **Does it save time?** (e.g., recall solutions faster)
2. **Does it prevent mistakes?** (e.g., surface what didn't work)
3. **Does it enable something impossible before?** (e.g., team knowledge sharing)
4. **Is it essential for the core workflow?** (e.g., store, search)

Tools that don't pass this test should be:
- Simplified into another tool
- Made automatic (not user-invoked)
- Removed

---

## Appendix B: Messaging Guidelines

### Do Say
- "Never re-explain your project"
- "Remember what worked"
- "Pick up where you left off"
- "Zero config, just works"
- "Your data stays on your machine"

### Don't Say
- "Graph-based" (technical jargon)
- "35+ relationship types" (overwhelming)
- "Knowledge graph" (enterprise-y)
- "Semantic memory" (academic)
- "MCP protocol" (unless technical context)

### Tone
- Friendly, not corporate
- Technical but accessible
- Confident but not arrogant
- Focus on outcomes, not features

---

## Appendix C: Competitive Positioning

### Against CLAUDE.md
> "CLAUDE.md is great for static instructions. memory-graph is for dynamic learnings—what worked, what failed, and why."

### Against basic-memory
> "basic-memory is a great general-purpose tool. memory-graph is purpose-built for coding workflows—tracking solutions, problems, and patterns."

### Against "no memory"
> "Stop re-explaining your project every session. memory-graph gives your AI assistant a memory that persists."

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2025 | Gregory Dickson | Initial roadmap |
| 2.0 | Dec 2025 | Gregory Dickson | Refocused on value over technical features; simplified messaging; clearer monetization path |
| 2.1 | Dec 2025 | Gregory Dickson | Elevated "Claude as the Interface" architecture; reorganized phases to prioritize search/recall; integrated semantic search strategy into Phase 2 |

---

*This roadmap is a living document. It will be updated based on user feedback, market conditions, and learnings.*
