"""
Browse tool handlers for the MCP server.

This module contains handlers for browsing and discovering memories:
- browse_memory_types: List all memory types with counts and percentages
- browse_by_project: Navigate memories scoped to specific project paths
- browse_domains: High-level categorization by auto-inferred domains
"""

import logging
from typing import Any, Dict, List
from collections import Counter

from mcp.types import CallToolResult, TextContent

from ..database import MemoryDatabase
from ..models import SearchQuery, MemoryType

logger = logging.getLogger(__name__)

# Constants for browse operations
MIN_DOMAIN_SIZE = 3  # Minimum memories required to be considered a domain
MAX_MEMORIES_DISPLAY = 20  # Maximum memories to display in results
MAX_MEMORIES_ANALYZE = 1000  # Maximum memories to analyze for domain clustering
TOP_RELATED_TAGS = 3  # Number of top related tags to show for domains


async def handle_browse_memory_types(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle browse_memory_types tool call.

    Lists all memory types with their counts and percentages, enabling
    high-level discovery of what types of information are stored.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call (no arguments required)

    Returns:
        CallToolResult with formatted type statistics or error message
    """
    try:
        # Get backend and execute query to count memories by type
        backend = await memory_db.get_backend()

        # Query to get counts by type
        query = """
        MATCH (m:Memory)
        RETURN m.type as type, count(m) as count
        ORDER BY count DESC
        """

        results: List[Dict[str, Any]] = await backend.execute_query(query)

        if not results:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No memories found in the database."
                )]
            )

        # Calculate total and percentages
        total: int = sum(r["count"] for r in results)

        # Format results
        results_text: str = "**Memory Types Overview:**\n\n"

        for result in results:
            memory_type: str = result["type"]
            count: int = result["count"]
            percentage: float = (count / total * 100) if total > 0 else 0
            results_text += f"- **{memory_type}**: {count} ({percentage:.1f}%)\n"

        results_text += f"\n**Total:** {total} memories\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in browse memory types: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in browse memory types: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to browse memory types: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to browse memory types: {e}"
            )],
            isError=True
        )


async def handle_browse_by_project(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle browse_by_project tool call.

    Lists memories scoped to a specific project path, with support for
    fuzzy matching of project paths.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - project_path: Project identifier to filter by (required)

    Returns:
        CallToolResult with filtered memories or error message
    """
    try:
        # Validate required parameter
        if "project_path" not in arguments:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: 'project_path' parameter is required"
                )],
                isError=True
            )

        project_path: str = arguments["project_path"]

        # Use search with project_path filter
        search_query: SearchQuery = SearchQuery(
            project_path=project_path,
            limit=MAX_MEMORIES_ANALYZE  # Get up to max memories for project overview
        )

        memories = await memory_db.search_memories(search_query)

        if not memories:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No memories found for project: {project_path}"
                )]
            )

        # Calculate statistics
        type_counts: Counter = Counter(m.type.value for m in memories)

        # Format results
        results_text: str = f"**Project: {project_path}**\n\n"
        results_text += f"**Total memories:** {len(memories)}\n\n"

        # Show type breakdown
        results_text += "**By Type:**\n"
        for memory_type, count in type_counts.most_common():
            results_text += f"- {memory_type}: {count}\n"

        results_text += "\n**Memories:**\n\n"

        # List memories
        for i, memory in enumerate(memories[:MAX_MEMORIES_DISPLAY], 1):
            results_text += f"{i}. **{memory.title}** (ID: {memory.id})\n"
            results_text += f"   Type: {memory.type.value} | Importance: {memory.importance}\n"
            if memory.tags:
                results_text += f"   Tags: {', '.join(memory.tags)}\n"
            results_text += "\n"

        if len(memories) > MAX_MEMORIES_DISPLAY:
            results_text += f"\n... and {len(memories) - MAX_MEMORIES_DISPLAY} more memories\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in browse by project: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in browse by project: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to browse by project: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to browse by project: {e}"
            )],
            isError=True
        )


async def handle_browse_domains(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle browse_domains tool call.

    Lists high-level domains auto-inferred from tags and content clustering.
    Domains are clusters of related memories identified by common tags.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call (no arguments required)

    Returns:
        CallToolResult with discovered domains or error message
    """
    try:
        # Get all memories to analyze tags
        search_query: SearchQuery = SearchQuery(
            limit=MAX_MEMORIES_ANALYZE
        )

        memories: List = await memory_db.search_memories(search_query)

        if not memories:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No memories found in the database."
                )]
            )

        # Cluster by tags to identify domains
        tag_memory_map: Dict[str, List[str]] = {}  # tag -> list of memory IDs
        tag_counts: Counter = Counter()

        # Pre-compute tag co-occurrence matrix to avoid N+1 loop
        tag_cooccurrence: Dict[str, Counter] = {}  # tag -> Counter of co-occurring tags

        for memory in memories:
            if memory.tags:
                # Normalize tags once per memory
                normalized_tags: set[str] = {tag.lower() for tag in memory.tags}

                for tag in normalized_tags:
                    tag_counts[tag] += 1
                    if tag not in tag_memory_map:
                        tag_memory_map[tag] = []
                    tag_memory_map[tag].append(memory.id)

                    # Track co-occurring tags
                    if tag not in tag_cooccurrence:
                        tag_cooccurrence[tag] = Counter()
                    for other_tag in normalized_tags:
                        if other_tag != tag:
                            tag_cooccurrence[tag][other_tag] += 1

        # Identify dominant tags as domains (tags that appear in MIN_DOMAIN_SIZE+ memories)
        domains: List[Dict[str, Any]] = []
        for tag, count in tag_counts.most_common():
            if count >= MIN_DOMAIN_SIZE:
                # Get top related tags from pre-computed co-occurrence matrix
                related_tags: Counter = tag_cooccurrence.get(tag, Counter())
                top_related: List[str] = [t for t, _ in related_tags.most_common(TOP_RELATED_TAGS)]

                domains.append({
                    "name": tag.capitalize(),
                    "memory_count": count,
                    "tags": [tag] + top_related,
                    "memory_ids": tag_memory_map[tag]
                })

        if not domains:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No domains identified. Add more memories with tags to enable domain clustering."
                )]
            )

        # Format results
        results_text: str = "**Discovered Domains:**\n\n"
        results_text += f"Found {len(domains)} domains based on tag clustering.\n\n"

        for i, domain in enumerate(domains[:10], 1):  # Show top 10 domains
            results_text += f"{i}. **{domain['name']}**\n"
            results_text += f"   Memories: {domain['memory_count']}\n"
            results_text += f"   Related tags: {', '.join(domain['tags'])}\n"
            results_text += "\n"

        if len(domains) > 10:
            results_text += f"\n... and {len(domains) - 10} more domains\n"

        results_text += "\n💡 Use `browse_by_project` or `search_memories` with tags to explore each domain.\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in browse domains: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in browse domains: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to browse domains: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to browse domains: {e}"
            )],
            isError=True
        )
