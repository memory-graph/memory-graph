# LlamaIndex Integration Guide

Complete guide for using MemoryGraph with LlamaIndex for RAG pipelines and chat applications.

## Overview

The MemoryGraph SDK provides two main integrations for LlamaIndex:

1. **MemoryGraphChatMemory** - For chat engines with persistent memory
2. **MemoryGraphRetriever** - For RAG pipelines using memories as knowledge base

## Installation

```bash
pip install memorygraphsdk[llamaindex]
```

This installs both `memorygraphsdk` and `llama-index-core`.

## Quick Start

### Chat Memory Example

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

# Configure LlamaIndex
Settings.llm = OpenAI(model="gpt-4", temperature=0.7)

# Create memory
memory = MemoryGraphChatMemory(
    api_key="mgraph_your_key_here",
    session_id="user_123"  # Optional: isolate conversations
)

# Create chat engine with memory
chat_engine = SimpleChatEngine.from_defaults(memory=memory)

# Have a conversation
response = chat_engine.chat("I'm working on a Redis timeout issue")
print(response)

# Memory is automatically saved - retrieve in next session
response = chat_engine.chat("What was I working on?")
print(response)  # Remembers Redis timeout
```

---

## MemoryGraphChatMemory

Provides persistent memory for LlamaIndex chat engines by storing conversations in MemoryGraph.

### Constructor

```python
MemoryGraphChatMemory(
    api_key: str,
    session_id: str = "default",
    memory_key: str = "chat_history",
    return_messages: bool = True
)
```

**Parameters:**
- `api_key` (str): Your MemoryGraph API key
- `session_id` (str): Session identifier for isolating conversations. Default: "default"
- `memory_key` (str): Key used for memory in context. Default: "chat_history"
- `return_messages` (bool): Return as message objects vs strings. Default: True

### Methods

#### get(input: str | None = None) -> list[dict]

Retrieve relevant memories for the input.

```python
# Get recent conversation history
messages = memory.get()

# Get relevant messages for specific input
messages = memory.get(input="Redis timeout")
```

#### put(message: dict) -> None

Store a message in memory.

```python
memory.put({
    "role": "user",
    "content": "How do I fix Redis timeouts?"
})

memory.put({
    "role": "assistant",
    "content": "Use exponential backoff..."
})
```

#### set_messages(messages: list[dict]) -> None

Replace all messages in current session.

```python
memory.set_messages([
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello"}
])
```

#### reset() -> None

Reset memory (no-op in MemoryGraph - memories are permanent).

---

## Use Cases

### 1. Multi-Session Chat Application

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

Settings.llm = OpenAI(model="gpt-4")

def create_chat_for_user(user_id: str):
    """Create a chat engine with user-specific memory."""
    memory = MemoryGraphChatMemory(
        api_key="mgraph_...",
        session_id=f"user_{user_id}"
    )
    return SimpleChatEngine.from_defaults(memory=memory)

# User 1's conversation
chat1 = create_chat_for_user("alice")
chat1.chat("I'm debugging a Redis issue")

# User 2's conversation (isolated)
chat2 = create_chat_for_user("bob")
chat2.chat("I'm optimizing SQL queries")

# Later - memories are preserved
chat1_new = create_chat_for_user("alice")
response = chat1_new.chat("What was I debugging?")
# Response: "You were debugging a Redis issue"
```

### 2. Context-Aware Technical Assistant

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load documentation
documents = SimpleDirectoryReader("./docs").load_data()
index = VectorStoreIndex.from_documents(documents)

# Create memory
memory = MemoryGraphChatMemory(
    api_key="mgraph_...",
    session_id="tech_support"
)

# Create chat engine that combines memory + docs
chat_engine = CondenseQuestionChatEngine.from_defaults(
    query_engine=index.as_query_engine(),
    memory=memory,
    verbose=True
)

# Chat with context awareness
response = chat_engine.chat("How do I configure Redis?")
print(response)

# Follow-up understands context
response = chat_engine.chat("What about timeouts?")
print(response)
```

### 3. Project-Scoped Memory

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
from llama_index.core.chat_engine import SimpleChatEngine

class ProjectChatEngine:
    def __init__(self, project_name: str, api_key: str):
        self.memory = MemoryGraphChatMemory(
            api_key=api_key,
            session_id=f"project_{project_name}"
        )
        self.chat_engine = SimpleChatEngine.from_defaults(
            memory=self.memory
        )

    def chat(self, message: str):
        return self.chat_engine.chat(message)

# Use separate memory per project
payments_chat = ProjectChatEngine("payments-api", "mgraph_...")
auth_chat = ProjectChatEngine("auth-service", "mgraph_...")

payments_chat.chat("Redis timeout in payment flow")
auth_chat.chat("OAuth token expiration issue")
# Each project maintains separate conversation history
```

---

## MemoryGraphRetriever

Use MemoryGraph as a knowledge base for RAG pipelines by retrieving relevant memories.

### Constructor

```python
MemoryGraphRetriever(
    api_key: str,
    memory_types: list[str] | None = None,
    min_importance: float = 0.0,
    limit: int = 5
)
```

**Parameters:**
- `api_key` (str): Your MemoryGraph API key
- `memory_types` (list[str], optional): Filter by memory types. Default: ["solution", "code_pattern", "fix"]
- `min_importance` (float): Minimum importance score. Default: 0.0
- `limit` (int): Maximum results per query. Default: 5

### Methods

#### retrieve(query: str, include_relationships: bool = False) -> list[dict]

Retrieve relevant memories for a query.

```python
retriever = MemoryGraphRetriever(api_key="mgraph_...")
nodes = retriever.retrieve(
    query="How to fix Redis timeouts?",
    include_relationships=True
)

for node in nodes:
    print(f"- {node['text']}")
    print(f"  Score: {node['score']}")
```

---

## RAG Pipeline Examples

### 1. Memory-Augmented Query Engine

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphRetriever
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

# Create retriever
memory_retriever = MemoryGraphRetriever(
    api_key="mgraph_...",
    memory_types=["solution", "fix", "code_pattern"],
    min_importance=0.7,
    limit=5
)

# Use in query engine
query_engine = RetrieverQueryEngine.from_args(
    retriever=memory_retriever,
    verbose=True
)

# Query using memories as knowledge base
response = query_engine.query("What's the best way to handle Redis timeouts?")
print(response)
```

### 2. Hybrid Search (Documents + Memories)

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphRetriever
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.retrievers import QueryFusionRetriever

# Load documents
documents = SimpleDirectoryReader("./docs").load_data()
doc_index = VectorStoreIndex.from_documents(documents)
doc_retriever = doc_index.as_retriever(similarity_top_k=5)

# Create memory retriever
memory_retriever = MemoryGraphRetriever(
    api_key="mgraph_...",
    memory_types=["solution"],
    limit=5
)

# Combine both retrievers
fusion_retriever = QueryFusionRetriever(
    retrievers=[doc_retriever, memory_retriever],
    similarity_top_k=10,
    num_queries=1
)

# Query across both sources
nodes = fusion_retriever.retrieve("Redis timeout solutions")
for node in nodes:
    print(f"- {node.text[:100]}...")
```

### 3. Learning Agent with Memory Storage

```python
from memorygraphsdk import MemoryGraphClient
from memorygraphsdk.integrations.llamaindex import (
    MemoryGraphChatMemory,
    MemoryGraphRetriever
)
from llama_index.core.chat_engine import SimpleChatEngine

class LearningAgent:
    def __init__(self, api_key: str, session_id: str):
        self.client = MemoryGraphClient(api_key=api_key)
        self.session_id = session_id
        self.memory = MemoryGraphChatMemory(
            api_key=api_key,
            session_id=session_id
        )
        self.retriever = MemoryGraphRetriever(api_key=api_key)
        self.chat_engine = SimpleChatEngine.from_defaults(
            memory=self.memory
        )

    def chat(self, message: str):
        """Chat and automatically learn from important exchanges."""
        response = self.chat_engine.chat(message)

        # Extract and store important learnings
        if self._is_important(message, str(response)):
            self.client.create_memory(
                type="solution",
                title=self._extract_title(message),
                content=str(response),
                tags=self._extract_tags(message),
                importance=0.8,
                context={"session_id": self.session_id}
            )

        return response

    def recall_similar(self, query: str):
        """Recall similar past learnings."""
        return self.retriever.retrieve(query)

    def _is_important(self, message: str, response: str) -> bool:
        # Logic to determine if exchange is worth storing
        keywords = ["fix", "solve", "how to", "error", "issue"]
        return any(kw in message.lower() for kw in keywords)

    def _extract_title(self, message: str) -> str:
        # Extract concise title
        return message[:100]

    def _extract_tags(self, message: str) -> list[str]:
        # Extract relevant tags
        common_tags = ["redis", "timeout", "database", "api"]
        return [tag for tag in common_tags if tag in message.lower()]

# Usage
agent = LearningAgent(api_key="mgraph_...", session_id="dev_session")

# Agent learns from conversations
response = agent.chat("How do I fix Redis timeouts?")
# Important exchanges are automatically stored as memories

# Recall past learnings
learnings = agent.recall_similar("Redis issues")
for learning in learnings:
    print(f"Past learning: {learning['text'][:100]}...")
```

---

## Advanced Patterns

### Session Management

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
from llama_index.core.chat_engine import SimpleChatEngine

class SessionManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.active_sessions = {}

    def get_or_create_session(self, user_id: str, project: str = "default"):
        session_id = f"{user_id}_{project}"

        if session_id not in self.active_sessions:
            memory = MemoryGraphChatMemory(
                api_key=self.api_key,
                session_id=session_id
            )
            self.active_sessions[session_id] = SimpleChatEngine.from_defaults(
                memory=memory
            )

        return self.active_sessions[session_id]

# Usage
manager = SessionManager(api_key="mgraph_...")
chat = manager.get_or_create_session(
    user_id="alice",
    project="payments"
)
```

### Importance-Based Filtering

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphRetriever

# Retrieve only high-value memories
critical_retriever = MemoryGraphRetriever(
    api_key="mgraph_...",
    memory_types=["solution", "fix"],
    min_importance=0.8,  # Only critical learnings
    limit=3
)

# Get top solutions
nodes = critical_retriever.retrieve("production issues")
```

---

## Best Practices

### 1. Use Session IDs for Isolation

```python
# Good: Isolated sessions
memory = MemoryGraphChatMemory(
    api_key="mgraph_...",
    session_id=f"user_{user_id}"
)

# Avoid: Shared session for all users
memory = MemoryGraphChatMemory(api_key="mgraph_...")
```

### 2. Filter Memories by Type

```python
# Retrieve only actionable memories
retriever = MemoryGraphRetriever(
    api_key="mgraph_...",
    memory_types=["solution", "fix", "code_pattern"],
    min_importance=0.5
)
```

### 3. Combine with Document Search

Use MemoryGraph alongside traditional document retrieval for comprehensive RAG:

```python
# Hybrid: Documents + Memories
fusion_retriever = QueryFusionRetriever(
    retrievers=[
        doc_retriever,      # Official documentation
        memory_retriever    # Team learnings
    ],
    similarity_top_k=10
)
```

### 4. Store Important Exchanges

Automatically persist valuable conversations as memories:

```python
from memorygraphsdk import MemoryGraphClient

client = MemoryGraphClient(api_key="mgraph_...")

# After helpful exchange
client.create_memory(
    type="solution",
    title="Fixed Redis timeout in payments",
    content=response_text,
    tags=["redis", "payments", "production"],
    importance=0.9
)
```

---

## Troubleshooting

### Memory Not Persisting

**Issue:** Chat history not saved between sessions

**Solution:** Ensure you're using the same `session_id`:

```python
# Session 1
memory1 = MemoryGraphChatMemory(
    api_key="mgraph_...",
    session_id="user_123"  # Use consistent ID
)

# Session 2 (later)
memory2 = MemoryGraphChatMemory(
    api_key="mgraph_...",
    session_id="user_123"  # Same ID
)
```

### No Results from Retriever

**Issue:** `retrieve()` returns empty list

**Solutions:**

1. **Check memory types:**
```python
retriever = MemoryGraphRetriever(
    api_key="mgraph_...",
    memory_types=None  # Search all types
)
```

2. **Lower importance threshold:**
```python
retriever = MemoryGraphRetriever(
    api_key="mgraph_...",
    min_importance=0.0  # Include all importances
)
```

3. **Verify memories exist:**
```python
from memorygraphsdk import MemoryGraphClient
client = MemoryGraphClient(api_key="mgraph_...")
all_memories = client.search_memories(limit=100)
print(f"Total memories: {len(all_memories)}")
```

### Rate Limiting

**Issue:** `RateLimitError` raised

**Solution:** Implement exponential backoff:

```python
from memorygraphsdk import RateLimitError
import time

def retrieve_with_retry(retriever, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return retriever.retrieve(query)
        except RateLimitError:
            wait_time = 2 ** attempt
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

---

## API Reference

See [API Documentation](api.md) for complete reference of all methods and parameters.

## Examples

Complete working examples are available in the [examples directory](../examples/llamaindex_example.py).

## Support

- **Documentation**: https://memorygraph.dev/docs
- **GitHub Issues**: https://github.com/gregorydickson/claude-code-memory/issues
- **Discord**: https://discord.gg/memorygraph
