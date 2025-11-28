"""
Intelligence Layer - AI-powered features for the memory server.

This module provides:
- Automatic entity extraction from memory content
- Pattern recognition and similarity matching
- Temporal memory tracking and version history
- Context-aware intelligent retrieval
"""

from memorygraph.intelligence.entity_extraction import (
    EntityType,
    Entity,
    EntityExtractor,
    extract_entities,
    link_entities,
)
from memorygraph.intelligence.pattern_recognition import (
    PatternRecognizer,
    find_similar_problems,
    extract_patterns,
    suggest_patterns,
)
from memorygraph.intelligence.temporal import (
    TemporalMemory,
    get_memory_history,
    get_state_at,
    track_entity_changes,
)
from memorygraph.intelligence.context_retrieval import (
    ContextRetriever,
    get_context,
    get_project_context,
    get_session_context,
)

__all__ = [
    # Entity Extraction
    "EntityType",
    "Entity",
    "EntityExtractor",
    "extract_entities",
    "link_entities",
    # Pattern Recognition
    "PatternRecognizer",
    "find_similar_problems",
    "extract_patterns",
    "suggest_patterns",
    # Temporal Memory
    "TemporalMemory",
    "get_memory_history",
    "get_state_at",
    "track_entity_changes",
    # Context Retrieval
    "ContextRetriever",
    "get_context",
    "get_project_context",
    "get_session_context",
]
