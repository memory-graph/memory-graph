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
        # Results are returned as dictionaries
        row = result[0]
        assert "n.name" in row  # name field
        assert "n.id" in row  # id field
        assert row["n.name"] == "test_node"  # name field
        assert row["n.id"] == node_id  # id field

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
        assert row["rel_count"] == 1  # count should be 1

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
            assert "n.id" in row and "n.name" in row
            assert row["n.name"] == f"node_{i}"  # name field

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
        assert row["count"] == 1  # count should be 1

        # Create another backend instance to same database
        backend2 = LadybugDBBackend(
            db_path=backend.db_path, graph_name=backend.graph_name
        )
        await backend2.connect()

        try:
            # Should see node from other connection
            result2 = await backend2.execute_query(
                f"MATCH (n:{table_name} {{id: 1}}) RETURN count(n) as count"
            )
            assert len(result2) == 1
            row2 = result2[0]
            assert row2["count"] == 1  # count should be 1
        finally:
            await backend2.disconnect()

    @pytest.mark.asyncio
    async def test_store_and_retrieve_memory_with_parameters(self, backend):
        """Test storing a Memory node and retrieving it with parameterized queries."""
        # Initialize the standard Memory schema
        await backend.initialize_schema()

        # Create a memory with all required fields
        memory_id = str(uuid.uuid4())
        title = "User Preference"
        content = "I like icecream"
        memory_type = "general"
        importance = 0.9
        confidence = 1.0
        created_at = datetime.now().isoformat()
        updated_at = datetime.now().isoformat()

        # Store the memory
        create_query = f"""
        CREATE (m:Memory {{
            id: '{memory_id}',
            type: '{memory_type}',
            title: '{title}',
            content: '{content}',
            importance: {importance},
            confidence: {confidence},
            created_at: '{created_at}',
            updated_at: '{updated_at}',
            summary: '',
            tags: '[]',
            context_project_path: '',
            context_file_path: '',
            context_line_start: -1,
            context_line_end: -1,
            context_commit_hash: '',
            context_branch: '',
            metadata: '{{}}'
        }})
        RETURN m
        """

        result = await backend.execute_query(create_query, write=True)
        assert len(result) == 1
        assert len(result[0]) == 1  # Should return the created memory

        # Retrieve the memory using parameterized query
        # This tests the critical fix: parameters must be passed to LadybugDB's execute
        query = """
        MATCH (m:Memory)
        WHERE m.content CONTAINS $search_term AND m.importance >= $min_importance
        RETURN m.title, m.content, m.importance
        ORDER BY m.importance DESC
        LIMIT $limit
        """

        params = {
            "search_term": "icecream",
            "min_importance": 0.5,
            "limit": 10
        }

        result = await backend.execute_query(query, params)

        # Verify we found the memory
        assert len(result) == 1, f"Expected 1 result, got {len(result)}"
        row = result[0]

        # Results are returned as dictionaries
        # We RETURN m.title, m.content, m.importance
        assert "m.title" in row and "m.content" in row and "m.importance" in row
        assert row["m.title"] == title
        assert row["m.content"] == content
        assert row["m.importance"] == importance

    @pytest.mark.asyncio
    async def test_store_multiple_memories_and_search_with_parameters(self, backend):
        """Test storing multiple memories and searching with various parameter combinations."""
        await backend.initialize_schema()

        # Create multiple memories
        memories = [
            ("User likes icecream", "general", 0.9),
            ("Prefers chocolate icecream", "preference", 0.7),
            ("Likes vanilla too", "preference", 0.5),
            ("Not a preference", "general", 0.3),
        ]

        for i, (content, mtype, importance) in enumerate(memories):
            memory_id = str(uuid.uuid4())
            create_query = f"""
            CREATE (m:Memory {{
                id: '{memory_id}',
                type: '{mtype}',
                title: 'Memory {i}',
                content: '{content}',
                importance: {importance},
                confidence: 1.0,
                created_at: '{datetime.now().isoformat()}',
                updated_at: '{datetime.now().isoformat()}',
                summary: '',
                tags: '[]',
                context_project_path: '',
                context_file_path: '',
                context_line_start: -1,
                context_line_end: -1,
                context_commit_hash: '',
                context_branch: '',
                metadata: '{{}}'
            }})
            """
            await backend.execute_query(create_query, write=True)

        # Test 1: Search with CONTAINS parameter
        query1 = """
        MATCH (m:Memory)
        WHERE m.content CONTAINS $search_term
        RETURN m.content, m.importance
        ORDER BY m.importance DESC
        """
        result1 = await backend.execute_query(query1, {"search_term": "icecream"})
        assert len(result1) == 2
        assert "icecream" in result1[0]["m.content"]

        # Test 2: Filter by importance
        query2 = """
        MATCH (m:Memory)
        WHERE m.importance >= $min_importance
        RETURN m.content, m.importance
        ORDER BY m.importance DESC
        """
        result2 = await backend.execute_query(query2, {"min_importance": 0.6})
        assert len(result2) == 2
        for row in result2:
            assert row["m.importance"] >= 0.6

        # Test 3: Multiple parameters
        query3 = """
        MATCH (m:Memory)
        WHERE m.type = $memory_type AND m.importance >= $min_importance
        RETURN m.content, m.type, m.importance
        ORDER BY m.importance DESC
        LIMIT $limit
        """
        result3 = await backend.execute_query(
            query3,
            {
                "memory_type": "preference",
                "min_importance": 0.5,
                "limit": 10
            }
        )
        # Both preference memories match (0.7 and 0.5)
        assert len(result3) == 2
        for row in result3:
            assert row["m.type"] == "preference"
            assert row["m.importance"] >= 0.5


# Import here to avoid import errors when real_ladybug is not available
if LADYBUGDB_AVAILABLE:
    from memorygraph.backends.ladybugdb_backend import LadybugDBBackend
    from memorygraph.models import SchemaError
else:
    # Dummy classes for type checking when not available
    LadybugDBBackend = None
    SchemaError = Exception
