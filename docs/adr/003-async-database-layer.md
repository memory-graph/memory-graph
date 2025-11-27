# ADR 003: Async Database Layer with AsyncIO

## Status
Accepted

## Date
2025-11-27 (Phase 2.5)

## Context
The initial implementation used synchronous database operations, but we needed to:

1. **Improve Performance**: Handle multiple concurrent operations
2. **MCP Compatibility**: MCP server handlers are async
3. **Non-Blocking**: Don't block event loop during database queries
4. **Scalability**: Support higher throughput
5. **Best Practices**: Follow modern Python async patterns

## Decision Drivers
- **MCP Server**: All MCP handlers are async functions
- **Neo4j Driver**: Supports both sync and async interfaces
- **Performance**: Async queries can run concurrently
- **Python 3.11+**: Modern async/await syntax
- **Event Loop**: Avoid blocking the main event loop

## Considered Options

### Option 1: Synchronous Database Layer
**Pros:**
- Simpler to understand and debug
- No async complexity
- More familiar to developers

**Cons:**
- Blocks event loop during queries
- Can't run concurrent operations
- Doesn't match MCP async patterns
- Performance bottleneck

### Option 2: Thread Pool for Sync Operations
**Pros:**
- Keep sync database code
- Use asyncio.run_in_executor() for threading

**Cons:**
- Thread overhead
- Complex thread synchronization
- GIL limitations
- Mixed async/sync patterns

### Option 3: Native Async with AsyncIO
**Pros:**
- Native async support in Neo4j driver
- No thread overhead
- Clean async/await syntax
- Non-blocking operations
- Can run concurrent queries
- Matches MCP async patterns

**Cons:**
- Need to refactor sync code
- Requires async testing
- Slightly more complex

## Decision
We chose **Native Async with AsyncIO** because:

1. **Native Support**: Neo4j driver has full async support
2. **Performance**: True non-blocking concurrent operations
3. **MCP Alignment**: Matches async MCP handler pattern
4. **Modern Python**: Follows Python 3.11+ best practices
5. **Clean API**: Async/await is clearer than thread pools

## Implementation Pattern

### Database Connection
```python
class Neo4jConnection:
    async def connect(self) -> None:
        """Establish async connection to Neo4j."""
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )

    @asynccontextmanager
    async def session(self, database: str = None):
        """Async context manager for sessions."""
        if not self.driver:
            raise DatabaseConnectionError("Not connected")

        session = self.driver.session(database=database or self.database)
        try:
            yield session
        finally:
            await session.close()
```

### Query Execution
```python
async def execute_write_query(
    self,
    query: str,
    parameters: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """Execute write query asynchronously."""
    try:
        async with self.session() as session:
            result = await session.execute_write(
                self._run_query_async, query, parameters or {}
            )
            return result
    except Neo4jError as e:
        raise DatabaseConnectionError(f"Write query failed: {e}")

async def _run_query_async(
    self,
    tx: AsyncManagedTransaction,
    query: str,
    parameters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Run query within async transaction."""
    result = await tx.run(query, parameters)
    records = await result.data()
    return records
```

### Server Handlers
```python
async def _handle_store_memory(
    self,
    arguments: Dict[str, Any]
) -> CallToolResult:
    """Handle store_memory tool call (async)."""
    try:
        memory = Memory(**arguments)
        # Async database operation
        memory_id = await self.memory_db.store_memory(memory)
        return CallToolResult(content=[...])
    except Exception as e:
        return CallToolResult(content=[...], isError=True)
```

## Consequences

### Positive
- **Non-Blocking**: Database queries don't block event loop
- **Concurrent**: Can handle multiple requests simultaneously
- **Performance**: Better throughput under load
- **Clean Code**: Async/await is intuitive
- **MCP Native**: Matches MCP server async pattern
- **Testable**: pytest-asyncio for async testing

### Negative
- **Complexity**: Async adds cognitive overhead
- **Testing**: Need async test fixtures
- **Debugging**: Async stack traces can be harder
- **Migration**: Required refactoring existing code

### Mitigations
- **Comprehensive Tests**: 28 async database tests
- **Clear Patterns**: Consistent async/await usage
- **Documentation**: Examples of async patterns
- **Type Hints**: Explicit async function signatures
- **pytest-asyncio**: Proper async test infrastructure

## Migration Strategy (Phase 2.5)
1. ✅ Add `AsyncGraphDatabase` import
2. ✅ Convert `connect()` to async
3. ✅ Make `session()` an async context manager
4. ✅ Convert all query methods to async
5. ✅ Update all callers to await async methods
6. ✅ Add async test fixtures
7. ✅ Verify all tests pass

## Performance Impact
**Before (Sync):**
- Sequential query execution
- Event loop blocked during queries
- ~100ms per query (blocked)

**After (Async):**
- Concurrent query execution
- Event loop free during queries
- ~100ms per query (non-blocking)
- Can handle 10+ concurrent requests

## Testing Strategy
```python
@pytest.mark.asyncio
async def test_async_database():
    """Test async database operation."""
    db = MemoryDatabase(connection)

    # Async operation
    memory_id = await db.store_memory(memory)

    assert memory_id is not None
```

## References
- [Neo4j Async Driver Docs](https://neo4j.com/docs/python-manual/current/async/)
- [Python AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [AsyncIO Best Practices](https://docs.python.org/3/library/asyncio-dev.html)
