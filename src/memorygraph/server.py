"""
Claude Code Memory Server - MCP implementation.

This module implements the Model Context Protocol server that provides intelligent
memory capabilities for Claude Code using Neo4j as the backend storage.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
)
from pydantic import ValidationError

from . import __version__
from .database import MemoryDatabase
from .sqlite_database import SQLiteMemoryDatabase
from .backends.sqlite_fallback import SQLiteFallbackBackend
from .models import (
    Memory,
    MemoryType,
    RelationshipType,
    RelationshipProperties,
    SearchQuery,
    MemoryContext,
    MemoryError,
    MemoryNotFoundError,
    RelationshipError,
    ValidationError as MemoryValidationError,
    DatabaseConnectionError,
)
from .advanced_tools import ADVANCED_RELATIONSHIP_TOOLS, AdvancedRelationshipHandlers
from .intelligence_tools import INTELLIGENCE_TOOLS
from .integration_tools import INTEGRATION_TOOLS
from .proactive_tools import PROACTIVE_TOOLS
from .config import Config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClaudeMemoryServer:
    """Claude Code Memory MCP Server implementation."""
    
    def __init__(self):
        """Initialize the memory server."""
        self.server = Server("claude-memory")
        self.db_connection = None  # GraphBackend instance
        self.memory_db: Optional[MemoryDatabase] = None
        self.advanced_handlers: Optional[AdvancedRelationshipHandlers] = None

        # Register MCP handlers
        self._register_handlers()

        # Collect all tools from all modules
        all_tools = self._collect_all_tools()

        # Filter tools based on profile
        enabled_tool_names = Config.get_enabled_tools()
        if enabled_tool_names is None:
            # Full profile: all tools enabled
            self.tools = all_tools
            logger.info(f"Tool profile: FULL - All {len(all_tools)} tools enabled")
        else:
            # Filter tools by name
            self.tools = [tool for tool in all_tools if tool.name in enabled_tool_names]
            logger.info(f"Tool profile: {Config.TOOL_PROFILE.upper()} - {len(self.tools)}/{len(all_tools)} tools enabled")

    def _collect_all_tools(self) -> List[Tool]:
        """Collect all tool definitions from all modules."""
        # Basic tools (defined inline below)
        basic_tools = [
            Tool(
                name="store_memory",
                description="Store a new memory with context and metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [t.value for t in MemoryType],
                            "description": "Type of memory to store"
                        },
                        "title": {
                            "type": "string",
                            "description": "Short descriptive title for the memory"
                        },
                        "content": {
                            "type": "string",
                            "description": "Detailed content of the memory"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Optional brief summary of the memory"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags to categorize the memory"
                        },
                        "importance": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Importance score (0.0-1.0)"
                        },
                        "context": {
                            "type": "object",
                            "description": "Context information for the memory"
                        }
                    },
                    "required": ["type", "title", "content"]
                }
            ),
            Tool(
                name="get_memory",
                description="Retrieve a specific memory by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to retrieve"
                        },
                        "include_relationships": {
                            "type": "boolean",
                            "description": "Whether to include related memories"
                        }
                    },
                    "required": ["memory_id"]
                }
            ),
            Tool(
                name="search_memories",
                description="Search for memories based on various criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Text to search for in memory content"
                        },
                        "memory_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [t.value for t in MemoryType]
                            },
                            "description": "Filter by memory types"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags"
                        },
                        "project_path": {
                            "type": "string",
                            "description": "Filter by project path"
                        },
                        "min_importance": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum importance score"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Maximum number of results"
                        },
                        "search_tolerance": {
                            "type": "string",
                            "enum": ["strict", "normal", "fuzzy"],
                            "description": "Search tolerance mode: 'strict' for exact matches, 'normal' for stemming (default), 'fuzzy' for typo tolerance"
                        }
                    }
                }
            ),
            Tool(
                name="update_memory",
                description="Update an existing memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to update"
                        },
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "summary": {"type": "string"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "importance": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["memory_id"]
                }
            ),
            Tool(
                name="delete_memory",
                description="Delete a memory and all its relationships",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to delete"
                        }
                    },
                    "required": ["memory_id"]
                }
            ),
            Tool(
                name="create_relationship",
                description="Create a relationship between two memories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_memory_id": {
                            "type": "string",
                            "description": "ID of the source memory"
                        },
                        "to_memory_id": {
                            "type": "string",
                            "description": "ID of the target memory"
                        },
                        "relationship_type": {
                            "type": "string",
                            "enum": [t.value for t in RelationshipType],
                            "description": "Type of relationship to create"
                        },
                        "strength": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Strength of the relationship (0.0-1.0)"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence in the relationship (0.0-1.0)"
                        },
                        "context": {
                            "type": "string",
                            "description": "Context or description of the relationship"
                        }
                    },
                    "required": ["from_memory_id", "to_memory_id", "relationship_type"]
                }
            ),
            Tool(
                name="get_related_memories",
                description="Find memories related to a specific memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to find relations for"
                        },
                        "relationship_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [t.value for t in RelationshipType]
                            },
                            "description": "Filter by relationship types"
                        },
                        "max_depth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Maximum relationship depth to traverse"
                        }
                    },
                    "required": ["memory_id"]
                }
            ),
            Tool(
                name="get_memory_statistics",
                description="Get statistics about the memory database",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="search_relationships_by_context",
                description="Search relationships by their structured context fields (scope, conditions, evidence, components)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scope": {
                            "type": "string",
                            "enum": ["partial", "full", "conditional"],
                            "description": "Filter by scope (partial, full, or conditional implementation)"
                        },
                        "conditions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by conditions (e.g., ['production', 'Redis enabled']). Matches any."
                        },
                        "has_evidence": {
                            "type": "boolean",
                            "description": "Filter by presence/absence of evidence (verified by tests, etc.)"
                        },
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by specific evidence types (e.g., ['integration tests', 'unit tests']). Matches any."
                        },
                        "components": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by components mentioned (e.g., ['auth', 'Redis']). Matches any."
                        },
                        "temporal": {
                            "type": "string",
                            "description": "Filter by temporal information (e.g., 'v2.1.0', 'since 2024')"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Maximum number of results (default: 20)"
                        }
                    }
                }
            )
        ]

        # Combine all tools from all modules
        all_tools = (
            basic_tools +
            ADVANCED_RELATIONSHIP_TOOLS +
            INTELLIGENCE_TOOLS +
            INTEGRATION_TOOLS +
            PROACTIVE_TOOLS
        )

        return all_tools

    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(tools=self.tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls."""
            try:
                if not self.memory_db:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text="Error: Memory database not initialized"
                        )],
                        isError=True
                    )

                if name == "store_memory":
                    return await self._handle_store_memory(arguments)
                elif name == "get_memory":
                    return await self._handle_get_memory(arguments)
                elif name == "search_memories":
                    return await self._handle_search_memories(arguments)
                elif name == "update_memory":
                    return await self._handle_update_memory(arguments)
                elif name == "delete_memory":
                    return await self._handle_delete_memory(arguments)
                elif name == "create_relationship":
                    return await self._handle_create_relationship(arguments)
                elif name == "get_related_memories":
                    return await self._handle_get_related_memories(arguments)
                elif name == "get_memory_statistics":
                    return await self._handle_get_memory_statistics(arguments)
                elif name == "search_relationships_by_context":
                    return await self._handle_search_relationships_by_context(arguments)
                # Advanced relationship tools
                elif name in ["find_memory_path", "analyze_memory_clusters", "find_bridge_memories",
                                       "suggest_relationship_type", "reinforce_relationship",
                                       "get_relationship_types_by_category", "analyze_graph_metrics"]:
                    # Dispatch to advanced handlers
                    method_name = f"handle_{name}"
                    handler = getattr(self.advanced_handlers, method_name, None)
                    if handler:
                        return await handler(arguments)
                    else:
                        return CallToolResult(
                            content=[TextContent(type="text", text=f"Handler not found: {name}")],
                            isError=True
                        )

                # Intelligence tools
                elif name in ["find_similar_solutions", "suggest_patterns_for_context",
                                      "get_intelligent_context", "get_project_summary",
                                      "get_session_briefing", "get_memory_history", "track_entity_timeline"]:
                    from .intelligence_tools import INTELLIGENCE_HANDLERS
                    handler = INTELLIGENCE_HANDLERS.get(name)
                    if handler:
                        return await handler(self.memory_db, arguments)
                    else:
                        return CallToolResult(
                            content=[TextContent(type="text", text=f"Intelligence handler not found: {name}")],
                            isError=True
                        )

                # Integration tools
                elif name in ["capture_task", "capture_command", "track_error_solution",
                                      "detect_project", "analyze_project", "track_file_changes",
                                      "identify_patterns", "track_workflow", "suggest_workflow",
                                      "optimize_workflow", "get_session_state"]:
                    if hasattr(self, 'integration_handlers'):
                        return await self.integration_handlers.dispatch(name, arguments)
                    else:
                        return CallToolResult(
                            content=[TextContent(type="text", text="Integration handlers not initialized")],
                            isError=True
                        )

                # Proactive tools
                elif name in ["check_for_issues", "get_suggestions", "predict_solution_effectiveness",
                                      "suggest_related_memories", "record_outcome", "get_graph_visualization",
                                      "recommend_learning_paths", "identify_knowledge_gaps", "track_memory_roi"]:
                    from .proactive_tools import PROACTIVE_TOOL_HANDLERS
                    handler = PROACTIVE_TOOL_HANDLERS.get(name)
                    if handler:
                        return await handler(self.memory_db, arguments)
                    else:
                        return CallToolResult(
                            content=[TextContent(type="text", text=f"Proactive handler not found: {name}")],
                            isError=True
                        )

                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"Unknown tool: {name}"
                        )],
                        isError=True
                    )

            except Exception as e:
                logger.error(f"Error handling tool call {name}: {e}")
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )],
                    isError=True
                )
    
    async def initialize(self):
        """Initialize the server and establish database connection."""
        try:
            # Initialize backend connection using factory
            from .backends.factory import BackendFactory
            self.db_connection = await BackendFactory.create_backend()

            # Initialize memory database - use SQLiteMemoryDatabase for SQLite backend
            if isinstance(self.db_connection, SQLiteFallbackBackend):
                logger.info("Using SQLiteMemoryDatabase for SQLite backend")
                self.memory_db = SQLiteMemoryDatabase(self.db_connection)
            else:
                logger.info("Using MemoryDatabase for Cypher-compatible backend")
                self.memory_db = MemoryDatabase(self.db_connection)

            await self.memory_db.initialize_schema()

            # Initialize advanced relationship handlers
            self.advanced_handlers = AdvancedRelationshipHandlers(self.memory_db)

            # Initialize integration handlers if needed
            from .integration_tools import IntegrationToolHandlers
            self.integration_handlers = IntegrationToolHandlers(self.memory_db)

            backend_name = getattr(self.db_connection, 'backend_name', lambda: 'Unknown')
            if callable(backend_name):
                backend_name = backend_name()
            logger.info(f"Claude Memory Server initialized successfully")
            logger.info(f"Backend: {backend_name}")
            logger.info(f"Tool profile: {Config.TOOL_PROFILE.upper()} ({len(self.tools)} tools enabled)")

        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources."""
        if self.db_connection:
            await self.db_connection.close()
        logger.info("Claude Memory Server cleanup completed")
    
    async def _handle_store_memory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle store_memory tool call."""
        try:
            # Extract context if provided
            context = None
            if "context" in arguments:
                context = MemoryContext(**arguments["context"])

            # Create memory object
            memory = Memory(
                type=MemoryType(arguments["type"]),
                title=arguments["title"],
                content=arguments["content"],
                summary=arguments.get("summary"),
                tags=arguments.get("tags", []),
                importance=arguments.get("importance", 0.5),
                context=context
            )

            # Store in database
            memory_id = await self.memory_db.store_memory(memory)

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Memory stored successfully with ID: {memory_id}"
                )]
            )

        except (ValidationError, KeyError, ValueError) as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Validation error: {e}"
                )],
                isError=True
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to store memory: {e}"
                )],
                isError=True
            )
    
    async def _handle_get_memory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_memory tool call."""
        try:
            memory_id = arguments["memory_id"]
            include_relationships = arguments.get("include_relationships", True)

            memory = await self.memory_db.get_memory(memory_id, include_relationships)

            if not memory:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Memory not found: {memory_id}"
                    )],
                    isError=True
                )

            # Format memory for display
            memory_text = f"""**Memory: {memory.title}**
Type: {memory.type.value}
Created: {memory.created_at}
Importance: {memory.importance}
Tags: {', '.join(memory.tags) if memory.tags else 'None'}

**Content:**
{memory.content}"""

            if memory.summary:
                memory_text = f"**Summary:** {memory.summary}\n\n" + memory_text

            return CallToolResult(
                content=[TextContent(type="text", text=memory_text)]
            )
        except KeyError as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Missing required field: {e}"
                )],
                isError=True
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to get memory: {e}"
                )],
                isError=True
            )
    
    async def _handle_search_memories(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle search_memories tool call."""
        try:
            # Build search query
            search_query = SearchQuery(
                query=arguments.get("query"),
                memory_types=[MemoryType(t) for t in arguments.get("memory_types", [])],
                tags=arguments.get("tags", []),
                project_path=arguments.get("project_path"),
                min_importance=arguments.get("min_importance"),
                limit=arguments.get("limit", 20)
            )
            
            memories = await self.memory_db.search_memories(search_query)
            
            if not memories:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="No memories found matching the search criteria."
                    )]
                )
            
            # Format results
            results_text = f"Found {len(memories)} memories:\n\n"
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
            
        except ValidationError as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Invalid search parameters: {e}"
                )],
                isError=True
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to search memories: {e}"
                )],
                isError=True
            )
    
    async def _handle_update_memory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle update_memory tool call."""
        try:
            memory_id = arguments["memory_id"]

            # Get existing memory
            memory = await self.memory_db.get_memory(memory_id, include_relationships=False)
            if not memory:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Memory not found: {memory_id}"
                    )],
                    isError=True
                )

            # Update fields
            if "title" in arguments:
                memory.title = arguments["title"]
            if "content" in arguments:
                memory.content = arguments["content"]
            if "summary" in arguments:
                memory.summary = arguments["summary"]
            if "tags" in arguments:
                memory.tags = arguments["tags"]
            if "importance" in arguments:
                memory.importance = arguments["importance"]

            # Update in database
            success = await self.memory_db.update_memory(memory)

            if success:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Memory updated successfully: {memory_id}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Failed to update memory: {memory_id}"
                    )],
                    isError=True
                )
        except KeyError as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Missing required field: {e}"
                )],
                isError=True
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to update memory: {e}"
                )],
                isError=True
            )
    
    async def _handle_delete_memory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle delete_memory tool call."""
        try:
            memory_id = arguments["memory_id"]

            success = await self.memory_db.delete_memory(memory_id)

            if success:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Memory deleted successfully: {memory_id}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"Failed to delete memory (may not exist): {memory_id}"
                    )],
                    isError=True
                )
        except KeyError as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Missing required field: {e}"
                )],
                isError=True
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to delete memory: {e}"
                )],
                isError=True
            )
    
    async def _handle_create_relationship(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle create_relationship tool call."""
        try:
            # Get user-provided context (natural language)
            user_context = arguments.get("context")

            # Auto-extract structure if context provided
            structured_context = None
            if user_context:
                from .utils.context_extractor import extract_context_structure
                import json
                structure = extract_context_structure(user_context)
                structured_context = json.dumps(structure)  # Serialize to JSON string

            properties = RelationshipProperties(
                strength=arguments.get("strength", 0.5),
                confidence=arguments.get("confidence", 0.8),
                context=structured_context  # Store JSON string
            )

            relationship_id = await self.memory_db.create_relationship(
                from_memory_id=arguments["from_memory_id"],
                to_memory_id=arguments["to_memory_id"],
                relationship_type=RelationshipType(arguments["relationship_type"]),
                properties=properties
            )

            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Relationship created successfully: {relationship_id}"
                )]
            )

        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to create relationship: {e}"
                )],
                isError=True
            )
    
    async def _handle_get_related_memories(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_related_memories tool call."""
        try:
            memory_id = arguments["memory_id"]
            relationship_types = None

            if "relationship_types" in arguments:
                relationship_types = [RelationshipType(t) for t in arguments["relationship_types"]]

            max_depth = arguments.get("max_depth", 2)

            related_memories = await self.memory_db.get_related_memories(
                memory_id=memory_id,
                relationship_types=relationship_types,
                max_depth=max_depth
            )

            if not related_memories:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"No related memories found for: {memory_id}"
                    )]
                )

            # Format results
            results_text = f"Found {len(related_memories)} related memories:\n\n"
            for i, (memory, relationship) in enumerate(related_memories, 1):
                results_text += f"**{i}. {memory.title}** (ID: {memory.id})\n"
                results_text += f"Relationship: {relationship.type.value} (strength: {relationship.properties.strength})\n"
                results_text += f"Type: {memory.type.value} | Importance: {memory.importance}\n\n"

            return CallToolResult(
                content=[TextContent(type="text", text=results_text)]
            )
        except KeyError as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Missing required field: {e}"
                )],
                isError=True
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to get related memories: {e}"
                )],
                isError=True
            )
    
    async def _handle_get_memory_statistics(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle get_memory_statistics tool call."""
        try:
            stats = await self.memory_db.get_memory_statistics()

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
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Failed to get memory statistics: {e}"
                )],
                isError=True
            )

    async def _handle_search_relationships_by_context(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle search_relationships_by_context tool call."""
        try:
            # Use SQLiteMemoryDatabase's search_relationships_by_context method
            if not isinstance(self.memory_db, SQLiteMemoryDatabase):
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="Context-based relationship search is only available with SQLite backend"
                    )],
                    isError=True
                )

            relationships = await self.memory_db.search_relationships_by_context(
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


async def main():
    """Main entry point for the MCP server."""
    server = ClaudeMemoryServer()

    try:
        # Initialize the server
        await server.initialize()

        # Create notification options and capabilities BEFORE passing to InitializationOptions
        # This ensures proper object instantiation and avoids potential GC or scoping issues
        notification_options = NotificationOptions()
        capabilities = server.server.get_capabilities(
            notification_options=notification_options,
            experimental_capabilities={},
        )

        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-memory",
                    server_version=__version__,
                    capabilities=capabilities,
                ),
            )

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())