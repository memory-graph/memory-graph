"""Tests for custom exception hierarchy."""

import pytest
from memorygraph.models import (
    MemoryError,
    MemoryNotFoundError,
    RelationshipError,
    ValidationError,
    DatabaseConnectionError,
    SchemaError,
)


def test_memory_error_base():
    """Test base MemoryError exception."""
    error = MemoryError("Test error message")
    assert str(error) == "Test error message"
    assert error.message == "Test error message"
    assert error.details == {}


def test_memory_error_with_details():
    """Test MemoryError with details."""
    details = {"key": "value", "number": 42}
    error = MemoryError("Error with details", details)
    assert "Error with details" in str(error)
    assert "Details:" in str(error)
    assert error.details == details


def test_memory_not_found_error():
    """Test MemoryNotFoundError exception."""
    error = MemoryNotFoundError("test-id-123")
    assert "test-id-123" in str(error)
    assert error.memory_id == "test-id-123"
    assert isinstance(error, MemoryError)


def test_relationship_error():
    """Test RelationshipError exception."""
    error = RelationshipError("Relationship creation failed")
    assert "Relationship creation failed" in str(error)
    assert isinstance(error, MemoryError)


def test_validation_error():
    """Test ValidationError exception."""
    error = ValidationError("Invalid memory data")
    assert "Invalid memory data" in str(error)
    assert isinstance(error, MemoryError)


def test_database_connection_error():
    """Test DatabaseConnectionError exception."""
    error = DatabaseConnectionError("Connection failed")
    assert "Connection failed" in str(error)
    assert isinstance(error, MemoryError)


def test_schema_error():
    """Test SchemaError exception."""
    error = SchemaError("Schema initialization failed")
    assert "Schema initialization failed" in str(error)
    assert isinstance(error, MemoryError)


def test_exception_hierarchy():
    """Test that all custom exceptions inherit from MemoryError."""
    exceptions = [
        MemoryNotFoundError("test"),
        RelationshipError("test"),
        ValidationError("test"),
        DatabaseConnectionError("test"),
        SchemaError("test"),
    ]

    for exc in exceptions:
        assert isinstance(exc, MemoryError)
        assert isinstance(exc, Exception)


if __name__ == "__main__":
    pytest.main([__file__])
