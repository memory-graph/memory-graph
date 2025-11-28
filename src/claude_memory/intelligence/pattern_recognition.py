"""
Pattern Recognition - Identify reusable patterns from accumulated memories.

This module provides pattern matching, similar problem identification,
and pattern suggestion capabilities.
"""

import re
import logging
from typing import Optional
from datetime import datetime
from collections import Counter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Pattern(BaseModel):
    """Represents a recognized pattern."""

    id: str
    name: str
    description: str
    pattern_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    occurrences: int = 0
    source_memory_ids: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    context: Optional[dict] = None


class PatternRecognizer:
    """Recognizes patterns in memories using keyword and entity matching."""

    def __init__(self, backend):
        """
        Initialize pattern recognizer with database backend.

        Args:
            backend: Database backend instance
        """
        self.backend = backend

    async def find_similar_problems(
        self, problem: str, threshold: float = 0.7, limit: int = 10
    ) -> list[dict]:
        """
        Find similar problems and their solutions using keyword matching.

        Args:
            problem: Problem description to match against
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of similar problems with their solutions
        """
        # Extract keywords from problem
        keywords = self._extract_keywords(problem)

        if not keywords:
            return []

        # Search for problem-type memories with matching keywords
        query = """
        MATCH (m:Memory {type: 'problem'})
        WHERE any(keyword IN $keywords WHERE m.content CONTAINS keyword)
        OPTIONAL MATCH (m)-[r:SOLVES|SOLVED_BY]-(solution:Memory)
        WITH m, solution, r,
             size([keyword IN $keywords WHERE m.content CONTAINS keyword]) as match_count
        WITH m, solution, r,
             toFloat(match_count) / toFloat(size($keywords)) as similarity
        WHERE similarity >= $threshold
        ORDER BY similarity DESC, m.created_at DESC
        LIMIT $limit
        RETURN m.id as problem_id,
               m.title as problem_title,
               m.content as problem_content,
               m.created_at as created_at,
               similarity,
               collect({
                   id: solution.id,
                   title: solution.title,
                   content: solution.content,
                   effectiveness: r.effectiveness
               }) as solutions
        """

        params = {
            "keywords": keywords,
            "threshold": threshold,
            "limit": limit,
        }

        try:
            results = await self.backend.execute_query(query, params)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error finding similar problems: {e}")
            return []

    async def extract_patterns(
        self, memory_type: str = "solution", min_occurrences: int = 3
    ) -> list[Pattern]:
        """
        Extract common patterns from memories of a given type.

        Args:
            memory_type: Type of memories to analyze
            min_occurrences: Minimum number of occurrences to be considered a pattern

        Returns:
            List of identified patterns
        """
        # Find frequently co-occurring entities
        query = """
        MATCH (m:Memory {type: $memory_type})-[:MENTIONS]->(e:Entity)
        WITH e.text as entity, e.type as entity_type,
             collect(m.id) as memory_ids,
             count(m) as occurrence_count
        WHERE occurrence_count >= $min_occurrences
        RETURN entity, entity_type, memory_ids, occurrence_count
        ORDER BY occurrence_count DESC
        LIMIT 50
        """

        params = {
            "memory_type": memory_type,
            "min_occurrences": min_occurrences,
        }

        try:
            entity_results = await self.backend.execute_query(query, params)

            # Build patterns from frequent entities
            patterns: list[Pattern] = []

            for result in entity_results:
                pattern = Pattern(
                    id=f"pattern-{result['entity']}-{datetime.utcnow().timestamp()}",
                    name=f"{result['entity_type']} Pattern: {result['entity']}",
                    description=f"Common {memory_type} pattern involving {result['entity']}",
                    pattern_type=memory_type,
                    confidence=min(result["occurrence_count"] / 10.0, 1.0),
                    occurrences=result["occurrence_count"],
                    source_memory_ids=result["memory_ids"],
                    entities=[result["entity"]],
                )
                patterns.append(pattern)

            # Find co-occurring entity pairs
            if len(entity_results) > 1:
                co_occurrence_patterns = await self._find_entity_co_occurrences(
                    memory_type, min_occurrences
                )
                patterns.extend(co_occurrence_patterns)

            return patterns

        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return []

    async def _find_entity_co_occurrences(
        self, memory_type: str, min_occurrences: int
    ) -> list[Pattern]:
        """Find patterns from entities that frequently appear together."""
        query = """
        MATCH (m:Memory {type: $memory_type})-[:MENTIONS]->(e1:Entity)
        MATCH (m)-[:MENTIONS]->(e2:Entity)
        WHERE id(e1) < id(e2)
        WITH e1.text as entity1, e2.text as entity2,
             collect(m.id) as memory_ids,
             count(m) as occurrence_count
        WHERE occurrence_count >= $min_occurrences
        RETURN entity1, entity2, memory_ids, occurrence_count
        ORDER BY occurrence_count DESC
        LIMIT 20
        """

        params = {
            "memory_type": memory_type,
            "min_occurrences": min_occurrences,
        }

        try:
            results = await self.backend.execute_query(query, params)
            patterns: list[Pattern] = []

            for result in results:
                pattern = Pattern(
                    id=f"pattern-pair-{result['entity1']}-{result['entity2']}-{datetime.utcnow().timestamp()}",
                    name=f"Co-occurrence: {result['entity1']} + {result['entity2']}",
                    description=f"Frequent {memory_type} pattern combining {result['entity1']} and {result['entity2']}",
                    pattern_type=f"{memory_type}_combination",
                    confidence=min(result["occurrence_count"] / 5.0, 1.0),
                    occurrences=result["occurrence_count"],
                    source_memory_ids=result["memory_ids"],
                    entities=[result["entity1"], result["entity2"]],
                )
                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Error finding co-occurrences: {e}")
            return []

    async def suggest_patterns(self, context: str, limit: int = 5) -> list[Pattern]:
        """
        Suggest relevant patterns for given context.

        Args:
            context: Current context to match patterns against
            limit: Maximum number of suggestions

        Returns:
            List of relevant patterns
        """
        from claude_memory.intelligence.entity_extraction import extract_entities

        # Extract entities from context
        entities = extract_entities(context)

        if not entities:
            return []

        entity_texts = [e.text for e in entities]

        # Find patterns that match the context entities
        query = """
        UNWIND $entities as entity_text
        MATCH (m:Memory)-[:MENTIONS]->(e:Entity {text: entity_text})
        WITH m, collect(DISTINCT e.text) as matched_entities
        WHERE size(matched_entities) >= 1
        OPTIONAL MATCH (m)-[:MENTIONS]->(all_entities:Entity)
        WITH m, matched_entities,
             collect(DISTINCT all_entities.text) as all_entity_texts,
             size(matched_entities) as match_count
        RETURN m.id as memory_id,
               m.type as memory_type,
               m.title as title,
               m.content as content,
               matched_entities,
               all_entity_texts,
               match_count
        ORDER BY match_count DESC, m.created_at DESC
        LIMIT $limit
        """

        params = {
            "entities": entity_texts,
            "limit": limit * 2,  # Get more to filter
        }

        try:
            results = await self.backend.execute_query(query, params)

            patterns: list[Pattern] = []
            for idx, result in enumerate(results[:limit]):
                # Calculate relevance score
                overlap = len(set(result["matched_entities"]) & set(entity_texts))
                total_entities = len(set(result["all_entity_texts"]))
                relevance = overlap / max(total_entities, 1) if total_entities > 0 else 0

                pattern = Pattern(
                    id=result["memory_id"],
                    name=result.get("title", "Untitled Pattern"),
                    description=result.get("content", "")[:200],
                    pattern_type=result.get("memory_type", "unknown"),
                    confidence=min(relevance, 1.0),
                    occurrences=result["match_count"],
                    source_memory_ids=[result["memory_id"]],
                    entities=result["matched_entities"],
                )
                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Error suggesting patterns: {e}")
            return []

    def _extract_keywords(self, text: str) -> list[str]:
        """
        Extract keywords from text for matching.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        # Tokenize and clean
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())

        # Filter stop words and keep meaningful keywords
        keywords = [w for w in words if w not in stop_words]

        # Return unique keywords
        return list(set(keywords))


# Convenience functions using default backend parameter


async def find_similar_problems(
    backend, problem: str, threshold: float = 0.7, limit: int = 10
) -> list[dict]:
    """
    Find similar problems using keyword matching.

    Args:
        backend: Database backend instance
        problem: Problem description
        threshold: Similarity threshold (0.0-1.0)
        limit: Maximum results

    Returns:
        List of similar problems with solutions

    Example:
        >>> problems = await find_similar_problems(
        ...     backend,
        ...     "Authentication timeout in API",
        ...     threshold=0.6
        ... )
    """
    recognizer = PatternRecognizer(backend)
    return await recognizer.find_similar_problems(problem, threshold, limit)


async def extract_patterns(
    backend, memory_type: str = "solution", min_occurrences: int = 3
) -> list[Pattern]:
    """
    Extract patterns from memories.

    Args:
        backend: Database backend instance
        memory_type: Type of memories to analyze
        min_occurrences: Minimum occurrences

    Returns:
        List of patterns

    Example:
        >>> patterns = await extract_patterns(backend, "solution", min_occurrences=3)
        >>> for pattern in patterns:
        ...     print(f"{pattern.name}: {pattern.confidence}")
    """
    recognizer = PatternRecognizer(backend)
    return await recognizer.extract_patterns(memory_type, min_occurrences)


async def suggest_patterns(backend, context: str, limit: int = 5) -> list[Pattern]:
    """
    Suggest patterns for context.

    Args:
        backend: Database backend instance
        context: Current context
        limit: Maximum suggestions

    Returns:
        List of relevant patterns

    Example:
        >>> patterns = await suggest_patterns(
        ...     backend,
        ...     "Using React hooks with TypeScript"
        ... )
    """
    recognizer = PatternRecognizer(backend)
    return await recognizer.suggest_patterns(context, limit)
