"""
Advanced Analytics for Claude Code Memory Server.

Provides advanced graph analytics and visualization capabilities:
- Graph visualization data export
- Solution similarity matching
- Learning path recommendations
- Knowledge gap identification
- Memory effectiveness tracking (ROI)

Phase 7 Implementation - Advanced Analytics
"""

from .advanced_queries import (
    get_memory_graph_visualization,
    analyze_solution_similarity,
    predict_solution_effectiveness,
    recommend_learning_paths,
    identify_knowledge_gaps,
    track_memory_roi,
    GraphVisualizationData,
    SimilarSolution,
    LearningPath,
    KnowledgeGap,
    MemoryROI,
)

__all__ = [
    # Visualization
    "get_memory_graph_visualization",
    "GraphVisualizationData",
    # Similarity
    "analyze_solution_similarity",
    "SimilarSolution",
    # Prediction
    "predict_solution_effectiveness",
    # Learning
    "recommend_learning_paths",
    "LearningPath",
    # Gap analysis
    "identify_knowledge_gaps",
    "KnowledgeGap",
    # ROI tracking
    "track_memory_roi",
    "MemoryROI",
]
