"""
MCP Tool Handlers for Proactive Features and Advanced Analytics.

This module provides tool definitions and handlers for Phase 7's
proactive functionality.
"""

from typing import Any, Dict, List
import logging
import json
from datetime import datetime

from mcp.types import Tool, TextContent, CallToolResult

from .backends.base import GraphBackend
from .proactive.session_briefing import (
    generate_session_briefing,
    get_session_briefing_resource,
)
from .proactive.predictive import (
    predict_needs,
    warn_potential_issues,
    suggest_related_context,
)
from .proactive.outcome_learning import (
    record_outcome,
    update_pattern_effectiveness,
    calculate_effectiveness_score,
)
from .analytics.advanced_queries import (
    get_memory_graph_visualization,
    analyze_solution_similarity,
    predict_solution_effectiveness,
    recommend_learning_paths,
    identify_knowledge_gaps,
    track_memory_roi,
)

logger = logging.getLogger(__name__)


# Tool definitions for proactive features
PROACTIVE_TOOLS = [
    Tool(
        name="get_session_briefing",
        description="Get automatic session briefing for a project with recent activity, issues, and recommendations",
        inputSchema={
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Project directory path"
                },
                "recency_days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                    "default": 7,
                    "description": "How many days back to look for recent activity"
                },
                "verbosity": {
                    "type": "string",
                    "enum": ["minimal", "standard", "detailed"],
                    "default": "standard",
                    "description": "Verbosity level of briefing"
                }
            },
            "required": ["project_dir"]
        }
    ),
    Tool(
        name="get_suggestions",
        description="Get proactive suggestions based on current work context",
        inputSchema={
            "type": "object",
            "properties": {
                "current_context": {
                    "type": "string",
                    "description": "Current work context (e.g., file content, task description)"
                },
                "max_suggestions": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Maximum number of suggestions to return"
                },
                "min_relevance": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3,
                    "description": "Minimum relevance score threshold"
                }
            },
            "required": ["current_context"]
        }
    ),
    Tool(
        name="check_for_issues",
        description="Check for potential issues based on current context (deprecated approaches, known problems)",
        inputSchema={
            "type": "object",
            "properties": {
                "current_context": {
                    "type": "string",
                    "description": "Current work context to check for issues"
                },
                "severity_threshold": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                    "description": "Minimum severity level to report"
                }
            },
            "required": ["current_context"]
        }
    ),
    Tool(
        name="suggest_related_memories",
        description="Suggest related context for a memory ('You might also want to know...')",
        inputSchema={
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "Memory ID to find related context for"
                },
                "max_suggestions": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Maximum number of suggestions"
                }
            },
            "required": ["memory_id"]
        }
    ),
    Tool(
        name="record_outcome",
        description="Record the outcome of using a memory/solution (success or failure)",
        inputSchema={
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "ID of memory that was used"
                },
                "outcome_description": {
                    "type": "string",
                    "description": "Description of what happened"
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether the outcome was successful"
                },
                "context": {
                    "type": "object",
                    "description": "Additional context about the outcome"
                },
                "impact": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 1.0,
                    "description": "How significant this outcome was (0.0-1.0)"
                }
            },
            "required": ["memory_id", "outcome_description", "success"]
        }
    ),
    Tool(
        name="get_graph_visualization",
        description="Get graph visualization data for D3.js or vis.js",
        inputSchema={
            "type": "object",
            "properties": {
                "center_memory_id": {
                    "type": "string",
                    "description": "Optional center memory (omit for full graph)"
                },
                "depth": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 2,
                    "description": "Depth to traverse from center"
                },
                "max_nodes": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 500,
                    "default": 100,
                    "description": "Maximum nodes to return"
                },
                "include_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter to specific memory types"
                }
            }
        }
    ),
    Tool(
        name="find_similar_solutions",
        description="Find solutions similar to a given solution",
        inputSchema={
            "type": "object",
            "properties": {
                "solution_id": {
                    "type": "string",
                    "description": "Solution to find similar solutions for"
                },
                "top_k": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Number of similar solutions to return"
                },
                "min_similarity": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3,
                    "description": "Minimum similarity threshold"
                }
            },
            "required": ["solution_id"]
        }
    ),
    Tool(
        name="predict_solution_effectiveness",
        description="Predict how effective a solution will be for a problem",
        inputSchema={
            "type": "object",
            "properties": {
                "problem_description": {
                    "type": "string",
                    "description": "Description of the problem"
                },
                "solution_id": {
                    "type": "string",
                    "description": "Solution being considered"
                }
            },
            "required": ["problem_description", "solution_id"]
        }
    ),
    Tool(
        name="recommend_learning_paths",
        description="Get recommended learning paths for a topic",
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to learn about"
                },
                "max_paths": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 3,
                    "description": "Maximum number of paths to return"
                }
            },
            "required": ["topic"]
        }
    ),
    Tool(
        name="identify_knowledge_gaps",
        description="Identify knowledge gaps in the memory graph",
        inputSchema={
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Optional project filter"
                },
                "min_gap_severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                    "description": "Minimum severity to report"
                }
            }
        }
    ),
    Tool(
        name="track_memory_roi",
        description="Track return on investment for a memory",
        inputSchema={
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "string",
                    "description": "Memory to track ROI for"
                }
            },
            "required": ["memory_id"]
        }
    ),
]


# Tool handlers

async def handle_get_session_briefing(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_session_briefing tool call."""
    try:
        project_dir = arguments["project_dir"]
        recency_days = arguments.get("recency_days", 7)
        verbosity = arguments.get("verbosity", "standard")

        briefing = await generate_session_briefing(
            backend,
            project_dir,
            recency_days=recency_days,
        )

        if not briefing:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Could not detect project at {project_dir}"
                )],
                isError=True
            )

        formatted_text = briefing.format_as_text(verbosity)

        return CallToolResult(
            content=[TextContent(
                type="text",
                text=formatted_text
            )]
        )

    except Exception as e:
        logger.error(f"Error in get_session_briefing: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error generating session briefing: {str(e)}"
            )],
            isError=True
        )


async def handle_get_suggestions(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_suggestions tool call."""
    try:
        current_context = arguments["current_context"]
        max_suggestions = arguments.get("max_suggestions", 5)
        min_relevance = arguments.get("min_relevance", 0.3)

        suggestions = await predict_needs(
            backend,
            current_context,
            max_suggestions=max_suggestions,
            min_relevance=min_relevance,
        )

        if not suggestions:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No relevant suggestions found for current context."
                )]
            )

        # Format suggestions
        lines = ["# Proactive Suggestions\n"]
        for idx, suggestion in enumerate(suggestions, 1):
            lines.append(f"\n## {idx}. {suggestion.title}")
            lines.append(f"**Type:** {suggestion.suggestion_type}")
            lines.append(f"**Relevance:** {suggestion.relevance_score:.2%}")
            lines.append(f"**Reason:** {suggestion.reason}")
            lines.append(f"\n{suggestion.description}")
            if suggestion.effectiveness:
                lines.append(f"\n**Effectiveness:** {suggestion.effectiveness:.2%}")
            if suggestion.tags:
                lines.append(f"**Tags:** {', '.join(suggestion.tags)}")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(lines)
            )]
        )

    except Exception as e:
        logger.error(f"Error in get_suggestions: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error getting suggestions: {str(e)}"
            )],
            isError=True
        )


async def handle_check_for_issues(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle check_for_issues tool call."""
    try:
        current_context = arguments["current_context"]
        severity_threshold = arguments.get("severity_threshold", "medium")

        warnings = await warn_potential_issues(
            backend,
            current_context,
            severity_threshold=severity_threshold,
        )

        if not warnings:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No potential issues detected. All clear!"
                )]
            )

        # Format warnings
        lines = ["# Potential Issues\n"]
        for idx, warning in enumerate(warnings, 1):
            severity_icon = {"low": "ℹ️", "medium": "⚠️", "high": "🚨"}
            icon = severity_icon.get(warning.severity, "⚠️")

            lines.append(f"\n## {icon} {idx}. {warning.title}")
            lines.append(f"**Severity:** {warning.severity.upper()}")
            lines.append(f"\n{warning.description}")

            if warning.mitigation:
                lines.append(f"\n**Mitigation:** {warning.mitigation}")

            if warning.evidence:
                lines.append(f"\n**Evidence:** {len(warning.evidence)} related memory/memories")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(lines)
            )]
        )

    except Exception as e:
        logger.error(f"Error in check_for_issues: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error checking for issues: {str(e)}"
            )],
            isError=True
        )


async def handle_suggest_related_memories(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle suggest_related_memories tool call."""
    try:
        memory_id = arguments["memory_id"]
        max_suggestions = arguments.get("max_suggestions", 5)

        suggestions = await suggest_related_context(
            backend,
            memory_id,
            max_suggestions=max_suggestions,
        )

        if not suggestions:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No related memories found for {memory_id}"
                )]
            )

        # Format suggestions
        lines = ["# You Might Also Want to Know\n"]
        for idx, suggestion in enumerate(suggestions, 1):
            lines.append(f"\n## {idx}. {suggestion.title}")
            lines.append(f"**Reason:** {suggestion.reason}")
            lines.append(f"**Relevance:** {suggestion.relevance_score:.2%}")
            lines.append(f"\n{suggestion.description}")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(lines)
            )]
        )

    except Exception as e:
        logger.error(f"Error in suggest_related_memories: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error suggesting related memories: {str(e)}"
            )],
            isError=True
        )


async def handle_record_outcome(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle record_outcome tool call."""
    try:
        memory_id = arguments["memory_id"]
        outcome_description = arguments["outcome_description"]
        success = arguments["success"]
        context = arguments.get("context")
        impact = arguments.get("impact", 1.0)

        result = await record_outcome(
            backend,
            memory_id,
            outcome_description,
            success,
            context=context,
            impact=impact,
        )

        if result:
            status = "successful" if success else "unsuccessful"
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Outcome recorded: {status} use of memory {memory_id}\n"
                         f"Description: {outcome_description}\n"
                         f"Effectiveness scores have been updated."
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to record outcome for memory {memory_id}"
                )],
                isError=True
            )

    except Exception as e:
        logger.error(f"Error in record_outcome: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error recording outcome: {str(e)}"
            )],
            isError=True
        )


async def handle_get_graph_visualization(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle get_graph_visualization tool call."""
    try:
        center_memory_id = arguments.get("center_memory_id")
        depth = arguments.get("depth", 2)
        max_nodes = arguments.get("max_nodes", 100)
        include_types = arguments.get("include_types")

        viz_data = await get_memory_graph_visualization(
            backend,
            center_memory_id=center_memory_id,
            depth=depth,
            max_nodes=max_nodes,
            include_types=include_types,
        )

        # Return as JSON for visualization
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(viz_data.model_dump(), indent=2)
            )]
        )

    except Exception as e:
        logger.error(f"Error in get_graph_visualization: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error generating visualization: {str(e)}"
            )],
            isError=True
        )


async def handle_find_similar_solutions(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle find_similar_solutions tool call."""
    try:
        solution_id = arguments["solution_id"]
        top_k = arguments.get("top_k", 5)
        min_similarity = arguments.get("min_similarity", 0.3)

        similar = await analyze_solution_similarity(
            backend,
            solution_id,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        if not similar:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No similar solutions found for {solution_id}"
                )]
            )

        # Format results
        lines = [f"# Similar Solutions to {solution_id}\n"]
        for idx, sol in enumerate(similar, 1):
            lines.append(f"\n## {idx}. {sol.title}")
            lines.append(f"**Similarity:** {sol.similarity_score:.2%}")
            lines.append(f"\n{sol.description}")

            if sol.shared_entities:
                lines.append(f"\n**Shared entities:** {', '.join(sol.shared_entities[:5])}")
            if sol.shared_tags:
                lines.append(f"**Shared tags:** {', '.join(sol.shared_tags[:5])}")
            if sol.effectiveness:
                lines.append(f"**Effectiveness:** {sol.effectiveness:.2%}")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(lines)
            )]
        )

    except Exception as e:
        logger.error(f"Error in find_similar_solutions: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error finding similar solutions: {str(e)}"
            )],
            isError=True
        )


async def handle_predict_solution_effectiveness(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle predict_solution_effectiveness tool call."""
    try:
        problem_description = arguments["problem_description"]
        solution_id = arguments["solution_id"]

        effectiveness = await predict_solution_effectiveness(
            backend,
            problem_description,
            solution_id,
        )

        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Predicted effectiveness of solution {solution_id}: {effectiveness:.2%}\n\n"
                     f"This prediction is based on historical effectiveness and entity matching."
            )]
        )

    except Exception as e:
        logger.error(f"Error in predict_solution_effectiveness: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error predicting effectiveness: {str(e)}"
            )],
            isError=True
        )


async def handle_recommend_learning_paths(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle recommend_learning_paths tool call."""
    try:
        topic = arguments["topic"]
        max_paths = arguments.get("max_paths", 3)

        paths = await recommend_learning_paths(
            backend,
            topic,
            max_paths=max_paths,
        )

        if not paths:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No learning paths found for topic: {topic}"
                )]
            )

        # Format paths
        lines = [f"# Learning Paths for {topic}\n"]
        for path_idx, path in enumerate(paths, 1):
            lines.append(f"\n## Path {path_idx} ({path.total_memories} memories, value: {path.estimated_value:.2%})")

            for step in path.steps:
                lines.append(f"\n{step['step']}. **{step['title']}** ({step['type']})")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(lines)
            )]
        )

    except Exception as e:
        logger.error(f"Error in recommend_learning_paths: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error recommending learning paths: {str(e)}"
            )],
            isError=True
        )


async def handle_identify_knowledge_gaps(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle identify_knowledge_gaps tool call."""
    try:
        project = arguments.get("project")
        min_gap_severity = arguments.get("min_gap_severity", "medium")

        gaps = await identify_knowledge_gaps(
            backend,
            project=project,
            min_gap_severity=min_gap_severity,
        )

        if not gaps:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No knowledge gaps identified. Your knowledge graph is comprehensive!"
                )]
            )

        # Format gaps
        lines = ["# Knowledge Gaps\n"]
        for idx, gap in enumerate(gaps, 1):
            severity_icon = {"low": "ℹ️", "medium": "⚠️", "high": "🚨"}
            icon = severity_icon.get(gap.severity, "⚠️")

            lines.append(f"\n## {icon} {idx}. {gap.topic}")
            lines.append(f"**Severity:** {gap.severity.upper()}")
            lines.append(f"\n{gap.description}")

            if gap.suggestions:
                lines.append(f"\n**Suggestions:**")
                for suggestion in gap.suggestions:
                    lines.append(f"- {suggestion}")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(lines)
            )]
        )

    except Exception as e:
        logger.error(f"Error in identify_knowledge_gaps: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error identifying knowledge gaps: {str(e)}"
            )],
            isError=True
        )


async def handle_track_memory_roi(
    backend: GraphBackend,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle track_memory_roi tool call."""
    try:
        memory_id = arguments["memory_id"]

        roi = await track_memory_roi(backend, memory_id)

        if not roi:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Memory {memory_id} not found"
                )],
                isError=True
            )

        # Format ROI
        lines = [
            f"# ROI Report for {roi.title}\n",
            f"**Memory ID:** {roi.memory_id}",
            f"**Created:** {roi.creation_date.strftime('%Y-%m-%d')}",
            f"**Times Accessed:** {roi.times_accessed}",
            f"**Times Helpful:** {roi.times_helpful}",
            f"**Success Rate:** {roi.success_rate:.2%}",
            f"**Value Score:** {roi.value_score:.2%}",
        ]

        if roi.last_used:
            days_ago = (datetime.now() - roi.last_used).days
            lines.append(f"**Last Used:** {days_ago} days ago")

        return CallToolResult(
            content=[TextContent(
                type="text",
                text="\n".join(lines)
            )]
        )

    except Exception as e:
        logger.error(f"Error in track_memory_roi: {e}", exc_info=True)
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Error tracking ROI: {str(e)}"
            )],
            isError=True
        )


# Export handler mapping
PROACTIVE_TOOL_HANDLERS = {
    "get_session_briefing": handle_get_session_briefing,
    "get_suggestions": handle_get_suggestions,
    "check_for_issues": handle_check_for_issues,
    "suggest_related_memories": handle_suggest_related_memories,
    "record_outcome": handle_record_outcome,
    "get_graph_visualization": handle_get_graph_visualization,
    "find_similar_solutions": handle_find_similar_solutions,
    "predict_solution_effectiveness": handle_predict_solution_effectiveness,
    "recommend_learning_paths": handle_recommend_learning_paths,
    "identify_knowledge_gaps": handle_identify_knowledge_gaps,
    "track_memory_roi": handle_track_memory_roi,
}
