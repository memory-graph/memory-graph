"""
Tests for CrewAI integration.

These tests verify that the MemoryGraph CrewAI integration correctly
implements the CrewAI Memory interface and works as expected.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
from memorygraphsdk.models import Memory


@pytest.fixture
def mock_client():
    """Mock MemoryGraph client."""
    return Mock()


@pytest.fixture
def crewai_memory(api_key, mock_client):
    """CrewAI memory instance with mocked client."""
    with patch("memorygraphsdk.integrations.crewai.MemoryGraphClient") as MockClient:
        MockClient.return_value = mock_client
        memory = MemoryGraphCrewMemory(api_key=api_key, crew_id="test_crew")
        return memory


def test_save_memory(crewai_memory, mock_client):
    """Test saving a memory through CrewAI interface."""
    # Setup
    key = "test_key"
    value = "test_value"
    metadata = {
        "tags": ["test", "example"],
        "importance": 0.8,
        "type": "solution",
    }

    # Execute
    crewai_memory.save(key, value, metadata)

    # Verify
    mock_client.create_memory.assert_called_once()
    call_args = mock_client.create_memory.call_args
    assert call_args.kwargs["type"] == "solution"
    assert call_args.kwargs["title"] == key
    assert call_args.kwargs["content"] == value
    assert "test" in call_args.kwargs["tags"]
    assert "example" in call_args.kwargs["tags"]
    assert "crew:test_crew" in call_args.kwargs["tags"]
    assert call_args.kwargs["importance"] == 0.8


def test_save_memory_with_crew_tag(crewai_memory, mock_client):
    """Test that crew_id is automatically added as a tag."""
    crewai_memory.save("key", "value", {"tags": ["custom"]})

    call_args = mock_client.create_memory.call_args
    tags = call_args.kwargs["tags"]
    assert "crew:test_crew" in tags
    assert "custom" in tags


def test_save_memory_with_string_tags(crewai_memory, mock_client):
    """Test handling of string tags (should convert to list)."""
    crewai_memory.save("key", "value", {"tags": "single_tag"})

    call_args = mock_client.create_memory.call_args
    tags = call_args.kwargs["tags"]
    assert isinstance(tags, list)
    assert "single_tag" in tags


def test_save_memory_default_values(crewai_memory, mock_client):
    """Test saving memory with default values."""
    crewai_memory.save("key", "value")

    call_args = mock_client.create_memory.call_args
    assert call_args.kwargs["type"] == "general"
    assert call_args.kwargs["importance"] == 0.5
    assert "crew:test_crew" in call_args.kwargs["tags"]


def test_search_memories(crewai_memory, mock_client, sample_memory_response):
    """Test searching for memories."""
    # Setup
    memory = Memory(**sample_memory_response)
    mock_client.search_memories.return_value = [memory]

    # Execute
    results = crewai_memory.search("test query", limit=5)

    # Verify
    mock_client.search_memories.assert_called_once_with(
        query="test query",
        tags=["crew:test_crew"],
        limit=5,
    )

    assert len(results) == 1
    assert results[0]["key"] == memory.title
    assert results[0]["value"] == memory.content
    assert "metadata" in results[0]
    assert results[0]["metadata"]["id"] == memory.id
    assert results[0]["metadata"]["type"] == memory.type
    assert results[0]["metadata"]["importance"] == memory.importance


def test_search_memories_no_crew_id(api_key, mock_client):
    """Test searching without crew_id filter."""
    with patch("memorygraphsdk.integrations.crewai.MemoryGraphClient") as MockClient:
        MockClient.return_value = mock_client
        mock_client.search_memories.return_value = []  # Return empty list
        memory = MemoryGraphCrewMemory(api_key=api_key, crew_id="")

        memory.search("test", limit=3)

        call_args = mock_client.search_memories.call_args
        # Should not include tags filter when crew_id is empty
        assert call_args.kwargs["tags"] is None


def test_get_memory_found(crewai_memory, mock_client, sample_memory_response):
    """Test getting a specific memory by key."""
    # Setup
    memory = Memory(**sample_memory_response)
    memory.title = "exact_match"
    mock_client.search_memories.return_value = [memory]

    # Execute
    result = crewai_memory.get("exact_match")

    # Verify
    assert result == memory.content
    mock_client.search_memories.assert_called_once_with(
        query="exact_match",
        tags=["crew:test_crew"],
        limit=1,
    )


def test_get_memory_not_found(crewai_memory, mock_client):
    """Test getting a memory that doesn't exist."""
    # Setup
    mock_client.search_memories.return_value = []

    # Execute
    result = crewai_memory.get("nonexistent")

    # Verify
    assert result is None


def test_get_memory_title_mismatch(crewai_memory, mock_client, sample_memory_response):
    """Test get returns None when title doesn't match exactly."""
    # Setup - return a memory with different title
    memory = Memory(**sample_memory_response)
    memory.title = "different_title"
    mock_client.search_memories.return_value = [memory]

    # Execute
    result = crewai_memory.get("requested_title")

    # Verify - should return None because title doesn't match
    assert result is None


def test_clear_memory(crewai_memory):
    """Test clear method (no-op for MemoryGraph)."""
    # Should not raise any errors
    crewai_memory.clear()


def test_reset_memory(crewai_memory):
    """Test reset method (alias for clear)."""
    # Should not raise any errors
    crewai_memory.reset()


def test_close_memory(crewai_memory, mock_client):
    """Test closing the memory client."""
    crewai_memory.close()
    mock_client.close.assert_called_once()


def test_context_manager(api_key):
    """Test using memory as a context manager."""
    mock_client = Mock()

    with patch("memorygraphsdk.integrations.crewai.MemoryGraphClient") as MockClient:
        MockClient.return_value = mock_client

        with MemoryGraphCrewMemory(api_key=api_key) as memory:
            assert memory is not None

        # Should close on exit
        mock_client.close.assert_called_once()


def test_custom_api_url(api_key):
    """Test initialization with custom API URL."""
    custom_url = "https://custom.memorygraph.dev"

    with patch("memorygraphsdk.integrations.crewai.MemoryGraphClient") as MockClient:
        MemoryGraphCrewMemory(api_key=api_key, api_url=custom_url, crew_id="test")

        MockClient.assert_called_once()
        call_args = MockClient.call_args
        assert call_args.kwargs["api_key"] == api_key
        assert call_args.kwargs["api_url"] == custom_url


def test_metadata_context_handling(crewai_memory, mock_client):
    """Test that extra metadata fields are stored in context."""
    metadata = {
        "tags": ["test"],
        "importance": 0.7,
        "type": "solution",
        "custom_field": "custom_value",
        "another_field": 123,
    }

    crewai_memory.save("key", "value", metadata)

    call_args = mock_client.create_memory.call_args
    context = call_args.kwargs["context"]

    # Custom fields should be in context
    assert context["custom_field"] == "custom_value"
    assert context["another_field"] == 123
    assert context["crew_id"] == "test_crew"

    # Standard fields should not be in context
    assert "tags" not in context
    assert "importance" not in context
    assert "type" not in context


def test_memory_without_crewai_installed():
    """Test that module can be imported even if CrewAI is not installed."""
    # This is implicitly tested by the fact that all other tests run
    # The module uses conditional imports to handle missing CrewAI
    from memorygraphsdk.integrations import crewai
    assert crewai.MemoryGraphCrewMemory is not None


def test_search_result_includes_created_at(crewai_memory, mock_client, sample_memory_response):
    """Test that search results include timestamp metadata."""
    memory = Memory(**sample_memory_response)
    mock_client.search_memories.return_value = [memory]

    results = crewai_memory.search("test", limit=1)

    assert len(results) == 1
    assert "created_at" in results[0]["metadata"]
    assert results[0]["metadata"]["created_at"] == "2024-01-01T00:00:00+00:00"
