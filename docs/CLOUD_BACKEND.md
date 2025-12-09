# MemoryGraph Cloud Backend

The cloud backend enables you to sync your memories across devices and collaborate with team members using MemoryGraph Cloud.

## Features

- **Multi-device sync**: Access your memories from any device
- **Team collaboration**: Share memories with your team
- **Automatic backups**: Your data is safely stored in the cloud
- **Usage analytics**: Track your memory usage and patterns

## Quick Start

### 1. Get Your API Key

1. Sign up at [https://app.memorygraph.dev](https://app.memorygraph.dev)
2. Go to **Settings** → **API Keys**
3. Click **Generate New Key**
4. Copy your API key (starts with `mg_`)

### 2. Configure the MCP Server

Set the environment variable and backend type:

```bash
export MEMORYGRAPH_API_KEY=mg_your_api_key_here
export MEMORY_BACKEND=cloud
```

Or configure in your Claude Code settings:

```bash
claude mcp add --scope user memorygraph \
  --env MEMORYGRAPH_API_KEY=mg_your_key_here \
  --env MEMORY_BACKEND=cloud \
  -- memorygraph
```

### 3. Verify Connection

Ask Claude to store and recall a memory:

```
You: Store a memory about setting up cloud backend
Claude: ✓ Stored memory in cloud: mem_xxxxx

You: Recall memories about cloud
Claude: Found 1 memory about cloud backend setup...
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MEMORYGRAPH_API_KEY` | Yes | - | Your API key (starts with `mg_`) |
| `MEMORY_BACKEND` | No | `sqlite` | Set to `cloud` for cloud backend |
| `MEMORYGRAPH_API_URL` | No | `https://graph-api.memorygraph.dev` | API endpoint URL |
| `MEMORYGRAPH_TIMEOUT` | No | `30` | Request timeout in seconds |

### Example Configurations

**Basic cloud setup:**
```bash
export MEMORYGRAPH_API_KEY=mg_xxxxx
export MEMORY_BACKEND=cloud
```

**Custom timeout for slow connections:**
```bash
export MEMORYGRAPH_API_KEY=mg_xxxxx
export MEMORY_BACKEND=cloud
export MEMORYGRAPH_TIMEOUT=60
```

**Development with staging API:**
```bash
export MEMORYGRAPH_API_KEY=mg_test_xxxxx
export MEMORY_BACKEND=cloud
export MEMORYGRAPH_API_URL=https://staging-api.memorygraph.dev
```

## Usage

The cloud backend supports all standard MCP tools:

### Storing Memories
```
store_memory(
  type="solution",
  title="Fixed Redis timeout issue",
  content="Increased timeout to 30 seconds...",
  tags=["redis", "timeout", "fix"]
)
```

### Recalling Memories
```
recall_memories(query="Redis timeout solutions")
```

### Searching Memories
```
search_memories(
  query="redis",
  memory_types=["solution"],
  limit=10
)
```

### Creating Relationships
```
create_relationship(
  from_memory_id="mem_solution",
  to_memory_id="mem_problem",
  relationship_type="SOLVES"
)
```

## Error Handling

### Authentication Errors (401)

```
Error: Invalid API key
```

**Solution**: Verify your API key is correct and hasn't expired. Generate a new key at [https://app.memorygraph.dev/settings](https://app.memorygraph.dev/settings).

### Usage Limit Exceeded (403)

```
Error: Usage limit exceeded. Upgrade at https://app.memorygraph.dev/pricing
```

**Solution**: You've reached your plan's limits. Either:
- Delete unused memories
- Upgrade to a higher tier

### Rate Limit Exceeded (429)

```
Error: Rate limit exceeded. Please slow down requests.
```

**Solution**: The cloud backend automatically retries with exponential backoff. If you see this frequently, consider:
- Batching operations
- Adding delays between requests
- Contacting support for rate limit increase

### Connection Errors

```
Error: Cannot connect to Graph API
```

**Solution**:
1. Check your internet connection
2. Verify the API URL is correct
3. Try again - transient errors are automatically retried

## Migration from Local Backend

To migrate your local memories to the cloud:

### Option 1: Export and Import (Recommended)

```bash
# Export from local backend
memorygraph export --output memories.json

# Switch to cloud backend
export MEMORY_BACKEND=cloud
export MEMORYGRAPH_API_KEY=mg_xxxxx

# Import to cloud
memorygraph import --input memories.json
```

### Option 2: Manual Migration

1. Continue using local backend alongside cloud
2. Gradually re-store important memories to cloud
3. Switch to cloud-only when ready

## Troubleshooting

### "MEMORYGRAPH_API_KEY is required"

The API key environment variable is not set. Export it before starting:

```bash
export MEMORYGRAPH_API_KEY=mg_your_key_here
```

### "API key does not start with 'mg_'"

MemoryGraph API keys always start with `mg_`. Ensure you're using the correct key from your dashboard.

### Slow Performance

1. Check your internet connection
2. Increase timeout: `export MEMORYGRAPH_TIMEOUT=60`
3. The first request may be slower due to connection establishment

### Memories Not Syncing

1. Verify you're using `MEMORY_BACKEND=cloud`
2. Check that the same API key is used across devices
3. Look for error messages in logs

## Local vs Cloud Comparison

| Feature | Local (SQLite) | Cloud |
|---------|----------------|-------|
| Setup | Zero config | Requires API key |
| Multi-device | ❌ | ✅ |
| Team sharing | ❌ | ✅ |
| Offline access | ✅ | ❌ (planned) |
| Backups | Manual | Automatic |
| Cost | Free | Free tier + paid plans |

## Security

- All data is encrypted in transit (TLS 1.3)
- API keys can be rotated at any time
- Per-user data isolation
- No memory content is logged

## Support

- Documentation: [https://memorygraph.dev/docs](https://memorygraph.dev/docs)
- Issues: [https://github.com/gregorydickson/memory-graph/issues](https://github.com/gregorydickson/memory-graph/issues)
- Email: support@memorygraph.dev
