# Workplan 16: SDK Development (v1.0.0)

> 🚧 **STATUS: IN PROGRESS** (2025-12-08)
>
> **Section 1 (SDK Core)**: ✅ COMPLETE - 23 tests passing
> **Section 2-5 (Integrations)**: 🔄 IN PROGRESS - 4 parallel agents working
>
> **Priority Update (2025-12-08)**: LlamaIndex and LangChain elevated to 🔴 CRITICAL per PRODUCT_ROADMAP.md

**Version Target**: v1.0.0
**Priority**: 🔴 CRITICAL (Competitive Differentiation) - DEFERRED
**Prerequisites**:
- Workplans 14-15 complete (Cloud API + Auth) - in memorygraph.dev
- WP20 (Cloud Backend) release complete
**Estimated Effort**: 12-16 hours

---

## Parallel Execution Guide

This workplan can be executed with **4 parallel agents** after Section 1 (SDK Core) is complete.

### Dependency Graph

```
Section 1: SDK Core (SEQUENTIAL - must complete first)
    │
    ├──► Section 2: LlamaIndex ──┐
    │                            │
    ├──► Section 3: LangChain ───┼──► Section 6: Testing ──► Section 7: Docs ──► Section 8: Publishing
    │                            │
    ├──► Section 4: CrewAI ──────┤
    │                            │
    └──► Section 5: AutoGen ─────┘
```

### Parallel Work Units

| Agent | Section | Dependencies | Can Run With |
|-------|---------|--------------|--------------|
| **Agent 1** | Section 1: SDK Core | None | Solo (prerequisite) |
| **Agent 2** | Section 2: LlamaIndex | Section 1 | Agents 3, 4, 5 |
| **Agent 3** | Section 3: LangChain | Section 1 | Agents 2, 4, 5 |
| **Agent 4** | Section 4: CrewAI | Section 1 | Agents 2, 3, 5 |
| **Agent 5** | Section 5: AutoGen | Section 1 | Agents 2, 3, 4 |
| **Agent 6** | Section 6: Testing | Sections 2-5 | Solo (integration) |
| **Agent 7** | Section 7: Documentation | Section 6 | Agent 8 |
| **Agent 8** | Section 8: Publishing | Section 6 | Agent 7 |
| **Agent 9** | Section 9: Marketing | Section 8 | Solo |

### Recommended Execution Order

**Phase A** (1 agent): Section 1 - SDK Core setup
**Phase B** (4 agents parallel): Sections 2, 3, 4, 5 - Framework integrations
**Phase C** (1 agent): Section 6 - Integration testing
**Phase D** (2 agents parallel): Sections 7, 8 - Docs and publishing
**Phase E** (1 agent): Section 9 - Marketing

---

## Overview

Create `memorygraphsdk` - a Python SDK for integrating MemoryGraph with agent frameworks. This differentiates us from Cipher (MCP-only).

**Philosophy**: MCP is great for Claude, but other frameworks need native integrations. Our SDK makes MemoryGraph the universal memory layer.

---

## Integration Priorities (Updated 2025-12-08)

| # | Integration | Priority | Rationale |
|---|-------------|----------|-----------|
| 1 | **LlamaIndex** | 🔴 Critical | Dominant in RAG/retrieval - perfect fit for memory-graph |
| 2 | **LangChain/LangGraph** | 🔴 Critical | Massive ecosystem (100K+ stars) - huge market capture |
| 3 | **CrewAI** | 🟡 Medium | Multi-agent workflows, growing ecosystem |
| 4 | **AutoGen** | 🟢 Low | Microsoft ecosystem, smaller adoption |

---

## Goal

Python SDK that works with:
- MCP (already supported)
- **LlamaIndex** (MemoryVectorStore integration) - 🔴 CRITICAL
- **LangChain** (BaseMemory integration) - 🔴 CRITICAL
- CrewAI (Memory interface) - 🟡 MEDIUM
- AutoGen (message history) - 🟢 LOW
- Direct API usage (for custom integrations)

---

## Success Criteria

- [ ] SDK package published to PyPI as `memorygraphsdk`
- [ ] **LlamaIndex integration working** (🔴 Critical)
- [ ] **LangChain integration working** (🔴 Critical)
- [ ] CrewAI integration working (🟡 Medium - can defer)
- [ ] Comprehensive documentation with examples
- [ ] 30+ tests passing
- [ ] Type hints and docstrings for all public APIs

---

## Section 1: SDK Core

### 1.1 Project Structure

```
memorygraphsdk/
├── memorygraphsdk/
│   ├── __init__.py
│   ├── client.py           # Core API client
│   ├── models.py           # Pydantic models
│   ├── sync.py             # Synchronous client
│   ├── async_.py           # Async client
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── llamaindex.py   # LlamaIndex integration (🔴 CRITICAL)
│   │   ├── langchain.py    # LangChain memory (🔴 CRITICAL)
│   │   ├── crewai.py       # CrewAI memory (🟡 MEDIUM)
│   │   └── autogen.py      # AutoGen history (🟢 LOW)
│   └── exceptions.py
├── tests/
├── docs/
├── examples/
├── pyproject.toml
└── README.md
```

**Tasks**:
- [x] Create repository: `memorygraph-sdk` (or in monorepo under `/sdk`)
- [x] Set up project structure
- [x] Configure Poetry or setuptools
- [ ] Add pre-commit hooks (black, mypy, ruff)

### 1.2 Core Client

**File**: `/Users/gregorydickson/claude-code-memory/sdk/memorygraphsdk/client.py`

```python
"""
Core MemoryGraph client.
"""
from typing import List, Optional, Dict, Any
import httpx
from .models import Memory, Relationship, SearchResult
from .exceptions import MemoryGraphError, AuthenticationError


class MemoryGraphClient:
    """
    Synchronous client for MemoryGraph API.

    Usage:
        client = MemoryGraphClient(api_key="mgraph_...")
        memory = client.create_memory(
            type="solution",
            title="Fixed timeout with retry",
            content="...",
            tags=["redis", "timeout"]
        )
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.memorygraph.dev"
    ):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )

    def create_memory(
        self,
        type: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        **kwargs
    ) -> Memory:
        """Create a new memory."""
        response = self.client.post(
            f"{self.api_url}/api/v1/memories",
            json={
                "type": type,
                "title": title,
                "content": content,
                "tags": tags or [],
                "importance": importance,
                **kwargs
            }
        )
        self._check_response(response)
        return Memory(**response.json())

    def search_memories(
        self,
        query: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        **kwargs
    ) -> List[Memory]:
        """Search memories."""
        params = {
            "query": query,
            "memory_types": memory_types,
            "tags": tags,
            "limit": limit,
            **kwargs
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        response = self.client.get(
            f"{self.api_url}/api/v1/memories",
            params=params
        )
        self._check_response(response)
        return [Memory(**m) for m in response.json()["memories"]]

    def get_memory(self, memory_id: str) -> Memory:
        """Get memory by ID."""
        response = self.client.get(
            f"{self.api_url}/api/v1/memories/{memory_id}"
        )
        self._check_response(response)
        return Memory(**response.json())

    def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: str,
        **kwargs
    ) -> Relationship:
        """Create a relationship between memories."""
        response = self.client.post(
            f"{self.api_url}/api/v1/relationships",
            json={
                "from_memory_id": from_memory_id,
                "to_memory_id": to_memory_id,
                "relationship_type": relationship_type,
                **kwargs
            }
        )
        self._check_response(response)
        return Relationship(**response.json())

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _check_response(self, response: httpx.Response):
        """Check response status and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 429:
            raise MemoryGraphError("Rate limit exceeded")
        elif response.status_code >= 400:
            raise MemoryGraphError(
                f"API error: {response.status_code} - {response.text}"
            )
```

**Tasks**:
- [x] Implement synchronous client
- [x] Implement all CRUD operations
- [x] Add proper error handling
- [x] Add context manager support
- [x] Add type hints
- [x] Add docstrings

### 1.3 Async Client

**File**: `/Users/gregorydickson/claude-code-memory/sdk/memorygraphsdk/async_.py`

```python
"""
Async client for MemoryGraph API.
"""
import httpx
from typing import List, Optional
from .models import Memory, Relationship


class AsyncMemoryGraphClient:
    """
    Asynchronous client for MemoryGraph API.

    Usage:
        async with AsyncMemoryGraphClient(api_key="...") as client:
            memory = await client.create_memory(...)
    """

    def __init__(self, api_key: str, api_url: str = "https://api.memorygraph.dev"):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )

    async def create_memory(self, **kwargs) -> Memory:
        """Create a new memory."""
        response = await self.client.post(
            f"{self.api_url}/api/v1/memories",
            json=kwargs
        )
        self._check_response(response)
        return Memory(**response.json())

    async def search_memories(self, **kwargs) -> List[Memory]:
        """Search memories."""
        # Similar to sync version
        pass

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
```

**Tasks**:
- [x] Implement async client (mirror sync client)
- [x] Use httpx.AsyncClient
- [x] Add async context manager
- [ ] Test async operations

### 1.4 Models

**File**: `/Users/gregorydickson/claude-code-memory/sdk/memorygraphsdk/models.py`

```python
"""
Pydantic models for MemoryGraph SDK.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    TASK = "task"
    CODE_PATTERN = "code_pattern"
    PROBLEM = "problem"
    SOLUTION = "solution"
    PROJECT = "project"
    TECHNOLOGY = "technology"
    ERROR = "error"
    FIX = "fix"
    COMMAND = "command"
    FILE_CONTEXT = "file_context"
    WORKFLOW = "workflow"
    GENERAL = "general"


class Memory(BaseModel):
    """Memory model."""
    id: str
    type: MemoryType
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    importance: float = 0.5
    context: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class Relationship(BaseModel):
    """Relationship model."""
    id: str
    from_memory_id: str
    to_memory_id: str
    relationship_type: str
    strength: float = 0.5
    confidence: float = 0.8
    created_at: datetime
```

**Tasks**:
- [x] Create Pydantic models for all API types
- [x] Add validation
- [x] Add JSON serialization helpers
- [x] Add type hints

---

## Section 2: LlamaIndex Integration (🔴 CRITICAL)

> **Priority**: This is the #1 integration priority per PRODUCT_ROADMAP.md

### 2.1 LlamaIndex Memory Store

**File**: `/Users/gregorydickson/claude-code-memory/sdk/memorygraphsdk/integrations/llamaindex.py`

```python
"""
LlamaIndex integration for MemoryGraph.

Provides a custom memory module that integrates with LlamaIndex's
chat memory and retrieval systems.
"""
from typing import Any, Dict, List, Optional
from llama_index.core.memory import BaseMemory
from llama_index.core.bridge.pydantic import Field
from ..client import MemoryGraphClient


class MemoryGraphChatMemory(BaseMemory):
    """
    LlamaIndex chat memory backed by MemoryGraph.

    Usage:
        from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
        from llama_index.core.chat_engine import SimpleChatEngine

        memory = MemoryGraphChatMemory(api_key="mgraph_...")
        chat_engine = SimpleChatEngine.from_defaults(memory=memory)
    """

    client: MemoryGraphClient = Field(exclude=True)
    session_id: str = Field(default="default")

    def __init__(self, api_key: str, session_id: str = "default", **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'client', MemoryGraphClient(api_key=api_key))
        self.session_id = session_id

    def get(self, input: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get relevant memories for the input."""
        if input:
            memories = self.client.search_memories(
                query=input,
                tags=[f"session:{self.session_id}"],
                limit=10
            )
        else:
            memories = self.client.search_memories(
                tags=[f"session:{self.session_id}"],
                limit=10
            )

        return [
            {"role": m.context.get("role", "user"), "content": m.content}
            for m in memories
        ]

    def put(self, message: Dict[str, Any]) -> None:
        """Store a message in memory."""
        role = message.get("role", "user")
        content = message.get("content", "")

        self.client.create_memory(
            type="conversation",
            title=f"{role}: {content[:50]}...",
            content=content,
            tags=[f"session:{self.session_id}", f"role:{role}"],
            context={"role": role, "session_id": self.session_id}
        )

    def reset(self) -> None:
        """Reset memory (no-op - memories are permanent)."""
        pass

    @classmethod
    def class_name(cls) -> str:
        return "MemoryGraphChatMemory"


class MemoryGraphRetriever:
    """
    LlamaIndex-compatible retriever using MemoryGraph.

    Enables using MemoryGraph as a knowledge base for RAG pipelines.

    Usage:
        from memorygraphsdk.integrations.llamaindex import MemoryGraphRetriever

        retriever = MemoryGraphRetriever(api_key="mgraph_...")
        nodes = retriever.retrieve("What solved the timeout issue?")
    """

    def __init__(self, api_key: str, memory_types: List[str] = None):
        self.client = MemoryGraphClient(api_key=api_key)
        self.memory_types = memory_types or ["solution", "code_pattern", "fix"]

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant memories as nodes."""
        memories = self.client.search_memories(
            query=query,
            memory_types=self.memory_types,
            limit=limit
        )

        # Convert to LlamaIndex-compatible format
        return [
            {
                "id": m.id,
                "text": f"{m.title}\n\n{m.content}",
                "metadata": {
                    "type": m.type,
                    "tags": m.tags,
                    "importance": m.importance
                },
                "score": m.importance  # Use importance as relevance score
            }
            for m in memories
        ]
```

**Tasks**:
- [x] Implement LlamaIndex BaseMemory interface
- [x] Implement MemoryGraphRetriever for RAG pipelines
- [x] Support both chat memory and retrieval use cases
- [ ] Test with LlamaIndex chat engines
- [x] Add example usage

### 2.2 LlamaIndex Example

**File**: `sdk/examples/llamaindex_example.py`

```python
"""
Example: Using MemoryGraph with LlamaIndex.
"""
from llama_index.core import Settings
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.llms.openai import OpenAI
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory

# Configure LlamaIndex
Settings.llm = OpenAI(model="gpt-4")

# Create memory
memory = MemoryGraphChatMemory(api_key="mgraph_your_key_here")

# Create chat engine with memory
chat_engine = SimpleChatEngine.from_defaults(memory=memory)

# Have a conversation
response = chat_engine.chat("I'm working on a Redis timeout issue")
print(response)

response = chat_engine.chat("What was I just working on?")
print(response)  # Should remember Redis timeout
```

**Tasks**:
- [x] Create working example
- [ ] Test with OpenAI
- [x] Add RAG example with MemoryGraphRetriever
- [ ] Test memory persistence across sessions

---

## Section 3: LangChain Integration (🔴 CRITICAL)

### 3.1 LangChain Memory Class

**File**: `/Users/gregorydickson/claude-code-memory/sdk/memorygraphsdk/integrations/langchain.py`

```python
"""
LangChain integration for MemoryGraph.
"""
from typing import Any, Dict, List
from langchain.schema import BaseMemory
from ..client import MemoryGraphClient


class MemoryGraphMemory(BaseMemory):
    """
    LangChain memory backed by MemoryGraph.

    Usage:
        from memorygraphsdk.integrations.langchain import MemoryGraphMemory

        memory = MemoryGraphMemory(api_key="mgraph_...")
        chain = ConversationChain(memory=memory, llm=llm)
    """

    client: MemoryGraphClient
    session_id: str = "default"
    memory_key: str = "history"
    return_messages: bool = False

    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.client = MemoryGraphClient(api_key=api_key)

    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load conversation history from MemoryGraph."""
        # Search for conversation memories
        memories = self.client.search_memories(
            tags=[f"session:{self.session_id}"],
            memory_types=["conversation"],
            limit=10
        )

        if self.return_messages:
            # Return as message objects
            from langchain.schema import HumanMessage, AIMessage
            messages = []
            for m in memories:
                if m.context.get("role") == "human":
                    messages.append(HumanMessage(content=m.content))
                else:
                    messages.append(AIMessage(content=m.content))
            return {self.memory_key: messages}
        else:
            # Return as string
            history = "\n".join([f"{m.title}: {m.content}" for m in memories])
            return {self.memory_key: history}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save conversation turn to MemoryGraph."""
        # Save user input
        self.client.create_memory(
            type="conversation",
            title=f"User: {inputs.get('input', '')[:50]}",
            content=inputs.get("input", ""),
            tags=[f"session:{self.session_id}", "role:human"],
            context={"role": "human", "session_id": self.session_id}
        )

        # Save AI output
        self.client.create_memory(
            type="conversation",
            title=f"AI: {outputs.get('output', '')[:50]}",
            content=outputs.get("output", ""),
            tags=[f"session:{self.session_id}", "role:ai"],
            context={"role": "ai", "session_id": self.session_id}
        )

    def clear(self) -> None:
        """Clear session history (not implemented - memories are permanent)."""
        pass
```

**Tasks**:
- [x] Implement LangChain BaseMemory interface
- [x] Support both message and string formats
- [x] Add session management
- [ ] Test with LangChain chains
- [x] Add example usage

### 3.2 LangChain Example

**File**: `sdk/examples/langchain_example.py`

```python
"""
Example: Using MemoryGraph with LangChain.
"""
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from memorygraphsdk.integrations.langchain import MemoryGraphMemory

# Create memory
memory = MemoryGraphMemory(api_key="mgraph_your_key_here")

# Create chain
llm = OpenAI(temperature=0.7)
chain = ConversationChain(llm=llm, memory=memory)

# Have a conversation
response = chain.run("Hi, I'm working on a Redis timeout issue")
print(response)

response = chain.run("What did I just say?")
print(response)  # Should remember Redis timeout
```

**Tasks**:
- [x] Create working example
- [ ] Test with OpenAI
- [ ] Add to documentation
- [ ] Test memory persistence across sessions

---

## Section 4: CrewAI Integration (🟡 MEDIUM)

### 4.1 CrewAI Memory Implementation

**File**: `/Users/gregorydickson/claude-code-memory/sdk/memorygraphsdk/integrations/crewai.py`

```python
"""
CrewAI integration for MemoryGraph.
"""
from typing import Optional, List, Dict, Any
from crewai.memory import Memory as CrewAIMemory
from ..client import MemoryGraphClient


class MemoryGraphCrewMemory(CrewAIMemory):
    """
    CrewAI memory backed by MemoryGraph.

    Usage:
        from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory

        memory = MemoryGraphCrewMemory(api_key="mgraph_...")
        agent = Agent(memory=memory, ...)
    """

    def __init__(self, api_key: str):
        self.client = MemoryGraphClient(api_key=api_key)

    def save(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None):
        """Save a memory."""
        self.client.create_memory(
            type="general",
            title=key,
            content=value,
            tags=metadata.get("tags", []) if metadata else [],
            context=metadata or {}
        )

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories."""
        memories = self.client.search_memories(query=query, limit=limit)
        return [
            {
                "key": m.title,
                "value": m.content,
                "metadata": m.context or {}
            }
            for m in memories
        ]

    def get(self, key: str) -> Optional[str]:
        """Get a specific memory by key."""
        memories = self.client.search_memories(query=key, limit=1)
        return memories[0].content if memories else None
```

**Tasks**:
- [x] Implement CrewAI Memory interface
- [ ] Test with CrewAI agents
- [x] Add example
- [ ] Document in README

### 4.2 CrewAI Example

**File**: `sdk/examples/crewai_example.py`

```python
"""
Example: Using MemoryGraph with CrewAI.
"""
from crewai import Agent, Task, Crew
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory

# Create memory
memory = MemoryGraphCrewMemory(api_key="mgraph_your_key_here")

# Create agent with memory
researcher = Agent(
    role="Senior Researcher",
    goal="Research topics and remember findings",
    memory=memory,
    verbose=True
)

# Create task
task = Task(
    description="Research best practices for Python async programming",
    agent=researcher
)

# Execute
crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
print(result)
```

**Tasks**:
- [x] Create working example
- [ ] Test with CrewAI
- [ ] Add to documentation

---

## Section 5: AutoGen Integration (🟢 LOW)

### 5.1 AutoGen Message History

**File**: `/Users/gregorydickson/claude-code-memory/sdk/memorygraphsdk/integrations/autogen.py`

```python
"""
AutoGen integration for MemoryGraph.
"""
from typing import List, Dict, Any
from ..client import MemoryGraphClient


class MemoryGraphAutoGenHistory:
    """
    Message history for AutoGen backed by MemoryGraph.

    Usage:
        history = MemoryGraphAutoGenHistory(api_key="mgraph_...")
        agent = autogen.AssistantAgent(
            name="assistant",
            system_message="You are a helpful assistant",
        )
        # Save messages to history after each turn
    """

    def __init__(self, api_key: str, conversation_id: str = "default"):
        self.client = MemoryGraphClient(api_key=api_key)
        self.conversation_id = conversation_id

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to history."""
        self.client.create_memory(
            type="conversation",
            title=f"{role}: {content[:50]}",
            content=content,
            tags=[f"conversation:{self.conversation_id}", f"role:{role}"],
            context={"role": role, "conversation_id": self.conversation_id, **(metadata or {})}
        )

    def get_messages(self, limit: int = 100) -> List[Dict[str, str]]:
        """Get conversation history."""
        memories = self.client.search_memories(
            tags=[f"conversation:{self.conversation_id}"],
            limit=limit
        )

        return [
            {
                "role": m.context.get("role", "unknown"),
                "content": m.content
            }
            for m in sorted(memories, key=lambda m: m.created_at)
        ]

    def clear(self):
        """Clear history (not implemented - memories are permanent)."""
        pass
```

**Tasks**:
- [x] Implement AutoGen message history
- [ ] Test with AutoGen agents
- [x] Add example
- [x] Document integration

---

## Section 6: Testing

### 6.1 Unit Tests

**File**: `sdk/tests/test_client.py`

```python
"""Tests for MemoryGraph client."""
import pytest
from memorygraphsdk import MemoryGraphClient
from memorygraphsdk.exceptions import AuthenticationError


def test_create_memory(client):
    """Test creating a memory."""
    memory = client.create_memory(
        type="solution",
        title="Test memory",
        content="Test content",
        tags=["test"]
    )
    assert memory.id is not None
    assert memory.title == "Test memory"


def test_search_memories(client):
    """Test searching memories."""
    memories = client.search_memories(query="test", limit=10)
    assert isinstance(memories, list)


def test_invalid_api_key():
    """Test authentication error."""
    client = MemoryGraphClient(api_key="invalid")
    with pytest.raises(AuthenticationError):
        client.search_memories()


@pytest.fixture
def client():
    """Test client fixture."""
    return MemoryGraphClient(api_key=os.getenv("MEMORYGRAPH_API_KEY"))
```

**Tasks**:
- [ ] Write unit tests for all client methods
- [ ] Test error handling
- [ ] Test authentication
- [ ] Mock HTTP responses for faster tests
- [ ] Achieve 90%+ coverage

### 6.2 Integration Tests

**File**: `sdk/tests/test_integrations.py`

```python
"""Tests for framework integrations."""
import pytest
from memorygraphsdk.integrations.langchain import MemoryGraphMemory


def test_langchain_memory():
    """Test LangChain integration."""
    memory = MemoryGraphMemory(api_key=os.getenv("MEMORYGRAPH_API_KEY"))

    # Save context
    memory.save_context(
        {"input": "Hello"},
        {"output": "Hi there!"}
    )

    # Load memory
    variables = memory.load_memory_variables({})
    assert "history" in variables
```

**Tasks**:
- [ ] Test LangChain integration
- [ ] Test CrewAI integration
- [ ] Test AutoGen integration
- [ ] Test end-to-end workflows

---

## Section 7: Documentation

### 7.1 SDK README

**File**: `sdk/README.md`

```markdown
# MemoryGraph SDK

Python SDK for MemoryGraph - the memory layer for AI agents.

## Installation

```bash
pip install memorygraphsdk
```

## Quick Start

```python
from memorygraphsdk import MemoryGraphClient

client = MemoryGraphClient(api_key="mgraph_your_key_here")

# Create a memory
memory = client.create_memory(
    type="solution",
    title="Fixed Redis timeout",
    content="Used exponential backoff with max 5 retries",
    tags=["redis", "timeout", "solution"]
)

# Search memories
results = client.search_memories(query="redis", limit=10)
for memory in results:
    print(f"{memory.title}: {memory.content}")
```

## Framework Integrations

### LangChain

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory
from langchain.chains import ConversationChain

memory = MemoryGraphMemory(api_key="mgraph_...")
chain = ConversationChain(memory=memory, llm=llm)
```

### CrewAI

```python
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
from crewai import Agent

memory = MemoryGraphCrewMemory(api_key="mgraph_...")
agent = Agent(memory=memory, ...)
```

## Documentation

Full docs: https://memorygraph.dev/docs/sdk
```

**Tasks**:
- [ ] Write comprehensive README
- [ ] Add installation instructions
- [ ] Add quick start examples
- [ ] Link to full documentation

### 7.2 API Documentation

**File**: `sdk/docs/api.md`

**Tasks**:
- [ ] Document all client methods
- [ ] Document all models
- [ ] Document all integrations
- [ ] Add type hints to all examples
- [ ] Generate API docs with Sphinx or mkdocs

### 7.3 Integration Guides

**Files**:
- `sdk/docs/llamaindex.md` (🔴 Critical)
- `sdk/docs/langchain.md` (🔴 Critical)
- `sdk/docs/crewai.md`
- `sdk/docs/autogen.md`

**Tasks**:
- [ ] Write detailed guide for each integration
- [ ] Include complete working examples
- [ ] Add troubleshooting sections
- [ ] Link from main docs site

---

## Section 8: Publishing

### 8.1 PyPI Configuration

**File**: `sdk/pyproject.toml`

```toml
[project]
name = "memorygraphsdk"
version = "0.1.0"
description = "Python SDK for MemoryGraph - memory for AI agents"
authors = [{name = "Gregory Dickson", email = "your@email.com"}]
license = {text = "Apache-2.0"}
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
llamaindex = ["llama-index>=0.10.0"]
langchain = ["langchain>=0.1.0"]
crewai = ["crewai>=0.1.0"]
autogen = ["pyautogen>=0.2.0"]
all = ["llama-index>=0.10.0", "langchain>=0.1.0", "crewai>=0.1.0", "pyautogen>=0.2.0"]

[project.urls]
Homepage = "https://memorygraph.dev"
Documentation = "https://memorygraph.dev/docs/sdk"
Repository = "https://github.com/gregorydickson/memory-graph"

[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"
```

**Tasks**:
- [ ] Configure pyproject.toml
- [ ] Set appropriate version
- [ ] Add all dependencies
- [ ] Add optional dependencies for integrations

### 8.2 Build and Publish

**Tasks**:
- [ ] Build package: `python -m build`
- [ ] Test install locally: `pip install dist/memorygraphsdk-*.whl`
- [ ] Publish to TestPyPI first: `twine upload --repository testpypi dist/*`
- [ ] Test install from TestPyPI
- [ ] Publish to PyPI: `twine upload dist/*`
- [ ] Verify package on PyPI
- [ ] Test install: `pip install memorygraphsdk`

### 8.3 CI/CD for SDK

**File**: `.github/workflows/sdk-release.yml`

```yaml
name: Release SDK

on:
  push:
    tags:
      - 'sdk-v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd sdk
          pip install build twine
      - name: Build
        run: cd sdk && python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: cd sdk && twine upload dist/*
```

**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Add PyPI token to secrets
- [ ] Test release process
- [ ] Document release procedure

---

## Section 9: Marketing

### 9.1 Announcement

**Tasks**:
- [ ] Blog post: "Introducing MemoryGraph SDK"
- [ ] Show integrations with LangChain, CrewAI, AutoGen
- [ ] Compare with Cipher (MCP-only)
- [ ] Post on Twitter, LinkedIn, Reddit
- [ ] Submit to framework communities

### 9.2 Framework-Specific Outreach

**Tasks**:
- [ ] Post in LangChain Discord/forums
- [ ] Post in CrewAI community
- [ ] Post in AutoGen GitHub discussions
- [ ] Create example projects for each framework
- [ ] Submit to awesome-langchain, etc.

---

## Acceptance Criteria Summary

### Functional
- [ ] SDK installed via pip
- [ ] All client methods working
- [ ] LangChain integration working
- [ ] CrewAI integration working
- [ ] AutoGen integration working

### Quality
- [ ] 30+ tests passing
- [ ] 90%+ test coverage
- [ ] Type hints on all public APIs
- [ ] Docstrings on all public APIs

### Documentation
- [ ] README complete with examples
- [ ] API documentation generated
- [ ] Integration guides published
- [ ] Examples for each framework

### Publishing
- [ ] Published to PyPI
- [ ] Installable via pip
- [ ] Listed on memorygraph.dev

---

## Notes for Coding Agent

**Important**:

1. **Keep it simple**: Don't over-engineer. Start with basic functionality.

2. **Async is optional**: Most users will use sync client. Async is nice-to-have.

3. **Framework integrations should be minimal**: Implement the minimum required by each framework's interface.

4. **Test with real APIs**: Use actual MemoryGraph API for integration tests.

5. **Version carefully**: Semantic versioning. Breaking changes = major version bump.

---

## Dependencies

**External**:
- httpx (HTTP client)
- pydantic (models)
- langchain (optional)
- crewai (optional)
- pyautogen (optional)

**Internal**:
- MemoryGraph Cloud API (from Workplan 14)

---

## Estimated Timeline

| Section | Effort | Dependencies |
|---------|--------|--------------|
| Section 1: SDK Core | 4-5 hours | API ready |
| Section 2: LangChain | 2-3 hours | Core done |
| Section 3: CrewAI | 2 hours | Core done |
| Section 4: AutoGen | 2 hours | Core done |
| Section 5: Testing | 3-4 hours | All impl done |
| Section 6: Documentation | 2-3 hours | All done |
| Section 7: Publishing | 1-2 hours | All done |
| Section 8: Marketing | 1-2 hours | Published |
| **Total** | **17-24 hours** | Sequential |

---

## References

- **LangChain BaseMemory**: https://python.langchain.com/docs/modules/memory/
- **CrewAI Memory**: https://docs.crewai.com/core-concepts/Memory/
- **AutoGen Docs**: https://microsoft.github.io/autogen/

---

**Last Updated**: 2025-12-08
**Status**: DEFERRED (pending v0.10.0 release)
**Priority Update**: LlamaIndex and LangChain elevated to 🔴 CRITICAL
**Next Step**: After v0.10.0 release, set up SDK project structure with LlamaIndex integration first
