"""Tests for context capture functionality."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from memorygraph.integration.context_capture import (
    TaskContext,
    CommandExecution,
    ErrorPattern,
    capture_task_context,
    capture_command_execution,
    analyze_error_patterns,
    track_solution_effectiveness,
    _sanitize_content,
)


class TestTaskContext:
    """Test TaskContext model."""

    def test_task_context_creation(self):
        """Test creating a TaskContext."""
        task = TaskContext(
            description="Add dark mode",
            goals=["Create toggle", "Update styles"],
            files_involved=["settings.tsx", "theme.ts"],
        )

        assert task.description == "Add dark mode"
        assert len(task.goals) == 2
        assert len(task.files_involved) == 2
        assert task.task_id is not None
        assert task.success is None

    def test_task_context_defaults(self):
        """Test TaskContext with defaults."""
        task = TaskContext(description="Test task")

        assert task.goals == []
        assert task.files_involved == []
        assert task.start_time is not None
        assert task.end_time is None


class TestCommandExecution:
    """Test CommandExecution model."""

    def test_command_execution_creation(self):
        """Test creating a CommandExecution."""
        cmd = CommandExecution(
            command="npm test",
            output="All tests passed",
            success=True,
        )

        assert cmd.command == "npm test"
        assert cmd.output == "All tests passed"
        assert cmd.success is True
        assert cmd.command_id is not None

    def test_command_execution_with_error(self):
        """Test CommandExecution with error."""
        cmd = CommandExecution(
            command="npm build",
            output="",
            error="Build failed: Module not found",
            success=False,
        )

        assert cmd.success is False
        assert cmd.error is not None
        assert "Module not found" in cmd.error


class TestErrorPattern:
    """Test ErrorPattern model."""

    def test_error_pattern_creation(self):
        """Test creating an ErrorPattern."""
        pattern = ErrorPattern(
            error_type="TypeError",
            error_message="Cannot read property 'map' of undefined",
        )

        assert pattern.error_type == "TypeError"
        assert "undefined" in pattern.error_message
        assert pattern.frequency == 1
        assert pattern.solutions_tried == []

    def test_error_pattern_with_solutions(self):
        """Test ErrorPattern with solutions."""
        pattern = ErrorPattern(
            error_type="ModuleNotFoundError",
            error_message="No module named 'requests'",
            solutions_tried=["pip install requests"],
            successful_solutions=["pip install requests"],
        )

        assert len(pattern.solutions_tried) == 1
        assert len(pattern.successful_solutions) == 1


class TestSanitization:
    """Test content sanitization."""

    def test_sanitize_api_keys(self):
        """Test sanitization of API keys."""
        content = "Using API_KEY=abc123def456 for auth"
        sanitized = _sanitize_content(content)
        assert "abc123def456" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_passwords(self):
        """Test sanitization of passwords."""
        content = 'password="secretpass123" in config'
        sanitized = _sanitize_content(content)
        assert "secretpass123" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_tokens(self):
        """Test sanitization of tokens."""
        content = "Authorization: Bearer token123abc"
        sanitized = _sanitize_content(content)
        assert "token123abc" not in sanitized

    def test_sanitize_private_keys(self):
        """Test sanitization of private keys."""
        content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."
        sanitized = _sanitize_content(content)
        assert "-----BEGIN RSA PRIVATE KEY-----" not in sanitized
        assert "[REDACTED]" in sanitized

    def test_sanitize_urls_with_credentials(self):
        """Test sanitization of URLs with credentials."""
        content = "Connect to https://user:pass@database.com"
        sanitized = _sanitize_content(content)
        assert "user:pass" not in sanitized

    def test_sanitize_emails(self):
        """Test sanitization of email addresses."""
        content = "Contact user@example.com for help"
        sanitized = _sanitize_content(content)
        assert "user@example.com" not in sanitized

    def test_no_sanitization_needed(self):
        """Test content that doesn't need sanitization."""
        content = "This is a normal message without sensitive data"
        sanitized = _sanitize_content(content)
        assert sanitized == content


@pytest.mark.asyncio
class TestCaptureTaskContext:
    """Test capture_task_context function."""

    async def test_capture_task_basic(self):
        """Test capturing a basic task."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.store_relationship = AsyncMock()

        memory_id = await capture_task_context(
            backend,
            description="Add feature X",
            goals=["Design API", "Implement logic", "Write tests"],
        )

        assert memory_id == "memory-123"
        backend.store_node.assert_called_once()

        call_args = backend.store_node.call_args
        assert call_args[0][0] == "Memory"
        properties = call_args[0][1]
        assert properties["type"] == "task"
        assert "Add feature X" in properties["title"]
        assert properties["context"]["goals"] == ["Design API", "Implement logic", "Write tests"]

    async def test_capture_task_with_files(self):
        """Test capturing task with files."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[{"id": "file-123"}])

        memory_id = await capture_task_context(
            backend,
            description="Update API",
            goals=["Add endpoint"],
            files=["api/routes.py", "api/models.py"],
        )

        assert memory_id == "memory-123"
        # Should create file entities and relationships
        assert backend.execute_query.call_count == 2
        assert backend.store_relationship.call_count == 2

    async def test_capture_task_with_project(self):
        """Test capturing task with project ID."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")
        backend.store_relationship = AsyncMock()

        memory_id = await capture_task_context(
            backend,
            description="Fix bug",
            goals=["Identify cause", "Apply fix"],
            project_id="project-456",
        )

        assert memory_id == "memory-123"
        # Should link to project
        backend.store_relationship.assert_called_once()
        call_args = backend.store_relationship.call_args[0]
        assert call_args[0] == "memory-123"
        assert call_args[1] == "project-456"
        assert call_args[2] == "PART_OF"

    async def test_capture_task_sanitizes_content(self):
        """Test that task content is sanitized."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-123")

        await capture_task_context(
            backend,
            description="Add auth with API_KEY=secret123",
            goals=["Use password=admin123"],
        )

        call_args = backend.store_node.call_args[0][1]
        assert "secret123" not in call_args["content"]
        assert "admin123" not in call_args["content"]


@pytest.mark.asyncio
class TestCaptureCommandExecution:
    """Test capture_command_execution function."""

    async def test_capture_command_success(self):
        """Test capturing successful command."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-456")
        backend.store_relationship = AsyncMock()

        memory_id = await capture_command_execution(
            backend,
            command="npm test",
            output="All tests passed",
            success=True,
        )

        assert memory_id == "memory-456"
        backend.store_node.assert_called_once()

        call_args = backend.store_node.call_args[0]
        properties = call_args[1]
        assert properties["type"] == "observation"
        assert "npm test" in properties["title"]
        assert properties["context"]["success"] is True

    async def test_capture_command_failure(self):
        """Test capturing failed command."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-456")
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        memory_id = await capture_command_execution(
            backend,
            command="npm build",
            error="Module not found",
            success=False,
        )

        assert memory_id == "memory-456"
        call_args = backend.store_node.call_args[0][1]
        assert call_args["context"]["success"] is False
        assert call_args["context"]["has_error"] is True

    async def test_capture_command_with_task(self):
        """Test capturing command linked to task."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-456")
        backend.store_relationship = AsyncMock()

        memory_id = await capture_command_execution(
            backend,
            command="pytest",
            output="10 passed",
            success=True,
            task_id="task-789",
        )

        assert memory_id == "memory-456"
        backend.store_relationship.assert_called_once()
        call_args = backend.store_relationship.call_args[0]
        assert call_args[1] == "task-789"
        assert call_args[2] == "EXECUTED_IN"

    async def test_capture_command_sanitizes_output(self):
        """Test that command output is sanitized."""
        backend = AsyncMock()
        backend.store_node = AsyncMock(return_value="memory-456")
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        await capture_command_execution(
            backend,
            command="echo API_KEY=secret123",
            output="API_KEY=secret123",
            error="password=admin failed",
            success=False,
        )

        call_args = backend.store_node.call_args[0][1]
        assert "secret123" not in call_args["content"]
        assert "admin" not in call_args["content"]


@pytest.mark.asyncio
class TestAnalyzeErrorPatterns:
    """Test analyze_error_patterns function."""

    async def test_analyze_new_error(self):
        """Test analyzing a new error pattern."""
        backend = AsyncMock()
        backend.search_nodes = AsyncMock(return_value=[])
        backend.store_node = AsyncMock(return_value="pattern-123")

        pattern_ids = await analyze_error_patterns(
            backend, "TypeError: Cannot read property 'map' of undefined"
        )

        assert len(pattern_ids) == 1
        assert pattern_ids[0] == "pattern-123"

        # Should create new pattern
        backend.store_node.assert_called_once()
        call_args = backend.store_node.call_args[0][1]
        assert call_args["type"] == "error_pattern"
        assert call_args["context"]["error_type"] == "TypeError"

    async def test_analyze_existing_error(self):
        """Test analyzing an existing error pattern."""
        backend = AsyncMock()
        backend.search_nodes = AsyncMock(
            return_value=[{"id": "pattern-existing", "context": {"frequency": 1}}]
        )
        backend.execute_query = AsyncMock()
        backend.store_node = AsyncMock()

        pattern_ids = await analyze_error_patterns(backend, "TypeError: Something failed")

        assert len(pattern_ids) == 1
        assert pattern_ids[0] == "pattern-existing"

        # Should update existing pattern frequency
        backend.execute_query.assert_called_once()
        # Should not create new pattern
        backend.store_node.assert_not_called()

    async def test_analyze_error_without_type(self):
        """Test analyzing error without standard type."""
        backend = AsyncMock()
        backend.search_nodes = AsyncMock(return_value=[])
        backend.store_node = AsyncMock(return_value="pattern-123")

        pattern_ids = await analyze_error_patterns(backend, "Something went wrong")

        assert len(pattern_ids) == 1

        call_args = backend.store_node.call_args[0][1]
        assert call_args["context"]["error_type"] == "unknown"

    async def test_analyze_error_sanitizes(self):
        """Test that error analysis sanitizes content."""
        backend = AsyncMock()
        backend.search_nodes = AsyncMock(return_value=[])
        backend.store_node = AsyncMock(return_value="pattern-123")

        await analyze_error_patterns(backend, "Auth failed with API_KEY=secret123")

        call_args = backend.store_node.call_args[0][1]
        assert "secret123" not in call_args["content"]


@pytest.mark.asyncio
class TestTrackSolutionEffectiveness:
    """Test track_solution_effectiveness function."""

    async def test_track_successful_solution(self):
        """Test tracking a successful solution."""
        backend = AsyncMock()
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock()

        await track_solution_effectiveness(
            backend,
            solution_memory_id="solution-123",
            error_pattern_id="error-456",
            success=True,
            notes="Fixed by adding null check",
        )

        # Should create SOLVES relationship
        backend.store_relationship.assert_called_once()
        call_args = backend.store_relationship.call_args[0]
        assert call_args[0] == "solution-123"
        assert call_args[1] == "error-456"
        assert call_args[2] == "SOLVES"

        # Should update pattern and solution
        assert backend.execute_query.call_count == 2

    async def test_track_failed_solution(self):
        """Test tracking a failed solution attempt."""
        backend = AsyncMock()
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock()

        await track_solution_effectiveness(
            backend,
            solution_memory_id="solution-123",
            error_pattern_id="error-456",
            success=False,
        )

        # Should create ATTEMPTED_SOLUTION relationship
        call_args = backend.store_relationship.call_args[0]
        assert call_args[2] == "ATTEMPTED_SOLUTION"

        # Properties should reflect failure
        props = call_args[3]
        assert props["success"] is False
        assert props["strength"] < 1.0

    async def test_track_solution_sanitizes_notes(self):
        """Test that solution notes are sanitized."""
        backend = AsyncMock()
        backend.store_relationship = AsyncMock()
        backend.execute_query = AsyncMock()

        await track_solution_effectiveness(
            backend,
            solution_memory_id="solution-123",
            error_pattern_id="error-456",
            success=True,
            notes="Used password=admin123 to bypass",
        )

        call_args = backend.store_relationship.call_args[0][3]
        assert "admin123" not in call_args.get("notes", "")
