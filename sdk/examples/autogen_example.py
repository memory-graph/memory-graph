"""
Example: Using MemoryGraph with AutoGen.

This example demonstrates how to use MemoryGraphAutoGenHistory to persist
AutoGen conversation history across sessions.

Install requirements:
    pip install memorygraphsdk[autogen]
    pip install pyautogen

Set your API key:
    export MEMORYGRAPH_API_KEY="mgraph_your_key_here"
"""
import os
from memorygraphsdk.integrations.autogen import MemoryGraphAutoGenHistory

# Optional: If you want to use with actual AutoGen agents
try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    print("Note: pyautogen not installed. Running basic example only.")


def basic_example():
    """Basic example using MemoryGraphAutoGenHistory directly."""
    print("=" * 60)
    print("Basic Example: Storing and Retrieving Messages")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    # Create history manager
    with MemoryGraphAutoGenHistory(
        api_key=api_key,
        conversation_id="example_conversation_1"
    ) as history:
        # Add some messages to the conversation
        print("\n1. Adding messages to conversation...")
        history.add_message(
            "user",
            "I'm having issues with Redis timeouts in my Python application"
        )
        history.add_message(
            "assistant",
            "I can help with that. Redis timeouts often occur due to network issues "
            "or slow operations. Have you tried implementing retry logic?"
        )
        history.add_message(
            "user",
            "Not yet. How would I implement that?"
        )
        history.add_message(
            "assistant",
            "You can use exponential backoff with the redis-py library. "
            "Here's a simple example with max 5 retries..."
        )

        print("✓ Messages stored successfully\n")

        # Retrieve conversation history
        print("2. Retrieving conversation history...")
        messages = history.get_messages()

        print(f"✓ Retrieved {len(messages)} messages:\n")
        for i, msg in enumerate(messages, 1):
            role = msg["role"].upper()
            content = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            print(f"   [{i}] {role}: {content}\n")


def autogen_agent_example():
    """Example integrating with AutoGen agents."""
    if not AUTOGEN_AVAILABLE:
        print("\nAutoGen agent example skipped (pyautogen not installed)")
        return

    print("\n" + "=" * 60)
    print("AutoGen Agent Example")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    if not openai_api_key:
        print("Note: OPENAI_API_KEY not set. Skipping AutoGen agent example.")
        return

    # Configure AutoGen
    config_list = [
        {
            "model": "gpt-4",
            "api_key": openai_api_key,
        }
    ]

    # Create history manager
    history = MemoryGraphAutoGenHistory(
        api_key=api_key,
        conversation_id="autogen_example_1"
    )

    # Create AutoGen agents
    assistant = autogen.AssistantAgent(
        name="assistant",
        llm_config={
            "config_list": config_list,
            "temperature": 0.7,
        },
        system_message="You are a helpful AI assistant specialized in Python programming."
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",  # For this example, we'll use predefined inputs
        max_consecutive_auto_reply=1,
        code_execution_config=False,
    )

    try:
        # Simulate a conversation
        print("\n1. Starting AutoGen conversation...\n")

        user_message = "What's the best way to handle Redis connection pooling in Python?"

        # Store user message
        history.add_message("user", user_message)

        # Get assistant response
        user_proxy.initiate_chat(
            assistant,
            message=user_message,
        )

        # In a real application, you would capture the assistant's response
        # and store it with history.add_message("assistant", response)

        print("\n2. Conversation stored in MemoryGraph")
        print("   You can retrieve this conversation later using the same conversation_id")

        # Demonstrate retrieving history
        print("\n3. Retrieving stored conversation...\n")
        messages = history.get_messages()

        for msg in messages:
            role = msg["role"]
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"   {role.upper()}: {content}\n")

    finally:
        history.close()


def persistent_conversation_example():
    """Example showing persistence across sessions."""
    print("\n" + "=" * 60)
    print("Persistence Example: Continuing a Previous Conversation")
    print("=" * 60)

    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    conversation_id = "persistent_example"

    # Session 1: Start a conversation
    print("\nSession 1: Starting a new conversation...")
    with MemoryGraphAutoGenHistory(api_key=api_key, conversation_id=conversation_id) as history:
        history.add_message("user", "I need to implement caching in my API")
        history.add_message("assistant", "Great! I recommend using Redis for caching.")
        print("✓ Session 1 complete\n")

    # Session 2: Continue the same conversation (simulating a new session/restart)
    print("Session 2: Continuing the conversation (after restart)...")
    with MemoryGraphAutoGenHistory(api_key=api_key, conversation_id=conversation_id) as history:
        # Retrieve previous messages
        previous_messages = history.get_messages()
        print(f"✓ Retrieved {len(previous_messages)} previous messages")

        # Continue the conversation
        history.add_message("user", "How do I set an expiration time?")
        history.add_message("assistant", "You can use the EX parameter in Redis SET commands.")

        # Show full conversation history
        print("\nFull conversation history:")
        all_messages = history.get_messages()
        for i, msg in enumerate(all_messages, 1):
            role = msg["role"].upper()
            print(f"   [{i}] {role}: {msg['content']}")


def multi_conversation_example():
    """Example showing multiple separate conversations."""
    print("\n" + "=" * 60)
    print("Multiple Conversations Example")
    print("=" * 60)

    api_key = os.getenv("MEMORYGRAPH_API_KEY")
    if not api_key:
        print("Error: MEMORYGRAPH_API_KEY environment variable not set")
        return

    # Create two separate conversations
    print("\nManaging multiple separate conversations...\n")

    # Conversation 1: Redis help
    with MemoryGraphAutoGenHistory(api_key=api_key, conversation_id="redis_help") as history1:
        history1.add_message("user", "Redis connection issues")
        history1.add_message("assistant", "Let's troubleshoot your Redis connection")
        redis_messages = history1.get_messages()
        print(f"Conversation 'redis_help': {len(redis_messages)} messages")

    # Conversation 2: Python async
    with MemoryGraphAutoGenHistory(api_key=api_key, conversation_id="async_help") as history2:
        history2.add_message("user", "How does async/await work?")
        history2.add_message("assistant", "Let me explain Python's async features")
        async_messages = history2.get_messages()
        print(f"Conversation 'async_help': {len(async_messages)} messages")

    print("\n✓ Each conversation is stored separately and can be retrieved independently")


if __name__ == "__main__":
    # Run all examples
    basic_example()
    persistent_conversation_example()
    multi_conversation_example()
    autogen_agent_example()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. Messages persist across sessions using conversation_id")
    print("  2. Multiple conversations can be managed independently")
    print("  3. Easy integration with AutoGen agents")
    print("  4. Full conversation history is always retrievable")
