"""
SQLite-specific database implementation for MemoryGraph.

This module provides a SQLiteMemoryDatabase class that uses SQL queries
instead of Cypher. It works with the SQLiteFallbackBackend to provide
memory storage without requiring Neo4j.
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, UTC

from .models import (
    Memory, MemoryType, MemoryNode, Relationship, RelationshipType,
    RelationshipProperties, SearchQuery, MemoryContext,
    MemoryError, MemoryNotFoundError, RelationshipError,
    ValidationError, DatabaseConnectionError, SchemaError
)
from .backends.sqlite_fallback import SQLiteFallbackBackend

logger = logging.getLogger(__name__)


def _simple_stem(word: str) -> str:
    """
    Simple word stemming for fuzzy search.

    Handles common English plurals and verb tenses.
    This is a lightweight alternative to full NLP stemming.

    Args:
        word: Word to stem

    Returns:
        Stemmed word
    """
    word = word.lower().strip()

    if len(word) <= 3:
        return word

    # Handle 'ied' suffix specially (retried -> retry, not retri)
    if word.endswith('ied') and len(word) > 4:
        # Remove 'ied' and add 'y' back
        stem = word[:-3] + 'y'
        if len(stem) >= 3:
            return stem

    # Handle 'ies' suffix specially (retries -> retry, not retr)
    if word.endswith('ies') and len(word) > 4:
        # Remove 'ies' and add 'y' back
        stem = word[:-3] + 'y'
        if len(stem) >= 3:
            return stem

    # Remove common suffixes (ordered by specificity)
    suffixes = [
        'es',     # boxes -> box
        'ing',    # retrying -> retry
        'ed',     # timed -> tim
        's',      # errors -> error
    ]

    for suffix in suffixes:
        if word.endswith(suffix):
            stem = word[:-len(suffix)]
            # Don't stem too aggressively (keep at least 3 chars)
            if len(stem) >= 3:
                return stem

    return word


def _generate_fuzzy_patterns(query: str) -> list:
    """
    Generate fuzzy search patterns from a query string.

    Creates multiple patterns to match variations of words.

    Args:
        query: Search query string

    Returns:
        List of (pattern, weight) tuples for matching
    """
    patterns = []
    query_lower = query.lower().strip()

    # Exact match pattern (highest priority)
    patterns.append((f"%{query_lower}%", 1.0))

    # Split into words for multi-word queries
    words = query_lower.split()

    for word in words:
        if len(word) <= 2:
            continue

        # Stem the word
        stem = _simple_stem(word)

        # Add stemmed pattern if different from original
        if stem != word and len(stem) >= 3:
            patterns.append((f"%{stem}%", 0.8))

        # Also add patterns for common variations that would stem to this word
        # This helps match: "retry" -> "retries", "retrying", "retried"
        if len(word) >= 4:
            # Add common suffixes
            variations = []

            # Handle words ending in 'y' specially (retry -> retries, not retrys)
            if word.endswith('y'):
                variations.extend([
                    word[:-1] + "ies",  # retry -> retries
                    word + "ing",        # retry -> retrying
                    word[:-1] + "ied",  # retry -> retried
                ])
            else:
                variations.extend([
                    word + "s",     # cache -> caches
                    word + "es",    # box -> boxes
                    word + "ing",   # cache -> caching
                    word + "ed",    # cache -> cached
                ])

            for var in variations:
                var_stem = _simple_stem(var)
                # Only add if it stems back to our word's stem
                if var_stem == stem and len(var_stem) >= 3:
                    patterns.append((f"%{var}%", 0.9))

    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for pattern, weight in patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append((pattern, weight))

    return unique_patterns


class SQLiteMemoryDatabase:
    """SQLite-specific implementation of memory database operations."""

    def __init__(self, backend: SQLiteFallbackBackend):
        """
        Initialize with a SQLite backend connection.

        Args:
            backend: SQLiteFallbackBackend instance
        """
        self.backend = backend

    async def initialize_schema(self) -> None:
        """
        Create database schema, constraints, and indexes.

        This method ensures the SQLite backend has the proper schema
        for storing Memory objects as nodes.

        Raises:
            SchemaError: If schema creation fails
        """
        logger.info("Initializing SQLite schema for Memory storage...")

        try:
            # The backend already creates basic tables, but we may need additional indexes
            # for Memory-specific queries

            # Create index on properties for common queries
            # These are in addition to the basic indexes created by the backend
            try:
                self.backend.execute_sync(
                    "CREATE INDEX IF NOT EXISTS idx_nodes_memory ON nodes(label) WHERE label = 'Memory'"
                )
            except Exception as e:
                logger.debug(f"Index creation skipped (may already exist): {e}")

            logger.info("Memory schema initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise SchemaError(f"Failed to initialize schema: {e}")

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

            memory.updated_at = datetime.now(UTC)

            # Convert memory to properties dict
            memory_node = MemoryNode(memory=memory)
            properties = memory_node.to_neo4j_properties()

            # Serialize properties as JSON
            properties_json = json.dumps(properties)

            # Check if memory already exists (MERGE behavior)
            existing = self.backend.execute_sync(
                "SELECT id FROM nodes WHERE id = ? AND label = 'Memory'",
                (memory.id,)
            )

            if existing:
                # Update existing
                self.backend.execute_sync(
                    """
                    UPDATE nodes
                    SET properties = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND label = 'Memory'
                    """,
                    (properties_json, memory.id)
                )
            else:
                # Insert new
                self.backend.execute_sync(
                    """
                    INSERT INTO nodes (id, label, properties, created_at, updated_at)
                    VALUES (?, 'Memory', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """,
                    (memory.id, properties_json)
                )

            self.backend.commit()
            logger.info(f"Stored memory: {memory.id} ({memory.type})")
            return memory.id

        except Exception as e:
            self.backend.rollback()
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
            result = self.backend.execute_sync(
                "SELECT properties FROM nodes WHERE id = ? AND label = 'Memory'",
                (memory_id,)
            )

            if not result:
                return None

            properties_json = result[0]['properties']
            properties = json.loads(properties_json)

            return self._properties_to_memory(properties)

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
            # Build SQL WHERE conditions
            where_conditions = ["label = 'Memory'"]
            params = []

            # Multi-term search (takes precedence over single query)
            if search_query.terms:
                tolerance = search_query.search_tolerance or "normal"
                match_mode = search_query.match_mode or "any"

                term_conditions = []
                for term in search_query.terms:
                    if tolerance == "strict":
                        # Strict mode: exact substring match only
                        pattern = f"%{term.lower()}%"
                        term_conditions.append(
                            "(json_extract(properties, '$.title') LIKE ? OR "
                            "json_extract(properties, '$.content') LIKE ? OR "
                            "json_extract(properties, '$.summary') LIKE ?)"
                        )
                        params.extend([pattern, pattern, pattern])
                    else:
                        # Normal/fuzzy mode: use stemming
                        patterns = _generate_fuzzy_patterns(term)
                        pattern_conditions = []
                        for pattern, weight in patterns:
                            pattern_conditions.append(
                                "(json_extract(properties, '$.title') LIKE ? OR "
                                "json_extract(properties, '$.content') LIKE ? OR "
                                "json_extract(properties, '$.summary') LIKE ?)"
                            )
                            params.extend([pattern, pattern, pattern])
                        if pattern_conditions:
                            term_conditions.append(f"({' OR '.join(pattern_conditions)})")

                # Combine term conditions based on match_mode
                if term_conditions:
                    if match_mode == "all":
                        # AND: all terms must match
                        where_conditions.append(f"({' AND '.join(term_conditions)})")
                    else:
                        # OR: any term matches (default)
                        where_conditions.append(f"({' OR '.join(term_conditions)})")

            # Text search with tolerance-based matching (single query)
            elif search_query.query:
                tolerance = search_query.search_tolerance or "normal"

                if tolerance == "strict":
                    # Strict mode: exact substring match only (no stemming)
                    pattern = f"%{search_query.query.lower()}%"
                    pattern_conditions = [
                        "(json_extract(properties, '$.title') LIKE ? OR "
                        "json_extract(properties, '$.content') LIKE ? OR "
                        "json_extract(properties, '$.summary') LIKE ?)"
                    ]
                    params.extend([pattern, pattern, pattern])
                    where_conditions.append(f"({' OR '.join(pattern_conditions)})")

                elif tolerance == "fuzzy":
                    # Fuzzy mode: use same as normal for now (future: trigram similarity)
                    # Generate fuzzy patterns (exact match + stemmed variations)
                    patterns = _generate_fuzzy_patterns(search_query.query)

                    # Build OR condition for all patterns across all text fields
                    pattern_conditions = []
                    for pattern, weight in patterns:
                        # Each pattern matches against title, content, or summary
                        pattern_conditions.append(
                            "(json_extract(properties, '$.title') LIKE ? OR "
                            "json_extract(properties, '$.content') LIKE ? OR "
                            "json_extract(properties, '$.summary') LIKE ?)"
                        )
                        # Add pattern three times (once for each field)
                        params.extend([pattern, pattern, pattern])

                    # Combine all pattern conditions with OR
                    if pattern_conditions:
                        where_conditions.append(f"({' OR '.join(pattern_conditions)})")

                else:  # tolerance == "normal" (default)
                    # Normal mode: fuzzy matching with stemming
                    patterns = _generate_fuzzy_patterns(search_query.query)

                    # Build OR condition for all patterns across all text fields
                    pattern_conditions = []
                    for pattern, weight in patterns:
                        # Each pattern matches against title, content, or summary
                        pattern_conditions.append(
                            "(json_extract(properties, '$.title') LIKE ? OR "
                            "json_extract(properties, '$.content') LIKE ? OR "
                            "json_extract(properties, '$.summary') LIKE ?)"
                        )
                        # Add pattern three times (once for each field)
                        params.extend([pattern, pattern, pattern])

                    # Combine all pattern conditions with OR
                    if pattern_conditions:
                        where_conditions.append(f"({' OR '.join(pattern_conditions)})")

            # Memory type filter
            if search_query.memory_types:
                type_placeholders = ','.join('?' * len(search_query.memory_types))
                where_conditions.append(f"json_extract(properties, '$.type') IN ({type_placeholders})")
                params.extend([t.value for t in search_query.memory_types])

            # Tags filter (check if any tag matches)
            if search_query.tags:
                # For SQLite, we need to check JSON array
                tag_conditions = []
                for tag in search_query.tags:
                    tag_conditions.append("json_extract(properties, '$.tags') LIKE ?")
                    params.append(f'%"{tag}"%')
                where_conditions.append(f"({' OR '.join(tag_conditions)})")

            # Project path filter
            if search_query.project_path:
                where_conditions.append("json_extract(properties, '$.context_project_path') = ?")
                params.append(search_query.project_path)

            # Importance filter
            if search_query.min_importance is not None:
                where_conditions.append("CAST(json_extract(properties, '$.importance') AS REAL) >= ?")
                params.append(search_query.min_importance)

            # Confidence filter
            if search_query.min_confidence is not None:
                where_conditions.append("CAST(json_extract(properties, '$.confidence') AS REAL) >= ?")
                params.append(search_query.min_confidence)

            # Date filters
            if search_query.created_after:
                where_conditions.append("json_extract(properties, '$.created_at') >= ?")
                params.append(search_query.created_after.isoformat())

            if search_query.created_before:
                where_conditions.append("json_extract(properties, '$.created_at') <= ?")
                params.append(search_query.created_before.isoformat())

            # Build complete query
            where_clause = " AND ".join(where_conditions)
            query = f"""
                SELECT properties FROM nodes
                WHERE {where_clause}
                ORDER BY
                    CAST(json_extract(properties, '$.importance') AS REAL) DESC,
                    json_extract(properties, '$.created_at') DESC
                LIMIT ?
            """
            params.append(search_query.limit)

            result = self.backend.execute_sync(query, tuple(params))

            memories = []
            for row in result:
                properties = json.loads(row['properties'])
                memory = self._properties_to_memory(properties)
                if memory:
                    memories.append(memory)

            # Enrich results with relationships and match info if requested
            if search_query.include_relationships:
                # Use terms for enrichment if provided, otherwise use query
                search_text = (search_query.terms[0] if search_query.terms
                              else search_query.query)
                memories = await self._enrich_search_results(
                    memories,
                    search_text
                )

            # Apply relationship filter if specified
            if search_query.relationship_filter:
                filtered_memories = []
                for memory in memories:
                    # Check if memory has any of the specified relationship types
                    if hasattr(memory, 'relationships') and memory.relationships:
                        # relationships is a dict like {"SOLVES": ["title1", "title2"], ...}
                        has_matching_relationship = any(
                            rel_type in search_query.relationship_filter
                            for rel_type in memory.relationships.keys()
                        )
                        if has_matching_relationship:
                            filtered_memories.append(memory)
                    else:
                        # If relationship_filter is specified but memory has no relationships,
                        # we need to query relationships manually
                        query_rels = """
                            SELECT type FROM relationships
                            WHERE from_memory_id = ? OR to_memory_id = ?
                        """
                        rel_result = self.backend.execute_sync(
                            query_rels,
                            (memory.id, memory.id)
                        )
                        rel_types = {row['type'] for row in rel_result}
                        if any(rel_type in search_query.relationship_filter for rel_type in rel_types):
                            filtered_memories.append(memory)
                memories = filtered_memories

            logger.info(f"Found {len(memories)} memories for search query")
            return memories

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to search memories: {e}")
            raise DatabaseConnectionError(f"Failed to search memories: {e}")

    async def _enrich_search_results(
        self,
        memories: List[Memory],
        query: Optional[str] = None
    ) -> List[Memory]:
        """
        Enrich search results with relationship context and match quality hints.

        Args:
            memories: List of memories to enrich
            query: Original search query for match analysis

        Returns:
            List of enriched Memory objects with relationships, match_info, and context_summary
        """
        try:
            enriched_memories = []

            for memory in memories:
                # Get immediate relationships for this memory
                related = await self.get_related_memories(
                    memory.id,
                    relationship_types=None,  # Get all types
                    max_depth=1  # Only immediate relationships
                )

                # Group relationships by type
                relationships_by_type = {}
                for related_memory, relationship in related:
                    rel_type_key = relationship.type.value.lower()

                    if rel_type_key not in relationships_by_type:
                        relationships_by_type[rel_type_key] = []

                    # Add related memory title to the list
                    relationships_by_type[rel_type_key].append(related_memory.title)

                # Add match quality hints
                match_info = self._generate_match_info(memory, query)

                # Generate context summary
                context_summary = self._generate_context_summary(
                    memory,
                    relationships_by_type
                )

                # Update memory with enriched data
                memory.relationships = relationships_by_type if relationships_by_type else {}
                memory.match_info = match_info
                memory.context_summary = context_summary

                enriched_memories.append(memory)

            return enriched_memories

        except Exception as e:
            # If enrichment fails, log warning and return original memories
            logger.warning(f"Failed to enrich search results: {e}")
            return memories

    def _generate_match_info(
        self,
        memory: Memory,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate match quality hints for a search result.

        Args:
            memory: Memory object
            query: Search query string

        Returns:
            Dictionary with match information
        """
        matched_fields = []
        matched_terms = []
        match_quality = "low"

        if query:
            query_lower = query.lower()
            query_terms = query_lower.split()

            # Check which fields matched
            if memory.title and query_lower in memory.title.lower():
                matched_fields.append("title")
                match_quality = "high"  # Title matches are high quality

            if memory.content and query_lower in memory.content.lower():
                matched_fields.append("content")
                if match_quality == "low":
                    match_quality = "medium"

            if memory.summary and query_lower in memory.summary.lower():
                matched_fields.append("summary")
                if match_quality == "low":
                    match_quality = "medium"

            # Check tags
            for tag in memory.tags:
                if any(term in tag.lower() for term in query_terms):
                    matched_fields.append("tags")
                    break

            # Identify which terms matched
            for term in query_terms:
                term_found = False
                if memory.title and term in memory.title.lower():
                    term_found = True
                elif memory.content and term in memory.content.lower():
                    term_found = True
                elif memory.summary and term in memory.summary.lower():
                    term_found = True

                if term_found:
                    matched_terms.append(term)

        return {
            "matched_fields": matched_fields,
            "matched_terms": matched_terms,
            "match_quality": match_quality
        }

    def _generate_context_summary(
        self,
        memory: Memory,
        relationships: Dict[str, List[str]]
    ) -> str:
        """
        Generate a natural language context summary for a memory.

        Args:
            memory: Memory object
            relationships: Dict of relationship types to related memory titles

        Returns:
            Concise natural language summary (<100 chars)
        """
        summary_parts = []

        # Start with memory type
        summary_parts.append(memory.type.value.replace('_', ' ').capitalize())

        # Add key relationship information
        if 'solves' in relationships and relationships['solves']:
            problems = relationships['solves'][:2]  # Limit to 2
            summary_parts.append(f"solves {', '.join(problems)}")
        elif 'solved_by' in relationships and relationships['solved_by']:
            solutions = relationships['solved_by'][:1]
            summary_parts.append(f"solved by {solutions[0]}")

        if 'used_in' in relationships and relationships['used_in']:
            projects = relationships['used_in'][:1]
            summary_parts.append(f"in {projects[0]}")

        # Join parts with appropriate separators
        if len(summary_parts) == 1:
            return summary_parts[0]
        elif len(summary_parts) == 2:
            return f"{summary_parts[0]} {summary_parts[1]}"
        else:
            return f"{summary_parts[0]} {summary_parts[1]}, {summary_parts[2]}"

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

            memory.updated_at = datetime.now(UTC)

            # Convert memory to properties dict
            memory_node = MemoryNode(memory=memory)
            properties = memory_node.to_neo4j_properties()
            properties_json = json.dumps(properties)

            result = self.backend.execute_sync(
                """
                UPDATE nodes
                SET properties = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND label = 'Memory'
                """,
                (properties_json, memory.id)
            )

            self.backend.commit()

            # Check if any rows were updated
            # SQLite doesn't return affected rows in execute_sync result,
            # so we need to check if the memory exists
            check = self.backend.execute_sync(
                "SELECT id FROM nodes WHERE id = ? AND label = 'Memory'",
                (memory.id,)
            )

            success = len(check) > 0
            if success:
                logger.info(f"Updated memory: {memory.id}")

            return success

        except Exception as e:
            self.backend.rollback()
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
            # Check if memory exists
            existing = self.backend.execute_sync(
                "SELECT id FROM nodes WHERE id = ? AND label = 'Memory'",
                (memory_id,)
            )

            if not existing:
                return False

            # Delete relationships (CASCADE should handle this, but let's be explicit)
            self.backend.execute_sync(
                "DELETE FROM relationships WHERE from_id = ? OR to_id = ?",
                (memory_id, memory_id)
            )

            # Delete the memory node
            self.backend.execute_sync(
                "DELETE FROM nodes WHERE id = ? AND label = 'Memory'",
                (memory_id,)
            )

            self.backend.commit()
            logger.info(f"Deleted memory: {memory_id}")
            return True

        except Exception as e:
            self.backend.rollback()
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

            # Serialize properties as JSON
            properties_json = json.dumps(props_dict)

            # Verify both memories exist
            from_exists = self.backend.execute_sync(
                "SELECT id FROM nodes WHERE id = ? AND label = 'Memory'",
                (from_memory_id,)
            )
            to_exists = self.backend.execute_sync(
                "SELECT id FROM nodes WHERE id = ? AND label = 'Memory'",
                (to_memory_id,)
            )

            if not from_exists or not to_exists:
                raise RelationshipError(
                    f"One or both memories not found: {from_memory_id}, {to_memory_id}",
                    {"from_id": from_memory_id, "to_id": to_memory_id}
                )

            # Insert relationship
            self.backend.execute_sync(
                """
                INSERT INTO relationships (id, from_id, to_id, rel_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (relationship_id, from_memory_id, to_memory_id, relationship_type.value, properties_json)
            )

            self.backend.commit()
            logger.info(f"Created relationship: {relationship_type.value} between {from_memory_id} and {to_memory_id}")
            return relationship_id

        except Exception as e:
            self.backend.rollback()
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
            max_depth: Maximum depth for graph traversal (currently only supports depth 1)

        Returns:
            List of tuples containing (Memory, Relationship)

        Raises:
            DatabaseConnectionError: If query fails
        """
        try:
            # Build relationship type filter
            where_conditions = ["(r.from_id = ? OR r.to_id = ?)"]
            params = [memory_id, memory_id]

            if relationship_types:
                type_placeholders = ','.join('?' * len(relationship_types))
                where_conditions.append(f"r.rel_type IN ({type_placeholders})")
                params.extend([rt.value for rt in relationship_types])

            where_clause = " AND ".join(where_conditions)

            # Query for relationships and related nodes
            # For simplicity, we only do depth 1 (direct relationships)
            query = f"""
                SELECT
                    n.id as related_id,
                    n.properties as related_props,
                    r.id as rel_id,
                    r.rel_type as rel_type,
                    r.properties as rel_props,
                    r.from_id as rel_from,
                    r.to_id as rel_to
                FROM relationships r
                JOIN nodes n ON (
                    CASE
                        WHEN r.from_id = ? THEN n.id = r.to_id
                        WHEN r.to_id = ? THEN n.id = r.from_id
                    END
                )
                WHERE {where_clause}
                    AND n.label = 'Memory'
                    AND n.id != ?
                ORDER BY
                    CAST(json_extract(r.properties, '$.strength') AS REAL) DESC,
                    CAST(json_extract(n.properties, '$.importance') AS REAL) DESC
                LIMIT 20
            """

            # Add memory_id params for the JOIN conditions and final filter
            query_params = [memory_id, memory_id] + params + [memory_id]

            result = self.backend.execute_sync(query, tuple(query_params))

            related_memories = []
            for row in result:
                # Parse related memory
                related_props = json.loads(row['related_props'])
                memory = self._properties_to_memory(related_props)

                if memory:
                    # Parse relationship properties
                    rel_props = json.loads(row['rel_props'])
                    rel_type_str = row['rel_type']

                    try:
                        rel_type = RelationshipType(rel_type_str)
                    except ValueError:
                        rel_type = RelationshipType.RELATED_TO

                    relationship = Relationship(
                        id=row['rel_id'],
                        from_memory_id=row['rel_from'],
                        to_memory_id=row['rel_to'],
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

    async def search_relationships_by_context(
        self,
        scope: Optional[str] = None,
        conditions: Optional[List[str]] = None,
        has_evidence: Optional[bool] = None,
        evidence: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        temporal: Optional[str] = None,
        limit: int = 20
    ) -> List[Relationship]:
        """
        Search relationships by structured context fields.

        This method queries relationships based on their extracted context structure
        (scope, conditions, evidence, components, temporal). It parses the context
        JSON from each relationship and filters based on the provided criteria.

        Args:
            scope: Filter by scope (partial, full, conditional)
            conditions: Filter by conditions (OR logic - matches any)
            has_evidence: Filter by presence/absence of evidence
            evidence: Filter by specific evidence mentions (OR logic - matches any)
            components: Filter by components mentioned (OR logic - matches any)
            temporal: Filter by temporal information
            limit: Maximum number of results to return (default: 20)

        Returns:
            List of Relationship objects matching the criteria, ordered by strength

        Raises:
            DatabaseConnectionError: If query fails

        Examples:
            # Find all partial implementations
            await db.search_relationships_by_context(scope="partial")

            # Find relationships verified by tests
            await db.search_relationships_by_context(has_evidence=True)

            # Find production-only relationships
            await db.search_relationships_by_context(conditions=["production"])

            # Combined filters: partial scope AND production condition
            await db.search_relationships_by_context(
                scope="partial",
                conditions=["production"]
            )
        """
        from .utils.context_extractor import parse_context

        try:
            # Get all relationships
            query = """
                SELECT
                    r.id as rel_id,
                    r.from_id as rel_from,
                    r.to_id as rel_to,
                    r.rel_type as rel_type,
                    r.properties as rel_props
                FROM relationships r
            """

            result = self.backend.execute_sync(query)

            # Filter relationships in Python by parsing context
            matching_relationships = []

            for row in result:
                # Parse relationship properties
                rel_props = json.loads(row['rel_props'])
                context_text = rel_props.get("context")

                # Parse context to get structure
                context_struct = parse_context(context_text)

                # Apply filters
                matches = True

                # Filter by scope
                if scope is not None:
                    if context_struct.get("scope") != scope:
                        matches = False

                # Filter by conditions (OR logic - match any)
                if conditions is not None and matches:
                    if not context_struct.get("conditions"):
                        matches = False
                    else:
                        # Check if any provided condition matches any extracted condition
                        extracted_conditions = context_struct.get("conditions", [])
                        condition_match = any(
                            any(cond.lower() in extracted.lower() for extracted in extracted_conditions)
                            for cond in conditions
                        )
                        if not condition_match:
                            matches = False

                # Filter by evidence presence
                if has_evidence is not None and matches:
                    has_extracted_evidence = bool(context_struct.get("evidence"))
                    if has_evidence != has_extracted_evidence:
                        matches = False

                # Filter by specific evidence (OR logic - match any)
                if evidence is not None and matches:
                    if not context_struct.get("evidence"):
                        matches = False
                    else:
                        # Check if any provided evidence matches any extracted evidence
                        extracted_evidence = context_struct.get("evidence", [])
                        evidence_match = any(
                            any(ev.lower() in extracted.lower() for extracted in extracted_evidence)
                            for ev in evidence
                        )
                        if not evidence_match:
                            matches = False

                # Filter by components (OR logic - match any)
                if components is not None and matches:
                    if not context_struct.get("components"):
                        matches = False
                    else:
                        # Check if any provided component matches any extracted component
                        extracted_components = context_struct.get("components", [])
                        component_match = any(
                            any(comp.lower() in extracted.lower() for extracted in extracted_components)
                            for comp in components
                        )
                        if not component_match:
                            matches = False

                # Filter by temporal
                if temporal is not None and matches:
                    extracted_temporal = context_struct.get("temporal")
                    if not extracted_temporal or temporal.lower() not in extracted_temporal.lower():
                        matches = False

                # If all filters match, add to results
                if matches:
                    try:
                        rel_type = RelationshipType(row['rel_type'])
                    except ValueError:
                        rel_type = RelationshipType.RELATED_TO

                    relationship = Relationship(
                        id=row['rel_id'],
                        from_memory_id=row['rel_from'],
                        to_memory_id=row['rel_to'],
                        type=rel_type,
                        properties=RelationshipProperties(
                            strength=rel_props.get("strength", 0.5),
                            confidence=rel_props.get("confidence", 0.8),
                            context=rel_props.get("context"),
                            evidence_count=rel_props.get("evidence_count", 1)
                        )
                    )
                    matching_relationships.append(relationship)

            # Sort by strength (descending) and limit
            matching_relationships.sort(key=lambda r: r.properties.strength, reverse=True)
            matching_relationships = matching_relationships[:limit]

            logger.info(f"Found {len(matching_relationships)} relationships matching context filters")
            return matching_relationships

        except Exception as e:
            if isinstance(e, DatabaseConnectionError):
                raise
            logger.error(f"Failed to search relationships by context: {e}")
            raise DatabaseConnectionError(f"Failed to search relationships by context: {e}")

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics and metrics.

        Returns:
            Dictionary containing various database statistics

        Raises:
            DatabaseConnectionError: If query fails
        """
        try:
            stats = {}

            # Total memories
            result = self.backend.execute_sync(
                "SELECT COUNT(*) as count FROM nodes WHERE label = 'Memory'"
            )
            stats['total_memories'] = result[0] if result else {'count': 0}

            # Memories by type
            result = self.backend.execute_sync(
                """
                SELECT
                    json_extract(properties, '$.type') as type,
                    COUNT(*) as count
                FROM nodes
                WHERE label = 'Memory'
                GROUP BY json_extract(properties, '$.type')
                ORDER BY count DESC
                """
            )
            stats['memories_by_type'] = {row['type']: row['count'] for row in result} if result else {}

            # Total relationships
            result = self.backend.execute_sync(
                "SELECT COUNT(*) as count FROM relationships"
            )
            stats['total_relationships'] = result[0] if result else {'count': 0}

            # Average importance
            result = self.backend.execute_sync(
                """
                SELECT AVG(CAST(json_extract(properties, '$.importance') AS REAL)) as avg_importance
                FROM nodes
                WHERE label = 'Memory'
                """
            )
            stats['avg_importance'] = result[0] if result else {'avg_importance': 0}

            # Average confidence
            result = self.backend.execute_sync(
                """
                SELECT AVG(CAST(json_extract(properties, '$.confidence') AS REAL)) as avg_confidence
                FROM nodes
                WHERE label = 'Memory'
                """
            )
            stats['avg_confidence'] = result[0] if result else {'avg_confidence': 0}

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise DatabaseConnectionError(f"Failed to get statistics: {e}")

    async def get_recent_activity(
        self,
        days: int = 7,
        project: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recent activity summary for session briefing.

        Args:
            days: Number of days to look back (default: 7)
            project: Optional project path filter

        Returns:
            Dictionary containing:
            - total_count: Total number of memories in timeframe
            - memories_by_type: Count of memories grouped by type
            - recent_memories: List of recent memories (limited to 20)
            - unresolved_problems: List of problems with no SOLVES relationship
            - days: Number of days queried
            - project: Project filter applied (if any)

        Raises:
            DatabaseConnectionError: If query fails
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now(UTC) - timedelta(days=days)
            cutoff_iso = cutoff_date.isoformat()

            # Build WHERE conditions
            where_conditions = [
                "label = 'Memory'",
                "json_extract(properties, '$.created_at') >= ?"
            ]
            params = [cutoff_iso]

            # Add project filter if specified
            if project:
                where_conditions.append("json_extract(properties, '$.context_project_path') = ?")
                params.append(project)

            where_clause = " AND ".join(where_conditions)

            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM nodes WHERE {where_clause}"
            count_result = self.backend.execute_sync(count_query, tuple(params))
            total_count = count_result[0]['count'] if count_result else 0

            # Get memories by type
            type_query = f"""
                SELECT
                    json_extract(properties, '$.type') as type,
                    COUNT(*) as count
                FROM nodes
                WHERE {where_clause}
                GROUP BY json_extract(properties, '$.type')
            """
            type_result = self.backend.execute_sync(type_query, tuple(params))
            memories_by_type = {row['type']: row['count'] for row in type_result} if type_result else {}

            # Get recent memories (limited to 20)
            recent_query = f"""
                SELECT properties
                FROM nodes
                WHERE {where_clause}
                ORDER BY json_extract(properties, '$.created_at') DESC
                LIMIT 20
            """
            recent_result = self.backend.execute_sync(recent_query, tuple(params))

            recent_memories = []
            for row in recent_result:
                properties = json.loads(row['properties'])
                memory = self._properties_to_memory(properties)
                if memory:
                    recent_memories.append(memory)

            # Find unresolved problems (problems with no incoming SOLVES relationships)
            unresolved_query = f"""
                SELECT n.properties
                FROM nodes n
                WHERE {where_clause}
                    AND json_extract(properties, '$.type') IN ('problem', 'error')
                    AND NOT EXISTS (
                        SELECT 1
                        FROM relationships r
                        WHERE r.to_id = n.id
                            AND r.rel_type IN ('SOLVES', 'FIXES', 'ADDRESSES')
                    )
                ORDER BY CAST(json_extract(properties, '$.importance') AS REAL) DESC
                LIMIT 10
            """
            unresolved_result = self.backend.execute_sync(unresolved_query, tuple(params))

            unresolved_problems = []
            for row in unresolved_result:
                properties = json.loads(row['properties'])
                memory = self._properties_to_memory(properties)
                if memory:
                    unresolved_problems.append(memory)

            return {
                "total_count": total_count,
                "memories_by_type": memories_by_type,
                "recent_memories": recent_memories,
                "unresolved_problems": unresolved_problems,
                "days": days,
                "project": project
            }

        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            raise DatabaseConnectionError(f"Failed to get recent activity: {e}")

    def _properties_to_memory(self, properties: Dict[str, Any]) -> Optional[Memory]:
        """
        Convert properties dictionary to Memory object.

        Args:
            properties: Dictionary of memory properties

        Returns:
            Memory object or None if conversion fails
        """
        try:
            # Extract basic memory fields
            memory_data = {
                "id": properties.get("id"),
                "type": MemoryType(properties.get("type")),
                "title": properties.get("title"),
                "content": properties.get("content"),
                "summary": properties.get("summary"),
                "tags": properties.get("tags", []),
                "importance": properties.get("importance", 0.5),
                "confidence": properties.get("confidence", 0.8),
                "effectiveness": properties.get("effectiveness"),
                "usage_count": properties.get("usage_count", 0),
                "created_at": datetime.fromisoformat(properties.get("created_at")),
                "updated_at": datetime.fromisoformat(properties.get("updated_at")),
            }

            # Handle optional last_accessed field
            if properties.get("last_accessed"):
                memory_data["last_accessed"] = datetime.fromisoformat(properties["last_accessed"])

            # Extract context information
            context_data = {}
            for key, value in properties.items():
                if key.startswith("context_") and value is not None:
                    context_key = key[8:]  # Remove "context_" prefix

                    # Deserialize JSON strings back to Python objects
                    if isinstance(value, str) and context_key in ["additional_metadata", "files_involved", "languages", "frameworks", "technologies"]:
                        try:
                            context_data[context_key] = json.loads(value)
                        except json.JSONDecodeError:
                            context_data[context_key] = value
                    else:
                        context_data[context_key] = value

            if context_data:
                # Handle timestamp fields in context
                if "timestamp" in context_data and isinstance(context_data["timestamp"], str):
                    context_data["timestamp"] = datetime.fromisoformat(context_data["timestamp"])

                memory_data["context"] = MemoryContext(**context_data)

            return Memory(**memory_data)

        except Exception as e:
            logger.error(f"Failed to convert properties to Memory: {e}")
            return None
