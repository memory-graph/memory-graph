"""
Tests for session briefing functionality (Phase 2.E).

This module tests the get_recent_activity tool and project context detection.
"""

import pytest
from datetime import datetime, timedelta
from memorygraph.models import Memory, MemoryType, MemoryContext, SearchQuery, RelationshipType, RelationshipProperties
from memorygraph.sqlite_database import SQLiteMemoryDatabase
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend


@pytest.fixture
async def db():
    """Create test database instance."""
    backend = SQLiteFallbackBackend(":memory:")
    await backend.connect()
    await backend.initialize_schema()
    database = SQLiteMemoryDatabase(backend)
    await database.initialize_schema()
    yield database
    await backend.disconnect()


@pytest.fixture
async def populated_db(db):
    """Database with test memories from different time periods."""
    # Create memories from last 7 days
    recent_memories = []
    for i in range(5):
        memory = Memory(
            type=MemoryType.SOLUTION,
            title=f"Recent Solution {i}",
            content=f"Solution from {i} days ago",
            importance=0.7,
            context=MemoryContext(
                project_path="/project/current"
            )
        )
        memory_id = await db.store_memory(memory)
        memory.id = memory_id

        # Manually set created_at to simulate time passage
        backend = db.backend
        created_at = (datetime.utcnow() - timedelta(days=i)).isoformat()
        backend.execute_sync(
            """
            UPDATE nodes
            SET created_at = ?, properties = json_set(properties, '$.created_at', ?)
            WHERE id = ?
            """,
            (created_at, created_at, memory_id)
        )
        backend.commit()
        recent_memories.append(memory)

    # Create older memories (30+ days ago)
    old_memories = []
    for i in range(3):
        memory = Memory(
            type=MemoryType.PROBLEM,
            title=f"Old Problem {i}",
            content=f"Problem from {30 + i} days ago",
            importance=0.5,
            context=MemoryContext(
                project_path="/project/old"
            )
        )
        memory_id = await db.store_memory(memory)
        memory.id = memory_id

        # Set older created_at
        backend = db.backend
        created_at = (datetime.utcnow() - timedelta(days=30 + i)).isoformat()
        backend.execute_sync(
            """
            UPDATE nodes
            SET created_at = ?, properties = json_set(properties, '$.created_at', ?)
            WHERE id = ?
            """,
            (created_at, created_at, memory_id)
        )
        backend.commit()
        old_memories.append(memory)

    # Create unresolved problems (no SOLVES relationship)
    unresolved = Memory(
        type=MemoryType.PROBLEM,
        title="Unresolved Issue",
        content="This problem has no solution yet",
        importance=0.9,
        context=MemoryContext(
            project_path="/project/current"
        )
    )
    unresolved_id = await db.store_memory(unresolved)
    unresolved.id = unresolved_id

    # Create a resolved problem (has SOLVES relationship)
    resolved = Memory(
        type=MemoryType.PROBLEM,
        title="Resolved Issue",
        content="This problem has a solution",
        importance=0.8,
        context=MemoryContext(
            project_path="/project/current"
        )
    )
    resolved_id = await db.store_memory(resolved)
    resolved.id = resolved_id

    # Link solution to problem
    await db.create_relationship(
        from_memory_id=recent_memories[0].id,
        to_memory_id=resolved_id,
        relationship_type=RelationshipType.SOLVES,
        properties=RelationshipProperties(strength=0.9)
    )

    return {
        "db": db,
        "recent_memories": recent_memories,
        "old_memories": old_memories,
        "unresolved": unresolved,
        "resolved": resolved
    }


@pytest.mark.asyncio
async def test_get_recent_activity_returns_last_7_days(populated_db):
    """Test that get_recent_activity returns memories from last 7 days by default."""
    db = populated_db["db"]

    result = await db.get_recent_activity(days=7)

    # Should return 5 recent solutions + 2 problems (resolved + unresolved)
    assert result["total_count"] >= 6
    assert result["days"] == 7


@pytest.mark.asyncio
async def test_get_recent_activity_counts_by_type(populated_db):
    """Test that get_recent_activity counts memories by type."""
    db = populated_db["db"]

    result = await db.get_recent_activity(days=7)

    assert "memories_by_type" in result
    assert "solution" in result["memories_by_type"]
    assert "problem" in result["memories_by_type"]
    assert result["memories_by_type"]["solution"] >= 5
    assert result["memories_by_type"]["problem"] >= 2


@pytest.mark.asyncio
async def test_get_recent_activity_returns_recent_memories(populated_db):
    """Test that get_recent_activity returns list of recent memories."""
    db = populated_db["db"]

    result = await db.get_recent_activity(days=7)

    assert "recent_memories" in result
    assert len(result["recent_memories"]) >= 5

    # Check that memories are Memory objects
    for memory in result["recent_memories"]:
        assert isinstance(memory, Memory)
        assert hasattr(memory, "title")
        assert hasattr(memory, "type")


@pytest.mark.asyncio
async def test_get_recent_activity_finds_unresolved_problems(populated_db):
    """Test that get_recent_activity identifies unresolved problems."""
    db = populated_db["db"]

    result = await db.get_recent_activity(days=30)  # Include all recent memories

    assert "unresolved_problems" in result
    assert len(result["unresolved_problems"]) >= 1

    # Check that unresolved problem is in the list
    unresolved_titles = [m.title for m in result["unresolved_problems"]]
    assert "Unresolved Issue" in unresolved_titles

    # Check that resolved problem is NOT in the list
    assert "Resolved Issue" not in unresolved_titles


@pytest.mark.asyncio
async def test_get_recent_activity_filters_by_project(populated_db):
    """Test that get_recent_activity filters by project path."""
    db = populated_db["db"]

    result = await db.get_recent_activity(days=30, project="/project/current")

    # Should only include memories from /project/current
    for memory in result["recent_memories"]:
        if memory.context and memory.context.project_path:
            assert memory.context.project_path == "/project/current"

    # Should have fewer memories than without filter
    result_all = await db.get_recent_activity(days=30)
    assert result["total_count"] <= result_all["total_count"]


@pytest.mark.asyncio
async def test_get_recent_activity_with_custom_days(populated_db):
    """Test that get_recent_activity respects custom days parameter."""
    db = populated_db["db"]

    result_7 = await db.get_recent_activity(days=7)
    result_30 = await db.get_recent_activity(days=30)

    # 30 days should include more memories than 7 days
    assert result_30["total_count"] >= result_7["total_count"]


@pytest.mark.asyncio
async def test_get_recent_activity_handles_empty_database(db):
    """Test that get_recent_activity handles empty database gracefully."""
    result = await db.get_recent_activity(days=7)

    assert result["total_count"] == 0
    assert result["memories_by_type"] == {}
    assert result["recent_memories"] == []
    assert result["unresolved_problems"] == []


@pytest.mark.asyncio
async def test_get_recent_activity_limits_recent_memories(populated_db):
    """Test that get_recent_activity limits the number of returned memories."""
    db = populated_db["db"]

    result = await db.get_recent_activity(days=30)

    # Should limit to a reasonable number (e.g., 10-20)
    assert len(result["recent_memories"]) <= 20


@pytest.mark.asyncio
async def test_detect_project_from_cwd():
    """Test project detection from current working directory."""
    from memorygraph.utils.project_detection import detect_project_context
    import os

    # Save original cwd
    original_cwd = os.getcwd()

    try:
        # Test with a path that looks like a project
        test_path = "/Users/test/projects/my-awesome-app"
        result = detect_project_context(cwd=test_path)

        assert result is not None
        assert "project_name" in result
        assert result["project_name"] == "my-awesome-app"
        assert "project_path" in result
        assert result["project_path"] == test_path
    finally:
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_detect_project_from_git_repo(tmp_path):
    """Test project detection from git repository."""
    from memorygraph.utils.project_detection import detect_project_context
    import subprocess
    import os

    # Create a temporary git repo
    test_repo = tmp_path / "test-repo"
    test_repo.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=str(test_repo), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(test_repo),
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(test_repo),
        capture_output=True
    )

    # Create a test file and commit
    (test_repo / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=str(test_repo), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(test_repo),
        capture_output=True
    )

    # Test detection
    result = detect_project_context(cwd=str(test_repo))

    assert result is not None
    assert result["project_name"] == "test-repo"
    assert result["project_path"] == str(test_repo)
    assert result["is_git_repo"] is True


@pytest.mark.asyncio
async def test_time_based_search_filter(db):
    """Test that search_memories supports time-based filtering."""
    # Create memories with different timestamps
    old_memory = Memory(
        type=MemoryType.SOLUTION,
        title="Old Solution",
        content="From 30 days ago",
        importance=0.7
    )
    old_id = await db.store_memory(old_memory)

    # Set old timestamp
    backend = db.backend
    created_at = (datetime.utcnow() - timedelta(days=30)).isoformat()
    backend.execute_sync(
        """
        UPDATE nodes
        SET created_at = ?, properties = json_set(properties, '$.created_at', ?)
        WHERE id = ?
        """,
        (created_at, created_at, old_id)
    )
    backend.commit()

    recent_memory = Memory(
        type=MemoryType.SOLUTION,
        title="Recent Solution",
        content="From today",
        importance=0.7
    )
    recent_id = await db.store_memory(recent_memory)

    # Search with time filter (last 7 days)
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    query = SearchQuery(
        query="Solution",
        created_after=cutoff_date,
        limit=10
    )

    results = await db.search_memories(query)

    # Should only return recent memory
    assert len(results) == 1
    assert results[0].title == "Recent Solution"


@pytest.mark.asyncio
async def test_time_based_search_before_filter(db):
    """Test that search_memories supports created_before filtering."""
    # Create memories with different timestamps
    old_memory = Memory(
        type=MemoryType.SOLUTION,
        title="Old Solution",
        content="From 30 days ago",
        importance=0.7
    )
    old_id = await db.store_memory(old_memory)

    # Set old timestamp
    backend = db.backend
    created_at = (datetime.utcnow() - timedelta(days=30)).isoformat()
    backend.execute_sync(
        """
        UPDATE nodes
        SET created_at = ?, properties = json_set(properties, '$.created_at', ?)
        WHERE id = ?
        """,
        (created_at, created_at, old_id)
    )
    backend.commit()

    recent_memory = Memory(
        type=MemoryType.SOLUTION,
        title="Recent Solution",
        content="From today",
        importance=0.7
    )
    recent_id = await db.store_memory(recent_memory)

    # Search with before filter (only old memories)
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    query = SearchQuery(
        query="Solution",
        created_before=cutoff_date,
        limit=10
    )

    results = await db.search_memories(query)

    # Should only return old memory
    assert len(results) == 1
    assert results[0].title == "Old Solution"
