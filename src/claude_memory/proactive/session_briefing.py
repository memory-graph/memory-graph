"""
Session Start Intelligence for Claude Code Memory Server.

Provides automatic briefing when Claude Code starts, including:
- Recent project activity
- Unresolved problems
- Relevant patterns
- Deprecation warnings
- Recommended next steps

Phase 7 Implementation - Session Start Intelligence
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

from pydantic import BaseModel, Field

from ..backends.base import GraphBackend
from ..models import Memory, MemoryType, RelationshipType
from ..integration.project_analysis import detect_project, ProjectInfo

logger = logging.getLogger(__name__)


class RecentActivity(BaseModel):
    """Recent activity in a project."""

    memory_id: str
    memory_type: str
    title: str
    summary: Optional[str] = None
    timestamp: datetime
    tags: List[str] = Field(default_factory=list)


class UnresolvedProblem(BaseModel):
    """Unresolved problem without a solution."""

    problem_id: str
    title: str
    description: str
    created_at: datetime
    tags: List[str] = Field(default_factory=list)
    related_memories: int = 0


class RelevantPattern(BaseModel):
    """Relevant pattern for current project."""

    pattern_id: str
    pattern_type: str
    description: str
    effectiveness: float = 0.5
    usage_count: int = 0
    last_used: Optional[datetime] = None


class DeprecationWarning(BaseModel):
    """Warning about deprecated approaches."""

    deprecated_id: str
    deprecated_title: str
    reason: str
    replacement_id: Optional[str] = None
    replacement_title: Optional[str] = None


class SessionBriefing(BaseModel):
    """
    Complete session briefing for a project.

    Provides developers with relevant context when starting work.
    """

    project_name: str
    project_path: str
    project_type: str
    briefing_timestamp: datetime = Field(default_factory=datetime.now)

    # Activity
    recent_activities: List[RecentActivity] = Field(default_factory=list)
    total_memories: int = 0

    # Issues
    unresolved_problems: List[UnresolvedProblem] = Field(default_factory=list)

    # Recommendations
    relevant_patterns: List[RelevantPattern] = Field(default_factory=list)

    # Warnings
    deprecation_warnings: List[DeprecationWarning] = Field(default_factory=list)

    # Summary
    has_active_issues: bool = False
    has_warnings: bool = False

    def format_as_text(self, verbosity: str = "standard") -> str:
        """
        Format briefing as human-readable text.

        Args:
            verbosity: "minimal", "standard", or "detailed"

        Returns:
            Formatted briefing text
        """
        lines = []
        lines.append(f"# Session Briefing for {self.project_name}")
        lines.append(f"Path: {self.project_path}")
        lines.append(f"Type: {self.project_type}")
        lines.append(f"Time: {self.briefing_timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        # Recent Activity
        if self.recent_activities:
            lines.append("## Recent Activity")
            count = 5 if verbosity == "minimal" else (10 if verbosity == "standard" else len(self.recent_activities))
            for activity in self.recent_activities[:count]:
                age = (datetime.now() - activity.timestamp).days
                age_str = f"{age}d ago" if age > 0 else "today"
                lines.append(f"- [{activity.memory_type}] {activity.title} ({age_str})")
                if verbosity == "detailed" and activity.summary:
                    lines.append(f"  {activity.summary}")
            lines.append("")

        # Active Issues
        if self.unresolved_problems:
            lines.append("## Active Issues ⚠️")
            for problem in self.unresolved_problems:
                age = (datetime.now() - problem.created_at).days
                lines.append(f"- {problem.title} ({age}d old)")
                if verbosity in ["standard", "detailed"]:
                    lines.append(f"  {problem.description[:200]}...")
            lines.append("")

        # Recommended Patterns
        if self.relevant_patterns:
            lines.append("## Recommended Patterns")
            count = 3 if verbosity == "minimal" else 5
            for pattern in self.relevant_patterns[:count]:
                eff_pct = int(pattern.effectiveness * 100)
                lines.append(f"- {pattern.pattern_type}: {pattern.description}")
                if verbosity in ["standard", "detailed"]:
                    lines.append(f"  Effectiveness: {eff_pct}%, Used {pattern.usage_count} times")
            lines.append("")

        # Warnings
        if self.deprecation_warnings:
            lines.append("## Deprecation Warnings ⚠️")
            for warning in self.deprecation_warnings:
                lines.append(f"- {warning.deprecated_title} is deprecated")
                if warning.replacement_title:
                    lines.append(f"  Use instead: {warning.replacement_title}")
                if verbosity == "detailed":
                    lines.append(f"  Reason: {warning.reason}")
            lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append(f"- Total memories: {self.total_memories}")
        lines.append(f"- Active issues: {len(self.unresolved_problems)}")
        lines.append(f"- Patterns available: {len(self.relevant_patterns)}")
        if self.deprecation_warnings:
            lines.append(f"- ⚠️ {len(self.deprecation_warnings)} deprecation warnings")

        return "\n".join(lines)


async def generate_session_briefing(
    backend: GraphBackend,
    project_dir: str,
    recency_days: int = 7,
    max_activities: int = 10,
) -> Optional[SessionBriefing]:
    """
    Generate a session briefing for a project.

    Args:
        backend: Database backend
        project_dir: Project directory path
        recency_days: How many days back to look for recent activity
        max_activities: Maximum number of recent activities to include

    Returns:
        SessionBriefing if project detected, None otherwise

    Example:
        >>> briefing = await generate_session_briefing(backend, "/Users/me/my-app")
        >>> print(briefing.format_as_text("standard"))
    """
    # Detect project
    project = await detect_project(backend, project_dir)
    if not project:
        logger.warning(f"Could not detect project at {project_dir}")
        return None

    logger.info(f"Generating session briefing for project: {project.name}")

    # Initialize briefing
    briefing = SessionBriefing(
        project_name=project.name,
        project_path=project.path,
        project_type=project.project_type,
    )

    # Get total memory count for project
    total_count_query = """
    MATCH (m:Memory)
    WHERE m.context IS NOT NULL
      AND (m.context CONTAINS $project_path OR m.context CONTAINS $project_name)
    RETURN count(m) as total
    """

    try:
        result = await backend.execute_query(
            total_count_query,
            {
                "project_path": project.path,
                "project_name": project.name,
            }
        )
        briefing.total_memories = result[0]["total"] if result else 0
    except Exception as e:
        logger.error(f"Error counting memories: {e}")

    # Get recent activities
    cutoff_date = datetime.now() - timedelta(days=recency_days)

    recent_query = """
    MATCH (m:Memory)
    WHERE m.context IS NOT NULL
      AND (m.context CONTAINS $project_path OR m.context CONTAINS $project_name)
      AND datetime(m.created_at) >= datetime($cutoff)
    RETURN m.id as id, m.type as type, m.title as title,
           m.summary as summary, m.created_at as created_at,
           m.tags as tags
    ORDER BY m.created_at DESC
    LIMIT $limit
    """

    try:
        results = await backend.execute_query(
            recent_query,
            {
                "project_path": project.path,
                "project_name": project.name,
                "cutoff": cutoff_date.isoformat(),
                "limit": max_activities,
            }
        )

        for record in results:
            briefing.recent_activities.append(RecentActivity(
                memory_id=record["id"],
                memory_type=record["type"],
                title=record["title"],
                summary=record.get("summary"),
                timestamp=datetime.fromisoformat(record["created_at"]),
                tags=record.get("tags", []),
            ))
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")

    # Get unresolved problems (problems without solutions)
    problems_query = """
    MATCH (p:Memory {type: 'problem'})
    WHERE p.context IS NOT NULL
      AND (p.context CONTAINS $project_path OR p.context CONTAINS $project_name)
      AND NOT EXISTS {
        MATCH (p)-[:SOLVES|ADDRESSES]->(:Memory)
      }
    OPTIONAL MATCH (p)-[r]-()
    RETURN p.id as id, p.title as title, p.content as content,
           p.created_at as created_at, p.tags as tags,
           count(r) as related_count
    ORDER BY p.created_at DESC
    LIMIT 5
    """

    try:
        results = await backend.execute_query(
            problems_query,
            {
                "project_path": project.path,
                "project_name": project.name,
            }
        )

        for record in results:
            briefing.unresolved_problems.append(UnresolvedProblem(
                problem_id=record["id"],
                title=record["title"],
                description=record["content"][:200],
                created_at=datetime.fromisoformat(record["created_at"]),
                tags=record.get("tags", []),
                related_memories=record.get("related_count", 0),
            ))

        briefing.has_active_issues = len(briefing.unresolved_problems) > 0
    except Exception as e:
        logger.error(f"Error fetching unresolved problems: {e}")

    # Get relevant patterns
    patterns_query = """
    MATCH (m:Memory {type: 'code_pattern'})
    WHERE m.context IS NOT NULL
      AND (m.context CONTAINS $project_path OR m.context CONTAINS $project_name)
    RETURN m.id as id, m.title as type, m.content as description,
           m.effectiveness as effectiveness, m.usage_count as usage_count,
           m.last_accessed as last_used
    ORDER BY m.effectiveness DESC, m.usage_count DESC
    LIMIT 5
    """

    try:
        results = await backend.execute_query(
            patterns_query,
            {
                "project_path": project.path,
                "project_name": project.name,
            }
        )

        for record in results:
            briefing.relevant_patterns.append(RelevantPattern(
                pattern_id=record["id"],
                pattern_type=record["type"],
                description=record["description"][:200],
                effectiveness=record.get("effectiveness", 0.5),
                usage_count=record.get("usage_count", 0),
                last_used=datetime.fromisoformat(record["last_used"]) if record.get("last_used") else None,
            ))
    except Exception as e:
        logger.error(f"Error fetching patterns: {e}")

    # Get deprecation warnings (memories with DEPRECATED_BY relationships)
    deprecated_query = """
    MATCH (old:Memory)-[r:DEPRECATED_BY]->(new:Memory)
    WHERE old.context IS NOT NULL
      AND (old.context CONTAINS $project_path OR old.context CONTAINS $project_name)
    RETURN old.id as old_id, old.title as old_title,
           new.id as new_id, new.title as new_title,
           r.context as reason
    LIMIT 5
    """

    try:
        results = await backend.execute_query(
            deprecated_query,
            {
                "project_path": project.path,
                "project_name": project.name,
            }
        )

        for record in results:
            briefing.deprecation_warnings.append(DeprecationWarning(
                deprecated_id=record["old_id"],
                deprecated_title=record["old_title"],
                reason=record.get("reason", "No longer recommended"),
                replacement_id=record.get("new_id"),
                replacement_title=record.get("new_title"),
            ))

        briefing.has_warnings = len(briefing.deprecation_warnings) > 0
    except Exception as e:
        logger.error(f"Error fetching deprecation warnings: {e}")

    logger.info(f"Session briefing generated: {len(briefing.recent_activities)} activities, "
                f"{len(briefing.unresolved_problems)} problems, "
                f"{len(briefing.relevant_patterns)} patterns")

    return briefing


def get_session_briefing_resource(briefing: SessionBriefing, verbosity: str = "standard") -> Dict[str, Any]:
    """
    Format session briefing as MCP resource.

    Args:
        briefing: Session briefing to format
        verbosity: Verbosity level ("minimal", "standard", "detailed")

    Returns:
        MCP resource dictionary

    Example:
        >>> resource = get_session_briefing_resource(briefing, "standard")
    """
    return {
        "uri": f"memory://session/briefing/{briefing.project_name}",
        "name": f"Session Briefing: {briefing.project_name}",
        "description": f"Automatic session briefing for {briefing.project_name}",
        "mimeType": "text/markdown",
        "text": briefing.format_as_text(verbosity),
    }
