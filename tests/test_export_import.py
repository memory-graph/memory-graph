"""
Tests for data export/import functionality (Phase 2.F).

This module tests JSON and Markdown export/import.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from memorygraph.models import Memory, MemoryType, MemoryContext, RelationshipType, RelationshipProperties
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
    """Database with test memories and relationships."""
    # Create memories
    solution = Memory(
        type=MemoryType.SOLUTION,
        title="Redis Timeout Fix",
        content="Increase timeout to 5000ms for Redis connections",
        tags=["redis", "timeout", "fix"],
        importance=0.9,
        context=MemoryContext(
            project_path="/project/api"
        )
    )
    solution_id = await db.store_memory(solution)
    solution.id = solution_id

    problem = Memory(
        type=MemoryType.PROBLEM,
        title="Redis Connection Timeout",
        content="Redis connections timing out after 1000ms",
        tags=["redis", "timeout", "problem"],
        importance=0.8,
        context=MemoryContext(
            project_path="/project/api"
        )
    )
    problem_id = await db.store_memory(problem)
    problem.id = problem_id

    # Create relationship
    rel_id = await db.create_relationship(
        from_memory_id=solution_id,
        to_memory_id=problem_id,
        relationship_type=RelationshipType.SOLVES,
        properties=RelationshipProperties(
            strength=0.9,
            confidence=0.95,
            context="Solution verified by testing in production"
        )
    )

    return {
        "db": db,
        "solution": solution,
        "problem": problem,
        "relationship_id": rel_id
    }


@pytest.mark.asyncio
async def test_export_to_json(populated_db):
    """Test exporting memories to JSON format."""
    from memorygraph.utils.export_import import export_to_json

    db = populated_db["db"]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name

    try:
        # Export to JSON
        await export_to_json(db, output_path)

        # Verify file exists and is valid JSON
        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Verify structure
        assert "export_version" in data
        assert "export_date" in data
        assert "memories" in data
        assert "relationships" in data

        # Verify memories
        assert len(data["memories"]) == 2
        memory_titles = [m["title"] for m in data["memories"]]
        assert "Redis Timeout Fix" in memory_titles
        assert "Redis Connection Timeout" in memory_titles

        # Verify relationships
        assert len(data["relationships"]) == 1
        rel = data["relationships"][0]
        assert rel["type"] == "SOLVES"
        assert rel["properties"]["strength"] == 0.9

    finally:
        os.unlink(output_path)


@pytest.mark.asyncio
async def test_import_from_json(db):
    """Test importing memories from JSON format."""
    from memorygraph.utils.export_import import import_from_json

    # Create test JSON data
    test_data = {
        "export_version": "1.0",
        "export_date": "2025-12-01T00:00:00",
        "memories": [
            {
                "id": "test-memory-1",
                "type": "solution",
                "title": "Test Solution",
                "content": "Test content",
                "tags": ["test"],
                "importance": 0.7,
                "created_at": "2025-12-01T00:00:00",
                "updated_at": "2025-12-01T00:00:00"
            },
            {
                "id": "test-memory-2",
                "type": "problem",
                "title": "Test Problem",
                "content": "Problem content",
                "tags": ["test"],
                "importance": 0.6,
                "created_at": "2025-12-01T00:00:00",
                "updated_at": "2025-12-01T00:00:00"
            }
        ],
        "relationships": [
            {
                "from_memory_id": "test-memory-1",
                "to_memory_id": "test-memory-2",
                "type": "SOLVES",
                "properties": {
                    "strength": 0.8,
                    "confidence": 0.9
                }
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        input_path = f.name

    try:
        # Import from JSON
        result = await import_from_json(db, input_path)

        # Verify import results
        assert result["imported_memories"] == 2
        assert result["imported_relationships"] == 1

        # Verify memories exist in database
        solution = await db.get_memory("test-memory-1")
        assert solution is not None
        assert solution.title == "Test Solution"

        problem = await db.get_memory("test-memory-2")
        assert problem is not None
        assert problem.title == "Test Problem"

        # Verify relationship exists
        related = await db.get_related_memories("test-memory-1")
        assert len(related) == 1
        related_memory, relationship = related[0]
        assert related_memory.id == "test-memory-2"
        assert relationship.type == RelationshipType.SOLVES

    finally:
        os.unlink(input_path)


@pytest.mark.asyncio
async def test_export_import_round_trip(populated_db):
    """Test that export followed by import preserves all data."""
    from memorygraph.utils.export_import import export_to_json, import_from_json

    db = populated_db["db"]

    # Create a new empty database for import
    backend2 = SQLiteFallbackBackend(":memory:")
    await backend2.connect()
    await backend2.initialize_schema()
    db2 = SQLiteMemoryDatabase(backend2)
    await db2.initialize_schema()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        export_path = f.name

    try:
        # Export from first database
        await export_to_json(db, export_path)

        # Import into second database
        await import_from_json(db2, export_path)

        # Verify all memories transferred
        stats_original = await db.get_memory_statistics()
        stats_imported = await db2.get_memory_statistics()

        assert stats_original["total_memories"]["count"] == stats_imported["total_memories"]["count"]
        assert stats_original["total_relationships"]["count"] == stats_imported["total_relationships"]["count"]

        # Verify specific memory
        solution = await db2.get_memory(populated_db["solution"].id)
        assert solution is not None
        assert solution.title == "Redis Timeout Fix"
        assert solution.tags == ["redis", "timeout", "fix"]

    finally:
        await backend2.disconnect()
        os.unlink(export_path)


@pytest.mark.asyncio
async def test_export_to_markdown(populated_db):
    """Test exporting memories to Markdown files."""
    from memorygraph.utils.export_import import export_to_markdown

    db = populated_db["db"]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Export to Markdown
        await export_to_markdown(db, str(output_dir))

        # Verify files created
        md_files = list(output_dir.glob("*.md"))
        assert len(md_files) == 2  # One for each memory

        # Verify content
        for md_file in md_files:
            content = md_file.read_text()

            # Should have frontmatter
            assert content.startswith("---")

            # Should have title, content, tags
            assert "title:" in content
            assert "type:" in content
            assert "tags:" in content
            assert "importance:" in content


@pytest.mark.asyncio
async def test_import_handles_duplicates(db):
    """Test that import handles duplicate IDs gracefully."""
    from memorygraph.utils.export_import import import_from_json

    # Store a memory
    memory = Memory(
        id="duplicate-id",
        type=MemoryType.SOLUTION,
        title="Original",
        content="Original content",
        importance=0.5
    )
    await db.store_memory(memory)

    # Create test data with same ID but different content
    test_data = {
        "export_version": "1.0",
        "export_date": "2025-12-01T00:00:00",
        "memories": [
            {
                "id": "duplicate-id",
                "type": "solution",
                "title": "Updated",
                "content": "Updated content",
                "tags": [],
                "importance": 0.8,
                "created_at": "2025-12-01T00:00:00",
                "updated_at": "2025-12-01T00:00:00"
            }
        ],
        "relationships": []
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        input_path = f.name

    try:
        # Import with skip_duplicates=True
        result = await import_from_json(db, input_path, skip_duplicates=True)

        # Should skip duplicate
        assert result["skipped_memories"] == 1
        assert result["imported_memories"] == 0

        # Original should be unchanged
        retrieved = await db.get_memory("duplicate-id")
        assert retrieved.title == "Original"

    finally:
        os.unlink(input_path)


@pytest.mark.asyncio
async def test_import_handles_missing_relationships(db):
    """Test that import handles relationships to missing memories."""
    from memorygraph.utils.export_import import import_from_json

    # Create test data with relationship to non-existent memory
    test_data = {
        "export_version": "1.0",
        "export_date": "2025-12-01T00:00:00",
        "memories": [
            {
                "id": "memory-1",
                "type": "solution",
                "title": "Solution",
                "content": "Content",
                "tags": [],
                "importance": 0.7,
                "created_at": "2025-12-01T00:00:00",
                "updated_at": "2025-12-01T00:00:00"
            }
        ],
        "relationships": [
            {
                "from_memory_id": "memory-1",
                "to_memory_id": "non-existent",
                "type": "SOLVES",
                "properties": {
                    "strength": 0.8,
                    "confidence": 0.9
                }
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        input_path = f.name

    try:
        # Import should succeed but skip invalid relationship
        result = await import_from_json(db, input_path)

        assert result["imported_memories"] == 1
        assert result["skipped_relationships"] == 1
        assert result["imported_relationships"] == 0

    finally:
        os.unlink(input_path)


@pytest.mark.asyncio
async def test_markdown_export_includes_relationships(populated_db):
    """Test that Markdown export includes relationship information."""
    from memorygraph.utils.export_import import export_to_markdown

    db = populated_db["db"]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        await export_to_markdown(db, str(output_dir))

        # Find the solution file (should mention relationships)
        solution_file = None
        for md_file in output_dir.glob("*.md"):
            if "Redis Timeout Fix" in md_file.read_text():
                solution_file = md_file
                break

        assert solution_file is not None
        content = solution_file.read_text()

        # Should mention relationships
        assert "Relationships" in content or "relationships:" in content
        assert "SOLVES" in content
