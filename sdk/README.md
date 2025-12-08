# MemoryGraph SDK

Python SDK for MemoryGraph - the graph-based memory layer for AI agents.

## Installation

```bash
pip install memorygraphsdk
```

With framework integrations:

```bash
# LlamaIndex integration
pip install memorygraphsdk[llamaindex]

# LangChain integration
pip install memorygraphsdk[langchain]

# CrewAI integration
pip install memorygraphsdk[crewai]

# AutoGen integration
pip install memorygraphsdk[autogen]

# All integrations
pip install memorygraphsdk[all]
```

## Quick Start

```python
from memorygraphsdk import MemoryGraphClient

# Initialize client (api_key can also be set via MEMORYGRAPH_API_KEY env var)
client = MemoryGraphClient(api_key="mgraph_your_key_here")

# Create a memory
memory = client.create_memory(
    type="solution",
    title="Fixed Redis timeout issue",
    content="Used exponential backoff with max 5 retries. Key was setting proper timeout values.",
    tags=["redis", "timeout", "solution"],
    importance=0.8
)
print(f"Created memory: {memory.id}")

# Search memories
results = client.search_memories(query="redis timeout", limit=10)
for mem in results:
    print(f"- {mem.title}: {mem.content[:100]}...")

# Create relationships
client.create_relationship(
    from_memory_id=solution_id,
    to_memory_id=problem_id,
    relationship_type="SOLVES"
)

# Get related memories
related = client.get_related_memories(
    memory_id=problem_id,
    relationship_types=["SOLVES"]
)
```

## Async Client

```python
from memorygraphsdk import AsyncMemoryGraphClient

async with AsyncMemoryGraphClient(api_key="mgraph_...") as client:
    memory = await client.create_memory(
        type="solution",
        title="Async solution",
        content="..."
    )

    memories = await client.search_memories(query="async")
```

## Framework Integrations

### LlamaIndex

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
from llama_index.core.chat_engine import SimpleChatEngine

memory = MemoryGraphChatMemory(api_key="mgraph_...")
chat_engine = SimpleChatEngine.from_defaults(memory=memory)

response = chat_engine.chat("I'm working on a Redis timeout issue")
```

### LangChain

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory
from langchain.chains import ConversationChain

memory = MemoryGraphMemory(api_key="mgraph_...")
chain = ConversationChain(memory=memory, llm=llm)

response = chain.run("What Redis issues have we seen?")
```

### CrewAI

```python
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
from crewai import Agent

memory = MemoryGraphCrewMemory(api_key="mgraph_...")
agent = Agent(
    role="Developer",
    goal="Solve technical problems",
    memory=memory
)
```

## API Reference

### MemoryGraphClient

| Method | Description |
|--------|-------------|
| `create_memory(...)` | Create a new memory |
| `get_memory(id)` | Get memory by ID |
| `update_memory(id, ...)` | Update a memory |
| `delete_memory(id)` | Delete a memory |
| `search_memories(...)` | Search for memories |
| `recall_memories(query)` | Natural language recall |
| `create_relationship(...)` | Create relationship |
| `get_related_memories(id)` | Get related memories |

### Memory Types

- `task` - Tasks and todos
- `solution` - Solutions to problems
- `problem` - Problems encountered
- `error` - Errors and exceptions
- `fix` - Bug fixes
- `code_pattern` - Code patterns
- `workflow` - Workflows and processes
- `conversation` - Chat/conversation messages (used by integrations)
- `general` - General information

### Relationship Types

- `SOLVES` - Solution → Problem
- `CAUSES` - Cause → Effect
- `TRIGGERS` - Trigger → Event
- `REQUIRES` - Dependent → Dependency
- `RELATED_TO` - General association

## Configuration

Environment variables:

```bash
export MEMORYGRAPH_API_KEY="mgraph_..."
export MEMORYGRAPH_API_URL="https://api.memorygraph.dev"  # optional
```

Or in code:

```python
client = MemoryGraphClient(
    api_key="mgraph_...",
    api_url="https://api.memorygraph.dev",
    timeout=30.0
)
```

## Error Handling

```python
from memorygraphsdk import (
    MemoryGraphClient,
    AuthenticationError,
    RateLimitError,
    NotFoundError
)

try:
    memory = client.get_memory("invalid-id")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Memory not found")
except RateLimitError:
    print("Rate limit exceeded, please retry")
```

## Documentation

- [API Reference](docs/api.md) - Complete API documentation
- [LlamaIndex Integration Guide](docs/llamaindex.md) - Using MemoryGraph with LlamaIndex
- [LangChain Integration Guide](docs/langchain.md) - Using MemoryGraph with LangChain
- [CrewAI Integration Guide](docs/crewai.md) - Using MemoryGraph with CrewAI
- [AutoGen Integration Guide](docs/autogen.md) - Using MemoryGraph with AutoGen
- [Examples](examples/) - Working code examples

## Features

- **Synchronous and Async** - Full async/await support for high-performance applications
- **Type-Safe** - Complete type hints and Pydantic models
- **Framework Integrations** - Native support for LlamaIndex, LangChain, CrewAI, and AutoGen
- **Graph-Based** - Relationships between memories for complex reasoning
- **Search & Recall** - Powerful search with natural language queries
- **Error Handling** - Comprehensive exception handling with specific error types

## Get API Key

Sign up at [memorygraph.dev](https://memorygraph.dev) to get your API key.

## Support

- GitHub Issues: https://github.com/gregorydickson/claude-code-memory/issues
- Documentation: https://memorygraph.dev/docs
- Email: support@memorygraph.dev

## License

Apache 2.0
