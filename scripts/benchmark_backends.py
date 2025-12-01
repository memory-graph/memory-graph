#!/usr/bin/env python3
"""
Simple benchmark script for MemoryGraph backends.

This script validates basic performance characteristics using the SQLite backend
(which is always available). For FalkorDB benchmarking, users should run this
against their own deployment.

Usage:
    python3 scripts/benchmark_backends.py
"""

import asyncio
import time
import statistics
from datetime import datetime
from typing import List, Tuple

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.models import Memory, MemoryType, RelationshipType, SearchQuery


async def benchmark_insert_throughput(backend, num_memories: int = 100) -> float:
    """
    Measure insert throughput (memories/second).

    Args:
        backend: Backend instance to test
        num_memories: Number of memories to insert

    Returns:
        Memories per second
    """
    print(f"\n{'='*60}")
    print(f"Benchmark: Insert Throughput ({num_memories} memories)")
    print(f"{'='*60}")

    start_time = time.perf_counter()

    for i in range(num_memories):
        memory = Memory(
            type=MemoryType.SOLUTION,
            title=f"Test Memory {i}",
            content=f"This is test memory content for benchmark {i}",
            tags=["benchmark", "test"],
            importance=0.5,
            confidence=0.8
        )
        await backend.store_memory(memory)

    end_time = time.perf_counter()
    elapsed = end_time - start_time
    throughput = num_memories / elapsed

    print(f"✓ Inserted {num_memories} memories in {elapsed:.2f}s")
    print(f"✓ Throughput: {throughput:.2f} memories/second")

    return throughput


async def benchmark_query_latency(backend, num_queries: int = 50) -> Tuple[float, float, float]:
    """
    Measure query latency for simple searches.

    Args:
        backend: Backend instance to test
        num_queries: Number of queries to run

    Returns:
        Tuple of (p50, p95, p99) latencies in milliseconds
    """
    print(f"\n{'='*60}")
    print(f"Benchmark: Query Latency ({num_queries} queries)")
    print(f"{'='*60}")

    latencies = []

    for i in range(num_queries):
        query = SearchQuery(
            query="test",
            limit=10
        )

        start_time = time.perf_counter()
        results = await backend.search_memories(query)
        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)

    # Calculate percentiles
    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
    p99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile

    print(f"✓ Executed {num_queries} queries")
    print(f"✓ p50 latency: {p50:.2f}ms")
    print(f"✓ p95 latency: {p95:.2f}ms")
    print(f"✓ p99 latency: {p99:.2f}ms")

    return p50, p95, p99


async def benchmark_relationship_creation(backend, num_relationships: int = 50) -> float:
    """
    Measure relationship creation time.

    Args:
        backend: Backend instance to test
        num_relationships: Number of relationships to create

    Returns:
        Average time per relationship in milliseconds
    """
    print(f"\n{'='*60}")
    print(f"Benchmark: Relationship Creation ({num_relationships} relationships)")
    print(f"{'='*60}")

    # Create two memories to link
    memory1 = Memory(
        type=MemoryType.PROBLEM,
        title="Source Memory",
        content="Source memory content",
        tags=["source"],
        importance=0.7,
        confidence=0.9
    )
    memory2 = Memory(
        type=MemoryType.SOLUTION,
        title="Target Memory",
        content="Target memory content",
        tags=["target"],
        importance=0.8,
        confidence=0.95
    )

    id1 = await backend.store_memory(memory1)
    id2 = await backend.store_memory(memory2)

    relationship_times = []

    for i in range(num_relationships):
        start_time = time.perf_counter()
        await backend.create_relationship(
            from_memory_id=id1,
            to_memory_id=id2,
            relationship_type=RelationshipType.SOLVES
        )
        end_time = time.perf_counter()

        relationship_times.append((end_time - start_time) * 1000)

    avg_time = statistics.mean(relationship_times)

    print(f"✓ Created {num_relationships} relationships")
    print(f"✓ Average time: {avg_time:.2f}ms per relationship")

    return avg_time


async def main():
    """Run all benchmarks."""
    print("\n" + "="*60)
    print("MemoryGraph Backend Performance Validation")
    print("="*60)
    print("\nBackend: SQLite (default)")
    print("Note: For FalkorDB benchmarking, run against your own deployment")

    # Create SQLite backend with in-memory database for benchmarking
    sqlite_backend = SQLiteFallbackBackend(":memory:")
    await sqlite_backend.connect()
    await sqlite_backend.initialize_schema()
    backend = SQLiteMemoryDatabase(sqlite_backend)

    try:
        # Run benchmarks
        throughput = await benchmark_insert_throughput(backend, num_memories=100)
        p50, p95, p99 = await benchmark_query_latency(backend, num_queries=50)
        avg_rel_time = await benchmark_relationship_creation(backend, num_relationships=50)

        # Summary
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")
        print(f"✓ Insert throughput: {throughput:.2f} memories/sec")
        print(f"✓ Query latency (p50): {p50:.2f}ms")
        print(f"✓ Query latency (p95): {p95:.2f}ms")
        print(f"✓ Query latency (p99): {p99:.2f}ms")
        print(f"✓ Relationship creation: {avg_rel_time:.2f}ms/relationship")

        # Performance expectations
        print(f"\n{'='*60}")
        print("Performance Expectations")
        print(f"{'='*60}")
        print("✓ SQLite (embedded): Good for <10k memories, single-user")
        print("✓ FalkorDB (server): Excellent for >10k memories, multi-user")
        print("✓ FalkorDBLite (embedded): Similar to SQLite but with native Cypher")
        print("\nFor production workloads >10k memories, consider FalkorDB server deployment.")
        print("FalkorDB provides ~500x faster p99 latency compared to other graph databases.")

    finally:
        await sqlite_backend.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
