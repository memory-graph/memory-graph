"""
Activity and statistics tool handlers for the MCP server.

This module contains handlers for activity and statistics operations:
- get_recent_activity: Get summary of recent memory activity
- get_memory_statistics: Get statistics about the memory database
- search_relationships_by_context: Search relationships by structured context fields
"""

import logging
from typing import Any, Dict, Union

from mcp.types import CallToolResult, TextContent

from ..database import MemoryDatabase
from ..models import Memory

logger = logging.getLogger(__name__)


def _get_memory_attr(memory: Union[Memory, Dict[str, Any]], attr: str, default: Any = None) -> Any:
    """Get attribute from Memory object or dict, handling both cases.

    Args:
        memory: Memory object or dict representation
        attr: Attribute name to retrieve
        default: Default value if attribute not found

    Returns:
        Attribute value or default
    """
    if hasattr(memory, attr):
        value = getattr(memory, attr)
        # Handle nested attributes like type.value
        if attr == "type" and hasattr(value, "value"):
            return value.value
        return value
    elif isinstance(memory, dict):
        return memory.get(attr, default)
    return default


async def handle_get_memory_statistics(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_memory_statistics tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call (no parameters required)

    Returns:
        CallToolResult with formatted statistics or error message
    """
    try:
        stats = await memory_db.get_memory_statistics()

        # Format statistics
        stats_text = "**Memory Database Statistics**\n\n"

        if stats.get("total_memories"):
            stats_text += f"Total Memories: {stats['total_memories']['count']}\n"

        if stats.get("memories_by_type"):
            stats_text += "\n**Memories by Type:**\n"
            for mem_type, count in stats["memories_by_type"].items():
                stats_text += f"- {mem_type}: {count}\n"

        if stats.get("total_relationships"):
            stats_text += f"\nTotal Relationships: {stats['total_relationships']['count']}\n"

        if stats.get("avg_importance"):
            stats_text += f"Average Importance: {stats['avg_importance']['avg_importance']:.2f}\n"

        if stats.get("avg_confidence"):
            stats_text += f"Average Confidence: {stats['avg_confidence']['avg_confidence']:.2f}\n"

        return CallToolResult(
            content=[TextContent(type="text", text=stats_text)]
        )
    except Exception as e:
        logger.error(f"Failed to get memory statistics: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to get memory statistics: {e}"
            )],
            isError=True
        )


async def handle_get_recent_activity(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_recent_activity tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - days: Number of days to look back (default: 7)
            - project: Optional project path to filter by

    Returns:
        CallToolResult with formatted activity summary or error message
    """
    try:
        # Check if database supports get_recent_activity
        if not hasattr(memory_db, 'get_recent_activity'):
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Recent activity summary is not supported by this backend"
                )],
                isError=True
            )

        days = arguments.get("days", 7)
        project = arguments.get("project")

        # Auto-detect project if not specified
        if not project:
            from ..utils.project_detection import detect_project_context
            project_info = detect_project_context()
            if project_info:
                project = project_info.get("project_path")

        activity = await memory_db.get_recent_activity(days=days, project=project)

        # Format results
        result_text = f"**Recent Activity Summary (Last {days} days)**\n\n"

        if project:
            result_text += f"**Project**: {project}\n\n"

        # Total count
        result_text += f"**Total Memories**: {activity['total_count']}\n\n"

        # Memories by type
        if activity['memories_by_type']:
            result_text += "**Breakdown by Type**:\n"
            for mem_type, count in sorted(activity['memories_by_type'].items(), key=lambda x: x[1], reverse=True):
                result_text += f"- {mem_type.replace('_', ' ').title()}: {count}\n"
            result_text += "\n"

        # Unresolved problems
        if activity['unresolved_problems']:
            result_text += f"**⚠️ Unresolved Problems ({len(activity['unresolved_problems'])})**:\n"
            for problem in activity['unresolved_problems']:
                title = _get_memory_attr(problem, 'title', 'Unknown')
                importance = _get_memory_attr(problem, 'importance', 0.5)
                summary = _get_memory_attr(problem, 'summary')
                result_text += f"- **{title}** (importance: {importance:.1f})\n"
                if summary:
                    result_text += f"  {summary}\n"
            result_text += "\n"

        # Recent memories
        if activity['recent_memories']:
            result_text += f"**Recent Memories** (showing {min(10, len(activity['recent_memories']))}):\n"
            for i, memory in enumerate(activity['recent_memories'][:10], 1):
                title = _get_memory_attr(memory, 'title', 'Unknown')
                mem_type = _get_memory_attr(memory, 'type', 'general')
                summary = _get_memory_attr(memory, 'summary')
                result_text += f"{i}. **{title}** ({mem_type})\n"
                if summary:
                    result_text += f"   {summary}\n"
            result_text += "\n"

        # Next steps suggestion
        result_text += "**💡 Next Steps**:\n"
        if activity['unresolved_problems']:
            result_text += "- Review unresolved problems and consider solutions\n"
            result_text += "- Use `get_memory(memory_id=\"...\")` for details\n"
        else:
            result_text += "- All problems have been addressed!\n"

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )

    except Exception as e:
        logger.error(f"Error in get_recent_activity: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to get recent activity: {e}"
            )],
            isError=True
        )


async def handle_search_relationships_by_context(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle search_relationships_by_context tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - scope: Filter by scope (partial/full/conditional, optional)
            - conditions: Filter by conditions (optional)
            - has_evidence: Filter by presence/absence of evidence (optional)
            - evidence: Filter by specific evidence types (optional)
            - components: Filter by components mentioned (optional)
            - temporal: Filter by temporal information (optional)
            - limit: Maximum results (default: 20)

    Returns:
        CallToolResult with formatted relationship results or error message
    """
    try:
        # Check if database supports search_relationships_by_context method
        if not hasattr(memory_db, 'search_relationships_by_context'):
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Context-based relationship search is not supported by this backend"
                )],
                isError=True
            )

        relationships = await memory_db.search_relationships_by_context(
            scope=arguments.get("scope"),
            conditions=arguments.get("conditions"),
            has_evidence=arguments.get("has_evidence"),
            evidence=arguments.get("evidence"),
            components=arguments.get("components"),
            temporal=arguments.get("temporal"),
            limit=arguments.get("limit", 20)
        )

        if not relationships:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No relationships found matching the specified context criteria"
                )]
            )

        # Format results
        result_text = f"**Found {len(relationships)} relationships matching context criteria**\n\n"

        # Show applied filters
        filters_applied = []
        if arguments.get("scope"):
            filters_applied.append(f"Scope: {arguments['scope']}")
        if arguments.get("conditions"):
            filters_applied.append(f"Conditions: {', '.join(arguments['conditions'])}")
        if arguments.get("has_evidence") is not None:
            filters_applied.append(f"Has Evidence: {arguments['has_evidence']}")
        if arguments.get("evidence"):
            filters_applied.append(f"Evidence: {', '.join(arguments['evidence'])}")
        if arguments.get("components"):
            filters_applied.append(f"Components: {', '.join(arguments['components'])}")
        if arguments.get("temporal"):
            filters_applied.append(f"Temporal: {arguments['temporal']}")

        if filters_applied:
            result_text += "**Filters Applied:**\n"
            for f in filters_applied:
                result_text += f"- {f}\n"
            result_text += "\n"

        # List relationships
        for i, rel in enumerate(relationships, 1):
            result_text += f"{i}. **{rel.type.value}**\n"
            result_text += f"   - ID: {rel.id}\n"
            result_text += f"   - From: {rel.from_memory_id}\n"
            result_text += f"   - To: {rel.to_memory_id}\n"
            result_text += f"   - Strength: {rel.properties.strength:.2f}\n"
            if rel.properties.context:
                result_text += f"   - Context: {rel.properties.context}\n"
            result_text += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=result_text)]
        )

    except Exception as e:
        logger.error(f"Error in search_relationships_by_context: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to search relationships by context: {e}"
            )],
            isError=True
        )
