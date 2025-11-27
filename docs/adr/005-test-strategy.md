# ADR 005: Test Strategy and Coverage Goals

## Status
Accepted

## Date
2025-11-27 (Phase 2.5)

## Context
We needed a comprehensive testing strategy to ensure:

1. **Quality**: High-quality, reliable code
2. **Refactoring Safety**: Confidence when making changes
3. **Documentation**: Tests serve as usage examples
4. **Regression Prevention**: Catch bugs early
5. **MCP Compliance**: Verify protocol adherence

## Decision Drivers
- **Test Coverage Target**: 80% code coverage
- **Test Organization**: Mirror source structure
- **Async Testing**: Support async/await patterns
- **Mock Strategy**: Test layers independently
- **CI/CD Ready**: Tests run in CI pipeline

## Considered Options

### Option 1: Integration Tests Only
**Pros:**
- Test real system behavior
- Catch integration issues

**Cons:**
- Slow test execution
- Requires real Neo4j instance
- Hard to test edge cases
- Difficult to isolate failures

### Option 2: Unit Tests Only
**Pros:**
- Fast execution
- Easy to isolate failures
- Good for TDD

**Cons:**
- May miss integration issues
- Lots of mocking
- Doesn't verify real database behavior

### Option 3: Balanced Test Pyramid
**Pros:**
- Fast unit tests for most code
- Integration tests for critical paths
- E2E tests for workflows
- Best of all approaches

**Cons:**
- More test infrastructure
- Need to manage different test types

## Decision
We chose **Balanced Test Pyramid** with emphasis on unit tests:

```
        /\
       /E2\    (Future: End-to-end MCP tests)
      /----\
     / Intg \  (Database integration tests)
    /--------\
   /   Unit   \ (Comprehensive unit tests)
  /------------\
```

## Test Suite Composition

### Unit Tests (90% of tests)
**Coverage Target:** 80%+

**test_models.py (7 tests)**
- Model validation
- Pydantic field validators
- Serialization/deserialization
- Enum value validation
- Context handling

**test_exceptions.py (8 tests)**
- Custom exception creation
- Error hierarchy
- Exception with details
- Error message formatting

**test_database.py (28 tests)**
- Database connection management
- CRUD operations (with mocked Neo4j)
- Relationship creation and traversal
- Query execution
- Error handling
- Async operations

**test_server.py (19 tests)**
- MCP handler validation
- Tool call handling
- Error responses
- isError flag verification
- Input validation
- Response formatting

### Integration Tests (10% of tests)
**test_database.py subset**
- Real Neo4j connection tests (optional)
- Schema initialization
- End-to-end query execution

## Testing Patterns

### Async Test Pattern
```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async database operation."""
    db = MemoryDatabase(mock_connection)

    result = await db.some_async_method()

    assert result is not None
```

### Mock Pattern for Database
```python
@pytest.fixture
def mock_driver():
    """Mock Neo4j driver."""
    driver = AsyncMock(spec=AsyncDriver)
    return driver

@pytest.fixture
async def connection(mock_driver):
    """Create connection with mocked driver."""
    conn = Neo4jConnection(uri="bolt://localhost:7687", ...)
    conn.driver = mock_driver
    return conn
```

### Mock Pattern for Server
```python
@pytest.fixture
async def mock_database():
    """Mock MemoryDatabase for server tests."""
    db = AsyncMock(spec=MemoryDatabase)
    db.store_memory = AsyncMock(return_value="mock-id")
    return db

@pytest.fixture
async def mcp_server(mock_database):
    """Create server with mocked database."""
    server = ClaudeMemoryServer()
    server.memory_db = mock_database
    return server
```

## Coverage Goals

### Overall Target: 76%+ (achieved)
- database.py: 71% (target 70%+)
- server.py: 63% (target 60%+)
- models.py: 97% (target 95%+)
- __init__.py: 100%

### Coverage Reporting
```bash
# Run tests with coverage
pytest tests/ --cov=src/claude_memory --cov-report=term-missing

# Generate HTML report
pytest tests/ --cov=src/claude_memory --cov-report=html

# Coverage threshold (CI)
pytest tests/ --cov=src/claude_memory --cov-fail-under=75
```

## Test Organization

### File Structure
```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_models.py       # Model tests (7 tests)
├── test_database.py     # Database tests (28 tests)
├── test_server.py       # Server tests (19 tests)
└── test_exceptions.py   # Exception tests (8 tests)
```

### Fixture Scope
- **Function-scoped**: Most fixtures (default)
- **Module-scoped**: Expensive setup (future)
- **Session-scoped**: Shared test data (future)

## Testing Infrastructure

### Dependencies
```toml
[tool.poetry.dev-dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
```

### pytest Configuration
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

## Test Quality Principles

### 1. AAA Pattern (Arrange-Act-Assert)
```python
async def test_store_memory():
    # Arrange
    memory = Memory(type=MemoryType.SOLUTION, ...)
    mock_db.store_memory.return_value = "test-id"

    # Act
    result = await server._handle_store_memory(args)

    # Assert
    assert result.isError is False
    assert "test-id" in str(result.content)
```

### 2. Meaningful Test Names
- ✅ `test_store_memory_success`
- ✅ `test_store_memory_missing_required_fields`
- ✅ `test_get_memory_not_found`
- ❌ `test_1`, `test_memory`

### 3. One Assertion Focus Per Test
- Each test verifies one behavior
- Multiple assertions OK if testing same concept
- Avoid testing multiple unrelated things

### 4. Test Independence
- No test depends on another
- Can run in any order
- Each test sets up its own state

### 5. Fast Execution
- Mock external dependencies
- Avoid sleep() calls
- Use fixtures for setup
- Target: < 1 second total

## Consequences

### Positive
- **High Confidence**: 62 tests, 100% pass rate
- **Fast Feedback**: Tests run in < 1 second
- **Refactoring Safety**: Can refactor with confidence
- **Documentation**: Tests show how to use APIs
- **Bug Prevention**: Caught 24 issues during Phase 2.5
- **MCP Compliance**: All handlers tested

### Negative
- **Mock Maintenance**: Mocks must match real implementations
- **Test Code Volume**: ~800 lines of test code
- **Learning Curve**: Async testing patterns

### Mitigations
- **Clear Patterns**: Consistent test structure
- **Fixtures**: Reusable test setup
- **Documentation**: Test examples in README
- **Regular Updates**: Keep mocks in sync with code

## Test Execution

### Local Development
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database.py

# Run specific test
pytest tests/test_database.py::test_store_memory_basic

# Run with coverage
pytest --cov=src/claude_memory --cov-report=term
```

### CI/CD (Future)
```yaml
- name: Run tests
  run: pytest tests/ --cov=src/claude_memory --cov-fail-under=75
```

## Metrics (Phase 2.5 Complete)
- **Total Tests**: 62
- **Pass Rate**: 100% (62/62)
- **Coverage**: 76% overall
- **Execution Time**: < 1 second
- **Test LOC**: ~800 lines

## Future Enhancements

### Phase 3+
- Integration tests with real Neo4j (testcontainers)
- Property-based testing (hypothesis)
- Performance benchmarks
- Load testing
- E2E MCP protocol tests
- Mutation testing (mutpy)

## References
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
