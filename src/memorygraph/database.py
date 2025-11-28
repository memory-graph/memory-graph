"""
Neo4j database connection and management for Claude Code Memory Server.

This module handles all database operations, connection management, and provides
a high-level interface for interacting with the Neo4j graph database.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union, Tuple, TYPE_CHECKING
from contextlib import asynccontextmanager
import uuid
from datetime import datetime

# Lazy imports for neo4j - only imported when Neo4jConnection is instantiated
# This allows the package to work with SQLite backend without neo4j installed
if TYPE_CHECKING:
    from neo4j import AsyncDriver

from .models import (
    Memory, MemoryType, MemoryNode, Relationship, RelationshipType,
    RelationshipProperties, SearchQuery, MemoryGraph, MemoryContext,
    MemoryError, MemoryNotFoundError, RelationshipError,
    ValidationError, DatabaseConnectionError, SchemaError
)


logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connection and async operations."""

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        database: str = "neo4j"
    ):
        """Initialize Neo4j connection.

        Args:
            uri: Neo4j database URI (defaults to NEO4J_URI env var or bolt://localhost:7687)
            user: Database username (defaults to NEO4J_USER env var or 'neo4j')
            password: Database password (defaults to NEO4J_PASSWORD env var)
            database: Database name (defaults to 'neo4j')

        Raises:
            DatabaseConnectionError: If password is not provided
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database
        self.driver: Optional[AsyncDriver] = None

        if not self.password:
            raise DatabaseConnectionError(
                "Neo4j password must be provided via parameter or NEO4J_PASSWORD env var"
            )

    async def connect(self) -> None:
        """Establish async connection to Neo4j database.

        Raises:
            DatabaseConnectionError: If connection fails
        """
        # Lazy import neo4j only when connecting
        try:
            from neo4j import AsyncGraphDatabase
            from neo4j.exceptions import ServiceUnavailable, AuthError
        except ImportError as e:
            raise DatabaseConnectionError(
                "neo4j package is required for Neo4j backend. "
                "Install with: pip install neo4j"
            ) from e

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0
            )

            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {self.uri}")

        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise DatabaseConnectionError(f"Failed to connect to Neo4j: {e}")
        except AuthError as e:
            logger.error(f"Authentication failed for Neo4j: {e}")
            raise DatabaseConnectionError(f"Authentication failed for Neo4j: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise DatabaseConnectionError(f"Unexpected error connecting to Neo4j: {e}")

    async def close(self) -> None:
        """Close the database connection."""
        if self.driver:
            await self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")

    @asynccontextmanager
    async def session(self, database: str = None):
        """Async context manager for Neo4j session.

        Raises:
            DatabaseConnectionError: If not connected
        """
        if not self.driver:
            raise DatabaseConnectionError("Not connected to Neo4j. Call connect() first.")

        session = self.driver.session(database=database or self.database)
        try:
            yield session
        finally:
            await session.close()

    async def execute_write_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        database: str = None
    ) -> List[Dict[str, Any]]:
        """Execute a write query in a transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (optional)

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseConnectionError: If query execution fails
        """
        # Lazy import Neo4jError for exception handling
        try:
            from neo4j.exceptions import Neo4jError
        except ImportError:
            # If neo4j not installed, we shouldn't be here anyway
            Neo4jError = Exception

        try:
            async with self.session(database) as session:
                result = await session.execute_write(
                    self._run_query_async, query, parameters or {}
                )
                return result
        except Neo4jError as e:
            logger.error(f"Write query failed: {e}")
            raise DatabaseConnectionError(f"Write query failed: {e}")

    async def execute_read_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        database: str = None
    ) -> List[Dict[str, Any]]:
        """Execute a read query in a transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (optional)

        Returns:
            List of result records as dictionaries

        Raises:
            DatabaseConnectionError: If query execution fails
        """
        # Lazy import Neo4jError for exception handling
        try:
            from neo4j.exceptions import Neo4jError
        except ImportError:
            # If neo4j not installed, we shouldn't be here anyway
            Neo4jError = Exception

        try:
            async with self.session(database) as session:
                result = await session.execute_read(
                    self._run_query_async, query, parameters or {}
                )
                return result
        except Neo4jError as e:
            logger.error(f"Read query failed: {e}")
            raise DatabaseConnectionError(f"Read query failed: {e}")

    @staticmethod
    async def _run_query_async(tx, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper method to run a query within an async transaction.

        Args:
            tx: Transaction object
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        result = await tx.run(query, parameters)
        records = await result.data()
        return records


class MemoryDatabase:
    """High-level interface for memory database operations."""

    def __init__(self, connection):
        """
        Initialize with a database backend connection.

        Args:
            connection: Database backend connection (Neo4jConnection or GraphBackend).
                       Must provide execute_write_query and execute_read_query methods.
        """
        self.connection = connection
    
    async def initialize_schema(self) -> None:
        """Create database schema, constraints, and indexes.

        Raises:
            SchemaError: If schema creation fails
        """
        logger.info("Initializing Neo4j schema for Claude Memory...")

        # Create constraints
        constraints = [
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR (r:RELATIONSHIP) REQUIRE r.id IS UNIQUE",
        ]

        # Create indexes for performance
        indexes = [
            "CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type)",
            "CREATE INDEX memory_created_at_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
            "CREATE INDEX memory_tags_index IF NOT EXISTS FOR (m:Memory) ON (m.tags)",
            "CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS FOR (m:Memory) ON EACH [m.title, m.content, m.summary]",
            "CREATE INDEX memory_importance_index IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
            "CREATE INDEX memory_confidence_index IF NOT EXISTS FOR (m:Memory) ON (m.confidence)",
            "CREATE INDEX memory_project_path_index IF NOT EXISTS FOR (m:Memory) ON (m.context_project_path)",
        ]

        # Execute schema creation
        for constraint in constraints:
            try:
                await self.connection.execute_write_query(constraint)
                logger.debug(f"Created constraint: {constraint}")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create constraint: {e}")

        for index in indexes:
            try:
                await self.connection.execute_write_query(index)
                logger.debug(f"Created index: {index}")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create index: {e}")

        logger.info("Schema initialization completed")
    
    async def store_memory(self, memory: Memory) -> str:
        """Store a memory in the database and return its ID.

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

            memory.updated_at = datetime.utcnow()

            # Convert memory to Neo4j properties
            memory_node = MemoryNode(memory=memory)
            properties = memory_node.to_neo4j_properties()

            query = """
            MERGE (m:Memory {id: $id})
            SET m += $properties
            RETURN m.id as id
            """

            result = await self.connection.execute_write_query(
                query,
                {"id": memory.id, "properties": properties}
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
        """Retrieve a memory by ID.

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

            result = await self.connection.execute_read_query(query, {"memory_id": memory_id})

            if not result:
                return None

            memory_data = result[0]["m"]
            return self._neo4j_to_memory(memory_data)

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to get memory {memory_id}: {e}")
            raise DatabaseConnectionError(f"Failed to get memory: {e}")
    
    async def search_memories(self, search_query: SearchQuery) -> List[Memory]:
        """Search for memories based on query parameters.

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

            if search_query.created_after:
                conditions.append("datetime(m.created_at) >= datetime($created_after)")
                parameters["created_after"] = search_query.created_after.isoformat()

            if search_query.created_before:
                conditions.append("datetime(m.created_at) <= datetime($created_before)")
                parameters["created_before"] = search_query.created_before.isoformat()

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

            result = await self.connection.execute_read_query(query, parameters)

            memories = []
            for record in result:
                memory = self._neo4j_to_memory(record["m"])
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
        """Update an existing memory.

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

            memory.updated_at = datetime.utcnow()

            # Convert memory to Neo4j properties
            memory_node = MemoryNode(memory=memory)
            properties = memory_node.to_neo4j_properties()

            query = """
            MATCH (m:Memory {id: $id})
            SET m += $properties
            RETURN m.id as id
            """

            result = await self.connection.execute_write_query(
                query,
                {"id": memory.id, "properties": properties}
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
        """Delete a memory and all its relationships.

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

            result = await self.connection.execute_write_query(query, {"memory_id": memory_id})

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
        """Create a relationship between two memories.

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

            # Convert properties to dict for Neo4j
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

            result = await self.connection.execute_write_query(
                query,
                {
                    "from_id": from_memory_id,
                    "to_id": to_memory_id,
                    "properties": props_dict
                }
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
        """Get memories related to a specific memory.

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

            # Fixed query to properly extract relationship metadata
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

            result = await self.connection.execute_read_query(query, {"memory_id": memory_id})

            related_memories = []
            for record in result:
                memory = self._neo4j_to_memory(record["related"])
                if memory:
                    # Fixed: Properly extract relationship type and properties
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
    
    def _neo4j_to_memory(self, node_data: Dict[str, Any]) -> Optional[Memory]:
        """Convert Neo4j node data to Memory object."""
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
            import json
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
            logger.error(f"Failed to convert Neo4j node to Memory: {e}")
            return None

    async def update_relationship_properties(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: RelationshipProperties
    ) -> bool:
        """Update properties of an existing relationship.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship to update
            properties: Updated relationship properties

        Returns:
            bool: True if update successful, False otherwise

        Raises:
            DatabaseConnectionError: If query fails
            RelationshipError: If relationship not found
        """
        try:
            # Convert properties to dict
            props_dict = properties.model_dump()

            # Convert datetime fields to ISO format strings
            for key in ['created_at', 'last_validated']:
                if key in props_dict and props_dict[key]:
                    props_dict[key] = props_dict[key].isoformat()

            # Update the relationship properties
            query = """
            MATCH (from:Memory {id: $from_id})-[r:$rel_type]->(to:Memory {id: $to_id})
            SET r += $props
            RETURN r
            """

            # Neo4j doesn't support parameterized relationship types, so construct query dynamically
            query = f"""
            MATCH (from:Memory {{id: $from_id}})-[r:{relationship_type.value}]->(to:Memory {{id: $to_id}})
            SET r += $props
            RETURN r
            """

            result = await self.connection.execute_write_query(
                query,
                {
                    "from_id": from_memory_id,
                    "to_id": to_memory_id,
                    "props": props_dict
                }
            )

            if not result:
                raise RelationshipError(
                    f"Relationship not found: {from_memory_id} -{relationship_type.value}-> {to_memory_id}"
                )

            logger.info(
                f"Updated relationship {from_memory_id} -{relationship_type.value}-> {to_memory_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update relationship: {e}")
            if isinstance(e, RelationshipError):
                raise
            raise DatabaseConnectionError(f"Failed to update relationship: {str(e)}")

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get database statistics and metrics.

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
                result = await self.connection.execute_read_query(query)
                if stat_name == "memories_by_type":
                    stats[stat_name] = {record["type"]: record["count"] for record in result}
                else:
                    stats[stat_name] = result[0] if result else None
            except Exception as e:
                logger.error(f"Failed to get statistic {stat_name}: {e}")
                stats[stat_name] = None

        return stats