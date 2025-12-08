"""
AutoGen integration for MemoryGraph.

Provides message history storage for AutoGen agents backed by MemoryGraph.
This allows AutoGen conversations to persist across sessions.

Example:
    from memorygraphsdk.integrations.autogen import MemoryGraphAutoGenHistory

    history = MemoryGraphAutoGenHistory(api_key="mgraph_...")

    # Store messages
    history.add_message("user", "Hello, I need help with Redis")
    history.add_message("assistant", "I'd be happy to help with Redis!")

    # Retrieve conversation history
    messages = history.get_messages()
"""
from typing import Any

try:
    import pyautogen  # noqa: F401
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

from ..client import MemoryGraphClient


class MemoryGraphAutoGenHistory:
    """
    Message history for AutoGen backed by MemoryGraph.

    This class provides persistent conversation storage for AutoGen agents.
    Messages are stored as memories with conversation context and can be
    retrieved across sessions.

    Args:
        api_key: MemoryGraph API key
        conversation_id: Unique identifier for this conversation (default: "default")
        api_url: Optional custom API URL

    Usage:
        history = MemoryGraphAutoGenHistory(api_key="mgraph_...")

        # In your AutoGen workflow
        agent = autogen.AssistantAgent(
            name="assistant",
            system_message="You are a helpful assistant",
        )

        # After each message exchange
        history.add_message("user", user_input)
        history.add_message("assistant", agent_response)

        # Retrieve history
        messages = history.get_messages()

    Note:
        This integration requires pyautogen to be installed:
            pip install memorygraphsdk[autogen]

        However, the integration can be used standalone without importing
        pyautogen if you're just using it for message storage.
    """

    def __init__(
        self,
        api_key: str,
        conversation_id: str = "default",
        api_url: str = "https://api.memorygraph.dev"
    ):
        """
        Initialize AutoGen history backed by MemoryGraph.

        Args:
            api_key: Your MemoryGraph API key
            conversation_id: Unique conversation identifier
            api_url: MemoryGraph API URL (default: https://api.memorygraph.dev)
        """
        self.client = MemoryGraphClient(api_key=api_key, api_url=api_url)
        self.conversation_id = conversation_id

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: Message role (e.g., 'user', 'assistant', 'system')
            content: Message content
            metadata: Optional additional metadata to store with the message

        Example:
            history.add_message(
                "user",
                "How do I fix a Redis timeout?",
                metadata={"timestamp": "2025-12-08T10:30:00"}
            )
        """
        # Prepare context with role and conversation info
        context: dict[str, Any] = {
            "role": role,
            "conversation_id": self.conversation_id,
        }

        # Merge in any additional metadata
        if metadata:
            context.update(metadata)

        # Create memory for this message
        self.client.create_memory(
            type="conversation",
            title=f"{role}: {content[:50]}{'...' if len(content) > 50 else ''}",
            content=content,
            tags=[
                f"conversation:{self.conversation_id}",
                f"role:{role}",
                "autogen"
            ],
            context=context,
            importance=0.5  # Conversation messages have standard importance
        )

    def get_messages(self, limit: int = 100) -> list[dict[str, str]]:
        """
        Get conversation history.

        Returns messages sorted chronologically (oldest first) in the format
        expected by most chat frameworks.

        Args:
            limit: Maximum number of messages to retrieve (default: 100)

        Returns:
            List of message dictionaries with 'role' and 'content' keys

        Example:
            messages = history.get_messages(limit=50)
            for msg in messages:
                print(f"{msg['role']}: {msg['content']}")
        """
        # Search for all messages in this conversation
        memories = self.client.search_memories(
            tags=[f"conversation:{self.conversation_id}"],
            limit=limit
        )

        # Sort by creation time (oldest first) and convert to message format
        sorted_memories = sorted(memories, key=lambda m: m.created_at)

        return [
            {
                "role": m.context.get("role", "unknown") if m.context else "unknown",
                "content": m.content
            }
            for m in sorted_memories
        ]

    def clear(self) -> None:
        """
        Clear conversation history.

        Note:
            This is a no-op in the current implementation as MemoryGraph
            maintains permanent memory storage. To start a new conversation,
            create a new MemoryGraphAutoGenHistory instance with a different
            conversation_id.

        Example:
            # Instead of clearing, start a new conversation
            new_history = MemoryGraphAutoGenHistory(
                api_key=api_key,
                conversation_id="conversation_2"
            )
        """
        # MemoryGraph uses permanent storage by design
        # To "clear" history, use a new conversation_id
        pass

    def close(self) -> None:
        """
        Close the underlying HTTP client.

        Call this when you're done using the history object to clean up
        resources properly.

        Example:
            history = MemoryGraphAutoGenHistory(api_key="...")
            try:
                history.add_message("user", "Hello")
            finally:
                history.close()
        """
        self.client.close()

    def __enter__(self) -> "MemoryGraphAutoGenHistory":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and close client."""
        self.close()


# Provide helpful error message if AutoGen is not available
def _check_autogen_available() -> None:
    """Check if pyautogen is available and raise helpful error if not."""
    if not AUTOGEN_AVAILABLE:
        raise ImportError(
            "AutoGen integration requires pyautogen to be installed.\n"
            "Install with: pip install memorygraphsdk[autogen]\n"
            "Or: pip install pyautogen"
        )


__all__ = ["MemoryGraphAutoGenHistory"]
