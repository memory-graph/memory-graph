"""
Workflow Memory Tools for Claude Code Integration.

Tracks development workflows and provides intelligent suggestions:
- Workflow action tracking
- Session state management
- Workflow suggestions based on past successes
- Workflow optimization recommendations
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from ..backends.base import GraphBackend


class WorkflowAction(BaseModel):
    """Workflow action information."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str = Field(..., description="Session ID")
    action_type: str = Field(..., description="Type of action (e.g., 'command', 'file_edit', 'search')")
    action_data: dict[str, Any] = Field(default_factory=dict, description="Action-specific data")
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_seconds: Optional[float] = Field(None, description="Duration of action")
    success: bool = Field(default=True, description="Whether action succeeded")


class WorkflowSuggestion(BaseModel):
    """Workflow suggestion."""

    suggestion_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_name: str = Field(..., description="Name of suggested workflow")
    description: str = Field(..., description="Description of workflow")
    steps: list[str] = Field(default_factory=list, description="Workflow steps")
    success_rate: float = Field(..., description="Historical success rate")
    relevance_score: float = Field(..., description="Relevance to current context")
    last_used: Optional[datetime] = Field(None, description="When workflow was last used")


class Recommendation(BaseModel):
    """Workflow optimization recommendation."""

    recommendation_id: str = Field(default_factory=lambda: str(uuid4()))
    recommendation_type: str = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    impact: str = Field(..., description="Expected impact (low, medium, high)")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")


class SessionState(BaseModel):
    """Session state information."""

    session_id: str = Field(..., description="Session ID")
    start_time: datetime = Field(..., description="Session start time")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    current_task: Optional[str] = Field(None, description="Current task description")
    open_problems: list[str] = Field(default_factory=list, description="Unresolved problems")
    next_steps: list[str] = Field(default_factory=list, description="Suggested next steps")
    context: dict[str, Any] = Field(default_factory=dict, description="Session context")


async def track_workflow(
    backend: GraphBackend,
    session_id: str,
    action_type: str,
    action_data: dict[str, Any],
    success: bool = True,
    duration_seconds: Optional[float] = None,
) -> str:
    """
    Track a workflow action in the current session.

    Args:
        backend: Database backend
        session_id: Session identifier
        action_type: Type of action
        action_data: Action-specific data
        success: Whether action succeeded
        duration_seconds: Duration of action (optional)

    Returns:
        Memory ID of tracked action

    Example:
        >>> memory_id = await track_workflow(
        ...     backend,
        ...     session_id="session-123",
        ...     action_type="command",
        ...     action_data={"command": "npm test", "exit_code": 0},
        ...     success=True,
        ...     duration_seconds=12.5
        ... )
    """
    action = WorkflowAction(
        session_id=session_id,
        action_type=action_type,
        action_data=action_data,
        success=success,
        duration_seconds=duration_seconds,
    )

    # Store action as observation memory
    properties = {
        "id": action.action_id,
        "type": "workflow_action",
        "title": f"Action: {action_type}",
        "content": f"Session: {session_id}\n"
        f"Action: {action_type}\n"
        f"Success: {success}\n"
        f"Duration: {duration_seconds}s" if duration_seconds else "",
        "context": {
            "session_id": session_id,
            "action_type": action_type,
            "action_data": action_data,
            "success": success,
            "duration_seconds": duration_seconds,
            "timestamp": action.timestamp.isoformat(),
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    memory_id = await backend.store_node("Memory", properties)

    # Create or get session entity
    session_entity = await backend.execute_query(
        """
        MERGE (s:Entity {id: $session_id, type: 'session'})
        ON CREATE SET s.created_at = datetime(), s.start_time = datetime()
        SET s.last_activity = datetime()
        RETURN s.id as id
        """,
        {"session_id": session_id},
    )

    if session_entity:
        # Link action to session
        await backend.store_relationship(
            memory_id,
            session_id,
            "IN_SESSION",
            {"created_at": datetime.now(), "strength": 1.0},
        )

        # Link to previous action (workflow sequence)
        previous_actions = await backend.execute_query(
            """
            MATCH (a:Memory {type: 'workflow_action'})-[:IN_SESSION]->(s:Entity {id: $session_id})
            WHERE a.id <> $current_id
            RETURN a.id as id, a.created_at as created_at
            ORDER BY a.created_at DESC
            LIMIT 1
            """,
            {"session_id": session_id, "current_id": memory_id},
        )

        if previous_actions:
            prev_id = previous_actions[0]["id"]
            await backend.store_relationship(
                memory_id,
                prev_id,
                "FOLLOWS",
                {"created_at": datetime.now(), "strength": 0.8},
            )

    return memory_id


async def suggest_workflow(
    backend: GraphBackend, current_context: dict[str, Any], max_suggestions: int = 5
) -> list[WorkflowSuggestion]:
    """
    Suggest workflows based on current context and past successes.

    Args:
        backend: Database backend
        current_context: Current development context
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of workflow suggestions

    Example:
        >>> suggestions = await suggest_workflow(
        ...     backend,
        ...     current_context={"task": "add feature", "files": ["api.py"]},
        ...     max_suggestions=3
        ... )
        >>> for sug in suggestions:
        ...     print(f"{sug.workflow_name}: {sug.success_rate:.0%}")
    """
    suggestions: list[WorkflowSuggestion] = []

    # Extract context elements for matching
    task_keywords = []
    if "task" in current_context:
        task_keywords = current_context["task"].lower().split()

    # Find similar past workflows
    # Look for sequences of successful actions
    past_workflows = await backend.execute_query(
        """
        MATCH (s:Entity {type: 'session'})
        OPTIONAL MATCH (a:Memory {type: 'workflow_action'})-[:IN_SESSION]->(s)
        WHERE a.context.success = true
        WITH s, COUNT(a) as action_count, COLLECT(a) as actions
        WHERE action_count >= 3
        RETURN s.id as session_id,
               s.start_time as start_time,
               s.last_activity as last_activity,
               actions
        ORDER BY s.last_activity DESC
        LIMIT 20
        """,
        {},
    )

    # Analyze workflow patterns
    workflow_patterns: dict[str, dict] = {}

    for workflow in past_workflows:
        actions = workflow.get("actions", [])
        if not actions:
            continue

        # Create workflow signature from action types
        action_sequence = " -> ".join(a.get("context", {}).get("action_type", "unknown") for a in actions[:10])

        if action_sequence not in workflow_patterns:
            workflow_patterns[action_sequence] = {
                "sequence": action_sequence,
                "count": 0,
                "successes": 0,
                "last_used": None,
                "examples": [],
            }

        workflow_patterns[action_sequence]["count"] += 1
        workflow_patterns[action_sequence]["successes"] += 1  # Already filtered for success
        workflow_patterns[action_sequence]["examples"].append(workflow["session_id"])

        last_activity = workflow.get("last_activity")
        if last_activity and (
            not workflow_patterns[action_sequence]["last_used"]
            or last_activity > workflow_patterns[action_sequence]["last_used"]
        ):
            workflow_patterns[action_sequence]["last_used"] = last_activity

    # Convert patterns to suggestions
    for pattern_key, pattern_data in workflow_patterns.items():
        if pattern_data["count"] < 2:  # Need at least 2 occurrences
            continue

        success_rate = pattern_data["successes"] / pattern_data["count"]

        # Calculate relevance score (placeholder - can be enhanced with semantic matching)
        relevance_score = 0.5
        if task_keywords:
            # Boost relevance if action types match keywords
            for keyword in task_keywords:
                if keyword in pattern_key.lower():
                    relevance_score += 0.1

        relevance_score = min(relevance_score, 1.0)

        # Extract steps from sequence
        steps = pattern_key.split(" -> ")

        suggestion = WorkflowSuggestion(
            workflow_name=f"Workflow: {' -> '.join(steps[:3])}...",
            description=f"Common workflow seen {pattern_data['count']} times",
            steps=steps,
            success_rate=success_rate,
            relevance_score=relevance_score,
            last_used=pattern_data["last_used"],
        )

        suggestions.append(suggestion)

    # Sort by success rate and relevance
    suggestions.sort(
        key=lambda s: (s.success_rate * 0.6 + s.relevance_score * 0.4), reverse=True
    )

    return suggestions[:max_suggestions]


async def optimize_workflow(
    backend: GraphBackend, session_id: str
) -> list[Recommendation]:
    """
    Analyze workflow and provide optimization recommendations.

    Args:
        backend: Database backend
        session_id: Session ID to analyze

    Returns:
        List of optimization recommendations

    Example:
        >>> recommendations = await optimize_workflow(backend, "session-123")
        >>> for rec in recommendations:
        ...     print(f"{rec.title} ({rec.impact} impact)")
    """
    recommendations: list[Recommendation] = []

    # Get session actions
    actions = await backend.execute_query(
        """
        MATCH (a:Memory {type: 'workflow_action'})-[:IN_SESSION]->(s:Entity {id: $session_id})
        RETURN a.id as id,
               a.context as context,
               a.created_at as created_at
        ORDER BY a.created_at
        """,
        {"session_id": session_id},
    )

    if not actions:
        return recommendations

    # Analyze for bottlenecks
    slow_actions = [
        a for a in actions if a.get("context", {}).get("duration_seconds", 0) > 30
    ]

    if slow_actions:
        rec = Recommendation(
            recommendation_type="performance",
            title="Slow actions detected",
            description=f"Found {len(slow_actions)} actions taking over 30 seconds. "
            "Consider optimizing these operations or running them in background.",
            impact="medium",
            evidence=[
                f"Action {a['context'].get('action_type')} took "
                f"{a['context'].get('duration_seconds')}s"
                for a in slow_actions[:3]
            ],
        )
        recommendations.append(rec)

    # Analyze for repeated failures
    failed_actions = [a for a in actions if not a.get("context", {}).get("success", True)]

    if len(failed_actions) >= 3:
        # Look for repeated error patterns
        error_types: dict[str, int] = {}
        for action in failed_actions:
            action_type = action.get("context", {}).get("action_type", "unknown")
            error_types[action_type] = error_types.get(action_type, 0) + 1

        for action_type, count in error_types.items():
            if count >= 2:
                rec = Recommendation(
                    recommendation_type="error_pattern",
                    title=f"Repeated failures in {action_type}",
                    description=f"Action type '{action_type}' failed {count} times. "
                    "This may indicate a systematic issue that needs addressing.",
                    impact="high",
                    evidence=[f"Failed {count} times in this session"],
                )
                recommendations.append(rec)

    # Analyze action sequence for inefficiencies
    action_types = [a.get("context", {}).get("action_type") for a in actions]

    # Look for repeated back-and-forth patterns
    for i in range(len(action_types) - 2):
        if action_types[i] == action_types[i + 2] and action_types[i] != action_types[i + 1]:
            rec = Recommendation(
                recommendation_type="workflow_pattern",
                title="Inefficient back-and-forth pattern detected",
                description=f"Detected switching between {action_types[i]} and {action_types[i+1]} multiple times. "
                "Consider batching similar operations together.",
                impact="low",
                evidence=[f"Pattern: {action_types[i]} -> {action_types[i+1]} -> {action_types[i]}"],
            )
            recommendations.append(rec)
            break  # Only report once

    # Check for long sessions without breaks
    if len(actions) > 50:
        rec = Recommendation(
            recommendation_type="productivity",
            title="Long session detected",
            description=f"This session has {len(actions)} actions. Consider taking breaks "
            "for better productivity and code quality.",
            impact="low",
            evidence=[f"Session has {len(actions)} actions"],
        )
        recommendations.append(rec)

    return recommendations


async def get_session_state(
    backend: GraphBackend, session_id: str
) -> Optional[SessionState]:
    """
    Get current state of a session for continuity.

    Args:
        backend: Database backend
        session_id: Session ID

    Returns:
        SessionState if session exists, None otherwise

    Example:
        >>> state = await get_session_state(backend, "session-123")
        >>> if state:
        ...     print(f"Current task: {state.current_task}")
        ...     print(f"Open problems: {len(state.open_problems)}")
    """
    # Get session entity
    session_data = await backend.execute_query(
        """
        MATCH (s:Entity {id: $session_id, type: 'session'})
        RETURN s.created_at as start_time,
               s.last_activity as last_activity,
               s.current_task as current_task,
               s.context as context
        """,
        {"session_id": session_id},
    )

    if not session_data:
        return None

    session = session_data[0]

    # Get recent actions to determine next steps
    recent_actions = await backend.execute_query(
        """
        MATCH (a:Memory {type: 'workflow_action'})-[:IN_SESSION]->(s:Entity {id: $session_id})
        RETURN a.context as context
        ORDER BY a.created_at DESC
        LIMIT 5
        """,
        {"session_id": session_id},
    )

    # Find open problems (errors without solutions)
    open_problems_data = await backend.execute_query(
        """
        MATCH (e:Memory {type: 'error_pattern'})<-[:EXHIBITS]-(a:Memory {type: 'workflow_action'})
        WHERE (a)-[:IN_SESSION]->(:Entity {id: $session_id})
        AND NOT EXISTS {
            MATCH (e)<-[:SOLVES]-(:Memory)
        }
        RETURN DISTINCT e.title as problem
        LIMIT 10
        """,
        {"session_id": session_id},
    )

    open_problems = [p["problem"] for p in open_problems_data]

    # Suggest next steps based on recent actions
    next_steps = []
    if recent_actions:
        last_action = recent_actions[0]
        action_type = last_action.get("context", {}).get("action_type")
        success = last_action.get("context", {}).get("success", True)

        if not success:
            next_steps.append("Resolve the error from the last action")
        elif action_type == "file_edit":
            next_steps.append("Test the changes made")
        elif action_type == "command" and "test" in last_action.get("context", {}).get("action_data", {}).get("command", ""):
            if success:
                next_steps.append("Commit the changes")
            else:
                next_steps.append("Fix failing tests")

    state = SessionState(
        session_id=session_id,
        start_time=session.get("start_time", datetime.now()),
        last_activity=session.get("last_activity", datetime.now()),
        current_task=session.get("current_task"),
        open_problems=open_problems,
        next_steps=next_steps,
        context=session.get("context", {}),
    )

    return state
