"""
CrewAI integration for MemoryGraph.

This module provides a memory backend for CrewAI agents that stores
memories in MemoryGraph, enabling persistent memory across sessions
and automatic relationship building.

Usage:
    from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
    from crewai import Agent, Task, Crew

    memory = MemoryGraphCrewMemory(api_key="mgraph_your_key_here")
    agent = Agent(
        role="Researcher",
        goal="Research and remember findings",
        memory=memory,
        verbose=True
    )
"""
from typing import TYPE_CHECKING, Any

from ..client import MemoryGraphClient

# Optional import - crewai may not be installed
if TYPE_CHECKING:
    try:
        from crewai.memory import Memory as CrewAIMemory
    except ImportError:
        CrewAIMemory = object  # type: ignore
else:
    try:
        from crewai.memory import Memory as CrewAIMemory
    except ImportError:
        # CrewAI not installed - create a placeholder base class
        class CrewAIMemory:  # type: ignore
            """Placeholder for CrewAI Memory when crewai is not installed."""
            pass


class MemoryGraphCrewMemory(CrewAIMemory):
    """
    CrewAI memory backed by MemoryGraph.

    This class implements the CrewAI Memory interface to store agent
    memories in MemoryGraph, providing:
    - Persistent memory across sessions
    - Semantic search capabilities
    - Automatic relationship tracking
    - Multi-agent memory sharing

    Args:
        api_key: Your MemoryGraph API key (starts with 'mgraph_')
        api_url: Base URL for the API (default: https://api.memorygraph.dev)
        crew_id: Optional identifier for the crew (for memory isolation)

    Example:
        >>> memory = MemoryGraphCrewMemory(api_key="mgraph_...")
        >>> agent = Agent(
        ...     role="Senior Researcher",
        ...     goal="Research best practices",
        ...     memory=memory,
        ...     verbose=True
        ... )
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.memorygraph.dev",
        crew_id: str = "default",
    ):
        """
        Initialize the MemoryGraph-backed CrewAI memory.

        Args:
            api_key: Your MemoryGraph API key
            api_url: MemoryGraph API URL (default: https://api.memorygraph.dev)
            crew_id: Identifier for this crew's memory space (default: "default")
        """
        self.client = MemoryGraphClient(api_key=api_key, api_url=api_url)
        self.crew_id = crew_id

    def save(
        self,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Save a memory to MemoryGraph.

        Args:
            key: A unique identifier or title for the memory
            value: The content to store
            metadata: Optional metadata including tags, importance, etc.

        Example:
            >>> memory.save(
            ...     "research_findings",
            ...     "Python async is better for I/O-bound tasks",
            ...     metadata={"tags": ["python", "async"], "importance": 0.8}
            ... )
        """
        metadata = metadata or {}

        # Extract metadata fields
        tags = metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        # Add crew identifier tag
        if self.crew_id not in tags:
            tags.append(f"crew:{self.crew_id}")

        importance = metadata.get("importance", 0.5)
        memory_type = metadata.get("type", "general")
        context = {k: v for k, v in metadata.items() if k not in ["tags", "importance", "type"]}
        if self.crew_id:
            context["crew_id"] = self.crew_id

        # Create the memory
        self.client.create_memory(
            type=memory_type,
            title=key,
            content=value,
            tags=tags,
            importance=importance,
            context=context if context else None,
        )

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search for memories using natural language query.

        Args:
            query: The search query
            limit: Maximum number of results to return (default: 10)

        Returns:
            List of memory dictionaries with keys: 'key', 'value', 'metadata'

        Example:
            >>> results = memory.search("python async patterns", limit=5)
            >>> for result in results:
            ...     print(f"{result['key']}: {result['value']}")
        """
        # Search with crew_id filter
        memories = self.client.search_memories(
            query=query,
            tags=[f"crew:{self.crew_id}"] if self.crew_id else None,
            limit=limit,
        )

        # Convert to CrewAI format
        return [
            {
                "key": memory.title,
                "value": memory.content,
                "metadata": {
                    "id": memory.id,
                    "type": memory.type,
                    "tags": memory.tags,
                    "importance": memory.importance,
                    "created_at": memory.created_at.isoformat(),
                    **(memory.context or {}),
                },
            }
            for memory in memories
        ]

    def get(self, key: str) -> str | None:
        """
        Get a specific memory by key (title).

        Args:
            key: The memory key/title to retrieve

        Returns:
            The memory content if found, None otherwise

        Example:
            >>> content = memory.get("research_findings")
            >>> if content:
            ...     print(content)
        """
        # Search for exact title match within crew
        memories = self.client.search_memories(
            query=key,
            tags=[f"crew:{self.crew_id}"] if self.crew_id else None,
            limit=1,
        )

        # Return content if we found a match with the exact title
        if memories and memories[0].title == key:
            return memories[0].content

        return None

    def clear(self) -> None:
        """
        Clear all memories for this crew.

        Note: MemoryGraph memories are designed to be persistent.
        This method is provided for interface compatibility but
        does not actually delete memories. To delete memories,
        use the MemoryGraph client directly.
        """
        # CrewAI interface requires this method, but we don't implement
        # automatic deletion as MemoryGraph memories are meant to be persistent.
        # Users can manually delete via the client if needed.
        pass

    def reset(self) -> None:
        """
        Reset the memory state.

        Alias for clear() to match CrewAI's interface.
        """
        self.clear()

    def close(self) -> None:
        """
        Close the MemoryGraph client connection.

        Should be called when done using the memory to clean up resources.

        Example:
            >>> memory = MemoryGraphCrewMemory(api_key="...")
            >>> try:
            ...     # Use memory
            ...     pass
            ... finally:
            ...     memory.close()
        """
        self.client.close()

    def __enter__(self) -> "MemoryGraphCrewMemory":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and close client."""
        self.close()
