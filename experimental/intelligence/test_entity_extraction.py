"""Tests for entity extraction functionality."""

import pytest
from memorygraph.intelligence.entity_extraction import (
    EntityType,
    Entity,
    EntityExtractor,
    extract_entities,
)


class TestEntityExtraction:
    """Test entity extraction from various text inputs."""

    def test_extract_file_paths(self):
        """Test extraction of file paths."""
        text = "Fixed bug in /src/auth/handler.py and tests/test_auth.py"
        entities = extract_entities(text)

        file_entities = [e for e in entities if e.entity_type == EntityType.FILE]
        assert len(file_entities) >= 2

        file_texts = {e.text for e in file_entities}
        assert "/src/auth/handler.py" in file_texts or "src/auth/handler.py" in file_texts
        assert "tests/test_auth.py" in file_texts or "test_auth.py" in file_texts

    def test_extract_functions(self):
        """Test extraction of function names."""
        text = "The authenticate() function calls validate_token() internally"
        entities = extract_entities(text)

        func_entities = [e for e in entities if e.entity_type == EntityType.FUNCTION]
        assert len(func_entities) >= 2

        func_texts = {e.text for e in func_entities}
        assert "authenticate" in func_texts
        assert "validate_token" in func_texts

    def test_extract_classes(self):
        """Test extraction of class names."""
        text = "Implemented AuthHandler and TokenService classes"
        entities = extract_entities(text)

        class_entities = [e for e in entities if e.entity_type == EntityType.CLASS]
        assert len(class_entities) >= 2

        class_texts = {e.text for e in class_entities}
        assert "AuthHandler" in class_texts
        assert "TokenService" in class_texts

    def test_extract_errors(self):
        """Test extraction of error types."""
        text = "Got ValueError and ConnectionError, also saw 404 and 500 status codes"
        entities = extract_entities(text)

        error_entities = [e for e in entities if e.entity_type == EntityType.ERROR]
        assert len(error_entities) >= 2

        error_texts = {e.text for e in error_entities}
        assert "ValueError" in error_texts or "ConnectionError" in error_texts

    def test_extract_technologies(self):
        """Test extraction of technology names."""
        text = "Using Python with FastAPI framework and PostgreSQL database"
        entities = extract_entities(text)

        tech_entities = [e for e in entities if e.entity_type == EntityType.TECHNOLOGY]
        assert len(tech_entities) >= 2

        tech_texts = {e.text for e in tech_entities}
        assert "Python" in tech_texts
        assert "FastAPI" in tech_texts or "PostgreSQL" in tech_texts

    def test_extract_concepts(self):
        """Test extraction of programming concepts."""
        text = "Implemented authentication and caching for the API"
        entities = extract_entities(text)

        concept_entities = [e for e in entities if e.entity_type == EntityType.CONCEPT]
        assert len(concept_entities) >= 1

        concept_texts = {e.text for e in concept_entities}
        assert "authentication" in concept_texts or "caching" in concept_texts

    def test_extract_urls(self):
        """Test extraction of URLs."""
        text = "Check https://example.com/api/v1/users for the endpoint"
        entities = extract_entities(text)

        url_entities = [e for e in entities if e.entity_type == EntityType.URL]
        assert len(url_entities) >= 1

        assert any("https://example.com" in e.text for e in url_entities)

    def test_extract_commands(self):
        """Test extraction of commands in backticks."""
        text = "Run `npm install` and then `npm test` to verify"
        entities = extract_entities(text)

        cmd_entities = [e for e in entities if e.entity_type == EntityType.COMMAND]
        assert len(cmd_entities) >= 1

        cmd_texts = {e.text for e in cmd_entities}
        assert "npm install" in cmd_texts or "npm test" in cmd_texts

    def test_extract_mixed_content(self):
        """Test extraction from mixed content with multiple entity types."""
        text = """
        Fixed authentication bug in src/auth/handler.py by updating the
        validateToken() function. The issue was a ValueError being raised
        when using PostgreSQL. Solution works with Python 3.10+.
        """
        entities = extract_entities(text)

        # Should extract multiple types
        entity_types = {e.entity_type for e in entities}
        assert len(entity_types) >= 3

        # Should have at least one of each major type
        assert EntityType.FILE in entity_types or EntityType.FUNCTION in entity_types
        assert EntityType.ERROR in entity_types or EntityType.TECHNOLOGY in entity_types

    def test_confidence_scores(self):
        """Test that confidence scores are reasonable."""
        text = "Fixed bug in /src/main.py using Python"
        entities = extract_entities(text)

        assert all(0.0 <= e.confidence <= 1.0 for e in entities)
        assert any(e.confidence > 0.8 for e in entities)

    def test_min_confidence_filtering(self):
        """Test filtering by minimum confidence."""
        text = "Some text with various entities /path/file.py authenticate()"

        all_entities = extract_entities(text, min_confidence=0.0)
        filtered_entities = extract_entities(text, min_confidence=0.9)

        assert len(filtered_entities) <= len(all_entities)

    def test_context_extraction(self):
        """Test that context is extracted around entities."""
        text = "This is a long text with src/file.py in the middle of it for testing"
        entities = extract_entities(text)

        file_entity = next((e for e in entities if e.entity_type == EntityType.FILE), None)
        assert file_entity is not None
        assert file_entity.context is not None
        assert "src/file.py" in file_entity.context

    def test_deduplication(self):
        """Test that duplicate entities are removed."""
        text = "Call authenticate() first, then authenticate() again"
        entities = extract_entities(text)

        # Count authenticate entities
        auth_count = sum(1 for e in entities if e.text == "authenticate" and e.entity_type == EntityType.FUNCTION)
        assert auth_count == 1  # Should be deduplicated

    def test_empty_text(self):
        """Test extraction from empty text."""
        entities = extract_entities("")
        assert entities == []

    def test_no_entities_found(self):
        """Test text with no recognizable entities."""
        text = "Some random text without any entities"
        entities = extract_entities(text)
        # May find some entities depending on patterns, but should not crash
        assert isinstance(entities, list)

    def test_entity_positions(self):
        """Test that entity positions are tracked correctly."""
        text = "Check file.py for errors"
        entities = extract_entities(text)

        assert all(e.start_pos is not None for e in entities)
        assert all(e.end_pos is not None for e in entities)
        assert all(e.start_pos < e.end_pos for e in entities)


class TestEntityExtractor:
    """Test EntityExtractor class directly."""

    def test_extractor_initialization(self):
        """Test extractor can be initialized."""
        extractor = EntityExtractor()
        assert extractor is not None
        assert not extractor.enable_nlp  # Default is False

    def test_extractor_with_nlp_disabled(self):
        """Test extractor works with NLP disabled."""
        extractor = EntityExtractor(enable_nlp=False)
        text = "Test Python code in main.py"
        entities = extractor.extract(text)
        assert isinstance(entities, list)

    def test_custom_min_confidence(self):
        """Test extraction with custom confidence threshold."""
        extractor = EntityExtractor()
        text = "Code in /path/file.py using Python"

        low_conf_entities = extractor.extract(text, min_confidence=0.3)
        high_conf_entities = extractor.extract(text, min_confidence=0.95)

        assert len(low_conf_entities) >= len(high_conf_entities)


class TestEntityModel:
    """Test Entity model validation."""

    def test_entity_creation(self):
        """Test creating an Entity instance."""
        entity = Entity(
            text="test.py",
            entity_type=EntityType.FILE,
            confidence=0.95,
        )
        assert entity.text == "test.py"
        assert entity.entity_type == EntityType.FILE
        assert entity.confidence == 0.95

    def test_entity_confidence_validation(self):
        """Test confidence value validation."""
        # Valid confidence
        entity = Entity(text="test", entity_type=EntityType.FILE, confidence=0.5)
        assert entity.confidence == 0.5

        # Test bounds
        with pytest.raises(Exception):  # Pydantic validation error
            Entity(text="test", entity_type=EntityType.FILE, confidence=1.5)

        with pytest.raises(Exception):  # Pydantic validation error
            Entity(text="test", entity_type=EntityType.FILE, confidence=-0.1)

    def test_entity_optional_fields(self):
        """Test that optional fields can be None."""
        entity = Entity(text="test", entity_type=EntityType.FILE)
        assert entity.context is None
        assert entity.start_pos is None
        assert entity.end_pos is None


class TestRealWorldExamples:
    """Test entity extraction with real-world examples."""

    def test_bug_fix_description(self):
        """Test extraction from a typical bug fix description."""
        text = """
        Fixed authentication timeout in src/auth/middleware.py.
        The issue was in the validateSession() function which was
        throwing a SessionExpiredError after 30 minutes. Updated
        to use Redis for session storage and increased timeout to 1 hour.
        """
        entities = extract_entities(text)

        entity_types = {e.entity_type for e in entities}
        assert EntityType.FILE in entity_types
        assert EntityType.FUNCTION in entity_types
        assert EntityType.ERROR in entity_types
        assert EntityType.TECHNOLOGY in entity_types or EntityType.CONCEPT in entity_types

    def test_feature_implementation(self):
        """Test extraction from feature implementation description."""
        text = """
        Implemented GraphQL API using FastAPI and Strawberry.
        Created resolvers in api/graphql/resolvers.py and
        schema definitions in api/graphql/schema.py.
        Uses PostgreSQL database with async SQLAlchemy.
        """
        entities = extract_entities(text)

        # Should find technologies
        tech_entities = [e for e in entities if e.entity_type == EntityType.TECHNOLOGY]
        assert len(tech_entities) >= 2

        # Should find files
        file_entities = [e for e in entities if e.entity_type == EntityType.FILE]
        assert len(file_entities) >= 1

    def test_error_debugging(self):
        """Test extraction from error debugging notes."""
        text = """
        Debugged 500 Internal Server Error in production.
        Root cause: ConnectionRefusedError when connecting to
        the MongoDB instance. Fixed by updating connection pool
        settings in config/database.py.
        """
        entities = extract_entities(text)

        error_entities = [e for e in entities if e.entity_type == EntityType.ERROR]
        assert len(error_entities) >= 1

        tech_entities = [e for e in entities if e.entity_type == EntityType.TECHNOLOGY]
        assert len(tech_entities) >= 1

    def test_code_review_comment(self):
        """Test extraction from code review comments."""
        text = """
        In UserController.handleRequest(), consider using dependency
        injection instead of directly instantiating AuthService.
        This would make testing easier and improve separation of concerns.
        """
        entities = extract_entities(text)

        # Should extract class and function names
        assert any(e.entity_type == EntityType.CLASS for e in entities)
        assert any(e.entity_type == EntityType.FUNCTION for e in entities)

    def test_deployment_notes(self):
        """Test extraction from deployment notes."""
        text = """
        Deployed v2.1.0 to production using Docker and Kubernetes.
        Run `kubectl apply -f k8s/deployment.yaml` to deploy.
        PostgreSQL migrations applied successfully.
        Monitor https://app.example.com/health for status.
        """
        entities = extract_entities(text)

        # Should find commands
        cmd_entities = [e for e in entities if e.entity_type == EntityType.COMMAND]
        assert len(cmd_entities) >= 1

        # Should find technologies
        tech_entities = [e for e in entities if e.entity_type == EntityType.TECHNOLOGY]
        assert len(tech_entities) >= 2

        # Should find URLs
        url_entities = [e for e in entities if e.entity_type == EntityType.URL]
        assert len(url_entities) >= 1


@pytest.mark.asyncio
async def test_link_entities_integration():
    """Test linking entities to memories (integration test with mock backend)."""

    class MockBackend:
        """Mock backend for testing."""

        def __init__(self):
            self.queries = []

        async def execute_query(self, query: str, params: dict):
            """Mock query execution."""
            self.queries.append((query, params))
            return [{"entity_id": f"entity-{len(self.queries)}"}]

    from memorygraph.intelligence.entity_extraction import link_entities

    # Create mock backend
    backend = MockBackend()

    # Create test entities
    entities = [
        Entity(text="test.py", entity_type=EntityType.FILE, confidence=0.95),
        Entity(text="Python", entity_type=EntityType.TECHNOLOGY, confidence=0.95),
    ]

    # Link entities
    entity_ids = await link_entities(backend, "memory-123", entities)

    # Verify entities were linked
    assert len(entity_ids) == 2
    assert len(backend.queries) == 2

    # Verify query parameters
    for query, params in backend.queries:
        assert "MERGE" in query
        assert "MENTIONS" in query
        assert params["memory_id"] == "memory-123"
        assert "confidence" in params
