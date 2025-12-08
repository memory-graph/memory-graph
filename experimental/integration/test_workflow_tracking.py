"""Tests for workflow tracking functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from memorygraph.integration.workflow_tracking import (
    WorkflowAction,
    WorkflowSuggestion,
    Recommendation,
    SessionState,
    track_workflow,
    suggest_workflow,
    optimize_workflow,
    get_session_state,
)


class TestWorkflowAction:
    """Test WorkflowAction model."""

    def test_workflow_action_creation(self):
        """Test creating a WorkflowAction."""
        action = WorkflowAction(
            session_id="session-123",
            action_type="command",
            action_data={"command": "npm test", "exit_code": 0},
            success=True,
            duration_seconds=12.5,
        )

        assert action.session_id == "session-123"
        assert action.action_type == "command"
        assert action.success is True
        assert action.duration_seconds == 12.5
        assert action.action_id is not None


class TestWorkflowSuggestion:
    """Test WorkflowSuggestion model."""

    def test_workflow_suggestion_creation(self):
        """Test creating a WorkflowSuggestion."""
        suggestion = WorkflowSuggestion(
            workflow_name="Test and Build",
            description="Run tests then build",
            steps=["run tests", "fix failures", "build"],
            success_rate=0.85,
            relevance_score=0.75,
        )

        assert suggestion.workflow_name == "Test and Build"
        assert len(suggestion.steps) == 3
        assert suggestion.success_rate == 0.85


class TestRecommendation:
    """Test Recommendation model."""

    def test_recommendation_creation(self):
        """Test creating a Recommendation."""
        rec = Recommendation(
            recommendation_type="performance",
            title="Slow operation detected",
            description="Command took 45 seconds",
            impact="high",
            evidence=["npm install took 45s"],
        )

        assert rec.recommendation_type == "performance"
        assert rec.impact == "high"
        assert len(rec.evidence) == 1


class TestSessionState:
    """Test SessionState model."""

    def test_session_state_creation(self):
        """Test creating a SessionState."""
        state = SessionState(
            session_id="session-123",
            start_time=datetime.now(),
            last_activity=datetime.now(),
            current_task="Add feature X",
            open_problems=["Build failing", "Tests not passing"],
            next_steps=["Fix tests", "Run build again"],
        )

        assert state.session_id == "session-123"
        assert len(state.open_problems) == 2
        assert len(state.next_steps) == 2


@pytest.mark.asyncio
class TestTrackWorkflow:
    """Test track_workflow function."""

    async def test_track_workflow_basic(self):
        """Test tracking a basic workflow action."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.execute_query = AsyncMock(return_value=[{"id": "session-123"}])
        backend.store_relationship = AsyncMock()

        memory_id = await track_workflow(
            backend,
            session_id="session-123",
            action_type="command",
            action_data={"command": "npm test"},
            success=True,
        )

        assert memory_id == "memory-123"
        backend.store_node.assert_called_once()

        call_args = backend.store_node.call_args[0]
        properties = call_args[1]
        assert properties["type"] == "workflow_action"
        assert properties["context"]["session_id"] == "session-123"
        assert properties["context"]["action_type"] == "command"

    async def test_track_workflow_with_duration(self):
        """Test tracking workflow action with duration."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.execute_query = AsyncMock(return_value=[{"id": "session-123"}])
        backend.store_relationship = AsyncMock()

        memory_id = await track_workflow(
            backend,
            session_id="session-123",
            action_type="file_edit",
            action_data={"file": "api.py", "lines_changed": 50},
            success=True,
            duration_seconds=125.7,
        )

        assert memory_id == "memory-123"
        call_args = backend.store_node.call_args[0][1]
        assert call_args["context"]["duration_seconds"] == 125.7

    async def test_track_workflow_creates_session(self):
        """Test that tracking creates session if not exists."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.execute_query = AsyncMock(return_value=[{"id": "session-new"}])
        backend.store_relationship = AsyncMock()

        await track_workflow(
            backend,
            session_id="session-new",
            action_type="search",
            action_data={"query": "API endpoint"},
        )

        # Should create or merge session entity
        assert backend.execute_query.called

    async def test_track_workflow_links_to_previous(self):
        """Test that action links to previous action."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-456")
        backend.execute_query = AsyncMock(
            side_effect=[
                [{"id": "session-123"}],  # Session query
                [{"id": "memory-123", "created_at": datetime.now()}],  # Previous action query
            ]
        )
        backend.store_relationship = AsyncMock()

        await track_workflow(
            backend,
            session_id="session-123",
            action_type="command",
            action_data={"command": "npm build"},
        )

        # Should create two relationships: to session and to previous action
        assert backend.store_relationship.call_count == 2

    async def test_track_workflow_failed_action(self):
        """Test tracking a failed action."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.execute_query = AsyncMock(return_value=[{"id": "session-123"}])
        backend.store_relationship = AsyncMock()

        memory_id = await track_workflow(
            backend,
            session_id="session-123",
            action_type="command",
            action_data={"command": "npm test", "exit_code": 1},
            success=False,
        )

        call_args = backend.store_node.call_args[0][1]
        assert call_args["context"]["success"] is False


@pytest.mark.asyncio
class TestSuggestWorkflow:
    """Test suggest_workflow function."""

    async def test_suggest_workflow_no_history(self):
        """Test suggesting workflows with no history."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        suggestions = await suggest_workflow(backend, {})

        assert suggestions == []

    async def test_suggest_workflow_from_history(self):
        """Test suggesting workflows from successful history."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            return_value=[
                {
                    "session_id": "session-1",
                    "start_time": datetime.now(),
                    "last_activity": datetime.now(),
                    "actions": [
                        {"context": {"action_type": "edit", "success": True}},
                        {"context": {"action_type": "test", "success": True}},
                        {"context": {"action_type": "commit", "success": True}},
                    ],
                },
                {
                    "session_id": "session-2",
                    "start_time": datetime.now(),
                    "last_activity": datetime.now(),
                    "actions": [
                        {"context": {"action_type": "edit", "success": True}},
                        {"context": {"action_type": "test", "success": True}},
                        {"context": {"action_type": "commit", "success": True}},
                    ],
                },
            ]
        )

        suggestions = await suggest_workflow(
            backend, {"task": "update feature"}, max_suggestions=5
        )

        # Should identify the repeated pattern
        assert len(suggestions) > 0
        # Pattern should have high success rate (both times succeeded)
        if suggestions:
            assert suggestions[0].success_rate == 1.0

    async def test_suggest_workflow_relevance_scoring(self):
        """Test that workflow suggestions are scored for relevance."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            return_value=[
                {
                    "session_id": "session-1",
                    "start_time": datetime.now(),
                    "last_activity": datetime.now(),
                    "actions": [
                        {"context": {"action_type": "test", "success": True}},
                        {"context": {"action_type": "build", "success": True}},
                        {"context": {"action_type": "deploy", "success": True}},
                    ],
                },
            ]
        )

        suggestions = await suggest_workflow(
            backend, {"task": "test new feature"}, max_suggestions=5
        )

        if suggestions:
            # Should have relevance score
            assert suggestions[0].relevance_score > 0

    async def test_suggest_workflow_minimum_actions(self):
        """Test that workflows need minimum action count."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            return_value=[
                {
                    "session_id": "session-1",
                    "start_time": datetime.now(),
                    "last_activity": datetime.now(),
                    "actions": [
                        {"context": {"action_type": "test", "success": True}},
                        # Only 2 actions - should be filtered
                        {"context": {"action_type": "commit", "success": True}},
                    ],
                }
            ]
        )

        suggestions = await suggest_workflow(backend, {}, max_suggestions=5)

        # Should filter out workflows with < 3 actions
        assert suggestions == []

    async def test_suggest_workflow_max_limit(self):
        """Test that suggestions respect max limit."""
        backend = AsyncMock()

        # Create many workflow patterns
        workflows = []
        for i in range(10):
            workflows.append(
                {
                    "session_id": f"session-{i}",
                    "start_time": datetime.now(),
                    "last_activity": datetime.now(),
                    "actions": [
                        {"context": {"action_type": f"action{i}-1", "success": True}},
                        {"context": {"action_type": f"action{i}-2", "success": True}},
                        {"context": {"action_type": f"action{i}-3", "success": True}},
                    ],
                }
            )

        backend.execute_query = AsyncMock(return_value=workflows)

        suggestions = await suggest_workflow(backend, {}, max_suggestions=3)

        # Should limit to max_suggestions
        assert len(suggestions) <= 3


@pytest.mark.asyncio
class TestOptimizeWorkflow:
    """Test optimize_workflow function."""

    async def test_optimize_workflow_no_actions(self):
        """Test optimizing workflow with no actions."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        recommendations = await optimize_workflow(backend, "session-123")

        assert recommendations == []

    async def test_optimize_workflow_slow_actions(self):
        """Test detecting slow actions."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            return_value=[
                {
                    "id": "action-1",
                    "context": {"action_type": "build", "duration_seconds": 45},
                    "created_at": datetime.now(),
                },
                {
                    "id": "action-2",
                    "context": {"action_type": "install", "duration_seconds": 120},
                    "created_at": datetime.now(),
                },
            ]
        )

        recommendations = await optimize_workflow(backend, "session-123")

        assert len(recommendations) > 0
        # Should recommend optimizing slow actions
        perf_recs = [r for r in recommendations if r.recommendation_type == "performance"]
        assert len(perf_recs) > 0

    async def test_optimize_workflow_repeated_failures(self):
        """Test detecting repeated failures."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            return_value=[
                {
                    "id": "action-1",
                    "context": {"action_type": "test", "success": False},
                    "created_at": datetime.now(),
                },
                {
                    "id": "action-2",
                    "context": {"action_type": "test", "success": False},
                    "created_at": datetime.now(),
                },
                {
                    "id": "action-3",
                    "context": {"action_type": "test", "success": False},
                    "created_at": datetime.now(),
                },
            ]
        )

        recommendations = await optimize_workflow(backend, "session-123")

        # Should identify error pattern
        error_recs = [r for r in recommendations if r.recommendation_type == "error_pattern"]
        assert len(error_recs) > 0
        assert error_recs[0].impact == "high"

    async def test_optimize_workflow_back_and_forth(self):
        """Test detecting inefficient back-and-forth patterns."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            return_value=[
                {
                    "id": "action-1",
                    "context": {"action_type": "edit", "success": True},
                    "created_at": datetime.now(),
                },
                {
                    "id": "action-2",
                    "context": {"action_type": "test", "success": True},
                    "created_at": datetime.now(),
                },
                {
                    "id": "action-3",
                    "context": {"action_type": "edit", "success": True},
                    "created_at": datetime.now(),
                },
            ]
        )

        recommendations = await optimize_workflow(backend, "session-123")

        # Should detect back-and-forth pattern
        pattern_recs = [
            r for r in recommendations if r.recommendation_type == "workflow_pattern"
        ]
        assert len(pattern_recs) > 0

    async def test_optimize_workflow_long_session(self):
        """Test detecting long sessions."""
        backend = AsyncMock()
        # Create 60 actions
        actions = [
            {
                "id": f"action-{i}",
                "context": {"action_type": "edit", "success": True},
                "created_at": datetime.now(),
            }
            for i in range(60)
        ]
        backend.execute_query = AsyncMock(return_value=actions)

        recommendations = await optimize_workflow(backend, "session-123")

        # Should recommend taking breaks
        productivity_recs = [
            r for r in recommendations if r.recommendation_type == "productivity"
        ]
        assert len(productivity_recs) > 0


@pytest.mark.asyncio
class TestGetSessionState:
    """Test get_session_state function."""

    async def test_get_session_state_not_found(self):
        """Test getting state for nonexistent session."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        state = await get_session_state(backend, "nonexistent")

        assert state is None

    async def test_get_session_state_basic(self):
        """Test getting basic session state."""
        start_time = datetime.now()
        last_activity = datetime.now()

        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            side_effect=[
                [
                    {
                        "start_time": start_time,
                        "last_activity": last_activity,
                        "current_task": "Add feature X",
                        "context": {"project": "my-app"},
                    }
                ],
                [],  # Recent actions
                [],  # Open problems
            ]
        )

        state = await get_session_state(backend, "session-123")

        assert state is not None
        assert state.session_id == "session-123"
        assert state.current_task == "Add feature X"
        assert state.start_time == start_time
        assert state.last_activity == last_activity

    async def test_get_session_state_with_open_problems(self):
        """Test getting session state with open problems."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            side_effect=[
                [
                    {
                        "start_time": datetime.now(),
                        "last_activity": datetime.now(),
                        "current_task": None,
                        "context": {},
                    }
                ],
                [],  # Recent actions
                [
                    {"problem": "TypeError: undefined"},
                    {"problem": "Module not found"},
                ],  # Open problems
            ]
        )

        state = await get_session_state(backend, "session-123")

        assert state is not None
        assert len(state.open_problems) == 2
        assert "TypeError" in state.open_problems[0]

    async def test_get_session_state_suggests_next_steps(self):
        """Test that session state suggests next steps."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            side_effect=[
                [
                    {
                        "start_time": datetime.now(),
                        "last_activity": datetime.now(),
                        "current_task": "Update API",
                        "context": {},
                    }
                ],
                [
                    {
                        "context": {
                            "action_type": "file_edit",
                            "success": True,
                            "action_data": {},
                        }
                    }
                ],  # Recent actions
                [],  # Open problems
            ]
        )

        state = await get_session_state(backend, "session-123")

        assert state is not None
        # Should suggest testing after file edit
        assert len(state.next_steps) > 0
        assert any("test" in step.lower() for step in state.next_steps)

    async def test_get_session_state_after_failed_action(self):
        """Test next steps after failed action."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(
            side_effect=[
                [
                    {
                        "start_time": datetime.now(),
                        "last_activity": datetime.now(),
                        "current_task": None,
                        "context": {},
                    }
                ],
                [
                    {
                        "context": {
                            "action_type": "command",
                            "success": False,
                            "action_data": {"command": "npm test"},
                        }
                    }
                ],
                [],
            ]
        )

        state = await get_session_state(backend, "session-123")

        assert state is not None
        # Should suggest resolving the error
        assert len(state.next_steps) > 0
        assert any("resolve" in step.lower() or "error" in step.lower() for step in state.next_steps)
