/**
 * Data models for the MemoryGraph SDK.
 *
 * Lightweight, self-contained types mirroring the Python SDK pydantic models.
 * Datetimes are represented as ISO strings to keep the SDK JSON-friendly.
 */

// ---------------------------------------------------------------------------
// Enums (string union types with a runtime constant object for reflection)
// ---------------------------------------------------------------------------

export const MemoryType = {
  TASK: "task",
  CODE_PATTERN: "code_pattern",
  PROBLEM: "problem",
  SOLUTION: "solution",
  PROJECT: "project",
  TECHNOLOGY: "technology",
  ERROR: "error",
  FIX: "fix",
  COMMAND: "command",
  FILE_CONTEXT: "file_context",
  WORKFLOW: "workflow",
  GENERAL: "general",
  CONVERSATION: "conversation",
} as const;

export type MemoryType = (typeof MemoryType)[keyof typeof MemoryType];

export const RelationshipType = {
  CAUSES: "CAUSES",
  TRIGGERS: "TRIGGERS",
  LEADS_TO: "LEADS_TO",
  PREVENTS: "PREVENTS",
  BREAKS: "BREAKS",
  SOLVES: "SOLVES",
  ADDRESSES: "ADDRESSES",
  ALTERNATIVE_TO: "ALTERNATIVE_TO",
  IMPROVES: "IMPROVES",
  REPLACES: "REPLACES",
  OCCURS_IN: "OCCURS_IN",
  APPLIES_TO: "APPLIES_TO",
  WORKS_WITH: "WORKS_WITH",
  REQUIRES: "REQUIRES",
  USED_IN: "USED_IN",
  BUILDS_ON: "BUILDS_ON",
  CONTRADICTS: "CONTRADICTS",
  CONFIRMS: "CONFIRMS",
  GENERALIZES: "GENERALIZES",
  SPECIALIZES: "SPECIALIZES",
  SIMILAR_TO: "SIMILAR_TO",
  VARIANT_OF: "VARIANT_OF",
  RELATED_TO: "RELATED_TO",
  ANALOGY_TO: "ANALOGY_TO",
  OPPOSITE_OF: "OPPOSITE_OF",
  FOLLOWS: "FOLLOWS",
  DEPENDS_ON: "DEPENDS_ON",
  ENABLES: "ENABLES",
  BLOCKS: "BLOCKS",
  PARALLEL_TO: "PARALLEL_TO",
  EFFECTIVE_FOR: "EFFECTIVE_FOR",
  INEFFECTIVE_FOR: "INEFFECTIVE_FOR",
  PREFERRED_OVER: "PREFERRED_OVER",
  DEPRECATED_BY: "DEPRECATED_BY",
  VALIDATED_BY: "VALIDATED_BY",
} as const;

export type RelationshipType = (typeof RelationshipType)[keyof typeof RelationshipType];

// ---------------------------------------------------------------------------
// Core domain types
// ---------------------------------------------------------------------------

/**
 * A memory stored in MemoryGraph.
 *
 * Field names mirror the JSON returned by the MemoryGraph Cloud API.
 */
export interface Memory {
  id: string;
  type: string;
  title: string;
  content: string;
  tags: string[];
  importance: number;
  context?: Record<string, unknown> | null;
  summary?: string | null;
  created_at: string;
  updated_at: string;
}

/** Request payload for creating a memory. */
export interface MemoryCreate {
  [key: string]: unknown;
  type: string;
  title: string;
  content: string;
  tags?: string[];
  importance?: number;
  context?: Record<string, unknown> | null;
  summary?: string | null;
}

/** Request payload for updating a memory. All fields optional. */
export interface MemoryUpdate {
  [key: string]: unknown;
  title?: string;
  content?: string;
  tags?: string[];
  importance?: number;
  summary?: string | null;
}

/**
 * A relationship between two memories.
 */
export interface Relationship {
  id: string;
  from_memory_id: string;
  to_memory_id: string;
  relationship_type: string;
  strength: number;
  confidence: number;
  context?: string | null;
  created_at: string;
  // Bi-temporal tracking fields (optional)
  valid_from?: string | null;
  valid_until?: string | null;
  recorded_at?: string | null;
  invalidated_by?: string | null;
}

/** Request payload for creating a relationship. */
export interface RelationshipCreate {
  [key: string]: unknown;
  from_memory_id: string;
  to_memory_id: string;
  relationship_type: string;
  strength?: number;
  confidence?: number;
  context?: string | null;
}

/** Result from a memory search. */
export interface SearchResult {
  memories: Memory[];
  total: number;
  offset: number;
  limit: number;
}

/** A memory returned as part of relationship traversal. */
export interface RelatedMemory {
  memory: Memory;
  relationship_type: string;
  strength: number;
  depth: number;
}
