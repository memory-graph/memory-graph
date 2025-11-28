"""
Predictive Suggestions for Claude Code Memory Server.

Provides proactive suggestions based on current context:
- Predict relevant memories and patterns
- Warn about potential issues
- Suggest related context

Phase 7 Implementation - Predictive Suggestions
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from pydantic import BaseModel, Field

from ..backends.base import GraphBackend
from ..models import Memory, MemoryType, RelationshipType
from ..intelligence.entity_extraction import extract_entities, Entity

logger = logging.getLogger(__name__)


class Suggestion(BaseModel):
    """
    Proactive suggestion for relevant memory or pattern.

    Suggestions are ranked by relevance score.
    """

    suggestion_id: str
    suggestion_type: str  # "memory", "pattern", "solution"
    title: str
    description: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    reason: str  # Why this is suggested
    memory_id: str
    tags: List[str] = Field(default_factory=list)
    effectiveness: Optional[float] = None


class Warning(BaseModel):
    """
    Warning about potential issues.

    Based on known problems and patterns.
    """

    warning_id: str
    severity: str  # "low", "medium", "high"
    title: str
    description: str
    evidence: List[str] = Field(default_factory=list)  # Memory IDs that support this warning
    mitigation: Optional[str] = None  # Suggested mitigation
    related_problem_id: Optional[str] = None


async def predict_needs(
    backend: GraphBackend,
    current_context: str,
    max_suggestions: int = 5,
    min_relevance: float = 0.3,
) -> List[Suggestion]:
    """
    Predict relevant memories and patterns based on current context.

    Uses entity extraction and relationship matching to find relevant information.

    Args:
        backend: Database backend
        current_context: Current work context (e.g., file content, task description)
        max_suggestions: Maximum number of suggestions to return
        min_relevance: Minimum relevance score threshold

    Returns:
        List of suggestions ranked by relevance

    Example:
        >>> suggestions = await predict_needs(backend, "Working on authentication with JWT")
        >>> for s in suggestions:
        ...     print(f"{s.title}: {s.reason}")
    """
    logger.info("Predicting needs from current context")

    # Extract entities from current context
    entities = extract_entities(current_context)
    logger.debug(f"Extracted {len(entities)} entities from context")

    if not entities:
        logger.warning("No entities extracted from context")
        return []

    suggestions = []

    # Find memories that mention the same entities
    for entity in entities[:10]:  # Limit to top 10 entities to avoid overwhelming queries
        entity_query = """
        MATCH (m:Memory)-[:MENTIONS]->(e:Entity {text: $entity_text})
        WHERE m.type IN ['solution', 'code_pattern', 'fix']
        OPTIONAL MATCH (m)-[r:EFFECTIVE_FOR|SOLVES|ADDRESSES]->()
        RETURN m.id as id, m.type as type, m.title as title,
               m.content as content, m.tags as tags,
               m.effectiveness as effectiveness,
               m.usage_count as usage_count,
               count(r) as effectiveness_links
        ORDER BY m.effectiveness DESC, m.usage_count DESC
        LIMIT 3
        """

        try:
            results = await backend.execute_query(
                entity_query,
                {"entity_text": entity.text}
            )

            for record in results:
                # Calculate relevance score based on:
                # - Entity match (base score)
                # - Effectiveness
                # - Usage count
                # - Number of effectiveness relationships
                base_score = entity.confidence
                effectiveness_bonus = record.get("effectiveness", 0.5) * 0.3
                usage_bonus = min(record.get("usage_count", 0) / 10.0, 0.2)
                links_bonus = min(record.get("effectiveness_links", 0) / 5.0, 0.2)

                relevance = base_score + effectiveness_bonus + usage_bonus + links_bonus
                relevance = min(relevance, 1.0)  # Cap at 1.0

                if relevance >= min_relevance:
                    suggestions.append(Suggestion(
                        suggestion_id=record["id"],
                        suggestion_type=record["type"],
                        title=record["title"],
                        description=record["content"][:200],
                        relevance_score=relevance,
                        reason=f"Related to {entity.entity_type.value}: {entity.text}",
                        memory_id=record["id"],
                        tags=record.get("tags", []),
                        effectiveness=record.get("effectiveness"),
                    ))

        except Exception as e:
            logger.error(f"Error querying memories for entity {entity.text}: {e}")

    # Find patterns that match the context
    pattern_keywords = [(e.text.lower(), e.confidence) for e in entities if e.entity_type.value in ["technology", "concept"]]

    if pattern_keywords:
        pattern_query = """
        MATCH (p:Memory {type: 'code_pattern'})
        WHERE any(keyword IN $keywords WHERE p.content CONTAINS keyword)
        RETURN p.id as id, p.title as title, p.content as content,
               p.tags as tags, p.effectiveness as effectiveness,
               p.usage_count as usage_count
        ORDER BY p.effectiveness DESC
        LIMIT 3
        """

        try:
            # Get average confidence of matching entities
            avg_confidence = sum(conf for _, conf in pattern_keywords) / len(pattern_keywords)
            keywords_only = [kw for kw, _ in pattern_keywords]

            results = await backend.execute_query(
                pattern_query,
                {"keywords": keywords_only}
            )

            for record in results:
                # Calculate relevance for patterns based on entity confidence
                effectiveness = record.get("effectiveness", 0.5)
                usage_count = record.get("usage_count", 0)

                # Use entity confidence as base, similar to entity-based suggestions
                relevance = avg_confidence + (effectiveness * 0.3) + min(usage_count / 10.0, 0.1)
                relevance = min(relevance, 1.0)  # Cap at 1.0

                if relevance >= min_relevance:
                    suggestions.append(Suggestion(
                        suggestion_id=record["id"],
                        suggestion_type="pattern",
                        title=record["title"],
                        description=record["content"][:200],
                        relevance_score=relevance,
                        reason="Matching pattern for current context",
                        memory_id=record["id"],
                        tags=record.get("tags", []),
                        effectiveness=record.get("effectiveness"),
                    ))

        except Exception as e:
            logger.error(f"Error querying patterns: {e}")

    # Deduplicate and sort by relevance
    seen_ids = set()
    unique_suggestions = []
    for suggestion in sorted(suggestions, key=lambda s: s.relevance_score, reverse=True):
        if suggestion.memory_id not in seen_ids:
            unique_suggestions.append(suggestion)
            seen_ids.add(suggestion.memory_id)

    logger.info(f"Generated {len(unique_suggestions)} suggestions")
    return unique_suggestions[:max_suggestions]


async def warn_potential_issues(
    backend: GraphBackend,
    current_context: str,
    severity_threshold: str = "medium",
) -> List[Warning]:
    """
    Warn about potential issues based on current context.

    Matches against known problem patterns and deprecated approaches.

    Args:
        backend: Database backend
        current_context: Current work context
        severity_threshold: Minimum severity to report ("low", "medium", "high")

    Returns:
        List of warnings with evidence

    Example:
        >>> warnings = await warn_potential_issues(backend, "Using JWT authentication")
        >>> for w in warnings:
        ...     print(f"{w.severity.upper()}: {w.title}")
    """
    logger.info("Checking for potential issues in current context")

    # Extract entities from context
    entities = extract_entities(current_context)

    warnings = []

    # Check for deprecated approaches
    entity_texts = [e.text for e in entities]

    if entity_texts:
        deprecated_query = """
        MATCH (old:Memory)-[r:DEPRECATED_BY]->(new:Memory)
        MATCH (old)-[:MENTIONS]->(e:Entity)
        WHERE e.text IN $entity_texts
        RETURN old.id as old_id, old.title as old_title,
               old.content as old_content,
               new.id as new_id, new.title as new_title,
               r.context as reason,
               collect(e.text) as entities
        """

        try:
            results = await backend.execute_query(
                deprecated_query,
                {"entity_texts": entity_texts}
            )

            for record in results:
                warnings.append(Warning(
                    warning_id=record["old_id"],
                    severity="high",
                    title=f"Deprecated: {record['old_title']}",
                    description=record.get("reason", "This approach is deprecated"),
                    evidence=[record["old_id"]],
                    mitigation=f"Consider using: {record['new_title']}",
                    related_problem_id=record["old_id"],
                ))

        except Exception as e:
            logger.error(f"Error checking for deprecated approaches: {e}")

    # Check for known problem patterns
    problem_keywords = [e.text.lower() for e in entities]

    if problem_keywords:
        problem_query = """
        MATCH (p:Memory {type: 'problem'})
        WHERE any(keyword IN $keywords WHERE p.content CONTAINS keyword)
        OPTIONAL MATCH (p)-[:SOLVES|ADDRESSES]-(s:Memory {type: 'solution'})
        RETURN p.id as problem_id, p.title as problem_title,
               p.content as problem_content, p.tags as tags,
               collect(s.id) as solution_ids,
               collect(s.title) as solution_titles
        LIMIT 5
        """

        try:
            results = await backend.execute_query(
                problem_query,
                {"keywords": problem_keywords}
            )

            for record in results:
                # If problem has solutions, suggest them; otherwise warn
                has_solutions = bool(record.get("solution_ids"))

                if has_solutions:
                    mitigation = f"Known solutions: {', '.join(record['solution_titles'][:2])}"
                    severity = "medium"
                else:
                    mitigation = "No known solution yet - proceed with caution"
                    severity = "high"

                warnings.append(Warning(
                    warning_id=record["problem_id"],
                    severity=severity,
                    title=f"Known issue: {record['problem_title']}",
                    description=record["problem_content"][:200],
                    evidence=[record["problem_id"]],
                    mitigation=mitigation,
                    related_problem_id=record["problem_id"],
                ))

        except Exception as e:
            logger.error(f"Error checking for known problems: {e}")

    # Filter by severity threshold
    severity_levels = {"low": 0, "medium": 1, "high": 2}
    threshold_level = severity_levels.get(severity_threshold, 1)

    filtered_warnings = [
        w for w in warnings
        if severity_levels.get(w.severity, 0) >= threshold_level
    ]

    logger.info(f"Generated {len(filtered_warnings)} warnings")
    return filtered_warnings


async def suggest_related_context(
    backend: GraphBackend,
    memory_id: str,
    max_suggestions: int = 5,
) -> List[Suggestion]:
    """
    Suggest related context that the user might want to know about.

    "You might also want to know..." suggestions based on relationship graph.

    Args:
        backend: Database backend
        memory_id: Current memory being viewed
        max_suggestions: Maximum number of suggestions

    Returns:
        List of related suggestions

    Example:
        >>> suggestions = await suggest_related_context(backend, "mem_123")
        >>> for s in suggestions:
        ...     print(f"Related: {s.title}")
    """
    logger.info(f"Suggesting related context for memory {memory_id}")

    # Find related memories through strong relationships
    related_query = """
    MATCH (m:Memory {id: $memory_id})-[r]->(related:Memory)
    WHERE r.strength >= 0.5
      AND type(r) IN ['BUILDS_ON', 'CONFIRMS', 'SIMILAR_TO', 'RELATED_TO',
                      'ALTERNATIVE_TO', 'IMPROVES']
    RETURN related.id as id, related.type as type, related.title as title,
           related.content as content, related.tags as tags,
           related.effectiveness as effectiveness,
           type(r) as rel_type, r.strength as strength
    ORDER BY r.strength DESC
    LIMIT $limit
    """

    suggestions = []

    try:
        results = await backend.execute_query(
            related_query,
            {"memory_id": memory_id, "limit": max_suggestions}
        )

        for record in results:
            rel_type = record["rel_type"]
            strength = record.get("strength", 0.5)

            # Map relationship type to reason
            reasons = {
                "BUILDS_ON": "Builds on this concept",
                "CONFIRMS": "Confirms this approach",
                "SIMILAR_TO": "Similar approach",
                "RELATED_TO": "Related information",
                "ALTERNATIVE_TO": "Alternative approach",
                "IMPROVES": "Improved version",
            }

            reason = reasons.get(rel_type, "Related")

            suggestions.append(Suggestion(
                suggestion_id=record["id"],
                suggestion_type=record["type"],
                title=record["title"],
                description=record["content"][:200],
                relevance_score=strength,
                reason=reason,
                memory_id=record["id"],
                tags=record.get("tags", []),
                effectiveness=record.get("effectiveness"),
            ))

    except Exception as e:
        logger.error(f"Error finding related context: {e}")

    logger.info(f"Found {len(suggestions)} related suggestions")
    return suggestions[:max_suggestions]
