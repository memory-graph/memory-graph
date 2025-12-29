"""
Neo4j database connection and management for Claude Code Memory Server.

This module handles all database operations, connection management, and provides
a high-level interface for interacting with the Neo4j graph database.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Union, Tuple, TYPE_CHECKING
from contextlib import asynccontextmanager
import uuid
from datetime import datetime, timezone

# Lazy imports for neo4j - only imported when Neo4jConnection is instantiated
# This allows the package to work with SQLite backend without neo4j installed
if TYPE_CHECKING:
    from neo4j import AsyncDriver

from .models import (
    Memory, MemoryType, MemoryNode, Relationship, RelationshipType,
    RelationshipProperties, SearchQuery, MemoryGraph, MemoryContext,
    MemoryError, MemoryNotFoundError, RelationshipError,
    ValidationError, DatabaseConnectionError, SchemaError, PaginatedResult
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

    LADYBUG = "ladybugdb"

    def __init__(self, connection):
        """
        Initialize with a database backend connection.

        Args:
            connection: Database backend connection (Neo4jConnection or GraphBackend).
                       Must provide execute_write_query and execute_read_query methods.
        """
        self.connection = connection
        self._backend = None
        backend_name_attr = getattr(connection, "backend_name", lambda: "unknown")
        if callable(backend_name_attr):
            self._backend = backend_name_attr()
        else:
            self._backend = backend_name_attr

    def _to_backend_id(self, memory_id: str):
        """Convert string ID to backend-specific format.

        Args:
            memory_id: String ID to convert

        Returns:
            UUID object for LadybugDB, string for Neo4j
        """
        return uuid.UUID(memory_id) if self._backend == self.LADYBUG else memory_id

    def _build_ladybug_memory_params(self, memory: Memory) -> dict:
        """Build parameters dictionary for LadybugDB memory operations.

        Args:
            memory: Memory object to convert

        Returns:
            Dictionary of parameters with native Python types
        """
        params = {
            "id": str(memory.id),  # Convert UUID to string for JSON compatibility
            "type": memory.type.value,
            "title": memory.title,
            "content": memory.content,
            "importance": memory.importance,
            "confidence": memory.confidence,
            "usage_count": memory.usage_count,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
            "version": memory.version,
        }

        # Add optional fields
        if memory.summary:
            params["summary"] = memory.summary
        if memory.updated_by:
            params["updated_by"] = memory.updated_by
        if memory.effectiveness is not None:
            params["effectiveness"] = memory.effectiveness
        if memory.last_accessed:
            params["last_accessed"] = memory.last_accessed

        # Handle context fields
        if memory.context:
            context_data = memory.context.model_dump()
            for key, value in context_data.items():
                if value is not None:
                    if isinstance(value, datetime):
                        params[f"context_{key}"] = value
                    elif isinstance(value, (list, dict)):
                        params[f"context_{key}"] = json.dumps(value)
                    else:
                        params[f"context_{key}"] = value

        # Add tags as JSON string for LadybugDB
        params["tags"] = json.dumps(memory.tags)

        return params

    def _build_ladybug_memory_query(self, params: dict, operation: str = "MERGE") -> str:
        """Build LadybugDB query for memory operations.

        Args:
            params: Parameter dictionary from _build_ladybug_memory_params
            operation: Either 'MERGE' or 'MATCH' for the initial clause

        Returns:
            Complete Cypher query string
        """
        # Build SET clause (excluding id and tags which are handled separately)
        set_fields = [k for k in params.keys() if k not in ("id", "tags")]
        set_clauses = ", ".join([f"m.{k} = ${k}" for k in set_fields])

        # Handle tags - convert list to JSON string representation
        # LadybugDB's to_json() expects a string parameter, not a list
        if set_clauses:
            set_clauses += ", "
        set_clauses += "m.tags = $tags"

        return f"""
        {operation} (m:Memory {{id: $id}})
        SET {set_clauses}
        RETURN m.id as id
        """

    def _node_to_memory(self, node_data: Dict[str, Any]) -> Optional[Memory]:
        """Convert database node data to Memory object (backend-agnostic).

        Args:
            node_data: Node data from database query

        Returns:
            Memory object or None if conversion fails
        """
        if self._backend == self.LADYBUG:
            return self._ladybug_to_memory(node_data)
        else:
            return self._neo4j_to_memory(node_data)

    async def initialize_schema(self) -> None:
        """Create database schema, constraints, and indexes.

        Raises:
            SchemaError: If schema creation fails
        """
        if self._backend == self.LADYBUG:
            await self.initialize_ladybugdb_schema()
        else:
            await self.initialize_neo4j_schema()

    async def initialize_ladybugdb_schema(self) -> None:
        """Create LadybugDB schema, constraints, and indexes.

        LadybugDB uses different Cypher syntax than Neo4j.
        LadybugDB requires NODE TABLE before REL TABLE.

        Raises:
            SchemaError: If schema creation fails
        """
        logger.info("Initializing LadybugDB schema for Claude Memory...")

        # LadybugDB cannot create unique constraints beyond primary key and not null
        # Create NODE TABLE first, then REL TABLE

        # Create Memory node table using LadybugDB syntax
        create_memory_table = """
        CREATE NODE TABLE IF NOT EXISTS Memory(
            id UUID PRIMARY KEY,
            type STRING,
            title STRING,
            content STRING,
            summary STRING,
            tags JSON,
            importance DOUBLE,
            confidence DOUBLE,
            effectiveness DOUBLE,
            usage_count INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            last_accessed TIMESTAMP,
            version INT,
            updated_by STRING,
            context_project_path STRING,
            context_line_start INT,
            context_line_end INT,
            context_commit_hash STRING,
            context_branch STRING,
            metadata STRING
        )
        """

        # Create REL table for relationships using LadybugDB syntax
        # This requires Memory node table to exist first
        create_relationship_table = """
        CREATE REL TABLE IF NOT EXISTS REL(
            FROM Memory TO Memory,
            id UUID,
            type STRING,
            properties STRING,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            metadata STRING
        )
        """

        # LadybugDB doesn't support CREATE INDEX at all, so we skip indexes
        # The primary keys will provide indexing automatically

        # Extensions (JSON, FTS) are loaded during backend connection in ladybugdb_backend.py

        # Execute schema creation
        await self.connection.execute_write_query(create_memory_table)
        logger.debug("Created Memory node table")

        await self.connection.execute_write_query(create_relationship_table)
        logger.debug("Created REL table for relationships")

        logger.info("LadybugDB schema initialization completed")

    async def initialize_neo4j_schema(self) -> None:
        """Create Neo4j database schema, constraints, and indexes.

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

        logger.info("Neo4j schema initialization completed")

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

            memory.updated_at = datetime.now(timezone.utc)

            if self._backend == self.LADYBUG:
                params = self._build_ladybug_memory_params(memory)
                query = self._build_ladybug_memory_query(params, "MERGE")
            else:
                # Neo4j code path - unchanged
                memory_node = MemoryNode(memory=memory)
                properties = memory_node.to_neo4j_properties()
                query = """
                MERGE (m:Memory {id: $id})
                SET m += $properties
                RETURN m.id as id
                """
                params = {"id": memory.id, "properties": properties}

            result = await self.connection.execute_write_query(query, params)

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

            params = {"memory_id": self._to_backend_id(memory_id)}
            result = await self.connection.execute_read_query(query, params)

            if not result:
                return None

            memory_data = result[0]["m"]
            return self._node_to_memory(memory_data)

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
                # Both Neo4j/Memgraph and LadybugDB (with JSON extension) support list operations
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
                memory = self._node_to_memory(record["m"])
                if memory:
                    memories.append(memory)

            logger.info(f"Found {len(memories)} memories for search query")
            return memories

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to search memories: {e}")
            raise DatabaseConnectionError(f"Failed to search memories: {e}")

    async def search_memories_paginated(self, search_query: SearchQuery) -> PaginatedResult:
        """Search for memories with pagination support.

        Args:
            search_query: SearchQuery object with filter criteria, limit, and offset

        Returns:
            PaginatedResult with memories and pagination metadata

        Raises:
            DatabaseConnectionError: If search fails
        """
        try:
            conditions = []
            parameters = {}

            # Build WHERE conditions based on search parameters (same as search_memories)
            if search_query.query:
                conditions.append("(m.title CONTAINS $query OR m.content CONTAINS $query OR m.summary CONTAINS $query)")
                parameters["query"] = search_query.query

            if search_query.memory_types:
                conditions.append("m.type IN $memory_types")
                parameters["memory_types"] = [t.value for t in search_query.memory_types]

            if search_query.tags:
                # Both Neo4j/Memgraph and LadybugDB (with JSON extension) support list operations
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

            where_clause = " AND ".join(conditions) if conditions else "true"

            # First, get the total count
            count_query = f"""
            MATCH (m:Memory)
            WHERE {where_clause}
            RETURN count(m) as total_count
            """

            count_result = await self.connection.execute_read_query(count_query, parameters)
            total_count = count_result[0]["total_count"] if count_result else 0

            # Then get the paginated results
            results_query = f"""
            MATCH (m:Memory)
            WHERE {where_clause}
            RETURN m
            ORDER BY m.importance DESC, m.created_at DESC
            SKIP $offset
            LIMIT $limit
            """

            parameters["offset"] = search_query.offset
            parameters["limit"] = search_query.limit

            result = await self.connection.execute_read_query(results_query, parameters)

            memories = []
            for record in result:
                memory = self._node_to_memory(record["m"])
                if memory:
                    memories.append(memory)

            # Calculate pagination metadata
            has_more = (search_query.offset + search_query.limit) < total_count
            next_offset = (search_query.offset + search_query.limit) if has_more else None

            logger.info(f"Found {len(memories)} memories (page {search_query.offset}-{search_query.offset + len(memories)} of {total_count})")

            return PaginatedResult(
                results=memories,
                total_count=total_count,
                limit=search_query.limit,
                offset=search_query.offset,
                has_more=has_more,
                next_offset=next_offset
            )

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to search memories (paginated): {e}")
            raise DatabaseConnectionError(f"Failed to search memories (paginated): {e}")

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

            memory.updated_at = datetime.now(timezone.utc)

            if self._backend == self.LADYBUG:
                params = self._build_ladybug_memory_params(memory)
                query = self._build_ladybug_memory_query(params, "MATCH")
            else:
                # Neo4j code path - unchanged
                memory_node = MemoryNode(memory=memory)
                properties = memory_node.to_neo4j_properties()
                query = """
                MATCH (m:Memory {id: $id})
                SET m += $properties
                RETURN m.id as id
                """
                params = {"id": memory.id, "properties": properties}

            result = await self.connection.execute_write_query(query, params)

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

            params = {"memory_id": self._to_backend_id(memory_id)}
            result = await self.connection.execute_write_query(query, params)

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

            params = {
                "from_id": self._to_backend_id(from_memory_id),
                "to_id": self._to_backend_id(to_memory_id),
                "properties": props_dict
            }
            result = await self.connection.execute_write_query(query, params)

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

            # Query to capture both outgoing and incoming relationships with proper direction
            # We query in both directions and capture the actual source/target nodes
            query = f"""
            MATCH (start:Memory {{id: $memory_id}})
            MATCH path = (start)-[r{rel_filter}*1..{max_depth}]-(related:Memory)
            WHERE related.id <> start.id
            WITH DISTINCT related, r[0] as rel,
                 startNode(rel) as source,
                 endNode(rel) as target
            RETURN related,
                   type(rel) as rel_type,
                   properties(rel) as rel_props,
                   source.id as from_id,
                   target.id as to_id
             ORDER BY rel.strength DESC, related.importance DESC
             LIMIT 20
             """

            params = {"memory_id": self._to_backend_id(memory_id)}
            result = await self.connection.execute_read_query(query, params)

            related_memories = []
            for record in result:
                memory = self._node_to_memory(record["related"])
                if memory:
                    # Properly extract relationship type, properties, and direction
                    rel_type_str = record.get("rel_type", "RELATED_TO")
                    rel_props = record.get("rel_props", {})
                    from_id = record.get("from_id")
                    to_id = record.get("to_id")

                    # Fallback: if from_id/to_id are not provided, infer from query
                    # This happens in older implementations or mocked tests
                    if not from_id or not to_id:
                        # We don't know the direction, so skip this relationship
                        # or use a conservative approach and assume outgoing
                        logger.warning(
                            f"Relationship direction not provided in query result, "
                            f"skipping relationship to {memory.id}"
                        )
                        continue

                    try:
                        rel_type = RelationshipType(rel_type_str)
                    except ValueError:
                        rel_type = RelationshipType.RELATED_TO

                    relationship = Relationship(
                        from_memory_id=from_id,
                        to_memory_id=to_id,
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

    def _ladybug_to_memory(self, node_data: Dict[str, Any]) -> Optional[Memory]:
        """Convert LadybugDB node data to Memory object.

        LadybugDB returns native Python types:
        - UUID as UUID objects
        - TIMESTAMP as datetime objects
        - JSON as parsed Python objects (lists, dicts)
        """
        try:
            # Extract tags - JSON type returns string representation
            tags_value = node_data.get("tags", [])
            if isinstance(tags_value, str):
                # Parse JSON string
                try:
                    tags_value = json.loads(tags_value)
                except json.JSONDecodeError:
                    tags_value = []
            elif not isinstance(tags_value, list):
                tags_value = []

            # Extract basic memory fields - types are already native Python
            memory_data = {
                "id": str(node_data.get("id")),  # Convert UUID to string
                "type": MemoryType(node_data.get("type")),
                "title": node_data.get("title"),
                "content": node_data.get("content"),
                "summary": node_data.get("summary"),
                "tags": tags_value,
                "importance": node_data.get("importance", 0.5),
                "confidence": node_data.get("confidence", 0.8),
                "effectiveness": node_data.get("effectiveness"),
                "usage_count": node_data.get("usage_count", 0),
                "last_accessed": node_data.get("last_accessed"),
                "created_at": node_data.get("created_at"),  # Already datetime
                "updated_at": node_data.get("updated_at"),  # Already datetime
                "version": node_data.get("version", 1),
                "updated_by": node_data.get("updated_by"),
            }

            # Extract context information
            context_data = {}
            context_field_mapping = {
                "context_project_path": "project_path",
                "context_file_path": "file_path",
                "context_line_start": "line_start",
                "context_line_end": "line_end",
                "context_commit_hash": "git_commit",
                "context_branch": "git_branch",
            }
            for db_field, context_key in context_field_mapping.items():
                if db_field in node_data and node_data[db_field] is not None:
                    context_data[context_key] = node_data[db_field]

            if context_data:
                memory_data["context"] = MemoryContext(**context_data)

            return Memory(**memory_data)

        except Exception as e:
            logger.error(f"Failed to convert LadybugDB node to Memory: {e}")
            return None

    def _neo4j_to_memory(self, node_data: Dict[str, Any]) -> Optional[Memory]:
        """Convert Neo4j node data to Memory object."""
        try:
            # Extract tags (LadybugDB JSON extension returns list directly like Neo4j/Memgraph)
            tags_value = node_data.get("tags", [])
            if not isinstance(tags_value, list):
                tags_value = []

            # Extract basic memory fields
            memory_data = {
                "id": node_data.get("id"),
                "type": MemoryType(node_data.get("type")),
                "title": node_data.get("title"),
                "content": node_data.get("content"),
                "summary": node_data.get("summary"),
                "tags": tags_value,
                "importance": node_data.get("importance", 0.5),
                "confidence": node_data.get("confidence", 0.8),
                "effectiveness": node_data.get("effectiveness"),
                "usage_count": node_data.get("usage_count", 0),
                "created_at": node_data.get("created_at") if isinstance(node_data.get("created_at"), datetime) else (datetime.fromisoformat(node_data["created_at"]) if node_data.get("created_at") else None),
                "updated_at": node_data.get("updated_at") if isinstance(node_data.get("updated_at"), datetime) else (datetime.fromisoformat(node_data["updated_at"]) if node_data.get("updated_at") else None),
            }

            # Handle optional last_accessed field
            if node_data.get("last_accessed"):
                last_accessed = node_data["last_accessed"]
                if isinstance(last_accessed, str):
                    last_accessed = datetime.fromisoformat(last_accessed)
                memory_data["last_accessed"] = last_accessed

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

            if self._backend == self.LADYBUG:
                # LadybugDB doesn't support += for map updates, so we need to set properties individually
                set_clauses = ", ".join([f"r.{k} = ${k}" for k in props_dict.keys()])
                query = f"""
                MATCH (src:Memory {{id: $from_id}})-[r:{relationship_type.value}]->(dst:Memory {{id: $to_id}})
                SET {set_clauses}
                RETURN r
                """
                params = {
                    "from_id": self._to_backend_id(from_memory_id),
                    "to_id": self._to_backend_id(to_memory_id),
                    **props_dict
                }
            else:
               # Neo4j doesn't support parameterized relationship types, so construct query dynamically
                query = f"""
                MATCH (from:Memory {{id: $from_id}})-[r:{relationship_type.value}]->(to:Memory {{id: $to_id}})
                SET r += $props
                RETURN r
                """

                params = {
                    "from_id": from_memory_id,
                    "to_id": to_memory_id,
                    "props": props_dict
                }
            result = await self.connection.execute_write_query(query, params)

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