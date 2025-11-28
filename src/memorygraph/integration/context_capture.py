"""
Development Context Capture for Claude Code Integration.

Automatically captures development context from Claude Code sessions including:
- Task context (description, goals, files involved)
- Command executions (commands run, results, errors)
- Error pattern analysis (recurring errors, solutions)
- Solution effectiveness tracking
"""

import re
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from ..backends.base import GraphBackend


class TaskContext(BaseModel):
    """Task context information."""

    task_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str = Field(..., description="Task description")
    goals: list[str] = Field(default_factory=list, description="Task goals")
    files_involved: list[str] = Field(default_factory=list, description="Files involved in task")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    success: Optional[bool] = None
    notes: Optional[str] = None


class CommandExecution(BaseModel):
    """Command execution information."""

    command_id: str = Field(default_factory=lambda: str(uuid4()))
    command: str = Field(..., description="Command executed")
    output: str = Field(default="", description="Command output")
    error: Optional[str] = Field(None, description="Error message if failed")
    success: bool = Field(..., description="Whether command succeeded")
    timestamp: datetime = Field(default_factory=datetime.now)
    task_id: Optional[str] = Field(None, description="Associated task ID")


class ErrorPattern(BaseModel):
    """Error pattern identified from commands."""

    pattern_id: str = Field(default_factory=lambda: str(uuid4()))
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message pattern")
    frequency: int = Field(default=1, description="Number of occurrences")
    solutions_tried: list[str] = Field(default_factory=list, description="Solutions attempted")
    successful_solutions: list[str] = Field(
        default_factory=list, description="Solutions that worked"
    )
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


# Security filters for sensitive data
SENSITIVE_PATTERNS = [
    r"(?i)(api[_-]?key|token|password|secret|auth)[=:\s]+['\"]?[\w\-\.]+['\"]?",
    r"(?i)bearer\s+[\w\-\.]+",  # Bearer tokens
    r"(?i)(aws|gcp|azure)[_-]?(access|secret)[_-]?key[=:\s]+['\"]?[\w\-\.]+['\"]?",
    r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    r"(?:https?://)?[\w\-]+:[\w\-]+@",  # URLs with credentials
    r"\b[\w\-\.]+@[\w\-\.]+\.(com|net|org|io|dev)\b",  # Email addresses (PII)
]


def _sanitize_content(content: str) -> str:
    """
    Sanitize content by removing sensitive information.

    Args:
        content: Content to sanitize

    Returns:
        Sanitized content
    """
    sanitized = content
    for pattern in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)
    return sanitized


async def capture_task_context(
    backend: GraphBackend,
    description: str,
    goals: list[str],
    files: Optional[list[str]] = None,
    project_id: Optional[str] = None,
) -> str:
    """
    Capture task context and store as memory.

    Args:
        backend: Database backend
        description: Task description
        goals: List of task goals
        files: List of files involved (optional)
        project_id: Project ID (optional)

    Returns:
        Memory ID of stored task context

    Example:
        >>> memory_id = await capture_task_context(
        ...     backend,
        ...     "Add dark mode toggle to settings",
        ...     ["Create toggle component", "Add state management", "Update styling"],
        ...     files=["src/components/Settings.tsx", "src/context/ThemeContext.tsx"],
        ...     project_id="my-app"
        ... )
    """
    # Sanitize inputs
    description = _sanitize_content(description)
    goals = [_sanitize_content(goal) for goal in goals]
    files = [_sanitize_content(f) for f in (files or [])]

    task_context = TaskContext(
        description=description, goals=goals, files_involved=files or []
    )

    # Store as memory
    properties = {
        "id": task_context.task_id,
        "type": "task",
        "title": f"Task: {description[:100]}",
        "content": f"Description: {description}\n\nGoals:\n"
        + "\n".join(f"- {goal}" for goal in goals),
        "context": {
            "goals": goals,
            "files": files or [],
            "start_time": task_context.start_time.isoformat(),
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    # Add project relationship if provided
    if project_id:
        properties["context"]["project_id"] = project_id

    memory_id = await backend.store_node("Memory", properties)

    # Create relationships to file entities
    for file_path in files or []:
        # Create or get file entity
        file_entity = await backend.execute_query(
            """
            MERGE (f:Entity {name: $file_path, type: 'file'})
            ON CREATE SET f.id = $file_id, f.created_at = datetime()
            RETURN f.id as id
            """,
            {"file_path": file_path, "file_id": str(uuid4())},
        )

        if file_entity:
            file_id = file_entity[0]["id"]
            # Link task to file
            await backend.store_relationship(
                memory_id,
                file_id,
                "INVOLVES",
                {"created_at": datetime.now(), "strength": 1.0},
            )

    # Link to project if provided
    if project_id:
        await backend.store_relationship(
            memory_id,
            project_id,
            "PART_OF",
            {"created_at": datetime.now(), "strength": 1.0},
        )

    return memory_id


async def capture_command_execution(
    backend: GraphBackend,
    command: str,
    output: str = "",
    error: Optional[str] = None,
    success: bool = True,
    task_id: Optional[str] = None,
) -> str:
    """
    Capture command execution and store as observation memory.

    Args:
        backend: Database backend
        command: Command executed
        output: Command output
        error: Error message if failed
        success: Whether command succeeded
        task_id: Associated task ID (optional)

    Returns:
        Memory ID of stored command execution

    Example:
        >>> memory_id = await capture_command_execution(
        ...     backend,
        ...     "npm run build",
        ...     output="Build completed successfully",
        ...     success=True,
        ...     task_id="task-123"
        ... )
    """
    # Sanitize inputs
    command = _sanitize_content(command)
    output = _sanitize_content(output)
    if error:
        error = _sanitize_content(error)

    cmd_exec = CommandExecution(
        command=command, output=output, error=error, success=success, task_id=task_id
    )

    # Store as observation memory
    properties = {
        "id": cmd_exec.command_id,
        "type": "observation",
        "title": f"Command: {command[:100]}",
        "content": f"Command: {command}\n\n"
        f"Success: {success}\n\n"
        f"Output:\n{output[:500]}"
        + (f"\n\nError:\n{error[:500]}" if error else ""),
        "context": {
            "command": command,
            "success": success,
            "has_error": bool(error),
            "timestamp": cmd_exec.timestamp.isoformat(),
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    if task_id:
        properties["context"]["task_id"] = task_id

    memory_id = await backend.store_node("Memory", properties)

    # Link to task if provided
    if task_id:
        await backend.store_relationship(
            memory_id,
            task_id,
            "EXECUTED_IN",
            {"created_at": datetime.now(), "strength": 1.0},
        )

    # Extract and link errors if present
    if error and not success:
        error_patterns = await analyze_error_patterns(backend, error)
        for pattern_id in error_patterns:
            await backend.store_relationship(
                memory_id,
                pattern_id,
                "EXHIBITS",
                {"created_at": datetime.now(), "strength": 0.9},
            )

    return memory_id


async def analyze_error_patterns(backend: GraphBackend, error: str) -> list[str]:
    """
    Analyze error message and identify patterns.

    Args:
        backend: Database backend
        error: Error message

    Returns:
        List of pattern memory IDs

    Example:
        >>> pattern_ids = await analyze_error_patterns(
        ...     backend,
        ...     "TypeError: Cannot read property 'map' of undefined"
        ... )
    """
    # Sanitize error
    error = _sanitize_content(error)

    # Extract error type
    error_type = "unknown"
    type_match = re.search(r"^(\w+Error|\w+Exception):", error)
    if type_match:
        error_type = type_match.group(1)

    # Search for existing error pattern
    existing_patterns = await backend.search_nodes(
        "Memory",
        {
            "type": "error_pattern",
            "context.error_type": error_type,
        },
    )

    pattern_ids = []

    if existing_patterns:
        # Update existing pattern
        for pattern in existing_patterns:
            pattern_id = pattern["id"]
            # Increment frequency
            await backend.execute_query(
                """
                MATCH (m:Memory {id: $pattern_id})
                SET m.context.frequency = COALESCE(m.context.frequency, 0) + 1,
                    m.updated_at = datetime()
                """,
                {"pattern_id": pattern_id},
            )
            pattern_ids.append(pattern_id)
    else:
        # Create new pattern
        error_pattern = ErrorPattern(
            error_type=error_type,
            error_message=error[:500],  # Truncate long errors
        )

        properties = {
            "id": error_pattern.pattern_id,
            "type": "error_pattern",
            "title": f"Error Pattern: {error_type}",
            "content": f"Error Type: {error_type}\n\nMessage Pattern:\n{error_pattern.error_message}",
            "context": {
                "error_type": error_type,
                "error_message": error_pattern.error_message,
                "frequency": 1,
                "solutions_tried": [],
                "successful_solutions": [],
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        pattern_id = await backend.store_node("Memory", properties)
        pattern_ids.append(pattern_id)

    return pattern_ids


async def track_solution_effectiveness(
    backend: GraphBackend,
    solution_memory_id: str,
    error_pattern_id: str,
    success: bool,
    notes: Optional[str] = None,
) -> None:
    """
    Track effectiveness of a solution for an error pattern.

    Args:
        backend: Database backend
        solution_memory_id: Memory ID of the solution
        error_pattern_id: Memory ID of the error pattern
        success: Whether the solution worked
        notes: Additional notes (optional)

    Example:
        >>> await track_solution_effectiveness(
        ...     backend,
        ...     solution_id="sol-123",
        ...     error_pattern_id="err-456",
        ...     success=True,
        ...     notes="Fixed by adding null check"
        ... )
    """
    # Create relationship between solution and error pattern
    rel_type = "SOLVES" if success else "ATTEMPTED_SOLUTION"

    properties = {
        "created_at": datetime.now(),
        "success": success,
        "strength": 1.0 if success else 0.3,
        "confidence": 0.9 if success else 0.5,
    }

    if notes:
        properties["notes"] = _sanitize_content(notes)

    await backend.store_relationship(
        solution_memory_id, error_pattern_id, rel_type, properties
    )

    # Update error pattern with solution info
    if success:
        await backend.execute_query(
            """
            MATCH (m:Memory {id: $pattern_id})
            SET m.context.successful_solutions =
                COALESCE(m.context.successful_solutions, []) + [$solution_id],
                m.updated_at = datetime()
            """,
            {"pattern_id": error_pattern_id, "solution_id": solution_memory_id},
        )
    else:
        await backend.execute_query(
            """
            MATCH (m:Memory {id: $pattern_id})
            SET m.context.solutions_tried =
                COALESCE(m.context.solutions_tried, []) + [$solution_id],
                m.updated_at = datetime()
            """,
            {"pattern_id": error_pattern_id, "solution_id": solution_memory_id},
        )

    # Update solution confidence based on effectiveness
    await backend.execute_query(
        """
        MATCH (s:Memory {id: $solution_id})
        MATCH (s)-[r:SOLVES|ATTEMPTED_SOLUTION]->(e:Memory {type: 'error_pattern'})
        WITH s, COUNT(r) as total_attempts,
             SUM(CASE WHEN type(r) = 'SOLVES' THEN 1 ELSE 0 END) as successes
        SET s.context.effectiveness = toFloat(successes) / toFloat(total_attempts),
            s.context.total_uses = total_attempts,
            s.updated_at = datetime()
        """,
        {"solution_id": solution_memory_id},
    )
