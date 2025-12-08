# LlamaIndex Integration

The MemoryGraph SDK provides native integration with LlamaIndex, enabling persistent memory for chat engines and semantic retrieval for RAG pipelines.

## Installation

```bash
pip install memorygraphsdk[llamaindex]
```

This installs the SDK with LlamaIndex dependencies.

## Features

- **Chat Memory**: Store conversation history in MemoryGraph with semantic search
- **RAG Retrieval**: Use MemoryGraph as a knowledge base for retrieval-augmented generation
- **Persistent Sessions**: Conversations persist across sessions
- **Relationship Traversal**: Retrieve related memories for richer context

## Quick Start

### Chat Memory

Use MemoryGraph as a memory backend for LlamaIndex chat engines:

```python
from llama_index.core import Settings
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.llms.openai import OpenAI
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory

# Configure LLM
Settings.llm = OpenAI(model="gpt-4")

# Create memory with session ID
memory = MemoryGraphChatMemory(
    api_key="mgraph_your_key_here",
    session_id="user-123-session"
)

# Create chat engine
chat_engine = SimpleChatEngine.from_defaults(memory=memory)

# Have conversations
response = chat_engine.chat("I'm working on a Redis timeout issue")
# Later, in the same or different session...
response = chat_engine.chat("What was I working on?")
# Will remember the Redis issue!
```

### RAG Retrieval

Use MemoryGraph as a retriever for knowledge-based queries:

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphRetriever
from memorygraphsdk import MemoryGraphClient

# First, store some knowledge
client = MemoryGraphClient(api_key="mgraph_your_key_here")
client.create_memory(
    type="solution",
    title="Fixed Redis Timeout with Connection Pooling",
    content="Implemented connection pooling with max_connections=50...",
    tags=["redis", "timeout", "solution"],
    importance=0.9
)

# Create retriever
retriever = MemoryGraphRetriever(
    api_key="mgraph_your_key_here",
    memory_types=["solution", "code_pattern", "fix"],
    min_importance=0.5
)

# Retrieve relevant memories
nodes = retriever.retrieve("How to fix Redis timeout?", limit=5)

for node in nodes:
    print(f"Score: {node['score']:.2f}")
    print(f"Type: {node['metadata']['type']}")
    print(f"Text: {node['text']}\n")
```

### Advanced: Retrieval with Relationships

Retrieve memories along with their relationships for richer context:

```python
nodes = retriever.retrieve_with_relationships(
    query="Redis connection pooling",
    limit=3,
    include_related=True,
    max_depth=1
)

for node in nodes:
    print(f"Memory: {node['text'][:100]}")
    if node['metadata'].get('related'):
        print(f"Related memories:")
        for rel in node['metadata']['related']:
            print(f"  - {rel['relationship_type']}: {rel['title']}")
```

## API Reference

### MemoryGraphChatMemory

Chat memory that stores conversation history in MemoryGraph.

**Parameters:**
- `api_key` (str): Your MemoryGraph API key
- `session_id` (str): Unique session identifier (default: "default")
- `api_url` (str): API URL (default: "https://api.memorygraph.dev")

**Methods:**
- `get(input=None, **kwargs)`: Get relevant memories/messages
- `get_all()`: Get all messages in chronological order
- `put(message)`: Store a ChatMessage
- `set(messages)`: Store multiple messages
- `reset()`: No-op (memories are persistent)

### MemoryGraphRetriever

Retriever for using MemoryGraph in RAG pipelines.

**Parameters:**
- `api_key` (str): Your MemoryGraph API key
- `memory_types` (list[str]): Types to retrieve (default: ["solution", "code_pattern", "fix"])
- `api_url` (str): API URL (default: "https://api.memorygraph.dev")
- `min_importance` (float): Minimum importance score (0.0-1.0)

**Methods:**
- `retrieve(query, limit=5, **kwargs)`: Retrieve relevant memories
- `retrieve_with_relationships(query, limit=5, include_related=True, max_depth=1, **kwargs)`: Retrieve with relationship context
- `close()`: Close client connection

## Complete Example

See [examples/llamaindex_example.py](../examples/llamaindex_example.py) for complete working examples including:
- Chat memory with persistent sessions
- RAG retrieval pipeline
- Retrieval with relationships

## Best Practices

### Session Management

Use meaningful session IDs to organize conversations:

```python
# User-specific sessions
memory = MemoryGraphChatMemory(
    api_key=api_key,
    session_id=f"user-{user_id}-{datetime.now().strftime('%Y%m%d')}"
)

# Topic-specific sessions
memory = MemoryGraphChatMemory(
    api_key=api_key,
    session_id="project-redis-optimization"
)
```

### Memory Types

Choose appropriate memory types for retrieval:

- **Solutions**: `["solution", "fix"]` - for problem-solving queries
- **Code**: `["code_pattern", "solution"]` - for coding help
- **Documentation**: `["technology", "workflow"]` - for process questions
- **Mixed**: `["solution", "code_pattern", "problem", "fix"]` - for general queries

### Importance Scoring

Set importance to control retrieval relevance:

```python
# Critical production fix
client.create_memory(
    type="solution",
    title="Production Redis Fix",
    content="...",
    importance=0.9  # High importance
)

# Experimental note
client.create_memory(
    type="general",
    title="Redis experiment",
    content="...",
    importance=0.3  # Low importance
)

# Retriever will prioritize high-importance memories
retriever = MemoryGraphRetriever(
    api_key=api_key,
    min_importance=0.5  # Only get important memories
)
```

## Troubleshooting

### Import Error

If you get an import error:
```
ImportError: llama-index is required for this integration
```

Install the LlamaIndex extra:
```bash
pip install memorygraphsdk[llamaindex]
```

### Empty Results

If retrieval returns no results:
1. Check that memories exist with the specified `memory_types`
2. Lower `min_importance` threshold
3. Verify tags match your search
4. Use broader memory types

### Session Persistence

Memories are permanent in MemoryGraph. To start fresh:
- Create a new `session_id`
- Or use filters in `get()` to limit history

## Next Steps

- See [LangChain Integration](./langchain.md) for LangChain support
- Read [API Documentation](./api.md) for full SDK reference
- Check out [examples/llamaindex_example.py](../examples/llamaindex_example.py) for complete code

## Support

- Documentation: https://memorygraph.dev/docs
- GitHub Issues: https://github.com/gregorydickson/claude-code-memory/issues
- API Status: https://status.memorygraph.dev
