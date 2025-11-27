"""
Tests for the advanced relationship management module.

Tests cover all 35 relationship types, relationship categories,
weighted properties, validation, and intelligent suggestions.
"""

import pytest
from datetime import datetime, timedelta

from src.claude_memory.relationships import (
    RelationshipManager,
    RelationshipCategory,
    RelationshipTypeMetadata,
    RELATIONSHIP_TYPE_METADATA,
    relationship_manager,
)
from src.claude_memory.models import (
    RelationshipType,
    RelationshipProperties,
    Relationship,
    Memory,
    MemoryType,
)


class TestRelationshipTypeMetadata:
    """Test relationship type metadata and category system."""

    def test_all_relationship_types_have_metadata(self):
        """Verify all 35 relationship types have metadata defined."""
        # Should have exactly 35 relationship types with metadata
        assert len(RELATIONSHIP_TYPE_METADATA) == 35

        # Every RelationshipType should have metadata
        for rel_type in RelationshipType:
            assert rel_type in RELATIONSHIP_TYPE_METADATA, \
                f"Missing metadata for {rel_type}"

    def test_relationship_categories_complete(self):
        """Verify all categories are represented."""
        categories_found = set()

        for metadata in RELATIONSHIP_TYPE_METADATA.values():
            categories_found.add(metadata.category)

        # Should have all 7 categories
        expected_categories = {
            RelationshipCategory.CAUSAL,
            RelationshipCategory.SOLUTION,
            RelationshipCategory.CONTEXT,
            RelationshipCategory.LEARNING,
            RelationshipCategory.SIMILARITY,
            RelationshipCategory.WORKFLOW,
            RelationshipCategory.QUALITY,
        }

        assert categories_found == expected_categories

    def test_category_distribution(self):
        """Verify each category has 5 relationship types."""
        category_counts = {}

        for metadata in RELATIONSHIP_TYPE_METADATA.values():
            category = metadata.category
            category_counts[category] = category_counts.get(category, 0) + 1

        # Each category should have exactly 5 types
        for category, count in category_counts.items():
            assert count == 5, \
                f"Category {category} has {count} types, expected 5"

    def test_default_strength_values_valid(self):
        """Verify all default strength values are in valid range."""
        for rel_type, metadata in RELATIONSHIP_TYPE_METADATA.items():
            assert 0.0 <= metadata.default_strength <= 1.0, \
                f"{rel_type} has invalid default_strength: {metadata.default_strength}"

    def test_default_confidence_values_valid(self):
        """Verify all default confidence values are in valid range."""
        for rel_type, metadata in RELATIONSHIP_TYPE_METADATA.items():
            assert 0.0 <= metadata.default_confidence <= 1.0, \
                f"{rel_type} has invalid default_confidence: {metadata.default_confidence}"

    def test_bidirectional_relationships_have_inverse(self):
        """Verify bidirectional relationships have inverse types defined."""
        for rel_type, metadata in RELATIONSHIP_TYPE_METADATA.items():
            if metadata.bidirectional:
                assert metadata.inverse_type is not None, \
                    f"Bidirectional {rel_type} missing inverse_type"

    def test_metadata_descriptions_not_empty(self):
        """Verify all relationship types have descriptions."""
        for rel_type, metadata in RELATIONSHIP_TYPE_METADATA.items():
            assert metadata.description, \
                f"{rel_type} has empty description"
            assert len(metadata.description) > 10, \
                f"{rel_type} description too short"


class TestRelationshipManagerBasics:
    """Test basic RelationshipManager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a RelationshipManager instance."""
        return RelationshipManager()

    def test_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager is not None
        assert manager.metadata == RELATIONSHIP_TYPE_METADATA

    def test_singleton_instance_available(self):
        """Test singleton instance is available."""
        assert relationship_manager is not None
        assert isinstance(relationship_manager, RelationshipManager)

    def test_get_relationship_metadata(self, manager):
        """Test getting metadata for relationship types."""
        metadata = manager.get_relationship_metadata(RelationshipType.SOLVES)

        assert metadata.category == RelationshipCategory.SOLUTION
        assert metadata.description
        assert 0.0 <= metadata.default_strength <= 1.0

    def test_get_relationship_metadata_invalid_type(self, manager):
        """Test getting metadata for invalid type raises error."""
        # Create a mock invalid type (this would never happen in practice)
        # but tests error handling
        with pytest.raises(ValueError, match="Unknown relationship type"):
            # Use a string that's not a valid RelationshipType
            manager.get_relationship_metadata("INVALID_TYPE")

    def test_get_relationship_category(self, manager):
        """Test getting category for relationship types."""
        # Test a few examples from each category
        assert manager.get_relationship_category(RelationshipType.CAUSES) == \
            RelationshipCategory.CAUSAL

        assert manager.get_relationship_category(RelationshipType.SOLVES) == \
            RelationshipCategory.SOLUTION

        assert manager.get_relationship_category(RelationshipType.SIMILAR_TO) == \
            RelationshipCategory.SIMILARITY

    def test_get_types_by_category(self, manager):
        """Test getting all types in a category."""
        causal_types = manager.get_types_by_category(RelationshipCategory.CAUSAL)

        assert len(causal_types) == 5
        assert RelationshipType.CAUSES in causal_types
        assert RelationshipType.TRIGGERS in causal_types
        assert RelationshipType.LEADS_TO in causal_types
        assert RelationshipType.PREVENTS in causal_types
        assert RelationshipType.BREAKS in causal_types


class TestRelationshipPropertiesCreation:
    """Test creating relationship properties with defaults."""

    @pytest.fixture
    def manager(self):
        return RelationshipManager()

    def test_create_properties_with_defaults(self, manager):
        """Test creating properties uses appropriate defaults."""
        props = manager.create_relationship_properties(RelationshipType.SOLVES)

        # Should use defaults from metadata
        metadata = RELATIONSHIP_TYPE_METADATA[RelationshipType.SOLVES]
        assert props.strength == metadata.default_strength
        assert props.confidence == metadata.default_confidence

    def test_create_properties_with_custom_strength(self, manager):
        """Test custom strength overrides default."""
        props = manager.create_relationship_properties(
            RelationshipType.SOLVES,
            strength=0.95
        )

        assert props.strength == 0.95

    def test_create_properties_with_custom_confidence(self, manager):
        """Test custom confidence overrides default."""
        props = manager.create_relationship_properties(
            RelationshipType.CAUSES,
            confidence=0.99
        )

        assert props.confidence == 0.99

    def test_create_properties_with_context(self, manager):
        """Test creating properties with context."""
        props = manager.create_relationship_properties(
            RelationshipType.APPLIES_TO,
            context="Only in production environments"
        )

        assert props.context == "Only in production environments"

    def test_create_properties_different_types_different_defaults(self, manager):
        """Test different relationship types have different defaults."""
        solves_props = manager.create_relationship_properties(RelationshipType.SOLVES)
        related_props = manager.create_relationship_properties(RelationshipType.RELATED_TO)

        # SOLVES should have higher default strength than RELATED_TO
        assert solves_props.strength > related_props.strength


class TestRelationshipValidation:
    """Test relationship validation logic."""

    @pytest.fixture
    def manager(self):
        return RelationshipManager()

    def test_validate_relationship_valid(self, manager):
        """Test validating a valid relationship."""
        is_valid, error = manager.validate_relationship(
            "mem1",
            "mem2",
            RelationshipType.SOLVES
        )

        assert is_valid is True
        assert error is None

    def test_validate_relationship_self_reference(self, manager):
        """Test validation fails for self-relationships."""
        is_valid, error = manager.validate_relationship(
            "mem1",
            "mem1",
            RelationshipType.RELATED_TO
        )

        assert is_valid is False
        assert "itself" in error.lower()

    def test_validate_all_relationship_types(self, manager):
        """Test validation works for all relationship types."""
        for rel_type in RelationshipType:
            is_valid, error = manager.validate_relationship(
                "mem1",
                "mem2",
                rel_type
            )

            assert is_valid is True
            assert error is None


class TestBidirectionalRelationships:
    """Test bidirectional relationship handling."""

    @pytest.fixture
    def manager(self):
        return RelationshipManager()

    def test_should_create_inverse_for_bidirectional(self, manager):
        """Test inverse creation for bidirectional types."""
        should_create, inverse_type = manager.should_create_inverse(
            RelationshipType.SIMILAR_TO
        )

        assert should_create is True
        assert inverse_type == RelationshipType.SIMILAR_TO

    def test_should_not_create_inverse_for_unidirectional(self, manager):
        """Test no inverse for unidirectional types."""
        should_create, inverse_type = manager.should_create_inverse(
            RelationshipType.SOLVES
        )

        assert should_create is False
        assert inverse_type is None

    def test_inverse_relationships(self, manager):
        """Test inverse relationship types are correct."""
        # GENERALIZES <-> SPECIALIZES
        metadata_gen = manager.get_relationship_metadata(RelationshipType.GENERALIZES)
        metadata_spec = manager.get_relationship_metadata(RelationshipType.SPECIALIZES)

        assert metadata_gen.inverse_type == RelationshipType.SPECIALIZES
        assert metadata_spec.inverse_type == RelationshipType.GENERALIZES


class TestRelationshipStrengthCalculation:
    """Test relationship strength calculation."""

    @pytest.fixture
    def manager(self):
        return RelationshipManager()

    def test_calculate_strength_base_only(self, manager):
        """Test strength calculation with just base strength."""
        strength = manager.calculate_relationship_strength(
            base_strength=0.5,
            evidence_count=1
        )

        assert strength == 0.5

    def test_calculate_strength_with_evidence_boost(self, manager):
        """Test evidence count increases strength."""
        strength_1 = manager.calculate_relationship_strength(
            base_strength=0.5,
            evidence_count=1
        )

        strength_5 = manager.calculate_relationship_strength(
            base_strength=0.5,
            evidence_count=5
        )

        assert strength_5 > strength_1

    def test_calculate_strength_with_success_rate(self, manager):
        """Test success rate affects strength."""
        strength_high = manager.calculate_relationship_strength(
            base_strength=0.7,
            evidence_count=1,
            success_rate=0.9
        )

        strength_low = manager.calculate_relationship_strength(
            base_strength=0.7,
            evidence_count=1,
            success_rate=0.3
        )

        assert strength_high > strength_low

    def test_calculate_strength_with_decay(self, manager):
        """Test time-based decay reduces strength."""
        strength_new = manager.calculate_relationship_strength(
            base_strength=0.8,
            evidence_count=1,
            age_days=0
        )

        strength_old = manager.calculate_relationship_strength(
            base_strength=0.8,
            evidence_count=1,
            age_days=30
        )

        assert strength_old < strength_new

    def test_calculate_strength_stays_in_bounds(self, manager):
        """Test strength always stays between 0 and 1."""
        # Try to create very high strength
        strength = manager.calculate_relationship_strength(
            base_strength=0.9,
            evidence_count=100,
            success_rate=1.0
        )

        assert 0.0 <= strength <= 1.0

        # Try to create very low strength
        strength_low = manager.calculate_relationship_strength(
            base_strength=0.1,
            evidence_count=1,
            success_rate=0.0,
            age_days=365
        )

        assert 0.0 <= strength_low <= 1.0


class TestRelationshipReinforcement:
    """Test relationship reinforcement logic."""

    @pytest.fixture
    def manager(self):
        return RelationshipManager()

    @pytest.fixture
    def base_properties(self):
        return RelationshipProperties(
            strength=0.5,
            confidence=0.7,
            evidence_count=1,
            validation_count=1,
            counter_evidence_count=0
        )

    def test_reinforce_with_success(self, manager, base_properties):
        """Test successful reinforcement increases values."""
        reinforced = manager.reinforce_relationship_properties(
            base_properties,
            success=True
        )

        assert reinforced.strength > base_properties.strength
        assert reinforced.confidence > base_properties.confidence
        assert reinforced.evidence_count == base_properties.evidence_count + 1
        assert reinforced.validation_count == base_properties.validation_count + 1

    def test_reinforce_with_failure(self, manager, base_properties):
        """Test failure reinforcement decreases values."""
        reinforced = manager.reinforce_relationship_properties(
            base_properties,
            success=False
        )

        assert reinforced.strength < base_properties.strength
        assert reinforced.confidence < base_properties.confidence
        assert reinforced.counter_evidence_count == base_properties.counter_evidence_count + 1

    def test_reinforce_updates_success_rate(self, manager, base_properties):
        """Test reinforcement updates success rate."""
        reinforced = manager.reinforce_relationship_properties(
            base_properties,
            success=True
        )

        assert reinforced.success_rate is not None
        assert reinforced.success_rate == 1.0  # 2 successes, 0 failures

    def test_reinforce_caps_at_maximum(self, manager):
        """Test reinforcement doesn't exceed 1.0."""
        strong_props = RelationshipProperties(
            strength=0.98,
            confidence=0.99
        )

        reinforced = manager.reinforce_relationship_properties(
            strong_props,
            success=True
        )

        assert reinforced.strength <= 1.0
        assert reinforced.confidence <= 1.0

    def test_reinforce_floors_at_minimum(self, manager):
        """Test reinforcement doesn't go below 0.1."""
        weak_props = RelationshipProperties(
            strength=0.15,
            confidence=0.15
        )

        reinforced = manager.reinforce_relationship_properties(
            weak_props,
            success=False
        )

        assert reinforced.strength >= 0.1
        assert reinforced.confidence >= 0.1


class TestContradictionDetection:
    """Test finding contradictory relationships."""

    @pytest.fixture
    def manager(self):
        return RelationshipManager()

    def test_find_contradictions_solves_vs_ineffective(self, manager):
        """Test detecting SOLVES vs INEFFECTIVE_FOR contradiction."""
        rel1 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem2",
            type=RelationshipType.SOLVES
        )

        rel2 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem2",
            type=RelationshipType.INEFFECTIVE_FOR
        )

        contradictions = manager.find_contradictory_relationships([rel1, rel2])

        assert len(contradictions) == 1
        assert (rel1, rel2) in contradictions or (rel2, rel1) in contradictions

    def test_find_contradictions_confirms_vs_contradicts(self, manager):
        """Test detecting CONFIRMS vs CONTRADICTS contradiction."""
        rel1 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem2",
            type=RelationshipType.CONFIRMS
        )

        rel2 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem2",
            type=RelationshipType.CONTRADICTS
        )

        contradictions = manager.find_contradictory_relationships([rel1, rel2])

        assert len(contradictions) == 1

    def test_find_no_contradictions_different_nodes(self, manager):
        """Test no contradictions for different node pairs."""
        rel1 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem2",
            type=RelationshipType.SOLVES
        )

        rel2 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem3",  # Different target
            type=RelationshipType.INEFFECTIVE_FOR
        )

        contradictions = manager.find_contradictory_relationships([rel1, rel2])

        assert len(contradictions) == 0

    def test_find_no_contradictions_compatible_types(self, manager):
        """Test no contradictions for compatible relationship types."""
        rel1 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem2",
            type=RelationshipType.SOLVES
        )

        rel2 = Relationship(
            from_memory_id="mem1",
            to_memory_id="mem2",
            type=RelationshipType.ADDRESSES
        )

        contradictions = manager.find_contradictory_relationships([rel1, rel2])

        assert len(contradictions) == 0


class TestRelationshipSuggestions:
    """Test intelligent relationship type suggestions."""

    @pytest.fixture
    def manager(self):
        return RelationshipManager()

    def test_suggest_solution_to_problem(self, manager):
        """Test suggesting SOLVES for solution->problem."""
        solution = Memory(
            type=MemoryType.SOLUTION,
            title="Fix for bug",
            content="Apply patch"
        )

        problem = Memory(
            type=MemoryType.PROBLEM,
            title="Bug in code",
            content="Error occurs"
        )

        suggestions = manager.suggest_relationship_type(solution, problem)

        # Should suggest SOLVES with high confidence
        assert len(suggestions) > 0
        types = [s[0] for s in suggestions]
        assert RelationshipType.SOLVES in types

        # SOLVES should be first suggestion
        assert suggestions[0][0] == RelationshipType.SOLVES

    def test_suggest_fix_to_error(self, manager):
        """Test suggesting SOLVES for fix->error."""
        fix = Memory(
            type=MemoryType.FIX,
            title="Fix for error",
            content="Apply fix"
        )

        error = Memory(
            type=MemoryType.ERROR,
            title="Error occurred",
            content="Error details"
        )

        suggestions = manager.suggest_relationship_type(fix, error)

        # Should suggest SOLVES with very high confidence
        assert suggestions[0][0] == RelationshipType.SOLVES
        assert suggestions[0][1] >= 0.8

    def test_suggest_task_to_task(self, manager):
        """Test suggesting workflow relationships for task->task."""
        task1 = Memory(
            type=MemoryType.TASK,
            title="Task 1",
            content="First task"
        )

        task2 = Memory(
            type=MemoryType.TASK,
            title="Task 2",
            content="Second task"
        )

        suggestions = manager.suggest_relationship_type(task1, task2)

        types = [s[0] for s in suggestions]
        # Should suggest workflow relationships
        assert any(t in [RelationshipType.FOLLOWS, RelationshipType.DEPENDS_ON,
                        RelationshipType.PARALLEL_TO] for t in types)

    def test_suggest_code_pattern_to_code_pattern(self, manager):
        """Test suggesting similarity relationships for patterns."""
        pattern1 = Memory(
            type=MemoryType.CODE_PATTERN,
            title="Pattern 1",
            content="First pattern"
        )

        pattern2 = Memory(
            type=MemoryType.CODE_PATTERN,
            title="Pattern 2",
            content="Second pattern"
        )

        suggestions = manager.suggest_relationship_type(pattern1, pattern2)

        types = [s[0] for s in suggestions]
        # Should suggest similarity relationships
        assert any(t in [RelationshipType.SIMILAR_TO, RelationshipType.VARIANT_OF,
                        RelationshipType.IMPROVES] for t in types)

    def test_suggest_fallback_for_unknown(self, manager):
        """Test fallback to RELATED_TO for unknown combinations."""
        mem1 = Memory(
            type=MemoryType.GENERAL,
            title="Memory 1",
            content="Content 1"
        )

        mem2 = Memory(
            type=MemoryType.GENERAL,
            title="Memory 2",
            content="Content 2"
        )

        suggestions = manager.suggest_relationship_type(mem1, mem2)

        # Should at least suggest RELATED_TO as fallback
        assert len(suggestions) > 0
        types = [s[0] for s in suggestions]
        assert RelationshipType.RELATED_TO in types

    def test_suggestions_sorted_by_confidence(self, manager):
        """Test suggestions are sorted by confidence descending."""
        solution = Memory(
            type=MemoryType.SOLUTION,
            title="Fix",
            content="Solution"
        )

        problem = Memory(
            type=MemoryType.PROBLEM,
            title="Bug",
            content="Problem"
        )

        suggestions = manager.suggest_relationship_type(solution, problem)

        # Verify descending confidence order
        for i in range(len(suggestions) - 1):
            assert suggestions[i][1] >= suggestions[i+1][1]


class TestRelationshipCategoryCoverage:
    """Test coverage of all relationship categories."""

    def test_causal_relationships(self):
        """Test all causal relationships are defined."""
        causal_types = [
            RelationshipType.CAUSES,
            RelationshipType.TRIGGERS,
            RelationshipType.LEADS_TO,
            RelationshipType.PREVENTS,
            RelationshipType.BREAKS,
        ]

        for rel_type in causal_types:
            metadata = RELATIONSHIP_TYPE_METADATA[rel_type]
            assert metadata.category == RelationshipCategory.CAUSAL

    def test_solution_relationships(self):
        """Test all solution relationships are defined."""
        solution_types = [
            RelationshipType.SOLVES,
            RelationshipType.ADDRESSES,
            RelationshipType.ALTERNATIVE_TO,
            RelationshipType.IMPROVES,
            RelationshipType.REPLACES,
        ]

        for rel_type in solution_types:
            metadata = RELATIONSHIP_TYPE_METADATA[rel_type]
            assert metadata.category == RelationshipCategory.SOLUTION

    def test_context_relationships(self):
        """Test all context relationships are defined."""
        context_types = [
            RelationshipType.OCCURS_IN,
            RelationshipType.APPLIES_TO,
            RelationshipType.WORKS_WITH,
            RelationshipType.REQUIRES,
            RelationshipType.USED_IN,
        ]

        for rel_type in context_types:
            metadata = RELATIONSHIP_TYPE_METADATA[rel_type]
            assert metadata.category == RelationshipCategory.CONTEXT

    def test_learning_relationships(self):
        """Test all learning relationships are defined."""
        learning_types = [
            RelationshipType.BUILDS_ON,
            RelationshipType.CONTRADICTS,
            RelationshipType.CONFIRMS,
            RelationshipType.GENERALIZES,
            RelationshipType.SPECIALIZES,
        ]

        for rel_type in learning_types:
            metadata = RELATIONSHIP_TYPE_METADATA[rel_type]
            assert metadata.category == RelationshipCategory.LEARNING

    def test_similarity_relationships(self):
        """Test all similarity relationships are defined."""
        similarity_types = [
            RelationshipType.SIMILAR_TO,
            RelationshipType.VARIANT_OF,
            RelationshipType.RELATED_TO,
            RelationshipType.ANALOGY_TO,
            RelationshipType.OPPOSITE_OF,
        ]

        for rel_type in similarity_types:
            metadata = RELATIONSHIP_TYPE_METADATA[rel_type]
            assert metadata.category == RelationshipCategory.SIMILARITY

    def test_workflow_relationships(self):
        """Test all workflow relationships are defined."""
        workflow_types = [
            RelationshipType.FOLLOWS,
            RelationshipType.DEPENDS_ON,
            RelationshipType.ENABLES,
            RelationshipType.BLOCKS,
            RelationshipType.PARALLEL_TO,
        ]

        for rel_type in workflow_types:
            metadata = RELATIONSHIP_TYPE_METADATA[rel_type]
            assert metadata.category == RelationshipCategory.WORKFLOW

    def test_quality_relationships(self):
        """Test all quality relationships are defined."""
        quality_types = [
            RelationshipType.EFFECTIVE_FOR,
            RelationshipType.INEFFECTIVE_FOR,
            RelationshipType.PREFERRED_OVER,
            RelationshipType.DEPRECATED_BY,
            RelationshipType.VALIDATED_BY,
        ]

        for rel_type in quality_types:
            metadata = RELATIONSHIP_TYPE_METADATA[rel_type]
            assert metadata.category == RelationshipCategory.QUALITY
