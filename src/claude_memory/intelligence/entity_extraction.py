"""
Entity Extraction - Automatic entity identification and linking.

This module extracts entities from memory content using regex patterns
and optional NLP models. Supports file paths, functions, classes, errors,
technologies, concepts, and more.
"""

import re
import logging
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities that can be extracted from memory content."""

    FILE = "file"  # /path/to/file.py, file.txt
    FUNCTION = "function"  # function_name(), methodName()
    CLASS = "class"  # ClassName, ComponentName
    ERROR = "error"  # ErrorType, Exception, error codes
    TECHNOLOGY = "technology"  # Python, React, PostgreSQL
    CONCEPT = "concept"  # authentication, caching, CORS
    PERSON = "person"  # @username, developer names
    PROJECT = "project"  # project/repo names
    COMMAND = "command"  # CLI commands
    PACKAGE = "package"  # npm/pip package names
    URL = "url"  # HTTP(S) URLs
    VARIABLE = "variable"  # variable_name, CONSTANT_NAME


class Entity(BaseModel):
    """Represents an extracted entity."""

    text: str = Field(..., description="The extracted entity text")
    entity_type: EntityType = Field(..., description="Type of the entity")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence")
    context: Optional[str] = Field(None, description="Surrounding context")
    start_pos: Optional[int] = Field(None, description="Start position in text")
    end_pos: Optional[int] = Field(None, description="End position in text")


class EntityExtractor:
    """Extracts entities from text using regex patterns."""

    # Regex patterns for different entity types
    PATTERNS = {
        EntityType.FILE: [
            # Absolute paths: /path/to/file.py
            r"(?:/[\w\-./]+)",
            # Relative paths with extension: src/file.py
            r"(?:[\w\-./]+\.[\w]+)",
            # Windows paths: C:\path\to\file.py
            r"(?:[A-Z]:\\[\w\-\\./]+)",
        ],
        EntityType.FUNCTION: [
            # function_name()
            r"\b([a-z_]\w*)\(\)",
            # methodName()
            r"\b([a-z]\w*[A-Z]\w*)\(\)",
        ],
        EntityType.CLASS: [
            # ClassName, Handler, Service, Manager, etc.
            r"\b([A-Z][\w]*(?:Class|Handler|Service|Manager|Controller|Provider|Factory|Builder|Strategy|Adapter|Facade|Proxy|Decorator|Observer|Singleton|Component|Module|Store|Action|Reducer|Hook|Context))\b",
            # Generic PascalCase
            r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b",
        ],
        EntityType.ERROR: [
            # *Error, *Exception
            r"\b(\w*(?:Error|Exception))\b",
            # HTTP status codes
            r"\b([45]\d{2})\b",
            # Error codes like ERR_*, E_*
            r"\b(E(?:RR)?_[\w_]+)\b",
        ],
        EntityType.TECHNOLOGY: [
            # Programming languages
            r"\b(Python|JavaScript|TypeScript|Java|Kotlin|Swift|Go|Rust|C\+\+|C#|Ruby|PHP|Scala|Haskell|Elixir|Clojure|Erlang)\b",
            # Frameworks
            r"\b(React|Vue|Angular|Django|Flask|FastAPI|Express|Spring|Rails|Laravel|Symfony|Nest\.?js|Next\.?js|Nuxt\.?js|Svelte|Solid)\b",
            # Databases
            r"\b(PostgreSQL|MySQL|MongoDB|Redis|Neo4j|Memgraph|SQLite|DynamoDB|Cassandra|CouchDB|Elasticsearch|MariaDB|Oracle|MSSQL)\b",
            # Cloud/Infrastructure
            r"\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform|Ansible|Jenkins|GitHub|GitLab|CircleCI|Travis)\b",
        ],
        EntityType.CONCEPT: [
            # Common programming concepts
            r"\b(authentication|authorization|caching|logging|testing|debugging|deployment|migration|refactoring|optimization|validation|serialization|deserialization|encryption|decryption|compression|decompression)\b",
            # Architecture patterns
            r"\b(MVC|MVVM|MVP|REST|GraphQL|gRPC|microservices|monolith|serverless|event-driven|CQRS|DDD|hexagonal|clean architecture)\b",
            # Security concepts
            r"\b(CORS|XSS|CSRF|SQL injection|JWT|OAuth|SAML|TLS|SSL|HTTPS|firewall|WAF)\b",
        ],
        EntityType.COMMAND: [
            # Commands in backticks or quotes
            r"`([^`]+)`",
            r'"([^"]+)"' + r'\s*(?:command|cmd|run|exec)',
        ],
        EntityType.PACKAGE: [
            # npm/pip packages
            r"\b((?:@[\w\-]+\/)?[\w\-]+)\b(?=\s*(?:package|library|module|dependency))",
            # Common package patterns
            r"\b(react-\w+|vue-\w+|@types/\w+|webpack-\w+|babel-\w+|eslint-\w+|pytest-\w+)\b",
        ],
        EntityType.URL: [
            # HTTP(S) URLs
            r"https?://[\w\-./]+(?:\?[\w\-=&]*)?",
        ],
        EntityType.VARIABLE: [
            # CONSTANT_NAME
            r"\b([A-Z][A-Z0-9_]{2,})\b",
            # snake_case
            r"\b([a-z_]\w*[a-z]\w*)\b(?=\s*[:=])",
        ],
    }

    def __init__(self, enable_nlp: bool = False):
        """
        Initialize the entity extractor.

        Args:
            enable_nlp: Enable NLP-based extraction (requires spaCy). Default: False
        """
        self.enable_nlp = enable_nlp
        self.nlp_model = None

        if enable_nlp:
            try:
                import spacy  # type: ignore

                self.nlp_model = spacy.load("en_core_web_sm")
                logger.info("NLP entity extraction enabled")
            except (ImportError, OSError):
                logger.warning(
                    "spaCy not available, falling back to regex-only extraction. "
                    "Install with: pip install spacy && python -m spacy download en_core_web_sm"
                )
                self.enable_nlp = False

    def extract(self, text: str, min_confidence: float = 0.5) -> list[Entity]:
        """
        Extract entities from text.

        Args:
            text: Text to extract entities from
            min_confidence: Minimum confidence threshold (0.0-1.0)

        Returns:
            List of extracted entities
        """
        entities: list[Entity] = []

        # Extract using regex patterns
        entities.extend(self._extract_with_regex(text))

        # Extract using NLP if enabled
        if self.enable_nlp and self.nlp_model:
            entities.extend(self._extract_with_nlp(text))

        # Deduplicate and filter by confidence
        entities = self._deduplicate(entities)
        entities = [e for e in entities if e.confidence >= min_confidence]

        return entities

    def _extract_with_regex(self, text: str) -> list[Entity]:
        """Extract entities using regex patterns."""
        entities: list[Entity] = []

        for entity_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entity_text = match.group(1) if match.groups() else match.group(0)

                    # Skip very short or very long matches
                    if len(entity_text) < 2 or len(entity_text) > 100:
                        continue

                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_confidence(entity_type, entity_text, text)

                    # Extract context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]

                    entities.append(
                        Entity(
                            text=entity_text,
                            entity_type=entity_type,
                            confidence=confidence,
                            context=context,
                            start_pos=match.start(),
                            end_pos=match.end(),
                        )
                    )

        return entities

    def _extract_with_nlp(self, text: str) -> list[Entity]:
        """Extract entities using NLP (spaCy)."""
        entities: list[Entity] = []

        if not self.nlp_model:
            return entities

        doc = self.nlp_model(text)

        # Map spaCy entity types to our EntityType
        nlp_type_mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.PROJECT,  # Organizations often map to projects
            "PRODUCT": EntityType.TECHNOLOGY,
            "GPE": EntityType.CONCEPT,  # Geopolitical entities as concepts
        }

        for ent in doc.ents:
            if ent.label_ in nlp_type_mapping:
                entities.append(
                    Entity(
                        text=ent.text,
                        entity_type=nlp_type_mapping[ent.label_],
                        confidence=0.8,  # NLP confidence is generally high
                        context=ent.sent.text if ent.sent else None,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                    )
                )

        return entities

    def _calculate_confidence(self, entity_type: EntityType, text: str, full_text: str) -> float:
        """
        Calculate extraction confidence based on entity type and context.

        Args:
            entity_type: Type of entity
            text: Extracted entity text
            full_text: Full text being analyzed

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.7  # Base confidence

        # Boost confidence for specific patterns
        if entity_type == EntityType.FILE:
            if text.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".txt", ".json", ".yaml", ".yml")):
                confidence = 0.95
            elif "/" in text or "\\" in text:
                confidence = 0.85

        elif entity_type == EntityType.FUNCTION:
            if "()" in text:
                confidence = 0.9

        elif entity_type == EntityType.CLASS:
            # Higher confidence for known suffixes
            if any(text.endswith(suffix) for suffix in ["Handler", "Service", "Manager", "Controller"]):
                confidence = 0.95
            else:
                confidence = 0.75

        elif entity_type == EntityType.ERROR:
            if text.endswith(("Error", "Exception")):
                confidence = 0.95
            elif re.match(r"[45]\d{2}", text):  # HTTP status codes
                confidence = 0.9

        elif entity_type == EntityType.TECHNOLOGY:
            # Known technologies have high confidence
            confidence = 0.95

        elif entity_type == EntityType.URL:
            confidence = 0.99

        elif entity_type == EntityType.COMMAND:
            # Commands in backticks are very reliable
            confidence = 0.9

        return min(confidence, 1.0)

    def _deduplicate(self, entities: list[Entity]) -> list[Entity]:
        """Remove duplicate entities, keeping highest confidence."""
        seen: dict[tuple[str, EntityType], Entity] = {}

        for entity in entities:
            key = (entity.text.lower(), entity.entity_type)

            if key not in seen or entity.confidence > seen[key].confidence:
                seen[key] = entity

        return list(seen.values())


# Singleton instance for convenience
_default_extractor = EntityExtractor()


def extract_entities(text: str, min_confidence: float = 0.5) -> list[Entity]:
    """
    Extract entities from text using the default extractor.

    Args:
        text: Text to extract entities from
        min_confidence: Minimum confidence threshold (0.0-1.0)

    Returns:
        List of extracted entities

    Example:
        >>> entities = extract_entities("Fixed authentication bug in src/auth.py")
        >>> for entity in entities:
        ...     print(f"{entity.entity_type.value}: {entity.text}")
        file: src/auth.py
        concept: authentication
    """
    return _default_extractor.extract(text, min_confidence)


async def link_entities(
    backend,
    memory_id: str,
    entities: list[Entity],
) -> list[str]:
    """
    Link extracted entities to a memory by creating entity nodes and MENTIONS relationships.

    Args:
        backend: Database backend instance
        memory_id: ID of the memory to link entities to
        entities: List of entities to link

    Returns:
        List of created entity IDs

    Example:
        >>> entities = extract_entities("Fixed React hooks issue")
        >>> entity_ids = await link_entities(backend, memory_id, entities)
    """
    entity_ids: list[str] = []

    for entity in entities:
        # Create or find entity node
        query = """
        MERGE (e:Entity {text: $text, type: $type})
        ON CREATE SET
            e.id = randomUUID(),
            e.created_at = datetime(),
            e.occurrence_count = 1
        ON MATCH SET
            e.occurrence_count = e.occurrence_count + 1,
            e.last_seen = datetime()
        WITH e
        MATCH (m:Memory {id: $memory_id})
        MERGE (m)-[r:MENTIONS]->(e)
        ON CREATE SET
            r.confidence = $confidence,
            r.created_at = datetime()
        RETURN e.id as entity_id
        """

        params = {
            "text": entity.text,
            "type": entity.entity_type.value,
            "memory_id": memory_id,
            "confidence": entity.confidence,
        }

        try:
            result = await backend.execute_query(query, params)
            if result:
                entity_ids.append(result[0]["entity_id"])
                logger.debug(
                    f"Linked entity '{entity.text}' ({entity.entity_type.value}) "
                    f"to memory {memory_id}"
                )
        except Exception as e:
            logger.error(f"Failed to link entity '{entity.text}': {e}")
            continue

    return entity_ids
