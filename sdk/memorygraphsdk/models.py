"""
Pydantic models for MemoryGraph SDK.
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryType(str, Enum):
    """Types of memories that can be stored."""

    TASK = "task"
    CODE_PATTERN = "code_pattern"
    PROBLEM = "problem"
    SOLUTION = "solution"
    PROJECT = "project"
    TECHNOLOGY = "technology"
    ERROR = "error"
    FIX = "fix"
    COMMAND = "command"
    FILE_CONTEXT = "file_context"
    WORKFLOW = "workflow"
    GENERAL = "general"
    CONVERSATION = "conversation"


class RelationshipType(str, Enum):
    """Types of relationships between memories."""

    CAUSES = "CAUSES"
    TRIGGERS = "TRIGGERS"
    LEADS_TO = "LEADS_TO"
    PREVENTS = "PREVENTS"
    BREAKS = "BREAKS"
    SOLVES = "SOLVES"
    ADDRESSES = "ADDRESSES"
    ALTERNATIVE_TO = "ALTERNATIVE_TO"
    IMPROVES = "IMPROVES"
    REPLACES = "REPLACES"
    OCCURS_IN = "OCCURS_IN"
    APPLIES_TO = "APPLIES_TO"
    WORKS_WITH = "WORKS_WITH"
    REQUIRES = "REQUIRES"
    USED_IN = "USED_IN"
    BUILDS_ON = "BUILDS_ON"
    CONTRADICTS = "CONTRADICTS"
    CONFIRMS = "CONFIRMS"
    GENERALIZES = "GENERALIZES"
    SPECIALIZES = "SPECIALIZES"
    SIMILAR_TO = "SIMILAR_TO"
    VARIANT_OF = "VARIANT_OF"
    RELATED_TO = "RELATED_TO"
    ANALOGY_TO = "ANALOGY_TO"
    OPPOSITE_OF = "OPPOSITE_OF"
    FOLLOWS = "FOLLOWS"
    DEPENDS_ON = "DEPENDS_ON"
    ENABLES = "ENABLES"
    BLOCKS = "BLOCKS"
    PARALLEL_TO = "PARALLEL_TO"


class Memory(BaseModel):
    """A memory stored in MemoryGraph."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str  # Using str to allow custom types
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    context: dict[str, Any] | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime


class MemoryCreate(BaseModel):
    """Request model for creating a memory."""

    type: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    context: dict[str, Any] | None = None
    summary: str | None = None


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""

    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    importance: float | None = Field(default=None, ge=0.0, le=1.0)
    summary: str | None = None


class Relationship(BaseModel):
    """A relationship between two memories."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    from_memory_id: str
    to_memory_id: str
    relationship_type: str
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    context: str | None = None
    created_at: datetime


class RelationshipCreate(BaseModel):
    """Request model for creating a relationship."""

    from_memory_id: str
    to_memory_id: str
    relationship_type: str
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    context: str | None = None


class SearchResult(BaseModel):
    """Result from a memory search."""

    memories: list[Memory]
    total: int
    offset: int
    limit: int


class RelatedMemory(BaseModel):
    """A memory returned as part of relationship traversal."""

    memory: Memory
    relationship_type: str
    strength: float
    depth: int
