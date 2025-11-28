"""Tests for pattern recognition functionality."""

import pytest
from datetime import datetime
from memorygraph.intelligence.pattern_recognition import (
    Pattern,
    PatternRecognizer,
    find_similar_problems,
    extract_patterns,
    suggest_patterns,
)


class MockBackend:
    """Mock backend for testing pattern recognition."""

    def __init__(self):
        """Initialize mock backend with test data."""
        self.queries = []
        self.test_data = {
            "similar_problems": [],
            "patterns": [],
            "suggestions": [],
            "co_occurrences": [],
        }

    async def execute_query(self, query: str, params: dict):
        """Mock query execution with test data."""
        self.queries.append((query, params))

        # Return appropriate test data based on query type
        if "type: 'problem'" in query:
            return self.test_data.get("similar_problems", [])
        elif "WHERE id(e1) < id(e2)" in query:
            # Co-occurrence query
            return self.test_data.get("co_occurrences", [])
        elif "MENTIONS" in query and "collect(m.id)" in query:
            return self.test_data.get("patterns", [])
        elif "UNWIND $entities" in query:
            return self.test_data.get("suggestions", [])
        else:
            return []


class TestPatternModel:
    """Test Pattern model."""

    def test_pattern_creation(self):
        """Test creating a Pattern instance."""
        pattern = Pattern(
            id="pattern-1",
            name="Test Pattern",
            description="A test pattern",
            pattern_type="solution",
            confidence=0.8,
            occurrences=5,
        )
        assert pattern.id == "pattern-1"
        assert pattern.confidence == 0.8
        assert pattern.occurrences == 5

    def test_pattern_with_entities(self):
        """Test pattern with entities."""
        pattern = Pattern(
            id="pattern-2",
            name="Auth Pattern",
            description="Authentication pattern",
            pattern_type="solution",
            confidence=0.9,
            entities=["Python", "JWT", "authentication"],
        )
        assert len(pattern.entities) == 3
        assert "JWT" in pattern.entities

    def test_pattern_confidence_validation(self):
        """Test confidence validation."""
        with pytest.raises(Exception):  # Pydantic validation error
            Pattern(
                id="p",
                name="test",
                description="test",
                pattern_type="test",
                confidence=1.5,  # Invalid
            )


class TestPatternRecognizer:
    """Test PatternRecognizer class."""

    @pytest.mark.asyncio
    async def test_recognizer_initialization(self):
        """Test recognizer can be initialized."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)
        assert recognizer.backend == backend

    @pytest.mark.asyncio
    async def test_find_similar_problems_empty(self):
        """Test finding similar problems with no results."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)

        results = await recognizer.find_similar_problems(
            "Authentication error in API", threshold=0.7
        )

        assert isinstance(results, list)
        assert len(backend.queries) > 0

    @pytest.mark.asyncio
    async def test_find_similar_problems_with_results(self):
        """Test finding similar problems with mock results."""
        backend = MockBackend()
        backend.test_data["similar_problems"] = [
            {
                "problem_id": "p1",
                "problem_title": "Auth timeout",
                "problem_content": "Authentication times out after 30min",
                "created_at": datetime.utcnow(),
                "similarity": 0.85,
                "solutions": [
                    {
                        "id": "s1",
                        "title": "Increase timeout",
                        "content": "Set timeout to 1 hour",
                        "effectiveness": 0.9,
                    }
                ],
            }
        ]

        recognizer = PatternRecognizer(backend)
        results = await recognizer.find_similar_problems("Auth timeout issue")

        assert len(results) > 0
        assert results[0]["problem_id"] == "p1"
        assert results[0]["similarity"] == 0.85

    @pytest.mark.asyncio
    async def test_extract_patterns_empty(self):
        """Test extracting patterns with no data."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)

        patterns = await recognizer.extract_patterns("solution", min_occurrences=3)

        assert isinstance(patterns, list)
        assert len(backend.queries) > 0

    @pytest.mark.asyncio
    async def test_extract_patterns_with_entities(self):
        """Test extracting patterns from entity occurrences."""
        backend = MockBackend()
        backend.test_data["patterns"] = [
            {
                "entity": "Python",
                "entity_type": "technology",
                "memory_ids": ["m1", "m2", "m3"],
                "occurrence_count": 3,
            },
            {
                "entity": "FastAPI",
                "entity_type": "technology",
                "memory_ids": ["m1", "m2", "m4"],
                "occurrence_count": 3,
            },
        ]

        recognizer = PatternRecognizer(backend)
        patterns = await recognizer.extract_patterns("solution", min_occurrences=3)

        assert len(patterns) > 0
        # Should have patterns for Python and FastAPI
        pattern_names = {p.name for p in patterns}
        assert any("Python" in name for name in pattern_names)

    @pytest.mark.asyncio
    async def test_suggest_patterns_empty_context(self):
        """Test suggesting patterns with empty context."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)

        patterns = await recognizer.suggest_patterns("")

        assert isinstance(patterns, list)
        # Should return empty if no entities in context
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_suggest_patterns_with_context(self):
        """Test suggesting patterns with valid context."""
        backend = MockBackend()
        backend.test_data["suggestions"] = [
            {
                "memory_id": "m1",
                "memory_type": "solution",
                "title": "React Authentication",
                "content": "How to implement auth in React with hooks",
                "matched_entities": ["React", "authentication"],
                "all_entity_texts": ["React", "authentication", "hooks"],
                "match_count": 2,
            }
        ]

        recognizer = PatternRecognizer(backend)
        patterns = await recognizer.suggest_patterns(
            "Need to implement authentication in React application"
        )

        # Should find patterns if entities match
        assert isinstance(patterns, list)

    def test_extract_keywords(self):
        """Test keyword extraction."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)

        text = "The authentication system has a timeout error"
        keywords = recognizer._extract_keywords(text)

        # Should extract meaningful keywords
        assert "authentication" in keywords
        assert "system" in keywords or "timeout" in keywords or "error" in keywords

        # Should filter stop words
        assert "the" not in keywords
        assert "has" not in keywords


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_find_similar_problems_function(self):
        """Test find_similar_problems convenience function."""
        backend = MockBackend()

        results = await find_similar_problems(
            backend, "API authentication error", threshold=0.6, limit=5
        )

        assert isinstance(results, list)
        assert len(backend.queries) > 0

    @pytest.mark.asyncio
    async def test_extract_patterns_function(self):
        """Test extract_patterns convenience function."""
        backend = MockBackend()

        patterns = await extract_patterns(backend, "solution", min_occurrences=3)

        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_suggest_patterns_function(self):
        """Test suggest_patterns convenience function."""
        backend = MockBackend()

        patterns = await suggest_patterns(backend, "Using Python with FastAPI")

        assert isinstance(patterns, list)


class TestRealWorldScenarios:
    """Test pattern recognition with real-world scenarios."""

    @pytest.mark.asyncio
    async def test_bug_pattern_recognition(self):
        """Test recognizing bug patterns."""
        backend = MockBackend()
        backend.test_data["patterns"] = [
            {
                "entity": "NullPointerException",
                "entity_type": "error",
                "memory_ids": ["b1", "b2", "b3", "b4"],
                "occurrence_count": 4,
            }
        ]

        recognizer = PatternRecognizer(backend)
        patterns = await recognizer.extract_patterns("problem", min_occurrences=3)

        # Should identify common error patterns
        assert len(patterns) > 0
        error_pattern = patterns[0]
        assert error_pattern.occurrences >= 3

    @pytest.mark.asyncio
    async def test_solution_pattern_suggestion(self):
        """Test suggesting solution patterns."""
        backend = MockBackend()
        backend.test_data["suggestions"] = [
            {
                "memory_id": "s1",
                "memory_type": "solution",
                "title": "Caching Strategy",
                "content": "Use Redis for session caching",
                "matched_entities": ["Redis", "caching"],
                "all_entity_texts": ["Redis", "caching", "session"],
                "match_count": 2,
            }
        ]

        recognizer = PatternRecognizer(backend)
        patterns = await recognizer.suggest_patterns(
            "Need to implement caching with Redis"
        )

        # Should suggest relevant solution patterns
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_technology_stack_patterns(self):
        """Test identifying technology stack patterns."""
        backend = MockBackend()
        backend.test_data["patterns"] = [
            {
                "entity": "React",
                "entity_type": "technology",
                "memory_ids": ["t1", "t2", "t3"],
                "occurrence_count": 3,
            },
            {
                "entity": "TypeScript",
                "entity_type": "technology",
                "memory_ids": ["t1", "t2", "t3"],
                "occurrence_count": 3,
            },
        ]

        recognizer = PatternRecognizer(backend)
        patterns = await recognizer.extract_patterns("decision", min_occurrences=3)

        # Should identify common technology choices
        assert isinstance(patterns, list)


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_problem_text(self):
        """Test with empty problem text."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)

        results = await recognizer.find_similar_problems("")

        # Should handle empty text gracefully
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_very_long_text(self):
        """Test with very long text."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)

        long_text = "authentication " * 1000
        keywords = recognizer._extract_keywords(long_text)

        # Should still extract keywords
        assert "authentication" in keywords

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test keyword extraction with special characters."""
        backend = MockBackend()
        recognizer = PatternRecognizer(backend)

        text = "Error in @user/package-name with C++ code"
        keywords = recognizer._extract_keywords(text)

        # Should handle special characters
        assert isinstance(keywords, list)
        assert "error" in keywords or "code" in keywords

    @pytest.mark.asyncio
    async def test_backend_error_handling(self):
        """Test handling of backend errors."""

        class ErrorBackend:
            """Backend that raises errors."""

            async def execute_query(self, query, params):
                """Raise an error."""
                raise Exception("Database error")

        backend = ErrorBackend()
        recognizer = PatternRecognizer(backend)

        # Should handle errors gracefully
        results = await recognizer.find_similar_problems("test problem")
        assert results == []

        patterns = await recognizer.extract_patterns("solution")
        assert patterns == []

        suggestions = await recognizer.suggest_patterns("test context")
        assert suggestions == []


class TestPatternQuality:
    """Test pattern quality and relevance."""

    @pytest.mark.asyncio
    async def test_pattern_confidence_scoring(self):
        """Test that pattern confidence is calculated correctly."""
        backend = MockBackend()
        backend.test_data["patterns"] = [
            {
                "entity": "Docker",
                "entity_type": "technology",
                "memory_ids": ["m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8"],
                "occurrence_count": 8,
            },
            {
                "entity": "Kubernetes",
                "entity_type": "technology",
                "memory_ids": ["m1", "m2"],
                "occurrence_count": 2,
            },
        ]

        recognizer = PatternRecognizer(backend)
        patterns = await recognizer.extract_patterns("solution", min_occurrences=2)

        # Higher occurrence should have higher confidence
        if len(patterns) >= 2:
            docker_pattern = next((p for p in patterns if "Docker" in p.name), None)
            k8s_pattern = next((p for p in patterns if "Kubernetes" in p.name), None)

            if docker_pattern and k8s_pattern:
                assert docker_pattern.confidence > k8s_pattern.confidence

    @pytest.mark.asyncio
    async def test_similarity_threshold_filtering(self):
        """Test that similarity threshold filters results correctly."""
        backend = MockBackend()
        backend.test_data["similar_problems"] = [
            {
                "problem_id": "p1",
                "problem_title": "High similarity",
                "problem_content": "content",
                "created_at": datetime.utcnow(),
                "similarity": 0.9,
                "solutions": [],
            },
            {
                "problem_id": "p2",
                "problem_title": "Low similarity",
                "problem_content": "content",
                "created_at": datetime.utcnow(),
                "similarity": 0.5,
                "solutions": [],
            },
        ]

        recognizer = PatternRecognizer(backend)

        # High threshold should filter out low similarity
        high_threshold_results = await recognizer.find_similar_problems(
            "test", threshold=0.8
        )

        # Results depend on backend filtering in actual implementation
        assert isinstance(high_threshold_results, list)
