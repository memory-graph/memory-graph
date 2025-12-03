"""
Pagination utilities for working with memories across different backends.

Provides reusable pagination helpers that work with both MemoryDatabase
and SQLiteMemoryDatabase interfaces.
"""

import logging
from typing import AsyncIterator, List, Callable, Optional

from ..models import Memory, SearchQuery

logger = logging.getLogger(__name__)


async def paginate_memories(
    db,  # MemoryDatabase or SQLiteMemoryDatabase
    batch_size: int = 1000,
    progress_callback: Optional[Callable[[int], None]] = None
) -> AsyncIterator[List[Memory]]:
    """
    Async generator that yields batches of memories.

    Works with both MemoryDatabase and SQLiteMemoryDatabase by using
    the search_memories interface with pagination support.

    Args:
        db: Database instance (any backend)
        batch_size: Number of memories to fetch per batch
        progress_callback: Optional callback(total_yielded) for progress reporting

    Yields:
        Batches of Memory objects

    Example:
        async for batch in paginate_memories(db, batch_size=500):
            for memory in batch:
                print(memory.title)
    """
    offset = 0
    total_yielded = 0

    while True:
        query = SearchQuery(
            query="",  # Empty query matches all memories
            limit=batch_size,
            offset=offset,
            match_mode="any"
        )

        # Use paginated search if available, fallback to regular search
        if hasattr(db, 'search_memories_paginated'):
            result = await db.search_memories_paginated(query)
            memories = result.results
            has_more = result.has_more
        else:
            # Fallback for backends without pagination
            memories = await db.search_memories(query)
            has_more = len(memories) >= batch_size

        if memories:
            yield memories
            total_yielded += len(memories)

            if progress_callback:
                progress_callback(total_yielded)

        if not has_more or not memories:
            break

        offset += batch_size


async def count_memories(db) -> int:
    """
    Count total memories in database using efficient method.

    Args:
        db: Database instance (any backend)

    Returns:
        Total number of memories
    """
    query = SearchQuery(query="", limit=1, offset=0, match_mode="any")

    # Use paginated search for efficient counting if available
    if hasattr(db, 'search_memories_paginated'):
        result = await db.search_memories_paginated(query)
        return result.total_count
    else:
        # Fallback: count manually by iterating
        count = 0
        async for batch in paginate_memories(db, batch_size=1000):
            count += len(batch)
        return count


async def count_relationships(db) -> int:
    """
    Count total relationships in database.

    Args:
        db: Database instance (any backend)

    Returns:
        Total number of relationships (deduplicated)
    """
    count = 0
    seen_relationships = set()

    async for batch in paginate_memories(db, batch_size=1000):
        for memory in batch:
            try:
                related = await db.get_related_memories(memory.id, max_depth=1)
                for _, relationship in related:
                    # Use tuple as key for deduplication
                    key = (
                        relationship.from_memory_id,
                        relationship.to_memory_id,
                        relationship.type.value
                    )
                    if key not in seen_relationships:
                        seen_relationships.add(key)
                        count += 1
            except Exception as e:
                logger.warning(f"Failed to count relationships for memory {memory.id}: {e}")
                continue

    return count


async def get_all_memories(db) -> List[Memory]:
    """
    Get all memories from database.

    Args:
        db: Database instance (any backend)

    Returns:
        List of all memories

    Warning:
        This loads all memories into memory. For large databases,
        prefer using paginate_memories() to process in batches.
    """
    all_memories = []
    async for batch in paginate_memories(db, batch_size=1000):
        all_memories.extend(batch)
    return all_memories
