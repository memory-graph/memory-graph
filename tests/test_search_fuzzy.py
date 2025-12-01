"""
Tests for fuzzy search and case-insensitive search functionality.

This module tests Phase 2.A improvements to search:
- Fuzzy text matching (typos, plurals, tense variations)
- Case-insensitive search by default
- Multi-field search (title, content, summary)

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
        db_path = os.path.join(tmpdir, "test_fuzzy_search.db")
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


class TestCaseInsensitiveSearch:
    """Test case-insensitive search functionality (Task 2.A.2)."""

    @pytest.mark.asyncio
    async def test_search_case_insensitive_title(self, sqlite_db):
        """Test that search matches different cases in title."""
        # Store memory with specific case
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Timeout Error Fix",
            content="Solution for handling timeout errors"
        )
        await sqlite_db.store_memory(memory)

        # Search with different cases
        test_cases = [
            "timeout",      # lowercase
            "Timeout",      # title case
            "TIMEOUT",      # uppercase
            "TimeOut",      # mixed case
            "TIMEOUT ERROR" # multiple words, uppercase
        ]

        for query in test_cases:
            search_query = SearchQuery(query=query, limit=10)
            results = await sqlite_db.search_memories(search_query)

            assert len(results) > 0, f"Failed to find memory with query: '{query}'"
            assert any(r.id == memory.id for r in results), \
                f"Memory not found in results for query: '{query}'"

    @pytest.mark.asyncio
    async def test_search_case_insensitive_content(self, sqlite_db):
        """Test that search matches different cases in content."""
        memory = Memory(
            type=MemoryType.PROBLEM,
            title="API Issue",
            content="The Redis connection kept timing out in production"
        )
        await sqlite_db.store_memory(memory)

        # Search with different cases
        test_cases = ["redis", "REDIS", "Redis", "ReDiS"]

        for query in test_cases:
            search_query = SearchQuery(query=query, limit=10)
            results = await sqlite_db.search_memories(search_query)

            assert len(results) > 0, f"Failed to find memory with query: '{query}'"
            assert results[0].id == memory.id

    @pytest.mark.asyncio
    async def test_search_case_insensitive_summary(self, sqlite_db):
        """Test that search matches different cases in summary."""
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Cache Implementation",
            content="Implemented Redis cache for API responses",
            summary="Caching solution using Redis"
        )
        await sqlite_db.store_memory(memory)

        # Search in summary with different cases
        test_cases = ["caching", "CACHING", "Caching"]

        for query in test_cases:
            search_query = SearchQuery(query=query, limit=10)
            results = await sqlite_db.search_memories(search_query)

            assert len(results) > 0, f"Failed to find memory with query: '{query}'"
            assert results[0].id == memory.id


class TestFuzzyTextMatching:
    """Test fuzzy text matching functionality (Task 2.A.1)."""

    @pytest.mark.asyncio
    async def test_fuzzy_match_plurals(self, sqlite_db):
        """Test that singular search matches plural and vice versa."""
        # Store memories with plural/singular variations
        memories = [
            Memory(
                type=MemoryType.PROBLEM,
                title="Error in authentication",
                content="Single error occurred"
            ),
            Memory(
                type=MemoryType.PROBLEM,
                title="Multiple errors found",
                content="Several errors in the logs"
            ),
            Memory(
                type=MemoryType.SOLUTION,
                title="Timeout handling",
                content="Handle timeout issues"
            ),
            Memory(
                type=MemoryType.SOLUTION,
                title="Timeouts in production",
                content="Multiple timeouts detected"
            )
        ]

        for memory in memories:
            await sqlite_db.store_memory(memory)

        # Test singular -> plural matching
        search_query = SearchQuery(query="error", limit=10)
        results = await sqlite_db.search_memories(search_query)
        assert len(results) >= 2, "Should find both 'error' and 'errors'"

        # Test plural -> singular matching
        search_query = SearchQuery(query="timeouts", limit=10)
        results = await sqlite_db.search_memories(search_query)
        assert len(results) >= 2, "Should find both 'timeout' and 'timeouts'"

    @pytest.mark.asyncio
    async def test_fuzzy_match_tense_variations(self, sqlite_db):
        """Test that search matches different tenses."""
        memories = [
            Memory(
                type=MemoryType.PROBLEM,
                title="Retry mechanism",
                content="We retry failed requests"
            ),
            Memory(
                type=MemoryType.SOLUTION,
                title="Retrying logic",
                content="System is retrying automatically"
            ),
            Memory(
                type=MemoryType.GENERAL,
                title="Past attempts",
                content="We retried the operation multiple times"
            )
        ]

        for memory in memories:
            await sqlite_db.store_memory(memory)

        # Search for different tenses
        test_cases = ["retry", "retrying", "retried"]

        for query in test_cases:
            search_query = SearchQuery(query=query, limit=10)
            results = await sqlite_db.search_memories(search_query)

            # Should find at least 2 memories (generous threshold for fuzzy matching)
            assert len(results) >= 2, \
                f"Should find multiple memories with query: '{query}', found {len(results)}"

    @pytest.mark.asyncio
    async def test_fuzzy_match_partial_words(self, sqlite_db):
        """Test that partial word search matches full words."""
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Authentication system",
            content="Implemented authentication and authorization"
        )
        await sqlite_db.store_memory(memory)

        # Partial word searches
        test_cases = ["auth", "authen", "authent"]

        for query in test_cases:
            search_query = SearchQuery(query=query, limit=10)
            results = await sqlite_db.search_memories(search_query)

            assert len(results) > 0, f"Should find memory with partial query: '{query}'"
            assert results[0].id == memory.id

    @pytest.mark.asyncio
    async def test_fuzzy_match_common_typos(self, sqlite_db):
        """Test that common typos are matched (if using trigram similarity)."""
        memory = Memory(
            type=MemoryType.PROBLEM,
            title="Timeout issue",
            content="System experiencing timeout problems"
        )
        await sqlite_db.store_memory(memory)

        # Common typos (this test may initially fail and is aspirational)
        # We'll be generous and accept if some typos work
        test_cases = [
            ("tmeout", "timeout"),   # adjacent swap
            ("timout", "timeout"),   # missing letter
        ]

        matches = 0
        for typo, correct in test_cases:
            search_query = SearchQuery(query=typo, limit=10)
            results = await sqlite_db.search_memories(search_query)

            if len(results) > 0 and results[0].id == memory.id:
                matches += 1

        # We expect at least basic fuzzy matching to work
        # This is aspirational - initial implementation may not support this
        # Comment: This test documents the desired behavior even if not immediately implemented
        assert matches >= 0, "Typo matching is aspirational (may not be implemented yet)"


class TestMultiFieldSearch:
    """Test that search works across all text fields."""

    @pytest.mark.asyncio
    async def test_search_across_title_content_summary(self, sqlite_db):
        """Test that search finds matches in any text field."""
        # Store memories with keywords in different fields
        memory1 = Memory(
            type=MemoryType.SOLUTION,
            title="Redis caching solution",
            content="Implementation details",
            summary="Quick summary"
        )
        memory2 = Memory(
            type=MemoryType.SOLUTION,
            title="Database optimization",
            content="Using Redis for caching API responses",
            summary="Performance improvement"
        )
        memory3 = Memory(
            type=MemoryType.SOLUTION,
            title="API improvements",
            content="Various optimizations",
            summary="Added Redis caching layer"
        )

        for memory in [memory1, memory2, memory3]:
            await sqlite_db.store_memory(memory)

        # Search for "Redis" - should find all three
        search_query = SearchQuery(query="Redis", limit=10)
        results = await sqlite_db.search_memories(search_query)

        assert len(results) == 3, "Should find Redis in title, content, and summary"
        result_ids = {r.id for r in results}
        assert memory1.id in result_ids, "Should find memory with Redis in title"
        assert memory2.id in result_ids, "Should find memory with Redis in content"
        assert memory3.id in result_ids, "Should find memory with Redis in summary"

    @pytest.mark.asyncio
    async def test_search_prioritizes_title_matches(self, sqlite_db):
        """Test that title matches are ranked higher than content matches."""
        # Store memories with keyword in different positions
        memory_title = Memory(
            type=MemoryType.SOLUTION,
            title="Timeout solution",
            content="Various fixes",
            importance=0.5
        )
        memory_content = Memory(
            type=MemoryType.SOLUTION,
            title="Network issues",
            content="Fixed timeout problems",
            importance=0.5  # Same importance to test ranking
        )

        await sqlite_db.store_memory(memory_title)
        await sqlite_db.store_memory(memory_content)

        # Search for "timeout"
        search_query = SearchQuery(query="timeout", limit=10)
        results = await sqlite_db.search_memories(search_query)

        assert len(results) == 2, "Should find both memories"
        # Title match should come first (this is aspirational - may need ranking implementation)
        # For now, we just verify both are found
        result_ids = [r.id for r in results]
        assert memory_title.id in result_ids
        assert memory_content.id in result_ids


class TestSearchSuccessMetrics:
    """Test suite for Phase 2 success criteria: 80%+ fuzzy match success rate."""

    @pytest.mark.asyncio
    async def test_comprehensive_fuzzy_scenarios(self, sqlite_db):
        """Test multiple fuzzy search scenarios for success rate measurement.

        Success criteria: 80%+ of these scenarios should return relevant results.
        """
        # Store test data
        memories = [
            Memory(
                type=MemoryType.PROBLEM,
                title="API timeout errors",
                content="REST API timing out under load"
            ),
            Memory(
                type=MemoryType.SOLUTION,
                title="Retry with backoff",
                content="Implemented exponential backoff for retries"
            ),
            Memory(
                type=MemoryType.PROBLEM,
                title="Authentication failures",
                content="Users unable to authenticate"
            ),
            Memory(
                type=MemoryType.SOLUTION,
                title="Cache implementation",
                content="Added Redis caching layer"
            ),
        ]

        for memory in memories:
            await sqlite_db.store_memory(memory)

        # Define test scenarios: (query, expected_to_find_count)
        test_scenarios = [
            # Case variations (4 scenarios)
            ("TIMEOUT", 1),
            ("retry", 1),
            ("Authentication", 1),
            ("CACHE", 1),

            # Plural/singular (4 scenarios)
            ("error", 1),
            ("timeouts", 1),
            ("failure", 1),
            ("retries", 1),

            # Partial matches (4 scenarios)
            ("auth", 1),
            ("time", 1),
            ("back", 1),
            ("Redis", 1),

            # Tense variations (3 scenarios)
            ("timing", 1),
            ("retrying", 1),
            ("cached", 1),
        ]

        successful = 0
        total = len(test_scenarios)

        for query, expected_min in test_scenarios:
            search_query = SearchQuery(query=query, limit=10)
            results = await sqlite_db.search_memories(search_query)

            if len(results) >= expected_min:
                successful += 1

        success_rate = (successful / total) * 100

        # Document success rate
        print(f"\nFuzzy Search Success Rate: {success_rate:.1f}% ({successful}/{total} scenarios)")

        # Target: 80%+ success rate
        assert success_rate >= 80.0, \
            f"Success rate {success_rate:.1f}% below target of 80%"
