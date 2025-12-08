"""
LangChain integration for MemoryGraph.

Provides BaseMemory implementation that stores conversation history
in MemoryGraph for persistent, searchable memory across sessions.

Usage:
    from memorygraphsdk.integrations.langchain import MemoryGraphMemory
    from langchain.chains import ConversationChain
    from langchain_openai import ChatOpenAI

    memory = MemoryGraphMemory(api_key="mgraph_...")
    llm = ChatOpenAI()
    chain = ConversationChain(llm=llm, memory=memory)

    response = chain.run("Hi, I'm working on a Redis timeout issue")
    # Memory is automatically saved to MemoryGraph

Note: Requires langchain to be installed:
    pip install memorygraphsdk[langchain]
    # or
    pip install langchain
"""
from typing import Any

try:
    from langchain.schema import AIMessage, BaseMessage, HumanMessage
    from langchain.schema.memory import BaseMemory

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseMemory = object  # type: ignore
    BaseMessage = object  # type: ignore
    HumanMessage = object  # type: ignore
    AIMessage = object  # type: ignore

from ..client import MemoryGraphClient


class MemoryGraphMemory(BaseMemory):
    """
    LangChain memory backed by MemoryGraph.

    Stores conversation history as memories in MemoryGraph, enabling:
    - Persistent memory across sessions
    - Searchable conversation history
    - Memory sharing across agents
    - Relationship tracking between conversations

    Args:
        api_key: MemoryGraph API key (required)
        api_url: MemoryGraph API URL (default: https://api.memorygraph.dev)
        session_id: Session identifier for grouping conversations (default: "default")
        memory_key: Key name for memory variable in chain (default: "history")
        return_messages: Return as Message objects vs strings (default: False)
        input_key: Key for user input in chain (default: "input")
        output_key: Key for AI output in chain (default: "output")

    Example:
        >>> from memorygraphsdk.integrations.langchain import MemoryGraphMemory
        >>> from langchain.chains import ConversationChain
        >>> from langchain_openai import ChatOpenAI
        >>>
        >>> memory = MemoryGraphMemory(
        ...     api_key="mgraph_...",
        ...     session_id="user-123",
        ...     return_messages=True
        ... )
        >>> llm = ChatOpenAI()
        >>> chain = ConversationChain(llm=llm, memory=memory)
        >>>
        >>> response = chain.run("What is Redis?")
        >>> # Conversation is saved to MemoryGraph automatically
    """

    client: MemoryGraphClient
    session_id: str
    memory_key: str
    return_messages: bool
    input_key: str
    output_key: str

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.memorygraph.dev",
        session_id: str = "default",
        memory_key: str = "history",
        return_messages: bool = False,
        input_key: str = "input",
        output_key: str = "output",
    ):
        """Initialize LangChain memory with MemoryGraph backend."""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. "
                "Install it with: pip install memorygraphsdk[langchain]"
            )

        # Initialize using object.__setattr__ to bypass Pydantic validation
        # This is necessary because BaseMemory uses Pydantic v1 compatibility
        object.__setattr__(self, "client", MemoryGraphClient(api_key=api_key, api_url=api_url))
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "memory_key", memory_key)
        object.__setattr__(self, "return_messages", return_messages)
        object.__setattr__(self, "input_key", input_key)
        object.__setattr__(self, "output_key", output_key)

    @property
    def memory_variables(self) -> list[str]:
        """
        Return memory variables.

        LangChain uses this to determine what variables this memory provides.
        """
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Load conversation history from MemoryGraph.

        Args:
            inputs: Input dictionary (can be used for filtering)

        Returns:
            Dictionary with memory_key containing history (messages or string)
        """
        # Search for conversation memories in this session
        memories = self.client.search_memories(
            tags=[f"session:{self.session_id}"],
            memory_types=["conversation"],
            limit=50,  # Load last 50 messages
        )

        # Sort by creation time to maintain conversation order
        memories.sort(key=lambda m: m.created_at)

        if self.return_messages:
            # Return as LangChain Message objects
            messages: list[BaseMessage] = []
            for memory in memories:
                role = memory.context.get("role") if memory.context else "human"
                if role == "human":
                    messages.append(HumanMessage(content=memory.content))
                elif role == "ai":
                    messages.append(AIMessage(content=memory.content))
                else:
                    # Default to human message for unknown roles
                    messages.append(HumanMessage(content=memory.content))

            return {self.memory_key: messages}
        else:
            # Return as formatted string
            if not memories:
                return {self.memory_key: ""}

            history_lines = []
            for memory in memories:
                role = memory.context.get("role") if memory.context else "human"
                role_label = "Human" if role == "human" else "AI"
                history_lines.append(f"{role_label}: {memory.content}")

            return {self.memory_key: "\n".join(history_lines)}

    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """
        Save conversation turn to MemoryGraph.

        Args:
            inputs: Input dictionary containing user input
            outputs: Output dictionary containing AI response
        """
        # Extract input and output using configured keys
        user_input = inputs.get(self.input_key, "")
        ai_output = outputs.get(self.output_key, "")

        # Save user input as a memory
        if user_input:
            self.client.create_memory(
                type="conversation",
                title=f"User: {user_input[:50]}{'...' if len(user_input) > 50 else ''}",
                content=user_input,
                tags=[f"session:{self.session_id}", "role:human"],
                context={"role": "human", "session_id": self.session_id},
                importance=0.5,
            )

        # Save AI output as a memory
        if ai_output:
            self.client.create_memory(
                type="conversation",
                title=f"AI: {ai_output[:50]}{'...' if len(ai_output) > 50 else ''}",
                content=ai_output,
                tags=[f"session:{self.session_id}", "role:ai"],
                context={"role": "ai", "session_id": self.session_id},
                importance=0.5,
            )

    def clear(self) -> None:
        """
        Clear session history.

        Note: MemoryGraph stores memories permanently by design.
        This method is a no-op to maintain LangChain interface compatibility.
        To start a fresh conversation, use a new session_id.
        """
        pass


# Export for convenience
__all__ = ["MemoryGraphMemory"]
