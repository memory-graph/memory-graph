"""
Advanced relationship management for Claude Code Memory Server.

This module implements the full 35-relationship type system with weighted
relationships, graph analytics, and intelligent relationship evolution.

Phase 4 Implementation - Advanced Relationship System
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from .models import (
    RelationshipType,
    RelationshipProperties,
    Relationship,
    Memory,
    RelationshipError
)

logger = logging.getLogger(__name__)


class RelationshipCategory(str, Enum):
    """
    Categories that group related relationship types together.

    Each category represents a different semantic dimension of how
    memories can relate to each other.
    """

    CAUSAL = "causal"          # Cause-and-effect relationships
    SOLUTION = "solution"      # Problem-solving relationships
    CONTEXT = "context"        # Environmental/situational relationships
    LEARNING = "learning"      # Knowledge building relationships
    SIMILARITY = "similarity"  # Similarity and analogy relationships
    WORKFLOW = "workflow"      # Sequential and dependency relationships
    QUALITY = "quality"        # Effectiveness and preference relationships


@dataclass
class RelationshipTypeMetadata:
    """
    Metadata describing a relationship type's characteristics.

    Attributes:
        category: The category this relationship belongs to
        description: Human-readable description of the relationship
        bidirectional: Whether the relationship implies a reverse relationship
        default_strength: Default strength value (0.0 to 1.0)
        default_confidence: Default confidence value (0.0 to 1.0)
        inverse_type: The inverse relationship type (if bidirectional)
    """

    category: RelationshipCategory
    description: str
    bidirectional: bool = False
    default_strength: float = 0.5
    default_confidence: float = 0.8
    inverse_type: Optional[RelationshipType] = None


# Complete metadata for all 35 relationship types
RELATIONSHIP_TYPE_METADATA: Dict[RelationshipType, RelationshipTypeMetadata] = {
    # Causal relationships (5 types)
    RelationshipType.CAUSES: RelationshipTypeMetadata(
        category=RelationshipCategory.CAUSAL,
        description="Memory A causes or directly triggers Memory B",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.7,
    ),
    RelationshipType.TRIGGERS: RelationshipTypeMetadata(
        category=RelationshipCategory.CAUSAL,
        description="Memory A initiates or activates Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.LEADS_TO: RelationshipTypeMetadata(
        category=RelationshipCategory.CAUSAL,
        description="Memory A eventually results in Memory B",
        bidirectional=False,
        default_strength=0.6,
        default_confidence=0.6,
    ),
    RelationshipType.PREVENTS: RelationshipTypeMetadata(
        category=RelationshipCategory.CAUSAL,
        description="Memory A prevents or blocks Memory B from occurring",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.BREAKS: RelationshipTypeMetadata(
        category=RelationshipCategory.CAUSAL,
        description="Memory A breaks or disrupts Memory B",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.7,
    ),

    # Solution relationships (5 types)
    RelationshipType.SOLVES: RelationshipTypeMetadata(
        category=RelationshipCategory.SOLUTION,
        description="Memory A solves the problem described in Memory B",
        bidirectional=False,
        default_strength=0.9,
        default_confidence=0.8,
    ),
    RelationshipType.ADDRESSES: RelationshipTypeMetadata(
        category=RelationshipCategory.SOLUTION,
        description="Memory A addresses or partially solves Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.ALTERNATIVE_TO: RelationshipTypeMetadata(
        category=RelationshipCategory.SOLUTION,
        description="Memory A is an alternative approach to Memory B",
        bidirectional=True,
        default_strength=0.6,
        default_confidence=0.7,
        inverse_type=RelationshipType.ALTERNATIVE_TO,
    ),
    RelationshipType.IMPROVES: RelationshipTypeMetadata(
        category=RelationshipCategory.SOLUTION,
        description="Memory A improves upon Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.REPLACES: RelationshipTypeMetadata(
        category=RelationshipCategory.SOLUTION,
        description="Memory A replaces or supersedes Memory B",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.8,
    ),

    # Context relationships (5 types)
    RelationshipType.OCCURS_IN: RelationshipTypeMetadata(
        category=RelationshipCategory.CONTEXT,
        description="Memory A occurs within the context of Memory B",
        bidirectional=False,
        default_strength=0.6,
        default_confidence=0.8,
    ),
    RelationshipType.APPLIES_TO: RelationshipTypeMetadata(
        category=RelationshipCategory.CONTEXT,
        description="Memory A applies to or is relevant in Memory B context",
        bidirectional=False,
        default_strength=0.6,
        default_confidence=0.7,
    ),
    RelationshipType.WORKS_WITH: RelationshipTypeMetadata(
        category=RelationshipCategory.CONTEXT,
        description="Memory A works together with Memory B",
        bidirectional=True,
        default_strength=0.7,
        default_confidence=0.7,
        inverse_type=RelationshipType.WORKS_WITH,
    ),
    RelationshipType.REQUIRES: RelationshipTypeMetadata(
        category=RelationshipCategory.CONTEXT,
        description="Memory A requires Memory B to function",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.8,
    ),
    RelationshipType.USED_IN: RelationshipTypeMetadata(
        category=RelationshipCategory.CONTEXT,
        description="Memory A is used within Memory B",
        bidirectional=False,
        default_strength=0.6,
        default_confidence=0.7,
    ),

    # Learning relationships (5 types)
    RelationshipType.BUILDS_ON: RelationshipTypeMetadata(
        category=RelationshipCategory.LEARNING,
        description="Memory A builds upon knowledge from Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.8,
    ),
    RelationshipType.CONTRADICTS: RelationshipTypeMetadata(
        category=RelationshipCategory.LEARNING,
        description="Memory A contradicts information in Memory B",
        bidirectional=True,
        default_strength=0.8,
        default_confidence=0.6,
        inverse_type=RelationshipType.CONTRADICTS,
    ),
    RelationshipType.CONFIRMS: RelationshipTypeMetadata(
        category=RelationshipCategory.LEARNING,
        description="Memory A confirms or validates Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.8,
    ),
    RelationshipType.GENERALIZES: RelationshipTypeMetadata(
        category=RelationshipCategory.LEARNING,
        description="Memory A is a generalization of Memory B",
        bidirectional=False,
        default_strength=0.6,
        default_confidence=0.7,
        inverse_type=RelationshipType.SPECIALIZES,
    ),
    RelationshipType.SPECIALIZES: RelationshipTypeMetadata(
        category=RelationshipCategory.LEARNING,
        description="Memory A is a specialization of Memory B",
        bidirectional=False,
        default_strength=0.6,
        default_confidence=0.7,
        inverse_type=RelationshipType.GENERALIZES,
    ),

    # Similarity relationships (5 types)
    RelationshipType.SIMILAR_TO: RelationshipTypeMetadata(
        category=RelationshipCategory.SIMILARITY,
        description="Memory A is similar to Memory B",
        bidirectional=True,
        default_strength=0.6,
        default_confidence=0.7,
        inverse_type=RelationshipType.SIMILAR_TO,
    ),
    RelationshipType.VARIANT_OF: RelationshipTypeMetadata(
        category=RelationshipCategory.SIMILARITY,
        description="Memory A is a variant or version of Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.RELATED_TO: RelationshipTypeMetadata(
        category=RelationshipCategory.SIMILARITY,
        description="Memory A is related to Memory B in some way",
        bidirectional=True,
        default_strength=0.5,
        default_confidence=0.6,
        inverse_type=RelationshipType.RELATED_TO,
    ),
    RelationshipType.ANALOGY_TO: RelationshipTypeMetadata(
        category=RelationshipCategory.SIMILARITY,
        description="Memory A serves as an analogy for Memory B",
        bidirectional=False,
        default_strength=0.5,
        default_confidence=0.6,
    ),
    RelationshipType.OPPOSITE_OF: RelationshipTypeMetadata(
        category=RelationshipCategory.SIMILARITY,
        description="Memory A is the opposite or inverse of Memory B",
        bidirectional=True,
        default_strength=0.7,
        default_confidence=0.7,
        inverse_type=RelationshipType.OPPOSITE_OF,
    ),

    # Workflow relationships (5 types)
    RelationshipType.FOLLOWS: RelationshipTypeMetadata(
        category=RelationshipCategory.WORKFLOW,
        description="Memory A follows Memory B in a sequence",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.8,
    ),
    RelationshipType.DEPENDS_ON: RelationshipTypeMetadata(
        category=RelationshipCategory.WORKFLOW,
        description="Memory A depends on Memory B being completed first",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.8,
    ),
    RelationshipType.ENABLES: RelationshipTypeMetadata(
        category=RelationshipCategory.WORKFLOW,
        description="Memory A enables or allows Memory B to occur",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.BLOCKS: RelationshipTypeMetadata(
        category=RelationshipCategory.WORKFLOW,
        description="Memory A blocks or prevents Memory B from proceeding",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.7,
    ),
    RelationshipType.PARALLEL_TO: RelationshipTypeMetadata(
        category=RelationshipCategory.WORKFLOW,
        description="Memory A can occur in parallel with Memory B",
        bidirectional=True,
        default_strength=0.6,
        default_confidence=0.7,
        inverse_type=RelationshipType.PARALLEL_TO,
    ),

    # Quality relationships (5 types)
    RelationshipType.EFFECTIVE_FOR: RelationshipTypeMetadata(
        category=RelationshipCategory.QUALITY,
        description="Memory A is effective for solving Memory B",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.7,
    ),
    RelationshipType.INEFFECTIVE_FOR: RelationshipTypeMetadata(
        category=RelationshipCategory.QUALITY,
        description="Memory A is ineffective for solving Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.PREFERRED_OVER: RelationshipTypeMetadata(
        category=RelationshipCategory.QUALITY,
        description="Memory A is preferred over Memory B",
        bidirectional=False,
        default_strength=0.7,
        default_confidence=0.7,
    ),
    RelationshipType.DEPRECATED_BY: RelationshipTypeMetadata(
        category=RelationshipCategory.QUALITY,
        description="Memory A is deprecated by Memory B",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.8,
        inverse_type=RelationshipType.REPLACES,
    ),
    RelationshipType.VALIDATED_BY: RelationshipTypeMetadata(
        category=RelationshipCategory.QUALITY,
        description="Memory A is validated or proven by Memory B",
        bidirectional=False,
        default_strength=0.8,
        default_confidence=0.8,
    ),
}


class RelationshipManager:
    """
    Manages advanced relationship operations including creation,
    validation, evolution, and graph analytics.

    This class provides high-level relationship management on top of
    the backend storage layer.
    """

    def __init__(self):
        """Initialize the relationship manager."""
        self.metadata = RELATIONSHIP_TYPE_METADATA

    def get_relationship_metadata(
        self,
        relationship_type: RelationshipType
    ) -> RelationshipTypeMetadata:
        """
        Get metadata for a relationship type.

        Args:
            relationship_type: The relationship type to look up

        Returns:
            Metadata for the relationship type

        Raises:
            ValueError: If relationship type is not recognized
        """
        if relationship_type not in self.metadata:
            raise ValueError(f"Unknown relationship type: {relationship_type}")

        return self.metadata[relationship_type]

    def get_relationship_category(
        self,
        relationship_type: RelationshipType
    ) -> RelationshipCategory:
        """
        Get the category for a relationship type.

        Args:
            relationship_type: The relationship type

        Returns:
            The category this relationship belongs to
        """
        metadata = self.get_relationship_metadata(relationship_type)
        return metadata.category

    def get_types_by_category(
        self,
        category: RelationshipCategory
    ) -> List[RelationshipType]:
        """
        Get all relationship types in a category.

        Args:
            category: The relationship category

        Returns:
            List of relationship types in that category
        """
        return [
            rel_type for rel_type, meta in self.metadata.items()
            if meta.category == category
        ]

    def create_relationship_properties(
        self,
        relationship_type: RelationshipType,
        strength: Optional[float] = None,
        confidence: Optional[float] = None,
        context: Optional[str] = None,
        **kwargs
    ) -> RelationshipProperties:
        """
        Create relationship properties with appropriate defaults.

        Args:
            relationship_type: The type of relationship
            strength: Custom strength value (uses default if None)
            confidence: Custom confidence value (uses default if None)
            context: Optional context information
            **kwargs: Additional property values

        Returns:
            RelationshipProperties instance with appropriate defaults
        """
        metadata = self.get_relationship_metadata(relationship_type)

        return RelationshipProperties(
            strength=strength if strength is not None else metadata.default_strength,
            confidence=confidence if confidence is not None else metadata.default_confidence,
            context=context,
            **kwargs
        )

    def validate_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a relationship before creation.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for self-relationships
        if from_memory_id == to_memory_id:
            return False, "Cannot create relationship from memory to itself"

        # Validate relationship type exists
        if relationship_type not in self.metadata:
            return False, f"Unknown relationship type: {relationship_type}"

        # All basic validations passed
        return True, None

    def should_create_inverse(
        self,
        relationship_type: RelationshipType
    ) -> Tuple[bool, Optional[RelationshipType]]:
        """
        Check if an inverse relationship should be created.

        Args:
            relationship_type: The relationship type

        Returns:
            Tuple of (should_create, inverse_type)
        """
        metadata = self.get_relationship_metadata(relationship_type)

        if metadata.bidirectional and metadata.inverse_type:
            return True, metadata.inverse_type

        return False, None

    def calculate_relationship_strength(
        self,
        base_strength: float,
        evidence_count: int,
        success_rate: Optional[float] = None,
        age_days: Optional[float] = None,
        decay_rate: float = 0.01
    ) -> float:
        """
        Calculate effective relationship strength considering multiple factors.

        Args:
            base_strength: Base strength value
            evidence_count: Number of times relationship has been observed
            success_rate: Success rate for solution relationships (0.0-1.0)
            age_days: Age of relationship in days
            decay_rate: Daily decay rate for strength

        Returns:
            Calculated effective strength (0.0-1.0)
        """
        strength = base_strength

        # Boost based on evidence count (logarithmic)
        if evidence_count > 1:
            evidence_boost = min(0.2, 0.05 * (evidence_count - 1) ** 0.5)
            strength = min(1.0, strength + evidence_boost)

        # Adjust based on success rate
        if success_rate is not None:
            strength = strength * (0.5 + 0.5 * success_rate)

        # Apply time-based decay
        if age_days is not None and age_days > 0:
            decay_factor = max(0.5, 1.0 - (decay_rate * age_days))
            strength = strength * decay_factor

        # Ensure within bounds
        return max(0.0, min(1.0, strength))

    def reinforce_relationship_properties(
        self,
        properties: RelationshipProperties,
        success: bool = True,
        strength_increase: float = 0.05,
        confidence_increase: float = 0.03
    ) -> RelationshipProperties:
        """
        Reinforce relationship properties based on successful use.

        Args:
            properties: Current relationship properties
            success: Whether this reinforcement is from a success
            strength_increase: How much to increase strength
            confidence_increase: How much to increase confidence

        Returns:
            Updated relationship properties
        """
        new_evidence = properties.evidence_count + 1
        new_validation = properties.validation_count + (1 if success else 0)
        new_counter = properties.counter_evidence_count + (0 if success else 1)

        # Calculate new success rate
        total_evidence = new_validation + new_counter
        new_success_rate = new_validation / total_evidence if total_evidence > 0 else None

        # Adjust strength and confidence
        if success:
            new_strength = min(1.0, properties.strength + strength_increase)
            new_confidence = min(1.0, properties.confidence + confidence_increase)
        else:
            new_strength = max(0.1, properties.strength - strength_increase * 0.5)
            new_confidence = max(0.1, properties.confidence - confidence_increase * 0.5)

        return RelationshipProperties(
            strength=new_strength,
            confidence=new_confidence,
            context=properties.context,
            evidence_count=new_evidence,
            success_rate=new_success_rate,
            created_at=properties.created_at,
            last_validated=datetime.utcnow(),
            validation_count=new_validation,
            counter_evidence_count=new_counter
        )

    def find_contradictory_relationships(
        self,
        relationships: List[Relationship]
    ) -> List[Tuple[Relationship, Relationship]]:
        """
        Find pairs of relationships that may be contradictory.

        Args:
            relationships: List of relationships to analyze

        Returns:
            List of contradictory relationship pairs
        """
        contradictions = []

        # Look for explicit contradictions
        for i, rel1 in enumerate(relationships):
            for rel2 in relationships[i+1:]:
                # Same nodes, contradictory types
                if (rel1.from_memory_id == rel2.from_memory_id and
                    rel1.to_memory_id == rel2.to_memory_id):

                    # Check for contradictory relationship types
                    contradictory_pairs = [
                        (RelationshipType.SOLVES, RelationshipType.INEFFECTIVE_FOR),
                        (RelationshipType.CONFIRMS, RelationshipType.CONTRADICTS),
                        (RelationshipType.EFFECTIVE_FOR, RelationshipType.INEFFECTIVE_FOR),
                        (RelationshipType.ENABLES, RelationshipType.BLOCKS),
                        (RelationshipType.PREVENTS, RelationshipType.CAUSES),
                    ]

                    for type_a, type_b in contradictory_pairs:
                        if ((rel1.type == type_a and rel2.type == type_b) or
                            (rel1.type == type_b and rel2.type == type_a)):
                            contradictions.append((rel1, rel2))

        return contradictions

    def suggest_relationship_type(
        self,
        from_memory: Memory,
        to_memory: Memory,
        context: Optional[str] = None
    ) -> List[Tuple[RelationshipType, float]]:
        """
        Suggest appropriate relationship types based on memory types.

        Args:
            from_memory: Source memory
            to_memory: Target memory
            context: Optional context information

        Returns:
            List of (relationship_type, confidence) tuples, sorted by confidence
        """
        suggestions: List[Tuple[RelationshipType, float]] = []

        # Problem -> Solution relationships
        if from_memory.type.value == "solution" and to_memory.type.value == "problem":
            suggestions.append((RelationshipType.SOLVES, 0.8))
            suggestions.append((RelationshipType.ADDRESSES, 0.7))

        # Error -> Fix relationships
        if from_memory.type.value == "fix" and to_memory.type.value == "error":
            suggestions.append((RelationshipType.SOLVES, 0.9))

        # Technology relationships
        if (from_memory.type.value == "technology" and
            to_memory.type.value == "technology"):
            suggestions.append((RelationshipType.WORKS_WITH, 0.6))
            suggestions.append((RelationshipType.ALTERNATIVE_TO, 0.5))

        # Workflow relationships
        if from_memory.type.value == "task" and to_memory.type.value == "task":
            suggestions.append((RelationshipType.FOLLOWS, 0.6))
            suggestions.append((RelationshipType.DEPENDS_ON, 0.5))
            suggestions.append((RelationshipType.PARALLEL_TO, 0.4))

        # Code pattern relationships
        if (from_memory.type.value == "code_pattern" and
            to_memory.type.value == "code_pattern"):
            suggestions.append((RelationshipType.SIMILAR_TO, 0.6))
            suggestions.append((RelationshipType.VARIANT_OF, 0.5))
            suggestions.append((RelationshipType.IMPROVES, 0.4))

        # Default fallback
        if not suggestions:
            suggestions.append((RelationshipType.RELATED_TO, 0.5))

        # Sort by confidence descending
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions


# Singleton instance for easy access
relationship_manager = RelationshipManager()
