"""
Tests for AutoGen integration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from memorygraphsdk.integrations.autogen import MemoryGraphAutoGenHistory
from memorygraphsdk.models import Memory
from datetime import datetime


@pytest.fixture
def mock_client():
    """Create a mock MemoryGraph client."""
    with patch('memorygraphsdk.integrations.autogen.MemoryGraphClient') as mock:
        yield mock


def test_autogen_history_init(mock_client):
    """Test AutoGen history initialization."""
    history = MemoryGraphAutoGenHistory(
        api_key="test_key",
        conversation_id="test_conv"
    )

    assert history.conversation_id == "test_conv"
    mock_client.assert_called_once_with(
        api_key="test_key",
        api_url="https://api.memorygraph.dev"
    )


def test_add_message(mock_client):
    """Test adding a message to history."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    history = MemoryGraphAutoGenHistory(
        api_key="test_key",
        conversation_id="test_conv"
    )

    history.add_message("user", "Hello, world!")

    # Verify create_memory was called with correct arguments
    mock_instance.create_memory.assert_called_once()
    call_args = mock_instance.create_memory.call_args

    assert call_args[1]["type"] == "conversation"
    assert call_args[1]["content"] == "Hello, world!"
    assert "conversation:test_conv" in call_args[1]["tags"]
    assert "role:user" in call_args[1]["tags"]
    assert "autogen" in call_args[1]["tags"]
    assert call_args[1]["context"]["role"] == "user"
    assert call_args[1]["context"]["conversation_id"] == "test_conv"


def test_add_message_with_metadata(mock_client):
    """Test adding a message with metadata."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    history = MemoryGraphAutoGenHistory(api_key="test_key")

    history.add_message(
        "assistant",
        "I can help with that",
        metadata={"timestamp": "2025-12-08T10:30:00", "model": "gpt-4"}
    )

    call_args = mock_instance.create_memory.call_args
    assert call_args[1]["context"]["timestamp"] == "2025-12-08T10:30:00"
    assert call_args[1]["context"]["model"] == "gpt-4"


def test_get_messages(mock_client):
    """Test retrieving messages."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    # Create mock memories
    mock_memories = [
        Memory(
            id="1",
            type="conversation",
            title="user: Hello",
            content="Hello, world!",
            tags=["conversation:test_conv", "role:user"],
            importance=0.5,
            context={"role": "user", "conversation_id": "test_conv"},
            created_at=datetime(2025, 12, 8, 10, 0, 0),
            updated_at=datetime(2025, 12, 8, 10, 0, 0)
        ),
        Memory(
            id="2",
            type="conversation",
            title="assistant: Hi there",
            content="Hi there! How can I help?",
            tags=["conversation:test_conv", "role:assistant"],
            importance=0.5,
            context={"role": "assistant", "conversation_id": "test_conv"},
            created_at=datetime(2025, 12, 8, 10, 0, 5),
            updated_at=datetime(2025, 12, 8, 10, 0, 5)
        )
    ]

    mock_instance.search_memories.return_value = mock_memories

    history = MemoryGraphAutoGenHistory(api_key="test_key", conversation_id="test_conv")
    messages = history.get_messages()

    # Verify search was called correctly
    mock_instance.search_memories.assert_called_once_with(
        tags=["conversation:test_conv"],
        limit=100
    )

    # Verify messages are returned in correct format and order
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello, world!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there! How can I help?"


def test_get_messages_with_limit(mock_client):
    """Test retrieving messages with custom limit."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance
    mock_instance.search_memories.return_value = []

    history = MemoryGraphAutoGenHistory(api_key="test_key")
    history.get_messages(limit=50)

    mock_instance.search_memories.assert_called_once_with(
        tags=["conversation:default"],
        limit=50
    )


def test_clear_is_noop(mock_client):
    """Test that clear() is a no-op."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    history = MemoryGraphAutoGenHistory(api_key="test_key")
    history.clear()  # Should not raise any errors

    # No methods should be called on client
    assert not mock_instance.delete_memory.called


def test_context_manager(mock_client):
    """Test using AutoGen history as context manager."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    with MemoryGraphAutoGenHistory(api_key="test_key") as history:
        assert history.conversation_id == "default"

    # Verify close was called
    mock_instance.close.assert_called_once()


def test_close(mock_client):
    """Test closing the history client."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    history = MemoryGraphAutoGenHistory(api_key="test_key")
    history.close()

    mock_instance.close.assert_called_once()


def test_long_content_truncation_in_title(mock_client):
    """Test that long content is truncated in the title."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    history = MemoryGraphAutoGenHistory(api_key="test_key")

    long_content = "a" * 100  # 100 character message
    history.add_message("user", long_content)

    call_args = mock_instance.create_memory.call_args
    title = call_args[1]["title"]

    # Title should be truncated
    assert len(title) == 59  # "user: " (6) + 50 chars + "..." (3) = 59
    assert title.startswith("user: ")
    assert title.endswith("...")


def test_message_without_role_in_context(mock_client):
    """Test handling messages where context doesn't have role."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    # Create mock memory without role in context
    mock_memory = Memory(
        id="1",
        type="conversation",
        title="Message",
        content="Some content",
        tags=["conversation:test_conv"],
        importance=0.5,
        context={"conversation_id": "test_conv"},  # No role
        created_at=datetime(2025, 12, 8, 10, 0, 0),
        updated_at=datetime(2025, 12, 8, 10, 0, 0)
    )

    mock_instance.search_memories.return_value = [mock_memory]

    history = MemoryGraphAutoGenHistory(api_key="test_key")
    messages = history.get_messages()

    # Should default to "unknown" role
    assert messages[0]["role"] == "unknown"


def test_message_with_none_context(mock_client):
    """Test handling messages where context is None."""
    mock_instance = Mock()
    mock_client.return_value = mock_instance

    # Create mock memory with None context
    mock_memory = Memory(
        id="1",
        type="conversation",
        title="Message",
        content="Some content",
        tags=["conversation:test_conv"],
        importance=0.5,
        context=None,  # None context
        created_at=datetime(2025, 12, 8, 10, 0, 0),
        updated_at=datetime(2025, 12, 8, 10, 0, 0)
    )

    mock_instance.search_memories.return_value = [mock_memory]

    history = MemoryGraphAutoGenHistory(api_key="test_key")
    messages = history.get_messages()

    # Should default to "unknown" role
    assert messages[0]["role"] == "unknown"


def test_custom_api_url(mock_client):
    """Test using custom API URL."""
    history = MemoryGraphAutoGenHistory(
        api_key="test_key",
        api_url="https://custom.api.com"
    )

    mock_client.assert_called_once_with(
        api_key="test_key",
        api_url="https://custom.api.com"
    )
