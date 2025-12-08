# memory-graph Product Roadmap

**Document Version**: 4.0
**Last Updated**: December 2025
**Author**: Gregory Dickson
**Status**: Strategic Plan - ALIGNED WITH MEMORYGRAPH.DEV IMPLEMENTATION

---

## ⚠️ COMPETITIVE LANDSCAPE

**This version incorporates strategic responses to our key competitors in the AI agent memory space.**

### Competitor 1: Byterover Cipher (Direct MCP Competitor)

Cipher is an MCP-based memory layer for coding agents with 3.2K GitHub stars and a commercial cloud product (Byterover.dev). They target the exact same market as memory-graph.

**🚨 BREAKING UPDATE (Dec 3, 2025): Byterover CLI 0.3.1 Release**

Byterover has pivoted away from vector search! Key changes:
- **Context Tree**: New hierarchical memory structure (Domains → Topics → Context Files)
- **Agentic Search**: Replaced vector DB with agent-driven navigation
- **Deprecated ACE**: Removed their previous workflow due to "garbage in, garbage out" problems
- **New CLI**: `brv curate`, `brv query`, `brv pull` (team sync)

**Their stated reasoning for abandoning vectors:**
> "Vector DB and cosine similarity are not great at capturing complex and high-variance coding details... similarity search is strong at recall but often weaker at precision... retrieving a similar-looking function instead of the correct one can overload your context window."

> "Instead of flattening code into embeddings and hoping cosine similarity finds the right function, we let the agent navigate the codebase like a developer would."

**This validates our graph-first approach!** They're moving toward what we already do.

| Aspect | Cipher (v0.3.1) | memory-graph |
|--------|-----------------|--------------|
| License | Elastic 2.0 (restrictive) | Apache 2.0 ✅ |
| Language | Node.js | Python ✅ |
| Search | ~~Vectors~~ → Agentic Search | Graph-first + Semantic Navigation ✅ |
| Memory Structure | Context Tree (Domains/Topics) | Knowledge Graph (35+ typed relationships) ✅ |
| Relationships | Generic edges | 35+ typed relationships ✅ |
| GitHub Stars | 3,200+ | Growing |
| Cloud | Byterover.dev (live) | memorygraph.dev (in progress) |
| Team Sync | `brv pull` | Planned Phase 4 |

### Competitor 2: Zep/Graphiti (Temporal Knowledge Graph Leader)

Graphiti (by Zep AI, Y Combinator backed) is the state-of-the-art temporal knowledge graph framework with 20K+ GitHub stars. While not coding-specific, they've solved hard problems we can learn from.

| Aspect | Graphiti | memory-graph |
|--------|----------|--------------|
| License | Apache 2.0 | Apache 2.0 ✅ |
| Focus | General AI agents | Coding-specific ✅ |
| Temporal Model | Bi-temporal (advanced) ✅ | Basic → Phase 2 upgrade |
| Search | Hybrid (semantic + BM25 + graph) ✅ | Graph → Phase 2 hybrid |
| Dependencies | Neo4j required | SQLite (lightweight) ✅ |
| Benchmark | 94.8% DMR accuracy (SOTA) | Not yet benchmarked |
| GitHub Stars | 20,000+ | Growing |

**Key Graphiti innovations to study and adopt:**
- **Bi-temporal tracking**: Track both when a fact was true AND when we learned it
- **Hybrid search**: Combine semantic embeddings, BM25 keyword search, and graph traversal
- **Edge invalidation**: Mark outdated facts as invalid (don't delete), preserving history
- **Episode-based ingestion**: Structure memories as discrete episodes with provenance

### Key Competitive Gaps to Close

| Gap | Competitors Have | We Need | Priority | Phase |
|-----|-----------------|---------|----------|-------|
| Semantic Navigation | Cipher: Agentic Search | Enhanced navigation tools | 🔴 CRITICAL | 2 |
| Temporal Model | Graphiti: bi-temporal | Implement bi-temporal tracking | 🔴 HIGH | 2 |
| Cloud Product | Cipher: Byterover.dev, Zep: managed | memorygraph.dev | 🔴 CRITICAL | 3 |
| GitHub Stars | Cipher: 3.2K, Graphiti: 20K | Accelerate marketing | 🔴 HIGH | 1 |
| Team Sync | Cipher: `brv pull` (manual) | Cloud-native sync (automatic) | 🟡 MEDIUM | 3-4 |
| Benchmarks | Graphiti: DMR 94.8% | Run DMR benchmark | 🟡 MEDIUM | 2 |

**Note on Semantic Search**: Cipher has abandoned vector search in favor of agentic navigation (CLI 0.3.1). This validates our approach. We should focus on **Semantic Navigation** (enhanced tools for LLM-driven graph traversal) rather than rushing to add embeddings.

### Key Advantages to Leverage

| Advantage | Details | Marketing Action |
|-----------|---------|-----------------|
| **Apache 2.0 License** | True open source vs. Cipher's Elastic 2.0 | Blog post, prominent badge |
| **Typed Relationships** | 35+ semantic types vs. generic edges | Comparison demos |
| **Coding-Specific Types** | 8 entity types designed for dev workflows | Feature comparison |
| **Python Native** | AI/ML ecosystem majority | Target Python devs |
| **Lightweight** | SQLite default vs. Neo4j required | Performance benchmarks |
| **Test Coverage** | 93% (409 tests) | Quality messaging |

---

## Product Priorities (December 2025)

| # | Product | Priority | Phase | Notes |
|---|---------|----------|-------|-------|
| 1 | **LlamaIndex Integration** | 🔴 Critical | 3 | SDK expansion - highest strategic value |
| 2 | **LangChain/LangGraph Integration** | 🔴 Critical | 3 | SDK expansion - massive ecosystem reach |
| 3 | **Insights/Analytics** | 🔴 High | 3 | Dashboard analytics for cloud users |
| 4 | **VS Code Extension** | 🔴 High | 3-4 | Cloud-only, requires subscription |
| 5 | **CLI Tool** | 🟡 Medium | 2 | Enhanced CLI for local management |
| 6 | **Dashboard (Web UI)** | 🟡 Medium | 3 | app.memorygraph.dev |
| 7 | **CrewAI Integration** | 🟡 Medium | 3 | SDK expansion - multi-agent workflows |
| 8 | **GitHub Action** | 🟢 Low | 4 | CI/CD memory automation |
| 9 | **AutoGen Integration** | 🟢 Low | 5 | SDK expansion - Microsoft ecosystem |
| 10 | **Enterprise, Knowledge Importer, Mobile** | 🟢 Low | 5+ | Future enterprise features |

**Strategic Focus**: LlamaIndex and LangChain integrations are now **Critical** priority to capture the broader AI/ML framework ecosystem before competitors.

---

## Product Portfolio

| Product | Status | Revenue Model |
|---------|--------|---------------|
| **MCP Server** | ✅ Live | Open Source (adoption driver) |
| **Cloud Platform** | 🚧 In Progress | SaaS ($8-12/mo) |
| **SDK (Python)** | 🔜 Planned | Open Source + Enterprise |

---

## Product Implementation Details

### LlamaIndex Integration (🔴 Critical #1)

**Value Proposition**: "Graph-enhanced RAG for production applications"

**Why LlamaIndex First**:
- 30K+ GitHub stars, massive RAG ecosystem
- RAG is THE dominant LLM application pattern
- Natural fit: RAG needs context, we provide structured context with relationships
- No major graph-based memory competitor in LlamaIndex ecosystem

**Integration Components**:

| Component | LlamaIndex Class | Purpose |
|-----------|------------------|---------|
| `MemoryGraphVectorStore` | `BasePydanticVectorStore` | Graph-aware document storage |
| `MemoryGraphRetriever` | `BaseRetriever` | Relationship-enhanced retrieval |
| `MemoryGraphChatMemory` | `BaseChatStore` | Persistent conversation memory |
| `MemoryGraphIndex` | `BaseIndex` | Knowledge graph index type |

**Code Example**:
```python
from llama_index.core import VectorStoreIndex
from memorygraph.integrations.llamaindex import (
    MemoryGraphVectorStore,
    MemoryGraphRetriever
)

# As Vector Store with relationship awareness
vector_store = MemoryGraphVectorStore(
    api_key="mg_...",
    include_relationships=True,  # Our differentiator!
    relationship_depth=2
)

index = VectorStoreIndex.from_documents(documents, vector_store=vector_store)

# Queries automatically traverse relationships
response = index.as_query_engine().query("What caused the authentication failures?")
# Returns context from: Error → CAUSED_BY → Config → RELATED_TO → Similar issues
```

**Unique Value vs Plain Vector Stores**:
```
Standard RAG:  Query → Vector Search → Top K Documents → Response

MemoryGraph RAG:  Query → Vector Search → Top K Documents
                                              ↓
                                    Relationship Expansion
                                              ↓
                         Related Solutions, Causes, Dependencies
                                              ↓
                                    Enriched Response
```

---

### LangChain/LangGraph Integration (🔴 Critical #2)

**Value Proposition**: "Drop-in memory for LangChain agents with relationship intelligence"

**Why LangChain/LangGraph**:
- LangChain: 95K+ GitHub stars (largest LLM framework)
- LangGraph: Fast-growing for stateful agent applications
- Agents need memory more than simple chains
- Cipher has NO framework integrations

**Integration Components**:

| Component | LangChain/LangGraph Class | Purpose |
|-----------|---------------------------|---------|
| `MemoryGraphMemory` | `BaseMemory` | Conversation memory |
| `MemoryGraphChatMessageHistory` | `BaseChatMessageHistory` | Message persistence |
| `MemoryGraphRetriever` | `BaseRetriever` | Document retrieval |
| `MemoryGraphCheckpointer` | `BaseCheckpointSaver` | LangGraph state |
| `MemoryGraphStore` | `BaseStore` | LangGraph Store |

**Code Examples**:

```python
# LangChain: As Conversation Memory
from langchain.memory import MemoryGraphMemory
from langchain.agents import create_react_agent

memory = MemoryGraphMemory(
    api_key="mg_...",
    return_relationships=True,
    relationship_summary=True  # Include "You previously solved X with Y"
)

agent = create_react_agent(llm, tools, memory=memory)
```

```python
# LangGraph: As State Checkpointer
from langgraph.graph import StateGraph
from memorygraph.integrations.langgraph import MemoryGraphCheckpointer

checkpointer = MemoryGraphCheckpointer(
    api_key="mg_...",
    store_relationships=True
)

graph = StateGraph(AgentState)
app = graph.compile(checkpointer=checkpointer)

# State persists across sessions with relationship context
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke({"messages": [HumanMessage("Continue where we left off")]}, config)
```

---

### Insights/Analytics Dashboard (🔴 High #3)

**Value Proposition**: "Discover what your coding agent has learned"

**Features**:
- **Knowledge Gap Detection**: "You have many errors about X but no solutions"
- **Pattern Discovery**: "These 5 solutions all use retry logic"
- **Expertise Mapping**: "Most of your auth knowledge came from Project A"
- **Stale Knowledge Alerts**: "This solution was created 6 months ago, still valid?"
- **Team Knowledge Distribution**: Who knows what
- **Temporal Insights**: How understanding evolved over time

**Dashboard Mockup**:
```
┌─────────────────────────────────────────────────────────────┐
│  MemoryGraph Insights                                       │
├─────────────────────────────────────────────────────────────┤
│  Knowledge Health Score: 78/100                             │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ 🔴 15 Unsolved  │  │ 🟢 47 Solutions │                   │
│  │    Errors       │  │    Documented   │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                             │
│  Top Knowledge Gaps:                                        │
│  • Authentication (5 errors, 1 solution)                    │
│  • Database timeouts (3 errors, 0 solutions)                │
│                                                             │
│  Emerging Patterns:                                         │
│  • Retry logic used in 12 solutions (+40% this month)       │
│  • Circuit breaker pattern gaining adoption                 │
└─────────────────────────────────────────────────────────────┘
```

**Revenue Model**: Premium tier feature (+$5/mo or included in Team plan)

---

### VS Code Extension (🔴 High #4)

**Value Proposition**: "Your coding memory, where you code"

**Business Model**: ☁️ **Cloud-Only, Subscription Required**
- Requires active MemoryGraph Cloud subscription (Pro or Team tier)
- No local/offline mode - all data synced via memorygraph.dev
- Drives cloud subscription revenue
- Simplifies architecture (no local backend complexity)

**Rationale for Cloud-Only**:
1. **Revenue Driver**: VS Code has massive reach - convert users to paying subscribers
2. **Simplified Development**: Single backend (cloud API), no local SQLite/Neo4j support needed
3. **Better UX**: Real-time sync across devices, no setup complexity
4. **Team Features**: Seamless team memory sharing built-in

**Features**:
- **Memory Panel**: Sidebar showing relevant memories for current file
- **Inline Suggestions**: "You solved a similar error in Project X..."
- **Quick Capture**: Right-click → "Save to MemoryGraph"
- **Hover Context**: Hover over error → see related solutions
- **Graph Explorer**: Visual graph navigation in VS Code
- **GitHub Copilot Integration**: Memory-enhanced completions
- **Team Memories**: See team knowledge inline (Team tier)

---

### CLI Tool (🟡 Medium #5)

**Value Proposition**: "Memory management from your terminal"

**Commands**:
```bash
mg add "Fixed timeout with retry logic" --type solution --tags redis,timeout
mg search "timeout" --type error
mg relate mem123 SOLVES mem456
mg chain mem123                    # Show relationship chain
mg sync                            # Cloud sync
mg export --format json
mg stats                           # Quick analytics
mg visualize                       # Opens web dashboard
```

---

## Revenue Model

| Product | Model | Price Point |
|---------|-------|-------------|
| MCP Server | Open Source | Free |
| Cloud Platform | SaaS | $8-12/mo |
| Dashboard | Included in Cloud | - |
| SDK | Open Source | Free |
| LlamaIndex/LangChain | Open Source | Free (drives Cloud) |
| CLI | Open Source | Free |
| **VS Code Extension** | **Cloud-Only** | **Requires Pro/Team subscription** |
| Insights | Premium Feature | +$5/mo or Team plan |
| Enterprise Server | License | $10K-50K/year |

**Target Revenue Mix (Year 2)**:
- Cloud Subscriptions: 60%
- Enterprise Licenses: 30%
- Professional Services: 10%

---

## Success Metrics

| Metric | Current | Year 1 Target | Year 2 Target |
|--------|---------|---------------|---------------|
| GitHub Stars | ~100 | 2,000 | 5,000 |
| PyPI Downloads/month | ~500 | 10,000 | 50,000 |
| Cloud Subscribers | 0 | 200 | 1,000 |
| MRR | $0 | $2,000 | $15,000 |
| Framework Integrations | 1 (MCP) | 4 | 6 |

---

## Partnership Opportunities

### Technology Partnerships

| Partner | Opportunity | Value |
|---------|-------------|-------|
| **LangChain** | Official memory integration | Large community access |
| **LlamaIndex** | Recommended retrieval backend | RAG market capture |
| **CrewAI** | Recommended memory provider | Multi-agent positioning |
| **Anthropic** | Claude Code showcase | Credibility, visibility |
| **Cursor** | Built-in memory option | IDE market access |

### Distribution Partnerships

| Partner | Opportunity | Value |
|---------|-------------|-------|
| **Smithery** | Featured MCP server | Discovery |
| **Awesome MCP** | Featured listing | Credibility |
| **AI Tool Directories** | Listings | SEO, discovery |

---

## Executive Summary

memory-graph is a lightweight memory server for AI coding agents. It helps coding assistants like Claude Code remember what worked, avoid past mistakes, and maintain context across sessions.

### Vision Statement

> **"Never re-explain your project to your AI again."**

### Revised Competitive Positioning

```
                    MCP Memory for Coding Agents
                    
     Vector-First                    Graph-First
     (Similarity)                   (Relationships)
           │                            │
    ┌──────┴──────┐              ┌──────┴──────┐
    │   Cipher    │              │ memory-graph│
    │ (Byterover) │              │             │
    ├─────────────┤              ├─────────────┤
    │ • 3.2K stars│              │ • Apache 2.0│
    │ • Vectors   │              │ • 35+ types │
    │ • Node.js   │              │ • Python    │
    │ • Elastic   │              │ • 93% tests │
    └─────────────┘              └─────────────┘
    
              Graphiti (Zep)
           ┌─────────────────┐
           │ • 20K stars     │
           │ • Bi-temporal   │
           │ • Hybrid search │
           │ • Neo4j required│
           │ • General focus │
           └─────────────────┘
```

**Our Position**: "Memory that understands code relationships, not just similarity"

---

## REVISED PHASE STRUCTURE

### Phase 0: Competitive Response Sprint ⚡ NEW
**Timeline**: Weeks 1-2 (IMMEDIATE)
**Goal**: Close critical gaps, establish differentiation

### Phase 1: Launch & Community (Updated)
**Timeline**: Weeks 3-5
**Goal**: Establish presence, outpace Cipher in adoption velocity

### Phase 2: Search & Temporal Model (ELEVATED PRIORITY)
**Timeline**: Weeks 6-9
**Goal**: Close semantic search gap, implement bi-temporal tracking (learn from Graphiti)

### Phase 3: Cloud Launch (ACCELERATED)
**Timeline**: Weeks 10-14
**Goal**: Launch memorygraph.dev before Byterover gains more ground

### Phase 4: Team Features
**Timeline**: Weeks 15-20
**Goal**: Match Cipher's workspace memory, add unique value

### Phase 5: Scale & Enterprise
**Timeline**: Weeks 21-28
**Goal**: Enterprise readiness, sustainable growth

---

## Phase 0: Competitive Response Sprint ⚡
**Timeline**: Weeks 1-2 (START IMMEDIATELY)
**Goal**: Close critical gaps, establish clear differentiation

### 0.1 License Differentiation Campaign

| Task | Priority | Status |
|------|----------|--------|
| Add prominent "Apache 2.0" badge to README | 🔴 CRITICAL | ⬜ TODO |
| Blog post: "Why memory-graph is True Open Source" | 🔴 CRITICAL | ⬜ TODO |
| Comparison page: memory-graph vs Cipher licensing | 🔴 CRITICAL | ⬜ TODO |
| Update all marketing to highlight Apache 2.0 | 🔴 HIGH | ⬜ TODO |

**Key Message**: "Cipher uses Elastic License 2.0 which restricts competitive use. memory-graph is Apache 2.0 - use it however you want, forever."

### 0.2 Typed Relationships Showcase

| Task | Priority | Status |
|------|----------|--------|
| Create visual diagram: "35+ relationship types" | 🔴 CRITICAL | ⬜ TODO |
| Demo video: "How relationships enable smarter recall" | 🔴 HIGH | ⬜ TODO |
| Blog post: "Why Graph Relationships Beat Vector Similarity" | 🔴 HIGH | ⬜ TODO |
| Add relationship examples to README | 🔴 HIGH | ⬜ TODO |

**Example Showcase**:
```
Cipher: "Found 5 documents similar to 'timeout'"

memory-graph: "Found TimeoutError which was SOLVED by RetryWithBackoff,
              which DEPENDS_ON ExponentialBackoff, which is USED_IN 
              PaymentService and AuthService"
```

### 0.3 Competitive Comparison Page

| Task | Priority | Status |
|------|----------|--------|
| Create docs/COMPARISON.md | 🔴 CRITICAL | ⬜ TODO |
| Feature matrix: memory-graph vs Cipher vs Graphiti | 🔴 CRITICAL | ⬜ TODO |
| Honest assessment (acknowledge their strengths) | 🔴 HIGH | ⬜ TODO |
| Migration guide from Cipher | 🟡 MEDIUM | ⬜ TODO |

### 0.4 Smithery Marketplace Listing

Cipher is listed on Smithery. We need to be there too.

| Task | Priority | Status |
|------|----------|--------|
| Create Smithery listing | 🔴 CRITICAL | ⬜ TODO |
| Optimize listing description | 🔴 HIGH | ⬜ TODO |
| Add installation via Smithery to README | 🔴 HIGH | ⬜ TODO |

### 0.5 SDK Foundation (Pre-work for SDK Expansion)

Begin laying groundwork for SDK that will differentiate us from Cipher's MCP-only approach.

| Task | Priority | Status |
|------|----------|--------|
| Design SDK API surface | 🔴 HIGH | ⬜ TODO |
| Create memorygraphsdk package stub | 🟡 MEDIUM | ⬜ TODO |
| Document SDK roadmap publicly | 🟡 MEDIUM | ⬜ TODO |

### Phase 0 Success Metrics
- [ ] Apache 2.0 prominently displayed everywhere
- [ ] Comparison page live (including Graphiti)
- [ ] Smithery listing active
- [ ] 2+ blog posts published (license, relationships)
- [ ] SDK roadmap announced

---

## Phase 1: Launch & Community (UPDATED)
**Timeline**: Weeks 3-5
**Goal**: Establish presence, outpace Cipher adoption velocity

### 1.1 Aggressive Messaging Update

| Before | After |
|--------|-------|
| "Lightweight memory server" | "The Python-native memory for AI coding agents" |
| "Graph-based architecture" | "Memory that understands code relationships" |
| Generic value props | Direct Cipher comparison points |

**New README Structure**:
```
1. Hero: "Never re-explain your project" + Apache 2.0 badge
2. "Why memory-graph over alternatives?" (vs Cipher, basic-memory)
3. 30-second install
4. GIF demo
5. "What makes us different" (typed relationships, Python, license)
6. Getting started
```

### 1.2 Visual Demo (Anti-Cipher)

| Task | Priority | Status |
|------|----------|--------|
| Demo showing relationship traversal (Cipher can't do this) | 🔴 CRITICAL | ⬜ TODO |
| Side-by-side: vector search vs graph query | 🔴 HIGH | ⬜ TODO |
| "Problem → Solution" chain demo | 🔴 HIGH | ⬜ TODO |

**Demo Script** (60 seconds):
```
1. "Let's find what solved our timeout issues"
2. memory-graph returns: TimeoutError SOLVED_BY RetryWithBackoff
3. "What else uses this pattern?"
4. Graph traversal shows: Used in 3 services
5. "What caused the original error?"
6. Shows: APIRateLimiting CAUSES TimeoutError
7. End: "Relationships reveal context. Vectors just find similarity."
```

### 1.3 Launch Campaign (Cipher-Aware)

| Task | Priority | Status |
|------|----------|--------|
| HN post emphasizing Apache 2.0 + typed relationships | 🔴 CRITICAL | ⬜ TODO |
| Reddit post with Cipher comparison (respectful) | 🔴 HIGH | ⬜ TODO |
| LinkedIn targeting Python AI/ML developers | 🔴 HIGH | ⬜ TODO |
| Twitter thread: "Why we chose Apache 2.0" | 🔴 HIGH | ⬜ TODO |

**Updated HN Post**:
```
Title: Show HN: memory-graph – Apache 2.0 memory for Claude Code with typed relationships

Comment:
I built memory-graph because AI coding assistants forget everything between sessions.

What makes it different:
- 35+ typed relationships (SOLVES, CAUSES, DEPENDS_ON) - not just vector similarity
- Apache 2.0 license - truly open, no restrictions
- Python-native - fits the AI/ML ecosystem
- 93% test coverage - production quality

When you ask "what solved the timeout issue?", memory-graph doesn't just find 
similar documents. It traces: TimeoutError → SOLVED_BY → RetryWithBackoff → 
USED_IN → PaymentService.

Install:
  pip install memorygraphMCP
  claude mcp add memorygraph

Local SQLite, works offline, your data stays private.

https://github.com/gregorydickson/memory-graph

There's another tool in this space (Cipher) with more stars, but it uses 
Elastic License and is Node.js only. We chose Apache 2.0 and Python deliberately.
```

### 1.4 Community Building (Outpace Cipher)

| Task | Priority | Status |
|------|----------|--------|
| Discord server with active engagement | 🔴 CRITICAL | ⬜ TODO |
| Weekly "office hours" in Discord | 🔴 HIGH | ⬜ TODO |
| Showcase channel for user implementations | 🔴 HIGH | ⬜ TODO |
| Contribution guide for community PRs | 🟡 MEDIUM | ⬜ TODO |

### Phase 1 Success Metrics
- [ ] 200+ GitHub stars (vs Cipher's 3.2K - start closing gap)
- [ ] 100+ Discord members
- [ ] 2,000+ PyPI downloads
- [ ] HN post 100+ points
- [ ] 5+ mentions comparing us favorably to Cipher
- [ ] Smithery listing with 50+ installs

---

## Phase 2: Semantic Navigation & Temporal Model (ELEVATED PRIORITY)
**Timeline**: Weeks 6-9
**Goal**: Implement semantic navigation (validated by Cipher's pivot), add bi-temporal tracking (learn from Graphiti)

### Critical Strategic Insight

**Cipher abandoned vector search in v0.3.1!** They now use "Agentic Search" - letting the LLM navigate rather than relying on embeddings. This validates our graph-first approach.

Our strategy: Instead of adding embeddings, enhance our tools so Claude can navigate our knowledge graph semantically. Claude already understands language, synonyms, and intent - we just need better navigation tools.

### 2.1 Study Graphiti Architecture

Before implementing, study how Graphiti solved these problems.

| Task | Priority | Status |
|------|----------|--------|
| Read Graphiti paper: "Zep: A Temporal Knowledge Graph Architecture" | 🔴 CRITICAL | ⬜ TODO |
| Review Graphiti source code (Apache 2.0, can learn from it) | 🔴 CRITICAL | ⬜ TODO |
| Document key patterns: bi-temporal model, hybrid search, edge invalidation | 🔴 HIGH | ⬜ TODO |
| Identify what we can adopt vs. what's overkill for our use case | 🔴 HIGH | ⬜ TODO |
| Write internal technical spec based on learnings | 🔴 HIGH | ⬜ TODO |

**Key Graphiti concepts to understand:**
- **Bi-temporal model**: `t_valid` (when fact was true) vs. `t_invalid` (when superseded)
- **Episode-based ingestion**: Each memory is tied to a discrete episode with provenance
- **Edge invalidation**: Contradicting facts invalidate old edges, don't delete them
- **Hybrid retrieval**: Semantic + BM25 + graph traversal without LLM calls at query time

### 2.2 Implement Bi-Temporal Tracking

Adopt Graphiti's temporal model for our schema.

| Task | Priority | Status |
|------|----------|--------|
| Design bi-temporal schema for memory-graph | 🔴 CRITICAL | ⬜ TODO |
| Add `valid_from` timestamp to relationships | 🔴 CRITICAL | ⬜ TODO |
| Add `valid_until` timestamp to relationships (NULL = still valid) | 🔴 CRITICAL | ⬜ TODO |
| Add `recorded_at` timestamp (when we learned the fact) | 🔴 CRITICAL | ⬜ TODO |
| Implement edge invalidation (mark old facts invalid on contradiction) | 🔴 HIGH | ⬜ TODO |
| Add point-in-time query support ("what did we know on date X?") | 🟡 MEDIUM | ⬜ TODO |
| Migration script for existing databases | 🔴 HIGH | ⬜ TODO |

**Bi-Temporal Schema Design:**
```sql
-- Current: relationships table
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    from_entity_id TEXT,
    to_entity_id TEXT,
    relationship_type TEXT,
    created_at TIMESTAMP,
    -- ... existing fields
);

-- New: bi-temporal relationships table
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    from_entity_id TEXT,
    to_entity_id TEXT,
    relationship_type TEXT,
    
    -- Bi-temporal fields (inspired by Graphiti)
    valid_from TIMESTAMP NOT NULL,      -- When the fact became true
    valid_until TIMESTAMP,              -- When the fact stopped being true (NULL = still valid)
    recorded_at TIMESTAMP NOT NULL,     -- When we learned this fact
    invalidated_by TEXT,                -- ID of relationship that superseded this one
    
    -- Existing fields
    created_at TIMESTAMP,
    -- ...
);

-- Index for temporal queries
CREATE INDEX idx_relationships_temporal ON relationships(valid_from, valid_until);
```

**Use Cases Enabled:**
- "What solutions were we using before we switched to Redis?"
- "Show me how our understanding evolved over time"
- "What did we know about this problem last month?"

### 2.3 Semantic Navigation (Agentic Search Alternative)

Instead of embeddings, we implement enhanced tools for LLM-driven navigation. This approach is validated by Cipher's pivot away from vectors.

**Philosophy**: Claude already understands language semantically. We don't need to embed "timeout" to find "connection error" - Claude knows they're related. We just need tools that let Claude navigate our graph intelligently.

| Task | Priority | Status |
|------|----------|--------|
| Add `browse_memory_types` tool - show entity types with counts | 🔴 CRITICAL | ⬜ TODO |
| Add `browse_by_project` tool - navigate by project context | 🔴 CRITICAL | ⬜ TODO |
| Add `find_chain` tool - auto-traverse SOLVES/CAUSES/DEPENDS_ON | 🔴 CRITICAL | ⬜ TODO |
| Add `contextual_search` tool - search within related memories | 🔴 HIGH | ⬜ TODO |
| Add `browse_domains` tool - list high-level categories | 🔴 HIGH | ⬜ TODO |
| Implement intent classification for queries | 🟡 MEDIUM | ⬜ TODO |
| Add "why this result?" explanations | 🟡 MEDIUM | ⬜ TODO |

**New Navigation Tools**:
```python
# Enhanced tools for semantic navigation
new_tools = [
    "browse_memory_types",   # "Show me all error types" → lists errors with counts
    "browse_by_project",     # Navigate memories by project context
    "browse_domains",        # High-level categories (like Cipher's Context Tree)
    "find_chain",            # "What solved X?" → auto-traverses SOLVES relationships
    "contextual_search",     # Search only within related memories
    "trace_dependencies",    # Follow DEPENDS_ON chains
]
```

**Semantic Navigation Flow** (vs Cipher's Agentic Search):
```
User: "What solved the timeout issue?"
         │
         ▼
Claude analyzes intent: "find solution to timeout problem"
         │
         ▼
Claude uses navigation tools:
  1. search_memories(type="error", query="timeout")
     → finds TimeoutError entity
  2. find_chain(entity_id, relationship="SOLVES") 
     → finds RetryWithBackoff solution
  3. get_related(solution_id, relationship="DEPENDS_ON")
     → finds ExponentialBackoff dependency
         │
         ▼
Result: "TimeoutError was SOLVED_BY RetryWithBackoff,
        which DEPENDS_ON ExponentialBackoff, 
        USED_IN PaymentService and AuthService"
        
        + Temporal: "Valid since 2024-01-15"
```

**Why This Beats Embeddings**:
- No embedding model dependency (stays lightweight)
- No vector DB overhead
- Claude's semantic understanding is better than cosine similarity for code
- Relationship traversal provides context embeddings can't
- Validates Cipher's conclusion: "precision is critical for code"

### 2.4 Optional Embedding Support (Future)

Keep embeddings as optional enhancement, not core requirement.

| Task | Priority | Status |
|------|----------|--------|
| Design optional embedding interface | 🟡 MEDIUM | ⬜ TODO |
| Add sentence-transformers as optional dependency | 🟡 MEDIUM | ⬜ TODO |
| SQLite vector storage (sqlite-vec) for those who want it | 🟡 MEDIUM | ⬜ TODO |

**Key Decision**: Embeddings are optional. Default is semantic navigation via enhanced tools. Users who want vectors can enable them, but it's not required.

### 2.5 Search UX Improvements

| Task | Priority | Status |
|------|----------|--------|
| Natural language query support | 🔴 HIGH | ⬜ TODO |
| Auto-suggest completions | 🟡 MEDIUM | ⬜ TODO |
| Search history | 🟡 MEDIUM | ⬜ TODO |
| Saved searches | 🟢 LOW | ⬜ TODO |

### 2.6 Marketing: "Semantic Navigation + Relationships + Time"

| Task | Priority | Status |
|------|----------|--------|
| Blog: "Why We Chose Semantic Navigation Over Vectors" | 🔴 HIGH | ⬜ TODO |
| Blog: "Cipher Abandoned Vectors - Here's Why We Agree" | 🔴 HIGH | ⬜ TODO |
| Blog: "Temporal Memory: Know What Changed and When" | 🔴 HIGH | ⬜ TODO |
| Demo video: semantic navigation in action | 🔴 HIGH | ⬜ TODO |
| Update comparison page with navigation + temporal capabilities | 🔴 HIGH | ⬜ TODO |

**Marketing Angle**: "Even Cipher admits vectors don't work for code. We've known this all along - that's why we built a knowledge graph with typed relationships."

### Phase 2 Success Metrics
- [ ] Bi-temporal schema implemented and documented
- [ ] New navigation tools implemented (browse_memory_types, find_chain, etc.)
- [ ] Semantic navigation demo video published
- [ ] <50ms p95 latency for navigation queries (faster than vector search!)
- [ ] Point-in-time queries working
- [ ] User feedback: "navigation feels natural, like browsing code"
- [ ] 500+ GitHub stars

---

## Phase 3: Cloud Launch (ACCELERATED)
**Timeline**: Weeks 10-14
**Goal**: Launch memorygraph.dev before Byterover consolidates market

### Implementation Status

> **Note**: Cloud infrastructure is being built in the separate `memorygraph.dev` repository.
> See `/memorygraph.dev/docs/planning/` for detailed workplans.

### 3.1 Cloud Infrastructure ✅ COMPLETE

Reference: memorygraph.dev Workplan 1-3

| Task | Priority | Status |
|------|----------|--------|
| GCP project setup (memorygraph-prod) | 🔴 CRITICAL | ✅ DONE |
| Cloud SQL PostgreSQL 15 (34.57.139.115) | 🔴 CRITICAL | ✅ DONE |
| FalkorDB self-hosted (34.57.52.93:6379) | 🔴 CRITICAL | ✅ DONE |
| Auth API (FastAPI on Cloud Run) | 🔴 CRITICAL | ✅ DONE |
| Graph API (FastAPI on Cloud Run) | 🔴 CRITICAL | 🚧 IN PROGRESS |
| Marketing site (memorygraph.dev) | 🔴 CRITICAL | ✅ DONE |

**Architecture Decisions Made** (see memorygraph.dev ADRs):
- **ADR-001**: FastAPI + GCP + FalkorDB + Stripe (not Supabase)
- **ADR-002**: Graph-per-tenant isolation for multi-tenancy
- **ADR-003**: API key + JWT authentication (not Supabase Auth)
- **ADR-004**: Static site on Cloud Storage + CDN (Cloudflare Pages)
- **ADR-006**: FalkorDB self-hosted on GCE (not Turso)

### 3.2 Competitive Pricing

Match or beat Byterover's pricing (if known). Our target:

| Tier | Price | vs. Competitor |
|------|-------|----------------|
| Free | $0 | Match Cipher free tier |
| Pro | $8/month | Competitive |
| Team | $12/user/month | Competitive |

### 3.3 Landing Page (memorygraph.dev) ✅ COMPLETE

| Task | Priority | Status |
|------|----------|--------|
| Domain registration | 🔴 CRITICAL | ✅ DONE |
| Landing page with comparison section | 🔴 CRITICAL | ✅ DONE |
| "Why Choose memory-graph" (vs alternatives) | 🔴 HIGH | ✅ DONE |
| Pricing page | 🔴 HIGH | ✅ DONE |
| Spanish translations | 🟡 MEDIUM | ✅ DONE |
| Documentation hub | 🔴 HIGH | ✅ DONE |

**Landing Page Must Include**:
1. Apache 2.0 badge prominently displayed
2. "35+ typed relationships" highlight
3. "Bi-temporal tracking" as advanced feature
4. Side-by-side comparison with "other tools"
5. Python-native messaging
6. Clear pricing vs. alternatives

### 3.4 SDK Launch (Differentiation from Cipher) 🔴 CRITICAL PRIORITY

Cipher is MCP-only. Our SDK expands to LangChain, LlamaIndex, CrewAI, etc.

Reference: memorygraph.dev Workplans 8-10

| Task | Priority | Status |
|------|----------|--------|
| memorygraphsdk core package | 🔴 CRITICAL | 🔜 PLANNED (after Workplan 4) |
| **LlamaIndex integration** | 🔴 CRITICAL | 🔜 PLANNED (Priority #1) |
| **LangChain/LangGraph integration** | 🔴 CRITICAL | 🔜 PLANNED (Priority #2) |
| CrewAI integration | 🟡 MEDIUM | 🔜 ON-DEMAND |
| Semantic search capability | 🔴 HIGH | 🔜 PLANNED (Workplan 10) |
| Publish to PyPI | 🔴 HIGH | 🔜 PLANNED |

**Key Message**: "memory-graph works everywhere - MCP, LlamaIndex, LangChain, CrewAI, and more. Not locked into one protocol."

**Strategic Rationale**: LlamaIndex and LangChain integrations are now **Critical** priority because:
- LlamaIndex: Dominant in RAG/retrieval pipelines - perfect fit for memory-graph
- LangChain: Massive ecosystem (100K+ GitHub stars) - SDK integration captures huge market

### 3.5 Remaining Cloud Work (memorygraph.dev)

| Workplan | Status | Scope |
|----------|--------|-------|
| 4: Graph Service | 🚧 Ready to start | FastAPI graph service, multi-tenant isolation |
| 5: MCP Integration | Blocked by 4 | Cloud backend adapter for MCP server |
| 6: User Dashboard | 🚧 Ready to start | Next.js dashboard at app.memorygraph.dev |
| 7: Operations | Blocked by 4 | Monitoring, alerting, security hardening |

### Phase 3 Success Metrics
- [x] memorygraph.dev live ✅
- [ ] 50+ Pro subscribers
- [ ] SDK published with 2+ framework integrations
- [ ] $400+ MRR
- [ ] 1,000+ GitHub stars
- [ ] Feature parity with Byterover cloud (core features)

---

## Phase 4: Team Features
**Timeline**: Weeks 15-20
**Goal**: Match Cipher's workspace memory, add unique value

### 4.1 Automatic Memory Scoping (Zero User Configuration)

Memories should automatically be scoped correctly without user input. The system infers scope from content and context.

**Three Scope Levels:**
- **User-scoped**: Personal preferences, individual learnings (visible only to user)
- **Project-scoped**: Code patterns, errors, solutions for a specific codebase (visible to project members)
- **Team-scoped**: Shared conventions, architecture decisions, team standards (visible to all team members)

**Automatic Scope Detection:**

| Signal | Inferred Scope | Example |
|--------|---------------|--------|
| References specific file paths | Project | "Fixed bug in `/src/auth/oauth.py`" |
| References project-specific entities | Project | "PaymentService timeout issue" |
| General coding pattern (no project refs) | Team | "Use exponential backoff for retries" |
| Team convention/standard language | Team | "We use snake_case for Python" |
| Personal preference markers | User | "I prefer...", "My typical..." |
| Created in team workspace context | Team | Working in shared repo |

| Task | Priority | Status |
|------|----------|--------|
| Design scope inference algorithm | 🔴 CRITICAL | ⬜ TODO |
| Implement content-based scope detection | 🔴 CRITICAL | ⬜ TODO |
| Implement context-based scope detection | 🔴 CRITICAL | ⬜ TODO |
| Add project_path tracking to memories | 🔴 HIGH | ⬜ TODO |
| Scope inheritance via relationships | 🔴 HIGH | ⬜ TODO |
| Admin override for mis-scoped memories | 🟡 MEDIUM | ⬜ TODO |

**Scope Inference Logic:**
```python
def infer_scope(memory: Memory, context: Context) -> Scope:
    # 1. Project markers (file paths, specific entities)
    if has_project_paths(memory) or references_project_entities(memory):
        return Scope.PROJECT
    
    # 2. Memory type patterns
    if memory.type in ["error", "fix", "file_context"]:
        return Scope.PROJECT  # Errors/fixes are project-specific
    
    if memory.type in ["code_pattern", "workflow"] and is_generalizable(memory):
        return Scope.TEAM  # Reusable patterns → team
    
    # 3. Personal indicators
    if has_personal_markers(memory) or memory.type == "general":
        return Scope.USER
    
    # 4. Relationship inheritance
    if memory.solves(project_scoped_problem):
        return Scope.PROJECT
    
    # 5. Default to project (safest - not too broad, not too narrow)
    return Scope.PROJECT
```

**Key Principle**: Users never manually choose scope. The system "just works."

### 4.2 Team Workspaces

Cipher v0.3.1 uses `brv pull` for manual team sync. Our cloud-first approach is simpler: **team members just connect to the same cloud workspace - no sync commands needed.**

| Our Approach | Cipher's Approach |
|--------------|-------------------|
| Connect to team workspace → automatic sync | Manual `brv pull` / `brv push` |
| Real-time collaboration | Batch sync with conflicts |
| No local state management | Must manage local vs remote |
| Works offline, syncs when online | Requires explicit sync |

**Key Insight**: Cloud-native beats sync commands. This is a UX advantage over Cipher.

| Task | Priority | Status |
|------|----------|--------|
| Team workspaces in cloud (from Phase 3) | 🔴 CRITICAL | ⬜ TODO |
| Team member management & invitations | 🔴 HIGH | ⬜ TODO |
| Seamless workspace switching (personal ↔ team) | 🔴 HIGH | ⬜ TODO |
| Team-wide search across all scopes | 🔴 HIGH | ⬜ TODO |
| Offline mode with automatic cloud sync | 🟡 MEDIUM | ⬜ TODO |
| Real-time memory updates across team | 🟡 MEDIUM | ⬜ TODO |

### 4.3 Beat Cipher with Better Attribution

Cipher has basic team sharing. We can add:

| Task | Priority | Status |
|------|----------|--------|
| Knowledge attribution (who discovered what) | 🔴 HIGH | ⬜ TODO |
| Team activity feed | 🟡 MEDIUM | ⬜ TODO |
| "Trending solutions" in team | 🟡 MEDIUM | ⬜ TODO |
| Expertise mapping (who knows what) | 🟢 LOW | ⬜ TODO |

### 4.4 RBAC (Match Cipher)

| Task | Priority | Status |
|------|----------|--------|
| Role-based permissions | 🔴 HIGH | ⬜ TODO |
| Admin controls | 🔴 HIGH | ⬜ TODO |
| Audit logging | 🟡 MEDIUM | ⬜ TODO |

### Phase 4 Success Metrics
- [ ] Team tier launched
- [ ] 10+ team subscriptions
- [ ] Feature parity with Cipher workspace memory
- [ ] $1,500+ MRR
- [ ] 2,000+ GitHub stars

---

## Phase 5: Scale & Enterprise
**Timeline**: Weeks 21-28
**Goal**: Enterprise readiness, sustainable market position

### 5.1 Enterprise Features (Beat Cipher to Enterprise)

Cipher's Elastic License may deter some enterprises. Opportunity!

| Task | Priority | Status |
|------|----------|--------|
| SSO (SAML/OIDC) | 🔴 HIGH | ⬜ TODO |
| Self-hosted deployment option | 🔴 HIGH | ⬜ TODO |
| Audit logging | 🔴 HIGH | ⬜ TODO |
| SOC 2 Type I | 🟡 MEDIUM | ⬜ TODO |

### 5.2 Expand SDK Ecosystem

> **Note**: LlamaIndex and LangChain integrations moved to Phase 3 as **Critical** priority.

| Task | Priority | Status |
|------|----------|--------|
| AutoGen integration | 🟢 LOW | ⬜ TODO |
| OpenAI Agents SDK integration | 🟡 MEDIUM | ⬜ TODO |
| JavaScript/TypeScript SDK | 🟡 MEDIUM | ⬜ TODO |

### 5.3 Advanced Temporal Features

Build on Phase 2 bi-temporal foundation.

| Task | Priority | Status |
|------|----------|--------|
| Time-travel queries in UI | 🟡 MEDIUM | ⬜ TODO |
| Knowledge evolution visualization | 🟡 MEDIUM | ⬜ TODO |
| Automated fact decay/expiration | 🟢 LOW | ⬜ TODO |

### Phase 5 Success Metrics
- [ ] 3+ enterprise customers
- [ ] $5,000+ MRR
- [ ] 3,000+ GitHub stars (closing gap with Cipher)
- [ ] SDK used by 500+ developers
- [ ] 1+ enterprise case study

---

## Competitive Overtake Strategy

### GitHub Stars Gap Analysis

| Timeline | Cipher (projected) | Graphiti (projected) | memory-graph (target) |
|----------|-------------------|---------------------|----------------------|
| Now | 3,200 | 20,000 | ~100 |
| 3 months | 4,000 | 22,000 | 500 |
| 6 months | 5,000 | 25,000 | 1,500 |
| 12 months | 7,000 | 30,000 | 4,000 |
| 18 months | 9,000 | 35,000 | 8,000 |

**Strategy**: We won't beat Graphiti on stars (they're general-purpose with massive reach). We can beat Cipher by being better for coding-specific use cases. Key differentiators:

1. **License** - Apache 2.0 wins for enterprises (vs Cipher's Elastic)
2. **Ecosystem** - SDK + framework integrations (Cipher is MCP-only)
3. **Relationships** - 35+ typed relationships (our unique technical advantage)
4. **Python** - AI/ML ecosystem alignment
5. **Temporal** - Bi-temporal tracking (learning from Graphiti, but lightweight)
6. **Coding-specific** - Purpose-built vs general-purpose (vs Graphiti)

### Win Scenarios

**Scenario 1: Enterprise Wins**
- Cipher's Elastic License blocks enterprise adoption
- memory-graph's Apache 2.0 wins enterprise deals
- 3-5 enterprise customers = $10K+ MRR

**Scenario 2: SDK Ecosystem Wins**
- Cipher stays MCP-only
- memory-graph SDK captures LangChain/CrewAI users
- Framework integrations drive adoption

**Scenario 3: Relationship Quality Wins**
- Users realize vectors aren't enough
- Typed relationships prove more useful
- Word of mouth: "memory-graph actually understands my code"

**Scenario 4: Coding-Specific Focus Wins**
- Graphiti is general-purpose, we're coding-specific
- Developers prefer purpose-built tools
- "memory-graph is made for developers, by developers"

**Scenario 5: Community Wins**
- More responsive, engaged community
- Better documentation
- More tutorials and examples
- Users feel heard and supported

---

## Immediate Action Items

### This Week (Phase 0)
- [ ] Add Apache 2.0 badge to README
- [ ] Create COMPARISON.md with Cipher + Graphiti feature matrix
- [ ] Submit Smithery marketplace listing
- [ ] Draft "Why Apache 2.0" blog post
- [ ] Create relationship visualization diagram

### Next Week
- [ ] Publish comparison blog post
- [ ] Update all marketing materials with competitive messaging
- [ ] Begin Graphiti architecture study (read paper, review code)
- [ ] Set up competitive monitoring (track Cipher and Graphiti releases)

### This Month
- [ ] Complete Phase 0 competitive response
- [ ] Launch revised marketing campaign
- [ ] Complete Graphiti technical study document
- [ ] Begin Phase 2 bi-temporal schema design
- [ ] Publish SDK roadmap

---

## Risk Assessment Update

### Competitive Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Cipher gains more market share | High | High | Accelerate cloud launch, emphasize differentiation |
| Cipher adds typed relationships | Medium | High | Move fast, build ecosystem moat |
| Cipher switches to permissive license | Low | Medium | Focus on technical differentiation |
| Cipher raises funding | Medium | High | Bootstrap efficiently, focus on profitability |
| Graphiti adds coding-specific features | Low | Medium | Stay focused on dev workflow, move faster |

### Mitigation Priorities
1. **Speed**: Launch cloud ASAP
2. **Differentiation**: Typed relationships + SDK ecosystem + bi-temporal
3. **License**: Apache 2.0 messaging everywhere
4. **Community**: Build stronger, more engaged community
5. **Learn**: Study Graphiti's proven patterns, adopt what makes sense

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2025 | Gregory Dickson | Initial roadmap |
| 2.0 | Dec 2025 | Gregory Dickson | Value-focused refactor |
| 2.1 | Dec 2025 | Gregory Dickson | Semantic search strategy |
| 3.0 | Dec 2025 | Gregory Dickson | **COMPETITIVE RESPONSE**: Added Phase 0 for Byterover Cipher response |
| 3.1 | Dec 2025 | Gregory Dickson | **GRAPHITI ANALYSIS**: Added Zep/Graphiti as competitor, added bi-temporal tracking to Phase 2, renamed Phase 2 to "Search & Temporal Model", added Graphiti architecture study tasks |
| 3.2 | Dec 2025 | Gregory Dickson | **CIPHER v0.3.1 RESPONSE**: Updated Cipher profile (they abandoned vectors for Agentic Search!), replaced embedding strategy with Semantic Navigation approach, positioned cloud-native sync as advantage over Cipher's manual `brv pull`, added marketing angles around Cipher's validation of our approach |
| 3.3 | Dec 2025 | Gregory Dickson | **DEFERRED FEATURES**: Added VSCode Extension deferral decision (v1.2.0+), documented MCP + GitHub Copilot as current alternative |
| 3.4 | Dec 2025 | Gregory Dickson | **MEMORYGRAPH.DEV ALIGNMENT**: Updated Phase 3 to reflect actual implementation in memorygraph.dev repository. Infrastructure complete (GCP, Cloud SQL, FalkorDB, Auth API). Marketing site live. Added ADR references. Updated task statuses. Documented remaining workplans (4-7, 8-10). |
| 3.5 | Dec 2025 | Gregory Dickson | **PRODUCT PRIORITIES UPDATE**: Added Product Priorities table. Elevated LlamaIndex and LangChain integrations to Critical priority. Elevated VS Code Extension from Deferred to High priority. Updated SDK section in Phase 3 and Phase 5. Lowered AutoGen to Low priority. |
| 4.0 | Dec 2025 | Gregory Dickson | **DOCUMENT CONSOLIDATION**: Merged COMPLEMENTARY_PRODUCTS_BRAINSTORM.md into this document. Added Product Portfolio, Product Implementation Details (LlamaIndex, LangChain, Insights, VS Code, CLI with code examples), Revenue Model, Success Metrics, and Partnership Opportunities sections. Removed duplicate VS Code section. |

---

*This roadmap is a living document updated based on competitive dynamics, user feedback, and market conditions.*
