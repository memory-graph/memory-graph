# ADR 002: Model Context Protocol (MCP) for Claude Integration

## Status
Accepted

## Date
2025-06-28

## Context
Claude Code needed a standardized way to interact with the memory system. We needed a protocol that:

1. **Supports Tool Calling**: Claude can invoke memory operations as tools
2. **Structured Responses**: Clear, parseable responses
3. **Error Handling**: Robust error reporting
4. **Future Proof**: Can evolve with new features
5. **Official Support**: Maintained by Anthropic

## Decision Drivers
- **Claude Integration**: Native integration with Claude desktop and API
- **Tool Discovery**: Claude can discover available memory operations
- **Type Safety**: Schema-based tool definitions with validation
- **Bidirectional Communication**: Server can push updates to Claude
- **Ecosystem**: Part of broader MCP ecosystem

## Considered Options

### Option 1: Custom JSON-RPC API
**Pros:**
- Full control over protocol design
- Can optimize for specific use cases
- No external dependencies

**Cons:**
- Need to maintain protocol spec
- Claude would need custom integration
- No tool discovery mechanism
- Manual error handling patterns

### Option 2: REST API
**Pros:**
- Familiar to developers
- Good tooling and ecosystem
- Cacheable responses

**Cons:**
- No native Claude integration
- No tool discovery
- Requires API key management
- Stateless (harder for context tracking)

### Option 3: Model Context Protocol (MCP)
**Pros:**
- Official Anthropic protocol
- Native Claude desktop integration
- Automatic tool discovery
- Structured tool definitions
- Built-in error handling
- Part of growing ecosystem

**Cons:**
- Newer protocol, evolving
- MCP SDK dependency
- Some features still in development

## Decision
We chose **Model Context Protocol (MCP)** because:

1. **Official Integration**: Native support in Claude desktop
2. **Tool Definitions**: Tools are self-documenting with schemas
3. **Type Safety**: Pydantic models + MCP schemas
4. **Error Handling**: Built-in error response structure
5. **Future Proof**: Anthropic-backed, will evolve with Claude

## Implementation Details

### Tool Registration
```python
from mcp.server import Server
from mcp.types import Tool

server = Server("claude-memory")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="store_memory",
            description="Store a new memory with context and metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["solution", "problem", ...]},
                    "title": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["type", "title", "content"]
            }
        )
    ]
```

### Error Responses
```python
from mcp.types import CallToolResult, TextContent

# Success
return CallToolResult(
    content=[TextContent(type="text", text="Memory stored successfully")],
    isError=False
)

# Error
return CallToolResult(
    content=[TextContent(type="text", text="Validation error: title required")],
    isError=True
)
```

## Consequences

### Positive
- **Zero Configuration**: Works with Claude desktop out of the box
- **Tool Discovery**: Claude automatically discovers all 8 memory tools
- **Schema Validation**: Input validation at protocol level
- **Error Clarity**: Structured error responses
- **Community**: Part of growing MCP ecosystem

### Negative
- **MCP Dependency**: Tied to MCP SDK lifecycle
- **Limited Documentation**: Protocol is new, docs are evolving
- **Breaking Changes**: Protocol may evolve (though versioned)

### Mitigations
- **Async Implementation**: Use async handlers for performance
- **Comprehensive Testing**: 19 server tests for MCP compliance
- **Error Handling**: Custom exceptions + MCP error responses
- **Documentation**: Clear examples of all 8 tools
- **Version Pinning**: Pin MCP SDK version in requirements

## Alternative Considered: Hybrid Approach
We considered building both MCP and REST APIs, but decided against it because:
- MCP covers all use cases
- Maintaining two APIs doubles complexity
- REST can be added later if needed
- Focus on MCP-first for best Claude experience

## References
- [Model Context Protocol Spec](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop MCP Integration](https://claude.ai/mcp)
- [MCP Tool Guidelines](https://spec.modelcontextprotocol.io/specification/tools/)
