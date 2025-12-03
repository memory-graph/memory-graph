"""
Export and import utilities for MemoryGraph data.

Supports JSON and Markdown export formats.
Works with all backends (SQLite, Neo4j, Memgraph, FalkorDB, FalkorDBLite).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set, Tuple, Union

from ..models import (
    Memory, MemoryType, MemoryContext, RelationshipType, RelationshipProperties,
    SearchQuery, Relationship
)
from .pagination import paginate_memories

logger = logging.getLogger(__name__)


async def _export_relationships(
    db,  # MemoryDatabase or SQLiteMemoryDatabase
    memories: List[Memory]
) -> List[Dict[str, Any]]:
    """
    Export all relationships for given memories using backend-agnostic methods.

    Args:
        db: Database instance (any backend)
        memories: List of memories to export relationships for

    Returns:
        List of relationship dictionaries
    """
    relationships_map: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    for memory in memories:
        try:
            related = await db.get_related_memories(
                memory_id=memory.id,
                max_depth=1
            )

            for related_memory, relationship in related:
                # Use tuple as key for deduplication (from_id, to_id, type)
                key = (relationship.from_memory_id, relationship.to_memory_id, relationship.type.value)

                if key not in relationships_map:
                    rel_dict = {
                        "from_memory_id": relationship.from_memory_id,
                        "to_memory_id": relationship.to_memory_id,
                        "type": relationship.type.value,
                        "properties": {
                            "strength": relationship.properties.strength,
                            "confidence": relationship.properties.confidence,
                            "context": relationship.properties.context,
                            "evidence_count": relationship.properties.evidence_count
                        }
                    }
                    relationships_map[key] = rel_dict
        except Exception as e:
            logger.warning(f"Failed to export relationships for memory {memory.id}: {e}")
            continue

    return list(relationships_map.values())


async def export_to_json(
    db,  # MemoryDatabase or SQLiteMemoryDatabase
    output_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]:
    """
    Export all memories and relationships to JSON format.

    Works with ANY backend by using the MemoryDatabase interface.

    Args:
        db: Database instance (works with all backends)
        output_path: Path to output JSON file
        progress_callback: Optional callback(current, total) for progress reporting

    Returns:
        Dictionary with export statistics

    Raises:
        IOError: If file cannot be written
    """
    logger.info("Starting backend-agnostic export...")

    # Export memories in batches using pagination helper
    all_memories = []

    def progress_reporter(count: int):
        if progress_callback:
            # We don't know total in advance without an extra query, so pass current count twice
            progress_callback(count, count)

    async for batch in paginate_memories(db, batch_size=1000, progress_callback=progress_reporter):
        all_memories.extend(batch)

    logger.info(f"Exported {len(all_memories)} memories")

    # Export relationships using backend-agnostic method
    relationships_data = await _export_relationships(db, all_memories)

    logger.info(f"Exported {len(relationships_data)} relationships")

    # Convert memories to dict format
    memories_data = []
    for memory in all_memories:
        memory_dict = {
            "id": memory.id,
            "type": memory.type.value,
            "title": memory.title,
            "content": memory.content,
            "summary": memory.summary,
            "tags": memory.tags,
            "importance": memory.importance,
            "confidence": memory.confidence,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat()
        }

        # Add context if present
        if memory.context:
            memory_dict["context"] = {}
            for field in ["project_path", "function_name", "class_name", "files_involved",
                         "languages", "frameworks", "technologies", "environment", "additional_metadata"]:
                value = getattr(memory.context, field, None)
                if value is not None:
                    memory_dict["context"][field] = value

        memories_data.append(memory_dict)

    # Get backend name if available
    backend_type = "unknown"
    if hasattr(db, 'backend') and hasattr(db.backend, 'backend_name'):
        backend_type = db.backend.backend_name()
    elif hasattr(db, 'connection') and hasattr(db.connection, 'backend_name'):
        backend_type = db.connection.backend_name()

    # Create export data structure (format v2.0 for universal export)
    export_data = {
        "format_version": "2.0",
        "export_version": "1.0",  # Keep for backward compatibility
        "export_date": datetime.now(timezone.utc).isoformat(),
        "backend_type": backend_type,
        "memory_count": len(memories_data),
        "relationship_count": len(relationships_data),
        "memories": memories_data,
        "relationships": relationships_data
    }

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)

    logger.info(f"Export complete: {len(memories_data)} memories and {len(relationships_data)} relationships to {output_path}")

    return {
        "memory_count": len(memories_data),
        "relationship_count": len(relationships_data),
        "backend_type": backend_type,
        "output_path": output_path
    }


async def import_from_json(
    db,  # MemoryDatabase or SQLiteMemoryDatabase
    input_path: str,
    skip_duplicates: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Dict[str, int]:
    """
    Import memories and relationships from JSON format.

    Works with ANY backend by using the MemoryDatabase interface.

    Args:
        db: Database instance (works with all backends)
        input_path: Path to input JSON file
        skip_duplicates: If True, skip memories with existing IDs
        progress_callback: Optional callback(current, total) for progress reporting

    Returns:
        Dictionary with import statistics:
        - imported_memories: Number of memories imported
        - imported_relationships: Number of relationships imported
        - skipped_memories: Number of duplicate memories skipped
        - skipped_relationships: Number of invalid relationships skipped

    Raises:
        IOError: If file cannot be read
        ValueError: If JSON format is invalid
    """
    # Read JSON file
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Validate structure
    if "memories" not in data or "relationships" not in data:
        raise ValueError("Invalid export format: missing 'memories' or 'relationships'")

    # Validate format version (support both v1.0 and v2.0)
    format_version = data.get("format_version") or data.get("export_version")
    if not format_version:
        raise ValueError("Invalid export format: missing version information")

    logger.info(f"Importing from export format {format_version}")

    # Validate required fields in memories
    for mem_data in data["memories"]:
        required_fields = ["id", "type", "title", "content"]
        missing_fields = [field for field in required_fields if field not in mem_data]
        if missing_fields:
            raise ValueError(f"Invalid memory data: missing fields {missing_fields}")

    # Validate memory IDs are unique in export
    memory_ids = set()
    duplicate_ids = []
    for mem_data in data["memories"]:
        mem_id = mem_data["id"]
        if mem_id in memory_ids:
            duplicate_ids.append(mem_id)
        memory_ids.add(mem_id)

    if duplicate_ids:
        raise ValueError(f"Invalid export: duplicate memory IDs found: {duplicate_ids}")

    # Validate relationship endpoints exist in export
    for rel_data in data["relationships"]:
        from_id = rel_data.get("from_memory_id")
        to_id = rel_data.get("to_memory_id")
        if from_id not in memory_ids or to_id not in memory_ids:
            logger.warning(f"Relationship references missing memory: {from_id} -> {to_id}")

    imported_memories = 0
    skipped_memories = 0
    total_memories = len(data["memories"])

    # Import memories
    for idx, mem_data in enumerate(data["memories"], 1):
        try:
            # Check if memory already exists
            if skip_duplicates:
                existing = await db.get_memory(mem_data["id"], include_relationships=False)
                if existing:
                    skipped_memories += 1
                    logger.debug(f"Skipping duplicate memory: {mem_data['id']}")
                    if progress_callback:
                        progress_callback(idx, total_memories)
                    continue

            # Create Memory object
            memory = Memory(
                id=mem_data["id"],
                type=MemoryType(mem_data["type"]),
                title=mem_data["title"],
                content=mem_data["content"],
                summary=mem_data.get("summary"),
                tags=mem_data.get("tags", []),
                importance=mem_data.get("importance", 0.5),
                confidence=mem_data.get("confidence", 0.8)
            )

            # Add context if present
            if "context" in mem_data:
                ctx_data = mem_data["context"]
                memory.context = MemoryContext(**ctx_data)

            # Store memory
            await db.store_memory(memory)
            imported_memories += 1

            if progress_callback:
                progress_callback(idx, total_memories)

        except Exception as e:
            logger.error(f"Failed to import memory {mem_data.get('id')}: {e}")
            skipped_memories += 1

    # Import relationships
    imported_relationships = 0
    skipped_relationships = 0
    total_relationships = len(data["relationships"])

    for idx, rel_data in enumerate(data["relationships"], 1):
        try:
            # Verify both memories exist
            from_mem = await db.get_memory(rel_data["from_memory_id"], include_relationships=False)
            to_mem = await db.get_memory(rel_data["to_memory_id"], include_relationships=False)

            if not from_mem or not to_mem:
                logger.warning(f"Skipping relationship: one or both memories not found")
                skipped_relationships += 1
                continue

            # Create relationship
            props_data = rel_data.get("properties", {})
            properties = RelationshipProperties(
                strength=props_data.get("strength", 0.5),
                confidence=props_data.get("confidence", 0.8),
                context=props_data.get("context"),
                evidence_count=props_data.get("evidence_count", 1)
            )

            await db.create_relationship(
                from_memory_id=rel_data["from_memory_id"],
                to_memory_id=rel_data["to_memory_id"],
                relationship_type=RelationshipType(rel_data["type"]),
                properties=properties
            )
            imported_relationships += 1

        except Exception as e:
            logger.error(f"Failed to import relationship: {e}")
            skipped_relationships += 1

    logger.info(
        f"Import complete: {imported_memories} memories, {imported_relationships} relationships "
        f"({skipped_memories} memories skipped, {skipped_relationships} relationships skipped)"
    )

    return {
        "imported_memories": imported_memories,
        "imported_relationships": imported_relationships,
        "skipped_memories": skipped_memories,
        "skipped_relationships": skipped_relationships
    }


async def export_to_markdown(
    db,  # MemoryDatabase or SQLiteMemoryDatabase
    output_dir: str
) -> None:
    """
    Export all memories to Markdown files.

    Creates one .md file per memory with frontmatter and content.
    Works with ANY backend by using the MemoryDatabase interface.

    Args:
        db: Database instance (works with all backends)
        output_dir: Directory to write Markdown files

    Raises:
        IOError: If files cannot be written
    """
    logger.info("Starting backend-agnostic markdown export...")

    # Get all memories using pagination helper
    all_memories = []
    async for batch in paginate_memories(db, batch_size=1000):
        all_memories.extend(batch)

    logger.info(f"Exporting {len(all_memories)} memories to markdown...")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for memory in all_memories:
        # Create safe filename from title
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in memory.title)
        safe_title = safe_title.replace(' ', '_')
        filename = f"{safe_title}_{memory.id[:8]}.md"

        # Get relationships for this memory
        related = await db.get_related_memories(memory.id, max_depth=1)

        # Build Markdown content
        content_lines = [
            "---",
            f"title: {memory.title}",
            f"id: {memory.id}",
            f"type: {memory.type.value}",
            f"importance: {memory.importance}",
            f"confidence: {memory.confidence}",
            f"tags: [{', '.join(memory.tags)}]",
            f"created_at: {memory.created_at.isoformat()}",
            f"updated_at: {memory.updated_at.isoformat()}"
        ]

        # Add context
        if memory.context:
            if memory.context.project_path:
                content_lines.append(f"project: {memory.context.project_path}")
            if memory.context.languages:
                content_lines.append(f"languages: [{', '.join(memory.context.languages)}]")
            if memory.context.technologies:
                content_lines.append(f"technologies: [{', '.join(memory.context.technologies)}]")

        content_lines.append("---")
        content_lines.append("")

        # Add summary if present
        if memory.summary:
            content_lines.append(f"## Summary\n")
            content_lines.append(memory.summary)
            content_lines.append("")

        # Add main content
        content_lines.append(f"## Content\n")
        content_lines.append(memory.content)
        content_lines.append("")

        # Add relationships
        if related:
            content_lines.append(f"## Relationships\n")
            for related_memory, relationship in related:
                content_lines.append(
                    f"- **{relationship.type.value}** → [{related_memory.title}]({related_memory.id})"
                )
            content_lines.append("")

        # Write file
        file_path = output_path / filename
        file_path.write_text('\n'.join(content_lines))

    logger.info(f"Exported {len(all_memories)} memories to {output_dir}")
