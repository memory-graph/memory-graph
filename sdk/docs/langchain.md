# LangChain Integration Guide

Use MemoryGraph as a persistent memory backend for LangChain conversations.

## Installation

```bash
pip install memorygraphsdk[langchain]
```

## Quick Start

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain

# Create memory with session isolation
memory = MemoryGraphMemory(
    api_key="mgraph_your_key_here",
    session_id="user_123",  # Isolate conversations per user
    return_messages=True     # Return as message objects
)

# Create chain with persistent memory
llm = ChatOpenAI(model="gpt-4")
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# Have a conversation
response = conversation.predict(input="I'm working on a Redis timeout issue")
print(response)

# Later, in a new session...
response = conversation.predict(input="What was I working on?")
print(response)  # Remembers Redis issue!
```

## MemoryGraphMemory API

### Constructor

```python
MemoryGraphMemory(
    api_key: str,
    session_id: str = "default",
    memory_key: str = "history",
    return_messages: bool = False,
    input_key: str | None = None,
    output_key: str | None = None
)
```

**Parameters:**
- `api_key`: Your MemoryGraph API key
- `session_id`: Session identifier for isolation
- `memory_key`: Key for memory in prompt template
- `return_messages`: Return as ChatMessage objects (True) or string (False)
- `input_key`: Key for inputs in save_context (default: "input")
- `output_key`: Key for outputs in save_context (default: "output")

### Methods

#### load_memory_variables(inputs: dict) -> dict

Load conversation history from MemoryGraph.

```python
history = memory.load_memory_variables({"input": "Hello"})
print(history["history"])  # Recent conversation
```

#### save_context(inputs: dict, outputs: dict) -> None

Save a conversation turn to MemoryGraph.

```python
memory.save_context(
    inputs={"input": "How do I fix Redis timeouts?"},
    outputs={"output": "Use exponential backoff with connection pooling..."}
)
```

#### clear() -> None

Clear memory (no-op - memories are permanent in MemoryGraph).

## Use Cases

### 1. Multi-User Chat Application

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain

class ChatService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.llm = ChatOpenAI(model="gpt-4")

    def get_conversation(self, user_id: str) -> ConversationChain:
        """Get or create a conversation for a user."""
        memory = MemoryGraphMemory(
            api_key=self.api_key,
            session_id=f"user_{user_id}",
            return_messages=True
        )
        return ConversationChain(llm=self.llm, memory=memory)

# Usage
service = ChatService(api_key="mgraph_...")
alice_chat = service.get_conversation("alice")
bob_chat = service.get_conversation("bob")

# Each user has isolated conversation history
alice_chat.predict(input="I need help with Redis")
bob_chat.predict(input="I need help with PostgreSQL")
```

### 2. Context-Aware Agent

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain import hub

# Load prompt
prompt = hub.pull("hwchase17/react")

# Create memory
memory = MemoryGraphMemory(
    api_key="mgraph_...",
    session_id="agent_session",
    return_messages=True
)

# Create agent with persistent memory
llm = ChatOpenAI(model="gpt-4")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)

# Agent remembers context across runs
response = agent_executor.invoke({"input": "Find Redis timeout solutions"})
# Later...
response = agent_executor.invoke({"input": "What did you find?"})
```

### 3. Project-Scoped Memory

```python
from memorygraphsdk.integrations.langchain import MemoryGraphMemory

def create_project_memory(project_name: str, api_key: str):
    """Create memory scoped to a specific project."""
    return MemoryGraphMemory(
        api_key=api_key,
        session_id=f"project_{project_name}",
        return_messages=True
    )

# Different projects have separate memory
payments_memory = create_project_memory("payments-api", "mgraph_...")
auth_memory = create_project_memory("auth-service", "mgraph_...")
```

## Message Formats

### String Format (return_messages=False)

Memory returned as concatenated string:

```python
memory = MemoryGraphMemory(api_key="mgraph_...", return_messages=False)
# Returns: "Human: Hello\nAI: Hi there!\n..."
```

### Message Format (return_messages=True)

Memory returned as LangChain message objects:

```python
memory = MemoryGraphMemory(api_key="mgraph_...", return_messages=True)
# Returns: [HumanMessage(content="Hello"), AIMessage(content="Hi there!"), ...]
```

## Best Practices

### 1. Use Session IDs for Isolation

```python
# Good: Per-user isolation
memory = MemoryGraphMemory(
    api_key="mgraph_...",
    session_id=f"user_{user_id}"
)

# Bad: Shared memory
memory = MemoryGraphMemory(api_key="mgraph_...")
```

### 2. Choose Appropriate Message Format

```python
# For chains expecting messages
memory = MemoryGraphMemory(api_key="mgraph_...", return_messages=True)

# For chains expecting strings
memory = MemoryGraphMemory(api_key="mgraph_...", return_messages=False)
```

### 3. Handle Custom Keys

```python
# For chains with non-standard keys
memory = MemoryGraphMemory(
    api_key="mgraph_...",
    input_key="question",   # Instead of "input"
    output_key="answer"     # Instead of "output"
)
```

## Troubleshooting

### Memory Not Loading

**Issue:** Conversation history not appearing in prompts

**Solution:** Check `memory_key` matches your prompt template:

```python
memory = MemoryGraphMemory(
    api_key="mgraph_...",
    memory_key="chat_history"  # Must match prompt template
)
```

### Session Isolation Not Working

**Issue:** Users seeing each other's conversations

**Solution:** Ensure unique session IDs:

```python
# Correct
memory = MemoryGraphMemory(
    api_key="mgraph_...",
    session_id=f"user_{user_id}"  # Unique per user
)
```

### TypeError with Messages

**Issue:** Chain expects messages but gets string (or vice versa)

**Solution:** Set `return_messages` appropriately:

```python
# For ConversationChain, ConversationalRetrievalChain
memory = MemoryGraphMemory(api_key="mgraph_...", return_messages=True)

# For basic chains
memory = MemoryGraphMemory(api_key="mgraph_...", return_messages=False)
```

## Advanced: Direct Memory Access

```python
from memorygraphsdk import MemoryGraphClient
from memorygraphsdk.integrations.langchain import MemoryGraphMemory

# Access underlying client for direct operations
client = MemoryGraphClient(api_key="mgraph_...")
memory = MemoryGraphMemory(api_key="mgraph_...", session_id="user_123")

# Search conversation history
memories = client.search_memories(
    tags=["session:user_123"],
    limit=50
)

# Analyze conversation patterns
for mem in memories:
    print(f"{mem.created_at}: {mem.title}")
```

## Examples

Complete examples in [examples/langchain_example.py](../examples/langchain_example.py)

## Support

- [API Reference](api.md)
- [GitHub Issues](https://github.com/gregorydickson/claude-code-memory/issues)
- [Documentation](https://memorygraph.dev/docs)
