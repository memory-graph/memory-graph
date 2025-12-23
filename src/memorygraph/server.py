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
from .cloud_database import CloudMemoryDatabase
from .backends.sqlite_fallback import SQLiteFallbackBackend
from .backends.cloud_backend import CloudBackend
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
from .migration_tools_module import MIGRATION_TOOLS, MIGRATION_TOOL_HANDLERS
# Removed: intelligence_tools, integration_tools, proactive_tools (moved to experimental/)
from .config import Config
from .tools import (
    handle_store_memory,
    handle_get_memory,
    handle_update_memory,
    handle_delete_memory,
    handle_create_relationship,
    handle_get_related_memories,
    handle_search_memories,
    handle_recall_memories,
    handle_contextual_search,
    handle_get_memory_statistics,
    handle_get_recent_activity,
    handle_search_relationships_by_context,
    # Temporal handlers deferred (backend methods available via Python API):
    # handle_query_as_of, handle_get_relationship_history, handle_what_changed
)


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
                name="recall_memories",
                description="""Primary tool for finding past memories using natural language queries.

Optimized for fuzzy matching - handles plurals, tenses, and case variations automatically.

BEST FOR:
- Conceptual queries ("how does X work")
- General exploration ("what do we know about authentication")
- Fuzzy/approximate matching

LESS EFFECTIVE FOR:
- Acronyms (DCAD, JWT, API) - use search_memories with tags instead
- Proper nouns (company names, services)
- Exact technical terms

EXAMPLES:
- recall_memories(query="timeout fix") - find timeout-related solutions
- recall_memories(query="how does auth work") - conceptual query
- recall_memories(project_path="/app") - memories from specific project

FALLBACK: If recall returns no relevant results, try search_memories with tags filter.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query for what you're looking for"
                        },
                        "memory_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [t.value for t in MemoryType]
                            },
                            "description": "Optional: Filter by memory types for more precision"
                        },
                        "project_path": {
                            "type": "string",
                            "description": "Optional: Filter by project path to scope results"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Maximum number of results per page (default: 20)"
                        },
                        "offset": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Number of results to skip for pagination (default: 0)"
                        }
                    }
                }
            ),
            Tool(
                name="store_memory",
                description="""Store a new memory with context and metadata.

Required: type, title, content. Optional: tags, importance (0-1), context.

TAGGING BEST PRACTICE:
- Always include acronyms AS TAGS (e.g., tags=["jwt", "auth"])
- Fuzzy search struggles with acronyms in content
- Tags provide exact match fallback for reliable retrieval

Types: solution, problem, error, fix, pattern, decision, task, code_pattern, technology, command, workflow, general

EXAMPLES:
- store_memory(type="solution", title="Fixed Redis timeout", content="Increased timeout to 30s...", tags=["redis"], importance=0.8)
- store_memory(type="error", title="OAuth2 auth failure", content="Error details...", tags=["auth", "oauth2"])

Returns memory_id. Use create_relationship to link related memories.""",
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
                description="""Retrieve a specific memory by ID.

Use when you have a memory_id from search results or store_memory.
Set include_relationships=true (default) to see connected memories.

EXAMPLE: get_memory(memory_id="abc-123")""",
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
                description="""Advanced search with fine-grained filters for precise retrieval.

USE THIS TOOL FIRST (not recall) when searching for:
- Acronyms: DCAD, JWT, MCR2, API, etc.
- Proper nouns: Company names, service names, project names
- Known tags: When you know the tag from previous memories
- Technical terms: Exact matches needed

PARAMETERS:
- tags: Filter by exact tag match (most reliable for acronyms)
- memory_types: Filter by type (solution, problem, etc.)
- min_importance: Filter by importance threshold
- search_tolerance: strict/normal/fuzzy
- match_mode: any/all for multiple terms

EXAMPLES:
- search_memories(tags=["jwt", "auth"]) - find JWT-related memories
- search_memories(tags=["dcad"]) - find DCAD memories by tag
- search_memories(query="timeout", memory_types=["solution"]) - timeout solutions
- search_memories(tags=["redis"], min_importance=0.7) - important Redis memories

For conceptual/natural language queries, use recall_memories instead.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Text to search for in memory content"
                        },
                        "terms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Multiple search terms for complex queries (alternative to query)"
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
                            "maximum": 1000,
                            "description": "Maximum number of results per page (default: 50)"
                        },
                        "offset": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Number of results to skip for pagination (default: 0)"
                        },
                        "search_tolerance": {
                            "type": "string",
                            "enum": ["strict", "normal", "fuzzy"],
                            "description": "Search tolerance mode: 'strict' for exact matches, 'normal' for stemming (default), 'fuzzy' for typo tolerance"
                        },
                        "match_mode": {
                            "type": "string",
                            "enum": ["any", "all"],
                            "description": "Match mode for terms: 'any' returns results matching ANY term (OR), 'all' requires ALL terms (AND)"
                        },
                        "relationship_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter results to only include memories with these relationship types"
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
                description="""Link two memories with a typed relationship.

Common types: SOLVES (solution→problem), CAUSES (cause→effect), ADDRESSES (fix→error), REQUIRES (dependent→dependency), RELATED_TO (general)

EXAMPLES:
- create_relationship(from_memory_id="sol-1", to_memory_id="prob-1", relationship_type="SOLVES")
- create_relationship(from_memory_id="err-1", to_memory_id="fix-1", relationship_type="CAUSES", context="Config error caused timeout")

Optional: strength (0-1), confidence (0-1), context (description)""",
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
                description="""Find memories connected to a specific memory via relationships.

Filter by relationship_types (e.g., ["SOLVES"], ["CAUSES"]) and max_depth (default 1).

EXAMPLES:
- get_related_memories(memory_id="prob-1", relationship_types=["SOLVES"]) - find solutions
- get_related_memories(memory_id="err-1", relationship_types=["CAUSES"], max_depth=2) - find root causes""",
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
                                "type": "string"
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
                name="get_recent_activity",
                description="""Get summary of recent memory activity for session context.

Returns: memory counts by type, recent memories (up to 20), unresolved problems.

EXAMPLES:
- get_recent_activity(days=7) - last week's activity
- get_recent_activity(days=30, project="/app") - last month for specific project""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 365,
                            "description": "Number of days to look back (default: 7)"
                        },
                        "project": {
                            "type": "string",
                            "description": "Optional: Filter by project path"
                        }
                    }
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
            ),
            # Contextual search tool for semantic graph traversal
            Tool(
                name="contextual_search",
                description="""Search only within the context of a given memory (scoped search).

Two-phase process: (1) Find related memories, (2) Search only within that set.
Provides semantic scoping without embeddings.

WHEN TO USE:
- Searching within a specific problem context
- Finding solutions in related knowledge
- Scoped discovery

HOW TO USE:
- Specify memory_id (context root)
- Provide query (search term)
- Optional: max_depth (default: 2)

RETURNS:
- Matches found only within related memories
- Context information
- No leakage outside context""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "Memory ID to use as context root (required)"
                        },
                        "query": {
                            "type": "string",
                            "description": "Search query within context (required)"
                        },
                        "max_depth": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Maximum relationship traversal depth (default: 2)"
                        }
                    },
                    "required": ["memory_id", "query"]
                }
            ),
            # Temporal tools deferred per ADR-017 (Context Budget Constraint)
            # Backend methods available via Python API:
            # - query_as_of, get_relationship_history, what_changed
            # MCP tool registration deferred until usage data justifies context cost
        ]

        # Combine all tools from all modules
        all_tools = (
            basic_tools +
            ADVANCED_RELATIONSHIP_TOOLS +
            MIGRATION_TOOLS
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

                if name == "recall_memories":
                    return await handle_recall_memories(self.memory_db, arguments)
                elif name == "store_memory":
                    return await handle_store_memory(self.memory_db, arguments)
                elif name == "get_memory":
                    return await handle_get_memory(self.memory_db, arguments)
                elif name == "search_memories":
                    return await handle_search_memories(self.memory_db, arguments)
                elif name == "update_memory":
                    return await handle_update_memory(self.memory_db, arguments)
                elif name == "delete_memory":
                    return await handle_delete_memory(self.memory_db, arguments)
                elif name == "create_relationship":
                    return await handle_create_relationship(self.memory_db, arguments)
                elif name == "get_related_memories":
                    return await handle_get_related_memories(self.memory_db, arguments)
                elif name == "get_memory_statistics":
                    return await handle_get_memory_statistics(self.memory_db, arguments)
                elif name == "get_recent_activity":
                    return await handle_get_recent_activity(self.memory_db, arguments)
                elif name == "search_relationships_by_context":
                    return await handle_search_relationships_by_context(self.memory_db, arguments)
                # Contextual search tool
                elif name == "contextual_search":
                    return await handle_contextual_search(self.memory_db, arguments)
                # Temporal tools deferred (backend methods available via Python API)
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

                # Migration tools
                elif name in ["migrate_database", "validate_migration"]:
                    handler = MIGRATION_TOOL_HANDLERS.get(name)
                    if handler:
                        # Migration tools don't need memory_db parameter - they create their own connections
                        result = await handler(**arguments)
                        # Format result as MCP response
                        import json
                        return CallToolResult(
                            content=[TextContent(
                                type="text",
                                text=json.dumps(result, indent=2)
                            )],
                            isError=not result.get("success", False)
                        )
                    else:
                        return CallToolResult(
                            content=[TextContent(type="text", text=f"Migration handler not found: {name}")],
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

            # Initialize memory database - choose wrapper based on backend type
            if isinstance(self.db_connection, SQLiteFallbackBackend):
                logger.info("Using SQLiteMemoryDatabase for SQLite backend")
                self.memory_db = SQLiteMemoryDatabase(self.db_connection)
            elif isinstance(self.db_connection, CloudBackend):
                logger.info("Using CloudMemoryDatabase for Cloud backend")
                self.memory_db = CloudMemoryDatabase(self.db_connection)
            else:
                logger.info("Using MemoryDatabase for Cypher-compatible backend")
                self.memory_db = MemoryDatabase(self.db_connection)

            await self.memory_db.initialize_schema()

            # Initialize advanced relationship handlers
            self.advanced_handlers = AdvancedRelationshipHandlers(self.memory_db)

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