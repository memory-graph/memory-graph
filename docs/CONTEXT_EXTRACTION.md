# Automatic Context Extraction

When creating relationships between memories, MemoryGraph automatically extracts structured information from natural language context. This enables powerful filtering and search while maintaining full backward compatibility.

## How It Works

Write natural language when creating relationships:

```python
create_relationship(
    from_memory_id="mem_123",
    to_memory_id="mem_456",
    relationship_type="SOLVES",
    context="partially implements auth module, only works in production"
)
```

MemoryGraph automatically extracts:

```json
{
    "text": "partially implements auth module, only works in production",
    "scope": "partial",
    "components": ["auth module"],
    "conditions": ["production"],
    "evidence": [],
    "temporal": null,
    "exceptions": []
}
```

## Structured Query Support

Search relationships by their extracted context structure:

```json
{
  "tool": "search_relationships_by_context",
  "scope": "partial",
  "conditions": ["production"],
  "limit": 10
}
```

### Available Filters

- **scope**: `"partial"`, `"full"`, or `"conditional"` - Filter by implementation completeness
- **conditions**: `["production", "Redis enabled"]` - Filter by when/where the relationship applies (OR logic)
- **has_evidence**: `true` / `false` - Filter by whether the relationship has verification
- **evidence**: `["integration tests", "unit tests"]` - Filter by specific evidence types (OR logic)
- **components**: `["auth", "Redis"]` - Filter by mentioned components or modules (OR logic)
- **temporal**: `"v2.1.0"` - Filter by version or time information
- **limit**: `20` - Maximum number of results (default: 20)

### Example Queries

Find all partial implementations:
```json
{
  "tool": "search_relationships_by_context",
  "scope": "partial"
}
```

Find production-only relationships verified by tests:
```json
{
  "tool": "search_relationships_by_context",
  "conditions": ["production"],
  "has_evidence": true
}
```

Find all auth-related relationships:
```json
{
  "tool": "search_relationships_by_context",
  "components": ["auth"]
}
```

Combined filters (uses AND logic between different filter types):
```json
{
  "tool": "search_relationships_by_context",
  "scope": "partial",
  "conditions": ["production"],
  "components": ["auth"],
  "has_evidence": true
}
```

## Extracted Fields

The system recognizes and extracts these categories:

- **scope**: Completeness indicators (partial, full, conditional)
- **components**: Mentioned modules, systems, or services
- **conditions**: When/if/requires patterns (environments, dependencies)
- **evidence**: Verification mentions (tested by, verified by, observed in)
- **temporal**: Version numbers, dates, or time-based information
- **exceptions**: Exclusions or limitations (except, excluding, but not)

## Examples

```python
# Scope detection
"fully supports user authentication" → scope: "full"
"limited to admin users" → scope: "partial"

# Conditions
"only works in production environment" → conditions: ["production"]
"requires Redis to be available" → conditions: ["Redis to be available"]

# Evidence
"verified by integration tests" → evidence: ["integration tests"]
"tested by QA team" → evidence: ["QA team"]

# Temporal
"implemented in v2.1.0" → temporal: "v2.1.0"
"since March 2024" → temporal: "March 2024"

# Exceptions
"supports all formats except XML" → exceptions: ["XML"]
"works without authentication" → exceptions: ["authentication"]
```

## Token Trade-off

Structure adds approximately 8-13 tokens per relationship context for storage:
- **Original text only**: ~12 tokens
- **Structured format**: ~20-25 tokens

The benefit is queryability and relationship intelligence, not token reduction. The original text is always preserved for readability.

## Backward Compatibility

All existing relationships with free-text contexts continue to work. The system automatically:
1. Tries parsing as JSON (new structured format)
2. Falls back to pattern extraction (legacy free text)
3. Returns empty structure if context is null/empty

No migration or changes required to existing data.
