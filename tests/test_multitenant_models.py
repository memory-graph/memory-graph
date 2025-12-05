"""
Tests for multi-tenant model enhancements.

This module tests the multi-tenancy fields added to MemoryContext and Memory models
in Phase 1 of the multi-tenancy implementation (ADR 009).
"""

import pytest
from datetime import datetime
from memorygraph.models import (
    Memory, MemoryType, MemoryContext, ValidationError
)


class TestMemoryContextMultiTenancy:
    """Test multi-tenancy fields in MemoryContext model."""

    def test_context_with_tenant_id(self):
        """Test creating context with tenant_id."""
        context = MemoryContext(
            project_path="/test/project",
            tenant_id="acme-corp"
        )

        assert context.tenant_id == "acme-corp"
        assert context.project_path == "/test/project"

    def test_context_with_team_id(self):
        """Test creating context with team_id."""
        context = MemoryContext(
            tenant_id="acme-corp",
            team_id="backend-team"
        )

        assert context.tenant_id == "acme-corp"
        assert context.team_id == "backend-team"

    def test_context_visibility_default(self):
        """Test that visibility defaults to 'project'."""
        context = MemoryContext()

        assert context.visibility == "project"

    def test_context_visibility_private(self):
        """Test setting visibility to 'private'."""
        context = MemoryContext(
            visibility="private",
            user_id="user123"
        )

        assert context.visibility == "private"
        assert context.user_id == "user123"

    def test_context_visibility_team(self):
        """Test setting visibility to 'team'."""
        context = MemoryContext(
            visibility="team",
            tenant_id="acme-corp",
            team_id="frontend-team"
        )

        assert context.visibility == "team"
        assert context.team_id == "frontend-team"

    def test_context_visibility_public(self):
        """Test setting visibility to 'public'."""
        context = MemoryContext(
            visibility="public",
            tenant_id="acme-corp"
        )

        assert context.visibility == "public"

    def test_context_visibility_validation_valid(self):
        """Test that valid visibility values are accepted."""
        valid_values = ["private", "project", "team", "public"]

        for value in valid_values:
            context = MemoryContext(visibility=value)
            assert context.visibility == value

    def test_context_visibility_validation_invalid(self):
        """Test that invalid visibility values are rejected."""
        with pytest.raises(ValueError) as excinfo:
            MemoryContext(visibility="invalid")

        assert "visibility must be one of" in str(excinfo.value)
        assert "private" in str(excinfo.value)
        assert "project" in str(excinfo.value)
        assert "team" in str(excinfo.value)
        assert "public" in str(excinfo.value)

    def test_context_created_by(self):
        """Test created_by field."""
        context = MemoryContext(
            created_by="user123",
            user_id="user123"
        )

        assert context.created_by == "user123"
        assert context.user_id == "user123"

    def test_context_backward_compatibility_no_tenant_fields(self):
        """Test that context works without any tenant fields (backward compatible)."""
        # This simulates existing single-tenant deployments
        context = MemoryContext(
            project_path="/my/project",
            session_id="session123"
        )

        assert context.project_path == "/my/project"
        assert context.session_id == "session123"
        assert context.tenant_id is None
        assert context.team_id is None
        assert context.visibility == "project"  # default
        assert context.created_by is None

    def test_context_serialization_includes_new_fields(self):
        """Test that model serialization includes multi-tenancy fields."""
        context = MemoryContext(
            project_path="/test/project",
            tenant_id="acme-corp",
            team_id="backend-team",
            visibility="team",
            created_by="user123"
        )

        # Convert to dict (serialization)
        context_dict = context.model_dump()

        assert "tenant_id" in context_dict
        assert context_dict["tenant_id"] == "acme-corp"
        assert "team_id" in context_dict
        assert context_dict["team_id"] == "backend-team"
        assert "visibility" in context_dict
        assert context_dict["visibility"] == "team"
        assert "created_by" in context_dict
        assert context_dict["created_by"] == "user123"

    def test_context_deserialization_handles_missing_fields(self):
        """Test that deserialization handles missing tenant fields (backward compat)."""
        # Simulate old data without tenant fields
        old_context_data = {
            "project_path": "/old/project",
            "session_id": "old-session",
            "timestamp": datetime.now().isoformat()
        }

        context = MemoryContext(**old_context_data)

        assert context.project_path == "/old/project"
        assert context.session_id == "old-session"
        assert context.tenant_id is None
        assert context.team_id is None
        assert context.visibility == "project"  # default


class TestMemoryVersionFields:
    """Test version and concurrency control fields in Memory model."""

    def test_memory_version_default(self):
        """Test that version defaults to 1."""
        memory = Memory(
            type=MemoryType.TASK,
            title="Test Memory",
            content="Test content"
        )

        assert memory.version == 1

    def test_memory_version_explicit(self):
        """Test setting explicit version."""
        memory = Memory(
            type=MemoryType.TASK,
            title="Test Memory",
            content="Test content",
            version=5
        )

        assert memory.version == 5

    def test_memory_version_validation_positive(self):
        """Test that version must be >= 1."""
        with pytest.raises(ValueError):
            Memory(
                type=MemoryType.TASK,
                title="Test Memory",
                content="Test content",
                version=0
            )

    def test_memory_updated_by_default(self):
        """Test that updated_by defaults to None."""
        memory = Memory(
            type=MemoryType.TASK,
            title="Test Memory",
            content="Test content"
        )

        assert memory.updated_by is None

    def test_memory_updated_by_set(self):
        """Test setting updated_by."""
        memory = Memory(
            type=MemoryType.TASK,
            title="Test Memory",
            content="Test content",
            updated_by="user123"
        )

        assert memory.updated_by == "user123"

    def test_memory_version_increment_pattern(self):
        """Test pattern for incrementing version on update."""
        # Create initial memory
        memory = Memory(
            type=MemoryType.TASK,
            title="Test Memory",
            content="Original content",
            version=1
        )

        assert memory.version == 1

        # Simulate update by creating new memory with incremented version
        updated_memory = memory.model_copy(update={
            "content": "Updated content",
            "version": memory.version + 1,
            "updated_by": "user456"
        })

        assert updated_memory.version == 2
        assert updated_memory.updated_by == "user456"
        assert updated_memory.content == "Updated content"

    def test_memory_serialization_includes_version_fields(self):
        """Test that serialization includes version fields."""
        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Test Solution",
            content="Solution content",
            version=3,
            updated_by="user789"
        )

        memory_dict = memory.model_dump()

        assert "version" in memory_dict
        assert memory_dict["version"] == 3
        assert "updated_by" in memory_dict
        assert memory_dict["updated_by"] == "user789"

    def test_memory_backward_compatibility_no_version_fields(self):
        """Test that memory works without version fields (backward compatible)."""
        # Simulate old memory data without version fields
        old_memory_data = {
            "type": "task",
            "title": "Old Memory",
            "content": "Old content",
            "importance": 0.5,
            "tags": ["old"]
        }

        memory = Memory(**old_memory_data)

        # Should use defaults
        assert memory.version == 1
        assert memory.updated_by is None


class TestMemoryWithMultiTenantContext:
    """Test Memory with multi-tenant MemoryContext."""

    def test_memory_with_tenant_context(self):
        """Test creating memory with tenant context."""
        context = MemoryContext(
            project_path="/test/project",
            tenant_id="acme-corp",
            team_id="backend-team",
            visibility="team",
            created_by="user123"
        )

        memory = Memory(
            type=MemoryType.SOLUTION,
            title="Multi-tenant Solution",
            content="Solution for team",
            context=context,
            version=1,
            updated_by="user123"
        )

        assert memory.context.tenant_id == "acme-corp"
        assert memory.context.team_id == "backend-team"
        assert memory.context.visibility == "team"
        assert memory.context.created_by == "user123"
        assert memory.version == 1
        assert memory.updated_by == "user123"

    def test_memory_private_visibility(self):
        """Test memory with private visibility."""
        context = MemoryContext(
            tenant_id="acme-corp",
            visibility="private",
            created_by="user123",
            user_id="user123"
        )

        memory = Memory(
            type=MemoryType.TASK,
            title="Private Task",
            content="Personal task",
            context=context
        )

        assert memory.context.visibility == "private"
        assert memory.context.created_by == "user123"

    def test_memory_public_visibility(self):
        """Test memory with public visibility."""
        context = MemoryContext(
            tenant_id="acme-corp",
            visibility="public",
            created_by="admin"
        )

        memory = Memory(
            type=MemoryType.CODE_PATTERN,
            title="Public Pattern",
            content="Company-wide pattern",
            context=context
        )

        assert memory.context.visibility == "public"

    def test_full_multi_tenant_memory(self):
        """Test complete multi-tenant memory with all fields."""
        context = MemoryContext(
            project_path="/apps/backend",
            tenant_id="acme-corp",
            team_id="backend-team",
            visibility="team",
            created_by="alice",
            user_id="alice",
            session_id="session456",
            files_involved=["api.py", "models.py"],
            languages=["python"],
            frameworks=["fastapi"]
        )

        memory = Memory(
            type=MemoryType.SOLUTION,
            title="API Rate Limiting Solution",
            content="Implemented token bucket rate limiting",
            summary="Token bucket rate limiter",
            tags=["api", "rate-limiting", "performance"],
            context=context,
            importance=0.9,
            version=1,
            updated_by="alice"
        )

        # Verify all fields
        assert memory.title == "API Rate Limiting Solution"
        assert memory.context.tenant_id == "acme-corp"
        assert memory.context.team_id == "backend-team"
        assert memory.context.visibility == "team"
        assert memory.context.created_by == "alice"
        assert memory.version == 1
        assert memory.updated_by == "alice"
        assert memory.importance == 0.9
        assert "api" in memory.tags


class TestBackwardCompatibility:
    """Test backward compatibility with existing single-tenant deployments."""

    def test_old_memory_without_tenant_fields(self):
        """Test that old memories without tenant fields still work."""
        # Simulate memory from single-tenant deployment
        old_memory = Memory(
            type=MemoryType.PROBLEM,
            title="Legacy Problem",
            content="Problem from before multi-tenancy",
            context=MemoryContext(
                project_path="/old/project"
            )
        )

        assert old_memory.context.tenant_id is None
        assert old_memory.context.team_id is None
        assert old_memory.context.visibility == "project"
        assert old_memory.version == 1
        assert old_memory.updated_by is None

    def test_deserialization_old_data(self):
        """Test deserializing old memory data without new fields."""
        old_data = {
            "type": "solution",
            "title": "Old Solution",
            "content": "Solution content",
            "tags": ["legacy"],
            "context": {
                "project_path": "/old/project",
                "session_id": "old-session"
            },
            "importance": 0.7
        }

        memory = Memory(**old_data)

        # Should work with defaults
        assert memory.version == 1
        assert memory.updated_by is None
        assert memory.context.tenant_id is None
        assert memory.context.visibility == "project"

    def test_mixed_old_and_new_memories(self):
        """Test that old and new memories can coexist."""
        # Old memory (single-tenant)
        old_memory = Memory(
            type=MemoryType.TASK,
            title="Old Task",
            content="Before multi-tenancy",
            context=MemoryContext(project_path="/project")
        )

        # New memory (multi-tenant)
        new_memory = Memory(
            type=MemoryType.TASK,
            title="New Task",
            content="With multi-tenancy",
            context=MemoryContext(
                project_path="/project",
                tenant_id="acme-corp",
                visibility="team"
            ),
            version=1
        )

        # Both should be valid
        assert old_memory.context.tenant_id is None
        assert new_memory.context.tenant_id == "acme-corp"
        assert old_memory.version == 1
        assert new_memory.version == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
