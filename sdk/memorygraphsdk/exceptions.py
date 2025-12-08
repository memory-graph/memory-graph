"""
Exceptions for MemoryGraph SDK.
"""


class MemoryGraphError(Exception):
    """Base exception for MemoryGraph SDK errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(MemoryGraphError):
    """Raised when API key is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class RateLimitError(MemoryGraphError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class NotFoundError(MemoryGraphError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(MemoryGraphError):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)


class ServerError(MemoryGraphError):
    """Raised when server returns an error."""

    def __init__(self, message: str = "Server error"):
        super().__init__(message, status_code=500)
