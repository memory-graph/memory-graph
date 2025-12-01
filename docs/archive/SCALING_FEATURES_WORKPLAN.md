# MemoryGraph Scaling Features - Implementation Workplan

> **STATUS**: Reference Document - Not Started
> **CONSOLIDATED**: Summary moved to `/docs/WORKPLAN.md` Phase 3.3
> **IMPLEMENTATION**: Deferred until user demand (10k+ memories or feature requests)

This document contains detailed implementation plans for future scaling features. It remains as a reference for when these features are needed.

**Active Workplan**: See `/docs/WORKPLAN.md` for current priorities.

---

## Pre-Implementation Analysis

### Architecture Considerations

Before implementing, note these critical points:

1. **Embedding Dependency**: Semantic clustering requires an embedding service (OpenAI, local models, etc.). This adds external dependencies and API costs. Consider making this optional/pluggable.

2. **Backend Complexity**: You have 3 backends (SQLite, Neo4j, Memgraph). Each feature must work across all, which significantly increases implementation complexity. Consider:
   - Implementing for SQLite first (your default)
   - Making advanced features (semantic clustering) optional for lighter backends
   - Using feature flags to enable/disable based on backend capabilities

3. **Breaking Changes Risk**: Adding fields like `last_accessed`, `usage_count`, `importance_decay` requires schema migrations. Existing databases will need migration scripts.

4. **Consolidation Complexity**: Merging memories while preserving relationships is non-trivial. What happens when Memory A (with 10 relationships) and Memory B (with 8 relationships) consolidate? Do you:
   - Merge all relationships to the consolidated memory?
   - Keep originals and add a "CONSOLIDATED_FROM" relationship?
   - Delete originals entirely?

5. **Performance Trade-offs**: Background tasks, caching, and async operations add complexity. The current codebase is already async, but adding background workers may require a task queue (Celery, Dramatiq, etc.).

**Recommendation**: Implement features in dependency order. Start with foundational tracking (access patterns), then decay/pruning (uses tracking), then consolidation (uses both), and finally semantic clustering (most complex).

---

## Feature 1: Access Pattern Tracking (Foundation)

This feature is prerequisite for decay-based pruning and enables analytics.

### 1.1 Database Schema Updates

- [ ] Add tracking fields to Memory model in `/src/memorygraph/models.py`:
  - `last_accessed: datetime` - timestamp of last retrieval
  - `access_count: int` - total number of accesses
  - `created_at: datetime` - when memory was created (if not exists)
  - `is_pinned: bool` - flag to prevent decay (default: False)

- [ ] Create SQLite migration script in `/migrations/001_add_access_tracking.sql`:
  - ALTER TABLE to add new columns with defaults
  - Backfill `created_at` with current timestamp for existing records
  - Backfill `last_accessed` = `created_at` for existing records
  - Set `access_count` = 0, `is_pinned` = False for existing records

- [ ] Update SQLite backend (`/src/memorygraph/backends/sqlite_fallback.py`):
  - Modify `_ensure_tables()` to include new columns in CREATE TABLE
  - Add migration check/execution on initialization

- [ ] Update Neo4j backend (`/src/memorygraph/backends/neo4j_backend.py`):
  - Add Cypher migration to add properties to existing Memory nodes
  - Update node creation queries to include new properties

### 1.2 Tracking Implementation

- [ ] Update `get_memory()` in all backends to:
  - Increment `access_count`
  - Update `last_accessed` to current timestamp
  - Use async UPDATE query (don't block retrieval)

- [ ] Update `search_memories()` in all backends to:
  - Track access for each returned memory
  - Batch update access stats for efficiency

- [ ] Add `pin_memory(memory_id: str)` tool to `/src/memorygraph/server.py`:
  - Set `is_pinned = True` for specified memory
  - Document that pinned memories won't decay

- [ ] Add `unpin_memory(memory_id: str)` tool (standard/full feature sets)

### 1.3 Testing

- [ ] Create `/tests/test_access_tracking.py`:
  - Test access_count increments on retrieval
  - Test last_accessed updates
  - Test pinning prevents later operations (verify in decay tests)
  - Test migration with existing data
  - Test across all backends (parametrize)

---

## Feature 2: Decay-Based Pruning

Depends on: Feature 1 (Access Pattern Tracking)

### 2.1 Decay Configuration

- [ ] Create `/src/memorygraph/config/decay_config.py`:
  - `DecayConfig` dataclass with fields:
    - `enabled: bool` (default: True)
    - `decay_rate_per_day: float` (default: 0.01, i.e., 1% per day)
    - `min_importance_threshold: float` (default: 0.1, archive below this)
    - `decay_interval_hours: int` (default: 24, how often to run decay)
    - `memory_type_multipliers: dict[str, float]` (e.g., {"error": 0.5, "solution": 0.8})
    - `archive_instead_of_delete: bool` (default: True)
  - Load from environment variables or config file

- [ ] Add decay config to server initialization in `/src/memorygraph/server.py`

### 2.2 Decay Calculation Logic

- [ ] Create `/src/memorygraph/decay/decay_engine.py`:
  - `calculate_decayed_importance(memory: Memory, config: DecayConfig) -> float`:
    - Get days since `last_accessed`
    - Apply exponential decay: `importance * (1 - decay_rate) ^ days_since_access`
    - Apply memory type multiplier
    - Return 0 if `is_pinned = True` (no decay)
  - `should_archive(decayed_importance: float, config: DecayConfig) -> bool`:
    - Return True if below threshold

### 2.3 Archive System

- [ ] Add `archived_at: datetime | None` field to Memory model in `/src/memorygraph/models.py`

- [ ] Create SQLite migration `/migrations/002_add_archived_at.sql`

- [ ] Update all search/retrieval operations to:
  - Filter out archived memories by default (`WHERE archived_at IS NULL`)
  - Add `include_archived: bool` parameter to search functions

- [ ] Add `archive_memory(memory_id: str)` tool to server (standard feature set)

- [ ] Add `unarchive_memory(memory_id: str)` tool to server (standard feature set)

### 2.4 Background Decay Process

- [ ] Create `/src/memorygraph/decay/decay_scheduler.py`:
  - `DecayScheduler` class with:
    - `start()` method to begin background task
    - `stop()` method to gracefully shutdown
    - Use `asyncio.create_task()` for background loop
    - Run decay process every `decay_interval_hours`

- [ ] Implement `run_decay_process(database, config)` in decay_scheduler.py:
  - Fetch all non-pinned, non-archived memories
  - For each, calculate decayed importance
  - Update importance in database (batch UPDATE)
  - Archive memories below threshold
  - Log statistics (memories processed, archived count)

- [ ] Integrate DecayScheduler into server lifecycle:
  - Start scheduler in server initialization
  - Stop scheduler on shutdown
  - Make optional via config flag

### 2.5 Manual Decay Operations

- [ ] Add `run_decay_now()` tool to server (full feature set):
  - Manually trigger decay process
  - Return statistics about decay run

- [ ] Add `get_decay_statistics()` tool (full feature set):
  - Return counts of archived, low-importance, pinned memories
  - Return next scheduled decay time

### 2.6 Testing

- [ ] Create `/tests/test_decay.py`:
  - Test decay calculation with different time deltas
  - Test pinned memories don't decay
  - Test memory type multipliers
  - Test archiving below threshold
  - Test archive filtering in searches
  - Test background scheduler (use mock time)
  - Test manual decay trigger
  - Test across all backends

---

## Feature 3: Memory Consolidation

Depends on: Feature 1 (Access Pattern Tracking), Feature 2 (Decay-Based Pruning)

### 3.1 Consolidation Strategy Design

- [ ] Create `/src/memorygraph/consolidation/strategy.py`:
  - `ConsolidationStrategy` enum:
    - `MERGE_AND_DELETE` - Create consolidated memory, delete originals
    - `MERGE_AND_ARCHIVE` - Create consolidated memory, archive originals
    - `MERGE_AND_LINK` - Create consolidated memory, keep originals with CONSOLIDATED_INTO relationship
  - `ConsolidationConfig` dataclass:
    - `strategy: ConsolidationStrategy`
    - `similarity_threshold: float` (for automatic consolidation)
    - `max_memories_per_consolidation: int` (default: 5)
    - `preserve_relationships: bool` (default: True)

### 3.2 Consolidation Identification

- [ ] Create `/src/memorygraph/consolidation/identifier.py`:
  - `identify_consolidation_candidates(database, config) -> list[list[str]]`:
    - Find memories with similar titles/tags (keyword-based)
    - Find memories with many SIMILAR_TO relationships
    - Find memories in same time window with same type
    - Return groups of memory IDs that could be consolidated
  - Use graph analysis (NetworkX for SQLite, Cypher for Neo4j)

### 3.3 Consolidation Execution

- [ ] Create `/src/memorygraph/consolidation/consolidator.py`:
  - `consolidate_memories(memory_ids: list[str], database, config) -> str`:
    - Fetch all memories to consolidate
    - Generate consolidated content (concatenate or summarize)
    - Create new consolidated memory with:
      - `title`: "Consolidated: {common theme}"
      - `content`: merged content
      - `type`: most common type among originals
      - `tags`: union of all tags
      - `importance`: max importance among originals
      - `summary`: "Consolidation of {count} memories"
    - Handle relationships based on strategy:
      - If MERGE_AND_DELETE/ARCHIVE: redirect all relationships to consolidated memory
      - If MERGE_AND_LINK: add CONSOLIDATED_INTO relationships from originals to new
    - Archive or delete originals based on strategy
    - Return consolidated memory ID

### 3.4 Relationship Preservation

- [ ] Update consolidator.py to handle relationship migration:
  - `migrate_relationships(original_ids: list[str], consolidated_id: str, database)`:
    - For each original memory, get all relationships (incoming and outgoing)
    - Create equivalent relationships on consolidated memory
    - Deduplicate relationships (multiple originals may have same relationships)
    - Preserve relationship metadata (confidence, strength, context)

### 3.5 Tools for Consolidation

- [ ] Add `consolidate_memories(memory_ids: list[str], strategy: str)` tool (full feature set):
  - Manual consolidation of specified memories
  - Validate memory_ids exist
  - Execute consolidation
  - Return new consolidated memory ID

- [ ] Add `find_consolidation_candidates()` tool (full feature set):
  - Return suggested groups for consolidation
  - Include reasoning (e.g., "5 memories about 'authentication errors'")

- [ ] Add `auto_consolidate(min_group_size: int)` tool (full feature set):
  - Automatically consolidate identified candidate groups
  - Require min_group_size to avoid over-consolidation
  - Return statistics

### 3.6 Testing

- [ ] Create `/tests/test_consolidation.py`:
  - Test candidate identification
  - Test consolidation with MERGE_AND_DELETE strategy
  - Test consolidation with MERGE_AND_ARCHIVE strategy
  - Test consolidation with MERGE_AND_LINK strategy
  - Test relationship preservation and migration
  - Test deduplication of relationships
  - Test consolidated memory properties
  - Test across all backends

---

## Feature 4: Semantic Clustering

Depends on: Feature 1 (foundational), optional dependency on external embedding service

### 4.1 Embedding Infrastructure

- [ ] Create `/src/memorygraph/embeddings/embedding_provider.py`:
  - `EmbeddingProvider` abstract base class:
    - `async def embed(text: str) -> list[float]`
    - `async def embed_batch(texts: list[str]) -> list[list[float]]`
    - `dimension: int` property
  - `OpenAIEmbeddingProvider` implementation (uses OpenAI API)
  - `LocalEmbeddingProvider` implementation (uses sentence-transformers)
  - `NoOpEmbeddingProvider` (returns None, for when feature is disabled)

- [ ] Add embedding dependencies to `/pyproject.toml`:
  - Make optional: `[tool.poetry.extras]` -> `embeddings = ["openai", "sentence-transformers"]`
  - Document that semantic clustering requires extras

- [ ] Add `embedding_vector: list[float] | None` to Memory model

- [ ] Create migration `/migrations/003_add_embedding_vector.sql` (SQLite):
  - Add TEXT column for JSON-serialized embedding
  - For Neo4j: add embedding property (array type)

### 4.2 Embedding Generation

- [ ] Create `/src/memorygraph/embeddings/embedding_manager.py`:
  - `EmbeddingManager` class:
    - `async def generate_embedding(memory: Memory) -> list[float]`:
      - Concatenate title + summary + content
      - Call provider.embed()
      - Cache result
    - `async def generate_embeddings_batch(memories: list[Memory])`:
      - Batch processing for efficiency
    - `async def update_missing_embeddings(database)`:
      - Find memories without embeddings
      - Generate and store embeddings

- [ ] Update `store_memory()` in all backends to:
  - Generate embedding when creating memory (if provider configured)
  - Store embedding in database

### 4.3 Clustering Algorithm

- [ ] Create `/src/memorygraph/clustering/clusterer.py`:
  - `SemanticClusterer` class:
    - `cluster_memories(memories: list[Memory], n_clusters: int) -> dict[int, list[Memory]]`:
      - Use K-means clustering on embedding vectors
      - Fallback to graph-based clustering if embeddings unavailable
    - `find_cluster_representatives(cluster: list[Memory]) -> list[Memory]`:
      - Return most central memories (highest avg similarity to cluster members)
      - Or highest importance memories
      - Configurable strategy

- [ ] Implement graph-based fallback clustering:
  - `graph_based_cluster(database, n_clusters: int)`:
    - Use community detection algorithms (Louvain, Label Propagation)
    - Available in NetworkX for SQLite backend
    - Use Cypher procedures for Neo4j

### 4.4 Cluster-Aware Retrieval

- [ ] Create `/src/memorygraph/intelligence/cluster_retrieval.py`:
  - `ClusterAwareRetrieval` class:
    - `search_with_clustering(query: str, max_results: int) -> list[Memory]`:
      - Cluster all memories
      - Find most relevant cluster to query (using embedding similarity)
      - Return representatives from top N clusters
      - Expand to more memories if needed

- [ ] Update `search_memories()` to support clustering mode:
  - Add `use_clustering: bool` parameter
  - Add `cluster_mode: str` parameter ("representatives" | "full_clusters")

### 4.5 Tools for Clustering

- [ ] Add `cluster_memories(n_clusters: int)` tool (full feature set):
  - Return cluster assignments
  - Return cluster summaries (common themes)

- [ ] Add `get_cluster_representatives(cluster_id: int)` tool (full feature set)

- [ ] Add `search_with_clustering(query: str, max_clusters: int)` tool (full feature set):
  - Cluster-aware search
  - Return representative memories from relevant clusters

- [ ] Add `generate_missing_embeddings()` tool (full feature set):
  - Backfill embeddings for existing memories
  - Return progress statistics

### 4.6 Testing

- [ ] Create `/tests/test_embeddings.py`:
  - Test embedding generation (with mock provider)
  - Test batch embedding
  - Test missing embeddings detection and backfill
  - Test OpenAI provider (integration test, conditional on API key)
  - Test local provider (if sentence-transformers installed)

- [ ] Create `/tests/test_clustering.py`:
  - Test K-means clustering with synthetic embeddings
  - Test graph-based clustering fallback
  - Test cluster representative selection
  - Test cluster-aware search
  - Test across backends

---

## Feature 5: Progressive Loading

Depends on: None (foundational performance feature)

### 5.1 Lazy Loading Architecture

- [ ] Create `/src/memorygraph/models.py` changes:
  - Add `MemorySummary` model (lightweight):
    - `id: str`
    - `title: str`
    - `type: str`
    - `importance: float`
    - `created_at: datetime`
    - `summary: str | None`
  - Add `MemoryDetail` model (extends MemorySummary):
    - Adds `content: str`, `tags`, `context`, `relationships`

### 5.2 Pagination Support

- [ ] Create `/src/memorygraph/pagination/paginator.py`:
  - `PaginationParams` dataclass:
    - `page: int` (default: 1)
    - `page_size: int` (default: 20)
    - `cursor: str | None` (for cursor-based pagination)
  - `PaginatedResult[T]` generic class:
    - `items: list[T]`
    - `total_count: int`
    - `page: int`
    - `page_size: int`
    - `has_next_page: bool`
    - `next_cursor: str | None`

- [ ] Update all backends to support pagination:
  - Add `LIMIT` and `OFFSET` to SQLite queries
  - Use `SKIP` and `LIMIT` in Neo4j Cypher
  - Add cursor-based pagination using `last_id` for SQLite

### 5.3 Progressive Search Implementation

- [ ] Create `/src/memorygraph/intelligence/progressive_search.py`:
  - `ProgressiveSearch` class:
    - `async def search_minimal(query: str) -> list[MemorySummary]`:
      - Return only summaries, no full content
      - Fast initial results
    - `async def expand_memory(memory_id: str) -> MemoryDetail`:
      - Load full memory with relationships on demand
    - `async def search_with_expansion(query: str, initial_count: int) -> AsyncIterator[Memory]`:
      - Yield summaries immediately
      - Optionally expand top results

### 5.4 Streaming Results

- [ ] Update search methods to support async generators:
  - `async def search_memories_stream(query, filters) -> AsyncIterator[Memory]`:
    - Yield memories as they're retrieved from database
    - Useful for large result sets
  - Implement in all backends (SQLite, Neo4j)

### 5.5 Tools for Progressive Loading

- [ ] Update `search_memories()` tool in server:
  - Add `return_summaries_only: bool` parameter
  - Add `page: int` and `page_size: int` parameters
  - Return paginated results with metadata

- [ ] Add `expand_memory_details(memory_id: str)` tool (standard feature set):
  - Load full memory details on demand

- [ ] Add `search_memories_paginated(query, page, page_size)` tool (standard feature set):
  - Explicit pagination support

### 5.6 Response Size Management

- [ ] Create `/src/memorygraph/response/size_manager.py`:
  - `estimate_token_count(memory: Memory) -> int`:
    - Rough estimation (chars / 4)
  - `truncate_to_token_budget(memories: list[Memory], max_tokens: int) -> list[Memory]`:
    - Prioritize by relevance and importance
    - Truncate content if needed
    - Return subset that fits budget

- [ ] Integrate into search functions:
  - Add `max_tokens: int` parameter to searches
  - Apply token budget before returning results

### 5.7 Testing

- [ ] Create `/tests/test_progressive_loading.py`:
  - Test summary-only retrieval
  - Test detail expansion
  - Test pagination (page-based and cursor-based)
  - Test streaming search
  - Test token budget enforcement
  - Test across backends

---

## Feature 6: Performance Enhancements

Depends on: All previous features (applies optimizations across the board)

### 6.1 Database Indexing

- [ ] Create `/migrations/004_add_performance_indexes.sql` (SQLite):
  - Index on `memories(type, importance, archived_at)` for filtered searches
  - Index on `memories(last_accessed)` for decay queries
  - Index on `memories(created_at)` for time-based queries
  - Index on `relationships(from_memory_id, relationship_type)`
  - Index on `relationships(to_memory_id)`

- [ ] Add Neo4j indexes in backend initialization:
  - Create index on `:Memory(type)`
  - Create index on `:Memory(importance)`
  - Create index on `:Memory(last_accessed)`
  - Create constraint on `:Memory(id)` (if not exists)

### 6.2 Query Optimization

- [ ] Optimize SQLite queries in `/src/memorygraph/backends/sqlite_fallback.py`:
  - Use parameterized queries everywhere (prevent injection, enable caching)
  - Combine multiple SELECTs into single query with JOINs where possible
  - Use `EXPLAIN QUERY PLAN` to verify index usage
  - Add query result caching for expensive relationship queries

- [ ] Optimize Neo4j queries in `/src/memorygraph/backends/neo4j_backend.py`:
  - Use `PROFILE` to analyze query performance
  - Add query hints (`USING INDEX`, `USING SCAN`)
  - Batch Cypher queries where possible (use `UNWIND` for lists)

### 6.3 Caching Layer

- [ ] Create `/src/memorygraph/cache/cache_manager.py`:
  - `CacheManager` class using `functools.lru_cache` or Redis:
    - `async def get_memory(memory_id: str) -> Memory | None`
    - `async def set_memory(memory: Memory)`
    - `async def invalidate(memory_id: str)`
    - `async def clear_all()`
  - TTL-based expiration (default: 5 minutes)
  - Size-based LRU eviction (default: 1000 memories)

- [ ] Integrate caching into backends:
  - Wrap `get_memory()` with cache lookup
  - Invalidate cache on `update_memory()` and `delete_memory()`
  - Optional cache for search results (keyed by query hash)

- [ ] Add cache configuration to server:
  - `cache_enabled: bool`
  - `cache_ttl_seconds: int`
  - `cache_max_size: int`
  - `cache_backend: str` ("memory" | "redis")

### 6.4 Batch Operations

- [ ] Add batch tools to server (full feature set):
  - `store_memories_batch(memories: list[dict])`:
    - Single transaction for multiple insertions
    - Return list of created IDs
  - `update_memories_batch(updates: list[dict])`:
    - Batch UPDATE in single query
  - `delete_memories_batch(memory_ids: list[str])`:
    - Batch DELETE with IN clause

- [ ] Optimize backend implementations:
  - Use `executemany()` for SQLite batch operations
  - Use `UNWIND` with Cypher for Neo4j batch operations
  - Wrap in transactions for atomicity

### 6.5 Background Task Queue

- [ ] Create `/src/memorygraph/tasks/task_queue.py`:
  - Simple in-memory queue using `asyncio.Queue`
  - `TaskQueue` class:
    - `async def enqueue(task_fn, *args, **kwargs)`
    - `async def start_worker()`
    - `async def stop_worker()`
  - Use for non-blocking operations (embedding generation, decay)

- [ ] Refactor decay scheduler to use task queue:
  - Enqueue decay calculations instead of blocking
  - Process in background worker

- [ ] Refactor embedding generation to use task queue:
  - Enqueue embedding generation after memory creation
  - Process asynchronously

### 6.6 Connection Pooling

- [ ] Update SQLite backend to use connection pool:
  - Use `aiosqlite` connection pool (if not already)
  - Configure max connections (default: 5)

- [ ] Update Neo4j backend to use connection pool:
  - Verify `neo4j.AsyncGraphDatabase.driver()` uses pooling
  - Configure pool size in config

### 6.7 Monitoring and Profiling

- [ ] Create `/src/memorygraph/monitoring/performance_monitor.py`:
  - `PerformanceMonitor` class:
    - Track query execution times
    - Track cache hit/miss rates
    - Track memory usage
    - `get_statistics() -> dict` tool

- [ ] Add performance logging:
  - Log slow queries (>100ms threshold)
  - Log cache statistics periodically
  - Log decay/consolidation run statistics

- [ ] Add `get_performance_stats()` tool (full feature set):
  - Return monitoring statistics
  - Include database size, memory count, relationship count

### 6.8 Testing

- [ ] Create `/tests/test_performance.py`:
  - Benchmark search with 1000, 5000, 10000 memories
  - Test index usage (verify EXPLAIN output)
  - Test cache hit rates
  - Test batch operation performance vs individual
  - Stress test concurrent operations
  - Test across backends

- [ ] Create `/tests/test_caching.py`:
  - Test cache hit/miss
  - Test cache invalidation
  - Test TTL expiration
  - Test LRU eviction

---

## Integration and Testing

### 7.1 Cross-Feature Integration

- [ ] Ensure decay works with consolidation:
  - Consolidated memories should reset `last_accessed`
  - Consolidated memories should inherit max importance

- [ ] Ensure clustering works with archived memories:
  - Exclude archived from clustering by default
  - Add option to include archived

- [ ] Ensure progressive loading works with decay:
  - Summaries should include importance and last_accessed
  - Allow sorting by recency or importance

### 7.2 End-to-End Testing

- [ ] Create `/tests/test_e2e_scaling.py`:
  - Simulate realistic usage scenario:
    - Create 5000 memories over simulated time
    - Perform searches (should use clustering and progressive loading)
    - Run decay (should archive old memories)
    - Run consolidation (should merge similar memories)
  - Verify final database state
  - Verify performance meets targets (searches < 500ms)

### 7.3 Backward Compatibility

- [ ] Test with existing databases (before migrations):
  - Verify migrations run successfully
  - Verify old data is preserved
  - Verify new features work with backfilled data

- [ ] Test graceful degradation:
  - If embeddings unavailable, clustering falls back to graph-based
  - If cache unavailable, queries go directly to database
  - If task queue full, operations run synchronously

### 7.4 Documentation Updates

- [ ] Update `/README.md`:
  - Document new features
  - Document configuration options
  - Document performance characteristics
  - Add scaling best practices section

- [ ] Create `/docs/SCALING.md`:
  - Explain decay, consolidation, clustering, progressive loading
  - Provide configuration examples
  - Explain when to use each feature
  - Performance tuning guide

- [ ] Update API documentation:
  - Document new tools
  - Document new parameters on existing tools
  - Provide usage examples

---

## Deployment and Migration

### 8.1 Migration Scripts

- [ ] Create `/scripts/migrate_database.py`:
  - Detect current schema version
  - Run necessary migrations in order
  - Backup database before migration
  - Verify migration success

- [ ] Test migrations on copies of production databases (if applicable)

### 8.2 Configuration Management

- [ ] Create `/config/default_config.yaml`:
  - All default configuration values
  - Comments explaining each option

- [ ] Update server to load config from file or environment:
  - Priority: CLI args > env vars > config file > defaults

### 8.3 Feature Flags

- [ ] Create `/src/memorygraph/feature_flags.py`:
  - `FeatureFlags` dataclass:
    - `decay_enabled: bool`
    - `consolidation_enabled: bool`
    - `clustering_enabled: bool`
    - `caching_enabled: bool`
  - Load from config

- [ ] Wrap new features in feature flag checks:
  - Only register tools if feature enabled
  - Skip background tasks if feature disabled

---

## Dependencies Between Features

1. **Access Pattern Tracking** - No dependencies (implement first)
2. **Decay-Based Pruning** - Requires Access Pattern Tracking
3. **Progressive Loading** - No dependencies (can implement in parallel with #1)
4. **Performance Enhancements** - No dependencies (can start early, optimize as you go)
5. **Memory Consolidation** - Requires Access Pattern Tracking, benefits from Decay
6. **Semantic Clustering** - No hard dependencies, but benefits from all other features

**Recommended Implementation Order:**
1. Access Pattern Tracking (Feature 1)
2. Progressive Loading (Feature 5) + Performance Enhancements (Feature 6) in parallel
3. Decay-Based Pruning (Feature 2)
4. Memory Consolidation (Feature 3)
5. Semantic Clustering (Feature 4)

---

## Notes for Coding Agent

- Each checkbox is an atomic, testable unit of work
- Run tests after completing each subsection (e.g., after 1.1, run tests before moving to 1.2)
- Commit after each major subsection (e.g., after 1.3, commit "feat: implement access pattern tracking")
- Check backward compatibility at each database schema change
- Verify all three backends (SQLite, Neo4j, Memgraph) remain functional after each feature
- Use feature flags to enable incremental rollout
- Profile performance after each feature to catch regressions early
