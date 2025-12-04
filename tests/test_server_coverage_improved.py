"""
Additional tests for server.py to improve test coverage to >70%.

This test file targets uncovered code paths in server.py:
- Main entry point function
- Server initialization edge cases
- Tool collection and filtering
- Cleanup scenarios
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from mcp.server import Server

from memorygraph.server import ClaudeMemoryServer, main
from memorygraph.models import DatabaseConnectionError
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend


class TestServerInitAndCleanup:
    """Test server initialization and cleanup scenarios."""

    @pytest.mark.asyncio
    async def test_initialize_with_sqlite_backend(self):
        """Test initialization chooses SQLiteMemoryDatabase for SQLite backend."""
        server = ClaudeMemoryServer()

        mock_backend = Mock(spec=SQLiteFallbackBackend)
        mock_backend.backend_name = lambda: "sqlite"

        with patch('memorygraph.backends.factory.BackendFactory.create_backend', return_value=mock_backend):
            with patch('memorygraph.server.SQLiteMemoryDatabase') as MockSQLiteDB:
                mock_sqlite_db = MockSQLiteDB.return_value
                mock_sqlite_db.initialize_schema = AsyncMock()

                await server.initialize()

                # Should use SQLiteMemoryDatabase for SQLite backend
                MockSQLiteDB.assert_called_once_with(mock_backend)
                assert server.memory_db == mock_sqlite_db

    @pytest.mark.asyncio
    async def test_initialize_with_non_sqlite_backend(self):
        """Test initialization uses MemoryDatabase for non-SQLite backends."""
        server = ClaudeMemoryServer()

        mock_backend = Mock()
        mock_backend.backend_name = lambda: "neo4j"

        with patch('memorygraph.backends.factory.BackendFactory.create_backend', return_value=mock_backend):
            with patch('memorygraph.server.MemoryDatabase') as MockMemoryDB:
                mock_memory_db = MockMemoryDB.return_value
                mock_memory_db.initialize_schema = AsyncMock()

                await server.initialize()

                # Should use MemoryDatabase for non-SQLite backends
                MockMemoryDB.assert_called_once_with(mock_backend)
                assert server.memory_db == mock_memory_db

    @pytest.mark.asyncio
    async def test_initialize_failure_propagates(self):
        """Test that initialization failures are propagated."""
        server = ClaudeMemoryServer()

        with patch('memorygraph.backends.factory.BackendFactory.create_backend', side_effect=DatabaseConnectionError("Connection failed")):
            with pytest.raises(DatabaseConnectionError) as exc_info:
                await server.initialize()

            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleanup_with_connection(self):
        """Test cleanup properly closes connection."""
        server = ClaudeMemoryServer()

        mock_connection = AsyncMock()
        mock_connection.close = AsyncMock()
        server.db_connection = mock_connection

        await server.cleanup()

        mock_connection.close.assert_called_once()
        # Connection should be None after cleanup (implied by server code)

    @pytest.mark.asyncio
    async def test_cleanup_without_connection(self):
        """Test cleanup when no connection exists."""
        server = ClaudeMemoryServer()
        server.db_connection = None

        # Should not raise any errors
        await server.cleanup()


class TestToolCollection:
    """Test tool collection and filtering."""

    def test_collect_all_tools_includes_all_categories(self):
        """Test that _collect_all_tools includes all tool categories."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        # Should include basic tools
        tool_names = [tool.name for tool in all_tools]
        assert "store_memory" in tool_names
        assert "get_memory" in tool_names
        assert "search_memories" in tool_names
        assert "recall_memories" in tool_names

        # Should include advanced relationship tools
        assert "find_memory_path" in tool_names, f"find_memory_path not found in {tool_names}"
        assert "create_relationship" in tool_names, f"create_relationship not found in {tool_names}"

        # Should include intelligence tools
        assert "find_similar_solutions" in tool_names, f"find_similar_solutions not found in {tool_names}"

        # Verify we have a reasonable total count
        assert len(all_tools) >= 10, f"Expected at least 10 tools, got {len(all_tools)}"

    def test_tool_profile_full_includes_all(self):
        """Test that FULL profile includes all tools."""
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=None):
            server = ClaudeMemoryServer()
            all_tools = server._collect_all_tools()

            # Full profile should have all tools
            assert len(server.tools) == len(all_tools)
            assert len(server.tools) > 20  # Should have many tools

    def test_tool_profile_filtering(self):
        """Test that tool profile filtering works."""
        # Mock Config to return a limited set of tool names
        enabled_tools = ["store_memory", "get_memory", "search_memories"]
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=enabled_tools):
            server = ClaudeMemoryServer()

            # Should only have the enabled tools
            assert len(server.tools) == 3
            tool_names = [tool.name for tool in server.tools]
            assert set(tool_names) == set(enabled_tools)


class TestMainEntryPoint:
    """Test the main() entry point function."""

    @pytest.mark.asyncio
    async def test_main_normal_execution(self):
        """Test main function executes initialization and server run."""
        with patch('memorygraph.server.ClaudeMemoryServer') as MockServer:
            mock_server = MockServer.return_value
            mock_server.initialize = AsyncMock()
            mock_server.cleanup = AsyncMock()
            mock_server.server = Mock()
            mock_server.server.get_capabilities = Mock(return_value={})
            mock_server.server.run = AsyncMock()

            with patch('memorygraph.server.stdio_server') as mock_stdio:
                # Mock the async context manager
                mock_read = AsyncMock()
                mock_write = AsyncMock()
                mock_stdio.return_value.__aenter__.return_value = (mock_read, mock_write)
                mock_stdio.return_value.__aexit__.return_value = AsyncMock()

                # Run main
                await main()

                # Verify initialization was called
                mock_server.initialize.assert_called_once()

                # Verify server.run was called
                mock_server.server.run.assert_called_once()

                # Verify cleanup was called
                mock_server.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt_handled(self):
        """Test main handles KeyboardInterrupt gracefully."""
        with patch('memorygraph.server.ClaudeMemoryServer') as MockServer:
            mock_server = MockServer.return_value
            mock_server.initialize = AsyncMock()
            mock_server.cleanup = AsyncMock()
            mock_server.server = Mock()
            mock_server.server.get_capabilities = Mock(return_value={})

            with patch('memorygraph.server.stdio_server') as mock_stdio:
                # Make stdio_server raise KeyboardInterrupt
                mock_stdio.return_value.__aenter__.side_effect = KeyboardInterrupt()

                # Should not raise, should handle gracefully
                await main()

                # Cleanup should still be called
                mock_server.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_exception_logged_and_raised(self):
        """Test main logs exceptions and raises them."""
        with patch('memorygraph.server.ClaudeMemoryServer') as MockServer:
            mock_server = MockServer.return_value
            mock_server.initialize = AsyncMock(side_effect=Exception("Init error"))
            mock_server.cleanup = AsyncMock()

            with pytest.raises(Exception) as exc_info:
                await main()

            assert "Init error" in str(exc_info.value)

            # Cleanup should still be called
            mock_server.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_creates_notification_options(self):
        """Test main creates NotificationOptions and capabilities correctly."""
        with patch('memorygraph.server.ClaudeMemoryServer') as MockServer:
            mock_server = MockServer.return_value
            mock_server.initialize = AsyncMock()
            mock_server.cleanup = AsyncMock()
            mock_mcp_server = Mock()
            mock_server.server = mock_mcp_server
            mock_mcp_server.run = AsyncMock()
            mock_mcp_server.get_capabilities = Mock(return_value={"test": "capabilities"})

            with patch('memorygraph.server.stdio_server') as mock_stdio:
                mock_read = AsyncMock()
                mock_write = AsyncMock()
                mock_stdio.return_value.__aenter__.return_value = (mock_read, mock_write)
                mock_stdio.return_value.__aexit__.return_value = AsyncMock()

                with patch('memorygraph.server.NotificationOptions') as MockNotificationOptions:
                    mock_notification_opts = MockNotificationOptions.return_value

                    await main()

                    # Verify NotificationOptions was created
                    MockNotificationOptions.assert_called_once()

                    # Verify get_capabilities was called with notification_options
                    mock_mcp_server.get_capabilities.assert_called_once_with(
                        notification_options=mock_notification_opts,
                        experimental_capabilities={}
                    )


class TestServerHandlerEdgeCases:
    """Test edge cases in server handler logic."""

    def test_server_initialization_creates_required_objects(self):
        """Test server __init__ creates required objects."""
        server = ClaudeMemoryServer()

        assert server.server is not None
        assert server.db_connection is None  # Not yet initialized
        assert server.memory_db is None  # Not yet initialized
        assert server.advanced_handlers is None  # Not yet initialized
        assert len(server.tools) > 0  # Tools should be collected


class TestServerToolSchemas:
    """Test tool input schemas are valid."""

    def test_recall_memories_has_pagination_params(self):
        """Test recall_memories tool has pagination parameters."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        recall_tool = next((t for t in all_tools if t.name == "recall_memories"), None)
        assert recall_tool is not None

        schema = recall_tool.inputSchema
        assert "limit" in schema["properties"]
        assert "offset" in schema["properties"]
        assert schema["properties"]["limit"]["minimum"] == 1
        assert schema["properties"]["limit"]["maximum"] == 1000
        assert schema["properties"]["offset"]["minimum"] == 0

    def test_search_memories_has_pagination_params(self):
        """Test search_memories tool has pagination parameters."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        search_tool = next((t for t in all_tools if t.name == "search_memories"), None)
        assert search_tool is not None

        schema = search_tool.inputSchema
        assert "limit" in schema["properties"]
        assert "offset" in schema["properties"]
        assert schema["properties"]["limit"]["minimum"] == 1
        assert schema["properties"]["limit"]["maximum"] == 1000

    def test_get_memory_has_relationships_param(self):
        """Test get_memory tool has include_relationships parameter."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        get_tool = next((t for t in all_tools if t.name == "get_memory"), None)
        assert get_tool is not None

        schema = get_tool.inputSchema
        assert "include_relationships" in schema["properties"]
        assert schema["properties"]["include_relationships"]["type"] == "boolean"

    def test_get_recent_activity_has_days_param(self):
        """Test get_recent_activity tool has days parameter."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        activity_tool = next((t for t in all_tools if t.name == "get_recent_activity"), None)
        assert activity_tool is not None

        schema = activity_tool.inputSchema
        assert "days" in schema["properties"]
        assert schema["properties"]["days"]["minimum"] == 1
        assert schema["properties"]["days"]["maximum"] == 365


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
