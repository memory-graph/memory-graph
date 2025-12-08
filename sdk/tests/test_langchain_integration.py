"""
Tests for LangChain integration.

These tests verify that the MemoryGraph LangChain integration correctly
implements the LangChain BaseMemory interface and works as expected.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from memorygraphsdk.integrations.langchain import MemoryGraphMemory
from memorygraphsdk.models import Memory


@pytest.fixture
def mock_client():
    """Mock MemoryGraph client."""
    return Mock()


@pytest.fixture
def langchain_memory(api_key, mock_client):
    """LangChain memory instance with mocked client."""
    with patch("memorygraphsdk.integrations.langchain.LANGCHAIN_AVAILABLE", True):
        with patch("memorygraphsdk.integrations.langchain.MemoryGraphClient") as MockClient:
            MockClient.return_value = mock_client
            memory = MemoryGraphMemory(
                api_key=api_key,
                session_id="test_session",
            )
            return memory


@pytest.fixture
def conversation_memories():
    """Sample conversation memories."""
    return [
        Memory(
            id="mem_1",
            type="conversation",
            title="User: Hello",
            content="Hello, how are you?",
            tags=["session:test_session", "role:human"],
            importance=0.5,
            context={"role": "human", "session_id": "test_session"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        ),
        Memory(
            id="mem_2",
            type="conversation",
            title="AI: I'm doing well",
            content="I'm doing well, thank you!",
            tags=["session:test_session", "role:ai"],
            importance=0.5,
            context={"role": "ai", "session_id": "test_session"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 1),
            updated_at=datetime(2024, 1, 1, 12, 0, 1),
        ),
    ]


def test_memory_variables(langchain_memory):
    """Test that memory_variables returns correct list."""
    assert langchain_memory.memory_variables == ["history"]


def test_memory_variables_custom_key(api_key):
    """Test custom memory_key."""
    with patch("memorygraphsdk.integrations.langchain.LANGCHAIN_AVAILABLE", True):
        with patch("memorygraphsdk.integrations.langchain.MemoryGraphClient"):
            memory = MemoryGraphMemory(
                api_key=api_key,
                memory_key="chat_history",
            )
            assert memory.memory_variables == ["chat_history"]


def test_save_context(langchain_memory, mock_client):
    """Test saving conversation context."""
    # Setup
    inputs = {"input": "What is Redis?"}
    outputs = {"output": "Redis is an in-memory data structure store."}

    # Execute
    langchain_memory.save_context(inputs, outputs)

    # Verify - should have been called twice (once for user, once for AI)
    assert mock_client.create_memory.call_count == 2

    # Check first call (user input)
    first_call = mock_client.create_memory.call_args_list[0]
    assert first_call.kwargs["type"] == "conversation"
    assert first_call.kwargs["content"] == "What is Redis?"
    assert "session:test_session" in first_call.kwargs["tags"]
    assert "role:human" in first_call.kwargs["tags"]
    assert first_call.kwargs["context"]["role"] == "human"
    assert first_call.kwargs["context"]["session_id"] == "test_session"

    # Check second call (AI output)
    second_call = mock_client.create_memory.call_args_list[1]
    assert second_call.kwargs["type"] == "conversation"
    assert second_call.kwargs["content"] == "Redis is an in-memory data structure store."
    assert "session:test_session" in second_call.kwargs["tags"]
    assert "role:ai" in second_call.kwargs["tags"]
    assert second_call.kwargs["context"]["role"] == "ai"


def test_save_context_truncates_long_titles(langchain_memory, mock_client):
    """Test that long inputs/outputs are truncated in titles."""
    long_text = "This is a very long text " * 10  # > 50 chars
    inputs = {"input": long_text}
    outputs = {"output": long_text}

    langchain_memory.save_context(inputs, outputs)

    # Both calls should have truncated titles
    for call in mock_client.create_memory.call_args_list:
        title = call.kwargs["title"]
        # Should be truncated and end with "..."
        assert "..." in title
        # Title should be reasonable length
        assert len(title) < 70


def test_load_memory_variables_string_format(langchain_memory, mock_client, conversation_memories):
    """Test loading memory variables as string format."""
    # Setup
    mock_client.search_memories.return_value = conversation_memories

    # Execute
    result = langchain_memory.load_memory_variables({})

    # Verify search call
    mock_client.search_memories.assert_called_once_with(
        tags=["session:test_session"],
        memory_types=["conversation"],
        limit=50,
    )

    # Verify result format
    assert "history" in result
    history = result["history"]
    assert isinstance(history, str)
    assert "Human: Hello, how are you?" in history
    assert "AI: I'm doing well, thank you!" in history


def test_load_memory_variables_message_format(api_key, mock_client, conversation_memories):
    """Test loading memory variables as Message objects."""
    # Setup - Mock the message classes
    mock_human_msg = Mock()
    mock_ai_msg = Mock()

    with patch("memorygraphsdk.integrations.langchain.LANGCHAIN_AVAILABLE", True):
        with patch("memorygraphsdk.integrations.langchain.HumanMessage", return_value=mock_human_msg):
            with patch("memorygraphsdk.integrations.langchain.AIMessage", return_value=mock_ai_msg):
                with patch("memorygraphsdk.integrations.langchain.MemoryGraphClient") as MockClient:
                    MockClient.return_value = mock_client
                    memory = MemoryGraphMemory(
                        api_key=api_key,
                        session_id="test_session",
                        return_messages=True,
                    )

                    mock_client.search_memories.return_value = conversation_memories

                    # Execute
                    result = memory.load_memory_variables({})

                    # Verify result format
                    assert "history" in result
                    messages = result["history"]
                    assert isinstance(messages, list)
                    assert len(messages) == 2


def test_load_memory_variables_empty(langchain_memory, mock_client):
    """Test loading memory variables when no history exists."""
    # Setup
    mock_client.search_memories.return_value = []

    # Execute
    result = langchain_memory.load_memory_variables({})

    # Verify
    assert "history" in result
    assert result["history"] == ""


def test_load_memory_variables_sorts_by_time(langchain_memory, mock_client):
    """Test that memories are sorted by creation time."""
    # Setup - create memories in reverse order
    unsorted_memories = [
        Memory(
            id="mem_2",
            type="conversation",
            title="Second message",
            content="Second",
            tags=["session:test_session", "role:ai"],
            importance=0.5,
            context={"role": "ai"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 1),
            updated_at=datetime(2024, 1, 1, 12, 0, 1),
        ),
        Memory(
            id="mem_1",
            type="conversation",
            title="First message",
            content="First",
            tags=["session:test_session", "role:human"],
            importance=0.5,
            context={"role": "human"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        ),
    ]
    mock_client.search_memories.return_value = unsorted_memories

    # Execute
    result = langchain_memory.load_memory_variables({})

    # Verify - should be sorted by time
    history = result["history"]
    # "First" should come before "Second"
    assert history.index("First") < history.index("Second")


def test_clear_is_noop(langchain_memory):
    """Test that clear() is a no-op (memories are permanent)."""
    # Should not raise any errors
    langchain_memory.clear()


def test_custom_input_output_keys(api_key, mock_client):
    """Test custom input/output keys."""
    with patch("memorygraphsdk.integrations.langchain.LANGCHAIN_AVAILABLE", True):
        with patch("memorygraphsdk.integrations.langchain.MemoryGraphClient") as MockClient:
            MockClient.return_value = mock_client
            memory = MemoryGraphMemory(
                api_key=api_key,
                input_key="question",
                output_key="answer",
            )

            inputs = {"question": "What is Python?"}
            outputs = {"answer": "Python is a programming language."}

            memory.save_context(inputs, outputs)

            # Verify both messages were saved
            assert mock_client.create_memory.call_count == 2
            first_call = mock_client.create_memory.call_args_list[0]
            assert first_call.kwargs["content"] == "What is Python?"
            second_call = mock_client.create_memory.call_args_list[1]
            assert second_call.kwargs["content"] == "Python is a programming language."


def test_missing_input_or_output(langchain_memory, mock_client):
    """Test handling of missing input or output."""
    # Missing output
    langchain_memory.save_context({"input": "Hello"}, {})
    assert mock_client.create_memory.call_count == 1

    mock_client.reset_mock()

    # Missing input
    langchain_memory.save_context({}, {"output": "Hello"})
    assert mock_client.create_memory.call_count == 1


def test_session_isolation(api_key, mock_client):
    """Test that different sessions are isolated."""
    with patch("memorygraphsdk.integrations.langchain.LANGCHAIN_AVAILABLE", True):
        with patch("memorygraphsdk.integrations.langchain.MemoryGraphClient") as MockClient:
            MockClient.return_value = mock_client
            # Mock the search to return empty list
            mock_client.search_memories.return_value = []

            memory1 = MemoryGraphMemory(api_key=api_key, session_id="session_1")
            memory2 = MemoryGraphMemory(api_key=api_key, session_id="session_2")

            # Save context in session 1
            memory1.save_context({"input": "Hello"}, {"output": "Hi"})

            # Load from session 2
            memory2.load_memory_variables({})

            # Verify session 2 searches with its own session tag
            calls = mock_client.search_memories.call_args_list
            assert any("session:session_2" in call.kwargs.get("tags", []) for call in calls)


def test_initialization_without_langchain():
    """Test that proper error is raised when langchain is not installed."""
    with patch("memorygraphsdk.integrations.langchain.LANGCHAIN_AVAILABLE", False):
        with pytest.raises(ImportError, match="LangChain is not installed"):
            MemoryGraphMemory(api_key="test_key")


def test_handles_unknown_role(langchain_memory, mock_client):
    """Test handling of messages with unknown roles."""
    # Setup memory with unknown role
    unknown_role_memory = Memory(
        id="mem_1",
        type="conversation",
        title="Unknown",
        content="Message with unknown role",
        tags=["session:test_session"],
        importance=0.5,
        context={"role": "system"},  # Unknown role
        summary=None,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )
    mock_client.search_memories.return_value = [unknown_role_memory]

    # In string format, should still work
    result = langchain_memory.load_memory_variables({})
    assert "Message with unknown role" in result["history"]


def test_handles_missing_context(langchain_memory, mock_client):
    """Test handling of memories without context."""
    # Setup memory without context
    no_context_memory = Memory(
        id="mem_1",
        type="conversation",
        title="No context",
        content="Message without context",
        tags=["session:test_session"],
        importance=0.5,
        context=None,
        summary=None,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )
    mock_client.search_memories.return_value = [no_context_memory]

    # Should handle gracefully
    result = langchain_memory.load_memory_variables({})
    assert "Message without context" in result["history"]
