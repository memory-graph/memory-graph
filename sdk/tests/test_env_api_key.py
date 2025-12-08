"""Tests for environment variable API key support."""
import os
import pytest
from memorygraphsdk import MemoryGraphClient, AsyncMemoryGraphClient
from memorygraphsdk.exceptions import AuthenticationError


def test_client_without_api_key_raises_error():
    """Test that client initialization without API key raises error."""
    # Ensure env var is not set
    original = os.environ.get("MEMORYGRAPH_API_KEY")
    if "MEMORYGRAPH_API_KEY" in os.environ:
        del os.environ["MEMORYGRAPH_API_KEY"]

    try:
        with pytest.raises(AuthenticationError) as exc_info:
            MemoryGraphClient()

        assert "API key required" in str(exc_info.value)
        assert "MEMORYGRAPH_API_KEY" in str(exc_info.value)
    finally:
        # Restore original value
        if original is not None:
            os.environ["MEMORYGRAPH_API_KEY"] = original


def test_client_with_env_var():
    """Test that client can read API key from environment variable."""
    original = os.environ.get("MEMORYGRAPH_API_KEY")

    try:
        os.environ["MEMORYGRAPH_API_KEY"] = "mgraph_test_key"
        client = MemoryGraphClient()
        assert client.api_key == "mgraph_test_key"
    finally:
        if original is not None:
            os.environ["MEMORYGRAPH_API_KEY"] = original
        else:
            del os.environ["MEMORYGRAPH_API_KEY"]


def test_client_explicit_key_overrides_env_var():
    """Test that explicit API key takes precedence over environment variable."""
    original = os.environ.get("MEMORYGRAPH_API_KEY")

    try:
        os.environ["MEMORYGRAPH_API_KEY"] = "mgraph_env_key"
        client = MemoryGraphClient(api_key="mgraph_explicit_key")
        assert client.api_key == "mgraph_explicit_key"
    finally:
        if original is not None:
            os.environ["MEMORYGRAPH_API_KEY"] = original
        else:
            del os.environ["MEMORYGRAPH_API_KEY"]


def test_async_client_without_api_key_raises_error():
    """Test that async client initialization without API key raises error."""
    original = os.environ.get("MEMORYGRAPH_API_KEY")
    if "MEMORYGRAPH_API_KEY" in os.environ:
        del os.environ["MEMORYGRAPH_API_KEY"]

    try:
        with pytest.raises(AuthenticationError) as exc_info:
            AsyncMemoryGraphClient()

        assert "API key required" in str(exc_info.value)
        assert "MEMORYGRAPH_API_KEY" in str(exc_info.value)
    finally:
        if original is not None:
            os.environ["MEMORYGRAPH_API_KEY"] = original


def test_async_client_with_env_var():
    """Test that async client can read API key from environment variable."""
    original = os.environ.get("MEMORYGRAPH_API_KEY")

    try:
        os.environ["MEMORYGRAPH_API_KEY"] = "mgraph_test_key"
        client = AsyncMemoryGraphClient()
        assert client.api_key == "mgraph_test_key"
    finally:
        if original is not None:
            os.environ["MEMORYGRAPH_API_KEY"] = original
        else:
            del os.environ["MEMORYGRAPH_API_KEY"]


def test_async_client_explicit_key_overrides_env_var():
    """Test that explicit API key takes precedence over env var in async client."""
    original = os.environ.get("MEMORYGRAPH_API_KEY")

    try:
        os.environ["MEMORYGRAPH_API_KEY"] = "mgraph_env_key"
        client = AsyncMemoryGraphClient(api_key="mgraph_explicit_key")
        assert client.api_key == "mgraph_explicit_key"
    finally:
        if original is not None:
            os.environ["MEMORYGRAPH_API_KEY"] = original
        else:
            del os.environ["MEMORYGRAPH_API_KEY"]
