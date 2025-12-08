"""
Example: Using MemoryGraph with LangChain

This example demonstrates how to use MemoryGraphMemory with LangChain
to create a conversational agent with persistent memory.

Prerequisites:
    pip install memorygraphsdk[langchain]
    pip install langchain-openai  # or your preferred LLM provider

Environment:
    export MEMORYGRAPH_API_KEY="mgraph_..."
    export OPENAI_API_KEY="sk-..."
"""
import os

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

from memorygraphsdk.integrations.langchain import MemoryGraphMemory


def basic_conversation_example():
    """Basic conversation with memory persistence."""
    print("=" * 60)
    print("Example 1: Basic Conversation with Memory")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    # Create memory with a specific session ID
    memory = MemoryGraphMemory(
        api_key=api_key,
        session_id="example-session-1",
        return_messages=False,  # Return as string format
    )

    # Create LLM and chain
    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    chain = ConversationChain(llm=llm, memory=memory, verbose=True)

    # Have a conversation
    print("\n1. First message:")
    response = chain.run("Hi, I'm working on a Redis timeout issue in my Python application.")
    print(f"Response: {response}\n")

    print("2. Follow-up question:")
    response = chain.run("What did I just say I was working on?")
    print(f"Response: {response}\n")

    print("Memory is automatically saved to MemoryGraph!")
    print("You can retrieve it in future sessions with the same session_id.\n")


def message_format_example():
    """Example using message format instead of string format."""
    print("=" * 60)
    print("Example 2: Using Message Format")
    print("=" * 60)

    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    # Create memory with return_messages=True
    memory = MemoryGraphMemory(
        api_key=api_key,
        session_id="example-session-2",
        return_messages=True,  # Return as Message objects
    )

    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    chain = ConversationChain(llm=llm, memory=memory, verbose=True)

    # Have a conversation
    print("\n1. First message:")
    response = chain.run("What are the benefits of using graph databases?")
    print(f"Response: {response}\n")

    print("2. Ask about conversation history:")
    response = chain.run("What did I ask about?")
    print(f"Response: {response}\n")


def persistent_session_example():
    """Demonstrate memory persistence across different script runs."""
    print("=" * 60)
    print("Example 3: Persistent Sessions")
    print("=" * 60)

    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    session_id = "persistent-session-demo"

    # Create memory - this will load any existing conversation history
    memory = MemoryGraphMemory(
        api_key=api_key,
        session_id=session_id,
        return_messages=False,
    )

    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    chain = ConversationChain(llm=llm, memory=memory, verbose=True)

    print(f"\nUsing session_id: {session_id}")
    print("This session persists across runs. Try running this script multiple times!")

    # Add new message to the conversation
    print("\n1. New message:")
    response = chain.run("Remember: My favorite programming language is Python.")
    print(f"Response: {response}\n")

    print("2. Test memory:")
    response = chain.run("What's my favorite programming language?")
    print(f"Response: {response}\n")

    print(
        f"\nNote: To start a fresh conversation, use a different session_id "
        f"or change the value of 'persistent-session-demo'"
    )


def custom_tags_example():
    """Example showing how to use custom context and tags."""
    print("=" * 60)
    print("Example 4: Advanced - Direct Memory Access")
    print("=" * 60)

    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    # Create memory
    memory = MemoryGraphMemory(
        api_key=api_key,
        session_id="advanced-example",
    )

    # You can also access the underlying MemoryGraph client directly
    # for more advanced operations
    print("\nAccessing conversation memories directly:")
    memories = memory.client.search_memories(
        tags=["session:advanced-example"],
        memory_types=["conversation"],
        limit=10,
    )

    if memories:
        print(f"\nFound {len(memories)} conversation memories:")
        for mem in memories:
            role = mem.context.get("role") if mem.context else "unknown"
            print(f"  - [{role}] {mem.title}")
    else:
        print("\nNo conversation memories found yet. Run the chain first!")

    # You can also create relationships between memories
    # or search across sessions
    print("\nYou have full access to MemoryGraph features!")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("MemoryGraph + LangChain Integration Examples")
    print("=" * 60 + "\n")

    # Check for required environment variables
    if not os.getenv("MEMORYGRAPH_API_KEY"):
        print("ERROR: Please set MEMORYGRAPH_API_KEY environment variable")
        print("Example: export MEMORYGRAPH_API_KEY='mgraph_...'")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='sk-...'")
        return

    # Run examples
    try:
        basic_conversation_example()
        print("\n" + "-" * 60 + "\n")

        message_format_example()
        print("\n" + "-" * 60 + "\n")

        persistent_session_example()
        print("\n" + "-" * 60 + "\n")

        custom_tags_example()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
