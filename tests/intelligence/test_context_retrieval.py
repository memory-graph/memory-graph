"""Tests for context-aware retrieval functionality."""

import pytest
from datetime import datetime, timedelta
from memorygraph.intelligence.context_retrieval import (
    ContextRetriever,
    get_context,
    get_project_context,
    get_session_context,
)


class MockBackend:
    """Mock backend for testing context retrieval."""

    def __init__(self):
        """Initialize mock backend."""
        self.queries = []
        self.test_data = {
            "context_search": [],
            "project_summary": [],
            "session_context": [],
        }

    async def execute_query(self, query: str, params: dict):
        """Mock query execution."""
        self.queries.append((query, params))

        # Route based on query type
        if "relevance_score" in query and "entity_matches" in query:
            return self.test_data.get("context_search", [])
        elif "project_summary" in query:
            return self.test_data.get("project_summary", [])
        elif "hours: $hours_back" in query:
            return self.test_data.get("session_context", [])
        else:
            return []


class TestContextRetriever:
    """Test ContextRetriever class."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test context retriever initialization."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)
        assert retriever.backend == backend

    @pytest.mark.asyncio
    async def test_get_context_empty(self):
        """Test getting context with no results."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        result = await retriever.get_context("test query")

        assert isinstance(result, dict)
        assert "context" in result
        assert "source_memories" in result
        assert len(result["source_memories"]) == 0

    @pytest.mark.asyncio
    async def test_get_context_with_results(self):
        """Test getting context with search results."""
        backend = MockBackend()
        backend.test_data["context_search"] = [
            {
                "id": "m1",
                "title": "Authentication Guide",
                "content": "How to implement authentication in the app",
                "memory_type": "documentation",
                "tags": ["auth", "guide"],
                "created_at": datetime.now(),
                "relevance_score": 0.95,
                "entity_matches": 2,
                "keyword_matches": 3,
                "related_memories": [],
            }
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_context("authentication implementation")

        assert len(result["source_memories"]) > 0
        assert result["total_memories"] >= 1
        assert "estimated_tokens" in result
        assert len(result["context"]) > 0

    @pytest.mark.asyncio
    async def test_get_context_token_limiting(self):
        """Test that context respects token limits."""
        backend = MockBackend()
        # Create many results to test limiting
        backend.test_data["context_search"] = [
            {
                "id": f"m{i}",
                "title": f"Memory {i}",
                "content": "x" * 1000,  # Long content
                "memory_type": "note",
                "tags": [],
                "created_at": datetime.now(),
                "relevance_score": 1.0 - (i * 0.1),
                "entity_matches": 1,
                "keyword_matches": 1,
                "related_memories": [],
            }
            for i in range(10)
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_context("test", max_tokens=500)

        # Should limit based on tokens
        assert result["estimated_tokens"] <= 500

    @pytest.mark.asyncio
    async def test_get_context_with_project_filter(self):
        """Test filtering context by project."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        result = await retriever.get_context(
            "test query",
            project="my-project"
        )

        # Verify project parameter was passed
        assert len(backend.queries) > 0
        _, params = backend.queries[0]
        assert params.get("project") == "my-project"

    @pytest.mark.asyncio
    async def test_get_project_context_empty(self):
        """Test getting project context with no data."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        result = await retriever.get_project_context("test-project")

        assert isinstance(result, dict)
        assert result.get("total_memories") == 0
        assert isinstance(result.get("recent_activity", []), list)

    @pytest.mark.asyncio
    async def test_get_project_context_with_data(self):
        """Test getting project context with data."""
        backend = MockBackend()
        backend.test_data["project_summary"] = [
            {
                "project_summary": {
                    "total_memories": 10,
                    "recent_activity": [
                        {
                            "id": "m1",
                            "title": "Recent work",
                            "type": "note",
                            "created_at": datetime.now(),
                        }
                    ],
                    "decisions": [
                        {
                            "id": "d1",
                            "title": "Architecture decision",
                            "created_at": datetime.now() - timedelta(days=5),
                        }
                    ],
                    "open_problems": [
                        {
                            "id": "p1",
                            "title": "Bug in login",
                            "created_at": datetime.now() - timedelta(days=2),
                        }
                    ],
                    "solutions": [
                        {
                            "id": "s1",
                            "title": "Fixed caching issue",
                            "created_at": datetime.now() - timedelta(days=1),
                        }
                    ],
                }
            }
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_project_context("my-project")

        assert result["total_memories"] == 10
        assert len(result["recent_activity"]) > 0
        assert len(result["decisions"]) > 0
        assert len(result["open_problems"]) > 0
        assert len(result["solutions"]) > 0

    @pytest.mark.asyncio
    async def test_get_session_context_empty(self):
        """Test getting session context with no recent memories."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        result = await retriever.get_session_context()

        assert isinstance(result, dict)
        assert result.get("total_count") == 0
        assert isinstance(result.get("recent_memories"), list)

    @pytest.mark.asyncio
    async def test_get_session_context_with_data(self):
        """Test getting session context with recent memories."""
        backend = MockBackend()
        backend.test_data["session_context"] = [
            {
                "id": "m1",
                "title": "Recent work",
                "content": "Just implemented feature X",
                "memory_type": "note",
                "created_at": datetime.now() - timedelta(hours=1),
                "entities": ["React", "TypeScript"],
            },
            {
                "id": "m2",
                "title": "Bug fix",
                "content": "Fixed issue with authentication",
                "memory_type": "solution",
                "created_at": datetime.now() - timedelta(hours=5),
                "entities": ["authentication", "JWT"],
            },
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_session_context(hours_back=24, limit=10)

        assert result["total_count"] == 2
        assert len(result["recent_memories"]) == 2
        assert result["time_range_hours"] == 24
        assert len(result["active_entities"]) > 0

    def test_format_memory(self):
        """Test memory formatting."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        record = {
            "title": "Test Memory",
            "memory_type": "note",
            "content": "This is test content",
            "relevance_score": 0.85,
            "related_memories": [],
        }

        formatted = retriever._format_memory(record)

        assert "Test Memory" in formatted
        assert "note" in formatted
        assert "0.85" in formatted
        assert "test content" in formatted

    def test_format_memory_truncates_long_content(self):
        """Test that long content is truncated."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        record = {
            "title": "Long Memory",
            "memory_type": "documentation",
            "content": "x" * 1000,  # Very long content
            "relevance_score": 0.9,
            "related_memories": [],
        }

        formatted = retriever._format_memory(record)

        # Should be truncated
        assert len(formatted) < 1000
        assert "..." in formatted

    def test_estimate_tokens(self):
        """Test token estimation."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        # Simple test - ~4 chars per token
        text = "a" * 400
        tokens = retriever._estimate_tokens(text)

        assert tokens == 100  # 400/4

    def test_extract_keywords(self):
        """Test keyword extraction."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        text = "How do I implement authentication in the React application?"
        keywords = retriever._extract_keywords(text)

        # Should extract meaningful words
        assert "implement" in keywords or "authentication" in keywords
        assert "react" in keywords or "application" in keywords

        # Should filter stop words
        assert "the" not in keywords
        assert "in" not in keywords
        assert "do" not in keywords


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_get_context_function(self):
        """Test get_context convenience function."""
        backend = MockBackend()

        result = await get_context(backend, "test query")

        assert isinstance(result, dict)
        assert "context" in result

    @pytest.mark.asyncio
    async def test_get_project_context_function(self):
        """Test get_project_context convenience function."""
        backend = MockBackend()

        result = await get_project_context(backend, "test-project")

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_session_context_function(self):
        """Test get_session_context convenience function."""
        backend = MockBackend()

        result = await get_session_context(backend)

        assert isinstance(result, dict)


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_backend_error_handling(self):
        """Test handling of backend errors."""

        class ErrorBackend:
            """Backend that raises errors."""

            async def execute_query(self, query, params):
                """Raise an error."""
                raise Exception("Database error")

        backend = ErrorBackend()
        retriever = ContextRetriever(backend)

        # Should handle errors gracefully
        result = await retriever.get_context("test")
        assert "error" in result

        result = await retriever.get_project_context("test")
        assert "error" in result

        result = await retriever.get_session_context()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test with empty query."""
        backend = MockBackend()
        retriever = ContextRetriever(backend)

        result = await retriever.get_context("")

        assert isinstance(result, dict)
        assert "context" in result

    @pytest.mark.asyncio
    async def test_very_low_token_limit(self):
        """Test with very low token limit."""
        backend = MockBackend()
        backend.test_data["context_search"] = [
            {
                "id": "m1",
                "title": "Test",
                "content": "Some content",
                "memory_type": "note",
                "tags": [],
                "created_at": datetime.now(),
                "relevance_score": 1.0,
                "entity_matches": 1,
                "keyword_matches": 1,
                "related_memories": [],
            }
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_context("test", max_tokens=10)

        # Should respect even very low limits
        assert result["estimated_tokens"] <= 10


class TestRealWorldScenarios:
    """Test context retrieval with real-world scenarios."""

    @pytest.mark.asyncio
    async def test_authentication_context(self):
        """Test retrieving context for authentication question."""
        backend = MockBackend()
        backend.test_data["context_search"] = [
            {
                "id": "auth-guide",
                "title": "JWT Authentication Setup",
                "content": "Configure JWT with FastAPI...",
                "memory_type": "documentation",
                "tags": ["auth", "fastapi"],
                "created_at": datetime.now(),
                "relevance_score": 0.95,
                "entity_matches": 3,
                "keyword_matches": 2,
                "related_memories": [
                    {"title": "Security Best Practices"}
                ],
            }
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_context(
            "How do I set up JWT authentication with FastAPI?"
        )

        assert len(result["source_memories"]) > 0
        assert result["source_memories"][0]["relevance"] > 0.9

    @pytest.mark.asyncio
    async def test_project_overview(self):
        """Test getting comprehensive project overview."""
        backend = MockBackend()
        backend.test_data["project_summary"] = [
            {
                "project_summary": {
                    "total_memories": 50,
                    "recent_activity": [
                        {"id": "r1", "title": "Added caching", "type": "feature", "created_at": datetime.now()}
                    ],
                    "decisions": [
                        {"id": "d1", "title": "Use PostgreSQL", "created_at": datetime.now() - timedelta(days=10)}
                    ],
                    "open_problems": [
                        {"id": "p1", "title": "Performance issue", "created_at": datetime.now() - timedelta(days=3)}
                    ],
                    "solutions": [
                        {"id": "s1", "title": "Optimized queries", "created_at": datetime.now() - timedelta(days=1)}
                    ],
                }
            }
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_project_context("my-app")

        # Should provide comprehensive overview
        assert result["total_memories"] == 50
        assert len(result["open_problems"]) > 0
        assert len(result["solutions"]) > 0

    @pytest.mark.asyncio
    async def test_debugging_session_context(self):
        """Test session context for debugging."""
        backend = MockBackend()
        backend.test_data["session_context"] = [
            {
                "id": "bug-1",
                "title": "Found NullPointerException",
                "content": "Error occurs in handler",
                "memory_type": "problem",
                "created_at": datetime.now() - timedelta(hours=2),
                "entities": ["NullPointerException", "handler"],
            },
            {
                "id": "fix-1",
                "title": "Added null check",
                "content": "Fixed by adding validation",
                "memory_type": "solution",
                "created_at": datetime.now() - timedelta(hours=1),
                "entities": ["validation", "handler"],
            },
        ]

        retriever = ContextRetriever(backend)
        result = await retriever.get_session_context(hours_back=12)

        # Should show debugging progression
        assert result["total_count"] == 2
        memory_types = [m["type"] for m in result["recent_memories"]]
        assert "problem" in memory_types
        assert "solution" in memory_types
