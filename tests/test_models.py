"""Tests for memory models and data structures."""

import pytest
from datetime import datetime
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, Relationship, RelationshipType,
    RelationshipProperties, SearchQuery, MemoryNode
)


def test_memory_creation():
    """Test basic memory creation."""
    memory = Memory(
        type=MemoryType.TASK,
        title="Test Memory",
        content="This is a test memory content",
        tags=["test", "example"],
        importance=0.8
    )
    
    assert memory.type == MemoryType.TASK
    assert memory.title == "Test Memory"
    assert memory.content == "This is a test memory content"
    assert memory.tags == ["test", "example"]
    assert memory.importance == 0.8
    assert memory.confidence == 0.8  # default value
    assert memory.usage_count == 0
    assert isinstance(memory.created_at, datetime)


def test_memory_with_context():
    """Test memory creation with context."""
    context = MemoryContext(
        project_path="/path/to/project",
        files_involved=["file1.py", "file2.js"],
        languages=["python", "javascript"],
        frameworks=["fastapi", "react"]
    )
    
    memory = Memory(
        type=MemoryType.CODE_PATTERN,
        title="API Pattern",
        content="REST API implementation pattern",
        context=context
    )
    
    assert memory.context.project_path == "/path/to/project"
    assert memory.context.files_involved == ["file1.py", "file2.js"]
    assert memory.context.languages == ["python", "javascript"]
    assert memory.context.frameworks == ["fastapi", "react"]


def test_relationship_creation():
    """Test relationship creation."""
    props = RelationshipProperties(
        strength=0.9,
        confidence=0.85,
        context="Test relationship context"
    )
    
    relationship = Relationship(
        from_memory_id="mem1",
        to_memory_id="mem2",
        type=RelationshipType.SOLVES,
        properties=props
    )
    
    assert relationship.from_memory_id == "mem1"
    assert relationship.to_memory_id == "mem2"
    assert relationship.type == RelationshipType.SOLVES
    assert relationship.properties.strength == 0.9
    assert relationship.properties.confidence == 0.85


def test_search_query():
    """Test search query creation."""
    query = SearchQuery(
        query="test search",
        memory_types=[MemoryType.TASK, MemoryType.SOLUTION],
        tags=["important"],
        min_importance=0.5,
        limit=10
    )
    
    assert query.query == "test search"
    assert query.memory_types == [MemoryType.TASK, MemoryType.SOLUTION]
    assert query.tags == ["important"]
    assert query.min_importance == 0.5
    assert query.limit == 10


def test_memory_node_to_neo4j():
    """Test conversion of memory to Neo4j properties."""
    memory = Memory(
        type=MemoryType.SOLUTION,
        title="Test Solution",
        content="Solution content",
        tags=["bug", "fix"],
        importance=0.7,
        effectiveness=0.9
    )
    
    memory_node = MemoryNode(memory=memory)
    props = memory_node.to_neo4j_properties()
    
    assert props["type"] == "solution"
    assert props["title"] == "Test Solution"
    assert props["content"] == "Solution content"
    assert props["tags"] == ["bug", "fix"]
    assert props["importance"] == 0.7
    assert props["effectiveness"] == 0.9
    assert "created_at" in props
    assert "updated_at" in props


def test_tag_validation():
    """Test tag validation and normalization."""
    memory = Memory(
        type=MemoryType.GENERAL,
        title="Test",
        content="Content",
        tags=["  UPPERCASE  ", "lowercase", "  ", "MixedCase"]
    )
    
    # Tags should be normalized to lowercase and empty strings removed
    assert memory.tags == ["uppercase", "lowercase", "mixedcase"]


def test_memory_validation():
    """Test memory field validation."""
    # Test empty title
    with pytest.raises(ValueError):
        Memory(
            type=MemoryType.TASK,
            title="",
            content="Content"
        )
    
    # Test empty content
    with pytest.raises(ValueError):
        Memory(
            type=MemoryType.TASK,
            title="Title",
            content=""
        )
    
    # Test invalid importance range
    with pytest.raises(ValueError):
        Memory(
            type=MemoryType.TASK,
            title="Title",
            content="Content",
            importance=1.5
        )


if __name__ == "__main__":
    pytest.main([__file__])