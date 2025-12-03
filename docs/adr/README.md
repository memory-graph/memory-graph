# Architecture Documentation

This directory contains architectural decisions and technical specifications for the claude-code-memory project.

## Contents

### Architecture Decision Records (ADRs)

- **[ADR-001: Turso DB Backend Evaluation](ADR-001-turso-backend-evaluation.md)**
  - Comprehensive analysis of Turso DB as a backend option
  - Evaluation of integration approaches
  - Trade-offs and recommendations
  - Status: Proposed

### Technical Specifications

- **[Turso Backend Implementation Spec](turso-backend-implementation-spec.md)**
  - Detailed implementation plan for Turso backend
  - Class definitions and API design
  - Configuration, testing, and deployment strategy
  - Success criteria and migration paths

### Comparisons and Analysis

- **[Turso vs Current Backends](turso-comparison.md)**
  - Visual architecture comparisons
  - Feature matrix across all backends
  - Use case recommendations
  - Cost analysis and real-world scenarios

## Quick Reference

### Current Backend Architecture

The project uses a unified `GraphBackend` interface with multiple implementations:

```python
class GraphBackend(ABC):
    async def connect() -> bool
    async def disconnect() -> None
    async def execute_query(query, parameters, write) -> list
    async def initialize_schema() -> None
    async def health_check() -> dict
    def backend_name() -> str
    def supports_fulltext_search() -> bool
    def supports_transactions() -> bool
```

### Supported Backends

| Backend | Type | Use Case |
|---------|------|----------|
| **SQLite** (default) | Embedded | Local-only, zero config |
| **Neo4j** | Graph DB | Advanced graph queries |
| **Memgraph** | In-memory Graph | Real-time analytics |
| **FalkorDB** | Redis-based Graph | Redis integration |
| **FalkorDBLite** | Embedded Graph | Lightweight graph |
| **Turso** (proposed) | Distributed SQLite | Multi-device sync |

### Backend Selection

Via `MEMORY_BACKEND` environment variable:
- `sqlite` (default): Zero-dependency fallback
- `neo4j`: Native graph database
- `memgraph`: In-memory graph database
- `falkordb`: Redis-based graph
- `falkordblite`: Embedded graph database
- `turso` (proposed): Distributed SQLite with sync
- `auto`: Automatic selection

## Turso Backend Summary

### What is Turso?

Turso is a distributed database built on **libSQL** (SQLite fork) with:
- 100% SQLite compatibility
- Embedded replicas (local + cloud sync)
- Edge deployment (100+ locations)
- Sub-40ms latency globally
- Vector search (coming)

### Why Consider Turso?

**Unique Value**: Only backend offering local speed + cloud sync + offline support

**Key Use Cases**:
1. Multi-device development (laptop + desktop + cloud VM)
2. Team memory sharing (2-10 developers)
3. Offline-first workflows
4. Zero-ops cloud backup
5. Global distributed teams

### Integration Approach (Recommended)

**Option B: Separate TursoBackend**
- Clean separation from SQLite backend
- Turso-specific features clearly exposed
- No impact on existing backends
- Easier to maintain and test

### Implementation Phases

1. **Phase 1: Core Backend (MVP)**
   - Local-only mode (drop-in SQLite replacement)
   - Basic CRUD operations
   - Schema initialization

2. **Phase 2: Embedded Replica**
   - Sync URL and auth token configuration
   - Auto-sync on connect/disconnect
   - Manual sync() method

3. **Phase 3: Advanced Features**
   - Background periodic sync
   - Migration tools
   - Vector search integration

### Configuration Example

**Local-only** (like SQLite):
```bash
MEMORY_BACKEND=turso
MEMORY_TURSO_PATH=~/.memorygraph/memory.db
```

**Embedded replica** (multi-device sync):
```bash
MEMORY_BACKEND=turso
MEMORY_TURSO_PATH=~/.memorygraph/memory.db
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your-token
```

### Trade-offs

**Pros**:
- Multi-device sync without operational complexity
- Cloud backup included
- Offline-first (local replica)
- Free tier generous
- SQLite-compatible (easy migration)

**Cons**:
- New dependency (libsql package)
- Requires Turso account for sync features
- External service dependency (mitigated by local-only mode)
- Additional configuration complexity

## Decision Status

- **ADR-001**: Proposed (awaiting decision)
- **Recommendation**: Implement Turso backend as Option B
- **Next Steps**: User/stakeholder feedback → Implementation → Testing

## Contributing to Architecture

### Process for New ADRs

1. **Identify Significant Decision**: Multi-backend impact or major feature
2. **Research**: Gather data, alternatives, constraints
3. **Document**: Use ADR template (Context → Decision → Consequences)
4. **Review**: Stakeholder feedback
5. **Decide**: Update status (Proposed → Accepted/Rejected)
6. **Implement**: Follow technical specification
7. **Maintain**: Update ADR if context changes

### ADR Template

```markdown
# ADR-XXX: [Title]

## Status: Proposed | Accepted | Deprecated | Superseded

## Context
What problem are we solving? What constraints exist?

## Decision
What are we doing?

## Alternatives Considered
What else did we evaluate? Why were they rejected?

## Consequences
Trade-offs, risks, follow-up work

## References
Links, documentation, related ADRs
```

## References

### External Documentation
- [Turso Documentation](https://docs.turso.tech/)
- [Turso Python SDK](https://docs.turso.tech/sdk/python/quickstart)
- [libSQL GitHub](https://github.com/tursodatabase/libsql)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Memgraph Documentation](https://memgraph.com/docs)

### Internal Documentation
- [Project README](/README.md)
- [Backend Factory](/src/memorygraph/backends/factory.py)
- [GraphBackend Interface](/src/memorygraph/backends/base.py)
- [Configuration](/src/memorygraph/config.py)

## Contact

For questions about architecture decisions, open an issue or discussion on GitHub.
