"""
Intelligence MCP tool handlers for Phase 5 intelligence layer.

This module provides tool definitions and handlers for entity extraction,
pattern recognition, temporal queries, and context retrieval.
"""

from typing import Any, Dict, List
import logging
import json
from datetime import datetime

from mcp.types import Tool, TextContent, CallToolResult

from .intelligence import (
    extract_entities,
    link_entities,
    find_similar_problems,
    suggest_patterns,
    get_memory_history,
    track_entity_changes,
    get_context,
    get_project_context,
    get_session_context,
)

logger = logging.getLogger(__name__)


# Tool definitions for intelligence features
INTELLIGENCE_TOOLS = [
    Tool(
        name="find_similar_solutions",
        description="Find similar problems and their solutions using keyword/entity matching",
        inputSchema={
            "type": "object",
            "properties": {
                "problem": {
                    "type": "string",
                    "description": "Problem description to find similar solutions for"
                },
                "threshold": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7,
                    "description": "Similarity threshold (0.0-1.0)"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 10,
                    "description": "Maximum number of results"
                }
            },
            "required": ["problem"]
        }
    ),
    Tool(
        name="suggest_patterns_for_context",
        description="Get relevant patterns and solutions based on current context",
        inputSchema={
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "Current context or problem description"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Maximum number of pattern suggestions"
                }
            },
            "required": ["context"]
        }
    ),
    Tool(
        name="get_memory_history",
        description="Get complete version history for a memory showing how it evolved",
        inputSchema={
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "ID of the memory to get history for"
                }
            },
            "required": ["memory_id"]
        }
    ),
    Tool(
        name="track_entity_timeline",
        description="Track how an entity (technology, concept, etc.) has been used over time",
        inputSchema={
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity name or ID to track (e.g., 'React', 'authentication', 'PostgreSQL')"
                }
            },
            "required": ["entity"]
        }
    ),
    Tool(
        name="get_intelligent_context",
        description="Get intelligent context for a query with relevance ranking and token limiting",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query or question to get context for"
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 500,
                    "maximum": 8000,
                    "default": 4000,
                    "description": "Maximum tokens in response"
                },
                "project": {
                    "type": "string",
                    "description": "Optional project filter to limit context"
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="get_project_summary",
        description="Get comprehensive overview of a project including recent activity, decisions, and open issues",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project name or tag"
                }
            },
            "required": ["project"]
        }
    ),
    Tool(
        name="get_session_briefing",
        description="Get briefing of recent session activity (last 24 hours)",
        inputSchema={
            "type": "object",
            "properties": {
                "hours_back": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 168,
                    "default": 24,
                    "description": "Hours of history to include"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                    "description": "Maximum memories to include"
                }
            }
        }
    ),
]


# Tool handlers


async def handle_find_similar_solutions(
    backend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle find_similar_solutions tool call."""
    try:
        problem = arguments["problem"]
        threshold = arguments.get("threshold", 0.7)
        limit = arguments.get("limit", 10)

        results = await find_similar_problems(backend, problem, threshold, limit)

        if not results:
            return CallToolResult(
                content=[TextContent(type="text", text="No similar problems found.")]
            )

        # Format results
        output = f"Found {len(results)} similar problem(s):\n\n"
        for idx, result in enumerate(results, 1):
            output += f"**{idx}. {result.get('problem_title', 'Untitled')}**\n"
            output += f"Similarity: {result.get('similarity', 0):.2f}\n"
            output += f"Problem ID: {result.get('problem_id')}\n"

            solutions = result.get("solutions", [])
            if solutions:
                output += f"\nSolutions ({len(solutions)}):\n"
                for sol in solutions[:3]:  # Limit to top 3
                    if sol.get("title"):
                        output += f"- {sol['title']}\n"

            output += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=output)]
        )

    except Exception as e:
        logger.error(f"Error in find_similar_solutions: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def handle_suggest_patterns(
    backend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle suggest_patterns_for_context tool call."""
    try:
        context = arguments["context"]
        limit = arguments.get("limit", 5)

        patterns = await suggest_patterns(backend, context, limit)

        if not patterns:
            return CallToolResult(
                content=[TextContent(type="text", text="No relevant patterns found.")]
            )

        # Format patterns
        output = f"Found {len(patterns)} relevant pattern(s):\n\n"
        for idx, pattern in enumerate(patterns, 1):
            output += f"**{idx}. {pattern.name}**\n"
            output += f"Type: {pattern.pattern_type}\n"
            output += f"Confidence: {pattern.confidence:.2f}\n"
            output += f"Occurrences: {pattern.occurrences}\n"

            if pattern.entities:
                output += f"Entities: {', '.join(pattern.entities[:5])}\n"

            if pattern.description:
                desc = pattern.description[:200]
                output += f"Description: {desc}...\n" if len(pattern.description) > 200 else f"Description: {desc}\n"

            output += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=output)]
        )

    except Exception as e:
        logger.error(f"Error in suggest_patterns: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def handle_get_memory_history(
    backend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_memory_history tool call."""
    try:
        memory_id = arguments["memory_id"]

        history = await get_memory_history(backend, memory_id)

        if not history:
            return CallToolResult(
                content=[TextContent(type="text", text=f"No history found for memory {memory_id}")]
            )

        # Format history
        output = f"Version history for memory {memory_id}:\n\n"
        for version in history:
            is_current = version.get("is_current", False)
            status = " (CURRENT)" if is_current else ""
            output += f"**{version['title']}{status}**\n"
            output += f"ID: {version['id']}\n"
            output += f"Created: {version.get('created_at', 'unknown')}\n"
            output += f"Version depth: {version.get('version_depth', 0)}\n\n"

        return CallToolResult(
            content=[TextContent(type="text", text=output)]
        )

    except Exception as e:
        logger.error(f"Error in get_memory_history: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def handle_track_entity_timeline(
    backend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle track_entity_timeline tool call."""
    try:
        entity = arguments["entity"]

        timeline = await track_entity_changes(backend, entity)

        if not timeline:
            return CallToolResult(
                content=[TextContent(type="text", text=f"No timeline found for entity '{entity}'")]
            )

        # Format timeline
        output = f"Timeline for entity '{entity}' ({len(timeline)} mention(s)):\n\n"
        for change in timeline:
            new_marker = " [NEW]" if change.get("was_new_mention") else ""
            output += f"**{change.get('title', 'Untitled')}{new_marker}**\n"
            output += f"Type: {change.get('memory_type', 'unknown')}\n"
            output += f"Created: {change.get('created_at', 'unknown')}\n"
            output += f"Status: {change.get('status', 'active')}\n\n"

        return CallToolResult(
            content=[TextContent(type="text", text=output)]
        )

    except Exception as e:
        logger.error(f"Error in track_entity_timeline: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def handle_get_intelligent_context(
    backend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_intelligent_context tool call."""
    try:
        query = arguments["query"]
        max_tokens = arguments.get("max_tokens", 4000)
        project = arguments.get("project")

        result = await get_context(backend, query, max_tokens, project)

        if "error" in result:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {result['error']}")]
            )

        # Format context
        output = f"Context for query: '{query}'\n"
        output += f"Tokens: {result.get('estimated_tokens', 0)}\n"
        output += f"Sources: {result.get('total_memories', 0)} memories\n\n"

        if result.get("context"):
            output += result["context"]
        else:
            output += "No relevant context found."

        return CallToolResult(
            content=[TextContent(type="text", text=output)]
        )

    except Exception as e:
        logger.error(f"Error in get_intelligent_context: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def handle_get_project_summary(
    backend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_project_summary tool call."""
    try:
        project = arguments["project"]

        summary = await get_project_context(backend, project)

        if "error" in summary:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {summary['error']}")]
            )

        # Format summary
        output = f"Project Summary: {project}\n\n"
        output += f"Total Memories: {summary.get('total_memories', 0)}\n\n"

        recent = summary.get("recent_activity", [])
        if recent:
            output += "Recent Activity:\n"
            for activity in recent[:5]:
                output += f"- {activity.get('title', 'Untitled')} ({activity.get('type', 'unknown')})\n"
            output += "\n"

        decisions = summary.get("decisions", [])
        if decisions:
            output += "Key Decisions:\n"
            for decision in decisions[:5]:
                output += f"- {decision.get('title', 'Untitled')}\n"
            output += "\n"

        problems = summary.get("open_problems", [])
        if problems:
            output += "Open Problems:\n"
            for problem in problems:
                output += f"- {problem.get('title', 'Untitled')}\n"
            output += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=output)]
        )

    except Exception as e:
        logger.error(f"Error in get_project_summary: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


async def handle_get_session_briefing(
    backend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_session_briefing tool call."""
    try:
        hours_back = arguments.get("hours_back", 24)
        limit = arguments.get("limit", 10)

        briefing = await get_session_context(backend, hours_back, limit)

        if "error" in briefing:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {briefing['error']}")]
            )

        # Format briefing
        output = f"Session Briefing (last {hours_back} hours)\n\n"
        output += f"Recent Memories: {briefing.get('total_count', 0)}\n"

        entities = briefing.get("active_entities", [])
        if entities:
            output += f"Active Entities: {', '.join(entities[:10])}\n"

        output += "\n"

        memories = briefing.get("recent_memories", [])
        if memories:
            output += "Recent Activity:\n"
            for memory in memories:
                output += f"- {memory.get('title', 'Untitled')} ({memory.get('type', 'unknown')})\n"

        return CallToolResult(
            content=[TextContent(type="text", text=output)]
        )

    except Exception as e:
        logger.error(f"Error in get_session_briefing: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )


# Handler dispatch map
INTELLIGENCE_HANDLERS = {
    "find_similar_solutions": handle_find_similar_solutions,
    "suggest_patterns_for_context": handle_suggest_patterns,
    "get_memory_history": handle_get_memory_history,
    "track_entity_timeline": handle_track_entity_timeline,
    "get_intelligent_context": handle_get_intelligent_context,
    "get_project_summary": handle_get_project_summary,
    "get_session_briefing": handle_get_session_briefing,
}
