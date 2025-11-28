"""
Tests for session briefing functionality (Phase 7).

These tests verify that session briefing generation works correctly,
providing relevant context, problems, and patterns.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from src.claude_memory.proactive.session_briefing import (
    generate_session_briefing,
    get_session_briefing_resource,
    SessionBriefing,
    RecentActivity,
    UnresolvedProblem,
    RelevantPattern,
    DeprecationWarning as DepWarn,
)
from src.claude_memory.integration.project_analysis import ProjectInfo


class TestSessionBriefingModels:
    """Test Pydantic models for session briefing."""

    def test_recent_activity_model(self):
        """Test RecentActivity model."""
        activity = RecentActivity(
            memory_id="mem_123",
            memory_type="solution",
            title="Fixed auth bug",
            timestamp=datetime.now(),
        )

        assert activity.memory_id == "mem_123"
        assert activity.memory_type == "solution"
        assert activity.title == "Fixed auth bug"

    def test_unresolved_problem_model(self):
        """Test UnresolvedProblem model."""
        problem = UnresolvedProblem(
            problem_id="prob_456",
            title="Database timeout",
            description="Connection times out after 30s",
            created_at=datetime.now(),
        )

        assert problem.problem_id == "prob_456"
        assert problem.related_memories == 0

    def test_relevant_pattern_model(self):
        """Test RelevantPattern model."""
        pattern = RelevantPattern(
            pattern_id="pat_789",
            pattern_type="authentication",
            description="JWT token validation pattern",
            effectiveness=0.85,
        )

        assert pattern.effectiveness == 0.85
        assert pattern.usage_count == 0

    def test_session_briefing_model(self):
        """Test SessionBriefing model."""
        briefing = SessionBriefing(
            project_name="my-app",
            project_path="/path/to/my-app",
            project_type="python",
        )

        assert briefing.project_name == "my-app"
        assert briefing.total_memories == 0
        assert briefing.has_active_issues is False


class TestSessionBriefingFormatting:
    """Test session briefing text formatting."""

    def test_format_minimal_verbosity(self):
        """Test formatting with minimal verbosity."""
        briefing = SessionBriefing(
            project_name="test-project",
            project_path="/test",
            project_type="python",
            total_memories=100,
        )

        # Add some activities
        for i in range(10):
            briefing.recent_activities.append(RecentActivity(
                memory_id=f"mem_{i}",
                memory_type="solution",
                title=f"Activity {i}",
                timestamp=datetime.now() - timedelta(days=i),
            ))

        text = briefing.format_as_text("minimal")

        assert "test-project" in text
        assert "Summary" in text
        # Minimal should show only 5 activities (allow header to say "Activity" too)
        assert text.count("Activity") <= 6  # 5 activities + 1 header

    def test_format_standard_verbosity(self):
        """Test formatting with standard verbosity."""
        briefing = SessionBriefing(
            project_name="test-project",
            project_path="/test",
            project_type="python",
        )

        # Add a problem
        briefing.unresolved_problems.append(UnresolvedProblem(
            problem_id="prob_1",
            title="Test Problem",
            description="This is a test problem",
            created_at=datetime.now() - timedelta(days=5),
        ))

        text = briefing.format_as_text("standard")

        assert "Active Issues" in text
        assert "Test Problem" in text

    def test_format_detailed_verbosity(self):
        """Test formatting with detailed verbosity."""
        briefing = SessionBriefing(
            project_name="test-project",
            project_path="/test",
            project_type="python",
        )

        # Add a deprecation warning
        briefing.deprecation_warnings.append(DepWarn(
            deprecated_id="old_1",
            deprecated_title="Old approach",
            reason="Security vulnerability",
            replacement_title="New approach",
        ))

        briefing.has_warnings = True

        text = briefing.format_as_text("detailed")

        assert "Deprecation Warnings" in text
        assert "Security vulnerability" in text
        assert "New approach" in text

    def test_format_with_patterns(self):
        """Test formatting with recommended patterns."""
        briefing = SessionBriefing(
            project_name="test-project",
            project_path="/test",
            project_type="python",
        )

        briefing.relevant_patterns.append(RelevantPattern(
            pattern_id="pat_1",
            pattern_type="authentication",
            description="JWT pattern",
            effectiveness=0.9,
            usage_count=15,
        ))

        text = briefing.format_as_text("standard")

        assert "Recommended Patterns" in text
        assert "authentication" in text
        assert "90%" in text  # Effectiveness percentage


@pytest.mark.asyncio
class TestGenerateSessionBriefing:
    """Test session briefing generation."""

    async def test_generate_briefing_no_project(self):
        """Test that None is returned when project cannot be detected."""
        backend = AsyncMock()

        # Mock detect_project to return None
        with patch('src.claude_memory.proactive.session_briefing.detect_project',
                   return_value=None):
            briefing = await generate_session_briefing(
                backend,
                "/nonexistent/path"
            )

            assert briefing is None

    async def test_generate_briefing_with_project(self):
        """Test briefing generation for detected project."""
        backend = AsyncMock()

        # Mock project info
        project = ProjectInfo(
            name="test-app",
            path="/test/app",
            project_type="python",
        )

        # Mock query responses
        backend.execute_query = AsyncMock(side_effect=[
            [{"total": 50}],  # Total count
            [],  # Recent activities
            [],  # Unresolved problems
            [],  # Patterns
            [],  # Deprecations
        ])

        with patch('src.claude_memory.proactive.session_briefing.detect_project',
                   return_value=project):
            briefing = await generate_session_briefing(
                backend,
                "/test/app"
            )

            assert briefing is not None
            assert briefing.project_name == "test-app"
            assert briefing.total_memories == 50

    async def test_generate_briefing_with_activities(self):
        """Test briefing includes recent activities."""
        backend = AsyncMock()

        project = ProjectInfo(
            name="test-app",
            path="/test/app",
            project_type="python",
        )

        # Mock recent activities
        backend.execute_query = AsyncMock(side_effect=[
            [{"total": 10}],
            [
                {
                    "id": "mem_1",
                    "type": "solution",
                    "title": "Fixed bug",
                    "summary": "Fixed authentication bug",
                    "created_at": datetime.now().isoformat(),
                    "tags": ["auth", "bug"],
                }
            ],
            [],  # Problems
            [],  # Patterns
            [],  # Deprecations
        ])

        with patch('src.claude_memory.proactive.session_briefing.detect_project',
                   return_value=project):
            briefing = await generate_session_briefing(
                backend,
                "/test/app",
                max_activities=10
            )

            assert len(briefing.recent_activities) == 1
            assert briefing.recent_activities[0].title == "Fixed bug"

    async def test_generate_briefing_with_unresolved_problems(self):
        """Test briefing includes unresolved problems."""
        backend = AsyncMock()

        project = ProjectInfo(
            name="test-app",
            path="/test/app",
            project_type="python",
        )

        # Mock unresolved problems
        backend.execute_query = AsyncMock(side_effect=[
            [{"total": 10}],
            [],  # Activities
            [
                {
                    "id": "prob_1",
                    "title": "Database timeout",
                    "content": "Database connection times out",
                    "created_at": datetime.now().isoformat(),
                    "tags": ["database"],
                    "related_count": 3,
                }
            ],
            [],  # Patterns
            [],  # Deprecations
        ])

        with patch('src.claude_memory.proactive.session_briefing.detect_project',
                   return_value=project):
            briefing = await generate_session_briefing(
                backend,
                "/test/app"
            )

            assert len(briefing.unresolved_problems) == 1
            assert briefing.unresolved_problems[0].title == "Database timeout"
            assert briefing.has_active_issues is True

    async def test_generate_briefing_with_patterns(self):
        """Test briefing includes relevant patterns."""
        backend = AsyncMock()

        project = ProjectInfo(
            name="test-app",
            path="/test/app",
            project_type="python",
        )

        # Mock patterns
        backend.execute_query = AsyncMock(side_effect=[
            [{"total": 10}],
            [],  # Activities
            [],  # Problems
            [
                {
                    "id": "pat_1",
                    "type": "authentication",
                    "description": "JWT validation pattern",
                    "effectiveness": 0.85,
                    "usage_count": 20,
                    "last_used": datetime.now().isoformat(),
                }
            ],
            [],  # Deprecations
        ])

        with patch('src.claude_memory.proactive.session_briefing.detect_project',
                   return_value=project):
            briefing = await generate_session_briefing(
                backend,
                "/test/app"
            )

            assert len(briefing.relevant_patterns) == 1
            assert briefing.relevant_patterns[0].effectiveness == 0.85

    async def test_generate_briefing_with_deprecations(self):
        """Test briefing includes deprecation warnings."""
        backend = AsyncMock()

        project = ProjectInfo(
            name="test-app",
            path="/test/app",
            project_type="python",
        )

        # Mock deprecations
        backend.execute_query = AsyncMock(side_effect=[
            [{"total": 10}],
            [],  # Activities
            [],  # Problems
            [],  # Patterns
            [
                {
                    "old_id": "old_1",
                    "old_title": "Old JWT library",
                    "new_id": "new_1",
                    "new_title": "New JWT library",
                    "reason": "Security vulnerability found",
                }
            ],
        ])

        with patch('src.claude_memory.proactive.session_briefing.detect_project',
                   return_value=project):
            briefing = await generate_session_briefing(
                backend,
                "/test/app"
            )

            assert len(briefing.deprecation_warnings) == 1
            assert briefing.has_warnings is True
            assert "Security vulnerability" in briefing.deprecation_warnings[0].reason


class TestSessionBriefingResource:
    """Test MCP resource generation for session briefing."""

    def test_get_session_briefing_resource(self):
        """Test resource generation with standard verbosity."""
        briefing = SessionBriefing(
            project_name="test-app",
            project_path="/test/app",
            project_type="python",
        )

        resource = get_session_briefing_resource(briefing, "standard")

        assert resource["uri"] == "memory://session/briefing/test-app"
        assert resource["name"] == "Session Briefing: test-app"
        assert resource["mimeType"] == "text/markdown"
        assert "test-app" in resource["text"]

    def test_get_session_briefing_resource_minimal(self):
        """Test resource generation with minimal verbosity."""
        briefing = SessionBriefing(
            project_name="test-app",
            project_path="/test/app",
            project_type="python",
        )

        resource = get_session_briefing_resource(briefing, "minimal")

        assert "text/markdown" in resource["mimeType"]
        # Minimal output should be shorter
        assert len(resource["text"]) > 0
