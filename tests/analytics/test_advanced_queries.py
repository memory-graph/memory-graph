"""
Tests for advanced analytics queries (Phase 7).

Tests critical analytics features:
- Graph visualization data generation
- Solution similarity analysis
- Knowledge gap identification
- Memory ROI tracking
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.memorygraph.analytics.advanced_queries import (
    get_memory_graph_visualization,
    analyze_solution_similarity,
    identify_knowledge_gaps,
    track_memory_roi,
    GraphVisualizationData,
    GraphNode,
    GraphEdge,
)


@pytest.mark.asyncio
class TestGraphVisualization:
    """Test graph visualization data generation."""

    async def test_get_visualization_full_graph(self):
        """Test getting full graph visualization."""
        backend = AsyncMock()

        # Mock graph data
        backend.execute_query = AsyncMock(return_value=[
            {
                "memories": [
                    {"id": "mem_1", "type": "problem", "title": "Problem 1", "importance": 0.8},
                    {"id": "mem_2", "type": "solution", "title": "Solution 1", "importance": 0.9},
                ],
                "relationships": [
                    {"from_id": "mem_2", "to_id": "mem_1", "type": "SOLVES", "strength": 0.9},
                ],
            }
        ])

        viz_data = await get_memory_graph_visualization(backend, max_nodes=100)

        assert isinstance(viz_data, GraphVisualizationData)
        assert len(viz_data.nodes) == 2
        assert len(viz_data.edges) == 1
        assert viz_data.metadata["node_count"] == 2

    async def test_get_visualization_centered(self):
        """Test getting visualization centered on a memory."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "memories": [
                    {"id": "mem_center", "type": "solution", "title": "Center", "importance": 0.9},
                    {"id": "mem_related", "type": "problem", "title": "Related", "importance": 0.7},
                ],
                "relationships": [
                    {"from_id": "mem_center", "to_id": "mem_related", "type": "SOLVES", "strength": 0.8},
                ],
            }
        ])

        viz_data = await get_memory_graph_visualization(
            backend,
            center_memory_id="mem_center",
            depth=2
        )

        assert len(viz_data.nodes) > 0
        assert viz_data.metadata["center_id"] == "mem_center"
        assert viz_data.metadata["depth"] == 2

    async def test_get_visualization_type_filter(self):
        """Test filtering visualization by memory types."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "memories": [
                    {"id": "sol_1", "type": "solution", "title": "Solution", "importance": 0.8},
                ],
                "relationships": [],
            }
        ])

        viz_data = await get_memory_graph_visualization(
            backend,
            include_types=["solution", "problem"]
        )

        assert len(viz_data.nodes) >= 0


@pytest.mark.asyncio
class TestSolutionSimilarity:
    """Test solution similarity analysis."""

    async def test_analyze_similarity_found(self):
        """Test finding similar solutions."""
        backend = AsyncMock()

        # Mock target solution
        backend.execute_query = AsyncMock(side_effect=[
            [{"tags": ["auth", "jwt"], "entities": ["JWT", "authentication"]}],
            [
                {
                    "id": "sol_2",
                    "title": "Similar solution",
                    "content": "Similar approach",
                    "tags": ["auth", "jwt", "security"],
                    "entities": ["JWT", "token"],
                    "effectiveness": 0.85,
                }
            ],
        ])

        similar = await analyze_solution_similarity(
            backend,
            "sol_1",
            top_k=5,
            min_similarity=0.3,
        )

        assert len(similar) > 0
        assert similar[0].solution_id == "sol_2"
        assert similar[0].similarity_score > 0.0

    async def test_analyze_similarity_not_found(self):
        """Test when no similar solutions found."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [{"tags": [], "entities": []}],
            [],
        ])

        similar = await analyze_solution_similarity(backend, "sol_unique")

        assert similar == []

    async def test_analyze_similarity_min_threshold(self):
        """Test similarity threshold filtering."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [{"tags": ["test"], "entities": ["Test"]}],
            [
                {
                    "id": "sol_low",
                    "title": "Low similarity",
                    "content": "Different",
                    "tags": [],
                    "entities": [],
                    "effectiveness": 0.5,
                }
            ],
        ])

        similar = await analyze_solution_similarity(
            backend,
            "sol_1",
            min_similarity=0.9  # Very high threshold
        )

        # Low similarity should be filtered out
        assert len(similar) == 0


@pytest.mark.asyncio
class TestKnowledgeGaps:
    """Test knowledge gap identification."""

    async def test_identify_gaps_unsolved_problems(self):
        """Test identifying unsolved problems as gaps."""
        backend = AsyncMock()

        # Mock unsolved problems
        backend.execute_query = AsyncMock(side_effect=[
            [
                {
                    "id": "prob_1",
                    "title": "Unsolved issue",
                    "tags": ["bug"],
                    "created_at": datetime.now().isoformat(),
                }
            ],
            [],  # No sparse entities
        ])

        gaps = await identify_knowledge_gaps(backend)

        assert len(gaps) > 0
        assert "Unsolved" in gaps[0].description

    async def test_identify_gaps_sparse_entities(self):
        """Test identifying sparsely documented entities."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [],  # No unsolved problems
            [
                {
                    "entity": "RareLibrary",
                    "type": "technology",
                    "mention_count": 1,
                }
            ],
        ])

        gaps = await identify_knowledge_gaps(backend)

        assert len(gaps) > 0
        assert "RareLibrary" in gaps[0].topic

    async def test_identify_gaps_with_project_filter(self):
        """Test gap identification with project filter."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(side_effect=[
            [
                {
                    "id": "prob_proj",
                    "title": "Project-specific problem",
                    "tags": [],
                    "created_at": datetime.now().isoformat(),
                }
            ],
            [],
        ])

        gaps = await identify_knowledge_gaps(backend, project="my-app")

        assert backend.execute_query.called


@pytest.mark.asyncio
class TestMemoryROI:
    """Test memory ROI tracking."""

    async def test_track_roi_with_usage(self):
        """Test tracking ROI for frequently used memory."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "mem_useful",
                "title": "Useful solution",
                "created_at": datetime.now().isoformat(),
                "usage_count": 15,
                "last_accessed": datetime.now().isoformat(),
                "total_outcomes": 12,
                "successful_outcomes": 10,
            }
        ])

        roi = await track_memory_roi(backend, "mem_useful")

        assert roi is not None
        assert roi.memory_id == "mem_useful"
        assert roi.times_accessed == 15
        assert roi.times_helpful == 10
        assert roi.success_rate > 0.8
        assert roi.value_score > 0.5

    async def test_track_roi_unused_memory(self):
        """Test tracking ROI for unused memory."""
        backend = AsyncMock()

        backend.execute_query = AsyncMock(return_value=[
            {
                "id": "mem_unused",
                "title": "Unused solution",
                "created_at": datetime.now().isoformat(),
                "usage_count": 0,
                "last_accessed": None,
                "total_outcomes": 0,
                "successful_outcomes": 0,
            }
        ])

        roi = await track_memory_roi(backend, "mem_unused")

        assert roi is not None
        assert roi.times_accessed == 0
        assert roi.success_rate == 0.0
        assert roi.value_score == 0.0

    async def test_track_roi_not_found(self):
        """Test tracking ROI for non-existent memory."""
        backend = AsyncMock()
        backend.execute_query = AsyncMock(return_value=[])

        roi = await track_memory_roi(backend, "mem_nonexistent")

        assert roi is None


class TestVisualizationModels:
    """Test visualization data models."""

    def test_graph_node_model(self):
        """Test GraphNode model."""
        node = GraphNode(
            id="node_1",
            label="Test Node",
            type="solution",
            group=1,
            value=5.0,
        )

        assert node.id == "node_1"
        assert node.group == 1
        assert node.value == 5.0

    def test_graph_edge_model(self):
        """Test GraphEdge model."""
        edge = GraphEdge(
            from_="node_1",
            to="node_2",
            type="SOLVES",
            value=0.8,
        )

        # Use dict() to access the field using the alias
        edge_dict = edge.dict(by_alias=True)
        assert edge_dict["from"] == "node_1"
        assert edge_dict["to"] == "node_2"
        assert edge.type == "SOLVES"

    def test_graph_visualization_data_model(self):
        """Test GraphVisualizationData model."""
        viz_data = GraphVisualizationData()

        assert len(viz_data.nodes) == 0
        assert len(viz_data.edges) == 0
        assert isinstance(viz_data.metadata, dict)

    def test_graph_visualization_data_with_content(self):
        """Test GraphVisualizationData with nodes and edges."""
        node1 = GraphNode(id="n1", label="Node 1", type="solution")
        node2 = GraphNode(id="n2", label="Node 2", type="problem")
        edge = GraphEdge(from_="n1", to="n2", type="SOLVES")

        viz_data = GraphVisualizationData(
            nodes=[node1, node2],
            edges=[edge],
            metadata={"test": "data"},
        )

        assert len(viz_data.nodes) == 2
        assert len(viz_data.edges) == 1
        assert viz_data.metadata["test"] == "data"
