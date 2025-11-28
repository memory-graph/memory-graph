"""
Temporal Memory - Track how information changes over time.

This module provides version tracking, memory history, and
temporal queries for understanding how knowledge evolves.
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TemporalMemory:
    """Handles temporal aspects of memories, including version tracking."""

    def __init__(self, backend):
        """
        Initialize temporal memory with database backend.

        Args:
            backend: Database backend instance
        """
        self.backend = backend

    async def get_memory_history(self, memory_id: str) -> list[dict]:
        """
        Get complete version history for a memory by traversing PREVIOUS relationships.

        Args:
            memory_id: ID of the memory to get history for

        Returns:
            List of memory versions in chronological order (oldest to newest)
        """
        query = """
        MATCH path = (current:Memory {id: $memory_id})-[:PREVIOUS*0..]->(older:Memory)
        WITH older, length(path) as depth
        ORDER BY depth DESC
        RETURN older.id as id,
               older.title as title,
               older.content as content,
               older.type as type,
               older.tags as tags,
               older.created_at as created_at,
               older.updated_at as updated_at,
               older.is_current as is_current,
               older.superseded_by as superseded_by,
               depth
        """

        params = {"memory_id": memory_id}

        try:
            results = await self.backend.execute_query(query, params)

            history = []
            for record in results:
                version = {
                    "id": record["id"],
                    "title": record.get("title"),
                    "content": record.get("content"),
                    "type": record.get("type"),
                    "tags": record.get("tags", []),
                    "created_at": record.get("created_at"),
                    "updated_at": record.get("updated_at"),
                    "is_current": record.get("is_current", True),
                    "superseded_by": record.get("superseded_by"),
                    "version_depth": record["depth"],
                }
                history.append(version)

            return history

        except Exception as e:
            logger.error(f"Error getting memory history for {memory_id}: {e}")
            return []

    async def get_state_at(
        self, memory_id: str, timestamp: datetime
    ) -> Optional[dict]:
        """
        Get the state of a memory at a specific point in time.

        Args:
            memory_id: ID of the memory
            timestamp: Target timestamp

        Returns:
            Memory state at that timestamp, or None if not found
        """
        query = """
        MATCH path = (current:Memory {id: $memory_id})-[:PREVIOUS*0..]->(older:Memory)
        WHERE older.created_at <= $timestamp
        WITH older, length(path) as depth
        ORDER BY depth ASC, older.created_at DESC
        LIMIT 1
        RETURN older.id as id,
               older.title as title,
               older.content as content,
               older.type as type,
               older.tags as tags,
               older.created_at as created_at,
               older.updated_at as updated_at,
               older.is_current as is_current
        """

        params = {"memory_id": memory_id, "timestamp": timestamp}

        try:
            results = await self.backend.execute_query(query, params)

            if not results:
                return None

            record = results[0]
            return {
                "id": record["id"],
                "title": record.get("title"),
                "content": record.get("content"),
                "type": record.get("type"),
                "tags": record.get("tags", []),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at"),
                "is_current": record.get("is_current", False),
                "queried_at": timestamp,
            }

        except Exception as e:
            logger.error(f"Error getting state at {timestamp} for {memory_id}: {e}")
            return None

    async def track_entity_changes(self, entity_id: str) -> list[dict]:
        """
        Track how an entity has changed over time by finding all memories that mention it.

        Args:
            entity_id: ID or text of the entity to track

        Returns:
            Timeline of changes to the entity
        """
        query = """
        MATCH (e:Entity)
        WHERE e.id = $entity_id OR e.text = $entity_id
        MATCH (m:Memory)-[r:MENTIONS]->(e)
        OPTIONAL MATCH (m)-[:PREVIOUS]->(prev:Memory)
        WITH m, e, prev,
             CASE WHEN prev IS NOT NULL
                  THEN exists((prev)-[:MENTIONS]->(e))
                  ELSE false
             END as was_mentioned_before
        RETURN m.id as memory_id,
               m.title as title,
               m.content as content,
               m.type as memory_type,
               m.created_at as created_at,
               m.updated_at as updated_at,
               r.confidence as mention_confidence,
               was_mentioned_before,
               CASE WHEN m.is_current = true THEN 'current'
                    WHEN m.superseded_by IS NOT NULL THEN 'superseded'
                    ELSE 'active'
               END as status
        ORDER BY m.created_at ASC
        """

        params = {"entity_id": entity_id}

        try:
            results = await self.backend.execute_query(query, params)

            timeline = []
            for record in results:
                change = {
                    "memory_id": record["memory_id"],
                    "title": record.get("title"),
                    "content": record.get("content"),
                    "memory_type": record.get("memory_type"),
                    "created_at": record.get("created_at"),
                    "updated_at": record.get("updated_at"),
                    "mention_confidence": record.get("mention_confidence"),
                    "was_new_mention": not record.get("was_mentioned_before", False),
                    "status": record.get("status", "active"),
                }
                timeline.append(change)

            return timeline

        except Exception as e:
            logger.error(f"Error tracking entity changes for {entity_id}: {e}")
            return []

    async def create_version(
        self,
        current_memory_id: str,
        new_memory: dict,
    ) -> str:
        """
        Create a new version of a memory, linking it to the previous version.

        Args:
            current_memory_id: ID of the current memory to supersede
            new_memory: New memory data

        Returns:
            ID of the new memory version
        """
        query = """
        MATCH (current:Memory {id: $current_id})
        CREATE (new:Memory)
        SET new = $new_props,
            new.id = randomUUID(),
            new.created_at = datetime(),
            new.updated_at = datetime(),
            new.is_current = true,
            current.is_current = false,
            current.superseded_by = new.id
        CREATE (new)-[:PREVIOUS {superseded_at: datetime()}]->(current)
        RETURN new.id as new_id
        """

        params = {
            "current_id": current_memory_id,
            "new_props": new_memory,
        }

        try:
            results = await self.backend.execute_query(query, params)

            if results:
                new_id = results[0]["new_id"]
                logger.info(f"Created new version {new_id} for memory {current_memory_id}")
                return new_id
            else:
                raise Exception("Failed to create new version")

        except Exception as e:
            logger.error(f"Error creating version for {current_memory_id}: {e}")
            raise

    async def get_version_diff(
        self, version1_id: str, version2_id: str
    ) -> dict[str, dict]:
        """
        Compare two versions of a memory and return differences.

        Args:
            version1_id: ID of first version
            version2_id: ID of second version

        Returns:
            Dictionary of changes between versions
        """
        query = """
        MATCH (v1:Memory {id: $v1_id})
        MATCH (v2:Memory {id: $v2_id})
        RETURN v1.title as v1_title, v2.title as v2_title,
               v1.content as v1_content, v2.content as v2_content,
               v1.type as v1_type, v2.type as v2_type,
               v1.tags as v1_tags, v2.tags as v2_tags,
               v1.updated_at as v1_updated, v2.updated_at as v2_updated
        """

        params = {"v1_id": version1_id, "v2_id": version2_id}

        try:
            results = await self.backend.execute_query(query, params)

            if not results:
                return {}

            record = results[0]
            diff = {}

            # Compare fields
            if record.get("v1_title") != record.get("v2_title"):
                diff["title"] = {
                    "from": record.get("v1_title"),
                    "to": record.get("v2_title"),
                }

            if record.get("v1_content") != record.get("v2_content"):
                diff["content"] = {
                    "from": record.get("v1_content"),
                    "to": record.get("v2_content"),
                }

            if record.get("v1_type") != record.get("v2_type"):
                diff["type"] = {
                    "from": record.get("v1_type"),
                    "to": record.get("v2_type"),
                }

            v1_tags = set(record.get("v1_tags", []))
            v2_tags = set(record.get("v2_tags", []))
            if v1_tags != v2_tags:
                diff["tags"] = {
                    "added": list(v2_tags - v1_tags),
                    "removed": list(v1_tags - v2_tags),
                }

            return diff

        except Exception as e:
            logger.error(f"Error comparing versions {version1_id} and {version2_id}: {e}")
            return {}


# Convenience functions


async def get_memory_history(backend, memory_id: str) -> list[dict]:
    """
    Get version history for a memory.

    Args:
        backend: Database backend instance
        memory_id: ID of the memory

    Returns:
        List of memory versions in chronological order

    Example:
        >>> history = await get_memory_history(backend, "memory-123")
        >>> for version in history:
        ...     print(f"Version created at {version['created_at']}")
    """
    temporal = TemporalMemory(backend)
    return await temporal.get_memory_history(memory_id)


async def get_state_at(
    backend, memory_id: str, timestamp: datetime
) -> Optional[dict]:
    """
    Get memory state at a specific timestamp.

    Args:
        backend: Database backend instance
        memory_id: ID of the memory
        timestamp: Target timestamp

    Returns:
        Memory state at that time, or None

    Example:
        >>> from datetime import datetime, timedelta
        >>> yesterday = datetime.utcnow() - timedelta(days=1)
        >>> state = await get_state_at(backend, "memory-123", yesterday)
    """
    temporal = TemporalMemory(backend)
    return await temporal.get_state_at(memory_id, timestamp)


async def track_entity_changes(backend, entity_id: str) -> list[dict]:
    """
    Track entity changes over time.

    Args:
        backend: Database backend instance
        entity_id: ID or text of the entity

    Returns:
        Timeline of entity mentions and changes

    Example:
        >>> timeline = await track_entity_changes(backend, "React")
        >>> for change in timeline:
        ...     print(f"{change['created_at']}: {change['title']}")
    """
    temporal = TemporalMemory(backend)
    return await temporal.track_entity_changes(entity_id)
