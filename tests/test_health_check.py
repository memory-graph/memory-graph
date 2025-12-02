"""
Tests for health check functionality in CLI.

Tests cover:
- Successful health check with all backends
- Backend connection failure
- Database unavailable
- Health check timeout
- JSON output format
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC

from memorygraph.cli import perform_health_check
from memorygraph.backends.sqlite_fallback import SQLiteFallbackBackend


class TestHealthCheckSuccess:
    """Test successful health check scenarios."""

    @pytest.mark.asyncio
    async def test_health_check_sqlite_backend(self):
        """Test health check with SQLite backend."""
        result = await perform_health_check(timeout=5.0)

        assert result["status"] == "healthy"
        assert result["backend_type"] in ["sqlite", "neo4j", "memgraph", "falkordb", "falkordblite"]
        assert "connected" in result
        assert result["connected"] is True
        assert "version" in result or "backend_type" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_health_check_includes_statistics(self):
        """Test that health check includes memory statistics."""
        result = await perform_health_check(timeout=5.0)

        # Should have statistics if backend is connected
        if result["connected"]:
            assert "statistics" in result or "memory_count" in result.get("statistics", {})

    @pytest.mark.asyncio
    async def test_health_check_json_output(self):
        """Test that health check result can be serialized to JSON."""
        result = await perform_health_check(timeout=5.0)

        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

        # Should be parseable
        parsed = json.loads(json_str)
        assert parsed["status"] in ["healthy", "unhealthy"]


class TestHealthCheckFailure:
    """Test health check failure scenarios."""

    @pytest.mark.asyncio
    async def test_health_check_backend_failure(self):
        """Test health check when backend connection fails."""
        with patch("memorygraph.backends.factory.BackendFactory.create_backend") as mock_factory:
            mock_factory.side_effect = Exception("Connection failed")

            result = await perform_health_check(timeout=5.0)

            assert result["status"] == "unhealthy"
            assert result["connected"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check respects timeout."""
        with patch("memorygraph.backends.factory.BackendFactory.create_backend") as mock_factory:
            # Create a mock that sleeps longer than timeout
            async def slow_connect():
                await asyncio.sleep(10)
                return MagicMock()

            mock_factory.side_effect = slow_connect

            start_time = asyncio.get_event_loop().time()
            result = await perform_health_check(timeout=1.0)
            elapsed = asyncio.get_event_loop().time() - start_time

            # Should timeout within reasonable time
            assert elapsed < 2.0
            assert result["status"] == "unhealthy"
            assert "timeout" in result.get("error", "").lower() or "error" in result

    @pytest.mark.asyncio
    async def test_health_check_disconnected_backend(self):
        """Test health check with backend that reports disconnected."""
        with patch("memorygraph.backends.factory.BackendFactory.create_backend") as mock_factory:
            mock_backend = AsyncMock()
            mock_backend.health_check.return_value = {
                "connected": False,
                "backend_type": "sqlite",
                "error": "Database not connected"
            }
            mock_factory.return_value = mock_backend

            result = await perform_health_check(timeout=5.0)

            assert result["status"] == "unhealthy"
            assert result["connected"] is False


class TestHealthCheckOutput:
    """Test health check output formatting."""

    @pytest.mark.asyncio
    async def test_health_check_includes_required_fields(self):
        """Test that health check result includes all required fields."""
        result = await perform_health_check(timeout=5.0)

        # Required fields
        assert "status" in result
        assert "connected" in result
        assert "backend_type" in result
        assert "timestamp" in result

        # Status should be one of the valid values
        assert result["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_health_check_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        result = await perform_health_check(timeout=5.0)

        # Should be able to parse the timestamp
        timestamp = datetime.fromisoformat(result["timestamp"])
        assert timestamp is not None

        # Should be recent (within last minute)
        now = datetime.now(UTC)
        time_diff = abs((now - timestamp).total_seconds())
        assert time_diff < 60  # Within 60 seconds

    @pytest.mark.asyncio
    async def test_health_check_version_info(self):
        """Test that version information is included when available."""
        result = await perform_health_check(timeout=5.0)

        # If connected, should have version info
        if result["connected"]:
            # Version might be at top level or in nested structure
            assert "version" in result or "backend_version" in result
