"""
Advanced Analytics Queries for Claude Code Memory Server.

Provides sophisticated graph analytics:
- Graph visualization data (D3/vis.js compatible)
- Solution similarity matching
- Solution effectiveness prediction
- Learning path recommendations
- Knowledge gap identification
- Memory ROI tracking

Phase 7 Implementation - Advanced Query & Analytics
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import logging
from collections import defaultdict

from pydantic import BaseModel, Field, ConfigDict

from ..backends.base import GraphBackend
from ..models import Memory, MemoryType, RelationshipType

logger = logging.getLogger(__name__)


class GraphNode(BaseModel):
    """Node in visualization graph."""

    id: str
    label: str
    type: str
    group: int = 0  # For coloring
    value: float = 1.0  # Node size
    title: Optional[str] = None  # Hover text


class GraphEdge(BaseModel):
    """Edge in visualization graph."""

    model_config = ConfigDict(
        populate_by_name=True
    )

    from_: str = Field(..., alias="from")
    to: str
    type: str
    value: float = 1.0  # Edge width/weight
    title: Optional[str] = None  # Hover text


class GraphVisualizationData(BaseModel):
    """
    Graph visualization data compatible with D3.js and vis.js.

    Can be directly consumed by visualization libraries.
    """

    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SimilarSolution(BaseModel):
    """Similar solution to a given solution."""

    solution_id: str
    title: str
    description: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    shared_entities: List[str] = Field(default_factory=list)
    shared_tags: List[str] = Field(default_factory=list)
    effectiveness: Optional[float] = None


class LearningPath(BaseModel):
    """Recommended learning path for a topic."""

    path_id: str
    topic: str
    steps: List[Dict[str, str]] = Field(default_factory=list)
    total_memories: int = 0
    estimated_value: float = 0.0


class KnowledgeGap(BaseModel):
    """Identified knowledge gap."""

    gap_id: str
    topic: str
    description: str
    severity: str = "medium"  # low, medium, high
    related_memories: int = 0
    suggestions: List[str] = Field(default_factory=list)


class MemoryROI(BaseModel):
    """Memory return on investment tracking."""

    memory_id: str
    title: str
    creation_date: datetime
    times_accessed: int = 0
    times_helpful: int = 0
    success_rate: float = 0.0
    value_score: float = 0.0
    last_used: Optional[datetime] = None


async def get_memory_graph_visualization(
    backend: GraphBackend,
    center_memory_id: Optional[str] = None,
    depth: int = 2,
    max_nodes: int = 100,
    include_types: Optional[List[str]] = None,
) -> GraphVisualizationData:
    """
    Get graph visualization data centered on a memory or full graph.

    Args:
        backend: Database backend
        center_memory_id: Optional center memory (None = full graph)
        depth: Depth to traverse from center
        max_nodes: Maximum nodes to return
        include_types: Filter to specific memory types

    Returns:
        GraphVisualizationData for D3/vis.js

    Example:
        >>> viz_data = await get_memory_graph_visualization(backend, "mem_123", depth=2)
        >>> # Use viz_data.nodes and viz_data.edges in your visualization
    """
    logger.info(f"Generating graph visualization: center={center_memory_id}, depth={depth}")

    visualization = GraphVisualizationData()

    # Set metadata early so it's available even if query fails
    visualization.metadata = {
        "node_count": 0,
        "edge_count": 0,
        "center_id": center_memory_id,
        "depth": depth,
        "generated_at": datetime.now().isoformat(),
    }

    if center_memory_id:
        # Get subgraph around center
        query = """
        MATCH path = (center:Memory {id: $center_id})-[*1..$depth]-(m:Memory)
        WITH center, m, relationships(path) as rels
        OPTIONAL MATCH (m)-[r]-(other:Memory)
        WHERE other IN collect(center) + collect(m)
        RETURN DISTINCT
            collect(DISTINCT center) + collect(DISTINCT m) as memories,
            collect(DISTINCT r) as relationships
        LIMIT 1
        """

        params = {"center_id": center_memory_id, "depth": depth}
    else:
        # Get full graph (limited)
        type_filter = ""
        if include_types:
            type_filter = "WHERE m.type IN $types"

        query = f"""
        MATCH (m:Memory)
        {type_filter}
        WITH m
        LIMIT $max_nodes
        OPTIONAL MATCH (m)-[r]-(other:Memory)
        WHERE other.id IN [m2 IN collect(m) | m2.id]
        RETURN collect(DISTINCT m) as memories,
               collect(DISTINCT r) as relationships
        """

        params = {"max_nodes": max_nodes}
        if include_types:
            params["types"] = include_types

    try:
        results = await backend.execute_query(query, params)

        if not results:
            return visualization

        memories = results[0].get("memories", [])
        relationships = results[0].get("relationships", [])

        # Create nodes
        type_groups = {
            "problem": 0,
            "solution": 1,
            "code_pattern": 2,
            "task": 3,
            "project": 4,
        }

        for mem in memories[:max_nodes]:
            mem_type = mem.get("type", "general")
            node = GraphNode(
                id=mem["id"],
                label=mem.get("title", "Untitled")[:50],
                type=mem_type,
                group=type_groups.get(mem_type, 5),
                value=mem.get("importance", 0.5) * 10,
                title=f"{mem_type}: {mem.get('title', 'Untitled')}",
            )
            visualization.nodes.append(node)

        # Create edges
        for rel in relationships:
            edge = GraphEdge(**{
                "from": rel["from_id"],
                "to": rel["to_id"],
                "type": rel.get("type", "RELATED_TO"),
                "value": rel.get("strength", 0.5) * 5,
                "title": f"{rel.get('type', 'RELATED_TO')} (strength: {rel.get('strength', 0.5):.2f})",
            })
            visualization.edges.append(edge)

        # Update metadata with actual counts
        visualization.metadata.update({
            "node_count": len(visualization.nodes),
            "edge_count": len(visualization.edges),
        })

        logger.info(f"Generated visualization: {len(visualization.nodes)} nodes, {len(visualization.edges)} edges")

    except Exception as e:
        logger.error(f"Error generating visualization: {e}")

    return visualization


async def analyze_solution_similarity(
    backend: GraphBackend,
    solution_id: str,
    top_k: int = 5,
    min_similarity: float = 0.3,
) -> List[SimilarSolution]:
    """
    Find solutions similar to a given solution.

    Uses shared entities, tags, and problem types to calculate similarity.

    Args:
        backend: Database backend
        solution_id: Solution to find similar solutions for
        top_k: Number of similar solutions to return
        min_similarity: Minimum similarity threshold

    Returns:
        List of similar solutions ranked by similarity

    Example:
        >>> similar = await analyze_solution_similarity(backend, "solution_123")
        >>> for sol in similar:
        ...     print(f"{sol.title}: {sol.similarity_score:.2f}")
    """
    logger.info(f"Analyzing similarity for solution {solution_id}")

    # Get entities and tags for target solution
    target_query = """
    MATCH (s:Memory {id: $solution_id})
    OPTIONAL MATCH (s)-[:MENTIONS]->(e:Entity)
    RETURN s.tags as tags, collect(e.text) as entities
    """

    try:
        result = await backend.execute_query(target_query, {"solution_id": solution_id})

        if not result:
            return []

        target_tags = set(result[0].get("tags", []))
        target_entities = set(result[0].get("entities", []))

        # Find similar solutions
        similarity_query = """
        MATCH (other:Memory)
        WHERE other.id <> $solution_id
          AND other.type IN ['solution', 'fix']
        OPTIONAL MATCH (other)-[:MENTIONS]->(e:Entity)
        WITH other,
             other.tags as tags,
             collect(e.text) as entities
        RETURN other.id as id, other.title as title,
               other.content as content, tags, entities,
               other.effectiveness as effectiveness
        LIMIT 50
        """

        results = await backend.execute_query(
            similarity_query,
            {"solution_id": solution_id}
        )

        similar_solutions = []

        for record in results:
            other_tags = set(record.get("tags", []))
            other_entities = set(record.get("entities", []))

            # Calculate similarity
            # Jaccard similarity for entities and tags
            shared_entities = target_entities & other_entities
            shared_tags = target_tags & other_tags

            entity_similarity = (
                len(shared_entities) / len(target_entities | other_entities)
                if target_entities or other_entities else 0.0
            )

            tag_similarity = (
                len(shared_tags) / len(target_tags | other_tags)
                if target_tags or other_tags else 0.0
            )

            # Weighted combination
            similarity = (entity_similarity * 0.6) + (tag_similarity * 0.4)

            if similarity >= min_similarity:
                similar_solutions.append(SimilarSolution(
                    solution_id=record["id"],
                    title=record["title"],
                    description=record["content"][:200],
                    similarity_score=similarity,
                    shared_entities=list(shared_entities),
                    shared_tags=list(shared_tags),
                    effectiveness=record.get("effectiveness"),
                ))

        # Sort by similarity
        similar_solutions.sort(key=lambda s: s.similarity_score, reverse=True)

        logger.info(f"Found {len(similar_solutions)} similar solutions")
        return similar_solutions[:top_k]

    except Exception as e:
        logger.error(f"Error analyzing similarity: {e}")
        return []


async def predict_solution_effectiveness(
    backend: GraphBackend,
    problem_description: str,
    solution_id: str,
) -> float:
    """
    Predict how effective a solution will be for a problem.

    Based on:
    - Solution's historical effectiveness
    - Similarity to successful past uses
    - Entity matches with problem

    Args:
        backend: Database backend
        problem_description: Description of the problem
        solution_id: Solution being considered

    Returns:
        Predicted effectiveness score (0.0 to 1.0)

    Example:
        >>> score = await predict_solution_effectiveness(
        ...     backend,
        ...     "Authentication failing with JWT",
        ...     "solution_456"
        ... )
        >>> print(f"Predicted effectiveness: {score:.2%}")
    """
    logger.info(f"Predicting effectiveness of solution {solution_id}")

    # Get solution's historical effectiveness
    solution_query = """
    MATCH (s:Memory {id: $solution_id})
    OPTIONAL MATCH (s)-[:RESULTED_IN]->(o:Outcome)
    RETURN s.effectiveness as base_effectiveness,
           s.confidence as confidence,
           count(o) as outcomes,
           sum(CASE WHEN o.success THEN 1 ELSE 0 END) as successes
    """

    try:
        result = await backend.execute_query(
            solution_query,
            {"solution_id": solution_id}
        )

        if not result:
            return 0.5  # Default

        record = result[0]
        base_effectiveness = record.get("base_effectiveness", 0.5)
        confidence = record.get("confidence", 0.5)

        # If high confidence, trust the historical score
        if confidence > 0.7:
            return base_effectiveness

        # Otherwise, blend with entity matching
        # (This would ideally use embeddings, but we'll use entity matching)

        # Extract entities from problem description
        from ..intelligence.entity_extraction import extract_entities

        entities = extract_entities(problem_description)
        entity_texts = [e.text for e in entities]

        if not entity_texts:
            return base_effectiveness

        # Check if solution has been used with similar entities
        entity_match_query = """
        MATCH (s:Memory {id: $solution_id})-[:MENTIONS]->(e:Entity)
        WHERE e.text IN $entity_texts
        RETURN count(DISTINCT e) as matched_entities
        """

        entity_result = await backend.execute_query(
            entity_match_query,
            {"solution_id": solution_id, "entity_texts": entity_texts}
        )

        matched_count = entity_result[0]["matched_entities"] if entity_result else 0
        entity_match_score = min(matched_count / len(entity_texts), 1.0)

        # Blend scores
        predicted = (base_effectiveness * 0.7) + (entity_match_score * 0.3)

        logger.info(f"Predicted effectiveness: {predicted:.2f} (base: {base_effectiveness:.2f}, match: {entity_match_score:.2f})")
        return predicted

    except Exception as e:
        logger.error(f"Error predicting effectiveness: {e}")
        return 0.5


async def recommend_learning_paths(
    backend: GraphBackend,
    topic: str,
    max_paths: int = 3,
) -> List[LearningPath]:
    """
    Recommend learning paths for a topic.

    Analyzes memory relationships to suggest learning sequences.

    Args:
        backend: Database backend
        topic: Topic to learn about
        max_paths: Maximum number of paths to return

    Returns:
        List of recommended learning paths

    Example:
        >>> paths = await recommend_learning_paths(backend, "React authentication")
        >>> for path in paths:
        ...     print(f"Path {path.path_id}: {len(path.steps)} steps")
    """
    logger.info(f"Recommending learning paths for topic: {topic}")

    # Find memories related to topic
    topic_query = """
    MATCH (m:Memory)
    WHERE m.content CONTAINS $topic
       OR any(tag IN m.tags WHERE tag CONTAINS $topic_lower)
       OR m.title CONTAINS $topic
    WITH m
    LIMIT 20
    MATCH path = (m)-[:BUILDS_ON|GENERALIZES|SPECIALIZES*1..3]-(related:Memory)
    RETURN m, collect(DISTINCT related) as related_memories,
           length(path) as path_length
    ORDER BY path_length DESC
    LIMIT $max_paths
    """

    try:
        results = await backend.execute_query(
            topic_query,
            {
                "topic": topic,
                "topic_lower": topic.lower(),
                "max_paths": max_paths,
            }
        )

        paths = []

        for idx, record in enumerate(results):
            start_memory = record["m"]
            related = record.get("related_memories", [])

            steps = [
                {
                    "memory_id": start_memory["id"],
                    "title": start_memory["title"],
                    "type": start_memory["type"],
                    "step": 1,
                }
            ]

            # Add related memories as subsequent steps
            for step_idx, mem in enumerate(related[:5], start=2):
                steps.append({
                    "memory_id": mem["id"],
                    "title": mem["title"],
                    "type": mem["type"],
                    "step": step_idx,
                })

            # Calculate value based on effectiveness
            total_effectiveness = sum(
                mem.get("effectiveness", 0.5)
                for mem in [start_memory] + related[:5]
            )
            avg_effectiveness = total_effectiveness / len(steps)

            paths.append(LearningPath(
                path_id=f"path_{idx + 1}",
                topic=topic,
                steps=steps,
                total_memories=len(steps),
                estimated_value=avg_effectiveness,
            ))

        logger.info(f"Recommended {len(paths)} learning paths")
        return paths

    except Exception as e:
        logger.error(f"Error recommending learning paths: {e}")
        return []


async def identify_knowledge_gaps(
    backend: GraphBackend,
    project: Optional[str] = None,
    min_gap_severity: str = "low",
) -> List[KnowledgeGap]:
    """
    Identify knowledge gaps in the memory graph.

    Looks for:
    - Problems without solutions
    - Sparse areas of the graph
    - Technologies mentioned but not documented

    Args:
        backend: Database backend
        project: Optional project filter
        min_gap_severity: Minimum severity ("low", "medium", "high")

    Returns:
        List of identified knowledge gaps

    Example:
        >>> gaps = await identify_knowledge_gaps(backend, project="my-app")
        >>> for gap in gaps:
        ...     print(f"{gap.severity.upper()}: {gap.topic}")
    """
    logger.info(f"Identifying knowledge gaps for project: {project}")

    gaps = []

    # Find problems without solutions
    unsolved_query = """
    MATCH (p:Memory {type: 'problem'})
    WHERE NOT EXISTS {
        MATCH (p)<-[:SOLVES|ADDRESSES]-(:Memory)
    }
    """

    if project:
        unsolved_query += """
        AND (p.context CONTAINS $project)
        """

    unsolved_query += """
    RETURN p.id as id, p.title as title, p.tags as tags,
           p.created_at as created_at
    ORDER BY p.created_at DESC
    LIMIT 10
    """

    try:
        params = {"project": project} if project else {}
        results = await backend.execute_query(unsolved_query, params)

        for record in results:
            age_days = (datetime.now() - datetime.fromisoformat(record["created_at"])).days

            # Severity based on age
            if age_days > 30:
                severity = "high"
            elif age_days > 7:
                severity = "medium"
            else:
                severity = "low"

            gaps.append(KnowledgeGap(
                gap_id=record["id"],
                topic=record["title"],
                description=f"Unsolved problem ({age_days} days old)",
                severity=severity,
                related_memories=0,
                suggestions=["Create a solution memory", "Link to existing solutions"],
            ))

    except Exception as e:
        logger.error(f"Error finding unsolved problems: {e}")

    # Find sparse entities (mentioned but no dedicated memories)
    sparse_query = """
    MATCH (e:Entity)<-[:MENTIONS]-(m:Memory)
    WITH e, count(m) as mention_count
    WHERE mention_count <= 2
      AND mention_count > 0
    RETURN e.text as entity, e.entity_type as type, mention_count
    LIMIT 10
    """

    try:
        results = await backend.execute_query(sparse_query, {})

        for record in results:
            gaps.append(KnowledgeGap(
                gap_id=f"sparse_{record['entity']}",
                topic=record["entity"],
                description=f"Technology/concept mentioned only {record['mention_count']} time(s)",
                severity="low",
                related_memories=record["mention_count"],
                suggestions=[f"Create documentation for {record['entity']}", "Add code patterns"],
            ))

    except Exception as e:
        logger.error(f"Error finding sparse entities: {e}")

    # Filter by severity
    severity_levels = {"low": 0, "medium": 1, "high": 2}
    threshold = severity_levels.get(min_gap_severity, 1)

    filtered_gaps = [
        gap for gap in gaps
        if severity_levels.get(gap.severity, 0) >= threshold
    ]

    logger.info(f"Identified {len(filtered_gaps)} knowledge gaps")
    return filtered_gaps


async def track_memory_roi(
    backend: GraphBackend,
    memory_id: str,
) -> Optional[MemoryROI]:
    """
    Track return on investment for a memory.

    Calculates value based on:
    - How often accessed
    - Success rate when used
    - Time since creation

    Args:
        backend: Database backend
        memory_id: Memory to track

    Returns:
        MemoryROI metrics, or None if not found

    Example:
        >>> roi = await track_memory_roi(backend, "solution_789")
        >>> print(f"ROI: {roi.value_score:.2f} (used {roi.times_accessed} times)")
    """
    logger.info(f"Tracking ROI for memory {memory_id}")

    roi_query = """
    MATCH (m:Memory {id: $memory_id})
    OPTIONAL MATCH (m)-[:RESULTED_IN]->(o:Outcome)
    RETURN m.id as id, m.title as title, m.created_at as created_at,
           m.usage_count as usage_count, m.last_accessed as last_accessed,
           count(o) as total_outcomes,
           sum(CASE WHEN o.success THEN 1 ELSE 0 END) as successful_outcomes
    """

    try:
        result = await backend.execute_query(roi_query, {"memory_id": memory_id})

        if not result:
            return None

        record = result[0]
        usage_count = record.get("usage_count", 0)
        total_outcomes = record.get("total_outcomes", 0)
        successful_outcomes = record.get("successful_outcomes", 0)

        success_rate = (
            successful_outcomes / total_outcomes
            if total_outcomes > 0 else 0.0
        )

        # Value score combines usage and success
        # High usage + high success = high value
        usage_score = min(usage_count / 10.0, 1.0)  # Cap at 10 uses
        value_score = (usage_score * 0.5) + (success_rate * 0.5)

        return MemoryROI(
            memory_id=record["id"],
            title=record["title"],
            creation_date=datetime.fromisoformat(record["created_at"]),
            times_accessed=usage_count,
            times_helpful=successful_outcomes,
            success_rate=success_rate,
            value_score=value_score,
            last_used=(
                datetime.fromisoformat(record["last_accessed"])
                if record.get("last_accessed") else None
            ),
        )

    except Exception as e:
        logger.error(f"Error tracking ROI: {e}")
        return None
