"""
Tests for LlamaIndex integration.

These tests verify that the MemoryGraph LlamaIndex integration correctly
implements the LlamaIndex interfaces and works as expected.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from memorygraphsdk.integrations.llamaindex import (
    MemoryGraphChatMemory,
    MemoryGraphRetriever,
)
from memorygraphsdk.models import Memory, RelatedMemory


@pytest.fixture
def mock_client():
    """Mock MemoryGraph client."""
    return Mock()


@pytest.fixture
def mock_llamaindex_available():
    """Mock LlamaIndex as available."""
    # Create mock message role enum
    mock_role = MagicMock()
    mock_role.USER = "user"
    mock_role.ASSISTANT = "assistant"
    mock_role.SYSTEM = "system"

    # Create mock ChatMessage class
    class MockChatMessage:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    with patch("memorygraphsdk.integrations.llamaindex.LLAMAINDEX_AVAILABLE", True):
        with patch("memorygraphsdk.integrations.llamaindex.MessageRole", mock_role):
            with patch("memorygraphsdk.integrations.llamaindex.ChatMessage", MockChatMessage):
                yield {"MessageRole": mock_role, "ChatMessage": MockChatMessage}


@pytest.fixture
def llamaindex_memory(api_key, mock_client, mock_llamaindex_available):
    """LlamaIndex memory instance with mocked client."""
    with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient") as MockClient:
        MockClient.return_value = mock_client
        memory = MemoryGraphChatMemory(
            api_key=api_key,
            session_id="test_session",
        )
        return memory


@pytest.fixture
def llamaindex_retriever(api_key, mock_client):
    """LlamaIndex retriever instance with mocked client."""
    with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient") as MockClient:
        MockClient.return_value = mock_client
        retriever = MemoryGraphRetriever(api_key=api_key)
        return retriever


@pytest.fixture
def conversation_memories():
    """Sample conversation memories."""
    return [
        Memory(
            id="mem_1",
            type="conversation",
            title="User: Hello",
            content="Hello, how are you?",
            tags=["session:test_session", "role:user"],
            importance=0.5,
            context={"role": "user", "session_id": "test_session"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        ),
        Memory(
            id="mem_2",
            type="conversation",
            title="AI: I'm doing well",
            content="I'm doing well, thank you!",
            tags=["session:test_session", "role:assistant"],
            importance=0.5,
            context={"role": "assistant", "session_id": "test_session"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 1),
            updated_at=datetime(2024, 1, 1, 12, 0, 1),
        ),
    ]


class TestMemoryGraphChatMemory:
    """Tests for MemoryGraphChatMemory class."""

    def test_initialization_without_llamaindex(self, api_key):
        """Test that proper error is raised when llama-index is not installed."""
        with patch("memorygraphsdk.integrations.llamaindex.LLAMAINDEX_AVAILABLE", False):
            with pytest.raises(ImportError, match="llama-index is required"):
                MemoryGraphChatMemory(api_key=api_key)

    def test_class_name(self, llamaindex_memory):
        """Test class_name method returns correct value."""
        assert MemoryGraphChatMemory.class_name() == "MemoryGraphChatMemory"

    def test_get_without_input(self, llamaindex_memory, mock_client, conversation_memories, mock_llamaindex_available):
        """Test get() without input query returns all session messages."""
        # Setup
        mock_client.search_memories.return_value = conversation_memories

        # Execute
        messages = llamaindex_memory.get()

        # Verify search call
        mock_client.search_memories.assert_called_once_with(
            tags=["session:test_session"],
            memory_types=["conversation"],
            limit=10,
        )

        # Verify messages
        assert len(messages) == 2
        assert messages[0].content == "Hello, how are you?"
        assert messages[1].content == "I'm doing well, thank you!"

    def test_get_with_input(self, llamaindex_memory, mock_client, conversation_memories, mock_llamaindex_available):
        """Test get() with input query performs semantic search."""
        # Setup
        mock_client.search_memories.return_value = conversation_memories

        # Execute
        messages = llamaindex_memory.get(input="greeting")

        # Verify search call includes query
        mock_client.search_memories.assert_called_once_with(
            tags=["session:test_session"],
            memory_types=["conversation"],
            limit=10,
            query="greeting",
        )

        assert len(messages) == 2

    def test_get_custom_limit(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test get() with custom limit parameter."""
        # Setup
        mock_client.search_memories.return_value = []

        # Execute
        llamaindex_memory.get(limit=5)

        # Verify
        call_args = mock_client.search_memories.call_args
        assert call_args.kwargs["limit"] == 5

    def test_get_sorts_by_created_at(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test that get() sorts messages by creation time."""
        # Setup - create memories in reverse order
        unsorted_memories = [
            Memory(
                id="mem_2",
                type="conversation",
                title="Second",
                content="Second message",
                tags=["session:test_session"],
                importance=0.5,
                context={"role": "user"},
                summary=None,
                created_at=datetime(2024, 1, 1, 12, 0, 1),
                updated_at=datetime(2024, 1, 1, 12, 0, 1),
            ),
            Memory(
                id="mem_1",
                type="conversation",
                title="First",
                content="First message",
                tags=["session:test_session"],
                importance=0.5,
                context={"role": "user"},
                summary=None,
                created_at=datetime(2024, 1, 1, 12, 0, 0),
                updated_at=datetime(2024, 1, 1, 12, 0, 0),
            ),
        ]
        mock_client.search_memories.return_value = unsorted_memories

        # Execute
        messages = llamaindex_memory.get()

        # Verify - should be sorted chronologically
        assert messages[0].content == "First message"
        assert messages[1].content == "Second message"

    def test_get_role_mapping_user(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test role mapping for user messages."""
        # Setup
        user_memory = Memory(
            id="mem_1",
            type="conversation",
            title="User message",
            content="User message",
            tags=["session:test_session"],
            importance=0.5,
            context={"role": "user"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_client.search_memories.return_value = [user_memory]

        # Execute
        messages = llamaindex_memory.get()

        # Verify
        assert messages[0].role == mock_llamaindex_available["MessageRole"].USER

    def test_get_role_mapping_assistant(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test role mapping for assistant messages."""
        # Setup
        assistant_memory = Memory(
            id="mem_1",
            type="conversation",
            title="Assistant message",
            content="Assistant message",
            tags=["session:test_session"],
            importance=0.5,
            context={"role": "assistant"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_client.search_memories.return_value = [assistant_memory]

        # Execute
        messages = llamaindex_memory.get()

        # Verify
        assert messages[0].role == mock_llamaindex_available["MessageRole"].ASSISTANT

    def test_get_role_mapping_ai_alias(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test role mapping for 'ai' role (alias for assistant)."""
        # Setup
        ai_memory = Memory(
            id="mem_1",
            type="conversation",
            title="AI message",
            content="AI message",
            tags=["session:test_session"],
            importance=0.5,
            context={"role": "ai"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_client.search_memories.return_value = [ai_memory]

        # Execute
        messages = llamaindex_memory.get()

        # Verify
        assert messages[0].role == mock_llamaindex_available["MessageRole"].ASSISTANT

    def test_get_role_mapping_system(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test role mapping for system messages."""
        # Setup
        system_memory = Memory(
            id="mem_1",
            type="conversation",
            title="System message",
            content="System message",
            tags=["session:test_session"],
            importance=0.5,
            context={"role": "system"},
            summary=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_client.search_memories.return_value = [system_memory]

        # Execute
        messages = llamaindex_memory.get()

        # Verify
        assert messages[0].role == mock_llamaindex_available["MessageRole"].SYSTEM

    def test_get_handles_missing_context(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test handling of memories without context (defaults to user)."""
        # Setup
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

        # Execute
        messages = llamaindex_memory.get()

        # Verify - should default to USER role
        assert messages[0].role == mock_llamaindex_available["MessageRole"].USER

    def test_get_all(self, llamaindex_memory, mock_client, conversation_memories, mock_llamaindex_available):
        """Test get_all() method returns all messages."""
        # Setup
        mock_client.search_memories.return_value = conversation_memories

        # Execute
        messages = llamaindex_memory.get_all()

        # Verify
        assert len(messages) == 2
        # Should call search without query
        call_args = mock_client.search_memories.call_args
        assert "query" not in call_args.kwargs

    def test_put_message(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test put() stores a message in memory."""
        # Setup
        ChatMessage = mock_llamaindex_available["ChatMessage"]
        MessageRole = mock_llamaindex_available["MessageRole"]
        message = ChatMessage(role=MessageRole.USER, content="Test message")

        # Execute
        llamaindex_memory.put(message)

        # Verify
        mock_client.create_memory.assert_called_once()
        call_args = mock_client.create_memory.call_args
        assert call_args.kwargs["type"] == "conversation"
        assert call_args.kwargs["content"] == "Test message"
        assert "session:test_session" in call_args.kwargs["tags"]
        assert "role:user" in call_args.kwargs["tags"]
        assert "llamaindex" in call_args.kwargs["tags"]
        assert call_args.kwargs["context"]["role"] == "user"
        assert call_args.kwargs["context"]["session_id"] == "test_session"

    def test_put_truncates_title(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test that put() truncates long content in title."""
        # Setup
        ChatMessage = mock_llamaindex_available["ChatMessage"]
        MessageRole = mock_llamaindex_available["MessageRole"]
        long_content = "This is a very long message " * 10  # > 50 chars
        message = ChatMessage(role=MessageRole.USER, content=long_content)

        # Execute
        llamaindex_memory.put(message)

        # Verify
        call_args = mock_client.create_memory.call_args
        title = call_args.kwargs["title"]
        assert "..." in title
        # Title should contain truncated content
        assert long_content[:50] in title

    def test_put_handles_role_enum(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test put() handles role with .value attribute."""
        # Setup
        ChatMessage = mock_llamaindex_available["ChatMessage"]

        # Create mock role with .value attribute
        mock_role = MagicMock()
        mock_role.value = "assistant"

        message = ChatMessage(role=mock_role, content="Test")

        # Execute
        llamaindex_memory.put(message)

        # Verify
        call_args = mock_client.create_memory.call_args
        assert "role:assistant" in call_args.kwargs["tags"]

    def test_set_messages(self, llamaindex_memory, mock_client, mock_llamaindex_available):
        """Test set() method stores multiple messages."""
        # Setup
        ChatMessage = mock_llamaindex_available["ChatMessage"]
        MessageRole = mock_llamaindex_available["MessageRole"]
        messages = [
            ChatMessage(role=MessageRole.USER, content="First"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Second"),
        ]

        # Execute
        llamaindex_memory.set(messages)

        # Verify
        assert mock_client.create_memory.call_count == 2

    def test_reset_is_noop(self, llamaindex_memory):
        """Test reset() is a no-op (memories are permanent)."""
        # Should not raise any errors
        llamaindex_memory.reset()


class TestMemoryGraphRetriever:
    """Tests for MemoryGraphRetriever class."""

    def test_initialization(self, api_key):
        """Test retriever initialization."""
        with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient") as MockClient:
            retriever = MemoryGraphRetriever(api_key=api_key)

            MockClient.assert_called_once_with(
                api_key=api_key,
                api_url="https://api.memorygraph.dev"
            )
            assert retriever.memory_types == ["solution", "code_pattern", "fix"]
            assert retriever.min_importance is None

    def test_initialization_custom_params(self, api_key):
        """Test retriever initialization with custom parameters."""
        with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient"):
            retriever = MemoryGraphRetriever(
                api_key=api_key,
                memory_types=["solution"],
                api_url="https://custom.api.dev",
                min_importance=0.7
            )

            assert retriever.memory_types == ["solution"]
            assert retriever.min_importance == 0.7

    def test_retrieve_basic(self, llamaindex_retriever, mock_client, sample_memory_response):
        """Test basic retrieve() functionality."""
        # Setup
        memory = Memory(**sample_memory_response)
        mock_client.search_memories.return_value = [memory]

        # Execute
        nodes = llamaindex_retriever.retrieve("test query", limit=5)

        # Verify search call
        mock_client.search_memories.assert_called_once_with(
            query="test query",
            memory_types=["solution", "code_pattern", "fix"],
            limit=5,
        )

        # Verify node format
        assert len(nodes) == 1
        node = nodes[0]
        assert node["id"] == "mem_123"
        assert node["text"] == "# Test Memory\n\nTest content for the memory"
        assert node["score"] == 0.5
        assert node["metadata"]["memory_id"] == "mem_123"
        assert node["metadata"]["type"] == "solution"
        assert node["metadata"]["tags"] == ["test", "sample"]
        assert node["metadata"]["importance"] == 0.5

    def test_retrieve_with_summary(self, llamaindex_retriever, mock_client, sample_memory_response):
        """Test retrieve() includes summary in metadata if present."""
        # Setup
        memory_data = {**sample_memory_response, "summary": "Test summary"}
        memory = Memory(**memory_data)
        mock_client.search_memories.return_value = [memory]

        # Execute
        nodes = llamaindex_retriever.retrieve("test query")

        # Verify
        assert nodes[0]["metadata"]["summary"] == "Test summary"

    def test_retrieve_memory_type_filtering(self, api_key, mock_client):
        """Test retrieve() with custom memory types."""
        # Setup
        with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient") as MockClient:
            MockClient.return_value = mock_client
            mock_client.search_memories.return_value = []

            retriever = MemoryGraphRetriever(
                api_key=api_key,
                memory_types=["solution", "problem"]
            )

            # Execute
            retriever.retrieve("test")

            # Verify
            call_args = mock_client.search_memories.call_args
            assert call_args.kwargs["memory_types"] == ["solution", "problem"]

    def test_retrieve_importance_filtering(self, api_key, mock_client):
        """Test retrieve() with min_importance threshold."""
        # Setup
        with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient") as MockClient:
            MockClient.return_value = mock_client
            mock_client.search_memories.return_value = []

            retriever = MemoryGraphRetriever(
                api_key=api_key,
                min_importance=0.8
            )

            # Execute
            retriever.retrieve("test")

            # Verify
            call_args = mock_client.search_memories.call_args
            assert call_args.kwargs["min_importance"] == 0.8

    def test_retrieve_kwargs_override(self, llamaindex_retriever, mock_client):
        """Test that additional kwargs override default parameters."""
        # Setup
        mock_client.search_memories.return_value = []

        # Execute
        llamaindex_retriever.retrieve(
            "test",
            limit=3,
            memory_types=["custom"],
            min_importance=0.9
        )

        # Verify overrides
        call_args = mock_client.search_memories.call_args
        assert call_args.kwargs["limit"] == 3
        assert call_args.kwargs["memory_types"] == ["custom"]
        assert call_args.kwargs["min_importance"] == 0.9

    def test_retrieve_with_relationships_basic(self, llamaindex_retriever, mock_client, sample_memory_response):
        """Test retrieve_with_relationships() basic functionality."""
        # Setup
        memory = Memory(**sample_memory_response)
        mock_client.search_memories.return_value = [memory]

        # Mock related memories
        related_memory = Memory(**{**sample_memory_response, "id": "mem_456", "title": "Related"})
        related_result = RelatedMemory(
            memory=related_memory,
            relationship_type="SOLVES",
            strength=0.8,
            depth=1
        )
        mock_client.get_related_memories.return_value = [related_result]

        # Execute
        nodes = llamaindex_retriever.retrieve_with_relationships("test query", limit=5)

        # Verify
        assert len(nodes) == 1
        node = nodes[0]

        # Should have called get_related_memories
        mock_client.get_related_memories.assert_called_once_with(
            memory_id="mem_123",
            max_depth=1
        )

        # Verify relationships in metadata
        assert "related" in node["metadata"]
        assert len(node["metadata"]["related"]) == 1
        related = node["metadata"]["related"][0]
        assert related["memory_id"] == "mem_456"
        assert related["title"] == "Related"
        assert related["relationship_type"] == "SOLVES"
        assert related["strength"] == 0.8

    def test_retrieve_with_relationships_no_related(self, llamaindex_retriever, mock_client, sample_memory_response):
        """Test retrieve_with_relationships() without including related."""
        # Setup
        memory = Memory(**sample_memory_response)
        mock_client.search_memories.return_value = [memory]

        # Execute
        nodes = llamaindex_retriever.retrieve_with_relationships(
            "test query",
            include_related=False
        )

        # Verify
        assert len(nodes) == 1
        # Should not have called get_related_memories
        mock_client.get_related_memories.assert_not_called()

    def test_retrieve_with_relationships_custom_depth(self, llamaindex_retriever, mock_client, sample_memory_response):
        """Test retrieve_with_relationships() with custom max_depth."""
        # Setup
        memory = Memory(**sample_memory_response)
        mock_client.search_memories.return_value = [memory]
        mock_client.get_related_memories.return_value = []

        # Execute
        llamaindex_retriever.retrieve_with_relationships(
            "test query",
            max_depth=2
        )

        # Verify
        call_args = mock_client.get_related_memories.call_args
        assert call_args.kwargs["max_depth"] == 2

    def test_retrieve_with_relationships_handles_errors(self, llamaindex_retriever, mock_client, sample_memory_response):
        """Test retrieve_with_relationships() gracefully handles NotFoundError and MemoryGraphError."""
        from memorygraphsdk.exceptions import NotFoundError
        # Setup
        memory = Memory(**sample_memory_response)
        mock_client.search_memories.return_value = [memory]
        # Simulate NotFoundError when getting relationships
        mock_client.get_related_memories.side_effect = NotFoundError("Memory not found")

        # Execute - should not raise
        nodes = llamaindex_retriever.retrieve_with_relationships("test query")

        # Verify - should return empty related list
        assert len(nodes) == 1
        assert nodes[0]["metadata"]["related"] == []

    def test_close(self, llamaindex_retriever, mock_client):
        """Test close() method."""
        llamaindex_retriever.close()
        mock_client.close.assert_called_once()

    def test_context_manager(self, api_key):
        """Test using retriever as a context manager."""
        mock_client = Mock()

        with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient") as MockClient:
            MockClient.return_value = mock_client

            with MemoryGraphRetriever(api_key=api_key) as retriever:
                assert retriever is not None

            # Should close on exit
            mock_client.close.assert_called_once()

    def test_context_manager_with_exception(self, api_key):
        """Test context manager closes even on exception."""
        mock_client = Mock()

        with patch("memorygraphsdk.integrations.llamaindex.MemoryGraphClient") as MockClient:
            MockClient.return_value = mock_client

            try:
                with MemoryGraphRetriever(api_key=api_key) as retriever:
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Should still close on exception
            mock_client.close.assert_called_once()
