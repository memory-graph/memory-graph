"""
Outcome Learning and Effectiveness Tracking for Claude Code Memory Server.

Tracks solution effectiveness and learns from outcomes:
- Record solution outcomes (success/failure)
- Update effectiveness scores
- Propagate learning to patterns
- Decay old outcomes

Phase 7 Implementation - Learning From Outcomes
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import math

from pydantic import BaseModel, Field

from ..backends.base import GraphBackend
from ..models import Memory, MemoryType

logger = logging.getLogger(__name__)


class Outcome(BaseModel):
    """
    Outcome of applying a memory (solution, pattern, etc.).

    Tracks whether a solution worked and in what context.
    """

    outcome_id: str
    memory_id: str
    success: bool
    description: str
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    impact: float = Field(default=1.0, ge=0.0, le=1.0)  # How significant this outcome was


class EffectivenessScore(BaseModel):
    """
    Effectiveness score for a memory.

    Combines multiple outcomes to calculate overall effectiveness.
    """

    memory_id: str
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    effectiveness: float = 0.5  # 0.0 to 1.0
    confidence: float = 0.5  # How confident we are in this score
    last_updated: datetime = Field(default_factory=datetime.now)


async def record_outcome(
    backend: GraphBackend,
    memory_id: str,
    outcome_description: str,
    success: bool,
    context: Optional[Dict[str, Any]] = None,
    impact: float = 1.0,
) -> bool:
    """
    Record the outcome of using a memory.

    Creates an Outcome node linked to the memory and updates effectiveness scores.

    Args:
        backend: Database backend
        memory_id: ID of memory that was used
        outcome_description: Description of what happened
        success: Whether the outcome was successful
        context: Additional context about the outcome
        impact: How significant this outcome was (0.0 to 1.0)

    Returns:
        True if outcome was recorded successfully

    Example:
        >>> success = await record_outcome(
        ...     backend,
        ...     "solution_123",
        ...     "Fixed the authentication bug",
        ...     success=True,
        ...     impact=0.9
        ... )
    """
    logger.info(f"Recording outcome for memory {memory_id}: success={success}")

    # Create outcome node and link to memory
    outcome_id = f"outcome_{datetime.now().timestamp()}"

    create_outcome_query = """
    MATCH (m:Memory {id: $memory_id})
    CREATE (o:Outcome {
        id: $outcome_id,
        memory_id: $memory_id,
        success: $success,
        description: $description,
        context: $context,
        timestamp: datetime($timestamp),
        impact: $impact
    })
    CREATE (m)-[:RESULTED_IN]->(o)
    RETURN o.id as id
    """

    try:
        result = await backend.execute_query(
            create_outcome_query,
            {
                "memory_id": memory_id,
                "outcome_id": outcome_id,
                "success": success,
                "description": outcome_description,
                "context": str(context) if context else None,
                "timestamp": datetime.now().isoformat(),
                "impact": impact,
            }
        )

        if not result:
            logger.error(f"Failed to create outcome for memory {memory_id}")
            return False

        logger.debug(f"Created outcome {outcome_id}")

        # Update memory effectiveness score
        await _update_memory_effectiveness(backend, memory_id, success, impact)

        # If this is a pattern or solution, propagate to related patterns
        await _propagate_to_patterns(backend, memory_id, success, impact)

        return True

    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        return False


async def _update_memory_effectiveness(
    backend: GraphBackend,
    memory_id: str,
    success: bool,
    impact: float,
) -> None:
    """
    Update effectiveness score for a memory based on outcome.

    Uses Bayesian updating to incorporate new evidence.
    """
    logger.debug(f"Updating effectiveness for memory {memory_id}")

    # Get current statistics
    stats_query = """
    MATCH (m:Memory {id: $memory_id})
    OPTIONAL MATCH (m)-[:RESULTED_IN]->(o:Outcome)
    RETURN m.effectiveness as current_effectiveness,
           m.usage_count as usage_count,
           count(o) as total_outcomes,
           sum(CASE WHEN o.success THEN 1 ELSE 0 END) as successful_outcomes
    """

    try:
        result = await backend.execute_query(stats_query, {"memory_id": memory_id})

        if not result:
            return

        record = result[0]
        current_effectiveness = record.get("current_effectiveness", 0.5)
        usage_count = record.get("usage_count", 0)
        total_outcomes = record.get("total_outcomes", 0)
        successful_outcomes = record.get("successful_outcomes", 0)

        # Calculate new effectiveness using weighted average
        # Recent outcomes weighted more heavily
        if total_outcomes > 0:
            success_rate = successful_outcomes / total_outcomes

            # Weighted blend: recent outcome has impact, historical has (1-impact)
            new_effectiveness = (success_rate * (1 - impact)) + (1.0 if success else 0.0) * impact
        else:
            new_effectiveness = 1.0 if success else 0.0

        # Clamp to [0, 1]
        new_effectiveness = max(0.0, min(1.0, new_effectiveness))

        # Calculate confidence based on number of outcomes
        # More outcomes = higher confidence
        confidence = min(0.9, 0.3 + (total_outcomes / 20.0) * 0.6)

        # Update memory
        update_query = """
        MATCH (m:Memory {id: $memory_id})
        SET m.effectiveness = $effectiveness,
            m.confidence = $confidence,
            m.usage_count = $usage_count + 1,
            m.last_accessed = datetime($timestamp)
        RETURN m.effectiveness as effectiveness
        """

        await backend.execute_query(
            update_query,
            {
                "memory_id": memory_id,
                "effectiveness": new_effectiveness,
                "confidence": confidence,
                "usage_count": usage_count,
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"Updated effectiveness for {memory_id}: {new_effectiveness:.2f} (confidence: {confidence:.2f})")

    except Exception as e:
        logger.error(f"Error updating memory effectiveness: {e}")


async def _propagate_to_patterns(
    backend: GraphBackend,
    memory_id: str,
    success: bool,
    impact: float,
) -> None:
    """
    Propagate outcome learning to related patterns.

    If a solution worked, increase confidence in related patterns.
    """
    logger.debug(f"Propagating outcome to related patterns for memory {memory_id}")

    # Find patterns this memory is derived from or related to
    pattern_query = """
    MATCH (m:Memory {id: $memory_id})
    MATCH (m)-[:DERIVED_FROM|USES|APPLIES]->(p:Memory {type: 'code_pattern'})
    RETURN p.id as pattern_id, p.effectiveness as effectiveness
    """

    try:
        results = await backend.execute_query(pattern_query, {"memory_id": memory_id})

        for record in results:
            pattern_id = record["pattern_id"]
            await update_pattern_effectiveness(backend, pattern_id, success, impact * 0.5)

    except Exception as e:
        logger.error(f"Error propagating to patterns: {e}")


async def update_pattern_effectiveness(
    backend: GraphBackend,
    pattern_id: str,
    success: bool,
    impact: float = 1.0,
) -> bool:
    """
    Update effectiveness of a pattern based on usage outcome.

    Args:
        backend: Database backend
        pattern_id: ID of pattern to update
        success: Whether usage was successful
        impact: Impact weight (0.0 to 1.0)

    Returns:
        True if updated successfully

    Example:
        >>> await update_pattern_effectiveness(backend, "pattern_123", success=True, impact=0.8)
    """
    logger.info(f"Updating pattern {pattern_id} effectiveness: success={success}, impact={impact}")

    # Get pattern statistics
    stats_query = """
    MATCH (p:Memory {id: $pattern_id, type: 'code_pattern'})
    OPTIONAL MATCH (p)-[:DERIVED_FROM|USES|APPLIES]-(m:Memory)-[:RESULTED_IN]->(o:Outcome)
    RETURN p.effectiveness as current_effectiveness,
           p.confidence as current_confidence,
           p.usage_count as usage_count,
           count(o) as total_outcomes,
           sum(CASE WHEN o.success THEN 1 ELSE 0 END) as successful_outcomes
    """

    try:
        result = await backend.execute_query(stats_query, {"pattern_id": pattern_id})

        if not result:
            logger.warning(f"Pattern {pattern_id} not found")
            return False

        record = result[0]
        current_effectiveness = record.get("current_effectiveness", 0.5)
        current_confidence = record.get("current_confidence", 0.5)
        usage_count = record.get("usage_count", 0)
        total_outcomes = record.get("total_outcomes", 0)
        successful_outcomes = record.get("successful_outcomes", 0)

        # Calculate new effectiveness with dampening
        # Patterns should change more slowly than individual solutions
        dampening = 0.3  # Patterns change 30% as fast as solutions

        if total_outcomes > 0:
            success_rate = successful_outcomes / total_outcomes
            adjustment = ((1.0 if success else 0.0) - success_rate) * impact * dampening
        else:
            adjustment = ((1.0 if success else 0.0) - current_effectiveness) * impact * dampening

        new_effectiveness = current_effectiveness + adjustment
        new_effectiveness = max(0.0, min(1.0, new_effectiveness))

        # Increase confidence slightly
        new_confidence = min(0.95, current_confidence + 0.02)

        # Update pattern
        update_query = """
        MATCH (p:Memory {id: $pattern_id})
        SET p.effectiveness = $effectiveness,
            p.confidence = $confidence,
            p.usage_count = p.usage_count + 1,
            p.last_accessed = datetime($timestamp)
        RETURN p.effectiveness as effectiveness
        """

        await backend.execute_query(
            update_query,
            {
                "pattern_id": pattern_id,
                "effectiveness": new_effectiveness,
                "confidence": new_confidence,
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"Updated pattern {pattern_id} effectiveness: {new_effectiveness:.2f}")
        return True

    except Exception as e:
        logger.error(f"Error updating pattern effectiveness: {e}")
        return False


async def calculate_effectiveness_score(
    backend: GraphBackend,
    memory_id: str,
) -> Optional[EffectivenessScore]:
    """
    Calculate detailed effectiveness score for a memory.

    Args:
        backend: Database backend
        memory_id: ID of memory to analyze

    Returns:
        EffectivenessScore with statistics, or None if not found

    Example:
        >>> score = await calculate_effectiveness_score(backend, "solution_123")
        >>> print(f"Success rate: {score.successful_uses / score.total_uses}")
    """
    logger.debug(f"Calculating effectiveness score for {memory_id}")

    query = """
    MATCH (m:Memory {id: $memory_id})
    OPTIONAL MATCH (m)-[:RESULTED_IN]->(o:Outcome)
    RETURN m.effectiveness as effectiveness,
           m.confidence as confidence,
           count(o) as total_outcomes,
           sum(CASE WHEN o.success THEN 1 ELSE 0 END) as successful_outcomes,
           sum(CASE WHEN NOT o.success THEN 1 ELSE 0 END) as failed_outcomes
    """

    try:
        result = await backend.execute_query(query, {"memory_id": memory_id})

        if not result:
            return None

        record = result[0]

        return EffectivenessScore(
            memory_id=memory_id,
            total_uses=record.get("total_outcomes", 0),
            successful_uses=record.get("successful_outcomes", 0),
            failed_uses=record.get("failed_outcomes", 0),
            effectiveness=record.get("effectiveness", 0.5),
            confidence=record.get("confidence", 0.5),
            last_updated=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error calculating effectiveness score: {e}")
        return None


def design_decay_mechanism() -> Dict[str, Any]:
    """
    Design for effectiveness decay mechanism (not yet implemented).

    Old outcomes should have less weight over time. This function documents
    the design for a background job that would implement decay.

    Returns:
        Design specification for decay mechanism

    Design:
        - Run periodically (e.g., weekly)
        - For each memory with outcomes:
          - Calculate time-weighted effectiveness
          - Recent outcomes weighted more heavily
          - Very old outcomes (>1 year) have minimal weight
        - Use exponential decay: weight = e^(-age_in_days / half_life)
        - Recommended half_life: 180 days (6 months)

    Example implementation:
        ```python
        async def decay_effectiveness_scores(backend: GraphBackend):
            query = '''
            MATCH (m:Memory)-[:RESULTED_IN]->(o:Outcome)
            WITH m, o,
                 duration.between(o.timestamp, datetime()).days as age_days
            WITH m,
                 sum(o.impact * exp(-age_days / 180.0) *
                     (CASE WHEN o.success THEN 1.0 ELSE 0.0 END)) as weighted_success,
                 sum(o.impact * exp(-age_days / 180.0)) as weighted_total
            SET m.effectiveness = weighted_success / weighted_total,
                m.last_decayed = datetime()
            '''
            await backend.execute_query(query, {})
        ```
    """
    return {
        "mechanism": "exponential_decay",
        "half_life_days": 180,
        "decay_function": "weight = exp(-age_in_days / half_life)",
        "run_frequency": "weekly",
        "implementation": "background_job",
        "status": "designed_not_implemented",
        "priority": "medium",
        "estimated_effort": "4 hours",
    }
