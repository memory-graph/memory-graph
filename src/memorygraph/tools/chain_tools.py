"""
Chain tool handlers for the MCP server.

This module contains handlers for traversing relationship chains:
- find_chain: Auto-traverse SOLVES/CAUSES/DEPENDS_ON chains
- trace_dependencies: Follow DEPENDS_ON/REQUIRES chains specifically
"""

import logging
from typing import Any, Dict, Set, List, Tuple
from collections import deque

from mcp.types import CallToolResult, TextContent

from ..database import MemoryDatabase
from ..models import RelationshipType, Memory, Relationship

logger = logging.getLogger(__name__)


async def handle_find_chain(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle find_chain tool call.

    Automatically traverses relationship chains from a starting memory,
    following the specified relationship type up to max_depth.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: Starting memory ID (required)
            - relationship_type: Type of chain to follow (required)
            - max_depth: Maximum traversal depth (default: 3)

    Returns:
        CallToolResult with discovered chain or error message
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

        if "relationship_type" not in arguments:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: 'relationship_type' parameter is required"
                )],
                isError=True
            )

        memory_id: str = arguments["memory_id"]
        relationship_type: RelationshipType = RelationshipType(arguments["relationship_type"])
        max_depth: int = arguments.get("max_depth", 3)

        # Validate max_depth
        if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 10:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: 'max_depth' must be an integer between 1 and 10"
                )],
                isError=True
            )

        # BFS traversal to find chain
        chain: List[Tuple[Memory, Relationship]] = []
        visited: Set[str] = {memory_id}  # Track visited to avoid cycles
        queue: deque = deque([(memory_id, 0)])  # (memory_id, depth)
        cycles_detected: int = 0

        while queue:
            current_id, depth = queue.popleft()

            if depth >= max_depth:
                continue

            # Get related memories for this node
            related = await memory_db.get_related_memories(
                memory_id=current_id,
                relationship_types=[relationship_type],
                max_depth=1  # Get immediate connections only
            )

            for related_memory, relationship in related:
                if related_memory.id not in visited:
                    visited.add(related_memory.id)
                    chain.append((related_memory, relationship))
                    queue.append((related_memory.id, depth + 1))
                else:
                    # Cycle detected
                    cycles_detected += 1

        if not chain:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No {relationship_type.value} chain found starting from: {memory_id}"
                )]
            )

        # Format results
        results_text: str = f"**Relationship Chain ({relationship_type.value}):**\n\n"
        results_text += f"Starting from: {memory_id}\n"
        results_text += f"Chain depth: {max_depth}\n"
        results_text += f"Found {len(chain)} connections:\n"
        if cycles_detected > 0:
            results_text += f"⚠️  Detected {cycles_detected} cycle(s) (skipped to prevent infinite loops)\n"
        results_text += "\n"

        for i, (memory, relationship) in enumerate(chain, 1):
            results_text += f"{i}. **{memory.title}** (ID: {memory.id})\n"
            results_text += f"   Type: {memory.type.value}\n"
            results_text += f"   Relationship: {relationship.type.value} (strength: {relationship.properties.strength:.2f})\n"
            results_text += f"   Importance: {memory.importance}\n"
            if memory.summary:
                results_text += f"   Summary: {memory.summary}\n"
            results_text += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in find chain: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in find chain: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to find chain: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to find chain: {e}"
            )],
            isError=True
        )


async def handle_trace_dependencies(
    memory_db: MemoryDatabase,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle trace_dependencies tool call.

    Traces all dependencies for a given memory by following DEPENDS_ON
    and REQUIRES relationships to build a complete dependency tree.

    Args:
        memory_db: Database instance for memory operations
        arguments: Tool arguments from MCP call containing:
            - memory_id: Memory ID to trace dependencies for (required)

    Returns:
        CallToolResult with dependency tree or error message
    """
    try:
        # Validate required parameter
        if "memory_id" not in arguments:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="Error: 'memory_id' parameter is required"
                )],
                isError=True
            )

        memory_id: str = arguments["memory_id"]

        # Follow DEPENDS_ON and REQUIRES relationships
        dependency_types: List[RelationshipType] = [RelationshipType.DEPENDS_ON, RelationshipType.REQUIRES]

        # BFS traversal to build dependency tree
        dependencies: List[Tuple[Memory, Relationship, int]] = []  # (memory, relationship, depth)
        visited: Set[str] = {memory_id}  # Track visited to detect cycles
        queue: deque = deque([(memory_id, 0)])  # (memory_id, depth)
        circular_detected: bool = False
        cycles_count: int = 0

        while queue:
            current_id, depth = queue.popleft()

            # Get dependencies for this node
            related = await memory_db.get_related_memories(
                memory_id=current_id,
                relationship_types=dependency_types,
                max_depth=1  # Get immediate connections only
            )

            for related_memory, relationship in related:
                if related_memory.id in visited:
                    # Circular dependency detected
                    circular_detected = True
                    cycles_count += 1
                    dependencies.append((related_memory, relationship, depth + 1))
                    continue

                visited.add(related_memory.id)
                dependencies.append((related_memory, relationship, depth + 1))
                queue.append((related_memory.id, depth + 1))

        if not dependencies:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"No dependencies found for memory: {memory_id}"
                )]
            )

        # Format results
        results_text: str = "**Dependency Tree:**\n\n"
        results_text += f"Root: {memory_id}\n"
        results_text += f"Total dependencies: {len(dependencies)}\n"

        if circular_detected:
            results_text += f"\n⚠️  **Circular dependency detected** ({cycles_count} cycle(s))\n"

        results_text += "\n"

        # Group by depth
        by_depth: Dict[int, List[Tuple[Memory, Relationship]]] = {}
        for memory, relationship, depth in dependencies:
            if depth not in by_depth:
                by_depth[depth] = []
            by_depth[depth].append((memory, relationship))

        # Display by depth
        for depth in sorted(by_depth.keys()):
            results_text += f"**Level {depth}:**\n"
            for memory, relationship in by_depth[depth]:
                indent = "  " * depth
                results_text += f"{indent}- **{memory.title}** (ID: {memory.id})\n"
                results_text += f"{indent}  Relationship: {relationship.type.value}\n"
                results_text += f"{indent}  Type: {memory.type.value} | Importance: {memory.importance}\n"
            results_text += "\n"

        return CallToolResult(
            content=[TextContent(type="text", text=results_text)]
        )

    except ValueError as e:
        logger.error(f"Invalid value in trace dependencies: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Invalid value: {e}"
            )],
            isError=True
        )
    except KeyError as e:
        logger.error(f"Missing required field in trace dependencies: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Missing required field: {e}"
            )],
            isError=True
        )
    except Exception as e:
        logger.error(f"Failed to trace dependencies: {e}")
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Failed to trace dependencies: {e}"
            )],
            isError=True
        )
