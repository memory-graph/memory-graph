"""
Advanced MCP tool handlers for relationship management and graph analytics.

This module provides tool definitions and handlers for Phase 4's
advanced relationship functionality.
"""

from typing import Any, Dict, List
import logging
import json

from mcp.types import Tool, TextContent, CallToolResult

from .models import (
    RelationshipType,
    MemoryType,
    Memory,
)
from .relationships import relationship_manager, RelationshipCategory
from .graph_analytics import graph_analyzer

logger = logging.getLogger(__name__)


# Tool definitions for advanced relationship features
ADVANCED_RELATIONSHIP_TOOLS = [
    Tool(
        name="find_memory_path",
        description="Find the shortest path between two memories through relationships",
        inputSchema={
            "type": "object",
            "properties": {
                "from_memory_id": {
                    "type": "string",
                    "description": "Starting memory ID"
                },
                "to_memory_id": {
                    "type": "string",
                    "description": "Target memory ID"
                },
                "max_depth": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                    "description": "Maximum path length to search"
                },
                "relationship_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [t.value for t in RelationshipType]
                    },
                    "description": "Filter by specific relationship types"
                }
            },
            "required": ["from_memory_id", "to_memory_id"]
        }
    ),
    Tool(
        name="analyze_memory_clusters",
        description="Detect clusters of densely connected memories",
        inputSchema={
            "type": "object",
            "properties": {
                "min_cluster_size": {
                    "type": "integer",
                    "minimum": 2,
                    "default": 3,
                    "description": "Minimum memories per cluster"
                },
                "min_density": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3,
                    "description": "Minimum cluster density (0.0-1.0)"
                }
            }
        }
    ),
    Tool(
        name="find_bridge_memories",
        description="Find memories that connect different clusters (knowledge bridges)",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="suggest_relationship_type",
        description="Get intelligent suggestions for relationship types between two memories",
        inputSchema={
            "type": "object",
            "properties": {
                "from_memory_id": {
                    "type": "string",
                    "description": "Source memory ID"
                },
                "to_memory_id": {
                    "type": "string",
                    "description": "Target memory ID"
                }
            },
            "required": ["from_memory_id", "to_memory_id"]
        }
    ),
    Tool(
        name="reinforce_relationship",
        description="Reinforce a relationship based on successful usage",
        inputSchema={
            "type": "object",
            "properties": {
                "from_memory_id": {
                    "type": "string",
                    "description": "Source memory ID"
                },
                "to_memory_id": {
                    "type": "string",
                    "description": "Target memory ID"
                },
                "success": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether this was a successful use"
                }
            },
            "required": ["from_memory_id", "to_memory_id"]
        }
    ),
    Tool(
        name="get_relationship_types_by_category",
        description="List all relationship types in a specific category",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": [c.value for c in RelationshipCategory],
                    "description": "Relationship category to query"
                }
            },
            "required": ["category"]
        }
    ),
    Tool(
        name="analyze_graph_metrics",
        description="Get comprehensive graph analytics and metrics",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
]


class AdvancedRelationshipHandlers:
    """Handlers for advanced relationship tools."""

    def __init__(self, memory_db):
        """Initialize handlers with database reference."""
        self.memory_db = memory_db

    async def handle_find_memory_path(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Find shortest path between two memories."""
        try:
            from_id = arguments["from_memory_id"]
            to_id = arguments["to_memory_id"]
            max_depth = arguments.get("max_depth", 5)
            rel_types = arguments.get("relationship_types")

            # Convert string types to enums if provided
            relationship_types = None
            if rel_types:
                relationship_types = [RelationshipType(t) for t in rel_types]

            # Get all memories and relationships
            # (In production, this should be optimized to only fetch relevant subset)
            all_memories = []
            all_relationships = []

            # For now, we'll use the related memories query as an approximation
            related = await self.memory_db.get_related_memories(
                from_id,
                relationship_types=relationship_types,
                max_depth=max_depth
            )

            if not related:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"No path found between {from_id} and {to_id}"
                    )]
                )

            # Check if target is in related memories
            found_target = any(m.id == to_id for m, _ in related)

            if found_target:
                path_info = {
                    "found": True,
                    "from_memory_id": from_id,
                    "to_memory_id": to_id,
                    "hops": len([m for m, _ in related if m.id == to_id]),
                    "related_memories": len(related)
                }
            else:
                path_info = {
                    "found": False,
                    "from_memory_id": from_id,
                    "to_memory_id": to_id,
                    "searched_depth": max_depth
                }

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(path_info, indent=2)
                )]
            )

        except Exception as e:
            logger.error(f"Error finding memory path: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error finding path: {str(e)}"
                )],
                isError=True
            )

    async def handle_analyze_memory_clusters(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Analyze memory clusters."""
        try:
            # Note: This is a simplified implementation
            # In production, we'd need to fetch all memories and relationships
            # from the database to perform proper cluster analysis

            stats = await self.memory_db.get_memory_statistics()

            cluster_info = {
                "analysis_type": "cluster_detection",
                "total_memories": stats.get("total_memories", 0),
                "total_relationships": stats.get("total_relationships", 0),
                "note": "Full cluster analysis requires loading entire graph. Use get_memory_statistics for overview."
            }

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(cluster_info, indent=2)
                )]
            )

        except Exception as e:
            logger.error(f"Error analyzing clusters: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error analyzing clusters: {str(e)}"
                )],
                isError=True
            )

    async def handle_find_bridge_memories(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Find bridge memories connecting clusters."""
        try:
            stats = await self.memory_db.get_memory_statistics()

            bridge_info = {
                "analysis_type": "bridge_detection",
                "total_memories": stats.get("total_memories", 0),
                "note": "Full bridge analysis requires loading entire graph. Use get_memory_statistics for overview."
            }

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(bridge_info, indent=2)
                )]
            )

        except Exception as e:
            logger.error(f"Error finding bridges: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error finding bridges: {str(e)}"
                )],
                isError=True
            )

    async def handle_suggest_relationship_type(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Suggest relationship types between memories."""
        try:
            from_id = arguments["from_memory_id"]
            to_id = arguments["to_memory_id"]

            # Get the memories
            from_memory = await self.memory_db.get_memory(from_id, include_relationships=False)
            to_memory = await self.memory_db.get_memory(to_id, include_relationships=False)

            if not from_memory or not to_memory:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="One or both memories not found"
                    )],
                    isError=True
                )

            # Get suggestions
            suggestions = relationship_manager.suggest_relationship_type(
                from_memory,
                to_memory
            )

            suggestion_list = [
                {
                    "type": rel_type.value,
                    "confidence": confidence,
                    "category": relationship_manager.get_relationship_category(rel_type).value,
                    "description": relationship_manager.get_relationship_metadata(rel_type).description
                }
                for rel_type, confidence in suggestions
            ]

            result = {
                "from_memory": {
                    "id": from_memory.id,
                    "type": from_memory.type.value,
                    "title": from_memory.title
                },
                "to_memory": {
                    "id": to_memory.id,
                    "type": to_memory.type.value,
                    "title": to_memory.title
                },
                "suggestions": suggestion_list
            }

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            )

        except Exception as e:
            logger.error(f"Error suggesting relationship: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )],
                isError=True
            )

    async def handle_reinforce_relationship(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Reinforce a relationship."""
        try:
            from_id = arguments["from_memory_id"]
            to_id = arguments["to_memory_id"]
            success = arguments.get("success", True)

            # Get the existing relationship to find its type and current properties
            related = await self.memory_db.get_related_memories(from_id, max_depth=1)

            # Find the relationship to the target memory
            target_rel = None
            for memory, rel in related:
                if memory.id == to_id:
                    target_rel = rel
                    break

            if not target_rel:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"No relationship found between {from_id} and {to_id}"
                    )],
                    isError=True
                )

            # Reinforce the relationship properties
            new_props = relationship_manager.reinforce_relationship_properties(
                target_rel.properties,
                success=success
            )

            # Update the relationship in the database
            await self.memory_db.update_relationship_properties(
                from_id,
                to_id,
                target_rel.type,
                new_props
            )

            result = {
                "from_memory_id": from_id,
                "to_memory_id": to_id,
                "relationship_type": target_rel.type.value,
                "success": success,
                "updated_properties": {
                    "strength": new_props.strength,
                    "confidence": new_props.confidence,
                    "evidence_count": new_props.evidence_count,
                    "success_rate": new_props.success_rate
                }
            }

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            )

        except Exception as e:
            logger.error(f"Error reinforcing relationship: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )],
                isError=True
            )

    async def handle_get_relationship_types_by_category(
        self,
        arguments: Dict[str, Any]
    ) -> CallToolResult:
        """Get all relationship types in a category."""
        try:
            category = RelationshipCategory(arguments["category"])

            types = relationship_manager.get_types_by_category(category)

            type_list = [
                {
                    "type": rel_type.value,
                    "description": relationship_manager.get_relationship_metadata(rel_type).description,
                    "default_strength": relationship_manager.get_relationship_metadata(rel_type).default_strength,
                    "bidirectional": relationship_manager.get_relationship_metadata(rel_type).bidirectional
                }
                for rel_type in types
            ]

            result = {
                "category": category.value,
                "relationship_types": type_list,
                "count": len(type_list)
            }

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            )

        except Exception as e:
            logger.error(f"Error getting relationship types: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )],
                isError=True
            )

    async def handle_analyze_graph_metrics(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get comprehensive graph metrics."""
        try:
            # Get database statistics
            stats = await self.memory_db.get_memory_statistics()

            # Enhance with relationship metadata
            result = {
                "database_statistics": stats,
                "relationship_system": {
                    "total_relationship_types": 35,
                    "categories": [
                        {
                            "name": cat.value,
                            "types_count": len(relationship_manager.get_types_by_category(cat))
                        }
                        for cat in RelationshipCategory
                    ]
                }
            }

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            )

        except Exception as e:
            logger.error(f"Error getting graph metrics: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )],
                isError=True
            )
