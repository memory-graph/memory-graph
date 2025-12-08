# CrewAI Integration Guide

Use MemoryGraph for persistent memory across CrewAI agent crews.

## Installation

```bash
pip install memorygraphsdk[crewai]
```

## Quick Start

```python
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
from crewai import Agent, Task, Crew

# Create memory
memory = MemoryGraphCrewMemory(
    api_key="mgraph_your_key_here",
    crew_id="research_crew"  # Isolate by crew
)

# Create agent with memory
researcher = Agent(
    role="Senior Researcher",
    goal="Research and document technical solutions",
    backstory="Expert at finding solutions to technical problems",
    memory=True,
    verbose=True
)

# Create and run task
task = Task(
    description="Research best practices for handling Redis timeouts",
    agent=researcher,
    expected_output="Detailed report on Redis timeout solutions"
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
print(result)
```

## MemoryGraphCrewMemory API

### Constructor

```python
MemoryGraphCrewMemory(
    api_key: str,
    crew_id: str = "default",
    api_url: str = "https://api.memorygraph.dev"
)
```

**Parameters:**
- `api_key`: Your MemoryGraph API key
- `crew_id`: Crew identifier for memory isolation
- `api_url`: API URL (default: https://api.memorygraph.dev)

### Methods

#### save(key: str, value: str, metadata: dict | None = None) -> None

Store a memory.

```python
memory.save(
    key="redis_solution",
    value="Use connection pooling with exponential backoff",
    metadata={"importance": 0.9, "tags": ["redis", "solution"]}
)
```

#### search(query: str, limit: int = 10) -> list[dict]

Search memories by query.

```python
results = memory.search(query="Redis timeout solutions", limit=5)
for result in results:
    print(f"{result['key']}: {result['value']}")
```

#### get(key: str) -> str | None

Retrieve a specific memory by key.

```python
value = memory.get("redis_solution")
if value:
    print(f"Solution: {value}")
```

#### clear() -> None

Clear all memories for this crew (stored in MemoryGraph).

```python
memory.clear()  # Adds 'cleared' flag to memories
```

#### reset() -> None

Reset memory state (alias for clear()).

## Use Cases

### 1. Multi-Agent Research Crew

```python
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
from crewai import Agent, Task, Crew

# Shared memory for the crew
crew_memory = MemoryGraphCrewMemory(
    api_key="mgraph_...",
    crew_id="research_team"
)

# Agents with shared memory
researcher = Agent(
    role="Researcher",
    goal="Find technical solutions",
    memory=True
)

analyst = Agent(
    role="Analyst",
    goal="Analyze solutions",
    memory=True
)

# Tasks that build on shared knowledge
research_task = Task(
    description="Research Redis timeout solutions",
    agent=researcher,
    expected_output="List of solutions"
)

analysis_task = Task(
    description="Analyze the researched solutions",
    agent=analyst,
    expected_output="Best solution recommendation",
    context=[research_task]  # Depends on research
)

crew = Crew(
    agents=[researcher, analyst],
    tasks=[research_task, analysis_task],
    verbose=True
)

result = crew.kickoff()
```

### 2. Persistent Learnings Across Runs

```python
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory
from crewai import Agent, Task, Crew

# Memory persists across crew runs
persistent_memory = MemoryGraphCrewMemory(
    api_key="mgraph_...",
    crew_id="learning_crew"
)

# First run - learn
crew1 = Crew(
    agents=[agent],
    tasks=[learning_task],
    verbose=True
)
crew1.kickoff()

# Second run - apply learnings
crew2 = Crew(
    agents=[agent],
    tasks=[application_task],
    verbose=True
)
# Agent has access to learnings from crew1
crew2.kickoff()
```

### 3. Crew-Specific Knowledge Bases

```python
from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory

# Different crews, different knowledge domains
dev_memory = MemoryGraphCrewMemory(
    api_key="mgraph_...",
    crew_id="dev_crew"
)

qa_memory = MemoryGraphCrewMemory(
    api_key="mgraph_...",
    crew_id="qa_crew"
)

ops_memory = MemoryGraphCrewMemory(
    api_key="mgraph_...",
    crew_id="ops_crew"
)
```

## Best Practices

### 1. Use Crew IDs for Isolation

```python
# Good: Isolated per crew
memory = MemoryGraphCrewMemory(
    api_key="mgraph_...",
    crew_id="research_crew"
)

# Avoid: Shared across all crews
memory = MemoryGraphCrewMemory(api_key="mgraph_...")
```

### 2. Tag Memories for Organization

```python
memory.save(
    key="solution_001",
    value="Redis connection pooling solution...",
    metadata={
        "tags": ["redis", "solution", "production"],
        "importance": 0.9
    }
)
```

### 3. Store Structured Knowledge

```python
import json

# Store structured data as JSON
solution_data = {
    "problem": "Redis timeouts",
    "solution": "Connection pooling",
    "code": "redis_client = Redis(connection_pool=pool)",
    "tested": True
}

memory.save(
    key="redis_pooling_solution",
    value=json.dumps(solution_data),
    metadata={"type": "solution", "importance": 0.9}
)
```

## Troubleshooting

### Memory Not Persisting

**Issue:** Crew doesn't remember learnings

**Solution:** Ensure consistent `crew_id`:

```python
# Session 1
memory1 = MemoryGraphCrewMemory(api_key="mgraph_...", crew_id="team_A")

# Session 2
memory2 = MemoryGraphCrewMemory(api_key="mgraph_...", crew_id="team_A")  # Same ID
```

### Search Returns Nothing

**Solution:** Verify memories were saved:

```python
from memorygraphsdk import MemoryGraphClient

client = MemoryGraphClient(api_key="mgraph_...")
all_memories = client.search_memories(
    tags=[f"crew:{crew_id}"],
    limit=100
)
print(f"Total memories: {len(all_memories)}")
```

## Examples

See [examples/crewai_example.py](../examples/crewai_example.py) for complete working examples.

## Support

- [API Reference](api.md)
- [GitHub Issues](https://github.com/gregorydickson/claude-code-memory/issues)
- [CrewAI Documentation](https://docs.crewai.com)
