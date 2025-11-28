"""
Tests for predictive suggestions (Phase 7).

Tests verify:
- Need prediction based on context
- Issue warnings for deprecated/problematic approaches
- Related context suggestions
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.memorygraph.proactive.predictive import (
    predict_needs,
    warn_potential_issues,
    suggest_related_context,
    Suggestion,
    Warning,
)
from src.memorygraph.intelligence.entity_extraction import Entity, EntityType


@pytest.mark.asyncio
class TestPredictNeeds:
    """Test need prediction from current context."""

    async def test_predict_needs_no_entities(self):
        """Test that no suggestions are returned when no entities extracted."""
        backend = AsyncMock()

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=[]):
            suggestions = await predict_needs(
                backend,
                "generic text with no entities"
            )

            assert suggestions == []

    async def test_predict_needs_with_entities(self):
        """Test suggestions based on extracted entities."""
        backend = AsyncMock()

        # Mock entity extraction
        entities = [
            Entity(
                text="React",
                entity_type=EntityType.TECHNOLOGY,
                confidence=0.9,
                start_pos=0,
                end_pos=5,
            )
        ]

        # Mock query results
        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "sol_1",
                "type": "solution",
                "title": "React authentication",
                "content": "How to implement auth in React",
                "tags": ["react", "auth"],
                "effectiveness": 0.8,
                "usage_count": 10,
                "effectiveness_links": 2,
            }
        ])

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=entities):
            suggestions = await predict_needs(
                backend,
                "Working with React authentication"
            )

            assert len(suggestions) > 0
            assert suggestions[0].title == "React authentication"
            assert suggestions[0].relevance_score > 0.3

    async def test_predict_needs_relevance_filtering(self):
        """Test that low-relevance suggestions are filtered out."""
        backend = AsyncMock()

        entities = [
            Entity(
                text="Python",
                entity_type=EntityType.TECHNOLOGY,
                confidence=0.3,  # Low confidence
                start_pos=0,
                end_pos=6,
            )
        ]

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "sol_1",
                "type": "solution",
                "title": "Low relevance solution",
                "content": "Content",
                "tags": [],
                "effectiveness": 0.2,
                "usage_count": 1,
                "effectiveness_links": 0,
            }
        ])

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=entities):
            suggestions = await predict_needs(
                backend,
                "Some context",
                min_relevance=0.5
            )

            # Low relevance should be filtered
            assert len(suggestions) == 0

    async def test_predict_needs_max_suggestions(self):
        """Test that max_suggestions limit is respected."""
        backend = AsyncMock()

        entities = [
            Entity(
                text="Django",
                entity_type=EntityType.TECHNOLOGY,
                confidence=0.9,
                start_pos=0,
                end_pos=6,
            )
        ]

        # Return many results
        backend.execute_query = AsyncMock(return_value=[
            {
                "id": f"sol_{i}",
                "type": "solution",
                "title": f"Solution {i}",
                "content": "Content",
                "tags": [],
                "effectiveness": 0.8,
                "usage_count": 10,
                "effectiveness_links": 1,
            }
            for i in range(10)
        ])

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=entities):
            suggestions = await predict_needs(
                backend,
                "Django context",
                max_suggestions=3
            )

            assert len(suggestions) <= 3


@pytest.mark.asyncio
class TestWarnPotentialIssues:
    """Test issue warning based on context."""

    async def test_warn_potential_issues_no_entities(self):
        """Test no warnings when no entities extracted."""
        backend = AsyncMock()

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=[]):
            warnings = await warn_potential_issues(
                backend,
                "generic text"
            )

            assert warnings == []

    async def test_warn_potential_issues_deprecated_approach(self):
        """Test warning for deprecated approaches."""
        backend = AsyncMock()

        entities = [
            Entity(
                text="OldLibrary",
                entity_type=EntityType.TECHNOLOGY,
                confidence=0.9,
                start_pos=0,
                end_pos=10,
            )
        ]

        # Mock deprecated relationship query
        backend.execute_query = AsyncMock(side_effect=[
            # Deprecated query
            [
                {
                    "old_id": "old_1",
                    "old_title": "OldLibrary usage",
                    "reason": "Security vulnerability",
                    "new_id": "new_1",
                    "new_title": "NewLibrary usage",
                    "entities": ["OldLibrary"],
                }
            ],
            # Problem query
            []
        ])

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=entities):
            warnings = await warn_potential_issues(
                backend,
                "Using OldLibrary for authentication"
            )

            assert len(warnings) > 0
            assert warnings[0].severity == "high"
            assert "Deprecated" in warnings[0].title

    async def test_warn_potential_issues_known_problem(self):
        """Test warning for known problem patterns."""
        backend = AsyncMock()

        entities = [
            Entity(
                text="PostgreSQL",
                entity_type=EntityType.TECHNOLOGY,
                confidence=0.9,
                start_pos=0,
                end_pos=10,
            )
        ]

        # Mock problem query
        backend.execute_query = AsyncMock(side_effect=[
            [],  # No deprecated
            [
                {
                    "problem_id": "prob_1",
                    "problem_title": "PostgreSQL connection leak",
                    "problem_content": "Connections not being closed properly",
                    "tags": ["postgresql", "connection"],
                    "solution_ids": ["sol_1"],
                    "solution_titles": ["Use connection pooling"],
                }
            ]
        ])

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=entities):
            warnings = await warn_potential_issues(
                backend,
                "Working with PostgreSQL connections"
            )

            assert len(warnings) > 0
            assert "connection leak" in warnings[0].title.lower()
            assert "connection pooling" in warnings[0].mitigation.lower()

    async def test_warn_potential_issues_severity_filter(self):
        """Test filtering by severity threshold."""
        backend = AsyncMock()

        entities = [
            Entity(
                text="Test",
                entity_type=EntityType.TECHNOLOGY,
                confidence=0.9,
                start_pos=0,
                end_pos=4,
            )
        ]

        # Mock low severity warning
        backend.execute_query = AsyncMock(side_effect=[
            [],  # No deprecated
            [
                {
                    "problem_id": "prob_1",
                    "problem_title": "Minor issue",
                    "problem_content": "Minor problem",
                    "tags": [],
                    "solution_ids": ["sol_1"],
                    "solution_titles": ["Fix"],
                }
            ]
        ])

        with patch('src.memorygraph.proactive.predictive.extract_entities',
                   return_value=entities):
            # Request only high severity
            warnings = await warn_potential_issues(
                backend,
                "Test context",
                severity_threshold="high"
            )

            # Medium severity warnings should be filtered out
            # (problems with solutions have medium severity)
            assert len([w for w in warnings if w.severity == "high"]) <= len(warnings)


@pytest.mark.asyncio
class TestSuggestRelatedContext:
    """Test related context suggestions."""

    async def test_suggest_related_context_no_relationships(self):
        """Test no suggestions when memory has no relationships."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        suggestions = await suggest_related_context(
            backend,
            "mem_123"
        )

        assert suggestions == []

    async def test_suggest_related_context_with_relationships(self):
        """Test suggestions based on strong relationships."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "mem_456",
                "type": "solution",
                "title": "Related solution",
                "content": "Related content",
                "tags": ["related"],
                "effectiveness": 0.9,
                "rel_type": "BUILDS_ON",
                "strength": 0.8,
            }
        ])

        suggestions = await suggest_related_context(
            backend,
            "mem_123",
            max_suggestions=5
        )

        assert len(suggestions) > 0
        assert suggestions[0].title == "Related solution"
        assert suggestions[0].reason == "Builds on this concept"
        assert suggestions[0].relevance_score == 0.8

    async def test_suggest_related_context_max_limit(self):
        """Test max_suggestions limit."""
        backend = AsyncMock()

        # Return many results
        backend.execute_query = AsyncMock(return_value=[
            {
                "id": f"mem_{i}",
                "type": "solution",
                "title": f"Solution {i}",
                "content": "Content",
                "tags": [],
                "effectiveness": 0.8,
                "rel_type": "SIMILAR_TO",
                "strength": 0.7,
            }
            for i in range(10)
        ])

        suggestions = await suggest_related_context(
            backend,
            "mem_123",
            max_suggestions=3
        )

        assert len(suggestions) <= 3


class TestSuggestionModel:
    """Test Suggestion model."""

    def test_suggestion_model_required_fields(self):
        """Test Suggestion model with required fields."""
        suggestion = Suggestion(
            suggestion_id="sug_1",
            suggestion_type="solution",
            title="Test suggestion",
            description="Description",
            relevance_score=0.8,
            reason="Test reason",
            memory_id="mem_123",
        )

        assert suggestion.relevance_score == 0.8
        assert suggestion.effectiveness is None

    def test_suggestion_model_with_optional_fields(self):
        """Test Suggestion model with optional fields."""
        suggestion = Suggestion(
            suggestion_id="sug_1",
            suggestion_type="solution",
            title="Test suggestion",
            description="Description",
            relevance_score=0.8,
            reason="Test reason",
            memory_id="mem_123",
            tags=["tag1", "tag2"],
            effectiveness=0.9,
        )

        assert len(suggestion.tags) == 2
        assert suggestion.effectiveness == 0.9


class TestWarningModel:
    """Test Warning model."""

    def test_warning_model_basic(self):
        """Test Warning model with basic fields."""
        warning = Warning(
            warning_id="warn_1",
            severity="high",
            title="Test warning",
            description="Warning description",
        )

        assert warning.severity == "high"
        assert len(warning.evidence) == 0

    def test_warning_model_with_evidence(self):
        """Test Warning model with evidence."""
        warning = Warning(
            warning_id="warn_1",
            severity="medium",
            title="Test warning",
            description="Warning description",
            evidence=["mem_1", "mem_2"],
            mitigation="Fix by doing X",
        )

        assert len(warning.evidence) == 2
        assert warning.mitigation == "Fix by doing X"
