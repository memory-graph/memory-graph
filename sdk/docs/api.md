# MemoryGraph SDK API Reference

Complete API reference for the MemoryGraph Python SDK.

## Table of Contents

- [Client Classes](#client-classes)
  - [MemoryGraphClient](#memorygraphclient)
  - [AsyncMemoryGraphClient](#asyncmemorygraphclient)
- [Models](#models)
  - [Memory](#memory)
  - [Relationship](#relationship)
  - [RelatedMemory](#relatedmemory)
- [Exceptions](#exceptions)
- [Integrations](#integrations)

---

## Client Classes

### MemoryGraphClient

Synchronous client for interacting with the MemoryGraph API.

#### Constructor

```python
MemoryGraphClient(
    api_key: str | None = None,
    api_url: str = "https://api.memorygraph.dev",
    timeout: float = 30.0
)
```

**Parameters:**
- `api_key` (str, optional): Your MemoryGraph API key. If not provided, looks for `MEMORYGRAPH_API_KEY` environment variable.
- `api_url` (str): Base URL for the API. Default: `https://api.memorygraph.dev`
- `timeout` (float): Request timeout in seconds. Default: 30.0

**Raises:**
- `AuthenticationError`: If no API key is provided and environment variable is not set.

**Example:**
```python
from memorygraphsdk import MemoryGraphClient

# With explicit API key
client = MemoryGraphClient(api_key="mgraph_...")

# Or using environment variable
import os
os.environ["MEMORYGRAPH_API_KEY"] = "mgraph_..."
client = MemoryGraphClient()

# With context manager (recommended)
with MemoryGraphClient(api_key="mgraph_...") as client:
    memories = client.search_memories(query="redis")
```

---

#### create_memory

```python
create_memory(
    type: str,
    title: str,
    content: str,
    tags: list[str] | None = None,
    importance: float = 0.5,
    context: dict[str, Any] | None = None,
    summary: str | None = None
) -> Memory
```

Create a new memory in the graph.

**Parameters:**
- `type` (str): Memory type (e.g., 'solution', 'problem', 'code_pattern')
- `title` (str): Short descriptive title
- `content` (str): Full content of the memory
- `tags` (list[str], optional): Tags for categorization
- `importance` (float): Importance score 0.0-1.0. Default: 0.5
- `context` (dict, optional): Additional context metadata
- `summary` (str, optional): Brief summary

**Returns:** `Memory` object with generated ID

**Raises:**
- `AuthenticationError`: Invalid API key
- `ValidationError`: Invalid input parameters
- `RateLimitError`: Rate limit exceeded

**Example:**
```python
memory = client.create_memory(
    type="solution",
    title="Fixed Redis timeout in payment flow",
    content="Implemented exponential backoff with max 5 retries. "
            "Set connection timeout to 5s and operation timeout to 10s.",
    tags=["redis", "timeout", "payment"],
    importance=0.8,
    context={"project": "payments-api", "version": "2.1.0"},
    summary="Redis timeout fix using exponential backoff"
)
print(f"Created: {memory.id}")
```

---

#### get_memory

```python
get_memory(
    memory_id: str,
    include_relationships: bool = True
) -> Memory
```

Retrieve a memory by its ID.

**Parameters:**
- `memory_id` (str): The ID of the memory to retrieve
- `include_relationships` (bool): Whether to include related memories. Default: True

**Returns:** `Memory` object

**Raises:**
- `NotFoundError`: Memory not found
- `AuthenticationError`: Invalid API key

**Example:**
```python
memory = client.get_memory("mem_abc123")
print(f"{memory.title}: {memory.content}")
```

---

#### update_memory

```python
update_memory(
    memory_id: str,
    title: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
    importance: float | None = None,
    summary: str | None = None
) -> Memory
```

Update an existing memory. Only provided fields will be updated.

**Parameters:**
- `memory_id` (str): The ID of the memory to update
- `title` (str, optional): New title
- `content` (str, optional): New content
- `tags` (list[str], optional): New tags (replaces existing)
- `importance` (float, optional): New importance score
- `summary` (str, optional): New summary

**Returns:** Updated `Memory` object

**Example:**
```python
updated = client.update_memory(
    "mem_abc123",
    importance=0.9,
    tags=["redis", "timeout", "critical"]
)
```

---

#### delete_memory

```python
delete_memory(memory_id: str) -> bool
```

Delete a memory and all its relationships.

**Parameters:**
- `memory_id` (str): The ID of the memory to delete

**Returns:** `True` if successful

**Raises:**
- `NotFoundError`: Memory not found

**Example:**
```python
client.delete_memory("mem_abc123")
```

---

#### search_memories

```python
search_memories(
    query: str | None = None,
    memory_types: list[str] | None = None,
    tags: list[str] | None = None,
    min_importance: float | None = None,
    limit: int = 20,
    offset: int = 0
) -> list[Memory]
```

Search for memories using various filters.

**Parameters:**
- `query` (str, optional): Text to search in title and content
- `memory_types` (list[str], optional): Filter by memory types
- `tags` (list[str], optional): Filter by tags (AND logic)
- `min_importance` (float, optional): Minimum importance score
- `limit` (int): Maximum results. Default: 20
- `offset` (int): Skip first N results. Default: 0

**Returns:** List of `Memory` objects

**Example:**
```python
# Search for Redis-related solutions
memories = client.search_memories(
    query="redis",
    memory_types=["solution", "fix"],
    tags=["production"],
    min_importance=0.7,
    limit=10
)

for mem in memories:
    print(f"- {mem.title} (importance: {mem.importance})")
```

---

#### recall_memories

```python
recall_memories(
    query: str,
    memory_types: list[str] | None = None,
    project_path: str | None = None,
    limit: int = 20
) -> list[Memory]
```

Natural language query for recalling memories. Optimized for conversational queries.

**Parameters:**
- `query` (str): Natural language query
- `memory_types` (list[str], optional): Filter by types
- `project_path` (str, optional): Filter by project
- `limit` (int): Maximum results. Default: 20

**Returns:** List of relevant `Memory` objects

**Example:**
```python
# Natural language query
memories = client.recall_memories(
    query="How did we fix the Redis timeout issue?",
    memory_types=["solution", "fix"]
)
```

---

#### create_relationship

```python
create_relationship(
    from_memory_id: str,
    to_memory_id: str,
    relationship_type: str,
    strength: float = 0.5,
    confidence: float = 0.8,
    context: str | None = None
) -> Relationship
```

Create a directed relationship between two memories.

**Parameters:**
- `from_memory_id` (str): Source memory ID
- `to_memory_id` (str): Target memory ID
- `relationship_type` (str): Type of relationship (e.g., 'SOLVES', 'CAUSES')
- `strength` (float): Relationship strength 0.0-1.0. Default: 0.5
- `confidence` (float): Confidence in relationship 0.0-1.0. Default: 0.8
- `context` (str, optional): Description of the relationship

**Returns:** `Relationship` object

**Example:**
```python
# Link a solution to the problem it solves
rel = client.create_relationship(
    from_memory_id=solution_id,
    to_memory_id=problem_id,
    relationship_type="SOLVES",
    strength=0.9,
    context="Exponential backoff completely resolved the timeout issue"
)
```

---

#### get_related_memories

```python
get_related_memories(
    memory_id: str,
    relationship_types: list[str] | None = None,
    max_depth: int = 1
) -> list[RelatedMemory]
```

Get memories related to a specific memory by traversing relationships.

**Parameters:**
- `memory_id` (str): The memory to find relations for
- `relationship_types` (list[str], optional): Filter by relationship types
- `max_depth` (int): Maximum traversal depth. Default: 1

**Returns:** List of `RelatedMemory` objects

**Example:**
```python
# Find all solutions for a problem
related = client.get_related_memories(
    memory_id=problem_id,
    relationship_types=["SOLVES"],
    max_depth=1
)

for rel in related:
    print(f"Solution: {rel.memory.title}")
    print(f"Strength: {rel.strength}")
```

---

#### close

```python
close() -> None
```

Close the HTTP client and release resources.

**Example:**
```python
client = MemoryGraphClient(api_key="mgraph_...")
try:
    # Use client
    memories = client.search_memories(query="test")
finally:
    client.close()
```

---

### AsyncMemoryGraphClient

Asynchronous client for high-performance applications. All methods are identical to `MemoryGraphClient` but are async.

**Example:**
```python
import asyncio
from memorygraphsdk import AsyncMemoryGraphClient

async def main():
    async with AsyncMemoryGraphClient(api_key="mgraph_...") as client:
        # All methods are awaitable
        memory = await client.create_memory(
            type="solution",
            title="Async solution",
            content="Content"
        )

        memories = await client.search_memories(query="async")

        for mem in memories:
            print(mem.title)

asyncio.run(main())
```

---

## Models

### Memory

Represents a memory node in the graph.

**Attributes:**
- `id` (str): Unique identifier (e.g., "mem_abc123")
- `type` (MemoryType): Type of memory
- `title` (str): Short descriptive title
- `content` (str): Full content
- `tags` (list[str]): List of tags
- `importance` (float): Importance score 0.0-1.0
- `context` (dict | None): Additional metadata
- `summary` (str | None): Brief summary
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Example:**
```python
print(f"Memory: {memory.title}")
print(f"Type: {memory.type}")
print(f"Tags: {', '.join(memory.tags)}")
print(f"Created: {memory.created_at}")
```

---

### MemoryType

Enum of valid memory types.

**Values:**
- `TASK` - "task"
- `CODE_PATTERN` - "code_pattern"
- `PROBLEM` - "problem"
- `SOLUTION` - "solution"
- `PROJECT` - "project"
- `TECHNOLOGY` - "technology"
- `ERROR` - "error"
- `FIX` - "fix"
- `COMMAND` - "command"
- `FILE_CONTEXT` - "file_context"
- `WORKFLOW` - "workflow"
- `GENERAL` - "general"

---

### Relationship

Represents a directed relationship between memories.

**Attributes:**
- `id` (str): Unique identifier
- `from_memory_id` (str): Source memory ID
- `to_memory_id` (str): Target memory ID
- `relationship_type` (str): Type (e.g., "SOLVES", "CAUSES")
- `strength` (float): Relationship strength 0.0-1.0
- `confidence` (float): Confidence 0.0-1.0
- `context` (str | None): Relationship description
- `created_at` (datetime): Creation timestamp

---

### RelationshipType

Common relationship types.

**Values:**
- `SOLVES` - Solution → Problem
- `CAUSES` - Cause → Effect
- `TRIGGERS` - Trigger → Event
- `PREVENTS` - Prevention → Problem
- `REQUIRES` - Dependent → Dependency
- `USED_IN` - Pattern → Project
- `RELATED_TO` - General association
- And many more...

---

### RelatedMemory

A memory with its relationship context.

**Attributes:**
- `memory` (Memory): The related memory
- `relationship_type` (str): How it's related
- `strength` (float): Relationship strength
- `depth` (int): Graph traversal depth

---

## Exceptions

All exceptions inherit from `MemoryGraphError`.

### MemoryGraphError

Base exception for all SDK errors.

**Attributes:**
- `message` (str): Error message
- `status_code` (int | None): HTTP status code if applicable

---

### AuthenticationError

Raised when API key is invalid or missing.

**HTTP Status:** 401

**Example:**
```python
from memorygraphsdk import MemoryGraphClient, AuthenticationError

try:
    client = MemoryGraphClient(api_key="invalid")
    client.search_memories()
except AuthenticationError as e:
    print("Invalid API key. Please check your credentials.")
```

---

### RateLimitError

Raised when API rate limit is exceeded.

**HTTP Status:** 429

**Handling:**
```python
from memorygraphsdk import RateLimitError
import time

try:
    memory = client.create_memory(...)
except RateLimitError:
    print("Rate limited. Waiting 60 seconds...")
    time.sleep(60)
    # Retry
```

---

### NotFoundError

Raised when a requested resource doesn't exist.

**HTTP Status:** 404

---

### ValidationError

Raised when request parameters are invalid.

**HTTP Status:** 400

---

### ServerError

Raised when the server encounters an error.

**HTTP Status:** 5xx

---

## Integrations

The SDK includes native integrations for popular AI frameworks.

### LlamaIndex

See [LlamaIndex Integration Guide](llamaindex.md)

```python
from memorygraphsdk.integrations.llamaindex import MemoryGraphChatMemory
```

### LangChain

See [LangChain Integration Guide](langchain.md)

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory
```

### CrewAI

See [CrewAI Integration Guide](crewai.md)

```python
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
```

### AutoGen

See [AutoGen Integration Guide](autogen.md)

```python
from memorygraphsdk.integrations.autogen import MemoryGraphAutoGenHistory
```

---

## Best Practices

### 1. Use Context Managers

Always use context managers to ensure proper cleanup:

```python
with MemoryGraphClient(api_key="mgraph_...") as client:
    memories = client.search_memories(query="test")
# Client automatically closed
```

### 2. Tag Consistently

Use consistent tagging for better search results:

```python
# Good
tags=["redis", "timeout", "production"]

# Bad
tags=["Redis", "TIMEOUT", "prod"]
```

### 3. Set Appropriate Importance

Use importance scores to prioritize memories:

- **0.8-1.0**: Critical production issues, major learnings
- **0.5-0.7**: Regular solutions, patterns
- **0.3-0.4**: Minor fixes, reference material

### 4. Create Relationships

Link related memories to build a knowledge graph:

```python
# Create problem
problem = client.create_memory(
    type="problem",
    title="Redis timeouts in production",
    content="..."
)

# Create solution
solution = client.create_memory(
    type="solution",
    title="Implemented exponential backoff",
    content="..."
)

# Link them
client.create_relationship(
    from_memory_id=solution.id,
    to_memory_id=problem.id,
    relationship_type="SOLVES"
)
```

### 5. Handle Errors Gracefully

```python
from memorygraphsdk import (
    MemoryGraphClient,
    AuthenticationError,
    RateLimitError,
    NotFoundError
)

try:
    memory = client.get_memory("mem_abc123")
except AuthenticationError:
    logger.error("Invalid API key")
except RateLimitError:
    logger.warning("Rate limited, will retry")
except NotFoundError:
    logger.info("Memory not found")
```

---

## Rate Limits

Current rate limits:

- **Free tier**: 100 requests/minute
- **Pro tier**: 1000 requests/minute
- **Enterprise**: Custom limits

When rate limited, the API returns a 429 status code. Implement exponential backoff for retries.

---

## Support

- **Documentation**: https://memorygraph.dev/docs
- **GitHub Issues**: https://github.com/gregorydickson/claude-code-memory/issues
- **Email**: support@memorygraph.dev
