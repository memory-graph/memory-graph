"""Shared pytest fixtures for MemoryGraph SDK tests."""
import pytest


@pytest.fixture
def api_url():
    """Base API URL for tests."""
    return "https://api.memorygraph.dev"


@pytest.fixture
def api_key():
    """Test API key."""
    return "mgraph_test_key_12345"


@pytest.fixture
def sample_memory_response():
    """Sample memory API response."""
    return {
        "id": "mem_123",
        "type": "solution",
        "title": "Test Memory",
        "content": "Test content for the memory",
        "tags": ["test", "sample"],
        "importance": 0.5,
        "context": None,
        "summary": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_relationship_response():
    """Sample relationship API response."""
    return {
        "id": "rel_123",
        "from_memory_id": "mem_1",
        "to_memory_id": "mem_2",
        "relationship_type": "SOLVES",
        "strength": 0.5,
        "confidence": 0.8,
        "context": None,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_search_response(sample_memory_response):
    """Sample search API response."""
    return {
        "memories": [sample_memory_response],
        "total": 1,
        "offset": 0,
        "limit": 20,
    }


@pytest.fixture
def sample_related_response(sample_memory_response):
    """Sample related memories API response."""
    return {
        "related": [
            {
                "memory": sample_memory_response,
                "relationship_type": "SOLVES",
                "strength": 0.8,
                "depth": 1,
            }
        ]
    }
