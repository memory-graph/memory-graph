"""Tests for temporal memory functionality."""

import pytest
from datetime import datetime, timedelta
from memorygraph.intelligence.temporal import (
    TemporalMemory,
    get_memory_history,
    get_state_at,
    track_entity_changes,
)


class MockBackend:
    """Mock backend for testing temporal features."""

    def __init__(self):
        """Initialize mock backend."""
        self.queries = []
        self.test_data = {
            "history": [],
            "state_at": [],
            "entity_timeline": [],
            "create_version": [{"new_id": "new-version-123"}],  # Default successful response
            "version_diff": [],
        }

    async def execute_query(self, query: str, params: dict):
        """Mock query execution."""
        self.queries.append((query, params))

        # Route based on query pattern (order matters - most specific first)
        if "CREATE (new:Memory)" in query and "PREVIOUS" in query:
            # Create version query
            result = self.test_data.get("create_version", [{"new_id": "new-version-123"}])
            if not result:
                return []  # Will cause create_version to raise exception
            return result
        elif "v1.title as v1_title" in query:
            # Version diff query
            return self.test_data.get("version_diff", [])
        elif "WHERE older.created_at <=" in query:
            # State at timestamp query
            return self.test_data.get("state_at", [])
        elif "PREVIOUS*0.." in query and "ORDER BY depth" in query:
            # History query
            return self.test_data.get("history", [])
        elif "MENTIONS" in query and "was_mentioned_before" in query:
            # Entity timeline query
            return self.test_data.get("entity_timeline", [])
        else:
            return []


class TestTemporalMemory:
    """Test TemporalMemory class."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test temporal memory initialization."""
        backend = MockBackend()
        temporal = TemporalMemory(backend)
        assert temporal.backend == backend

    @pytest.mark.asyncio
    async def test_get_memory_history_empty(self):
        """Test getting history for memory with no versions."""
        backend = MockBackend()
        temporal = TemporalMemory(backend)

        history = await temporal.get_memory_history("memory-123")

        assert isinstance(history, list)
        assert len(history) == 0
        assert len(backend.queries) > 0

    @pytest.mark.asyncio
    async def test_get_memory_history_with_versions(self):
        """Test getting history with multiple versions."""
        backend = MockBackend()
        backend.test_data["history"] = [
            {
                "id": "v1",
                "title": "Version 1",
                "content": "Initial content",
                "type": "note",
                "tags": ["v1"],
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 1),
                "is_current": False,
                "superseded_by": "v2",
                "depth": 2,
            },
            {
                "id": "v2",
                "title": "Version 2",
                "content": "Updated content",
                "type": "note",
                "tags": ["v2"],
                "created_at": datetime(2024, 1, 2),
                "updated_at": datetime(2024, 1, 2),
                "is_current": False,
                "superseded_by": "v3",
                "depth": 1,
            },
            {
                "id": "v3",
                "title": "Version 3",
                "content": "Latest content",
                "type": "note",
                "tags": ["v3"],
                "created_at": datetime(2024, 1, 3),
                "updated_at": datetime(2024, 1, 3),
                "is_current": True,
                "superseded_by": None,
                "depth": 0,
            },
        ]

        temporal = TemporalMemory(backend)
        history = await temporal.get_memory_history("memory-123")

        assert len(history) == 3
        assert all("version_depth" in v for v in history)
        # Should include all versions
        version_ids = {v["id"] for v in history}
        assert version_ids == {"v1", "v2", "v3"}

    @pytest.mark.asyncio
    async def test_get_state_at_not_found(self):
        """Test getting state at timestamp when not found."""
        backend = MockBackend()
        temporal = TemporalMemory(backend)

        timestamp = datetime(2024, 1, 1)
        state = await temporal.get_state_at("memory-123", timestamp)

        assert state is None

    @pytest.mark.asyncio
    async def test_get_state_at_success(self):
        """Test getting state at specific timestamp."""
        backend = MockBackend()
        target_time = datetime(2024, 1, 2)
        backend.test_data["state_at"] = [
            {
                "id": "v2",
                "title": "Version 2",
                "content": "Content at that time",
                "type": "note",
                "tags": ["tag1"],
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 2),
                "is_current": False,
            }
        ]

        temporal = TemporalMemory(backend)
        state = await temporal.get_state_at("memory-123", target_time)

        assert state is not None
        assert state["id"] == "v2"
        assert state["title"] == "Version 2"
        assert "queried_at" in state
        assert state["queried_at"] == target_time

    @pytest.mark.asyncio
    async def test_track_entity_changes_empty(self):
        """Test tracking entity with no mentions."""
        backend = MockBackend()
        temporal = TemporalMemory(backend)

        timeline = await temporal.track_entity_changes("entity-123")

        assert isinstance(timeline, list)
        assert len(timeline) == 0

    @pytest.mark.asyncio
    async def test_track_entity_changes_with_timeline(self):
        """Test tracking entity with mentions over time."""
        backend = MockBackend()
        backend.test_data["entity_timeline"] = [
            {
                "memory_id": "m1",
                "title": "First mention",
                "content": "Initial mention of entity",
                "memory_type": "note",
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 1),
                "mention_confidence": 0.9,
                "was_mentioned_before": False,
                "status": "current",
            },
            {
                "memory_id": "m2",
                "title": "Second mention",
                "content": "Entity used again",
                "memory_type": "solution",
                "created_at": datetime(2024, 1, 2),
                "updated_at": datetime(2024, 1, 2),
                "mention_confidence": 0.95,
                "was_mentioned_before": True,
                "status": "current",
            },
        ]

        temporal = TemporalMemory(backend)
        timeline = await temporal.track_entity_changes("React")

        assert len(timeline) == 2
        assert all("was_new_mention" in change for change in timeline)
        # First should be new, second should not
        assert timeline[0]["was_new_mention"] == True
        assert timeline[1]["was_new_mention"] == False

    @pytest.mark.asyncio
    async def test_create_version(self):
        """Test creating a new version."""
        backend = MockBackend()
        temporal = TemporalMemory(backend)

        new_memory = {
            "title": "Updated title",
            "content": "Updated content",
            "type": "note",
        }

        new_id = await temporal.create_version("old-memory-123", new_memory)

        assert new_id == "new-version-123"
        assert len(backend.queries) > 0
        # Verify query was called
        query, params = backend.queries[0]
        assert "CREATE (new:Memory)" in query
        assert "PREVIOUS" in query

    @pytest.mark.asyncio
    async def test_get_version_diff_no_differences(self):
        """Test diff between identical versions."""
        backend = MockBackend()
        backend.test_data["version_diff"] = [
            {
                "v1_title": "Same title",
                "v2_title": "Same title",
                "v1_content": "Same content",
                "v2_content": "Same content",
                "v1_type": "note",
                "v2_type": "note",
                "v1_tags": ["tag1"],
                "v2_tags": ["tag1"],
            }
        ]

        temporal = TemporalMemory(backend)
        diff = await temporal.get_version_diff("v1", "v2")

        # No differences
        assert len(diff) == 0

    @pytest.mark.asyncio
    async def test_get_version_diff_with_changes(self):
        """Test diff between different versions."""
        backend = MockBackend()
        backend.test_data["version_diff"] = [
            {
                "v1_title": "Old title",
                "v2_title": "New title",
                "v1_content": "Old content",
                "v2_content": "New content",
                "v1_type": "note",
                "v2_type": "solution",
                "v1_tags": ["old", "tag1"],
                "v2_tags": ["new", "tag1"],
            }
        ]

        temporal = TemporalMemory(backend)
        diff = await temporal.get_version_diff("v1", "v2")

        assert "title" in diff
        assert diff["title"]["from"] == "Old title"
        assert diff["title"]["to"] == "New title"

        assert "content" in diff
        assert "type" in diff
        assert "tags" in diff

        # Check tag changes
        assert "old" in diff["tags"]["removed"]
        assert "new" in diff["tags"]["added"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_get_memory_history_function(self):
        """Test get_memory_history convenience function."""
        backend = MockBackend()
        history = await get_memory_history(backend, "memory-123")
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_state_at_function(self):
        """Test get_state_at convenience function."""
        backend = MockBackend()
        timestamp = datetime.now()
        state = await get_state_at(backend, "memory-123", timestamp)
        # Returns None when no data
        assert state is None or isinstance(state, dict)

    @pytest.mark.asyncio
    async def test_track_entity_changes_function(self):
        """Test track_entity_changes convenience function."""
        backend = MockBackend()
        timeline = await track_entity_changes(backend, "React")
        assert isinstance(timeline, list)


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_backend_error_handling(self):
        """Test handling of backend errors."""

        class ErrorBackend:
            """Backend that raises errors."""

            async def execute_query(self, query, params):
                """Raise an error."""
                raise Exception("Database error")

        backend = ErrorBackend()
        temporal = TemporalMemory(backend)

        # Should handle errors gracefully
        history = await temporal.get_memory_history("memory-123")
        assert history == []

        state = await temporal.get_state_at("memory-123", datetime.now())
        assert state is None

        timeline = await temporal.track_entity_changes("entity-123")
        assert timeline == []

    @pytest.mark.asyncio
    async def test_create_version_error(self):
        """Test create_version error handling."""

        class ErrorBackend:
            """Backend that returns no results."""

            async def execute_query(self, query, params):
                """Return empty results."""
                return []

        backend = ErrorBackend()
        temporal = TemporalMemory(backend)

        with pytest.raises(Exception):
            await temporal.create_version("old-id", {"title": "new"})

    @pytest.mark.asyncio
    async def test_version_diff_missing_memory(self):
        """Test diff when memory not found."""
        backend = MockBackend()
        backend.test_data["version_diff"] = []

        temporal = TemporalMemory(backend)
        diff = await temporal.get_version_diff("nonexistent-1", "nonexistent-2")

        assert diff == {}


class TestRealWorldScenarios:
    """Test temporal features with real-world scenarios."""

    @pytest.mark.asyncio
    async def test_documentation_evolution(self):
        """Test tracking documentation changes over time."""
        backend = MockBackend()
        backend.test_data["history"] = [
            {
                "id": "doc-v1",
                "title": "API Documentation",
                "content": "Basic API docs",
                "type": "documentation",
                "tags": ["api", "v1"],
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 1),
                "is_current": False,
                "superseded_by": "doc-v2",
                "depth": 1,
            },
            {
                "id": "doc-v2",
                "title": "API Documentation",
                "content": "Complete API docs with examples",
                "type": "documentation",
                "tags": ["api", "v2", "examples"],
                "created_at": datetime(2024, 2, 1),
                "updated_at": datetime(2024, 2, 1),
                "is_current": True,
                "superseded_by": None,
                "depth": 0,
            },
        ]

        temporal = TemporalMemory(backend)
        history = await temporal.get_memory_history("doc-current")

        # Should show evolution from basic to complete
        assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_bug_fix_timeline(self):
        """Test tracking bug fixes over time."""
        backend = MockBackend()
        backend.test_data["entity_timeline"] = [
            {
                "memory_id": "bug-report",
                "title": "Bug: Null pointer error",
                "content": "Getting null pointer in handler",
                "memory_type": "problem",
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 1),
                "mention_confidence": 0.95,
                "was_mentioned_before": False,
                "status": "superseded",
            },
            {
                "memory_id": "bug-fix",
                "title": "Fix: Add null check",
                "content": "Added null check to handler",
                "memory_type": "solution",
                "created_at": datetime(2024, 1, 2),
                "updated_at": datetime(2024, 1, 2),
                "mention_confidence": 0.9,
                "was_mentioned_before": True,
                "status": "current",
            },
        ]

        temporal = TemporalMemory(backend)
        timeline = await temporal.track_entity_changes("NullPointerException")

        # Should show progression from problem to solution
        assert len(timeline) >= 2
        assert timeline[0]["memory_type"] == "problem"
        assert timeline[1]["memory_type"] == "solution"

    @pytest.mark.asyncio
    async def test_architecture_decision_timeline(self):
        """Test tracking architecture decisions."""
        backend = MockBackend()
        backend.test_data["entity_timeline"] = [
            {
                "memory_id": "decision-1",
                "title": "Chose PostgreSQL",
                "content": "Selected PostgreSQL as database",
                "memory_type": "decision",
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 1),
                "mention_confidence": 1.0,
                "was_mentioned_before": False,
                "status": "current",
            },
            {
                "memory_id": "decision-2",
                "title": "Added Redis cache",
                "content": "Added Redis for caching layer",
                "memory_type": "decision",
                "created_at": datetime(2024, 2, 1),
                "updated_at": datetime(2024, 2, 1),
                "mention_confidence": 0.95,
                "was_mentioned_before": False,
                "status": "current",
            },
        ]

        temporal = TemporalMemory(backend)
        timeline = await temporal.track_entity_changes("database")

        # Should capture all database-related decisions
        assert isinstance(timeline, list)


class TestTemporalQueries:
    """Test specific temporal query scenarios."""

    @pytest.mark.asyncio
    async def test_find_what_changed_between_dates(self):
        """Test finding what changed in a specific time period."""
        backend = MockBackend()

        # Get state at start of period
        start_date = datetime(2024, 1, 1)
        backend.test_data["state_at"] = [
            {
                "id": "v1",
                "title": "Initial",
                "content": "Initial content",
                "type": "note",
                "tags": [],
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 1),
                "is_current": False,
            }
        ]

        temporal = TemporalMemory(backend)
        start_state = await temporal.get_state_at("memory-123", start_date)

        assert start_state is not None
        assert start_state["title"] == "Initial"

    @pytest.mark.asyncio
    async def test_version_chain_integrity(self):
        """Test that version chains maintain integrity."""
        backend = MockBackend()
        backend.test_data["history"] = [
            {
                "id": "v1",
                "title": "V1",
                "content": "c1",
                "type": "note",
                "tags": [],
                "created_at": datetime(2024, 1, 1),
                "updated_at": datetime(2024, 1, 1),
                "is_current": False,
                "superseded_by": "v2",
                "depth": 2,
            },
            {
                "id": "v2",
                "title": "V2",
                "content": "c2",
                "type": "note",
                "tags": [],
                "created_at": datetime(2024, 1, 2),
                "updated_at": datetime(2024, 1, 2),
                "is_current": False,
                "superseded_by": "v3",
                "depth": 1,
            },
            {
                "id": "v3",
                "title": "V3",
                "content": "c3",
                "type": "note",
                "tags": [],
                "created_at": datetime(2024, 1, 3),
                "updated_at": datetime(2024, 1, 3),
                "is_current": True,
                "superseded_by": None,
                "depth": 0,
            },
        ]

        temporal = TemporalMemory(backend)
        history = await temporal.get_memory_history("v3")

        # Verify chain is complete
        assert len(history) == 3

        # Verify only one is current
        current_versions = [v for v in history if v.get("is_current")]
        assert len(current_versions) == 1

        # Verify depths are sequential
        depths = [v["version_depth"] for v in history]
        assert depths == [2, 1, 0] or sorted(depths, reverse=True) == [2, 1, 0]
