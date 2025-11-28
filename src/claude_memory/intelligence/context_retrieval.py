"""
Context-Aware Retrieval - Intelligent context retrieval beyond keyword search.

This module provides smart context assembly, relevance ranking,
and token-limited context formatting.
"""

import logging
import re
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContextRetriever:
    """Retrieves and ranks context intelligently with relevance-based scoring."""

    def __init__(self, backend):
        """
        Initialize context retriever with database backend.

        Args:
            backend: Database backend instance
        """
        self.backend = backend

    async def get_context(
        self, query: str, max_tokens: int = 4000, project: Optional[str] = None
    ) -> dict:
        """
        Get intelligent context for a query with smart ranking and token limiting.

        Args:
            query: User query to get context for
            max_tokens: Maximum tokens to include in context
            project: Optional project filter

        Returns:
            Dictionary with formatted context and source memory IDs
        """
        from claude_memory.intelligence.entity_extraction import extract_entities

        # Extract entities from query for matching
        entities = extract_entities(query)
        entity_texts = [e.text for e in entities if e.confidence > 0.6]

        # Extract keywords for fallback matching
        keywords = self._extract_keywords(query)

        # Build search query
        search_query = """
        // Find memories matching entities or keywords
        MATCH (m:Memory)
        WHERE (
            // Match by entities
            any(entity IN $entities WHERE
                exists((m)-[:MENTIONS]->(:Entity {text: entity}))
            )
            OR
            // Match by keywords
            any(keyword IN $keywords WHERE
                toLower(m.content) CONTAINS keyword OR
                toLower(m.title) CONTAINS keyword
            )
        )
        // Apply project filter if provided
        WITH m
        WHERE $project IS NULL OR $project IN m.tags

        // Calculate relevance score
        WITH m,
             // Entity match score
             size([entity IN $entities WHERE
                   exists((m)-[:MENTIONS]->(:Entity {text: entity}))]) as entity_matches,
             // Keyword match score
             size([keyword IN $keywords WHERE
                   toLower(m.content) CONTAINS keyword OR
                   toLower(m.title) CONTAINS keyword]) as keyword_matches,
             // Recency score (newer is better)
             duration.between(m.created_at, datetime()).days as age_days

        WITH m, entity_matches, keyword_matches, age_days,
             // Combined relevance score
             toFloat(entity_matches * 3 + keyword_matches * 2) /
             (1.0 + age_days / 30.0) as relevance_score

        // Get related memories via relationships
        OPTIONAL MATCH (m)-[r]->(related:Memory)
        WHERE type(r) IN ['SOLVES', 'BUILDS_ON', 'REQUIRES', 'RELATED_TO']
        WITH m, relevance_score,
             collect(DISTINCT {
                 id: related.id,
                 title: related.title,
                 rel_type: type(r),
                 rel_strength: coalesce(r.strength, 0.5)
             }) as related_memories

        // Order by relevance and limit results
        ORDER BY relevance_score DESC, m.created_at DESC
        LIMIT 20

        RETURN m.id as id,
               m.title as title,
               m.content as content,
               m.type as memory_type,
               m.tags as tags,
               m.created_at as created_at,
               relevance_score,
               entity_matches,
               keyword_matches,
               related_memories
        """

        params = {
            "entities": entity_texts,
            "keywords": keywords,
            "project": project,
        }

        try:
            results = await self.backend.execute_query(search_query, params)

            # Format context within token limit
            context_parts = []
            source_memories = []
            estimated_tokens = 0

            for record in results:
                memory_summary = self._format_memory(record)
                memory_tokens = self._estimate_tokens(memory_summary)

                if estimated_tokens + memory_tokens > max_tokens:
                    break

                context_parts.append(memory_summary)
                source_memories.append({
                    "id": record["id"],
                    "title": record.get("title"),
                    "relevance": float(record.get("relevance_score", 0)),
                })
                estimated_tokens += memory_tokens

            # Build structured context
            context = "\n\n".join(context_parts)

            return {
                "context": context,
                "source_memories": source_memories,
                "total_memories": len(source_memories),
                "estimated_tokens": estimated_tokens,
                "query_entities": entity_texts,
                "query_keywords": keywords,
            }

        except Exception as e:
            logger.error(f"Error retrieving context for query '{query}': {e}")
            return {
                "context": "",
                "source_memories": [],
                "error": str(e),
            }

    async def get_project_context(self, project: str) -> dict:
        """
        Get comprehensive overview of a project.

        Args:
            project: Project name or identifier

        Returns:
            Project context with recent activities, decisions, and issues
        """
        query = """
        MATCH (m:Memory)
        WHERE $project IN m.tags

        WITH m
        ORDER BY m.created_at DESC

        WITH collect(m) as all_memories

        // Get recent memories
        WITH all_memories,
             [m IN all_memories WHERE m.created_at >= datetime() - duration({days: 7})][..10] as recent,
             [m IN all_memories WHERE m.type = 'decision'][..5] as decisions,
             [m IN all_memories WHERE m.type = 'problem' AND
              NOT exists((m)<-[:SOLVES]-(:Memory))][..5] as open_problems,
             [m IN all_memories WHERE m.type = 'solution'][..5] as solutions

        RETURN {
            total_memories: size(all_memories),
            recent_activity: [m IN recent | {
                id: m.id,
                title: m.title,
                type: m.type,
                created_at: m.created_at
            }],
            decisions: [m IN decisions | {
                id: m.id,
                title: m.title,
                created_at: m.created_at
            }],
            open_problems: [m IN open_problems | {
                id: m.id,
                title: m.title,
                created_at: m.created_at
            }],
            solutions: [m IN solutions | {
                id: m.id,
                title: m.title,
                created_at: m.created_at
            }]
        } as project_summary
        """

        params = {"project": project}

        try:
            results = await self.backend.execute_query(query, params)

            if results and "project_summary" in results[0]:
                return results[0]["project_summary"]
            else:
                return {
                    "total_memories": 0,
                    "recent_activity": [],
                    "decisions": [],
                    "open_problems": [],
                    "solutions": [],
                }

        except Exception as e:
            logger.error(f"Error getting project context for '{project}': {e}")
            return {"error": str(e)}

    async def get_session_context(
        self, hours_back: int = 24, limit: int = 10
    ) -> dict:
        """
        Get recent session context from the last N hours.

        Args:
            hours_back: How many hours of history to include
            limit: Maximum number of memories to return

        Returns:
            Recent session context
        """
        query = """
        MATCH (m:Memory)
        WHERE m.created_at >= datetime() - duration({hours: $hours_back})

        WITH m
        ORDER BY m.created_at DESC
        LIMIT $limit

        // Get related patterns
        OPTIONAL MATCH (m)-[:MENTIONS]->(e:Entity)
        WITH m, collect(DISTINCT e.text) as entities

        RETURN m.id as id,
               m.title as title,
               m.content as content,
               m.type as memory_type,
               m.created_at as created_at,
               entities
        ORDER BY m.created_at DESC
        """

        params = {
            "hours_back": hours_back,
            "limit": limit,
        }

        try:
            results = await self.backend.execute_query(query, params)

            memories = []
            all_entities = set()

            for record in results:
                memories.append({
                    "id": record["id"],
                    "title": record.get("title"),
                    "type": record.get("memory_type"),
                    "created_at": record.get("created_at"),
                    "entities": record.get("entities", []),
                })
                all_entities.update(record.get("entities", []))

            return {
                "recent_memories": memories,
                "total_count": len(memories),
                "time_range_hours": hours_back,
                "active_entities": list(all_entities),
            }

        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {"error": str(e)}

    def _format_memory(self, record: dict) -> str:
        """
        Format a memory record into readable context.

        Args:
            record: Memory record from database

        Returns:
            Formatted string representation
        """
        title = record.get("title", "Untitled")
        memory_type = record.get("memory_type", "unknown")
        content = record.get("content", "")
        relevance = record.get("relevance_score", 0)

        # Truncate content if too long
        if len(content) > 500:
            content = content[:497] + "..."

        formatted = f"## {title} ({memory_type})\n"
        if relevance > 0:
            formatted += f"Relevance: {relevance:.2f}\n"
        formatted += f"{content}"

        # Add related memories if present
        related = record.get("related_memories", [])
        if related:
            formatted += "\n\nRelated: "
            related_titles = [r.get("title", "Untitled") for r in related[:3]]
            formatted += ", ".join(related_titles)

        return formatted

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def _extract_keywords(self, text: str) -> list[str]:
        """
        Extract keywords from query text.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "will", "would", "should", "could", "may",
            "might", "can", "this", "that", "these", "those", "what", "which",
            "who", "when", "where", "why", "how",
        }

        # Tokenize and filter
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        keywords = [w for w in words if w not in stop_words]

        # Return unique keywords
        return list(set(keywords))


# Convenience functions


async def get_context(
    backend, query: str, max_tokens: int = 4000, project: Optional[str] = None
) -> dict:
    """
    Get intelligent context for a query.

    Args:
        backend: Database backend instance
        query: User query
        max_tokens: Maximum tokens in context
        project: Optional project filter

    Returns:
        Context dictionary with formatted text and source memories

    Example:
        >>> context = await get_context(
        ...     backend,
        ...     "How do I implement authentication?",
        ...     max_tokens=2000
        ... )
        >>> print(context["context"])
    """
    retriever = ContextRetriever(backend)
    return await retriever.get_context(query, max_tokens, project)


async def get_project_context(backend, project: str) -> dict:
    """
    Get comprehensive project overview.

    Args:
        backend: Database backend instance
        project: Project name

    Returns:
        Project context with activities and issues

    Example:
        >>> context = await get_project_context(backend, "my-app")
        >>> print(f"Total memories: {context['total_memories']}")
        >>> print(f"Open problems: {len(context['open_problems'])}")
    """
    retriever = ContextRetriever(backend)
    return await retriever.get_project_context(project)


async def get_session_context(
    backend, hours_back: int = 24, limit: int = 10
) -> dict:
    """
    Get recent session context.

    Args:
        backend: Database backend instance
        hours_back: Hours of history to include
        limit: Maximum memories to return

    Returns:
        Recent session context

    Example:
        >>> context = await get_session_context(backend, hours_back=12)
        >>> for memory in context["recent_memories"]:
        ...     print(f"{memory['title']} - {memory['type']}")
    """
    retriever = ContextRetriever(backend)
    return await retriever.get_session_context(hours_back, limit)
