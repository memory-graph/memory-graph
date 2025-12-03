"""
Tests for pagination utilities.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from memorygraph.utils.pagination import (
    paginate_memories,
    count_memories,
    count_relationships,
    get_all_memories
)
from memorygraph.models import Memory, MemoryType, PaginatedResult, Relationship, RelationshipType, RelationshipProperties


def create_paginated_result(results, total_count, has_more, limit=1000, offset=0):
    """Helper to create PaginatedResult with all required fields."""
    return PaginatedResult(
        results=results,
        total_count=total_count,
        limit=limit,
        offset=offset,
        has_more=has_more,
        next_offset=offset + limit if has_more else None
    )


@pytest.mark.asyncio
async def test_paginate_memories_with_pagination_support():
    """Test pagination with a database that supports search_memories_paginated."""
    # Create mock memories
    memories_batch1 = [
        Memory(id="1", type=MemoryType.TASK, title="Memory 1", content="Content 1"),
        Memory(id="2", type=MemoryType.TASK, title="Memory 2", content="Content 2"),
    ]
    memories_batch2 = [
        Memory(id="3", type=MemoryType.TASK, title="Memory 3", content="Content 3"),
    ]

    # Mock database with paginated search
    db = MagicMock()
    db.search_memories_paginated = AsyncMock(side_effect=[
        create_paginated_result(memories_batch1, 3, True, limit=2, offset=0),
        create_paginated_result(memories_batch2, 3, False, limit=2, offset=2),
    ])

    # Collect all batches
    all_batches = []
    async for batch in paginate_memories(db, batch_size=2):
        all_batches.append(batch)

    # Verify we got 2 batches
    assert len(all_batches) == 2
    assert all_batches[0] == memories_batch1
    assert all_batches[1] == memories_batch2

    # Verify calls
    assert db.search_memories_paginated.call_count == 2


@pytest.mark.asyncio
async def test_paginate_memories_without_pagination_support():
    """Test pagination with a database that only supports search_memories."""
    # Create mock memories
    memories_batch1 = [
        Memory(id="1", type=MemoryType.TASK, title="Memory 1", content="Content 1"),
        Memory(id="2", type=MemoryType.TASK, title="Memory 2", content="Content 2"),
    ]
    memories_batch2 = [
        Memory(id="3", type=MemoryType.TASK, title="Memory 3", content="Content 3"),
    ]

    # Mock database without paginated search
    db = MagicMock(spec=['search_memories'])
    db.search_memories = AsyncMock(side_effect=[
        memories_batch1,  # First batch (full)
        memories_batch2,  # Second batch (partial - less than batch_size)
    ])

    # Collect all batches
    all_batches = []
    async for batch in paginate_memories(db, batch_size=2):
        all_batches.append(batch)

    # Verify we got 2 batches
    assert len(all_batches) == 2
    assert all_batches[0] == memories_batch1
    assert all_batches[1] == memories_batch2

    # Verify calls
    assert db.search_memories.call_count == 2


@pytest.mark.asyncio
async def test_paginate_memories_with_progress_callback():
    """Test pagination with progress callback."""
    # Create mock memories
    memories = [
        Memory(id="1", type=MemoryType.TASK, title="Memory 1", content="Content 1"),
        Memory(id="2", type=MemoryType.TASK, title="Memory 2", content="Content 2"),
    ]

    # Mock database
    db = MagicMock()
    db.search_memories_paginated = AsyncMock(return_value=create_paginated_result(
        memories, 2, False
    ))

    # Track progress
    progress_calls = []

    def progress_callback(count):
        progress_calls.append(count)

    # Paginate with progress
    async for batch in paginate_memories(db, batch_size=2, progress_callback=progress_callback):
        pass

    # Verify progress was reported
    assert progress_calls == [2]


@pytest.mark.asyncio
async def test_count_memories_with_pagination():
    """Test counting memories with paginated search."""
    db = MagicMock()
    db.search_memories_paginated = AsyncMock(return_value=create_paginated_result(
        [], 42, False
    ))

    count = await count_memories(db)
    assert count == 42


@pytest.mark.asyncio
async def test_count_memories_without_pagination():
    """Test counting memories without paginated search."""
    # Create 1500 memories split into batches (to test that it goes beyond one batch)
    # First batch: 1000 items (full batch)
    memories1 = [Memory(id=str(i), type=MemoryType.TASK, title=f"M{i}", content=f"C{i}") for i in range(1000)]
    # Second batch: 500 items (partial batch - triggers stop)
    memories2 = [Memory(id=str(i), type=MemoryType.TASK, title=f"M{i}", content=f"C{i}") for i in range(1000, 1500)]

    db = MagicMock()
    # Ensure the mock doesn't have search_memories_paginated by specifying spec
    db = MagicMock(spec=['search_memories'])
    # First batch returns 1000 (full), second batch returns 500 (partial - triggers stop)
    db.search_memories = AsyncMock(side_effect=[memories1, memories2])

    count = await count_memories(db)
    assert count == 1500


@pytest.mark.asyncio
async def test_count_relationships():
    """Test counting relationships with deduplication."""
    # Create mock memories
    memories = [
        Memory(id="1", type=MemoryType.TASK, title="Memory 1", content="Content 1"),
        Memory(id="2", type=MemoryType.TASK, title="Memory 2", content="Content 2"),
    ]

    # Create mock relationships
    rel1 = (
        Memory(id="2", type=MemoryType.TASK, title="Memory 2", content="Content 2"),
        Relationship(
            from_memory_id="1",
            to_memory_id="2",
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties()
        )
    )
    rel2 = (
        Memory(id="1", type=MemoryType.TASK, title="Memory 1", content="Content 1"),
        Relationship(
            from_memory_id="2",
            to_memory_id="1",
            type=RelationshipType.RELATED_TO,
            properties=RelationshipProperties()
        )
    )

    db = MagicMock()
    db.search_memories_paginated = AsyncMock(return_value=create_paginated_result(
        memories, 2, False
    ))
    db.get_related_memories = AsyncMock(side_effect=[
        [rel1],  # Memory 1 has 1 relationship
        [rel2],  # Memory 2 has 1 relationship
    ])

    count = await count_relationships(db)
    assert count == 2  # Two unique relationships


@pytest.mark.asyncio
async def test_count_relationships_with_deduplication():
    """Test that count_relationships deduplicates properly."""
    # Create mock memories
    memory1 = Memory(id="1", type=MemoryType.TASK, title="Memory 1", content="Content 1")
    memory2 = Memory(id="2", type=MemoryType.TASK, title="Memory 2", content="Content 2")

    # Create same relationship from both sides
    rel_forward = (
        memory2,
        Relationship(
            from_memory_id="1",
            to_memory_id="2",
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties()
        )
    )
    rel_backward = (
        memory1,
        Relationship(
            from_memory_id="1",
            to_memory_id="2",
            type=RelationshipType.SOLVES,
            properties=RelationshipProperties()
        )
    )

    db = MagicMock()
    db.search_memories_paginated = AsyncMock(return_value=create_paginated_result(
        [memory1, memory2], 2, False
    ))
    db.get_related_memories = AsyncMock(side_effect=[
        [rel_forward],  # Memory 1 -> Memory 2
        [rel_backward],  # Memory 2 -> Memory 1 (same relationship)
    ])

    count = await count_relationships(db)
    assert count == 1  # Should deduplicate to 1 relationship


@pytest.mark.asyncio
async def test_get_all_memories():
    """Test getting all memories."""
    memories1 = [Memory(id=str(i), type=MemoryType.TASK, title=f"M{i}", content=f"C{i}") for i in range(5)]
    memories2 = [Memory(id=str(i), type=MemoryType.TASK, title=f"M{i}", content=f"C{i}") for i in range(5, 8)]

    db = MagicMock()
    db.search_memories_paginated = AsyncMock(side_effect=[
        create_paginated_result(memories1, 8, True),
        create_paginated_result(memories2, 8, False),
    ])

    all_memories = await get_all_memories(db)
    assert len(all_memories) == 8
    assert all_memories == memories1 + memories2


@pytest.mark.asyncio
async def test_paginate_memories_empty_database():
    """Test pagination with empty database."""
    db = MagicMock()
    db.search_memories_paginated = AsyncMock(return_value=create_paginated_result(
        [], 0, False
    ))

    batches = []
    async for batch in paginate_memories(db, batch_size=10):
        batches.append(batch)

    # Should get no batches (empty list is not yielded)
    assert len(batches) == 0
