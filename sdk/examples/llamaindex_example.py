"""
Example: Using MemoryGraph with LlamaIndex

This example demonstrates how to use MemoryGraph as a memory backend
for LlamaIndex chat engines and RAG pipelines.

Prerequisites:
    pip install memorygraphsdk[llamaindex]
    pip install llama-index-llms-openai

Environment variables:
    MEMORYGRAPH_API_KEY: Your MemoryGraph API key
    OPENAI_API_KEY: Your OpenAI API key
"""
import os
from llama_index.core import Settings
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.llms.openai import OpenAI

from memorygraphsdk.integrations.llamaindex import (
    MemoryGraphChatMemory,
    MemoryGraphRetriever,
)


def example_chat_memory():
    """Example: Using MemoryGraph for chat memory."""
    print("\n=== Chat Memory Example ===\n")

    # Configure LlamaIndex with OpenAI
    Settings.llm = OpenAI(model="gpt-4", temperature=0.7)

    # Create memory backed by MemoryGraph
    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    memory = MemoryGraphChatMemory(
        api_key=api_key,
        session_id="example-session-1",  # Unique session ID
    )

    # Create chat engine with memory
    chat_engine = SimpleChatEngine.from_defaults(memory=memory)

    # Have a conversation
    print("User: I'm working on fixing a Redis timeout issue in production")
    response = chat_engine.chat("I'm working on fixing a Redis timeout issue in production")
    print(f"Assistant: {response}\n")

    print("User: What connection pool settings should I use?")
    response = chat_engine.chat("What connection pool settings should I use?")
    print(f"Assistant: {response}\n")

    print("User: What was I working on?")
    response = chat_engine.chat("What was I working on?")
    print(f"Assistant: {response}\n")

    print("The conversation is now stored in MemoryGraph!")
    print("You can resume this conversation later by using the same session_id.")


def example_retriever():
    """Example: Using MemoryGraph as a retriever for RAG."""
    print("\n=== Retriever Example ===\n")

    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    # First, store some knowledge in MemoryGraph
    print("Storing some example knowledge...")
    from memorygraphsdk import MemoryGraphClient

    with MemoryGraphClient(api_key=api_key) as client:
        # Store a solution
        client.create_memory(
            type="solution",
            title="Fixed Redis Timeout with Connection Pooling",
            content="""
            Problem: Redis connections were timing out under load.

            Solution: Implemented connection pooling with these settings:
            - max_connections: 50
            - socket_timeout: 5 seconds
            - socket_connect_timeout: 2 seconds
            - retry_on_timeout: True

            This reduced timeout errors by 95%.
            """,
            tags=["redis", "timeout", "connection-pool", "production"],
            importance=0.9,
        )

        # Store a code pattern
        client.create_memory(
            type="code_pattern",
            title="Redis Connection Pool Configuration Pattern",
            content="""
            import redis

            pool = redis.ConnectionPool(
                host='localhost',
                port=6379,
                max_connections=50,
                socket_timeout=5,
                socket_connect_timeout=2,
                retry_on_timeout=True
            )

            client = redis.Redis(connection_pool=pool)
            """,
            tags=["redis", "python", "code-pattern"],
            importance=0.8,
        )

    print("Knowledge stored!\n")

    # Now use the retriever
    print("Creating retriever...")
    retriever = MemoryGraphRetriever(
        api_key=api_key,
        memory_types=["solution", "code_pattern", "fix"],
        min_importance=0.5,
    )

    # Retrieve relevant memories
    print("\nQuery: 'How to fix Redis timeout issues?'\n")
    nodes = retriever.retrieve("How to fix Redis timeout issues?", limit=3)

    print(f"Found {len(nodes)} relevant memories:\n")
    for i, node in enumerate(nodes, 1):
        print(f"{i}. {node['metadata']['type']}: {node['metadata'].get('tags', [])}")
        print(f"   Score: {node['score']:.2f}")
        print(f"   {node['text'][:200]}...\n")

    # Retrieve with relationships
    print("\nRetrieving with relationships...\n")
    nodes_with_rels = retriever.retrieve_with_relationships(
        "Redis connection pooling",
        limit=2,
        include_related=True,
        max_depth=1,
    )

    for node in nodes_with_rels:
        print(f"Memory: {node['metadata']['type']}")
        if node["metadata"].get("related"):
            print(f"  Related memories: {len(node['metadata']['related'])}")
            for rel in node["metadata"]["related"]:
                print(f"    - {rel['relationship_type']}: {rel['title']}")
        print()

    retriever.close()


def example_rag_pipeline():
    """Example: Complete RAG pipeline with MemoryGraph."""
    print("\n=== RAG Pipeline Example ===\n")

    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    # Configure LLM
    Settings.llm = OpenAI(model="gpt-4", temperature=0.7)

    # Create retriever
    retriever = MemoryGraphRetriever(
        api_key=api_key,
        memory_types=["solution", "code_pattern", "problem", "fix"],
        min_importance=0.5,
    )

    # Query for relevant memories
    query = "How should I configure Redis for production?"
    print(f"Query: {query}\n")

    nodes = retriever.retrieve(query, limit=3)

    if not nodes:
        print("No relevant memories found.")
        return

    # Build context from retrieved memories
    context = "\n\n".join([f"Memory {i+1}:\n{node['text']}" for i, node in enumerate(nodes)])

    print("Retrieved context:\n")
    print(context[:500] + "...\n")

    # Use LLM to generate response with context
    prompt = f"""Based on the following information from memory:

{context}

Question: {query}

Please provide a comprehensive answer based on the memories above."""

    print("Generating response with LLM...\n")
    response = Settings.llm.complete(prompt)
    print(f"Answer: {response}\n")

    retriever.close()


def main():
    """Run all examples."""
    print("MemoryGraph + LlamaIndex Integration Examples")
    print("=" * 50)

    # Check environment variables
    if not os.getenv("MEMORYGRAPH_API_KEY"):
        print("\nError: MEMORYGRAPH_API_KEY not set")
        print("Get your API key at: https://memorygraph.dev")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("\nError: OPENAI_API_KEY not set")
        print("Set your OpenAI API key to run these examples")
        return

    # Run examples
    try:
        example_chat_memory()
        example_retriever()
        example_rag_pipeline()
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nInstall required dependencies:")
        print("  pip install memorygraphsdk[llamaindex] llama-index-llms-openai")
    except Exception as e:
        print(f"\nError running example: {e}")
        raise


if __name__ == "__main__":
    main()
