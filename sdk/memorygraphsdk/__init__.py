"""
MemoryGraph SDK - Python SDK for MemoryGraph memory layer.

Usage:
    from memorygraphsdk import MemoryGraphClient

    client = MemoryGraphClient(api_key="mgraph_...")
    memory = client.create_memory(
        type="solution",
        title="Fixed timeout issue",
        content="Used exponential backoff with retries",
        tags=["redis", "timeout"]
    )
"""

from .async_client import AsyncMemoryGraphClient
from .client import MemoryGraphClient
from .exceptions import (
    AuthenticationError,
    MemoryGraphError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    Memory,
    MemoryCreate,
    MemoryType,
    MemoryUpdate,
    RelatedMemory,
    Relationship,
    RelationshipCreate,
    RelationshipType,
    SearchResult,
)

__version__ = "0.1.0"
__all__ = [
    # Clients
    "MemoryGraphClient",
    "AsyncMemoryGraphClient",
    # Models
    "Memory",
    "MemoryCreate",
    "MemoryUpdate",
    "MemoryType",
    "Relationship",
    "RelationshipCreate",
    "RelationshipType",
    "RelatedMemory",
    "SearchResult",
    # Exceptions
    "MemoryGraphError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
]
