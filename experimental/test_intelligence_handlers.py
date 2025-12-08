"""Tests for intelligence MCP tool handlers.

This module tests all handlers in intelligence_tools.py with comprehensive
coverage of success cases, error cases, and edge cases.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from memorygraph.intelligence_tools import (
    handle_find_similar_solutions,
    handle_suggest_patterns,
    handle_get_memory_history,
    handle_track_entity_timeline,
    handle_get_intelligent_context,
    handle_get_project_summary,
    handle_get_session_briefing,
)
from memorygraph.intelligence.pattern_recognition import Pattern


@pytest.fixture
def mock_backend():
    """Create a mock backend."""
    return AsyncMock()


class TestFindSimilarSolutions:
    """Tests for find_similar_solutions handler."""

    @patch("memorygraph.intelligence_tools.find_similar_problems")
    async def test_find_similar_solutions_success(
        self, mock_find_similar, mock_backend
    ):
        """Test finding similar solutions successfully."""
        # Setup mock results
        mock_find_similar.return_value = [
            {
                "problem_id": "prob-1",
                "problem_title": "Database connection timeout",
                "similarity": 0.85,
                "solutions": [
                    {"title": "Increase pool size", "id": "sol-1"},
                    {"title": "Add retry logic", "id": "sol-2"},
                ],
            }
        ]

        # Execute
        result = await handle_find_similar_solutions(
            mock_backend,
            {"problem": "DB timeout issues", "threshold": 0.7, "limit": 10}
        )

        # Verify
        assert not result.isError
        assert "Found 1 similar problem" in result.content[0].text
        assert "Database connection timeout" in result.content[0].text
        assert "0.85" in result.content[0].text
        mock_find_similar.assert_called_once_with(mock_backend, "DB timeout issues", 0.7, 10)

    @patch("memorygraph.intelligence_tools.find_similar_problems")
    async def test_find_similar_solutions_no_matches(
        self, mock_find_similar, mock_backend
    ):
        """Test when no similar solutions are found."""
        mock_find_similar.return_value = []

        result = await handle_find_similar_solutions(
            mock_backend,
            {"problem": "Unknown problem"}
        )

        assert not result.isError
        assert "No similar problems found" in result.content[0].text

    @patch("memorygraph.intelligence_tools.find_similar_problems")
    async def test_find_similar_solutions_default_params(
        self, mock_find_similar, mock_backend
    ):
        """Test default threshold and limit parameters."""
        mock_find_similar.return_value = []

        await handle_find_similar_solutions(
            mock_backend,
            {"problem": "Test problem"}
        )

        # Verify defaults: threshold=0.7, limit=10
        mock_find_similar.assert_called_once_with(mock_backend, "Test problem", 0.7, 10)

    @patch("memorygraph.intelligence_tools.find_similar_problems")
    async def test_find_similar_solutions_error_handling(
        self, mock_find_similar, mock_backend
    ):
        """Test error handling."""
        mock_find_similar.side_effect = Exception("Search error")

        result = await handle_find_similar_solutions(
            mock_backend,
            {"problem": "Test"}
        )

        assert "Error" in result.content[0].text


class TestSuggestPatterns:
    """Tests for suggest_patterns_for_context handler."""

    @patch("memorygraph.intelligence_tools.suggest_patterns")
    async def test_suggest_patterns_success(
        self, mock_suggest, mock_backend
    ):
        """Test pattern suggestions successfully."""
        # Create mock pattern
        pattern = Pattern(
            id="pattern-1",
            name="Authentication Pattern",
            pattern_type="code",
            confidence=0.9,
            occurrences=5,
            entities=["jwt", "oauth", "session"],
            description="Common authentication pattern using JWT tokens",
            examples=["auth example 1"],
        )
        mock_suggest.return_value = [pattern]

        # Execute
        result = await handle_suggest_patterns(
            mock_backend,
            {"context": "need to implement login", "limit": 5}
        )

        # Verify
        assert not result.isError
        assert "Found 1 relevant pattern" in result.content[0].text
        assert "Authentication Pattern" in result.content[0].text
        assert "0.90" in result.content[0].text
        mock_suggest.assert_called_once_with(mock_backend, "need to implement login", 5)

    @patch("memorygraph.intelligence_tools.suggest_patterns")
    async def test_suggest_patterns_no_patterns(
        self, mock_suggest, mock_backend
    ):
        """Test when no patterns are found."""
        mock_suggest.return_value = []

        result = await handle_suggest_patterns(
            mock_backend,
            {"context": "random context"}
        )

        assert not result.isError
        assert "No relevant patterns found" in result.content[0].text

    @patch("memorygraph.intelligence_tools.suggest_patterns")
    async def test_suggest_patterns_default_limit(
        self, mock_suggest, mock_backend
    ):
        """Test default limit parameter."""
        mock_suggest.return_value = []

        await handle_suggest_patterns(
            mock_backend,
            {"context": "test"}
        )

        # Verify default limit=5
        mock_suggest.assert_called_once_with(mock_backend, "test", 5)

    @patch("memorygraph.intelligence_tools.suggest_patterns")
    async def test_suggest_patterns_error_handling(
        self, mock_suggest, mock_backend
    ):
        """Test error handling."""
        mock_suggest.side_effect = Exception("Pattern error")

        result = await handle_suggest_patterns(
            mock_backend,
            {"context": "test"}
        )

        assert "Error" in result.content[0].text


class TestGetMemoryHistory:
    """Tests for get_memory_history handler."""

    @patch("memorygraph.intelligence_tools.get_memory_history")
    async def test_get_memory_history_success(
        self, mock_history, mock_backend
    ):
        """Test getting memory history."""
        mock_history.return_value = [
            {
                "id": "mem-1-v1",
                "title": "Original version",
                "created_at": "2024-01-01T00:00:00",
                "version_depth": 0,
                "is_current": False,
            },
            {
                "id": "mem-1-v2",
                "title": "Updated version",
                "created_at": "2024-01-02T00:00:00",
                "version_depth": 1,
                "is_current": True,
            },
        ]

        result = await handle_get_memory_history(
            mock_backend,
            {"memory_id": "mem-1"}
        )

        assert not result.isError
        assert "Version history for memory mem-1" in result.content[0].text
        assert "Original version" in result.content[0].text
        assert "Updated version" in result.content[0].text
        assert "(CURRENT)" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_memory_history")
    async def test_get_memory_history_no_history(
        self, mock_history, mock_backend
    ):
        """Test when no history exists."""
        mock_history.return_value = []

        result = await handle_get_memory_history(
            mock_backend,
            {"memory_id": "nonexistent"}
        )

        assert not result.isError
        assert "No history found" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_memory_history")
    async def test_get_memory_history_error_handling(
        self, mock_history, mock_backend
    ):
        """Test error handling."""
        mock_history.side_effect = Exception("History error")

        result = await handle_get_memory_history(
            mock_backend,
            {"memory_id": "test"}
        )

        assert "Error" in result.content[0].text


class TestTrackEntityTimeline:
    """Tests for track_entity_timeline handler."""

    @patch("memorygraph.intelligence_tools.track_entity_changes")
    async def test_track_entity_timeline_success(
        self, mock_track, mock_backend
    ):
        """Test tracking entity timeline."""
        mock_track.return_value = [
            {
                "title": "First mention of React",
                "memory_type": "technology",
                "created_at": "2024-01-01",
                "status": "active",
                "was_new_mention": True,
            },
            {
                "title": "React migration project",
                "memory_type": "task",
                "created_at": "2024-01-05",
                "status": "completed",
                "was_new_mention": False,
            },
        ]

        result = await handle_track_entity_timeline(
            mock_backend,
            {"entity": "React"}
        )

        assert not result.isError
        assert "Timeline for entity 'React'" in result.content[0].text
        assert "2 mention(s)" in result.content[0].text
        assert "First mention of React" in result.content[0].text
        assert "[NEW]" in result.content[0].text

    @patch("memorygraph.intelligence_tools.track_entity_changes")
    async def test_track_entity_timeline_no_mentions(
        self, mock_track, mock_backend
    ):
        """Test when entity has no mentions."""
        mock_track.return_value = []

        result = await handle_track_entity_timeline(
            mock_backend,
            {"entity": "unknown"}
        )

        assert not result.isError
        assert "No timeline found" in result.content[0].text

    @patch("memorygraph.intelligence_tools.track_entity_changes")
    async def test_track_entity_timeline_error_handling(
        self, mock_track, mock_backend
    ):
        """Test error handling."""
        mock_track.side_effect = Exception("Timeline error")

        result = await handle_track_entity_timeline(
            mock_backend,
            {"entity": "test"}
        )

        assert "Error" in result.content[0].text


class TestGetIntelligentContext:
    """Tests for get_intelligent_context handler."""

    @patch("memorygraph.intelligence_tools.get_context")
    async def test_get_intelligent_context_success(
        self, mock_context, mock_backend
    ):
        """Test getting intelligent context."""
        mock_context.return_value = {
            "context": "Relevant context information here...",
            "estimated_tokens": 150,
            "total_memories": 5,
        }

        result = await handle_get_intelligent_context(
            mock_backend,
            {"query": "authentication", "max_tokens": 4000}
        )

        assert not result.isError
        assert "Context for query: 'authentication'" in result.content[0].text
        assert "Tokens: 150" in result.content[0].text
        assert "Sources: 5 memories" in result.content[0].text
        assert "Relevant context information" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_context")
    async def test_get_intelligent_context_no_context(
        self, mock_context, mock_backend
    ):
        """Test when no context is found."""
        mock_context.return_value = {
            "estimated_tokens": 0,
            "total_memories": 0,
        }

        result = await handle_get_intelligent_context(
            mock_backend,
            {"query": "unknown"}
        )

        assert not result.isError
        assert "No relevant context found" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_context")
    async def test_get_intelligent_context_with_project(
        self, mock_context, mock_backend
    ):
        """Test context retrieval with project filter."""
        mock_context.return_value = {"context": "Project context"}

        result = await handle_get_intelligent_context(
            mock_backend,
            {"query": "test", "project": "my-project"}
        )

        assert not result.isError
        mock_context.assert_called_once_with(
            mock_backend, "test", 4000, "my-project"
        )

    @patch("memorygraph.intelligence_tools.get_context")
    async def test_get_intelligent_context_error_in_result(
        self, mock_context, mock_backend
    ):
        """Test when context function returns error."""
        mock_context.return_value = {"error": "Context retrieval failed"}

        result = await handle_get_intelligent_context(
            mock_backend,
            {"query": "test"}
        )

        assert "Error: Context retrieval failed" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_context")
    async def test_get_intelligent_context_exception(
        self, mock_context, mock_backend
    ):
        """Test exception handling."""
        mock_context.side_effect = Exception("Context error")

        result = await handle_get_intelligent_context(
            mock_backend,
            {"query": "test"}
        )

        assert "Error" in result.content[0].text


class TestGetProjectSummary:
    """Tests for get_project_summary handler."""

    @patch("memorygraph.intelligence_tools.get_project_context")
    async def test_get_project_summary_success(
        self, mock_project, mock_backend
    ):
        """Test getting project summary."""
        mock_project.return_value = {
            "total_memories": 25,
            "recent_activity": [
                {"title": "Recent task", "type": "task"},
                {"title": "Recent problem", "type": "problem"},
            ],
            "decisions": [
                {"title": "Use PostgreSQL", "type": "decision"},
            ],
            "open_problems": [
                {"title": "Performance issue", "type": "problem"},
            ],
        }

        result = await handle_get_project_summary(
            mock_backend,
            {"project": "my-project"}
        )

        assert not result.isError
        assert "Project Summary: my-project" in result.content[0].text
        assert "Total Memories: 25" in result.content[0].text
        assert "Recent Activity:" in result.content[0].text
        assert "Key Decisions:" in result.content[0].text
        assert "Open Problems:" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_project_context")
    async def test_get_project_summary_empty_project(
        self, mock_project, mock_backend
    ):
        """Test summary for project with no data."""
        mock_project.return_value = {
            "total_memories": 0,
            "recent_activity": [],
            "decisions": [],
            "open_problems": [],
        }

        result = await handle_get_project_summary(
            mock_backend,
            {"project": "empty-project"}
        )

        assert not result.isError
        assert "Total Memories: 0" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_project_context")
    async def test_get_project_summary_error_in_result(
        self, mock_project, mock_backend
    ):
        """Test when project context returns error."""
        mock_project.return_value = {"error": "Project not found"}

        result = await handle_get_project_summary(
            mock_backend,
            {"project": "nonexistent"}
        )

        assert "Error: Project not found" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_project_context")
    async def test_get_project_summary_exception(
        self, mock_project, mock_backend
    ):
        """Test exception handling."""
        mock_project.side_effect = Exception("Project error")

        result = await handle_get_project_summary(
            mock_backend,
            {"project": "test"}
        )

        assert "Error" in result.content[0].text


class TestGetSessionBriefing:
    """Tests for get_session_briefing handler."""

    @patch("memorygraph.intelligence_tools.get_session_context")
    async def test_get_session_briefing_success(
        self, mock_session, mock_backend
    ):
        """Test getting session briefing."""
        mock_session.return_value = {
            "total_count": 8,
            "active_entities": ["React", "TypeScript", "PostgreSQL"],
            "recent_memories": [
                {"title": "Implement login", "type": "task"},
                {"title": "Fix bug in API", "type": "problem"},
            ],
        }

        result = await handle_get_session_briefing(
            mock_backend,
            {"hours_back": 24, "limit": 10}
        )

        assert not result.isError
        assert "Session Briefing (last 24 hours)" in result.content[0].text
        assert "Recent Memories: 8" in result.content[0].text
        assert "Active Entities:" in result.content[0].text
        assert "React" in result.content[0].text
        assert "Recent Activity:" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_session_context")
    async def test_get_session_briefing_default_params(
        self, mock_session, mock_backend
    ):
        """Test default parameters."""
        mock_session.return_value = {"total_count": 0}

        await handle_get_session_briefing(mock_backend, {})

        # Verify defaults: hours_back=24, limit=10
        mock_session.assert_called_once_with(mock_backend, 24, 10)

    @patch("memorygraph.intelligence_tools.get_session_context")
    async def test_get_session_briefing_custom_timeframe(
        self, mock_session, mock_backend
    ):
        """Test custom time window."""
        mock_session.return_value = {"total_count": 5}

        result = await handle_get_session_briefing(
            mock_backend,
            {"hours_back": 48, "limit": 20}
        )

        assert "last 48 hours" in result.content[0].text
        mock_session.assert_called_once_with(mock_backend, 48, 20)

    @patch("memorygraph.intelligence_tools.get_session_context")
    async def test_get_session_briefing_error_in_result(
        self, mock_session, mock_backend
    ):
        """Test when session context returns error."""
        mock_session.return_value = {"error": "Session error"}

        result = await handle_get_session_briefing(
            mock_backend,
            {}
        )

        assert "Error: Session error" in result.content[0].text

    @patch("memorygraph.intelligence_tools.get_session_context")
    async def test_get_session_briefing_exception(
        self, mock_session, mock_backend
    ):
        """Test exception handling."""
        mock_session.side_effect = Exception("Briefing error")

        result = await handle_get_session_briefing(
            mock_backend,
            {}
        )

        assert "Error" in result.content[0].text
