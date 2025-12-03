# Turso vs Current Backends: Quick Comparison

## Visual Architecture Comparison

### Current SQLite Backend

```
┌─────────────────────────────────────┐
│      User's Machine (Laptop)        │
│  ┌────────────────────────────┐    │
│  │  claude-code-memory        │    │
│  │  ┌──────────────────────┐  │    │
│  │  │ SQLiteFallbackBackend│  │    │
│  │  └──────────┬───────────┘  │    │
│  │             │               │    │
│  │             ▼               │    │
│  │  ┌──────────────────────┐  │    │
│  │  │  memory.db (local)   │  │    │
│  │  │  • Single file       │  │    │
│  │  │  • No sync           │  │    │
│  │  │  • Manual export     │  │    │
│  │  └──────────────────────┘  │    │
│  └────────────────────────────┘    │
└─────────────────────────────────────┘


Multi-device scenario:
Laptop ─╳─ Desktop  (No automatic sync)
         Manual export/import required
```

### Turso Backend (Local-Only Mode)

```
┌─────────────────────────────────────┐
│      User's Machine (Laptop)        │
│  ┌────────────────────────────┐    │
│  │  claude-code-memory        │    │
│  │  ┌──────────────────────┐  │    │
│  │  │   TursoBackend       │  │    │
│  │  └──────────┬───────────┘  │    │
│  │             │               │    │
│  │             ▼               │    │
│  │  ┌──────────────────────┐  │    │
│  │  │  memory.db (libsql)  │  │    │
│  │  │  • SQLite compatible │  │    │
│  │  │  • Modern async API  │  │    │
│  │  │  • No sync (local)   │  │    │
│  │  └──────────────────────┘  │    │
│  └────────────────────────────┘    │
└─────────────────────────────────────┘

Same as SQLite, but with libsql foundation
Drop-in replacement, ready for sync upgrade
```

### Turso Backend (Embedded Replica Mode) ⭐

```
┌─────────────────────────────────────┐
│      User's Laptop                   │
│  ┌────────────────────────────┐    │
│  │  claude-code-memory        │    │
│  │  ┌──────────────────────┐  │    │
│  │  │   TursoBackend       │  │    │
│  │  └──────────┬───────────┘  │    │
│  │             │               │    │
│  │     reads   ▼  writes       │    │
│  │  ┌──────────────────────┐  │    │
│  │  │ Embedded Replica     │◄─┼────┼─── sync() ───┐
│  │  │ memory.db (local)    │  │    │              │
│  │  │ • Fast local reads   │  │    │              │
│  │  │ • Offline capable    │  │    │              │
│  │  └──────────────────────┘  │    │              │
│  └────────────────────────────┘    │              │
└─────────────────────────────────────┘              │
                                                     │
                                                     ▼
┌──────────────────────────────────────────────────────────┐
│              Turso Cloud (Edge Network)                  │
│  ┌────────────────────────────────────────────────┐     │
│  │         Primary Database (libsql)              │     │
│  │         • Source of truth                       │     │
│  │         • Handles all writes                    │     │
│  │         • Syncs to all replicas                │     │
│  │         • Sub-40ms globally                     │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
                        │                   │
            ┌───────────┴───────┐  ┌────────┴────────┐
            │                   │  │                 │
            ▼                   ▼  ▼                 ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   Desktop Replica   │  │   Cloud VM Replica  │  │   Tablet Replica    │
│   memory.db         │  │   memory.db         │  │   memory.db         │
│   • Auto-syncs      │  │   • Auto-syncs      │  │   • Auto-syncs      │
│   • Same data       │  │   • Same data       │  │   • Same data       │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘

All devices share same memory graph automatically!
```

## Feature Matrix

| Feature | SQLite Backend | Turso (Local) | Turso (Replica) | Neo4j | Memgraph |
|---------|---------------|---------------|-----------------|-------|----------|
| **Setup Complexity** | ★☆☆☆☆ | ★☆☆☆☆ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| **Local Performance** | Fast | Fast | Fast | Medium | Fast |
| **Multi-device Sync** | ❌ Manual | ❌ Manual | ✅ Automatic | ❌ N/A | ❌ N/A |
| **Offline Support** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Cloud Backup** | ❌ Manual | ❌ Manual | ✅ Automatic | N/A | N/A |
| **External Service** | None | None | Turso Cloud | Neo4j Server | Memgraph Server |
| **Cost** | Free | Free | Free tier + paid | Self-host/Cloud | Self-host/Cloud |
| **Graph Features** | NetworkX | NetworkX | NetworkX | Native (Cypher) | Native (Cypher) |
| **Full-text Search** | FTS5 | FTS5 | FTS5 | Native | Limited |
| **Transactions** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Vector Search** | ❌ | 🔜 Native | 🔜 Native | Extensions | ❌ |
| **Scalability** | Single file | Single file | Distributed | Clustered | In-memory |
| **Data Privacy** | 100% local | 100% local | Local + Cloud | Server-based | Server-based |

## Use Case Recommendations

### Choose SQLite Backend When:
- Single machine usage
- Maximum privacy (100% local)
- No cloud dependencies
- Simple deployment
- Small to medium memory graphs

### Choose Turso Backend (Local-Only) When:
- Same as SQLite, but want:
  - Modern async API
  - Future upgrade path to sync
  - libSQL features (vector search coming)

### Choose Turso Backend (Embedded Replica) When:
- Multiple devices (laptop + desktop + cloud VM)
- Team memory sharing
- Cloud backup desired
- Offline-first workflow important
- Global distributed team
- Want best of both: local speed + cloud sync

### Choose Neo4j When:
- Complex graph queries (advanced Cypher)
- Large-scale graph analytics
- Need graph algorithms
- Centralized server acceptable
- Team has graph expertise

### Choose Memgraph When:
- Real-time graph analytics
- In-memory performance critical
- Streaming data integration
- Complex graph algorithms
- Self-hosted infrastructure

## Migration Paths

```
SQLite ──────────────┐
                     │
                     ├──> Turso (Local) ──> Turso (Replica)
                     │      (zero config)     (add sync)
                     │
                     └──> Neo4j / Memgraph
                          (different schema)
```

### Easy Migrations (Same Schema):
- SQLite → Turso Local: Copy file
- Turso Local → Turso Replica: Add env vars
- Turso Replica → Turso Local: Remove env vars
- Turso → SQLite: Reuse same file

### Complex Migrations (Different Schema):
- SQLite/Turso → Neo4j: Export/import tool needed
- Neo4j → SQLite/Turso: Export/import tool needed

## Cost Analysis

### SQLite Backend
- **Compute**: Free (local CPU)
- **Storage**: Free (local disk)
- **Network**: None
- **Total**: $0/month

### Turso Backend (Local-Only)
- **Compute**: Free (local CPU)
- **Storage**: Free (local disk)
- **Network**: None
- **Total**: $0/month

### Turso Backend (Embedded Replica)

**Free Tier** (generous):
- 9 GB total storage
- 1 billion row reads/month
- 25 million row writes/month
- 500+ edge locations
- 3 databases

**Typical Memory Graph Usage**:
- 1,000 memories × 5KB = 5MB storage
- 100 reads/day = 3K reads/month
- 10 writes/day = 300 writes/month

**Verdict**: Free tier covers most individual users indefinitely

**Paid Tiers** (if needed):
- Starter: $29/month (500 databases, analytics)
- Scaler: $199/month (higher limits)
- Enterprise: Custom pricing

### Neo4j (Self-hosted)
- **Compute**: Server costs (cloud VM ~$50-200/month)
- **Storage**: Volume storage
- **Network**: Bandwidth costs
- **Total**: $50-500/month

### Neo4j Aura (Cloud)
- Free Tier: Limited (5GB)
- Professional: $65+/month
- Enterprise: Custom

## Real-World Scenarios

### Scenario 1: Solo Developer, Single Machine
**Recommendation**: SQLite or Turso Local
- No sync needed
- Zero cost
- Maximum simplicity

### Scenario 2: Developer with Laptop + Desktop
**Recommendation**: Turso Embedded Replica
- Automatic sync between devices
- Fast local access on both
- No manual export/import
- Free tier sufficient

### Scenario 3: Remote Team (3-5 developers)
**Recommendation**: Turso Embedded Replica (Shared DB)
- Shared memory graph
- Each dev has fast local replica
- Team knowledge base builds automatically
- Free tier likely sufficient

### Scenario 4: Large Enterprise, Compliance Requirements
**Recommendation**: Neo4j (Self-hosted) or SQLite (Air-gapped)
- Full control over data
- No external services
- Advanced security
- Higher operational cost

### Scenario 5: Freelancer, Multiple Client Projects
**Recommendation**: Turso Local or SQLite (Separate DBs)
- One database per client
- Local-only for privacy
- No sync needed (separate contexts)

## Key Insights

### Turso's Sweet Spot:
1. **Individual developers with multiple machines** (laptop, desktop, cloud VM)
2. **Small teams** (2-10 people) sharing knowledge
3. **Offline-first workflows** (travel, unreliable internet)
4. **Zero-ops requirement** (no server management)
5. **Budget-conscious** (free tier is generous)

### When Turso Doesn't Make Sense:
1. **Single machine forever** → SQLite simpler
2. **Air-gapped environments** → SQLite required
3. **Enterprise compliance** → Self-hosted Neo4j
4. **Complex graph analytics** → Neo4j/Memgraph better

### Turso's Unique Value:
- **Only backend that offers**: Local speed + cloud sync + offline support
- **No alternatives offer**: Embedded replicas with auto-sync
- **Closest competitors**: Litestream (streaming) or custom sync (complex)

## Conclusion

Turso Backend fills a gap in the current backend lineup:

```
                     Low Ops ←──────────────→ High Ops
                     ↓                              ↓
Local-only:      SQLite ─────────── Turso Local ───────┐
                    │                    │              │
                    │                    │              │
Distributed:        └──── Turso Replica ─┘              │
                                                        │
                                                        │
Centralized:                                Neo4j / Memgraph
```

**Recommendation**: Implement Turso backend for users who need multi-device sync without operational complexity.
