"""
Example: Using MemoryGraph with CrewAI

This example demonstrates how to use MemoryGraph as the memory backend
for CrewAI agents, enabling persistent memory across sessions and
automatic relationship tracking between memories.

Prerequisites:
    pip install memorygraphsdk[crewai]
    # or
    pip install memorygraphsdk crewai

Environment:
    Set MEMORYGRAPH_API_KEY environment variable or replace the placeholder below
"""
import os

from crewai import Agent, Crew, Task

from memorygraphsdk.integrations.crewai import MemoryGraphCrewMemory


def basic_example():
    """Basic example of using MemoryGraph with a single CrewAI agent."""
    # Create memory backend
    api_key = os.getenv("MEMORYGRAPH_API_KEY", "mgraph_your_key_here")
    memory = MemoryGraphCrewMemory(api_key=api_key, crew_id="research_crew")

    # Create an agent with memory
    researcher = Agent(
        role="Senior Researcher",
        goal="Research topics and remember important findings",
        backstory=(
            "You are an experienced researcher who excels at finding and "
            "synthesizing information. You have a great memory for details."
        ),
        memory=memory,
        verbose=True,
        allow_delegation=False,
    )

    # Create a research task
    task = Task(
        description=(
            "Research best practices for Python async programming. "
            "Focus on when to use async vs sync, common patterns, "
            "and performance considerations."
        ),
        expected_output="A comprehensive summary of Python async best practices",
        agent=researcher,
    )

    # Execute the task
    crew = Crew(agents=[researcher], tasks=[task], verbose=True)
    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)
    print(result)

    # The agent's findings are now stored in MemoryGraph
    # Let's search what was learned
    print("\n" + "=" * 60)
    print("STORED MEMORIES")
    print("=" * 60)
    memories = memory.search("async python", limit=5)
    for mem in memories:
        print(f"\n{mem['key']}:")
        print(f"  {mem['value'][:200]}...")

    # Clean up
    memory.close()


def multi_agent_example():
    """Example with multiple agents sharing memory."""
    api_key = os.getenv("MEMORYGRAPH_API_KEY", "mgraph_your_key_here")

    # All agents share the same memory space via crew_id
    shared_memory = MemoryGraphCrewMemory(api_key=api_key, crew_id="dev_team")

    # Define multiple agents
    researcher = Agent(
        role="Research Specialist",
        goal="Research technical topics and document findings",
        backstory="Expert at finding and synthesizing technical information",
        memory=shared_memory,
        verbose=True,
    )

    architect = Agent(
        role="Software Architect",
        goal="Design software solutions based on research",
        backstory=(
            "Experienced architect who can leverage research to design "
            "robust solutions"
        ),
        memory=shared_memory,
        verbose=True,
    )

    # Create tasks
    research_task = Task(
        description="Research microservices communication patterns",
        expected_output="Summary of different communication patterns",
        agent=researcher,
    )

    design_task = Task(
        description=(
            "Based on the research findings, design a communication "
            "strategy for our microservices"
        ),
        expected_output="Detailed communication architecture design",
        agent=architect,
    )

    # Execute crew
    crew = Crew(
        agents=[researcher, architect],
        tasks=[research_task, design_task],
        verbose=True,
    )

    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("CREW RESULTS")
    print("=" * 60)
    print(result)

    # Clean up
    shared_memory.close()


def persistence_example():
    """Example showing memory persistence across sessions."""
    api_key = os.getenv("MEMORYGRAPH_API_KEY", "mgraph_your_key_here")

    # Session 1: Store some memories
    print("=" * 60)
    print("SESSION 1: Storing memories")
    print("=" * 60)

    memory = MemoryGraphCrewMemory(api_key=api_key, crew_id="persistent_crew")

    memory.save(
        key="python_async_best_practice",
        value="Use async for I/O-bound operations, sync for CPU-bound",
        metadata={
            "tags": ["python", "async", "best-practice"],
            "importance": 0.9,
            "type": "code_pattern",
        },
    )

    memory.save(
        key="redis_timeout_solution",
        value="Implement exponential backoff with max 5 retries",
        metadata={
            "tags": ["redis", "timeout", "solution"],
            "importance": 0.85,
            "type": "solution",
        },
    )

    print("Stored 2 memories")
    memory.close()

    # Session 2: Retrieve memories from previous session
    print("\n" + "=" * 60)
    print("SESSION 2: Retrieving persisted memories")
    print("=" * 60)

    memory = MemoryGraphCrewMemory(api_key=api_key, crew_id="persistent_crew")

    # Search for memories
    results = memory.search("python async", limit=5)
    print(f"\nFound {len(results)} memories about 'python async':")
    for result in results:
        print(f"\n- {result['key']}")
        print(f"  {result['value']}")
        print(f"  Tags: {result['metadata'].get('tags', [])}")

    # Get specific memory
    content = memory.get("redis_timeout_solution")
    if content:
        print("\n" + "=" * 60)
        print("RETRIEVED SPECIFIC MEMORY")
        print("=" * 60)
        print(f"Redis timeout solution: {content}")

    memory.close()


def context_manager_example():
    """Example using context manager for automatic cleanup."""
    api_key = os.getenv("MEMORYGRAPH_API_KEY", "mgraph_your_key_here")

    with MemoryGraphCrewMemory(api_key=api_key, crew_id="context_crew") as memory:
        # Store a memory
        memory.save(
            key="context_pattern",
            value="Use context managers for automatic resource cleanup",
            metadata={"tags": ["python", "pattern"], "importance": 0.8},
        )

        # Search memories
        results = memory.search("python pattern", limit=3)
        for result in results:
            print(f"{result['key']}: {result['value']}")

    # Memory client is automatically closed when exiting the context


if __name__ == "__main__":
    print("MemoryGraph CrewAI Integration Examples")
    print("=" * 60)

    # Check for API key
    if not os.getenv("MEMORYGRAPH_API_KEY"):
        print("\nWARNING: MEMORYGRAPH_API_KEY not set!")
        print("Set it with: export MEMORYGRAPH_API_KEY='mgraph_your_key_here'")
        print("\nRunning examples with placeholder key (will fail)...\n")

    # Run examples
    try:
        print("\n\n1. BASIC EXAMPLE")
        print("=" * 60)
        # Uncomment to run - requires OpenAI API key for CrewAI
        # basic_example()

        print("\n\n2. PERSISTENCE EXAMPLE")
        print("=" * 60)
        persistence_example()

        print("\n\n3. CONTEXT MANAGER EXAMPLE")
        print("=" * 60)
        context_manager_example()

        # Uncomment to run multi-agent example
        # print("\n\n4. MULTI-AGENT EXAMPLE")
        # print("=" * 60)
        # multi_agent_example()

    except Exception as e:
        print(f"\nError running example: {e}")
        print("\nMake sure you have:")
        print("1. Valid MEMORYGRAPH_API_KEY environment variable")
        print("2. CrewAI installed: pip install memorygraphsdk[crewai]")
        print("3. OpenAI API key if running agent examples")
