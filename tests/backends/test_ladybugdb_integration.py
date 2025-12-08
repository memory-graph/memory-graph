"""
Integration tests for LadybugDB backend.

These tests use real real_ladybug (if available) to test the full backend implementation.
Tests are skipped if real_ladybug is not installed.
"""

import pytest
import uuid
from datetime import datetime
import tempfile
import os

LADYBUGDB_AVAILABLE = False
SKIP_REASON = "real_ladybug not installed"

try:
    import real_ladybug as lb

    # Check if real_ladybug is available and functional
    if hasattr(lb, "Database") and callable(lb.Database):
        LADYBUGDB_AVAILABLE = True
    else:
        SKIP_REASON = "real_ladybug.Database not available"

except ImportError:
    SKIP_REASON = "real_ladybug not installed"
except Exception as e:
    SKIP_REASON = f"real_ladybug import failed: {e}"

# Import LadybugDBBackend only if real_ladybug is available
if LADYBUGDB_AVAILABLE:
    from memorygraph.backends.ladybugdb_backend import LadybugDBBackend


@pytest.mark.skipif(not LADYBUGDB_AVAILABLE, reason=SKIP_REASON)
class TestLadybugDBIntegration:
    """Integration tests for LadybugDB backend with real database."""

    @pytest.fixture
    async def backend(self):
        """Create a LadybugDB backend with temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        backend = LadybugDBBackend(db_path=db_path, graph_name="test_graph")

        try:
            connected = await backend.connect()
            if not connected:
                pytest.skip("Could not connect to LadybugDB")
            yield backend
        finally:
            await backend.disconnect()
            # Clean up the temporary database file
            try:
                os.unlink(db_path)
            except OSError:
                pass  # File may already be deleted or inaccessible
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_basic_connection(self, backend):
        """Test basic connection and disconnection."""
        assert backend._connected is True
        assert backend.client is not None
        assert backend.graph is not None

        await backend.disconnect()
        assert backend._connected is False

    @pytest.mark.asyncio
    async def test_create_and_query_node(self, backend):
        """Test creating a node and querying it."""
        # Use unique table name to avoid conflicts
        table_name = f"TestNode_{uuid.uuid4().hex[:8]}"

        # LadybugDB requires defining the node table schema first
        schema_query = f"""
        CREATE NODE TABLE {table_name}(
            id STRING,
            name STRING,
            type STRING,
            created_at STRING,
            PRIMARY KEY (id)
        )
        """
        await backend.execute_query(schema_query, write=True)

        # Create a test node
        node_id = str(uuid.uuid4())
        create_query = f"""
        CREATE (n:{table_name} {{
            id: '{node_id}',
            name: 'test_node',
            type: 'test',
            created_at: '{datetime.now().isoformat()}'
        }})
        """

        await backend.execute_query(create_query, write=True)

        # Query the node back
        query = f"MATCH (n:{table_name} {{name: 'test_node'}}) RETURN n.id, n.name"
        result = await backend.execute_query(query)

        assert len(result) == 1
        # LadybugDB returns results as lists
        row = result[0]
        assert len(row) == 2  # id and name
        assert row[1] == "test_node"  # name field
        assert row[0] == node_id  # id field

    @pytest.mark.asyncio
    async def test_create_relationship(self, backend):
        """Test creating nodes and relationships."""
        # Use unique table names
        node_table = f"TestNode_{uuid.uuid4().hex[:8]}"
        rel_table = f"CONNECTS_TO_{uuid.uuid4().hex[:8]}"

        # Define node table schema
        schema_query = f"""
        CREATE NODE TABLE {node_table}(
            id STRING,
            name STRING,
            PRIMARY KEY (id)
        )
        """
        await backend.execute_query(schema_query, write=True)

        # Define relationship table schema
        rel_schema_query = f"""
        CREATE REL TABLE {rel_table}(
            FROM {node_table} TO {node_table}
        )
        """
        await backend.execute_query(rel_schema_query, write=True)

        # Create two nodes
        node1_id = str(uuid.uuid4())
        node2_id = str(uuid.uuid4())

        create_nodes_query = f"""
        CREATE (n1:{node_table} {{id: '{node1_id}', name: 'node1'}}),
               (n2:{node_table} {{id: '{node2_id}', name: 'node2'}})
        """
        await backend.execute_query(create_nodes_query, write=True)

        # Create relationship
        create_rel_query = f"""
        MATCH (n1:{node_table} {{id: '{node1_id}'}}), (n2:{node_table} {{id: '{node2_id}'}})
        CREATE (n1)-[r:{rel_table}]->(n2)
        """
        await backend.execute_query(create_rel_query, write=True)

        # Query the relationship
        query = f"""
        MATCH (n1:{node_table} {{name: 'node1'}})-[r:{rel_table}]->(n2:{node_table} {{name: 'node2'}})
        RETURN count(r) as rel_count
        """
        result = await backend.execute_query(query)

        assert len(result) == 1
        row = result[0]
        assert row[0] == 1  # count should be 1

    @pytest.mark.asyncio
    async def test_query_with_no_results(self, backend):
        """Test query that returns no results."""
        # Try to query for non-existent table - this should fail gracefully
        try:
            query = "MATCH (n:NonExistentLabel) RETURN n"
            result = await backend.execute_query(query)
            # If it succeeds, result should be empty
            assert result == []
        except SchemaError:
            # LadybugDB raises an error for non-existent tables, which is expected
            pass

    @pytest.mark.asyncio
    async def test_multiple_queries(self, backend):
        """Test executing multiple queries in sequence."""
        # Use unique table name
        table_name = f"BatchNode_{uuid.uuid4().hex[:8]}"

        # Define table schema first
        schema_query = f"""
        CREATE NODE TABLE {table_name}(
            id INT64,
            name STRING,
            PRIMARY KEY (id)
        )
        """
        await backend.execute_query(schema_query, write=True)

        # Create multiple nodes
        for i in range(3):
            create_query = f"CREATE (n:{table_name} {{id: {i}, name: 'node_{i}'}})"
            await backend.execute_query(create_query, write=True)

        # Query all nodes
        query = f"MATCH (n:{table_name}) RETURN n.id, n.name ORDER BY n.id"
        result = await backend.execute_query(query)

        assert len(result) == 3
        # Check that we have 3 results
        for i, row_data in enumerate(result):
            row = row_data
            assert len(row) == 2  # id and name
            assert row[1] == f"node_{i}"  # name field

    @pytest.mark.asyncio
    async def test_error_handling(self, backend):
        """Test error handling for invalid queries."""
        with pytest.raises(SchemaError):
            await backend.execute_query("INVALID CYPHER QUERY")

    @pytest.mark.asyncio
    async def test_transaction_isolation(self, backend):
        """Test that operations are properly isolated."""
        # Use fixed table name for isolation testing
        table_name = "IsolationTest"

        # Define table schema
        schema_query = f"""
        CREATE NODE TABLE {table_name}(
            id INT64,
            PRIMARY KEY (id)
        )
        """
        await backend.execute_query(schema_query, write=True)

        # Create a node
        await backend.execute_query(f"CREATE (n:{table_name} {{id: 1}})", write=True)

        # Verify it exists in same connection
        result = await backend.execute_query(
            f"MATCH (n:{table_name} {{id: 1}}) RETURN count(n) as count"
        )
        assert len(result) == 1
        row = result[0]
        assert row[0] == 1  # count should be 1

        # Create another backend instance to same database
        backend2 = LadybugDBBackend(
            db_path=backend.db_path, graph_name=backend.graph_name
        )
        await backend2.connect()

        try:
            # Should see the node from the other connection
            result2 = await backend2.execute_query(
                f"MATCH (n:{table_name} {{id: 1}}) RETURN count(n) as count"
            )
            assert len(result2) == 1
            row2 = result2[0]
            assert row2[0] == 1  # count should be 1
        finally:
            await backend2.disconnect()


# Import here to avoid import errors when real_ladybug is not available
if LADYBUGDB_AVAILABLE:
    from memorygraph.backends.ladybugdb_backend import LadybugDBBackend
    from memorygraph.models import SchemaError
else:
    # Dummy classes for type checking when not available
    LadybugDBBackend = None
    SchemaError = Exception
