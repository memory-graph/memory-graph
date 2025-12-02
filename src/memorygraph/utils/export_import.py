"""
Export and import utilities for MemoryGraph data.

Supports JSON and Markdown export formats.
"""

import json
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..models import Memory, MemoryType, MemoryContext, RelationshipType, RelationshipProperties
from ..sqlite_database import SQLiteMemoryDatabase

logger = logging.getLogger(__name__)


async def export_to_json(db: SQLiteMemoryDatabase, output_path: str) -> None:
    """
    Export all memories and relationships to JSON format.

    Args:
        db: Database instance
        output_path: Path to output JSON file

    Raises:
        IOError: If file cannot be written
    """
    # Get all memories by querying database directly (no limit)
    query = "SELECT properties FROM nodes WHERE label = 'Memory' ORDER BY created_at DESC"
    rows = db.backend.execute_sync(query)

    all_memories = []
    for row in rows:
        properties = json.loads(row['properties'])
        memory = db._properties_to_memory(properties)
        if memory:
            all_memories.append(memory)

    # Get all relationships (query directly from backend)
    query = "SELECT id, from_id, to_id, rel_type, properties FROM relationships"
    rel_rows = db.backend.execute_sync(query)

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

    # Convert relationships to dict format
    relationships_data = []
    for row in rel_rows:
        props = json.loads(row['properties'])
        rel_dict = {
            "id": row['id'],
            "from_memory_id": row['from_id'],
            "to_memory_id": row['to_id'],
            "type": row['rel_type'],
            "properties": {
                "strength": props.get("strength", 0.5),
                "confidence": props.get("confidence", 0.8),
                "context": props.get("context"),
                "evidence_count": props.get("evidence_count", 1)
            }
        }
        relationships_data.append(rel_dict)

    # Create export data structure
    export_data = {
        "export_version": "1.0",
        "export_date": datetime.now(UTC).isoformat(),
        "memories": memories_data,
        "relationships": relationships_data
    }

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)

    logger.info(f"Exported {len(memories_data)} memories and {len(relationships_data)} relationships to {output_path}")


async def import_from_json(
    db: SQLiteMemoryDatabase,
    input_path: str,
    skip_duplicates: bool = False
) -> Dict[str, int]:
    """
    Import memories and relationships from JSON format.

    Args:
        db: Database instance
        input_path: Path to input JSON file
        skip_duplicates: If True, skip memories with existing IDs

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

    imported_memories = 0
    skipped_memories = 0

    # Import memories
    for mem_data in data["memories"]:
        try:
            # Check if memory already exists
            if skip_duplicates:
                existing = await db.get_memory(mem_data["id"], include_relationships=False)
                if existing:
                    skipped_memories += 1
                    logger.debug(f"Skipping duplicate memory: {mem_data['id']}")
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

        except Exception as e:
            logger.error(f"Failed to import memory {mem_data.get('id')}: {e}")
            skipped_memories += 1

    # Import relationships
    imported_relationships = 0
    skipped_relationships = 0

    for rel_data in data["relationships"]:
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


async def export_to_markdown(db: SQLiteMemoryDatabase, output_dir: str) -> None:
    """
    Export all memories to Markdown files.

    Creates one .md file per memory with frontmatter and content.

    Args:
        db: Database instance
        output_dir: Directory to write Markdown files

    Raises:
        IOError: If files cannot be written
    """
    # Get all memories by querying database directly (no limit)
    query = "SELECT properties FROM nodes WHERE label = 'Memory' ORDER BY created_at DESC"
    rows = db.backend.execute_sync(query)

    all_memories = []
    for row in rows:
        properties = json.loads(row['properties'])
        memory = db._properties_to_memory(properties)
        if memory:
            all_memories.append(memory)

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
