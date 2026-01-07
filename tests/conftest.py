"""
Pytest configuration and fixtures for memorygraph tests.
"""

import os
import pytest

from memorygraph.config import Config


# Store original Config values at module load time
_ORIGINAL_CONFIG = {
    'BACKEND': Config.BACKEND,
    'SQLITE_PATH': Config.SQLITE_PATH,
    'NEO4J_URI': Config.NEO4J_URI,
    'NEO4J_USER': Config.NEO4J_USER,
    'NEO4J_PASSWORD': Config.NEO4J_PASSWORD,
    'MEMGRAPH_URI': Config.MEMGRAPH_URI,
    'MEMGRAPH_USER': Config.MEMGRAPH_USER,
    'MEMGRAPH_PASSWORD': Config.MEMGRAPH_PASSWORD,
    'TURSO_PATH': Config.TURSO_PATH,
    'TURSO_DATABASE_URL': Config.TURSO_DATABASE_URL,
    'TURSO_AUTH_TOKEN': Config.TURSO_AUTH_TOKEN,
    'MEMORYGRAPH_API_KEY': Config.MEMORYGRAPH_API_KEY,
    'MEMORYGRAPH_API_URL': Config.MEMORYGRAPH_API_URL,
    'FALKORDB_HOST': Config.FALKORDB_HOST,
    'FALKORDB_PORT': Config.FALKORDB_PORT,
    'FALKORDB_PASSWORD': Config.FALKORDB_PASSWORD,
    'FALKORDBLITE_PATH': Config.FALKORDBLITE_PATH,
    'LADYBUGDB_PATH': Config.LADYBUGDB_PATH,
    'TOOL_PROFILE': Config.TOOL_PROFILE,
    'LOG_LEVEL': Config.LOG_LEVEL,
}


@pytest.fixture(autouse=True)
def reset_config():
    """Reset Config class attributes to their original values after each test.

    This prevents test pollution where one test modifies Config.BACKEND
    and subsequent tests see the modified value.
    """
    # Run the test
    yield

    # Reset Config to original values
    for key, value in _ORIGINAL_CONFIG.items():
        if hasattr(Config, key):
            setattr(Config, key, value)
