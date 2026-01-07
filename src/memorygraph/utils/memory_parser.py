"""Shared memory parsing utilities."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..models import Memory, MemoryType, MemoryContext

logger = logging.getLogger(__name__)


def parse_memory_from_properties(
    node_data: Dict[str, Any],
    source: str = "unknown"
) -> Optional[Memory]:
    """
    Convert database node properties to Memory object.

    Works with Neo4j, FalkorDB, SQLite, and other backends.

    Args:
        node_data: Dictionary of node properties
        source: Source backend name for logging

    Returns:
        Memory object or None if parsing fails
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
            "created_at": _parse_datetime(node_data.get("created_at")),
            "updated_at": _parse_datetime(node_data.get("updated_at")),
        }

        # Handle optional last_accessed field
        if node_data.get("last_accessed"):
            memory_data["last_accessed"] = _parse_datetime(node_data["last_accessed"])

        # Extract context information
        context_data = _extract_context(node_data)
        if context_data:
            memory_data["context"] = MemoryContext(**context_data)

        return Memory(**memory_data)

    except Exception as e:
        logger.error(f"Failed to parse memory from {source}: {e}")
        return None


def _parse_datetime(value: Any) -> datetime:
    """Parse datetime from string or return as-is if already datetime."""
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def _extract_context(node_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract context fields from node data."""
    context_data = {}
    for key, value in node_data.items():
        if key.startswith("context_") and value is not None:
            context_key = key[8:]  # Remove "context_" prefix

            # Deserialize JSON strings
            if isinstance(value, str) and context_key in ["additional_metadata"]:
                try:
                    context_data[context_key] = json.loads(value)
                except json.JSONDecodeError:
                    context_data[context_key] = value
            elif isinstance(value, str) and value.startswith(('[', '{')):
                try:
                    context_data[context_key] = json.loads(value)
                except json.JSONDecodeError:
                    context_data[context_key] = value
            else:
                context_data[context_key] = value

    # Handle timestamp fields in context
    if "timestamp" in context_data and isinstance(context_data["timestamp"], str):
        context_data["timestamp"] = datetime.fromisoformat(context_data["timestamp"])

    return context_data
