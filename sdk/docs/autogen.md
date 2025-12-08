# AutoGen Integration Guide

Use MemoryGraph to persist conversation history for Microsoft AutoGen agents.

## Installation

```bash
pip install memorygraphsdk[autogen]
```

## Quick Start

```python
from memorygraphsdk.integrations.autogen import MemoryGraphAutoGenHistory
import autogen

# Create persistent conversation history
history = MemoryGraphAutoGenHistory(
    api_key="mgraph_your_key_here",
    conversation_id="user_session_123"
)

# Configure AutoGen agent
config_list = [{"model": "gpt-4", "api_key": "your_openai_key"}]

assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={"config_list": config_list}
)

user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER"
)

# Save messages after each turn
def save_message(sender, recipient, message):
    history.add_message(
        role=sender.name,
        content=message,
        metadata={"recipient": recipient.name}
    )

# Use AutoGen with persistent history
assistant.initiate_chat(
    user_proxy,
    message="Help me fix Redis timeouts"
)
```

## MemoryGraphAutoGenHistory API

### Constructor

```python
MemoryGraphAutoGenHistory(
    api_key: str,
    conversation_id: str = "default",
    api_url: str = "https://api.memorygraph.dev"
)
```

**Parameters:**
- `api_key`: Your MemoryGraph API key
- `conversation_id`: Conversation identifier for isolation
- `api_url`: API URL

### Methods

#### add_message(role: str, content: str, metadata: dict | None = None) -> None

Store a message in conversation history.

```python
history.add_message(
    role="assistant",
    content="To fix Redis timeouts, use connection pooling...",
    metadata={"timestamp": "2024-01-01T00:00:00Z"}
)
```

#### get_messages(limit: int = 100) -> list[dict]

Retrieve conversation history.

```python
messages = history.get_messages(limit=50)
for msg in messages:
    print(f"{msg['role']}: {msg['content']}")
```

#### clear() -> None

Clear conversation history (no-op in MemoryGraph).

## Use Cases

### 1. Persistent Multi-Agent Conversations

```python
from memorygraphsdk.integrations.autogen import MemoryGraphAutoGenHistory
import autogen

# Persistent history across sessions
history = MemoryGraphAutoGenHistory(
    api_key="mgraph_...",
    conversation_id="project_alpha"
)

# Create agents
assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={"config_list": config_list}
)

user_proxy = autogen.UserProxyAgent(
    name="user",
    human_input_mode="ALWAYS"
)

# Session 1
assistant.initiate_chat(user_proxy, message="Let's debug this issue")
# ... conversation happens, save messages ...

# Session 2 (later)
# Load history
messages = history.get_messages()
# Continue conversation with context
```

### 2. Multi-User Agent System

```python
from memorygraphsdk.integrations.autogen import MemoryGraphAutoGenHistory

def create_user_history(user_id: str):
    """Create isolated history per user."""
    return MemoryGraphAutoGenHistory(
        api_key="mgraph_...",
        conversation_id=f"user_{user_id}"
    )

# Each user has separate conversation history
alice_history = create_user_history("alice")
bob_history = create_user_history("bob")
```

### 3. Conversation Analysis

```python
from memorygraphsdk import MemoryGraphClient

# Analyze all conversations
client = MemoryGraphClient(api_key="mgraph_...")

# Get all conversation memories
conversations = client.search_memories(
    memory_types=["conversation"],
    tags=["autogen"],
    limit=1000
)

# Analyze patterns
for conv in conversations:
    print(f"Role: {conv.context.get('role')}")
    print(f"Content: {conv.content[:100]}...")
```

## Best Practices

### 1. Use Conversation IDs for Isolation

```python
# Good: Per-user or per-session isolation
history = MemoryGraphAutoGenHistory(
    api_key="mgraph_...",
    conversation_id=f"user_{user_id}_session_{session_id}"
)

# Avoid: Shared history
history = MemoryGraphAutoGenHistory(api_key="mgraph_...")
```

### 2. Add Metadata to Messages

```python
history.add_message(
    role="assistant",
    content="Solution: Use Redis connection pooling",
    metadata={
        "timestamp": datetime.now().isoformat(),
        "model": "gpt-4",
        "task": "debugging"
    }
)
```

### 3. Retrieve Context Before New Conversations

```python
# Load previous context
history = MemoryGraphAutoGenHistory(api_key="mgraph_...", conversation_id="user_123")
messages = history.get_messages(limit=10)

# Provide context to new conversation
context = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-5:]])
assistant.initiate_chat(
    user_proxy,
    message=f"Previous context:\n{context}\n\nNow let's continue..."
)
```

## Troubleshooting

### Messages Not Persisting

**Solution:** Ensure you're calling `add_message` after each turn:

```python
def on_message(sender, message):
    history.add_message(
        role=sender.name,
        content=message["content"]
    )
```

### Wrong Conversation Loaded

**Solution:** Use consistent `conversation_id`:

```python
# Correct
history = MemoryGraphAutoGenHistory(
    api_key="mgraph_...",
    conversation_id="session_abc"  # Same ID
)
```

## Examples

See [examples/autogen_example.py](../examples/autogen_example.py) for complete working examples.

## Support

- [API Reference](api.md)
- [GitHub Issues](https://github.com/gregorydickson/claude-code-memory/issues)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
