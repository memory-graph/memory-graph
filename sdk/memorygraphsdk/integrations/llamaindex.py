"""
LlamaIndex integration for MemoryGraph.

Provides custom memory modules that integrate with LlamaIndex's
chat memory and retrieval systems.

This integration requires llama-index to be installed:
    pip install memorygraphsdk[llamaindex]
"""

from typing import Any

try:
    from llama_index.core.base.llms.types import ChatMessage, MessageRole
    from llama_index.core.bridge.pydantic import Field
    from llama_index.core.memory import BaseMemory

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    # Create stub classes for type checking
    BaseMemory = object  # type: ignore
    ChatMessage = dict  # type: ignore
    MessageRole = object  # type: ignore

    def Field(**kwargs: Any) -> Any:  # type: ignore  # noqa: N802
        """Stub for pydantic Field when llama-index not installed."""
        return None


from ..client import MemoryGraphClient
from ..exceptions import MemoryGraphError, NotFoundError


class MemoryGraphChatMemory(BaseMemory):
    """
    LlamaIndex chat memory backed by MemoryGraph.

    This memory module stores conversation history in MemoryGraph,
    enabling persistent memory across sessions and semantic search
    over conversation history.

    Usage:
        from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
        from llama_index.core.chat_engine import SimpleChatEngine

        memory = MemoryGraphChatMemory(api_key="mgraph_...")
        chat_engine = SimpleChatEngine.from_defaults(memory=memory)

    Args:
        api_key: Your MemoryGraph API key
        session_id: Unique identifier for this conversation session
        api_url: MemoryGraph API URL (default: https://api.memorygraph.dev)

    Example:
        memory = MemoryGraphChatMemory(
            api_key="mgraph_your_key_here",
            session_id="user-123-session"
        )
    """

    model_config = {"arbitrary_types_allowed": True}

    client: MemoryGraphClient = Field(exclude=True)
    session_id: str = Field(default="default")

    def __init__(
        self,
        api_key: str | None = None,
        session_id: str = "default",
        api_url: str = "https://api.memorygraph.dev",
        **kwargs: Any,
    ):
        """
        Initialize MemoryGraph chat memory.

        Args:
            api_key: MemoryGraph API key. If not provided, will look for
                MEMORYGRAPH_API_KEY environment variable.
            session_id: Session identifier for this conversation
            api_url: API URL (default: https://api.memorygraph.dev)
            **kwargs: Additional arguments passed to BaseMemory
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "llama-index is required for this integration. "
                "Install it with: pip install memorygraphsdk[llamaindex]"
            )

        super().__init__(**kwargs)
        # Use object.__setattr__ to bypass Pydantic's frozen model checks
        object.__setattr__(self, "client", MemoryGraphClient(api_key=api_key, api_url=api_url))
        object.__setattr__(self, "session_id", session_id)

    def get(self, input: str | None = None, **kwargs: Any) -> list[ChatMessage]:
        """
        Get relevant memories for the input.

        Args:
            input: Optional query to search for relevant memories
            **kwargs: Additional search parameters

        Returns:
            List of ChatMessage objects representing conversation history
        """
        # Build search parameters
        search_kwargs = {
            "tags": [f"session:{self.session_id}"],
            "memory_types": ["conversation"],
            "limit": kwargs.get("limit", 10),
        }

        # If input provided, search semantically
        if input:
            search_kwargs["query"] = input

        memories = self.client.search_memories(**search_kwargs)

        # Convert memories to ChatMessage format
        messages = []
        for m in sorted(memories, key=lambda x: x.created_at):
            role_str = m.context.get("role", "user") if m.context else "user"
            # Map role to MessageRole enum
            if role_str == "assistant" or role_str == "ai":
                role = MessageRole.ASSISTANT
            elif role_str == "system":
                role = MessageRole.SYSTEM
            else:
                role = MessageRole.USER

            messages.append(ChatMessage(role=role, content=m.content))

        return messages

    def get_all(self) -> list[ChatMessage]:
        """
        Get all messages in this session.

        Returns:
            List of all ChatMessage objects in chronological order
        """
        return self.get(input=None)

    def put(self, message: ChatMessage) -> None:
        """
        Store a message in memory.

        Args:
            message: ChatMessage to store
        """
        role = str(message.role.value) if hasattr(message.role, "value") else str(message.role)
        content = str(message.content)

        self.client.create_memory(
            type="conversation",
            title=f"{role}: {content[:50]}...",
            content=content,
            tags=[f"session:{self.session_id}", f"role:{role}", "llamaindex"],
            context={"role": role, "session_id": self.session_id},
        )

    def set(self, messages: list[ChatMessage]) -> None:
        """
        Set messages (overwrite existing memory).

        Note: MemoryGraph stores permanent memories, so this operation
        only adds new messages to the session. To start fresh, use a new session_id.

        Args:
            messages: List of ChatMessage objects to store
        """
        for message in messages:
            self.put(message)

    def reset(self) -> None:
        """
        Reset memory.

        Note: MemoryGraph stores permanent memories, so this is a no-op.
        To start a fresh conversation, create a new MemoryGraphChatMemory
        instance with a different session_id.
        """
        pass

    @classmethod
    def class_name(cls) -> str:
        """Return class name for serialization."""
        return "MemoryGraphChatMemory"

    @classmethod
    def from_defaults(
        cls,
        api_key: str | None = None,
        session_id: str = "default",
        api_url: str = "https://api.memorygraph.dev",
        **kwargs: Any,
    ) -> "MemoryGraphChatMemory":
        """
        Create a MemoryGraphChatMemory instance with default settings.

        This is the recommended way to create a memory instance.

        Args:
            api_key: MemoryGraph API key. If not provided, will look for
                MEMORYGRAPH_API_KEY environment variable.
            session_id: Session identifier for this conversation
            api_url: API URL (default: https://api.memorygraph.dev)
            **kwargs: Additional arguments passed to the constructor

        Returns:
            A new MemoryGraphChatMemory instance
        """
        return cls(
            api_key=api_key,
            session_id=session_id,
            api_url=api_url,
            **kwargs,
        )


class MemoryGraphRetriever:
    """
    LlamaIndex-compatible retriever using MemoryGraph.

    Enables using MemoryGraph as a knowledge base for RAG pipelines.
    Retrieves relevant memories based on semantic search.

    Usage:
        from memorygraphsdk.integrations.llamaindex import MemoryGraphRetriever

        retriever = MemoryGraphRetriever(api_key="mgraph_...")
        nodes = retriever.retrieve("What solved the timeout issue?")

    Args:
        api_key: Your MemoryGraph API key
        memory_types: Types of memories to retrieve (default: solution, code_pattern, fix)
        api_url: MemoryGraph API URL (default: https://api.memorygraph.dev)
        min_importance: Minimum importance score for retrieved memories (0.0-1.0)

    Example:
        # Retrieve solutions and patterns
        retriever = MemoryGraphRetriever(
            api_key="mgraph_your_key_here",
            memory_types=["solution", "code_pattern", "fix"],
            min_importance=0.5
        )
        nodes = retriever.retrieve("redis timeout", limit=5)
    """

    def __init__(
        self,
        api_key: str | None = None,
        memory_types: list[str] | None = None,
        api_url: str = "https://api.memorygraph.dev",
        min_importance: float | None = None,
    ):
        """
        Initialize MemoryGraph retriever.

        Args:
            api_key: MemoryGraph API key. If not provided, will look for
                MEMORYGRAPH_API_KEY environment variable.
            memory_types: Types of memories to retrieve
            api_url: API URL (default: https://api.memorygraph.dev)
            min_importance: Minimum importance threshold
        """
        self.client = MemoryGraphClient(api_key=api_key, api_url=api_url)
        self.memory_types = memory_types or ["solution", "code_pattern", "fix"]
        self.min_importance = min_importance

    def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Retrieve relevant memories as nodes.

        Args:
            query: Search query
            limit: Maximum number of results (default: 5)
            **kwargs: Additional search parameters

        Returns:
            List of node dictionaries with text, metadata, and score
        """
        # Build search parameters
        search_params = {
            "query": query,
            "memory_types": self.memory_types,
            "limit": limit,
        }

        if self.min_importance is not None:
            search_params["min_importance"] = self.min_importance

        # Allow override of parameters
        search_params.update(kwargs)

        memories = self.client.search_memories(**search_params)

        # Convert to LlamaIndex-compatible format
        nodes = []
        for m in memories:
            node = {
                "id": m.id,
                "text": f"# {m.title}\n\n{m.content}",
                "metadata": {
                    "memory_id": m.id,
                    "type": m.type,
                    "tags": m.tags,
                    "importance": m.importance,
                    "created_at": m.created_at.isoformat(),
                },
                "score": m.importance,  # Use importance as relevance score
            }
            if m.summary:
                node["metadata"]["summary"] = m.summary

            nodes.append(node)

        return nodes

    def retrieve_with_relationships(
        self,
        query: str,
        limit: int = 5,
        include_related: bool = True,
        max_depth: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Retrieve memories with their relationships.

        This advanced retrieval method fetches relevant memories and
        optionally includes related memories to provide richer context.

        Args:
            query: Search query
            limit: Maximum number of primary results
            include_related: Whether to include related memories
            max_depth: Maximum relationship depth to traverse
            **kwargs: Additional search parameters

        Returns:
            List of node dictionaries with relationships included in metadata
        """
        nodes = self.retrieve(query, limit=limit, **kwargs)

        if include_related:
            for node in nodes:
                memory_id = node["metadata"]["memory_id"]
                try:
                    related = self.client.get_related_memories(
                        memory_id=memory_id, max_depth=max_depth
                    )
                    node["metadata"]["related"] = [
                        {
                            "memory_id": r.memory.id,
                            "title": r.memory.title,
                            "relationship_type": r.relationship_type,
                            "strength": r.strength,
                        }
                        for r in related
                    ]
                except (NotFoundError, MemoryGraphError):
                    # If relationship retrieval fails, continue without them
                    node["metadata"]["related"] = []

        return nodes

    def close(self) -> None:
        """Close the underlying client connection."""
        self.client.close()

    def __enter__(self) -> "MemoryGraphRetriever":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self.close()


__all__ = ["MemoryGraphChatMemory", "MemoryGraphRetriever"]
