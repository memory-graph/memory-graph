"""
Tests for server initialization and tool collection.

These tests exercise actual code paths in server.py to increase coverage.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from memorygraph.server import ClaudeMemoryServer
from memorygraph.config import Config


class TestServerInitialization:
    """Test server initialization and setup."""

    def test_server_creation(self):
        """Test that server can be created."""
        server = ClaudeMemoryServer()
        assert server is not None
        assert server.server is not None
        assert server.db_connection is None
        assert server.memory_db is None

    def test_tool_collection_all_profiles(self):
        """Test that tools are collected correctly."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        # Should have basic tools (8) + advanced + intelligence + integration + proactive
        assert len(all_tools) > 8

        # Check that basic tools are present
        tool_names = [tool.name for tool in all_tools]
        assert "store_memory" in tool_names
        assert "get_memory" in tool_names
        assert "search_memories" in tool_names
        assert "create_relationship" in tool_names

    @patch.dict('os.environ', {'TOOL_PROFILE': 'lite'})
    def test_tool_filtering_lite_profile(self):
        """Test that lite profile filters tools correctly."""
        # Need to reload Config to pick up env var
        from importlib import reload
        from memorygraph import config as config_module
        reload(config_module)
        from memorygraph.config import Config as ReloadedConfig

        # Create server with patched config
        with patch('memorygraph.server.Config', ReloadedConfig):
            server = ClaudeMemoryServer()

            # Lite profile should have fewer tools
            assert len(server.tools) < 50  # Lite has limited tools
            tool_names = [tool.name for tool in server.tools]

            # Basic tools should be present
            assert "store_memory" in tool_names
            assert "get_memory" in tool_names

    @patch.dict('os.environ', {'TOOL_PROFILE': 'standard'})
    def test_tool_filtering_standard_profile(self):
        """Test that standard profile filters tools correctly."""
        from importlib import reload
        from memorygraph import config as config_module
        reload(config_module)
        from memorygraph.config import Config as ReloadedConfig

        with patch('memorygraph.server.Config', ReloadedConfig):
            server = ClaudeMemoryServer()

            # Standard profile should have moderate number of tools
            tool_names = [tool.name for tool in server.tools]

            # Core tools should be present
            assert "store_memory" in tool_names
            assert "search_memories" in tool_names

    def test_tool_filtering_full_profile(self):
        """Test that full profile includes all tools."""
        with patch('memorygraph.server.Config.get_enabled_tools', return_value=None):
            server = ClaudeMemoryServer()
            all_tools = server._collect_all_tools()

            # Full profile: all tools enabled
            assert len(server.tools) == len(all_tools)

    def test_handler_registration(self):
        """Test that MCP handlers are registered."""
        server = ClaudeMemoryServer()

        # Handlers should be registered during init
        # Check that the server has the necessary handler methods
        assert hasattr(server, '_handle_store_memory')
        assert hasattr(server, '_handle_get_memory')
        assert hasattr(server, '_handle_search_memories')
        assert hasattr(server, '_handle_update_memory')
        assert hasattr(server, '_handle_delete_memory')
        assert hasattr(server, '_handle_create_relationship')
        assert hasattr(server, '_handle_get_related_memories')
        assert hasattr(server, '_handle_get_memory_statistics')

    @pytest.mark.asyncio
    async def test_initialize_server(self):
        """Test server initialization with database."""
        server = ClaudeMemoryServer()

        # Mock the backend factory
        mock_backend = AsyncMock()
        mock_backend.backend_name = 'sqlite'
        mock_backend.close = AsyncMock()

        # Mock MemoryDatabase to avoid actual database operations
        mock_memory_db = AsyncMock()
        mock_memory_db.initialize_schema = AsyncMock()

        with patch('memorygraph.backends.factory.BackendFactory.create_backend', return_value=mock_backend):
            with patch.object(server, 'memory_db', None):
                # Directly test the parts we can control
                await server.initialize()

                # Verify that initialization happened
                assert server.db_connection is mock_backend
                assert server.memory_db is not None
                assert server.advanced_handlers is not None
                assert server.integration_handlers is not None

    @pytest.mark.asyncio
    async def test_initialize_server_failure(self):
        """Test server initialization handles errors."""
        server = ClaudeMemoryServer()

        # Mock backend factory to raise error
        with patch('memorygraph.backends.factory.BackendFactory.create_backend', side_effect=Exception("Backend error")):
            with pytest.raises(Exception) as exc_info:
                await server.initialize()

            assert "Backend error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleanup_server(self):
        """Test server cleanup."""
        server = ClaudeMemoryServer()

        # Mock a connection
        mock_connection = AsyncMock()
        mock_connection.close = AsyncMock()
        server.db_connection = mock_connection

        await server.cleanup()

        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_no_connection(self):
        """Test cleanup when no connection exists."""
        server = ClaudeMemoryServer()

        # Should not raise error
        await server.cleanup()


class TestToolSchemas:
    """Test that tool schemas are valid."""

    def test_store_memory_schema(self):
        """Test store_memory tool schema."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        store_tool = next((t for t in all_tools if t.name == "store_memory"), None)
        assert store_tool is not None

        schema = store_tool.inputSchema
        assert schema["type"] == "object"
        assert "type" in schema["properties"]
        assert "title" in schema["properties"]
        assert "content" in schema["properties"]
        assert set(schema["required"]) == {"type", "title", "content"}

    def test_search_memories_schema(self):
        """Test search_memories tool schema."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        search_tool = next((t for t in all_tools if t.name == "search_memories"), None)
        assert search_tool is not None

        schema = search_tool.inputSchema
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "memory_types" in schema["properties"]
        assert "tags" in schema["properties"]

    def test_create_relationship_schema(self):
        """Test create_relationship tool schema."""
        server = ClaudeMemoryServer()
        all_tools = server._collect_all_tools()

        rel_tool = next((t for t in all_tools if t.name == "create_relationship"), None)
        assert rel_tool is not None

        schema = rel_tool.inputSchema
        assert "from_memory_id" in schema["properties"]
        assert "to_memory_id" in schema["properties"]
        assert "relationship_type" in schema["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
