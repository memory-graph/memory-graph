"""
Framework integrations for MemoryGraph SDK.

Available integrations:
- LlamaIndex (memorygraphsdk.integrations.llamaindex)
- LangChain (memorygraphsdk.integrations.langchain)
- CrewAI (memorygraphsdk.integrations.crewai)
- AutoGen (memorygraphsdk.integrations.autogen)

Each integration requires the corresponding framework to be installed.
Install with extras:
    pip install memorygraphsdk[llamaindex]
    pip install memorygraphsdk[langchain]
    pip install memorygraphsdk[crewai]
    pip install memorygraphsdk[autogen]
    pip install memorygraphsdk[all]
"""

# Lazy imports to avoid requiring all frameworks
__all__: list[str] = []

# Note: Each integration handles its own import errors gracefully
