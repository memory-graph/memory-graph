"""
Claude Code Integration module for automatic context capture and project awareness.

This module provides deep integration with Claude Code development workflows:
- Development context capture (tasks, commands, errors)
- Project-aware memory (codebase analysis, file tracking)
- Workflow memory tools (tracking, suggestions, optimization)
"""

from .context_capture import (
    TaskContext,
    CommandExecution,
    ErrorPattern,
    capture_task_context,
    capture_command_execution,
    analyze_error_patterns,
    track_solution_effectiveness,
)

from .project_analysis import (
    ProjectInfo,
    CodebaseInfo,
    FileChange,
    Pattern,
    detect_project,
    analyze_codebase,
    track_file_changes,
    identify_code_patterns,
)

from .workflow_tracking import (
    WorkflowAction,
    WorkflowSuggestion,
    Recommendation,
    SessionState,
    track_workflow,
    suggest_workflow,
    optimize_workflow,
    get_session_state,
)

__all__ = [
    # Context Capture
    "TaskContext",
    "CommandExecution",
    "ErrorPattern",
    "capture_task_context",
    "capture_command_execution",
    "analyze_error_patterns",
    "track_solution_effectiveness",
    # Project Analysis
    "ProjectInfo",
    "CodebaseInfo",
    "FileChange",
    "Pattern",
    "detect_project",
    "analyze_codebase",
    "track_file_changes",
    "identify_code_patterns",
    # Workflow Tracking
    "WorkflowAction",
    "WorkflowSuggestion",
    "Recommendation",
    "SessionState",
    "track_workflow",
    "suggest_workflow",
    "optimize_workflow",
    "get_session_state",
]
