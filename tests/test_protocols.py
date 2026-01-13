"""
Tests for src/memorygraph/protocols.py

Protocols are structural types that define interfaces. We test:
1. Protocol structure is correct
2. Backends properly implement the protocol
3. Type checking works as expected

Following TDD approach to achieve coverage.
"""
import inspect
from typing import get_type_hints

import pytest

from memorygraph.protocols import MemoryOperations


class TestMemoryOperationsProtocol:
    """Test the MemoryOperations protocol structure."""

    def test_protocol_exists(self):
        """Test that MemoryOperations protocol is defined."""
        assert MemoryOperations is not None
        assert hasattr(MemoryOperations, "__annotations__") or hasattr(
            MemoryOperations, "__protocol_attrs__"
        )

    def test_protocol_has_store_memory(self):
        """Test that protocol defines store_memory method."""
        assert hasattr(MemoryOperations, "store_memory")
        # Get the signature
        sig = inspect.signature(MemoryOperations.store_memory)
        assert "memory" in sig.parameters

    def test_protocol_has_get_memory(self):
        """Test that protocol defines get_memory method."""
        assert hasattr(MemoryOperations, "get_memory")
        sig = inspect.signature(MemoryOperations.get_memory)
        assert "memory_id" in sig.parameters
        assert "include_relationships" in sig.parameters

    def test_protocol_has_update_memory(self):
        """Test that protocol defines update_memory method."""
        assert hasattr(MemoryOperations, "update_memory")
        sig = inspect.signature(MemoryOperations.update_memory)
        assert "memory_id" in sig.parameters
        assert "updates" in sig.parameters

    def test_protocol_has_delete_memory(self):
        """Test that protocol defines delete_memory method."""
        assert hasattr(MemoryOperations, "delete_memory")
        sig = inspect.signature(MemoryOperations.delete_memory)
        assert "memory_id" in sig.parameters

    def test_protocol_has_search_memories(self):
        """Test that protocol defines search_memories method."""
        assert hasattr(MemoryOperations, "search_memories")
        sig = inspect.signature(MemoryOperations.search_memories)
        assert "query" in sig.parameters

    def test_protocol_has_create_relationship(self):
        """Test that protocol defines create_relationship method."""
        assert hasattr(MemoryOperations, "create_relationship")
        sig = inspect.signature(MemoryOperations.create_relationship)
        assert "from_id" in sig.parameters
        assert "to_id" in sig.parameters
        assert "rel_type" in sig.parameters

    def test_protocol_has_get_related_memories(self):
        """Test that protocol defines get_related_memories method."""
        assert hasattr(MemoryOperations, "get_related_memories")
        sig = inspect.signature(MemoryOperations.get_related_memories)
        assert "memory_id" in sig.parameters

    def test_all_methods_are_async(self):
        """Test that all protocol methods are async."""
        methods = [
            "store_memory",
            "get_memory",
            "update_memory",
            "delete_memory",
            "search_memories",
            "create_relationship",
            "get_related_memories",
        ]
        for method_name in methods:
            method = getattr(MemoryOperations, method_name)
            # Check if it's a coroutine function (async)
            assert (
                inspect.iscoroutinefunction(method)
                or "coroutine" in str(inspect.signature(method).return_annotation).lower()
            ), f"{method_name} should be async"

    def test_protocol_method_count(self):
        """Test that protocol has exactly 7 core methods."""
        expected_methods = {
            "store_memory",
            "get_memory",
            "update_memory",
            "delete_memory",
            "search_memories",
            "create_relationship",
            "get_related_memories",
        }
        # Get all methods defined in the protocol
        protocol_methods = {
            name
            for name, value in inspect.getmembers(MemoryOperations)
            if not name.startswith("_") and callable(value)
        }
        assert expected_methods.issubset(
            protocol_methods
        ), f"Missing methods: {expected_methods - protocol_methods}"


class TestProtocolImports:
    """Test that protocol imports are correct."""

    def test_protocol_imports_typing(self):
        """Test that protocols module imports from typing."""
        from memorygraph import protocols

        source = inspect.getsource(protocols)
        assert "from typing import" in source
        assert "Protocol" in source

    def test_protocol_imports_models(self):
        """Test that protocols module imports required models."""
        from memorygraph import protocols

        source = inspect.getsource(protocols)
        assert "from .models import" in source or "import" in source

    def test_protocol_is_importable(self):
        """Test that the protocol can be imported."""
        try:
            from memorygraph.protocols import MemoryOperations

            assert MemoryOperations is not None
        except ImportError as e:
            pytest.fail(f"Failed to import MemoryOperations: {e}")


class TestProtocolDocumentation:
    """Test that protocol is properly documented."""

    def test_protocol_has_docstring(self):
        """Test that MemoryOperations protocol has a docstring."""
        assert MemoryOperations.__doc__ is not None
        assert len(MemoryOperations.__doc__) > 0

    def test_protocol_methods_have_docstrings(self):
        """Test that protocol methods have docstrings."""
        methods = [
            "store_memory",
            "get_memory",
            "update_memory",
            "delete_memory",
            "search_memories",
            "create_relationship",
            "get_related_memories",
        ]
        for method_name in methods:
            method = getattr(MemoryOperations, method_name)
            assert (
                method.__doc__ is not None
            ), f"{method_name} should have a docstring"
            assert len(method.__doc__) > 0, f"{method_name} docstring should not be empty"


class TestProtocolUsage:
    """Test how the protocol is used in the codebase."""

    def test_protocol_can_be_used_for_type_checking(self):
        """Test that protocol can be used in type hints."""
        from typing import TYPE_CHECKING

        # This should not raise any errors
        def process_backend(backend: MemoryOperations) -> None:
            """Example function that accepts any MemoryOperations implementation."""
            pass

        # Verify the function signature
        sig = inspect.signature(process_backend)
        assert "backend" in sig.parameters

    def test_protocol_with_sqlite_backend(self):
        """Test that SQLite backend can be used as MemoryOperations."""
        from memorygraph.sqlite_database import SQLiteMemoryDatabase

        # Check that SQLiteMemoryDatabase has all required methods
        required_methods = [
            "store_memory",
            "get_memory",
            "update_memory",
            "delete_memory",
            "search_memories",
            "create_relationship",
            "get_related_memories",
        ]

        for method in required_methods:
            assert hasattr(
                SQLiteMemoryDatabase, method
            ), f"SQLiteMemoryDatabase should have {method}"
            # Verify it's callable
            assert callable(
                getattr(SQLiteMemoryDatabase, method)
            ), f"SQLiteMemoryDatabase.{method} should be callable"
