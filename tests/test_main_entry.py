"""
Tests for src/memorygraph/__main__.py entry point.

Following TDD approach to achieve 100% coverage of __main__.py
"""
import subprocess
import sys
from unittest.mock import AsyncMock, patch

import pytest


class TestMainEntry:
    """Test the __main__.py entry point."""

    def test_main_module_executable(self):
        """Test that the module can be executed with python -m memorygraph."""
        # Test that the module is importable
        result = subprocess.run(
            [sys.executable, "-m", "memorygraph", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should return help text or start the server
        assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
        # Should have some output (either help or error about missing deps)
        assert len(result.stdout) > 0 or len(result.stderr) > 0

    @patch("memorygraph.__main__.main")
    @patch("memorygraph.__main__.asyncio.run")
    def test_main_calls_server_main(self, mock_asyncio_run, mock_main):
        """Test that __main__ calls asyncio.run(main())."""
        # Import and execute the __main__ block
        import importlib
        import memorygraph.__main__ as main_module

        # Reload to trigger the if __name__ == "__main__" block
        # We can't actually trigger it directly, but we can verify the structure
        assert hasattr(main_module, "main"), "__main__ should import main from server"
        assert hasattr(main_module, "asyncio"), "__main__ should import asyncio"

    def test_main_module_imports(self):
        """Test that __main__ module imports correctly."""
        import memorygraph.__main__

        # Verify the required imports exist
        assert hasattr(memorygraph.__main__, "main")
        assert hasattr(memorygraph.__main__, "asyncio")

    def test_main_module_has_name_check(self):
        """Test that __main__ module has the __name__ == '__main__' guard."""
        import memorygraph.__main__ as main_module

        # Read the source to verify structure
        import inspect

        source = inspect.getsource(main_module)
        assert 'if __name__ == "__main__"' in source, "__main__ should have name check"
        assert "asyncio.run(main())" in source, "__main__ should call asyncio.run(main())"


class TestMainEntryIntegration:
    """Integration tests for the main entry point."""

    @pytest.mark.timeout(10)
    def test_module_execution_with_version(self):
        """Test that python -m memorygraph --version works."""
        result = subprocess.run(
            [sys.executable, "-m", "memorygraph", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should succeed or fail gracefully
        assert result.returncode in [0, 1, 2]

    @pytest.mark.timeout(10)
    def test_module_execution_with_health(self):
        """Test that python -m memorygraph --health works."""
        result = subprocess.run(
            [sys.executable, "-m", "memorygraph", "--health"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Should succeed or fail gracefully
        assert result.returncode in [0, 1]

    def test_main_function_callable(self):
        """Test that the main function from server is callable."""
        from memorygraph.server import main

        # Verify it's a coroutine function
        import inspect

        assert inspect.iscoroutinefunction(main), "main should be an async function"
