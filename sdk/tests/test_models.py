"""Tests for MemoryGraph SDK models."""
import pytest
from datetime import datetime

from memorygraphsdk.models import (
    Memory,
    MemoryCreate,
    MemoryType,
    Relationship,
    RelationshipType,
)


class TestMemoryType:
    """Tests for MemoryType enum."""

    def test_memory_types(self):
        """Test all memory types are defined."""
        assert MemoryType.SOLUTION == "solution"
        assert MemoryType.PROBLEM == "problem"
        assert MemoryType.ERROR == "error"
        assert MemoryType.FIX == "fix"
        assert MemoryType.CODE_PATTERN == "code_pattern"

    def test_memory_type_string_value(self):
        """Test memory type can be used as string."""
        assert MemoryType.SOLUTION.value == "solution"


class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_relationship_types(self):
        """Test relationship types are defined."""
        assert RelationshipType.SOLVES == "SOLVES"
        assert RelationshipType.CAUSES == "CAUSES"
        assert RelationshipType.TRIGGERS == "TRIGGERS"
        assert RelationshipType.RELATED_TO == "RELATED_TO"


class TestMemory:
    """Tests for Memory model."""

    def test_memory_creation(self):
        """Test creating a Memory instance."""
        memory = Memory(
            id="mem_123",
            type="solution",
            title="Test Memory",
            content="Test content",
            tags=["test"],
            importance=0.8,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert memory.id == "mem_123"
        assert memory.type == "solution"
        assert memory.title == "Test Memory"
        assert memory.tags == ["test"]
        assert memory.importance == 0.8

    def test_memory_default_values(self):
        """Test Memory default values."""
        memory = Memory(
            id="mem_123",
            type="general",
            title="Test",
            content="Content",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert memory.tags == []
        assert memory.importance == 0.5
        assert memory.context is None
        assert memory.summary is None

    def test_memory_importance_validation(self):
        """Test importance is validated to 0.0-1.0 range."""
        with pytest.raises(ValueError):
            Memory(
                id="mem_123",
                type="general",
                title="Test",
                content="Content",
                importance=1.5,  # Invalid
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )


class TestMemoryCreate:
    """Tests for MemoryCreate model."""

    def test_memory_create(self):
        """Test MemoryCreate model."""
        create = MemoryCreate(
            type="solution",
            title="New Memory",
            content="Content",
            tags=["test"],
            importance=0.7,
        )

        assert create.type == "solution"
        assert create.title == "New Memory"
        assert create.importance == 0.7


class TestRelationship:
    """Tests for Relationship model."""

    def test_relationship_creation(self):
        """Test creating a Relationship instance."""
        rel = Relationship(
            id="rel_123",
            from_memory_id="mem_1",
            to_memory_id="mem_2",
            relationship_type="SOLVES",
            strength=0.8,
            confidence=0.9,
            created_at=datetime.now(),
        )

        assert rel.id == "rel_123"
        assert rel.from_memory_id == "mem_1"
        assert rel.to_memory_id == "mem_2"
        assert rel.relationship_type == "SOLVES"
        assert rel.strength == 0.8
        assert rel.confidence == 0.9

    def test_relationship_default_values(self):
        """Test Relationship default values."""
        rel = Relationship(
            id="rel_123",
            from_memory_id="mem_1",
            to_memory_id="mem_2",
            relationship_type="RELATED_TO",
            created_at=datetime.now(),
        )

        assert rel.strength == 0.5
        assert rel.confidence == 0.8
        assert rel.context is None
