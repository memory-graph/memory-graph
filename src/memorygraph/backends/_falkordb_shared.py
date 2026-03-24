"""
Shared base class for FalkorDB and FalkorDBLite backends.

Both backends use the same graph query engine and Cypher dialect. The only
differences are connection setup (client-server vs embedded) and health-check
metadata. This module extracts the ~95% of logic they share so that each
concrete backend is a thin subclass that overrides only connection plumbing.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..config import Config
from ..models import (
    DatabaseConnectionError,
    Memory,
    MemoryNode,
    Relationship,
    RelationshipError,
    RelationshipProperties,
    RelationshipType,
    SearchQuery,
    ValidationError,
)
from .base import GraphBackend

logger = logging.getLogger(__name__)


class BaseFalkorDBBackend(GraphBackend):
    """
    Shared implementation for FalkorDB-family backends.

    Subclasses must:
      - Set ``self.graph_name``, ``self.client``, ``self.graph``, and
        ``self._connected`` in ``__init__``.
      - Implement ``connect()``, ``health_check()``, and ``backend_name()``.
      - Provide a ``create()`` classmethod factory.
    """

    # Subclasses override this for log messages and memory-parser source tag.
    _display_name: str = "FalkorDB"

    # ------------------------------------------------------------------ #
    # Connection lifecycle (partially shared)
    # ------------------------------------------------------------------ #

    async def disconnect(self) -> None:
        """Close the database connection."""
        if self.client:
            self.client = None
            self.graph = None
            self._connected = False
            logger.info(f"{self._display_name} connection closed")

    # ------------------------------------------------------------------ #
    # Query execution
    # ------------------------------------------------------------------ #

    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        write: bool = False,
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
            raise DatabaseConnectionError(
                f"Connection failed: not connected to {self._display_name} (call connect() first)"
            )

        params = parameters or {}

        try:
            result = self.graph.query(query, params)

            result_list: list[dict[str, Any]] = []
            if hasattr(result, "result_set") and result.result_set:
                column_names: list[str] = []
                if hasattr(result, "header") and result.header:
                    for h in result.header:
                        if isinstance(h, (list, tuple)) and len(h) >= 2:
                            column_names.append(h[1])
                        else:
                            column_names.append(str(h))

                for row in result.result_set:
                    if isinstance(row, dict):
                        result_list.append(row)
                    elif isinstance(row, (list, tuple)) and column_names:
                        record = {
                            col_name: self._convert_falkordb_value(row[i])
                            for i, col_name in enumerate(column_names)
                            if i < len(row)
                        }
                        result_list.append(record)
                    else:
                        result_list.append(row)

            # Flush to disk after writes to prevent data loss on restart
            if write and hasattr(self, 'client') and self.client is not None:
                try:
                    self.client.client.save()
                except Exception as save_err:
                    logger.warning(f"Failed to persist after write: {save_err}")

            return result_list

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}") from e

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #

    async def initialize_schema(self) -> None:
        """
        Initialize database schema including indexes and constraints.

        Raises:
            SchemaError: If schema initialization fails
        """
        logger.info(f"Initializing {self._display_name} schema for Claude Memory...")

        constraints = [
            "CREATE CONSTRAINT ON (m:Memory) ASSERT m.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX ON :Memory(type)",
            "CREATE INDEX ON :Memory(created_at)",
            "CREATE INDEX ON :Memory(importance)",
            "CREATE INDEX ON :Memory(confidence)",
        ]

        if Config.is_multi_tenant_mode():
            indexes.extend([
                "CREATE INDEX ON :Memory(context_tenant_id)",
                "CREATE INDEX ON :Memory(context_team_id)",
                "CREATE INDEX ON :Memory(context_visibility)",
                "CREATE INDEX ON :Memory(context_created_by)",
                "CREATE INDEX ON :Memory(version)",
            ])
            logger.info("Multi-tenant mode enabled, adding tenant indexes")

        for constraint in constraints:
            try:
                await self.execute_query(constraint, write=True)
                logger.debug(f"Created constraint: {constraint}")
            except Exception as e:
                logger.debug(f"Constraint creation note: {e}")

        for index in indexes:
            try:
                await self.execute_query(index, write=True)
                logger.debug(f"Created index: {index}")
            except Exception as e:
                logger.debug(f"Index creation note: {e}")

        logger.info("Schema initialization completed")

    # ------------------------------------------------------------------ #
    # CRUD operations
    # ------------------------------------------------------------------ #

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
                write=True,
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
            raise DatabaseConnectionError(f"Failed to store memory: {e}") from e

    async def get_memory(
        self, memory_id: str, include_relationships: bool = True
    ) -> Optional[Memory]:
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
            return self._node_to_memory(memory_data)

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to get memory {memory_id}: {e}")
            raise DatabaseConnectionError(f"Failed to get memory: {e}") from e

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
            conditions: list[str] = []
            parameters: dict[str, Any] = {}

            if search_query.query:
                conditions.append(
                    "(m.title CONTAINS $query OR m.content CONTAINS $query OR m.summary CONTAINS $query)"
                )
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

            memories = [
                memory
                for record in result
                if (memory := self._node_to_memory(record["m"])) is not None
            ]

            logger.info(f"Found {len(memories)} memories for search query")
            return memories

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to search memories: {e}")
            raise DatabaseConnectionError(f"Failed to search memories: {e}") from e

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
                write=True,
            )

            success = len(result) > 0
            if success:
                logger.info(f"Updated memory: {memory.id}")

            return success

        except Exception as e:
            if isinstance(e, (ValidationError, DatabaseConnectionError)):
                raise
            logger.error(f"Failed to update memory {memory.id}: {e}")
            raise DatabaseConnectionError(f"Failed to update memory: {e}") from e

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
            # First check if the memory exists (COUNT after DETACH DELETE is
            # invalid Cypher — the variable is no longer bound).
            exists_query = """
            MATCH (m:Memory {id: $memory_id})
            RETURN m.id as id
            """
            exists = await self.execute_query(
                exists_query, {"memory_id": memory_id}, write=False
            )

            if not exists:
                return False

            delete_query = """
            MATCH (m:Memory {id: $memory_id})
            DETACH DELETE m
            """
            await self.execute_query(
                delete_query, {"memory_id": memory_id}, write=True
            )

            logger.info(f"Deleted memory: {memory_id}")
            return True

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            raise DatabaseConnectionError(f"Failed to delete memory: {e}") from e

    # ------------------------------------------------------------------ #
    # Relationships
    # ------------------------------------------------------------------ #

    async def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: RelationshipProperties = None,
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

            props_dict = properties.model_dump()
            props_dict["id"] = relationship_id
            # Convert ALL datetime values to isoformat strings
            from datetime import datetime as _dt
            for k, v in list(props_dict.items()):
                if isinstance(v, _dt):
                    props_dict[k] = v.isoformat()

            # FalkorDB's CYPHER preamble can't handle map parameters.
            # Build individual SET clauses for each property instead.
            set_clauses = []
            flat_params = {
                "from_id": from_memory_id,
                "to_id": to_memory_id,
            }
            for k, v in props_dict.items():
                if v is not None:
                    param_key = f"prop_{k}"
                    set_clauses.append(f"r.{k} = ${param_key}")
                    flat_params[param_key] = v

            set_clause_str = ", ".join(set_clauses) if set_clauses else ""
            set_line = f"SET {set_clause_str}" if set_clause_str else ""

            # Rename params to avoid CYPHER preamble conflicts with reserved words
            # FalkorDB's preamble can't handle param names like 'from_id' (contains 'from')
            flat_params["src_mem_id"] = flat_params.pop("from_id")
            flat_params["tgt_mem_id"] = flat_params.pop("to_id")

            query = f"""
            MATCH (src:Memory {{id: $src_mem_id}})
            MATCH (tgt:Memory {{id: $tgt_mem_id}})
            CREATE (src)-[r:{relationship_type.value}]->(tgt)
            {set_line}
            RETURN r.id as id
            """

            result = await self.execute_query(
                query,
                flat_params,
                write=True,
            )

            if result:
                logger.info(
                    f"Created relationship: {relationship_type.value} "
                    f"between {from_memory_id} and {to_memory_id}"
                )
                return result[0]["id"]
            else:
                raise RelationshipError(
                    f"Failed to create relationship between {from_memory_id} and {to_memory_id}",
                    {"from_id": from_memory_id, "to_id": to_memory_id, "type": relationship_type.value},
                )

        except Exception as e:
            if isinstance(e, (RelationshipError, DatabaseConnectionError)):
                raise
            logger.error(f"Failed to create relationship: {e}")
            raise RelationshipError(f"Failed to create relationship: {e}") from e

    async def get_related_memories(
        self,
        memory_id: str,
        relationship_types: List[RelationshipType] = None,
        max_depth: int = 2,
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
            rel_filter = ""
            if relationship_types:
                valid_types = {rt.value for rt in RelationshipType}
                for rt in relationship_types:
                    if rt.value not in valid_types:
                        raise ValidationError(f"Invalid relationship type: {rt}")
                rel_types = "|".join([rt.value for rt in relationship_types])
                rel_filter = f":{rel_types}"

            query = f"""
            MATCH (start:Memory {{id: $memory_id}})-[rel{rel_filter}]-(related:Memory)
            WHERE related.id <> start.id
            RETURN related,
                   type(rel) as rel_type,
                   rel.id as rel_id,
                   rel.strength as rel_strength,
                   rel.confidence as rel_confidence,
                   rel.context as rel_context,
                   rel.created_at as rel_created_at
            ORDER BY rel.strength DESC, related.importance DESC
            LIMIT 20
            """

            result = await self.execute_query(query, {"memory_id": memory_id}, write=False)

            related_memories: list[tuple[Memory, Relationship]] = []
            for record in result:
                memory = self._node_to_memory(record["related"])
                if memory:
                    rel_type_str = record.get("rel_type", "RELATED_TO")

                    try:
                        rel_type = RelationshipType(rel_type_str)
                    except ValueError:
                        rel_type = RelationshipType.RELATED_TO

                    relationship = Relationship(
                        from_memory_id=memory_id,
                        to_memory_id=memory.id,
                        type=rel_type,
                        properties=RelationshipProperties(
                            strength=record.get("rel_strength", 0.5),
                            confidence=record.get("rel_confidence", 0.8),
                            context=record.get("rel_context"),
                        ),
                    )
                    related_memories.append((memory, relationship))

            logger.info(f"Found {len(related_memories)} related memories for {memory_id}")
            return related_memories

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to get related memories for {memory_id}: {e}")
            raise DatabaseConnectionError(f"Failed to get related memories: {e}") from e

    # ------------------------------------------------------------------ #
    # Statistics
    # ------------------------------------------------------------------ #

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

        stats: dict[str, Any] = {}
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

    # ------------------------------------------------------------------ #
    # Capability flags
    # ------------------------------------------------------------------ #

    def supports_fulltext_search(self) -> bool:
        """Check if this backend supports full-text search."""
        return True

    def supports_transactions(self) -> bool:
        """Check if this backend supports ACID transactions."""
        return True

    def is_cypher_capable(self) -> bool:
        """FalkorDB-family backends support native Cypher query execution."""
        return True

    # ------------------------------------------------------------------ #
    # Value conversion helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _convert_falkordb_value(value: Any) -> Any:
        """
        Convert FalkorDB-specific types (Node, Edge) to plain dicts.

        Args:
            value: A value from a FalkorDB result row

        Returns:
            Converted value (dict for Node/Edge, original value otherwise)
        """
        if hasattr(value, "properties"):
            return dict(value.properties)
        return value

    def _node_to_memory(self, node_data: Dict[str, Any]) -> Optional[Memory]:
        """
        Convert FalkorDB node data to Memory object.

        Args:
            node_data: Dictionary of node properties

        Returns:
            Memory object or None if conversion fails
        """
        from ..utils.memory_parser import parse_memory_from_properties

        return parse_memory_from_properties(node_data, source=self._display_name)
