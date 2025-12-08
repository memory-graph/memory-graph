"""
Comprehensive tests for Proactive Tool handlers.

Tests all 11 proactive tools by mocking return values and focusing on handler logic.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from memorygraph.proactive_tools import PROACTIVE_TOOL_HANDLERS
from memorygraph.backends.base import GraphBackend


@pytest.fixture
def backend():
    """Create a mock backend."""
    return AsyncMock(spec=GraphBackend)


class TestGetSessionBriefing:
    """Tests for get_session_briefing handler."""

    @pytest.mark.asyncio
    async def test_get_session_briefing_success(self, backend):
        """Test successful session briefing generation."""
        mock_briefing = MagicMock()
        mock_briefing.format_as_text.return_value = "Test briefing output"

        with patch("memorygraph.proactive_tools.generate_session_briefing") as mock_gen:
            mock_gen.return_value = mock_briefing

            handler = PROACTIVE_TOOL_HANDLERS["get_session_briefing"]
            result = await handler(backend, {
                "project_dir": "/test/path",
                "recency_days": 7,
                "verbosity": "standard"
            })

            assert result is not None
            assert not result.isError
            assert "Test briefing output" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_session_briefing_no_project(self, backend):
        """Test when project is not found."""
        with patch("memorygraph.proactive_tools.generate_session_briefing") as mock_gen:
            mock_gen.return_value = None

            handler = PROACTIVE_TOOL_HANDLERS["get_session_briefing"]
            result = await handler(backend, {
                "project_dir": "/nonexistent"
            })

            assert result is not None
            assert result.isError
            assert "Could not detect project" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_session_briefing_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.generate_session_briefing") as mock_gen:
            mock_gen.side_effect = Exception("Database error")

            handler = PROACTIVE_TOOL_HANDLERS["get_session_briefing"]
            result = await handler(backend, {
                "project_dir": "/test"
            })

            assert result is not None
            assert result.isError
            assert "Error generating session briefing" in result.content[0].text


class TestGetSuggestions:
    """Tests for get_suggestions handler."""

    @pytest.mark.asyncio
    async def test_get_suggestions_with_results(self, backend):
        """Test getting suggestions with results."""
        mock_suggestion = MagicMock()
        mock_suggestion.title = "Use cached results"
        mock_suggestion.suggestion_type = "optimization"
        mock_suggestion.relevance_score = 0.85
        mock_suggestion.reason = "Similar pattern used before"
        mock_suggestion.description = "Consider caching these results"
        mock_suggestion.effectiveness = 0.92
        mock_suggestion.tags = ["caching", "performance"]

        with patch("memorygraph.proactive_tools.predict_needs") as mock_predict:
            mock_predict.return_value = [mock_suggestion]

            handler = PROACTIVE_TOOL_HANDLERS["get_suggestions"]
            result = await handler(backend, {
                "current_context": "Working on database queries",
                "max_suggestions": 5,
                "min_relevance": 0.3
            })

            assert result is not None
            assert not result.isError
            assert "Use cached results" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_suggestions_no_results(self, backend):
        """Test when no suggestions found."""
        with patch("memorygraph.proactive_tools.predict_needs") as mock_predict:
            mock_predict.return_value = []

            handler = PROACTIVE_TOOL_HANDLERS["get_suggestions"]
            result = await handler(backend, {
                "current_context": "New task"
            })

            assert result is not None
            assert "No relevant suggestions found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_suggestions_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.predict_needs") as mock_predict:
            mock_predict.side_effect = RuntimeError("Analysis failed")

            handler = PROACTIVE_TOOL_HANDLERS["get_suggestions"]
            result = await handler(backend, {
                "current_context": "test"
            })

            assert result is not None
            assert result.isError


class TestCheckForIssues:
    """Tests for check_for_issues handler."""

    @pytest.mark.asyncio
    async def test_check_for_issues_found(self, backend):
        """Test when issues are found."""
        mock_warning = MagicMock()
        mock_warning.title = "Deprecated API"
        mock_warning.description = "This API is deprecated"
        mock_warning.severity = "high"
        mock_warning.mitigation = "Use new API v2"
        mock_warning.evidence = ["mem_1", "mem_2"]

        with patch("memorygraph.proactive_tools.warn_potential_issues") as mock_warn:
            mock_warn.return_value = [mock_warning]

            handler = PROACTIVE_TOOL_HANDLERS["check_for_issues"]
            result = await handler(backend, {
                "current_context": "Using old API",
                "severity_threshold": "medium"
            })

            assert result is not None
            assert not result.isError
            assert "Deprecated API" in result.content[0].text
            assert "HIGH" in result.content[0].text

    @pytest.mark.asyncio
    async def test_check_for_issues_none_found(self, backend):
        """Test when no issues found."""
        with patch("memorygraph.proactive_tools.warn_potential_issues") as mock_warn:
            mock_warn.return_value = []

            handler = PROACTIVE_TOOL_HANDLERS["check_for_issues"]
            result = await handler(backend, {
                "current_context": "Clean code"
            })

            assert result is not None
            assert "No potential issues detected" in result.content[0].text

    @pytest.mark.asyncio
    async def test_check_for_issues_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.warn_potential_issues") as mock_warn:
            mock_warn.side_effect = ValueError("Invalid context")

            handler = PROACTIVE_TOOL_HANDLERS["check_for_issues"]
            result = await handler(backend, {
                "current_context": "test"
            })

            assert result is not None
            assert result.isError


class TestSuggestRelatedMemories:
    """Tests for suggest_related_memories handler."""

    @pytest.mark.asyncio
    async def test_suggest_related_memories_success(self, backend):
        """Test suggesting related memories."""
        mock_suggestion = MagicMock()
        mock_suggestion.title = "Related solution"
        mock_suggestion.description = "This might be useful"
        mock_suggestion.relevance_score = 0.75
        mock_suggestion.reason = "Same technology stack"

        with patch("memorygraph.proactive_tools.suggest_related_context") as mock_suggest:
            mock_suggest.return_value = [mock_suggestion]

            handler = PROACTIVE_TOOL_HANDLERS["suggest_related_memories"]
            result = await handler(backend, {
                "memory_id": "mem_123",
                "max_suggestions": 5
            })

            assert result is not None
            assert "You Might Also Want to Know" in result.content[0].text
            assert "Related solution" in result.content[0].text

    @pytest.mark.asyncio
    async def test_suggest_related_memories_none_found(self, backend):
        """Test when no related memories found."""
        with patch("memorygraph.proactive_tools.suggest_related_context") as mock_suggest:
            mock_suggest.return_value = []

            handler = PROACTIVE_TOOL_HANDLERS["suggest_related_memories"]
            result = await handler(backend, {
                "memory_id": "mem_123"
            })

            assert result is not None
            assert "No related memories found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_suggest_related_memories_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.suggest_related_context") as mock_suggest:
            mock_suggest.side_effect = Exception("Lookup failed")

            handler = PROACTIVE_TOOL_HANDLERS["suggest_related_memories"]
            result = await handler(backend, {
                "memory_id": "mem_123"
            })

            assert result is not None
            assert result.isError


class TestRecordOutcome:
    """Tests for record_outcome handler."""

    @pytest.mark.asyncio
    async def test_record_outcome_success(self, backend):
        """Test recording successful outcome."""
        with patch("memorygraph.proactive_tools.record_outcome") as mock_record:
            mock_record.return_value = True

            handler = PROACTIVE_TOOL_HANDLERS["record_outcome"]
            result = await handler(backend, {
                "memory_id": "mem_123",
                "outcome_description": "Solution worked perfectly",
                "success": True,
                "impact": 0.9
            })

            assert result is not None
            assert not result.isError
            assert "successful" in result.content[0].text

    @pytest.mark.asyncio
    async def test_record_outcome_failure(self, backend):
        """Test recording unsuccessful outcome."""
        with patch("memorygraph.proactive_tools.record_outcome") as mock_record:
            mock_record.return_value = True

            handler = PROACTIVE_TOOL_HANDLERS["record_outcome"]
            result = await handler(backend, {
                "memory_id": "mem_456",
                "outcome_description": "Solution did not work",
                "success": False,
                "context": {"reason": "version mismatch"}
            })

            assert result is not None
            assert not result.isError
            assert "unsuccessful" in result.content[0].text

    @pytest.mark.asyncio
    async def test_record_outcome_failed_to_record(self, backend):
        """Test when recording fails."""
        with patch("memorygraph.proactive_tools.record_outcome") as mock_record:
            mock_record.return_value = False

            handler = PROACTIVE_TOOL_HANDLERS["record_outcome"]
            result = await handler(backend, {
                "memory_id": "mem_123",
                "outcome_description": "Test",
                "success": True
            })

            assert result is not None
            assert result.isError
            assert "Failed to record outcome" in result.content[0].text

    @pytest.mark.asyncio
    async def test_record_outcome_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.record_outcome") as mock_record:
            mock_record.side_effect = Exception("Database write failed")

            handler = PROACTIVE_TOOL_HANDLERS["record_outcome"]
            result = await handler(backend, {
                "memory_id": "mem_123",
                "outcome_description": "Test",
                "success": True
            })

            assert result is not None
            assert result.isError


class TestGetGraphVisualization:
    """Tests for get_graph_visualization handler."""

    @pytest.mark.asyncio
    async def test_get_graph_visualization_success(self, backend):
        """Test graph visualization generation."""
        mock_viz = MagicMock()
        mock_viz.model_dump.return_value = {
            "nodes": [{"id": "mem_1"}],
            "edges": [{"source": "mem_1", "target": "mem_2"}]
        }

        with patch("memorygraph.proactive_tools.get_memory_graph_visualization") as mock_viz_func:
            mock_viz_func.return_value = mock_viz

            handler = PROACTIVE_TOOL_HANDLERS["get_graph_visualization"]
            result = await handler(backend, {
                "center_memory_id": "mem_1",
                "depth": 2,
                "max_nodes": 100
            })

            assert result is not None
            assert not result.isError
            assert "mem_1" in result.content[0].text

    @pytest.mark.asyncio
    async def test_get_graph_visualization_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.get_memory_graph_visualization") as mock_viz_func:
            mock_viz_func.side_effect = Exception("Visualization failed")

            handler = PROACTIVE_TOOL_HANDLERS["get_graph_visualization"]
            result = await handler(backend, {})

            assert result is not None
            assert result.isError


class TestFindSimilarSolutions:
    """Tests for find_similar_solutions handler."""

    @pytest.mark.asyncio
    async def test_find_similar_solutions_success(self, backend):
        """Test finding similar solutions."""
        mock_similar = MagicMock()
        mock_similar.title = "Similar Solution"
        mock_similar.description = "Also solves this problem"
        mock_similar.similarity_score = 0.88
        mock_similar.shared_entities = ["entity1", "entity2"]
        mock_similar.shared_tags = ["tag1"]
        mock_similar.effectiveness = 0.92

        with patch("memorygraph.proactive_tools.analyze_solution_similarity") as mock_analyze:
            mock_analyze.return_value = [mock_similar]

            handler = PROACTIVE_TOOL_HANDLERS["find_similar_solutions"]
            result = await handler(backend, {
                "solution_id": "sol_1",
                "top_k": 5,
                "min_similarity": 0.3
            })

            assert result is not None
            assert not result.isError
            assert "Similar Solution" in result.content[0].text

    @pytest.mark.asyncio
    async def test_find_similar_solutions_none_found(self, backend):
        """Test when no similar solutions found."""
        with patch("memorygraph.proactive_tools.analyze_solution_similarity") as mock_analyze:
            mock_analyze.return_value = []

            handler = PROACTIVE_TOOL_HANDLERS["find_similar_solutions"]
            result = await handler(backend, {
                "solution_id": "sol_1"
            })

            assert result is not None
            assert "No similar solutions found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_find_similar_solutions_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.analyze_solution_similarity") as mock_analyze:
            mock_analyze.side_effect = ValueError("Invalid solution ID")

            handler = PROACTIVE_TOOL_HANDLERS["find_similar_solutions"]
            result = await handler(backend, {
                "solution_id": "invalid"
            })

            assert result is not None
            assert result.isError


class TestPredictSolutionEffectiveness:
    """Tests for predict_solution_effectiveness handler."""

    @pytest.mark.asyncio
    async def test_predict_effectiveness_success(self, backend):
        """Test predicting solution effectiveness."""
        with patch("memorygraph.proactive_tools.predict_solution_effectiveness") as mock_predict:
            mock_predict.return_value = 0.85

            handler = PROACTIVE_TOOL_HANDLERS["predict_solution_effectiveness"]
            result = await handler(backend, {
                "problem_description": "Database slow query",
                "solution_id": "sol_123"
            })

            assert result is not None
            assert not result.isError
            assert "85" in result.content[0].text
            assert "sol_123" in result.content[0].text

    @pytest.mark.asyncio
    async def test_predict_effectiveness_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.predict_solution_effectiveness") as mock_predict:
            mock_predict.side_effect = Exception("Prediction failed")

            handler = PROACTIVE_TOOL_HANDLERS["predict_solution_effectiveness"]
            result = await handler(backend, {
                "problem_description": "test",
                "solution_id": "sol_1"
            })

            assert result is not None
            assert result.isError


class TestRecommendLearningPaths:
    """Tests for recommend_learning_paths handler."""

    @pytest.mark.asyncio
    async def test_recommend_learning_paths_success(self, backend):
        """Test recommending learning paths."""
        mock_path = MagicMock()
        mock_path.total_memories = 5
        mock_path.estimated_value = 0.85
        mock_path.steps = [
            {"step": "1", "memory_id": "mem_1", "title": "Intro to async", "type": "tutorial"},
            {"step": "2", "memory_id": "mem_2", "title": "Async patterns", "type": "code_pattern"}
        ]

        with patch("memorygraph.proactive_tools.recommend_learning_paths") as mock_recommend:
            mock_recommend.return_value = [mock_path]

            handler = PROACTIVE_TOOL_HANDLERS["recommend_learning_paths"]
            result = await handler(backend, {
                "topic": "Python async",
                "max_paths": 3
            })

            assert result is not None
            assert not result.isError
            assert "Python async" in result.content[0].text
            assert "Intro to async" in result.content[0].text

    @pytest.mark.asyncio
    async def test_recommend_learning_paths_none_found(self, backend):
        """Test when no learning paths found."""
        with patch("memorygraph.proactive_tools.recommend_learning_paths") as mock_recommend:
            mock_recommend.return_value = []

            handler = PROACTIVE_TOOL_HANDLERS["recommend_learning_paths"]
            result = await handler(backend, {
                "topic": "Unknown topic"
            })

            assert result is not None
            assert "No learning paths found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_recommend_learning_paths_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.recommend_learning_paths") as mock_recommend:
            mock_recommend.side_effect = RuntimeError("Analysis error")

            handler = PROACTIVE_TOOL_HANDLERS["recommend_learning_paths"]
            result = await handler(backend, {
                "topic": "test"
            })

            assert result is not None
            assert result.isError


class TestIdentifyKnowledgeGaps:
    """Tests for identify_knowledge_gaps handler."""

    @pytest.mark.asyncio
    async def test_identify_knowledge_gaps_found(self, backend):
        """Test when knowledge gaps are identified."""
        mock_gap = MagicMock()
        mock_gap.topic = "Error handling"
        mock_gap.severity = "high"
        mock_gap.description = "Missing error handling patterns"
        mock_gap.suggestions = ["Add try/except patterns", "Document error cases"]

        with patch("memorygraph.proactive_tools.identify_knowledge_gaps") as mock_identify:
            mock_identify.return_value = [mock_gap]

            handler = PROACTIVE_TOOL_HANDLERS["identify_knowledge_gaps"]
            result = await handler(backend, {
                "project": "test_project",
                "min_gap_severity": "medium"
            })

            assert result is not None
            assert not result.isError
            assert "Error handling" in result.content[0].text
            assert "HIGH" in result.content[0].text

    @pytest.mark.asyncio
    async def test_identify_knowledge_gaps_none_found(self, backend):
        """Test when no gaps found."""
        with patch("memorygraph.proactive_tools.identify_knowledge_gaps") as mock_identify:
            mock_identify.return_value = []

            handler = PROACTIVE_TOOL_HANDLERS["identify_knowledge_gaps"]
            result = await handler(backend, {})

            assert result is not None
            assert "No knowledge gaps identified" in result.content[0].text

    @pytest.mark.asyncio
    async def test_identify_knowledge_gaps_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.identify_knowledge_gaps") as mock_identify:
            mock_identify.side_effect = Exception("Analysis failed")

            handler = PROACTIVE_TOOL_HANDLERS["identify_knowledge_gaps"]
            result = await handler(backend, {})

            assert result is not None
            assert result.isError


class TestTrackMemoryROI:
    """Tests for track_memory_roi handler."""

    @pytest.mark.asyncio
    async def test_track_memory_roi_success(self, backend):
        """Test tracking memory ROI."""
        mock_roi = MagicMock()
        mock_roi.title = "Useful Solution"
        mock_roi.memory_id = "mem_123"
        mock_roi.creation_date = datetime.now() - timedelta(days=30)
        mock_roi.times_accessed = 15
        mock_roi.times_helpful = 12
        mock_roi.success_rate = 0.80
        mock_roi.value_score = 0.75
        mock_roi.last_used = datetime.now() - timedelta(days=2)

        with patch("memorygraph.proactive_tools.track_memory_roi") as mock_track:
            mock_track.return_value = mock_roi

            handler = PROACTIVE_TOOL_HANDLERS["track_memory_roi"]
            result = await handler(backend, {
                "memory_id": "mem_123"
            })

            assert result is not None
            assert not result.isError
            assert "Useful Solution" in result.content[0].text
            assert "15" in result.content[0].text

    @pytest.mark.asyncio
    async def test_track_memory_roi_not_found(self, backend):
        """Test when memory not found."""
        with patch("memorygraph.proactive_tools.track_memory_roi") as mock_track:
            mock_track.return_value = None

            handler = PROACTIVE_TOOL_HANDLERS["track_memory_roi"]
            result = await handler(backend, {
                "memory_id": "nonexistent"
            })

            assert result is not None
            assert result.isError
            assert "not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_track_memory_roi_error(self, backend):
        """Test error handling."""
        with patch("memorygraph.proactive_tools.track_memory_roi") as mock_track:
            mock_track.side_effect = Exception("ROI calculation failed")

            handler = PROACTIVE_TOOL_HANDLERS["track_memory_roi"]
            result = await handler(backend, {
                "memory_id": "mem_123"
            })

            assert result is not None
            assert result.isError
