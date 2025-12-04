"""
Shared fixtures for backend tests.

This file contains reusable fixtures for mocking backends,
especially for Memgraph and Neo4j-based backends.
"""

import pytest
from unittest.mock import AsyncMock, Mock


@pytest.fixture
def mock_memgraph_driver():
    """Create a mock Memgraph/Neo4j driver with common setup."""
    mock_driver = AsyncMock()
    mock_driver.verify_connectivity = AsyncMock()
    mock_driver.close = AsyncMock()
    return mock_driver


@pytest.fixture
def mock_memgraph_session():
    """Create a mock Memgraph/Neo4j session with common setup."""
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    return mock_session


@pytest.fixture
def mock_memgraph_transaction():
    """Create a mock Memgraph/Neo4j transaction with common setup."""
    mock_tx = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[])
    mock_tx.run = AsyncMock(return_value=mock_result)
    return mock_tx


@pytest.fixture
def mock_memgraph_database(mock_memgraph_driver, mock_memgraph_session, mock_memgraph_transaction):
    """
    Create a complete mock Memgraph/Neo4j database setup.

    Returns a tuple of (mock_db_class, mock_driver, mock_session, mock_tx)
    suitable for patching AsyncGraphDatabase.
    """

    async def execute_write_side_effect(fn, *args):
        """Execute the transaction function with the mock transaction."""
        return await fn(mock_memgraph_transaction, *args)

    mock_memgraph_session.execute_write = AsyncMock(side_effect=execute_write_side_effect)
    mock_memgraph_driver.session = Mock(return_value=mock_memgraph_session)

    mock_db_class = Mock()
    mock_db_class.driver.return_value = mock_memgraph_driver

    return (mock_db_class, mock_memgraph_driver, mock_memgraph_session, mock_memgraph_transaction)
