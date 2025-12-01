"""
Tests for enriched search results with relationship context.

Tests Phase 2.B functionality:
- Include immediate relationships in search results
- include_relationships parameter
- Match quality hints
- Relationship context summaries
"""

import pytest
from datetime import datetime
from memorygraph.models import (
    Memory, MemoryType, SearchQuery, RelationshipType,
    RelationshipProperties
)
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend


@pytest.fixture
async def test_db():
    """Create a test database with memories and relationships."""
    backend = SQLiteFallbackBackend(":memory:")
    await backend.connect()
    await backend.initialize_schema()
    db = SQLiteMemoryDatabase(backend)

    # Create test memories
    problem = Memory(
        id="problem-1",
        type=MemoryType.PROBLEM,
        title="API Timeout Errors",
        content="Users experiencing timeout errors when calling external API",
        tags=["api", "timeout", "error"],
        importance=0.8
    )

    solution = Memory(
        id="solution-1",
        type=MemoryType.SOLUTION,
        title="Retry with Exponential Backoff",
        content="Implemented retry mechanism with exponential backoff",
        tags=["retry", "backoff", "solution"],
        importance=0.9
    )

    project = Memory(
        id="project-1",
        type=MemoryType.PROJECT,
        title="Payment Integration Project",
        content="Integration with payment gateway API",
        tags=["payment", "integration"],
        importance=0.7
    )

    # Store memories
    await db.store_memory(problem)
    await db.store_memory(solution)
    await db.store_memory(project)

    # Create relationships
    await db.create_relationship(
        from_memory_id="solution-1",
        to_memory_id="problem-1",
        relationship_type=RelationshipType.SOLVES,
        properties=RelationshipProperties(
            strength=0.9,
            confidence=0.95,
            context="Exponential backoff resolves API timeout issues"
        )
    )

    await db.create_relationship(
        from_memory_id="solution-1",
        to_memory_id="project-1",
        relationship_type=RelationshipType.USED_IN,
        properties=RelationshipProperties(
            strength=0.8,
            confidence=0.9,
            context="Applied in payment integration"
        )
    )

    yield db


@pytest.mark.asyncio
async def test_search_includes_relationships_by_default(test_db):
    """Test that search results include relationships by default."""
    query = SearchQuery(query="timeout")

    # Search should return enriched results
    results = await test_db.search_memories(query)

    assert len(results) > 0
    problem = results[0]

    # Check that relationships are included in the result
    # Note: This test will initially fail until we implement the feature
    assert hasattr(problem, 'relationships') or hasattr(problem, 'related_memories'), \
        "Search results should include relationship information"


@pytest.mark.asyncio
async def test_search_with_include_relationships_true(test_db):
    """Test search with include_relationships=True."""
    query = SearchQuery(query="retry", include_relationships=True)

    results = await test_db.search_memories(query)

    assert len(results) > 0
    solution = results[0]
    assert solution.title == "Retry with Exponential Backoff"

    # Should have relationship information
    assert hasattr(solution, 'relationships') or hasattr(solution, 'related_memories'), \
        "Results should include relationships when explicitly requested"


@pytest.mark.asyncio
async def test_search_with_include_relationships_false(test_db):
    """Test search with include_relationships=False for performance."""
    query = SearchQuery(query="retry", include_relationships=False)

    results = await test_db.search_memories(query)

    assert len(results) > 0
    solution = results[0]
    assert solution.title == "Retry with Exponential Backoff"

    # Should NOT have relationship information (or it should be empty)
    if hasattr(solution, 'relationships'):
        assert solution.relationships is None or len(solution.relationships) == 0, \
            "Results should not include relationships when include_relationships=False"


@pytest.mark.asyncio
async def test_relationship_context_structure(test_db):
    """Test that relationship context has the expected structure."""
    query = SearchQuery(query="retry", include_relationships=True)

    results = await test_db.search_memories(query)
    solution = results[0]

    # Check relationship structure
    # Expected format from workplan:
    # {
    #   "solves": ["TimeoutError", "APIRateLimiting"],
    #   "used_in": ["ProjectAlpha"],
    #   "related_to": ["ErrorHandling"]
    # }
    assert hasattr(solution, 'relationships'), "Solution should have relationships attribute"

    relationships = solution.relationships

    # Should have solves and used_in relationships
    assert 'solves' in relationships or 'SOLVES' in relationships, \
        "Should include SOLVES relationships"
    assert 'used_in' in relationships or 'USED_IN' in relationships, \
        "Should include USED_IN relationships"


@pytest.mark.asyncio
async def test_match_quality_hints_present(test_db):
    """Test that search results include match quality hints."""
    query = SearchQuery(query="timeout error")

    results = await test_db.search_memories(query)

    assert len(results) > 0
    result = results[0]

    # Check for match quality hints
    # Expected format from workplan:
    # {
    #   "matched_fields": ["observations"],
    #   "matched_terms": ["timeout", "retry"],
    #   "match_quality": "high"
    # }
    assert hasattr(result, 'match_info'), "Result should have match_info attribute"

    match_info = result.match_info
    assert 'matched_fields' in match_info, "Should include matched_fields"
    assert 'matched_terms' in match_info, "Should include matched_terms"
    assert 'match_quality' in match_info, "Should include match_quality"


@pytest.mark.asyncio
async def test_match_quality_accuracy(test_db):
    """Test that match quality hints accurately reflect the match."""
    query = SearchQuery(query="timeout")

    results = await test_db.search_memories(query)
    problem = results[0]

    match_info = problem.match_info

    # Should indicate which fields matched
    matched_fields = match_info['matched_fields']
    assert any(field in ['title', 'content', 'tags'] for field in matched_fields), \
        "Matched fields should be one of title, content, or tags"

    # Should list matched terms
    matched_terms = match_info['matched_terms']
    assert 'timeout' in matched_terms or 'timeout' in str(matched_terms).lower(), \
        "Should include 'timeout' in matched terms"


@pytest.mark.asyncio
async def test_context_summary_present(test_db):
    """Test that results include natural language context summary."""
    query = SearchQuery(query="retry", include_relationships=True)

    results = await test_db.search_memories(query)
    solution = results[0]

    # Check for context summary
    # Expected format: "Solution that solved TimeoutError in ProjectAlpha"
    assert hasattr(solution, 'context_summary'), \
        "Result should have context_summary attribute"

    context_summary = solution.context_summary
    assert isinstance(context_summary, str), "Context summary should be a string"
    assert len(context_summary) <= 100, "Context summary should be concise (<100 chars)"


@pytest.mark.asyncio
async def test_context_summary_accuracy(test_db):
    """Test that context summary accurately describes the memory's relationships."""
    query = SearchQuery(query="retry", include_relationships=True)

    results = await test_db.search_memories(query)
    solution = results[0]

    context_summary = solution.context_summary.lower()

    # Should mention what it solves
    assert 'solves' in context_summary or 'solved' in context_summary, \
        "Summary should mention SOLVES relationship"

    # Should mention either the problem or project
    assert 'timeout' in context_summary or 'payment' in context_summary or 'project' in context_summary, \
        "Summary should reference related memories"


@pytest.mark.asyncio
async def test_relationship_performance(test_db):
    """Test that including relationships doesn't significantly impact performance."""
    import time

    # Search without relationships
    start = time.time()
    query1 = SearchQuery(query="timeout", include_relationships=False)
    await test_db.search_memories(query1)
    time_without = time.time() - start

    # Search with relationships
    start = time.time()
    query2 = SearchQuery(query="timeout", include_relationships=True)
    await test_db.search_memories(query2)
    time_with = time.time() - start

    # Should add <100ms overhead (as per workplan)
    overhead = time_with - time_without
    assert overhead < 0.1, f"Relationship overhead should be <100ms, got {overhead*1000:.2f}ms"


@pytest.mark.asyncio
async def test_empty_relationships_handled_gracefully(test_db):
    """Test that memories without relationships are handled properly."""
    # Create memory with no relationships
    orphan = Memory(
        id="orphan-1",
        type=MemoryType.GENERAL,
        title="Standalone Note",
        content="This memory has no relationships",
        tags=["standalone"],
        importance=0.5
    )
    await test_db.store_memory(orphan)

    query = SearchQuery(query="standalone", include_relationships=True)
    results = await test_db.search_memories(query)

    assert len(results) > 0
    result = results[0]

    # Should have empty or minimal relationship context
    if hasattr(result, 'relationships'):
        assert result.relationships == {} or result.relationships == {}, \
            "Memory with no relationships should have empty relationship context"

    if hasattr(result, 'context_summary'):
        # Summary should be minimal or indicate no relationships
        assert len(result.context_summary) < 50, \
            "Context summary for orphan memory should be brief"


@pytest.mark.asyncio
async def test_multiple_relationships_same_type(test_db):
    """Test handling of multiple relationships of the same type."""
    # Create two problems that the solution solves
    problem2 = Memory(
        id="problem-2",
        type=MemoryType.PROBLEM,
        title="API Rate Limiting",
        content="Hitting rate limits on external API",
        tags=["api", "rate-limit"],
        importance=0.7
    )
    await test_db.store_memory(problem2)

    # Link solution to both problems
    await test_db.create_relationship(
        from_memory_id="solution-1",
        to_memory_id="problem-2",
        relationship_type=RelationshipType.SOLVES,
        properties=RelationshipProperties(strength=0.85, confidence=0.9)
    )

    query = SearchQuery(query="retry", include_relationships=True)
    results = await test_db.search_memories(query)
    solution = results[0]

    # Should list both problems under 'solves'
    relationships = solution.relationships
    solves_key = 'solves' if 'solves' in relationships else 'SOLVES'

    assert len(relationships[solves_key]) >= 2, \
        "Should include all SOLVES relationships"


@pytest.mark.asyncio
async def test_bidirectional_relationships(test_db):
    """Test that relationships are shown correctly regardless of direction."""
    # Search for the problem (which is the target of a SOLVES relationship)
    query = SearchQuery(query="timeout error", include_relationships=True)
    results = await test_db.search_memories(query)

    problem = results[0]

    # Problem should show that a solution exists
    # Either as 'solved_by' or in relationships list
    assert hasattr(problem, 'relationships'), "Problem should have relationships"
    relationships = problem.relationships

    # Should have some relationship information (the solution that solves it)
    assert len(relationships) > 0, \
        "Problem should show relationship to its solution"
