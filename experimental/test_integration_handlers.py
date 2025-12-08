"""
Comprehensive tests for Integration Tool handlers.

Tests all 11 integration tools:
- capture_task
- capture_command
- track_error_solution
- detect_project
- analyze_project
- track_file_changes
- identify_patterns
- track_workflow
- suggest_workflow
- optimize_workflow
- get_session_state
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from memorygraph.integration_tools import IntegrationToolHandlers
from memorygraph.backends.factory import BackendFactory
from memorygraph.integration.context_capture import TaskContext
from memorygraph.integration.project_analysis import ProjectInfo, CodebaseInfo, FileChange, Pattern
from memorygraph.integration.workflow_tracking import WorkflowSuggestion, Recommendation, SessionState


@pytest.fixture
def backend_factory():
    """Create a mock backend factory."""
    factory = MagicMock(spec=BackendFactory)
    factory.create_backend = AsyncMock()
    return factory


@pytest.fixture
def handlers(backend_factory):
    """Create IntegrationToolHandlers instance."""
    return IntegrationToolHandlers(backend_factory)


@pytest.fixture
def mock_backend(backend_factory):
    """Create a mock backend."""
    backend = AsyncMock()
    backend_factory.create_backend.return_value = backend
    return backend


class TestCaptureTask:
    """Tests for capture_task handler."""

    @pytest.mark.asyncio
    async def test_capture_task_minimal(self, handlers, mock_backend):
        """Test capturing task with minimal required fields."""
        with patch("memorygraph.integration_tools.capture_task_context") as mock_capture:
            mock_capture.return_value = "mem_123"

            result = await handlers.handle_capture_task({
                "description": "Fix authentication bug",
                "goals": ["Fix bug", "Add tests"]
            })

            assert result is not None
            assert "mem_123" in result.content[0].text
            assert "Fix authentication bug" in result.content[0].text
            assert "Goals: 2" in result.content[0].text

            mock_capture.assert_called_once()
            args = mock_capture.call_args[0]
            assert args[1] == "Fix authentication bug"
            assert args[2] == ["Fix bug", "Add tests"]

    @pytest.mark.asyncio
    async def test_capture_task_with_files(self, handlers, mock_backend):
        """Test capturing task with files."""
        with patch("memorygraph.integration_tools.capture_task_context") as mock_capture:
            mock_capture.return_value = "mem_456"

            result = await handlers.handle_capture_task({
                "description": "Refactor database layer",
                "goals": ["Improve performance"],
                "files": ["db.py", "models.py", "migrations/001.sql"]
            })

            assert result is not None
            assert "mem_456" in result.content[0].text
            assert "Files: 3" in result.content[0].text

            args = mock_capture.call_args[0]
            assert args[3] == ["db.py", "models.py", "migrations/001.sql"]

    @pytest.mark.asyncio
    async def test_capture_task_with_project_id(self, handlers, mock_backend):
        """Test capturing task with project ID."""
        with patch("memorygraph.integration_tools.capture_task_context") as mock_capture:
            mock_capture.return_value = "mem_789"

            result = await handlers.handle_capture_task({
                "description": "Update dependencies",
                "goals": ["Security patches"],
                "project_id": "project_xyz"
            })

            assert result is not None
            args = mock_capture.call_args[0]
            assert args[4] == "project_xyz"

    @pytest.mark.asyncio
    async def test_capture_task_error(self, handlers, mock_backend):
        """Test error handling in capture_task."""
        with patch("memorygraph.integration_tools.capture_task_context") as mock_capture:
            mock_capture.side_effect = Exception("Database error")

            result = await handlers.handle_capture_task({
                "description": "Test task",
                "goals": ["Test"]
            })

            assert result is not None
            assert "Error capturing task" in result.content[0].text
            assert "Database error" in result.content[0].text


class TestCaptureCommand:
    """Tests for capture_command handler."""

    @pytest.mark.asyncio
    async def test_capture_command_success(self, handlers, mock_backend):
        """Test capturing successful command."""
        with patch("memorygraph.integration_tools.capture_command_execution") as mock_capture:
            mock_capture.return_value = "cmd_123"

            result = await handlers.handle_capture_command({
                "command": "pytest tests/",
                "output": "All tests passed",
                "success": True
            })

            assert result is not None
            assert "cmd_123" in result.content[0].text
            assert "pytest tests/" in result.content[0].text
            assert "Success: True" in result.content[0].text

    @pytest.mark.asyncio
    async def test_capture_command_failure(self, handlers, mock_backend):
        """Test capturing failed command."""
        with patch("memorygraph.integration_tools.capture_command_execution") as mock_capture:
            mock_capture.return_value = "cmd_456"

            result = await handlers.handle_capture_command({
                "command": "npm run build",
                "output": "Build output...",
                "error": "Type error in app.ts",
                "success": False
            })

            assert result is not None
            args = mock_capture.call_args[0]
            assert args[1] == "npm run build"
            assert args[3] == "Type error in app.ts"
            assert args[4] is False

    @pytest.mark.asyncio
    async def test_capture_command_with_task_id(self, handlers, mock_backend):
        """Test capturing command with associated task."""
        with patch("memorygraph.integration_tools.capture_command_execution") as mock_capture:
            mock_capture.return_value = "cmd_789"

            result = await handlers.handle_capture_command({
                "command": "git commit -m 'fix'",
                "success": True,
                "task_id": "task_123"
            })

            assert result is not None
            args = mock_capture.call_args[0]
            assert args[5] == "task_123"

    @pytest.mark.asyncio
    async def test_capture_command_error(self, handlers, mock_backend):
        """Test error handling in capture_command."""
        with patch("memorygraph.integration_tools.capture_command_execution") as mock_capture:
            mock_capture.side_effect = RuntimeError("Failed to save")

            result = await handlers.handle_capture_command({
                "command": "test",
                "success": True
            })

            assert "Error capturing command" in result.content[0].text


class TestTrackErrorSolution:
    """Tests for track_error_solution handler."""

    @pytest.mark.asyncio
    async def test_track_successful_solution(self, handlers, mock_backend):
        """Test tracking successful solution."""
        with patch("memorygraph.integration_tools.track_solution_effectiveness") as mock_track:
            result = await handlers.handle_track_error_solution({
                "solution_memory_id": "sol_123",
                "error_pattern_id": "err_456",
                "success": True
            })

            assert result is not None
            assert "sol_123" in result.content[0].text
            assert "err_456" in result.content[0].text
            assert "Success: True" in result.content[0].text

            mock_track.assert_called_once()
            args = mock_track.call_args[0]
            assert args[1] == "sol_123"
            assert args[2] == "err_456"
            assert args[3] is True
            assert args[4] is None

    @pytest.mark.asyncio
    async def test_track_failed_solution(self, handlers, mock_backend):
        """Test tracking failed solution."""
        with patch("memorygraph.integration_tools.track_solution_effectiveness") as mock_track:
            result = await handlers.handle_track_error_solution({
                "solution_memory_id": "sol_789",
                "error_pattern_id": "err_101",
                "success": False,
                "notes": "Solution didn't work in production environment"
            })

            assert result is not None
            args = mock_track.call_args[0]
            assert args[3] is False
            assert args[4] == "Solution didn't work in production environment"

    @pytest.mark.asyncio
    async def test_track_error_solution_error(self, handlers, mock_backend):
        """Test error handling in track_error_solution."""
        with patch("memorygraph.integration_tools.track_solution_effectiveness") as mock_track:
            mock_track.side_effect = ValueError("Invalid memory ID")

            result = await handlers.handle_track_error_solution({
                "solution_memory_id": "invalid",
                "error_pattern_id": "err_123",
                "success": True
            })

            assert "Error tracking solution" in result.content[0].text


class TestDetectProject:
    """Tests for detect_project handler."""

    @pytest.mark.asyncio
    async def test_detect_python_project(self, handlers, mock_backend):
        """Test detecting Python project."""
        mock_project = ProjectInfo(
            name="MyProject",
            project_type="python",
            path="/path/to/project",
            technologies=["pytest", "flask"],
            git_remote="github.com/user/project",
            project_id="proj_123"
        )

        with patch("memorygraph.integration_tools.detect_project") as mock_detect:
            mock_detect.return_value = mock_project

            result = await handlers.handle_detect_project({
                "directory": "/path/to/project"
            })

            assert result is not None
            assert "MyProject" in result.content[0].text
            assert "python" in result.content[0].text
            assert "pytest, flask" in result.content[0].text
            assert "github.com/user/project" in result.content[0].text
            assert "proj_123" in result.content[0].text

    @pytest.mark.asyncio
    async def test_detect_no_project(self, handlers, mock_backend):
        """Test when no project is detected."""
        with patch("memorygraph.integration_tools.detect_project") as mock_detect:
            mock_detect.return_value = None

            result = await handlers.handle_detect_project({
                "directory": "/tmp/empty"
            })

            assert result is not None
            assert "No project detected" in result.content[0].text

    @pytest.mark.asyncio
    async def test_detect_project_error(self, handlers, mock_backend):
        """Test error handling in detect_project."""
        with patch("memorygraph.integration_tools.detect_project") as mock_detect:
            mock_detect.side_effect = OSError("Permission denied")

            result = await handlers.handle_detect_project({
                "directory": "/restricted"
            })

            assert "Error detecting project" in result.content[0].text


class TestAnalyzeProject:
    """Tests for analyze_project handler."""

    @pytest.mark.asyncio
    async def test_analyze_codebase(self, handlers, mock_backend):
        """Test analyzing project codebase."""
        mock_info = CodebaseInfo(
            total_files=150,
            languages=["Python", "JavaScript"],
            frameworks=["FastAPI", "React"],
            file_types={".py": 80, ".js": 50, ".json": 20}
        )

        with patch("memorygraph.integration_tools.analyze_codebase") as mock_analyze:
            mock_analyze.return_value = mock_info

            result = await handlers.handle_analyze_project({
                "directory": "/path/to/project"
            })

            assert result is not None
            assert "Total Files: 150" in result.content[0].text
            assert "Python, JavaScript" in result.content[0].text
            assert "FastAPI, React" in result.content[0].text
            assert ".py: 80" in result.content[0].text

    @pytest.mark.asyncio
    async def test_analyze_no_frameworks(self, handlers, mock_backend):
        """Test analyzing project without frameworks."""
        mock_info = CodebaseInfo(
            total_files=10,
            languages=["Rust"],
            frameworks=[],
            file_types={".rs": 10}
        )

        with patch("memorygraph.integration_tools.analyze_codebase") as mock_analyze:
            mock_analyze.return_value = mock_info

            result = await handlers.handle_analyze_project({
                "directory": "/path/to/rust-project"
            })

            assert "None detected" in result.content[0].text

    @pytest.mark.asyncio
    async def test_analyze_project_error(self, handlers, mock_backend):
        """Test error handling in analyze_project."""
        with patch("memorygraph.integration_tools.analyze_codebase") as mock_analyze:
            mock_analyze.side_effect = FileNotFoundError("Directory not found")

            result = await handlers.handle_analyze_project({
                "directory": "/nonexistent"
            })

            assert "Error analyzing project" in result.content[0].text


class TestTrackFileChanges:
    """Tests for track_file_changes handler."""

    @pytest.mark.asyncio
    async def test_track_file_changes_success(self, handlers, mock_backend):
        """Test tracking file changes."""
        mock_changes = [
            FileChange(
                file_path="src/main.py",
                change_type="modified",
                lines_added=10,
                lines_removed=5
            ),
            FileChange(
                file_path="tests/test_main.py",
                change_type="added",
                lines_added=20,
                lines_removed=0
            )
        ]

        with patch("memorygraph.integration_tools.track_file_changes") as mock_track:
            mock_track.return_value = mock_changes

            result = await handlers.handle_track_file_changes({
                "repo_path": "/path/to/repo",
                "project_id": "proj_123"
            })

            assert result is not None
            assert "2 files" in result.content[0].text
            assert "modified: src/main.py (+10/-5)" in result.content[0].text
            assert "added: tests/test_main.py (+20/-0)" in result.content[0].text

    @pytest.mark.asyncio
    async def test_track_no_changes(self, handlers, mock_backend):
        """Test when no file changes detected."""
        with patch("memorygraph.integration_tools.track_file_changes") as mock_track:
            mock_track.return_value = []

            result = await handlers.handle_track_file_changes({
                "repo_path": "/path/to/repo",
                "project_id": "proj_123"
            })

            assert "No file changes detected" in result.content[0].text

    @pytest.mark.asyncio
    async def test_track_file_changes_error(self, handlers, mock_backend):
        """Test error handling in track_file_changes."""
        with patch("memorygraph.integration_tools.track_file_changes") as mock_track:
            mock_track.side_effect = RuntimeError("Git error")

            result = await handlers.handle_track_file_changes({
                "repo_path": "/invalid",
                "project_id": "proj_123"
            })

            assert "Error tracking file changes" in result.content[0].text


class TestIdentifyPatterns:
    """Tests for identify_patterns handler."""

    @pytest.mark.asyncio
    async def test_identify_code_patterns(self, handlers, mock_backend):
        """Test identifying code patterns."""
        mock_patterns = [
            Pattern(
                pattern_type="decorator",
                description="Decorator pattern",
                frequency=15,
                confidence=0.95
            ),
            Pattern(
                pattern_type="async_await",
                description="Async/await pattern",
                frequency=8,
                confidence=0.87
            )
        ]

        with patch("memorygraph.integration_tools.identify_code_patterns") as mock_identify:
            mock_identify.return_value = mock_patterns

            result = await handlers.handle_identify_patterns({
                "project_id": "proj_123",
                "files": ["src/main.py", "src/utils.py"]
            })

            assert result is not None
            assert "2 patterns" in result.content[0].text
            assert "decorator: 15 occurrences (confidence: 0.95)" in result.content[0].text
            assert "async_await: 8 occurrences (confidence: 0.87)" in result.content[0].text

    @pytest.mark.asyncio
    async def test_identify_no_patterns(self, handlers, mock_backend):
        """Test when no patterns found."""
        with patch("memorygraph.integration_tools.identify_code_patterns") as mock_identify:
            mock_identify.return_value = []

            result = await handlers.handle_identify_patterns({
                "project_id": "proj_123",
                "files": ["empty.py"]
            })

            assert "No significant patterns found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_identify_patterns_error(self, handlers, mock_backend):
        """Test error handling in identify_patterns."""
        with patch("memorygraph.integration_tools.identify_code_patterns") as mock_identify:
            mock_identify.side_effect = ValueError("Invalid file")

            result = await handlers.handle_identify_patterns({
                "project_id": "proj_123",
                "files": ["invalid.txt"]
            })

            assert "Error identifying patterns" in result.content[0].text


class TestTrackWorkflow:
    """Tests for track_workflow handler."""

    @pytest.mark.asyncio
    async def test_track_workflow_minimal(self, handlers, mock_backend):
        """Test tracking workflow with minimal fields."""
        with patch("memorygraph.integration_tools.track_workflow") as mock_track:
            mock_track.return_value = "wf_123"

            result = await handlers.handle_track_workflow({
                "session_id": "sess_456",
                "action_type": "file_edit"
            })

            assert result is not None
            assert "wf_123" in result.content[0].text
            assert "file_edit" in result.content[0].text
            assert "Success: True" in result.content[0].text

    @pytest.mark.asyncio
    async def test_track_workflow_full(self, handlers, mock_backend):
        """Test tracking workflow with all fields."""
        with patch("memorygraph.integration_tools.track_workflow") as mock_track:
            mock_track.return_value = "wf_789"

            result = await handlers.handle_track_workflow({
                "session_id": "sess_101",
                "action_type": "command",
                "action_data": {"cmd": "pytest", "args": ["tests/"]},
                "success": False,
                "duration_seconds": 5.2
            })

            assert result is not None
            args = mock_track.call_args[0]
            assert args[1] == "sess_101"
            assert args[2] == "command"
            assert args[3] == {"cmd": "pytest", "args": ["tests/"]}
            assert args[4] is False
            assert args[5] == 5.2

    @pytest.mark.asyncio
    async def test_track_workflow_error(self, handlers, mock_backend):
        """Test error handling in track_workflow."""
        with patch("memorygraph.integration_tools.track_workflow") as mock_track:
            mock_track.side_effect = Exception("Tracking error")

            result = await handlers.handle_track_workflow({
                "session_id": "sess_123",
                "action_type": "search"
            })

            assert "Error tracking workflow" in result.content[0].text


class TestSuggestWorkflow:
    """Tests for suggest_workflow handler."""

    @pytest.mark.asyncio
    async def test_suggest_workflow_with_results(self, handlers, mock_backend):
        """Test workflow suggestions with results."""
        mock_suggestions = [
            WorkflowSuggestion(
                workflow_name="TDD Workflow",
                description="Test-driven development pattern",
                success_rate=0.92,
                relevance_score=0.88,
                steps=["Write test", "Run test (fail)", "Implement", "Run test (pass)", "Refactor"]
            ),
            WorkflowSuggestion(
                workflow_name="Debug Flow",
                description="Debugging pattern",
                success_rate=0.85,
                relevance_score=0.75,
                steps=["Reproduce", "Log", "Hypothesis", "Test", "Fix"]
            )
        ]

        with patch("memorygraph.integration_tools.suggest_workflow") as mock_suggest:
            mock_suggest.return_value = mock_suggestions

            result = await handlers.handle_suggest_workflow({
                "context": {"task": "bug fix", "language": "python"}
            })

            assert result is not None
            assert "2)" in result.content[0].text  # Two suggestions
            assert "TDD Workflow" in result.content[0].text
            assert "92%" in result.content[0].text
            assert "Write test -> Run test (fail) -> Implement -> Run test (pass) -> Refactor" in result.content[0].text

    @pytest.mark.asyncio
    async def test_suggest_workflow_no_history(self, handlers, mock_backend):
        """Test workflow suggestions with no history."""
        with patch("memorygraph.integration_tools.suggest_workflow") as mock_suggest:
            mock_suggest.return_value = []

            result = await handlers.handle_suggest_workflow({
                "context": {"task": "new task"}
            })

            assert "No workflow suggestions available" in result.content[0].text
            assert "Build more workflow history" in result.content[0].text

    @pytest.mark.asyncio
    async def test_suggest_workflow_with_max(self, handlers, mock_backend):
        """Test workflow suggestions with max limit."""
        with patch("memorygraph.integration_tools.suggest_workflow") as mock_suggest:
            mock_suggest.return_value = []

            result = await handlers.handle_suggest_workflow({
                "context": {"task": "test"},
                "max_suggestions": 3
            })

            args = mock_suggest.call_args[0]
            assert args[2] == 3

    @pytest.mark.asyncio
    async def test_suggest_workflow_error(self, handlers, mock_backend):
        """Test error handling in suggest_workflow."""
        with patch("memorygraph.integration_tools.suggest_workflow") as mock_suggest:
            mock_suggest.side_effect = RuntimeError("Analysis error")

            result = await handlers.handle_suggest_workflow({
                "context": {}
            })

            assert "Error suggesting workflow" in result.content[0].text


class TestOptimizeWorkflow:
    """Tests for optimize_workflow handler."""

    @pytest.mark.asyncio
    async def test_optimize_workflow_with_recommendations(self, handlers, mock_backend):
        """Test workflow optimization with recommendations."""
        mock_recommendations = [
            Recommendation(
                recommendation_type="optimization",
                title="Reduce redundant searches",
                description="Consider caching search results",
                impact="high",
                evidence=["Searched same term 5 times", "1.2s wasted", "Pattern detected"]
            ),
            Recommendation(
                recommendation_type="efficiency",
                title="Batch file edits",
                description="Group related edits together",
                impact="medium",
                evidence=["7 separate edits", "Could be 2 operations"]
            )
        ]

        with patch("memorygraph.integration_tools.optimize_workflow") as mock_optimize:
            mock_optimize.return_value = mock_recommendations

            result = await handlers.handle_optimize_workflow({
                "session_id": "sess_123"
            })

            assert result is not None
            assert "2)" in result.content[0].text  # Two recommendations
            assert "Reduce redundant searches (high impact)" in result.content[0].text
            assert "Consider caching search results" in result.content[0].text
            assert "Searched same term 5 times, 1.2s wasted, Pattern detected" in result.content[0].text

    @pytest.mark.asyncio
    async def test_optimize_workflow_no_recommendations(self, handlers, mock_backend):
        """Test when workflow is already optimal."""
        with patch("memorygraph.integration_tools.optimize_workflow") as mock_optimize:
            mock_optimize.return_value = []

            result = await handlers.handle_optimize_workflow({
                "session_id": "sess_456"
            })

            assert "No optimization recommendations found" in result.content[0].text
            assert "Workflow looks good" in result.content[0].text

    @pytest.mark.asyncio
    async def test_optimize_workflow_error(self, handlers, mock_backend):
        """Test error handling in optimize_workflow."""
        with patch("memorygraph.integration_tools.optimize_workflow") as mock_optimize:
            mock_optimize.side_effect = ValueError("Invalid session")

            result = await handlers.handle_optimize_workflow({
                "session_id": "invalid"
            })

            assert "Error optimizing workflow" in result.content[0].text


class TestGetSessionState:
    """Tests for get_session_state handler."""

    @pytest.mark.asyncio
    async def test_get_session_state_active(self, handlers, mock_backend):
        """Test getting active session state."""
        mock_state = SessionState(
            session_id="sess_123",
            start_time="2025-11-30T10:00:00",
            last_activity="2025-11-30T11:30:00",
            current_task="Fix authentication",
            open_problems=["Type error in auth.py", "Missing test coverage"],
            next_steps=["Add unit tests", "Update documentation", "Review PR"]
        )

        with patch("memorygraph.integration_tools.get_session_state") as mock_get:
            mock_get.return_value = mock_state

            result = await handlers.handle_get_session_state({
                "session_id": "sess_123"
            })

            assert result is not None
            assert "sess_123" in result.content[0].text
            assert "2025-11-30" in result.content[0].text
            assert "10:00:00" in result.content[0].text
            assert "Fix authentication" in result.content[0].text
            assert "Type error in auth.py" in result.content[0].text
            assert "Add unit tests" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_session_state_empty(self, handlers, mock_backend):
        """Test session state with no problems or steps."""
        mock_state = SessionState(
            session_id="sess_456",
            start_time="2025-11-30T10:00:00",
            last_activity="2025-11-30T10:05:00",
            current_task=None,
            open_problems=[],
            next_steps=[]
        )

        with patch("memorygraph.integration_tools.get_session_state") as mock_get:
            mock_get.return_value = mock_state

            result = await handlers.handle_get_session_state({
                "session_id": "sess_456"
            })

            assert "None" in result.content[0].text  # Current task
            assert "None" in result.content[0].text or "  None" in result.content[0].text  # Open problems
            assert "No suggestions" in result.content[0].text  # Next steps

    @pytest.mark.asyncio
    async def test_get_session_state_not_found(self, handlers, mock_backend):
        """Test when session is not found."""
        with patch("memorygraph.integration_tools.get_session_state") as mock_get:
            mock_get.return_value = None

            result = await handlers.handle_get_session_state({
                "session_id": "nonexistent"
            })

            assert "Session not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_session_state_error(self, handlers, mock_backend):
        """Test error handling in get_session_state."""
        with patch("memorygraph.integration_tools.get_session_state") as mock_get:
            mock_get.side_effect = Exception("Database connection lost")

            result = await handlers.handle_get_session_state({
                "session_id": "sess_123"
            })

            assert "Error getting session state" in result.content[0].text


class TestDispatch:
    """Tests for handler dispatch mechanism."""

    @pytest.mark.asyncio
    async def test_dispatch_valid_tool(self, handlers, mock_backend):
        """Test dispatching to valid tool handler."""
        with patch.object(handlers, 'handle_capture_task') as mock_handler:
            mock_handler.return_value = MagicMock()

            result = await handlers.dispatch("capture_task", {"description": "test", "goals": []})

            assert result is not None
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool(self, handlers, mock_backend):
        """Test dispatching to unknown tool."""
        result = await handlers.dispatch("unknown_tool", {})

        assert result is not None
        assert "Unknown tool" in result.content[0].text
        assert "unknown_tool" in result.content[0].text


class TestBackendInitialization:
    """Tests for backend initialization."""

    @pytest.mark.asyncio
    async def test_ensure_backend_creates_once(self, handlers, backend_factory):
        """Test backend is created only once."""
        await handlers.ensure_backend()
        await handlers.ensure_backend()

        backend_factory.create_backend.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_initializes_backend(self, handlers, mock_backend):
        """Test handlers initialize backend automatically."""
        with patch("memorygraph.integration_tools.capture_task_context") as mock_capture:
            mock_capture.return_value = "mem_123"

            await handlers.handle_capture_task({
                "description": "test",
                "goals": ["test"]
            })

            assert handlers.backend is not None
