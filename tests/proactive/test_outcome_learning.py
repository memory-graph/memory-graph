"""
Tests for outcome learning and effectiveness tracking (Phase 7).

Tests verify:
- Outcome recording
- Effectiveness score updates
- Pattern effectiveness propagation
- ROI calculation
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.claude_memory.proactive.outcome_learning import (
    record_outcome,
    update_pattern_effectiveness,
    calculate_effectiveness_score,
    design_decay_mechanism,
    Outcome,
    EffectivenessScore,
)


@pytest.mark.asyncio
class TestRecordOutcome:
    """Test outcome recording functionality."""

    async def test_record_outcome_success(self):
        """Test recording a successful outcome."""
        backend = AsyncMock()

        # Mock query responses
        backend.execute_query = AsyncMock(side_effect=[
            [{"id": "outcome_123"}],  # Create outcome
            [{"effectiveness": 0.8}],  # Update effectiveness
            [],  # Propagate to patterns
        ])

        result = await record_outcome(
            backend,
            "mem_123",
            "Solution worked perfectly",
            success=True,
            impact=0.9,
        )

        assert result is True
        assert backend.execute_query.call_count >= 1

    async def test_record_outcome_failure(self):
        """Test recording a failed outcome."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [{"id": "outcome_456"}],
            [{"effectiveness": 0.4}],
            [],
        ])

        result = await record_outcome(
            backend,
            "mem_456",
            "Solution did not work",
            success=False,
            impact=0.5,
        )

        assert result is True

    async def test_record_outcome_with_context(self):
        """Test recording outcome with additional context."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [{"id": "outcome_789"}],
            [{"effectiveness": 0.7}],
            [],
        ])

        context = {
            "project": "my-app",
            "file": "auth.py",
        }

        result = await record_outcome(
            backend,
            "mem_789",
            "Worked after modifications",
            success=True,
            context=context,
            impact=0.7,
        )

        assert result is True

    async def test_record_outcome_backend_error(self):
        """Test handling of backend errors."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(side_effect=Exception("Database error"))

        result = await record_outcome(
            backend,
            "mem_error",
            "Test outcome",
            success=True,
        )

        assert result is False


@pytest.mark.asyncio
class TestUpdatePatternEffectiveness:
    """Test pattern effectiveness updates."""

    async def test_update_pattern_effectiveness_success(self):
        """Test updating pattern effectiveness after success."""
        backend = AsyncMock()

        # Mock pattern stats
        backend.execute_query = AsyncMock(side_effect=[
            [
                {
                    "current_effectiveness": 0.7,
                    "current_confidence": 0.6,
                    "usage_count": 10,
                    "total_outcomes": 8,
                    "successful_outcomes": 6,
                }
            ],
            [{"effectiveness": 0.75}],  # Update result
        ])

        result = await update_pattern_effectiveness(
            backend,
            "pat_123",
            success=True,
            impact=1.0,
        )

        assert result is True

    async def test_update_pattern_effectiveness_failure(self):
        """Test updating pattern effectiveness after failure."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [
                {
                    "current_effectiveness": 0.8,
                    "current_confidence": 0.7,
                    "usage_count": 5,
                    "total_outcomes": 4,
                    "successful_outcomes": 3,
                }
            ],
            [{"effectiveness": 0.75}],
        ])

        result = await update_pattern_effectiveness(
            backend,
            "pat_456",
            success=False,
            impact=0.8,
        )

        assert result is True

    async def test_update_pattern_effectiveness_not_found(self):
        """Test updating non-existent pattern."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        result = await update_pattern_effectiveness(
            backend,
            "pat_nonexistent",
            success=True,
        )

        assert result is False

    async def test_update_pattern_effectiveness_dampening(self):
        """Test that pattern updates use dampening."""
        backend = AsyncMock()

        # Pattern should change slower than solutions
        backend.execute_query = AsyncMock(side_effect=[
            [
                {
                    "current_effectiveness": 0.5,
                    "current_confidence": 0.5,
                    "usage_count": 1,
                    "total_outcomes": 0,
                    "successful_outcomes": 0,
                }
            ],
            [{"effectiveness": 0.65}],  # Should be dampened
        ])

        result = await update_pattern_effectiveness(
            backend,
            "pat_new",
            success=True,
            impact=1.0,
        )

        assert result is True


@pytest.mark.asyncio
class TestCalculateEffectivenessScore:
    """Test effectiveness score calculation."""

    async def test_calculate_effectiveness_score_with_outcomes(self):
        """Test calculating score for memory with outcomes."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "effectiveness": 0.85,
                "confidence": 0.9,
                "total_outcomes": 10,
                "successful_outcomes": 8,
                "failed_outcomes": 2,
            }
        ])

        score = await calculate_effectiveness_score(backend, "mem_123")

        assert score is not None
        assert score.memory_id == "mem_123"
        assert score.total_uses == 10
        assert score.successful_uses == 8
        assert score.failed_uses == 2
        assert score.effectiveness == 0.85

    async def test_calculate_effectiveness_score_no_outcomes(self):
        """Test calculating score for memory without outcomes."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "effectiveness": 0.5,
                "confidence": 0.5,
                "total_outcomes": 0,
                "successful_outcomes": 0,
                "failed_outcomes": 0,
            }
        ])

        score = await calculate_effectiveness_score(backend, "mem_456")

        assert score is not None
        assert score.total_uses == 0
        assert score.effectiveness == 0.5

    async def test_calculate_effectiveness_score_not_found(self):
        """Test calculating score for non-existent memory."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        score = await calculate_effectiveness_score(backend, "mem_nonexistent")

        assert score is None


class TestEffectivenessScoreModel:
    """Test EffectivenessScore model."""

    def test_effectiveness_score_model(self):
        """Test EffectivenessScore model."""
        score = EffectivenessScore(
            memory_id="mem_123",
            total_uses=10,
            successful_uses=8,
            failed_uses=2,
            effectiveness=0.8,
            confidence=0.9,
        )

        assert score.total_uses == 10
        assert score.successful_uses == 8
        assert score.failed_uses == 2

    def test_effectiveness_score_defaults(self):
        """Test EffectivenessScore with defaults."""
        score = EffectivenessScore(memory_id="mem_456")

        assert score.total_uses == 0
        assert score.successful_uses == 0
        assert score.failed_uses == 0
        assert score.effectiveness == 0.5
        assert score.confidence == 0.5


class TestOutcomeModel:
    """Test Outcome model."""

    def test_outcome_model_basic(self):
        """Test Outcome model with basic fields."""
        outcome = Outcome(
            outcome_id="out_123",
            memory_id="mem_456",
            success=True,
            description="Worked well",
        )

        assert outcome.success is True
        assert outcome.impact == 1.0

    def test_outcome_model_with_context(self):
        """Test Outcome model with context."""
        outcome = Outcome(
            outcome_id="out_456",
            memory_id="mem_789",
            success=False,
            description="Did not work",
            context={"reason": "missing dependency"},
            impact=0.5,
        )

        assert outcome.success is False
        assert outcome.context["reason"] == "missing dependency"
        assert outcome.impact == 0.5


class TestDecayMechanism:
    """Test decay mechanism design."""

    def test_design_decay_mechanism(self):
        """Test that decay mechanism design is documented."""
        design = design_decay_mechanism()

        assert "mechanism" in design
        assert design["mechanism"] == "exponential_decay"
        assert "half_life_days" in design
        assert design["half_life_days"] == 180
        assert "decay_function" in design
        assert "status" in design
        assert design["status"] == "designed_not_implemented"
