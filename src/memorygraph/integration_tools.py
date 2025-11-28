"""
MCP tools for Claude Code Integration features.

This module provides MCP tool definitions and handlers for Phase 6 integration features:
- Context capture tools (tasks, commands, errors)
- Project analysis tools (detection, codebase analysis)
- Workflow tracking tools (sessions, suggestions, optimization)
"""

import logging
from typing import Any, Optional

from mcp.types import Tool, TextContent, CallToolResult

from .backends.factory import BackendFactory
from .integration.context_capture import (
    capture_task_context,
    capture_command_execution,
    analyze_error_patterns,
    track_solution_effectiveness,
)
from .integration.project_analysis import (
    detect_project,
    analyze_codebase,
    track_file_changes,
    identify_code_patterns,
)
from .integration.workflow_tracking import (
    track_workflow,
    suggest_workflow,
    optimize_workflow,
    get_session_state,
)


logger = logging.getLogger(__name__)


# Tool definitions for Claude Code integration
INTEGRATION_TOOLS = [
    Tool(
        name="capture_task",
        description="Capture task context including description, goals, and files involved",
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Task description",
                },
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of task goals",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files involved in the task",
                },
                "project_id": {
                    "type": "string",
                    "description": "Project ID (optional)",
                },
            },
            "required": ["description", "goals"],
        },
    ),
    Tool(
        name="capture_command",
        description="Capture command execution with output and success status",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command executed",
                },
                "output": {
                    "type": "string",
                    "description": "Command output",
                },
                "error": {
                    "type": "string",
                    "description": "Error message if command failed",
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether command succeeded",
                },
                "task_id": {
                    "type": "string",
                    "description": "Associated task ID (optional)",
                },
            },
            "required": ["command", "success"],
        },
    ),
    Tool(
        name="track_error_solution",
        description="Track effectiveness of a solution for an error pattern",
        inputSchema={
            "type": "object",
            "properties": {
                "solution_memory_id": {
                    "type": "string",
                    "description": "Memory ID of the solution",
                },
                "error_pattern_id": {
                    "type": "string",
                    "description": "Memory ID of the error pattern",
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether the solution worked",
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes about the solution",
                },
            },
            "required": ["solution_memory_id", "error_pattern_id", "success"],
        },
    ),
    Tool(
        name="detect_project",
        description="Detect project information from a directory",
        inputSchema={
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path to analyze",
                },
            },
            "required": ["directory"],
        },
    ),
    Tool(
        name="analyze_project",
        description="Analyze project codebase structure and characteristics",
        inputSchema={
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Project directory path",
                },
            },
            "required": ["directory"],
        },
    ),
    Tool(
        name="track_file_changes",
        description="Track file changes in a git repository",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Git repository path",
                },
                "project_id": {
                    "type": "string",
                    "description": "Project ID",
                },
            },
            "required": ["repo_path", "project_id"],
        },
    ),
    Tool(
        name="identify_patterns",
        description="Identify code patterns in project files",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to analyze",
                },
            },
            "required": ["project_id", "files"],
        },
    ),
    Tool(
        name="track_workflow",
        description="Track a workflow action in the current session",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier",
                },
                "action_type": {
                    "type": "string",
                    "description": "Type of action (e.g., 'command', 'file_edit', 'search')",
                },
                "action_data": {
                    "type": "object",
                    "description": "Action-specific data",
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether action succeeded",
                },
                "duration_seconds": {
                    "type": "number",
                    "description": "Duration of action in seconds",
                },
            },
            "required": ["session_id", "action_type"],
        },
    ),
    Tool(
        name="suggest_workflow",
        description="Get workflow suggestions based on current context",
        inputSchema={
            "type": "object",
            "properties": {
                "context": {
                    "type": "object",
                    "description": "Current development context",
                },
                "max_suggestions": {
                    "type": "number",
                    "description": "Maximum number of suggestions",
                },
            },
            "required": ["context"],
        },
    ),
    Tool(
        name="optimize_workflow",
        description="Analyze workflow and get optimization recommendations",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to analyze",
                },
            },
            "required": ["session_id"],
        },
    ),
    Tool(
        name="get_session_state",
        description="Get current session state for continuity",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID",
                },
            },
            "required": ["session_id"],
        },
    ),
]


class IntegrationToolHandlers:
    """Handlers for integration tool calls."""

    def __init__(self, backend_factory: BackendFactory):
        """
        Initialize integration tool handlers.

        Args:
            backend_factory: Backend factory for creating database connections
        """
        self.backend_factory = backend_factory
        self.backend = None

    async def ensure_backend(self):
        """Ensure backend is initialized."""
        if self.backend is None:
            self.backend = await self.backend_factory.create_backend()

    async def handle_capture_task(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle capture_task tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with memory ID
        """
        try:
            await self.ensure_backend()

            description = arguments["description"]
            goals = arguments["goals"]
            files = arguments.get("files", [])
            project_id = arguments.get("project_id")

            memory_id = await capture_task_context(
                self.backend, description, goals, files, project_id
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Task captured successfully.\n"
                        f"Memory ID: {memory_id}\n"
                        f"Description: {description}\n"
                        f"Goals: {len(goals)}\n"
                        f"Files: {len(files)}",
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Error capturing task: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error capturing task: {str(e)}")]
            )

    async def handle_capture_command(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle capture_command tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with memory ID
        """
        try:
            await self.ensure_backend()

            command = arguments["command"]
            output = arguments.get("output", "")
            error = arguments.get("error")
            success = arguments["success"]
            task_id = arguments.get("task_id")

            memory_id = await capture_command_execution(
                self.backend, command, output, error, success, task_id
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Command captured successfully.\n"
                        f"Memory ID: {memory_id}\n"
                        f"Command: {command}\n"
                        f"Success: {success}",
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Error capturing command: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error capturing command: {str(e)}")]
            )

    async def handle_track_error_solution(
        self, arguments: dict[str, Any]
    ) -> CallToolResult:
        """
        Handle track_error_solution tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult
        """
        try:
            await self.ensure_backend()

            solution_memory_id = arguments["solution_memory_id"]
            error_pattern_id = arguments["error_pattern_id"]
            success = arguments["success"]
            notes = arguments.get("notes")

            await track_solution_effectiveness(
                self.backend, solution_memory_id, error_pattern_id, success, notes
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Solution effectiveness tracked.\n"
                        f"Solution: {solution_memory_id}\n"
                        f"Error Pattern: {error_pattern_id}\n"
                        f"Success: {success}",
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Error tracking solution: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error tracking solution: {str(e)}")
                ]
            )

    async def handle_detect_project(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle detect_project tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with project info
        """
        try:
            await self.ensure_backend()

            directory = arguments["directory"]

            project = await detect_project(self.backend, directory)

            if project:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Project detected:\n"
                            f"Name: {project.name}\n"
                            f"Type: {project.project_type}\n"
                            f"Path: {project.path}\n"
                            f"Technologies: {', '.join(project.technologies)}\n"
                            f"Git Remote: {project.git_remote or 'None'}\n"
                            f"Project ID: {project.project_id}",
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(type="text", text="No project detected in directory")
                    ]
                )

        except Exception as e:
            logger.error(f"Error detecting project: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error detecting project: {str(e)}")]
            )

    async def handle_analyze_project(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle analyze_project tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with codebase analysis
        """
        try:
            await self.ensure_backend()

            directory = arguments["directory"]

            info = await analyze_codebase(self.backend, directory)

            file_types_str = "\n".join(
                f"  {ext}: {count}" for ext, count in sorted(info.file_types.items())
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Codebase Analysis:\n"
                        f"Total Files: {info.total_files}\n"
                        f"Languages: {', '.join(info.languages)}\n"
                        f"Frameworks: {', '.join(info.frameworks) if info.frameworks else 'None detected'}\n"
                        f"\nFile Types:\n{file_types_str}",
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Error analyzing project: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error analyzing project: {str(e)}")
                ]
            )

    async def handle_track_file_changes(
        self, arguments: dict[str, Any]
    ) -> CallToolResult:
        """
        Handle track_file_changes tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with change summary
        """
        try:
            await self.ensure_backend()

            repo_path = arguments["repo_path"]
            project_id = arguments["project_id"]

            changes = await track_file_changes(self.backend, repo_path, project_id)

            if changes:
                changes_str = "\n".join(
                    f"  {c.change_type}: {c.file_path} (+{c.lines_added}/-{c.lines_removed})"
                    for c in changes
                )
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"File changes tracked ({len(changes)} files):\n{changes_str}",
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="No file changes detected")]
                )

        except Exception as e:
            logger.error(f"Error tracking file changes: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error tracking file changes: {str(e)}")
                ]
            )

    async def handle_identify_patterns(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle identify_patterns tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with identified patterns
        """
        try:
            await self.ensure_backend()

            project_id = arguments["project_id"]
            files = arguments["files"]

            patterns = await identify_code_patterns(self.backend, project_id, files)

            if patterns:
                patterns_str = "\n".join(
                    f"  {p.pattern_type}: {p.frequency} occurrences (confidence: {p.confidence:.2f})"
                    for p in patterns
                )
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Code patterns identified ({len(patterns)} patterns):\n{patterns_str}",
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="No significant patterns found")]
                )

        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error identifying patterns: {str(e)}")
                ]
            )

    async def handle_track_workflow(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle track_workflow tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with memory ID
        """
        try:
            await self.ensure_backend()

            session_id = arguments["session_id"]
            action_type = arguments["action_type"]
            action_data = arguments.get("action_data", {})
            success = arguments.get("success", True)
            duration_seconds = arguments.get("duration_seconds")

            memory_id = await track_workflow(
                self.backend, session_id, action_type, action_data, success, duration_seconds
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Workflow action tracked.\n"
                        f"Memory ID: {memory_id}\n"
                        f"Action: {action_type}\n"
                        f"Success: {success}",
                    )
                ]
            )

        except Exception as e:
            logger.error(f"Error tracking workflow: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error tracking workflow: {str(e)}")
                ]
            )

    async def handle_suggest_workflow(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle suggest_workflow tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with workflow suggestions
        """
        try:
            await self.ensure_backend()

            context = arguments["context"]
            max_suggestions = arguments.get("max_suggestions", 5)

            suggestions = await suggest_workflow(self.backend, context, max_suggestions)

            if suggestions:
                suggestions_str = "\n\n".join(
                    f"{i+1}. {s.workflow_name}\n"
                    f"   Description: {s.description}\n"
                    f"   Success Rate: {s.success_rate:.0%}\n"
                    f"   Relevance: {s.relevance_score:.0%}\n"
                    f"   Steps: {' -> '.join(s.steps[:5])}"
                    for i, s in enumerate(suggestions)
                )
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Workflow Suggestions ({len(suggestions)}):\n\n{suggestions_str}",
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="No workflow suggestions available yet. Build more workflow history!",
                        )
                    ]
                )

        except Exception as e:
            logger.error(f"Error suggesting workflow: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error suggesting workflow: {str(e)}")
                ]
            )

    async def handle_optimize_workflow(self, arguments: dict[str, Any]) -> CallToolResult:
        """
        Handle optimize_workflow tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with recommendations
        """
        try:
            await self.ensure_backend()

            session_id = arguments["session_id"]

            recommendations = await optimize_workflow(self.backend, session_id)

            if recommendations:
                recs_str = "\n\n".join(
                    f"{i+1}. {r.title} ({r.impact} impact)\n"
                    f"   {r.description}\n"
                    f"   Evidence: {', '.join(r.evidence[:3])}"
                    for i, r in enumerate(recommendations)
                )
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Workflow Optimization Recommendations ({len(recommendations)}):\n\n{recs_str}",
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(type="text", text="No optimization recommendations found. Workflow looks good!")
                    ]
                )

        except Exception as e:
            logger.error(f"Error optimizing workflow: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error optimizing workflow: {str(e)}")
                ]
            )

    async def handle_get_session_state(
        self, arguments: dict[str, Any]
    ) -> CallToolResult:
        """
        Handle get_session_state tool call.

        Args:
            arguments: Tool arguments

        Returns:
            CallToolResult with session state
        """
        try:
            await self.ensure_backend()

            session_id = arguments["session_id"]

            state = await get_session_state(self.backend, session_id)

            if state:
                next_steps_str = "\n".join(f"  - {step}" for step in state.next_steps)
                problems_str = "\n".join(f"  - {p}" for p in state.open_problems)

                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Session State:\n"
                            f"Session ID: {state.session_id}\n"
                            f"Start Time: {state.start_time}\n"
                            f"Last Activity: {state.last_activity}\n"
                            f"Current Task: {state.current_task or 'None'}\n"
                            f"\nOpen Problems ({len(state.open_problems)}):\n{problems_str or '  None'}\n"
                            f"\nNext Steps:\n{next_steps_str or '  No suggestions'}",
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="Session not found")]
                )

        except Exception as e:
            logger.error(f"Error getting session state: {e}")
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Error getting session state: {str(e)}")
                ]
            )

    async def dispatch(self, tool_name: str, arguments: dict[str, Any]) -> CallToolResult:
        """
        Dispatch tool call to appropriate handler.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            CallToolResult from handler
        """
        handlers = {
            "capture_task": self.handle_capture_task,
            "capture_command": self.handle_capture_command,
            "track_error_solution": self.handle_track_error_solution,
            "detect_project": self.handle_detect_project,
            "analyze_project": self.handle_analyze_project,
            "track_file_changes": self.handle_track_file_changes,
            "identify_patterns": self.handle_identify_patterns,
            "track_workflow": self.handle_track_workflow,
            "suggest_workflow": self.handle_suggest_workflow,
            "optimize_workflow": self.handle_optimize_workflow,
            "get_session_state": self.handle_get_session_state,
        }

        handler = handlers.get(tool_name)
        if handler:
            return await handler(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {tool_name}")]
            )
