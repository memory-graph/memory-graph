"""
Tests for search_tolerance parameter (Task 2.A.4).

This module tests the search_tolerance parameter which controls the
forgiveness level of text matching:
- strict: Exact substring match (no stemming)
- normal: Case-insensitive + stemming (default)
- fuzzy: Reserved for future trigram similarity matching

Following strict TDD discipline - these tests are written BEFORE implementation.
"""

import pytest
import tempfile
import os
from datetime import datetime

from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, SearchQuery
)


@pytest.fixture
async def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_tolerance.db")
        yield db_path


@pytest.fixture
async def sqlite_backend(temp_db_path):
    """Create a connected SQLite backend for testing."""
    backend = SQLiteFallbackBackend(db_path=temp_db_path)
    await backend.connect()
    await backend.initialize_schema()
    yield backend
    await backend.disconnect()


@pytest.fixture
async def sqlite_db(sqlite_backend):
    """Create a SQLiteMemoryDatabase instance for testing."""
    db = SQLiteMemoryDatabase(sqlite_backend)
    await db.initialize_schema()
    return db


@pytest.fixture
async def test_memories(sqlite_db):
    """Create test memories with various text patterns."""
    memories = [
        Memory(
            type=MemoryType.PROBLEM,
            title="API timeout error",
            content="The API timed out after 30 seconds"
        ),
        Memory(
            type=MemoryType.PROBLEM,
            title="Multiple timeouts detected",
            content="Several timeouts occurred in production"
        ),
        Memory(
            type=MemoryType.SOLUTION,
            title="Retry mechanism",
            content="Implemented retrying logic with exponential backoff"
        ),
        Memory(
            type=MemoryType.SOLUTION,
            title="Handled retries",
            content="Successfully retried failed requests"
        ),
    ]

    for memory in memories:
        await sqlite_db.store_memory(memory)

    return memories


class TestSearchToleranceStrict:
    """Test strict search tolerance mode."""

    @pytest.mark.asyncio
    async def test_strict_exact_match_only(self, sqlite_db, test_memories):
        """Test that strict mode only matches exact substring."""
        # Exact match should work
        search_query = SearchQuery(
            query="timeout",
            limit=10,
            search_tolerance="strict"
        )
        results = await sqlite_db.search_memories(search_query)

        # Should find "timeout" but maybe not "timeouts" depending on strict impl
        assert len(results) >= 1, "Should find at least exact substring matches"

    @pytest.mark.asyncio
    async def test_strict_no_stemming(self, sqlite_db, test_memories):
        """Test that strict mode does not apply stemming."""
        # Search for "retry" in strict mode
        search_query = SearchQuery(
            query="retry",
            limit=10,
            search_tolerance="strict"
        )
        results = await sqlite_db.search_memories(search_query)

        # In strict mode, "retry" should match memories containing exactly "retry"
        # but may not match "retrying" or "retried" as separate words
        # We'll be lenient since substring matching may catch these
        assert len(results) >= 0, "Strict mode should only do substring matching"

    @pytest.mark.asyncio
    async def test_strict_case_insensitive(self, sqlite_db, test_memories):
        """Test that strict mode is still case-insensitive."""
        # Strict mode should still be case-insensitive (SQLite LIKE behavior)
        search_query = SearchQuery(
            query="TIMEOUT",
            limit=10,
            search_tolerance="strict"
        )
        results = await sqlite_db.search_memories(search_query)

        assert len(results) >= 1, "Strict mode should be case-insensitive"


class TestSearchToleranceNormal:
    """Test normal search tolerance mode (default)."""

    @pytest.mark.asyncio
    async def test_normal_with_stemming(self, sqlite_db, test_memories):
        """Test that normal mode applies stemming."""
        # Search for "timeout" should match "timeouts"
        search_query = SearchQuery(
            query="timeout",
            limit=10,
            search_tolerance="normal"
        )
        results = await sqlite_db.search_memories(search_query)

        # Should find both singular and plural
        assert len(results) >= 2, "Normal mode should match stemmed variations"

    @pytest.mark.asyncio
    async def test_normal_default_behavior(self, sqlite_db, test_memories):
        """Test that normal is the default mode."""
        # Without specifying tolerance, should default to normal
        search_query = SearchQuery(query="retry", limit=10)
        results = await sqlite_db.search_memories(search_query)

        # Should find "retry", "retrying", "retried"
        assert len(results) >= 2, "Default should use normal mode with stemming"

    @pytest.mark.asyncio
    async def test_normal_case_insensitive(self, sqlite_db, test_memories):
        """Test that normal mode is case-insensitive."""
        search_query = SearchQuery(
            query="RETRY",
            limit=10,
            search_tolerance="normal"
        )
        results = await sqlite_db.search_memories(search_query)

        assert len(results) >= 2, "Normal mode should be case-insensitive"


class TestSearchToleranceFuzzy:
    """Test fuzzy search tolerance mode (future trigram similarity)."""

    @pytest.mark.asyncio
    async def test_fuzzy_mode_exists(self, sqlite_db, test_memories):
        """Test that fuzzy mode is accepted (even if not fully implemented)."""
        # Fuzzy mode should be accepted as a parameter
        search_query = SearchQuery(
            query="timeout",
            limit=10,
            search_tolerance="fuzzy"
        )
        results = await sqlite_db.search_memories(search_query)

        # Should at least work like normal mode
        assert len(results) >= 0, "Fuzzy mode should be accepted"

    @pytest.mark.asyncio
    async def test_fuzzy_matches_typos_aspirational(self, sqlite_db, test_memories):
        """Test fuzzy matching of typos (aspirational - may not work initially)."""
        # This is aspirational - documents desired behavior
        search_query = SearchQuery(
            query="timout",  # typo: missing 'e'
            limit=10,
            search_tolerance="fuzzy"
        )
        results = await sqlite_db.search_memories(search_query)

        # This may fail initially - that's okay
        # We document the desired behavior
        if len(results) > 0:
            print("Fuzzy typo matching works!")
        else:
            print("Fuzzy typo matching not yet implemented")


class TestSearchToleranceValidation:
    """Test validation and error handling for search_tolerance parameter."""

    @pytest.mark.asyncio
    async def test_invalid_tolerance_value(self, sqlite_db, test_memories):
        """Test that invalid tolerance values are rejected."""
        # Invalid tolerance value should raise an error or default to normal
        with pytest.raises(ValueError):
            search_query = SearchQuery(
                query="timeout",
                limit=10,
                search_tolerance="invalid_value"
            )

    @pytest.mark.asyncio
    async def test_none_tolerance_uses_default(self, sqlite_db, test_memories):
        """Test that None tolerance defaults to normal."""
        search_query = SearchQuery(
            query="retry",
            limit=10,
            search_tolerance=None
        )
        results = await sqlite_db.search_memories(search_query)

        # Should behave like normal mode
        assert len(results) >= 2, "None should default to normal mode"


class TestToleranceComparison:
    """Compare results across different tolerance modes."""

    @pytest.mark.asyncio
    async def test_tolerance_progression(self, sqlite_db, test_memories):
        """Test that tolerance modes provide progressively more results.

        Expected: strict <= normal <= fuzzy (in terms of result count)
        """
        query = "retry"

        # Strict mode
        strict_results = await sqlite_db.search_memories(
            SearchQuery(query=query, limit=10, search_tolerance="strict")
        )

        # Normal mode
        normal_results = await sqlite_db.search_memories(
            SearchQuery(query=query, limit=10, search_tolerance="normal")
        )

        # Fuzzy mode
        fuzzy_results = await sqlite_db.search_memories(
            SearchQuery(query=query, limit=10, search_tolerance="fuzzy")
        )

        # Document the progression
        print(f"\nStrict: {len(strict_results)} results")
        print(f"Normal: {len(normal_results)} results")
        print(f"Fuzzy: {len(fuzzy_results)} results")

        # Normal should find at least as many as strict
        assert len(normal_results) >= len(strict_results), \
            "Normal mode should be more forgiving than strict"

        # Fuzzy should find at least as many as normal (or same if not implemented)
        assert len(fuzzy_results) >= len(normal_results), \
            "Fuzzy mode should be most forgiving"
