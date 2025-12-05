"""
Search tool handlers for the MCP server.

This module contains handlers for search operations:
- search_memories: Advanced search with filtering and tolerance modes
- recall_memories: Simplified search with optimal defaults for natural language queries
- contextual_search: Search only within related memories (scoped search)
"""

import logging
from typing import Any, Dict, Set, List

from mcp.types import CallToolResult, TextContent
from pydantic import ValidationError

from ..database import MemoryDatabase
from ..models import MemoryType, SearchQuery

logger = logging.getLogger(__name__)


async def handle_search_memories(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle search_memories tool call.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - query: Text search query (optional)
            - terms: Multiple search terms (optional)
            - memory_types: Filter by memory types (optional)
            - tags: Filter by tags (optional)
            - project_path: Filter by project path (optional)
            - min_importance: Minimum importance threshold (optional)
            - limit: Maximum results per page (default: 50)
            - offset: Number of results to skip for pagination (default: 0)
            - search_tolerance: Search mode (strict/normal/fuzzy, default: normal)
            - match_mode: Match mode for terms (any/all, default: any)
            - relationship_filter: Filter by relationship types (optional)

    Returns:
        CallToolResult with formatted search results or error message
    """
    try:
        # Build search query
        search_query: SearchQuery = SearchQuery(
            query=arguments.get("query"),
            terms=arguments.get("terms", []),
            memory_types=[MemoryType(t) for t in arguments.get("memory_types", [])],
            tags=arguments.get("tags", []),
            project_path=arguments.get("project_path"),
            min_importance=arguments.get("min_importance"),
            limit=arguments.get("limit", 50),
            offset=arguments.get("offset", 0),
            search_tolerance=arguments.get("search_tolerance", "normal"),
            match_mode=arguments.get("match_mode", "any"),
            relationship_filter=arguments.get("relationship_filter")
        )

        memories = await memory_db.search_memories(search_query)

        if not memories:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No memories found matching the search criteria."
                )]
            )

        # Format results
        results_text: str = f"Found {len(memories)} memories:\n\n"
        for i, memory in enumerate(memories, 1):
            results_text += f"**{i}. {memory.title}** (ID: {memory.id})\n"
            results_text += f"Type: {memory.type.value} | Importance: {memory.importance}\n"
            results_text += f"Tags: {', '.join(memory.tags) if memory.tags else 'None'}\n"
            if memory.summary:
                results_text += f"Summary: {memory.summary}\n"
            results_text += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in search memories: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in search memories: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except ValidationError as e:
        logger.error(f"Invalid search parameters: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid search parameters: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to search memories: {e}"
            )],
            isError=True
        )


async def handle_recall_memories(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle recall_memories tool call - convenience wrapper around search_memories.

    This provides a simplified interface optimized for natural language queries with
    best-practice defaults (fuzzy matching, relationship inclusion).

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - query: Natural language search query (optional)
            - memory_types: Filter by memory types (optional)
            - project_path: Filter by project path (optional)
            - limit: Maximum results per page (default: 20)
            - offset: Number of results to skip for pagination (default: 0)

    Returns:
        CallToolResult with enhanced formatted results or error message
    """
    try:
        # Build search query with optimal defaults
        search_query: SearchQuery = SearchQuery(
            query=arguments.get("query"),
            memory_types=[MemoryType(t) for t in arguments.get("memory_types", [])],
            project_path=arguments.get("project_path"),
            limit=arguments.get("limit", 20),
            offset=arguments.get("offset", 0),
            search_tolerance="normal",  # Always use fuzzy matching
            include_relationships=True  # Always include relationships
        )

        # Use the existing search_memories implementation
        memories = await memory_db.search_memories(search_query)

        if not memories:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="No memories found matching your query. Try:\n- Using different search terms\n- Removing filters to broaden the search\n- Checking if memories have been stored for this topic"
                )]
            )

        # Format results with enhanced context
        results_text: str = f"**Found {len(memories)} relevant memories:**\n\n"

        for i, memory in enumerate(memories, 1):
            results_text += f"**{i}. {memory.title}** (ID: {memory.id})\n"
            results_text += f"Type: {memory.type.value} | Importance: {memory.importance}\n"

            # Add match quality if available
            if hasattr(memory, 'match_info') and memory.match_info:
                match_info = memory.match_info
                if isinstance(match_info, dict):
                    quality = match_info.get('match_quality', 'unknown')
                    matched_fields = match_info.get('matched_fields', [])
                    results_text += f"Match: {quality} quality"
                    if matched_fields:
                        results_text += f" (in {', '.join(matched_fields)})"
                    results_text += "\n"

            # Add context summary if available
            if hasattr(memory, 'context_summary') and memory.context_summary:
                results_text += f"Context: {memory.context_summary}\n"

            # Add summary or content snippet
            if memory.summary:
                results_text += f"Summary: {memory.summary}\n"
            elif memory.content:
                # Show first 150 chars of content
                snippet = memory.content[:150]
                if len(memory.content) > 150:
                    snippet += "..."
                results_text += f"Content: {snippet}\n"

            # Add tags
            if memory.tags:
                results_text += f"Tags: {', '.join(memory.tags)}\n"

            # Add relationships if available
            if hasattr(memory, 'relationships') and memory.relationships:
                rel_summary = []
                for rel_type, related_titles in memory.relationships.items():
                    if related_titles:
                        rel_summary.append(f"{rel_type}: {len(related_titles)} memories")
                if rel_summary:
                    results_text += f"Relationships: {', '.join(rel_summary)}\n"

            results_text += "\n"

        # Add helpful tip at the end
        results_text += "\n💡 **Next steps:**\n"
        results_text += "- Use `get_memory(memory_id=\"...\")` to see full details\n"
        results_text += "- Use `get_related_memories(memory_id=\"...\")` to explore connections\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in recall memories: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in recall memories: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except ValidationError as e:
        logger.error(f"Invalid search parameters: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid search parameters: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to recall memories: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to recall memories: {e}"
            )],
            isError=True
        )


async def handle_contextual_search(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle contextual_search tool call.

    Search only within the context of a given memory by first finding
    all related memories, then searching only within that related set.
    This provides semantic scoping without embeddings.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: ID of memory to use as context root (required)
            - query: Text search query (required)
            - max_depth: Maximum relationship traversal depth (default: 2)

    Returns:
        CallToolResult with scoped search results or error message
    """
    try:
        # Validate required parameters
        if "memory_id" not in arguments:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: 'memory_id' parameter is required"
                )],
                isError=True
            )

        if "query" not in arguments:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: 'query' parameter is required"
                )],
                isError=True
            )

        memory_id: str = arguments["memory_id"]
        query: str = arguments["query"]
        max_depth: int = arguments.get("max_depth", 2)

        # Phase 1: Find all memories related to the context memory
        related = await memory_db.get_related_memories(
            memory_id=memory_id,
            relationship_types=None,  # All relationship types
            max_depth=max_depth
        )

        if not related:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No related memories found for context: {memory_id}"
                )]
            )

        # Extract IDs of related memories to scope the search
        related_ids: Set[str] = {mem.id for mem, _ in related}

        # Phase 2: Search only within the related memories
        # Get all memories from search, then filter by related IDs
        search_query: SearchQuery = SearchQuery(
            query=query,
            limit=100,  # Get more results to filter
            search_tolerance="normal"
        )

        all_matches: List = await memory_db.search_memories(search_query)

        # Filter to only include memories that are in the related set
        contextual_matches: List = [
            mem for mem in all_matches
            if mem.id in related_ids
        ]

        if not contextual_matches:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No matches found for '{query}' within the context of {memory_id}"
                )]
            )

        # Format results
        results_text: str = f"**Contextual Search Results:**\n\n"
        results_text += f"Context: {memory_id}\n"
        results_text += f"Query: '{query}'\n"
        results_text += f"Searched within {len(related_ids)} related memories\n"
        results_text += f"Found {len(contextual_matches)} matches:\n\n"

        for i, memory in enumerate(contextual_matches, 1):
            results_text += f"{i}. **{memory.title}** (ID: {memory.id})\n"
            results_text += f"   Type: {memory.type.value} | Importance: {memory.importance}\n"

            # Add summary or content snippet
            if memory.summary:
                results_text += f"   Summary: {memory.summary}\n"
            elif memory.content:
                snippet = memory.content[:150]
                if len(memory.content) > 150:
                    snippet += "..."
                results_text += f"   Content: {snippet}\n"

            # Add tags
            if memory.tags:
                results_text += f"   Tags: {', '.join(memory.tags)}\n"

            results_text += "\n"

        results_text += f"\n💡 Use `get_memory(memory_id=\"...\")` to see full details\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in contextual search: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in contextual search: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to perform contextual search: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to perform contextual search: {e}"
            )],
            isError=True
        )
