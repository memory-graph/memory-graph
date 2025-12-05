"""
FalkorDBLite backend implementation for the Claude Code Memory Server.

This module provides the FalkorDBLite-specific implementation of the GraphBackend interface.
FalkorDBLite is an embedded graph database (like SQLite) with native Cypher support and exceptional performance.
Unlike FalkorDB (client-server), FalkorDBLite uses a file path for embedded local storage.
"""

import logging
import os
from typing import Any, Optional, List, Tuple, Dict
from pathlib import Path

from .base import GraphBackend
from ..models import (
    Memory,
    MemoryType,
    Relationship,
    RelationshipType,
    RelationshipProperties,
    SearchQuery,
    MemoryContext,
    MemoryNode,
    DatabaseConnectionError,
    SchemaError,
    ValidationError,
    RelationshipError,
)
from ..config import Config
from datetime import datetime, timezone
import uuid
import json

logger = logging.getLogger(__name__)


class FalkorDBLiteBackend(GraphBackend):
    """FalkorDBLite implementation of the GraphBackend interface."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        graph_name: str = "memorygraph"
    ):
        """
        Initialize FalkorDBLite backend.

        Args:
            db_path: Path to database file (defaults to FALKORDBLITE_PATH env var or ~/.memorygraph/falkordblite.db)
            graph_name: Name of the graph database (defaults to 'memorygraph')
        """
        if db_path is None:
            db_path = os.getenv("FALKORDBLITE_PATH")
            if db_path is None:
                # Default to ~/.memorygraph/falkordblite.db
                home = Path.home()
                db_dir = home / ".memorygraph"
                db_dir.mkdir(parents=True, exist_ok=True)
                db_path = str(db_dir / "falkordblite.db")

        self.db_path = db_path
        self.graph_name = graph_name
        self.client = None
        self.graph = None
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish connection to FalkorDBLite database.

        Returns:
            True if connection successful

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            # Lazy import falkordblite only when connecting
            try:
                from redislite.falkordb_client import FalkorDB
            except ImportError as e:
                raise DatabaseConnectionError(
                    "falkordblite package is required for FalkorDBLite backend. "
                    "Install with: pip install falkordblite"
                ) from e

            # Create FalkorDBLite client with file path (embedded database)
            self.client = FalkorDB(self.db_path)

            # Select the graph
            self.graph = self.client.select_graph(self.graph_name)
            self._connected = True

            logger.info(f"Successfully connected to FalkorDBLite at {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to FalkorDBLite: {e}")
            raise DatabaseConnectionError(f"Failed to connect to FalkorDBLite: {e}")

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self.client:
            # FalkorDBLite client doesn't require explicit close in Python SDK
            self.client = None
            self.graph = None
            self._connected = False
            logger.info("FalkorDBLite connection closed")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False
    ) -> list[dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: The Cypher query string
            parameters: Query parameters for parameterized queries
            write: Whether this is a write operation (default: False)

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseConnectionError: If not connected or query fails
        """
        if not self._connected or not self.graph:
            raise DatabaseConnectionError("Not connected to FalkorDBLite. Call connect() first.")

        params = parameters or {}

        try:
            # Execute query on FalkorDBLite
            result = self.graph.query(query, params)

            # Convert result to list of dicts
            result_list = []
            if hasattr(result, 'result_set') and result.result_set:
                result_list = result.result_set

            return result_list

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}")

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        Raises:
            SchemaError: If schema initialization fails
        """
        logger.info("Initializing FalkorDBLite schema for Claude Memory...")

        # Create constraints (FalkorDBLite uses similar Cypher syntax to FalkorDB)
        constraints = [
            "CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE",
        ]

        # Create indexes for performance
        indexes = [
            "CREATE INDEX ON :Memory(type)",
            "CREATE INDEX ON :Memory(created_at)",
            "CREATE INDEX ON :Memory(importance)",
            "CREATE INDEX ON :Memory(confidence)",
        ]

        # Conditional multi-tenant indexes (Phase 1)
        if Config.is_multi_tenant_mode():
            multitenant_indexes = [
                "CREATE INDEX ON :Memory(context_tenant_id)",
                "CREATE INDEX ON :Memory(context_team_id)",
                "CREATE INDEX ON :Memory(context_visibility)",
                "CREATE INDEX ON :Memory(context_created_by)",
                "CREATE INDEX ON :Memory(version)",
            ]
            indexes.extend(multitenant_indexes)
            logger.info("Multi-tenant mode enabled, adding tenant indexes")

        # Execute schema creation
        for constraint in constraints:
            try:
                await self.execute_query(constraint, write=True)
                logger.debug(f"Created constraint: {constraint}")
            except Exception as e:
                # FalkorDBLite may not support all constraint types, log but continue
                logger.debug(f"Constraint creation note: {e}")

        for index in indexes:
            try:
                await self.execute_query(index, write=True)
                logger.debug(f"Created index: {index}")
            except Exception as e:
                # FalkorDBLite may not support all index types, log but continue
                logger.debug(f"Index creation note: {e}")

        logger.info("Schema initialization completed")

    async def store_memory(self, memory: Memory) -> str:
        """
        Store a memory in the database and return its ID.

        Args:
            memory: Memory object to store

        Returns:
            ID of the stored memory

        Raises:
            ValidationError: If memory data is invalid
            DatabaseConnectionError: If storage fails
        """
        try:
            if not memory.id:
                memory.id = str(uuid.uuid4())

            memory.updated_at = datetime.now(timezone.utc)

            # Convert memory to properties
            memory_node = MemoryNode(memory=memory)
            properties = memory_node.to_neo4j_properties()

            query = """
            MERGE (m:Memory {id: $id})
            SET m += $properties
            RETURN m.id as id
            """

            result = await self.execute_query(
                query,
                {"id": memory.id, "properties": properties},
                write=True
            )

            if result:
                logger.info(f"Stored memory: {memory.id} ({memory.type})")
                return result[0]["id"]
            else:
                raise DatabaseConnectionError(f"Failed to store memory: {memory.id}")

        except Exception as e:
            if isinstance(e, (DatabaseConnectionError, ValidationError)):
                raise
            logger.error(f"Failed to store memory: {e}")
            raise DatabaseConnectionError(f"Failed to store memory: {e}")

    async def get_memory(self, memory_id: str, include_relationships: bool = True) -> Optional[Memory]:
        """
        Retrieve a memory by ID.

        Args:
            memory_id: ID of the memory to retrieve
            include_relationships: Whether to include relationships (not currently used)

        Returns:
            Memory object if found, None otherwise

        Raises:
            DatabaseConnectionError: If query fails
        """
        try:
            query = """
            MATCH (m:Memory {id: $memory_id})
            RETURN m
            """

            result = await self.execute_query(query, {"memory_id": memory_id}, write=False)

            if not result:
                return None

            memory_data = result[0]["m"]
            return self._falkordblite_to_memory(memory_data)

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to get memory {memory_id}: {e}")
            raise DatabaseConnectionError(f"Failed to get memory: {e}")

    async def search_memories(self, search_query: SearchQuery) -> List[Memory]:
        """
        Search for memories based on query parameters.

        Args:
            search_query: SearchQuery object with filter criteria

        Returns:
            List of Memory objects matching the search criteria

        Raises:
            DatabaseConnectionError: If search fails
        """
        try:
            conditions = []
            parameters = {}

            # Build WHERE conditions based on search parameters
            if search_query.query:
                conditions.append("(m.title CONTAINS $query OR m.content CONTAINS $query OR m.summary CONTAINS $query)")
                parameters["query"] = search_query.query

            if search_query.memory_types:
                conditions.append("m.type IN $memory_types")
                parameters["memory_types"] = [t.value for t in search_query.memory_types]

            if search_query.tags:
                conditions.append("ANY(tag IN $tags WHERE tag IN m.tags)")
                parameters["tags"] = search_query.tags

            if search_query.project_path:
                conditions.append("m.context_project_path = $project_path")
                parameters["project_path"] = search_query.project_path

            if search_query.min_importance is not None:
                conditions.append("m.importance >= $min_importance")
                parameters["min_importance"] = search_query.min_importance

            if search_query.min_confidence is not None:
                conditions.append("m.confidence >= $min_confidence")
                parameters["min_confidence"] = search_query.min_confidence

            # Build the complete query
            where_clause = " AND ".join(conditions) if conditions else "true"

            query = f"""
            MATCH (m:Memory)
            WHERE {where_clause}
            RETURN m
            ORDER BY m.importance DESC, m.created_at DESC
            LIMIT $limit
            """

            parameters["limit"] = search_query.limit

            result = await self.execute_query(query, parameters, write=False)

            memories = []
            for record in result:
                memory = self._falkordblite_to_memory(record["m"])
                if memory:
                    memories.append(memory)

            logger.info(f"Found {len(memories)} memories for search query")
            return memories

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to search memories: {e}")
            raise DatabaseConnectionError(f"Failed to search memories: {e}")

    async def update_memory(self, memory: Memory) -> bool:
        """
        Update an existing memory.

        Args:
            memory: Memory object with updated fields

        Returns:
            True if update succeeded, False otherwise

        Raises:
            ValidationError: If memory ID is missing
            DatabaseConnectionError: If update fails
        """
        try:
            if not memory.id:
                raise ValidationError("Memory must have an ID to update")

            memory.updated_at = datetime.now(timezone.utc)

            # Convert memory to properties
            memory_node = MemoryNode(memory=memory)
            properties = memory_node.to_neo4j_properties()

            query = """
            MATCH (m:Memory {id: $id})
            SET m += $properties
            RETURN m.id as id
            """

            result = await self.execute_query(
                query,
                {"id": memory.id, "properties": properties},
                write=True
            )

            success = len(result) > 0
            if success:
                logger.info(f"Updated memory: {memory.id}")

            return success

        except Exception as e:
            if isinstance(e, (ValidationError, DatabaseConnectionError)):
                raise
            logger.error(f"Failed to update memory {memory.id}: {e}")
            raise DatabaseConnectionError(f"Failed to update memory: {e}")

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory and all its relationships.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            True if deletion succeeded, False otherwise

        Raises:
            DatabaseConnectionError: If deletion fails
        """
        try:
            query = """
            MATCH (m:Memory {id: $memory_id})
            DETACH DELETE m
            RETURN COUNT(m) as deleted_count
            """

            result = await self.execute_query(query, {"memory_id": memory_id}, write=True)

            success = result and result[0]["deleted_count"] > 0
            if success:
                logger.info(f"Deleted memory: {memory_id}")

            return success

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            raise DatabaseConnectionError(f"Failed to delete memory: {e}")

    async def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: RelationshipProperties = None
    ) -> str:
        """
        Create a relationship between two memories.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship
            properties: Relationship properties (optional)

        Returns:
            ID of the created relationship

        Raises:
            RelationshipError: If relationship creation fails
            DatabaseConnectionError: If database operation fails
        """
        try:
            relationship_id = str(uuid.uuid4())

            if properties is None:
                properties = RelationshipProperties()

            # Convert properties to dict
            props_dict = properties.model_dump()
            props_dict['id'] = relationship_id
            props_dict['created_at'] = props_dict['created_at'].isoformat()
            props_dict['last_validated'] = props_dict['last_validated'].isoformat()

            query = f"""
            MATCH (from:Memory {{id: $from_id}})
            MATCH (to:Memory {{id: $to_id}})
            CREATE (from)-[r:{relationship_type.value} $properties]->(to)
            RETURN r.id as id
            """

            result = await self.execute_query(
                query,
                {
                    "from_id": from_memory_id,
                    "to_id": to_memory_id,
                    "properties": props_dict
                },
                write=True
            )

            if result:
                logger.info(f"Created relationship: {relationship_type.value} between {from_memory_id} and {to_memory_id}")
                return result[0]["id"]
            else:
                raise RelationshipError(
                    f"Failed to create relationship between {from_memory_id} and {to_memory_id}",
                    {"from_id": from_memory_id, "to_id": to_memory_id, "type": relationship_type.value}
                )

        except Exception as e:
            if isinstance(e, (RelationshipError, DatabaseConnectionError)):
                raise
            logger.error(f"Failed to create relationship: {e}")
            raise RelationshipError(f"Failed to create relationship: {e}")

    async def get_related_memories(
        self,
        memory_id: str,
        relationship_types: List[RelationshipType] = None,
        max_depth: int = 2
    ) -> List[Tuple[Memory, Relationship]]:
        """
        Get memories related to a specific memory.

        Args:
            memory_id: ID of the memory to find relations for
            relationship_types: Filter by specific relationship types (optional)
            max_depth: Maximum depth for graph traversal

        Returns:
            List of tuples containing (Memory, Relationship)

        Raises:
            DatabaseConnectionError: If query fails
        """
        try:
            # Build relationship type filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join([rt.value for rt in relationship_types])
                rel_filter = f":{rel_types}"

            query = f"""
            MATCH (start:Memory {{id: $memory_id}})
            MATCH (start)-[r{rel_filter}*1..{max_depth}]-(related:Memory)
            WHERE related.id <> start.id
            WITH DISTINCT related, r[0] as rel
            RETURN related,
                   type(rel) as rel_type,
                   properties(rel) as rel_props
            ORDER BY rel.strength DESC, related.importance DESC
            LIMIT 20
            """

            result = await self.execute_query(query, {"memory_id": memory_id}, write=False)

            related_memories = []
            for record in result:
                memory = self._falkordblite_to_memory(record["related"])
                if memory:
                    rel_type_str = record.get("rel_type", "RELATED_TO")
                    rel_props = record.get("rel_props", {})

                    try:
                        rel_type = RelationshipType(rel_type_str)
                    except ValueError:
                        rel_type = RelationshipType.RELATED_TO

                    relationship = Relationship(
                        from_memory_id=memory_id,
                        to_memory_id=memory.id,
                        type=rel_type,
                        properties=RelationshipProperties(
                            strength=rel_props.get("strength", 0.5),
                            confidence=rel_props.get("confidence", 0.8),
                            context=rel_props.get("context"),
                            evidence_count=rel_props.get("evidence_count", 1)
                        )
                    )
                    related_memories.append((memory, relationship))

            logger.info(f"Found {len(related_memories)} related memories for {memory_id}")
            return related_memories

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to get related memories for {memory_id}: {e}")
            raise DatabaseConnectionError(f"Failed to get related memories: {e}")

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics and metrics.

        Returns:
            Dictionary containing various database statistics

        Raises:
            DatabaseConnectionError: If query fails
        """
        queries = {
            "total_memories": "MATCH (m:Memory) RETURN COUNT(m) as count",
            "memories_by_type": """
                MATCH (m:Memory)
                RETURN m.type as type, COUNT(m) as count
                ORDER BY count DESC
            """,
            "total_relationships": "MATCH ()-[r]->() RETURN COUNT(r) as count",
            "avg_importance": "MATCH (m:Memory) RETURN AVG(m.importance) as avg_importance",
            "avg_confidence": "MATCH (m:Memory) RETURN AVG(m.confidence) as avg_confidence",
        }

        stats = {}
        for stat_name, query in queries.items():
            try:
                result = await self.execute_query(query, write=False)
                if stat_name == "memories_by_type":
                    stats[stat_name] = {record["type"]: record["count"] for record in result}
                else:
                    stats[stat_name] = result[0] if result else None
            except Exception as e:
                logger.error(f"Failed to get statistic {stat_name}: {e}")
                stats[stat_name] = None

        return stats

    async def health_check(self) -> dict[str, Any]:
        """
        Check backend health and return status information.

        Returns:
            Dictionary with health check results
        """
        health_info = {
            "connected": self._connected,
            "backend_type": "falkordblite",
            "db_path": self.db_path,
            "graph_name": self.graph_name
        }

        if self._connected:
            try:
                # Get basic node count
                count_query = "MATCH (m:Memory) RETURN count(m) as count"
                count_result = await self.execute_query(count_query, write=False)
                if count_result:
                    health_info["statistics"] = {
                        "memory_count": count_result[0].get("count", 0)
                    }
            except Exception as e:
                logger.warning(f"Could not get detailed health info: {e}")
                health_info["warning"] = str(e)

        return health_info

    def backend_name(self) -> str:
        """Return the name of this backend implementation."""
        return "falkordblite"

    def supports_fulltext_search(self) -> bool:
        """Check if this backend supports full-text search."""
        return True

    def supports_transactions(self) -> bool:
        """Check if this backend supports ACID transactions."""
        return True

    def _falkordblite_to_memory(self, node_data: Dict[str, Any]) -> Optional[Memory]:
        """
        Convert FalkorDBLite node data to Memory object.

        Args:
            node_data: Dictionary of node properties from FalkorDBLite

        Returns:
            Memory object or None if conversion fails
        """
        try:
            # Extract basic memory fields
            memory_data = {
                "id": node_data.get("id"),
                "type": MemoryType(node_data.get("type")),
                "title": node_data.get("title"),
                "content": node_data.get("content"),
                "summary": node_data.get("summary"),
                "tags": node_data.get("tags", []),
                "importance": node_data.get("importance", 0.5),
                "confidence": node_data.get("confidence", 0.8),
                "effectiveness": node_data.get("effectiveness"),
                "usage_count": node_data.get("usage_count", 0),
                "created_at": datetime.fromisoformat(node_data.get("created_at")),
                "updated_at": datetime.fromisoformat(node_data.get("updated_at")),
            }

            # Handle optional last_accessed field
            if node_data.get("last_accessed"):
                memory_data["last_accessed"] = datetime.fromisoformat(node_data["last_accessed"])

            # Extract context information
            context_data = {}
            for key, value in node_data.items():
                if key.startswith("context_") and value is not None:
                    context_key = key[8:]  # Remove "context_" prefix

                    # Deserialize JSON strings back to Python objects
                    if isinstance(value, str) and context_key in ["additional_metadata"]:
                        try:
                            context_data[context_key] = json.loads(value)
                        except json.JSONDecodeError:
                            context_data[context_key] = value
                    # Handle JSON-serialized lists/dicts
                    elif isinstance(value, str) and value.startswith(('[', '{')):
                        try:
                            context_data[context_key] = json.loads(value)
                        except json.JSONDecodeError:
                            context_data[context_key] = value
                    else:
                        context_data[context_key] = value

            if context_data:
                # Handle timestamp fields in context
                for time_field in ["timestamp"]:
                    if time_field in context_data:
                        if isinstance(context_data[time_field], str):
                            context_data[time_field] = datetime.fromisoformat(context_data[time_field])

                memory_data["context"] = MemoryContext(**context_data)

            return Memory(**memory_data)

        except Exception as e:
            logger.error(f"Failed to convert FalkorDBLite node to Memory: {e}")
            return None

    @classmethod
    async def create(
        cls,
        db_path: Optional[str] = None,
        graph_name: str = "memorygraph"
    ) -> "FalkorDBLiteBackend":
        """
        Factory method to create and connect to a FalkorDBLite backend.

        Args:
            db_path: Path to database file
            graph_name: Name of the graph database

        Returns:
            Connected FalkorDBLiteBackend instance

        Raises:
            DatabaseConnectionError: If connection fails
        """
        backend = cls(db_path, graph_name)
        await backend.connect()
        return backend
