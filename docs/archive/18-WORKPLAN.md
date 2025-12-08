# Workplan 18: Real-Time Team Sync (v1.1.0)

> ## ⚠️ DEPRECATED - DO NOT USE
>
> **Status**: DEPRECATED (2025-12-07)
> **Reason**: Superseded by memorygraph.dev project workplans
>
> **Real-time team sync belongs in the separate `memorygraph.dev` repository.**
>
> ### What to Use Instead
>
> See `/Users/gregorydickson/memorygraph.dev/docs/planning/` for:
> - **Cloud infrastructure** - Already deployed (Workplans 1-4, 6-7)
> - **Real-time sync** - Server-side implementation required
> - **Team collaboration** - Workspace management and RBAC
>
> ### Why This Workplan Doesn't Belong Here
>
> | Component | This Workplan Proposed | Repository Scope |
> |-----------|----------------------|------------------|
> | Team Models | `src/memorygraph_cloud/models/team.py` | ❌ Server-side (memorygraph.dev) |
> | SSE Server | `src/memorygraph_cloud/sync/sse.py` | ❌ Server-side (memorygraph.dev) |
> | Redis Pub/Sub | `src/memorygraph_cloud/sync/pubsub.py` | ❌ Server-side (memorygraph.dev) |
> | Cloud Backend Client | `src/memorygraph/backends/cloud_backend.py` | ✅ Already implemented (WP20) |
>
> ### Repository Responsibilities
>
> - **claude-code-memory** (this repo): Local MCP server + cloud backend **client** adapter
> - **memorygraph.dev**: Cloud API, auth service, graph service, team sync **server**
>
> **The memorygraph.dev decisions prevail.** This workplan is kept for historical reference only.

---

## ~~Overview~~ (DEPRECATED)

~~Implement real-time memory synchronization for teams. When one team member creates/updates a memory, others see it immediately without manual sync commands.~~

**Competitive Advantage**: Cipher uses manual `brv pull` commands. Our cloud-native approach provides automatic, real-time sync—a superior UX.

**Reference**: PRODUCT_ROADMAP.md Phase 4 (Team Features)

---

## Goal

Enable teams to:
- Share memories automatically (no manual sync)
- See real-time updates when teammates add memories
- Collaborate on knowledge building
- Maintain workspace-scoped memories

---

## Success Criteria

- [ ] Real-time updates using WebSocket or Server-Sent Events
- [ ] Team members see new memories within 5 seconds
- [ ] Automatic sync when online (works offline, syncs on reconnect)
- [ ] Conflict resolution for concurrent edits
- [ ] Team activity feed showing recent changes
- [ ] 25+ tests passing for sync logic

---

## Section 1: Team Workspace Model

### 1.1 Database Schema

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/models/team.py`

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime

# Association table for team membership
team_members = Table(
    'team_members',
    Base.metadata,
    Column('team_id', String, ForeignKey('teams.id')),
    Column('user_id', String, ForeignKey('users.id')),
    Column('role', String, default='member'),  # 'owner', 'admin', 'member'
    Column('joined_at', DateTime, default=datetime.utcnow)
)


class Team(Base):
    """Team workspace model."""
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)  # URL-friendly name

    # Owner
    owner_id = Column(String, ForeignKey('users.id'), nullable=False)

    # Subscription
    subscription_tier = Column(String, default="team")
    stripe_subscription_id = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("User", secondary=team_members, back_populates="teams")
    memories = relationship("TeamMemory", back_populates="team")


class TeamMemory(Base):
    """Memory scoped to a team workspace."""
    __tablename__ = "team_memories"

    id = Column(String, primary_key=True)
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)

    # Memory fields (same as individual memories)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    tags = Column(String)  # JSON array
    importance = Column(Float, default=0.5)
    context = Column(String)  # JSON

    # Attribution
    created_by = Column(String, ForeignKey('users.id'), nullable=False)
    updated_by = Column(String, ForeignKey('users.id'), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="memories")
    creator = relationship("User", foreign_keys=[created_by])
```

**Tasks**:
- [ ] Create team models
- [ ] Add Alembic migration
- [ ] Implement team CRUD operations
- [ ] Add team member management (add/remove users)
- [ ] Add role-based permissions (owner, admin, member)

### 1.2 Workspace Switching

**User can switch between**:
- Personal workspace (individual memories)
- Team workspaces (shared memories)

**API Endpoint**:
```python
@router.get("/api/v1/workspaces")
async def list_workspaces(user: User = Depends(get_current_active_user)):
    """List all workspaces user has access to."""
    workspaces = [
        {
            "id": user.id,
            "name": "Personal",
            "type": "personal"
        }
    ]

    # Add team workspaces
    for team in user.teams:
        workspaces.append({
            "id": team.id,
            "name": team.name,
            "type": "team"
        })

    return {"workspaces": workspaces}
```

**Tasks**:
- [ ] Implement workspace listing API
- [ ] Add workspace selection to dashboard UI
- [ ] Store current workspace in session/local storage
- [ ] Filter memories by workspace

---

## Section 2: Real-Time Sync Architecture

### 2.1 Technology Choice

**Options**:

1. **WebSockets** (bidirectional, persistent connection)
   - Pros: True real-time, bidirectional
   - Cons: More complex, requires connection management

2. **Server-Sent Events (SSE)** (unidirectional, simpler)
   - Pros: Simpler, built-in reconnection, works through proxies
   - Cons: Unidirectional (server → client only)

3. **Polling** (fallback, simple but inefficient)
   - Pros: Simple, works everywhere
   - Cons: Inefficient, higher latency

**Recommendation**: **SSE for primary, polling for fallback**
- SSE is simpler than WebSockets
- Sufficient for one-way updates (server → clients)
- Automatic reconnection built-in
- Works with Cloud Run (unlike long-lived WebSocket connections)

**Tasks**:
- [ ] Design sync architecture
- [ ] Choose SSE as primary method
- [ ] Implement polling fallback
- [ ] Document architecture decision in ADR

### 2.2 SSE Implementation

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/sync/sse.py`

```python
"""
Server-Sent Events for real-time updates.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from ..auth.middleware import get_current_active_user
import asyncio
import json

router = APIRouter()


@router.get("/api/v1/sync/stream")
async def sync_stream(
    request: Request,
    workspace_id: str,
    user: User = Depends(get_current_active_user)
):
    """
    Server-Sent Events stream for real-time memory updates.

    Client connects to this endpoint and receives events when
    memories are created/updated in the workspace.
    """
    async def event_generator():
        """Generate SSE events."""
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'workspace_id': workspace_id})}\n\n"

        # Subscribe to Redis pub/sub for this workspace
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"workspace:{workspace_id}")

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Wait for messages (with timeout)
                message = await pubsub.get_message(timeout=30)

                if message and message['type'] == 'message':
                    # Forward to client
                    data = message['data'].decode('utf-8')
                    yield f"data: {data}\n\n"
                else:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"

                await asyncio.sleep(1)

        finally:
            await pubsub.unsubscribe(f"workspace:{workspace_id}")
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
```

**Tasks**:
- [ ] Implement SSE endpoint
- [ ] Use Redis pub/sub for message distribution
- [ ] Handle client disconnections gracefully
- [ ] Add heartbeat to keep connection alive
- [ ] Test with multiple clients

### 2.3 Redis Pub/Sub for Message Distribution

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/sync/pubsub.py`

```python
"""
Redis pub/sub for distributing memory updates.
"""
import redis
import json
import os

redis_client = redis.from_url(os.getenv("UPSTASH_REDIS_URL"))


def publish_memory_created(workspace_id: str, memory: dict):
    """Publish memory creation event to all workspace subscribers."""
    event = {
        "type": "memory_created",
        "workspace_id": workspace_id,
        "memory": memory
    }
    redis_client.publish(f"workspace:{workspace_id}", json.dumps(event))


def publish_memory_updated(workspace_id: str, memory: dict):
    """Publish memory update event."""
    event = {
        "type": "memory_updated",
        "workspace_id": workspace_id,
        "memory": memory
    }
    redis_client.publish(f"workspace:{workspace_id}", json.dumps(event))


def publish_memory_deleted(workspace_id: str, memory_id: str):
    """Publish memory deletion event."""
    event = {
        "type": "memory_deleted",
        "workspace_id": workspace_id,
        "memory_id": memory_id
    }
    redis_client.publish(f"workspace:{workspace_id}", json.dumps(event))
```

**Tasks**:
- [ ] Implement pub/sub functions
- [ ] Call publish functions after memory operations
- [ ] Add error handling
- [ ] Test message distribution

---

## Section 3: Client-Side Sync

### 3.1 EventSource Client (Browser)

**File**: `website/src/lib/sync.ts`

```typescript
/**
 * Real-time sync client for browser.
 */
export class SyncClient {
  private eventSource: EventSource | null = null;
  private workspaceId: string;
  private token: string;
  private onMemoryCreated: (memory: any) => void;
  private onMemoryUpdated: (memory: any) => void;
  private onMemoryDeleted: (memoryId: string) => void;

  constructor(
    workspaceId: string,
    token: string,
    handlers: {
      onMemoryCreated: (memory: any) => void;
      onMemoryUpdated: (memory: any) => void;
      onMemoryDeleted: (memoryId: string) => void;
    }
  ) {
    this.workspaceId = workspaceId;
    this.token = token;
    this.onMemoryCreated = handlers.onMemoryCreated;
    this.onMemoryUpdated = handlers.onMemoryUpdated;
    this.onMemoryDeleted = handlers.onMemoryDeleted;
  }

  connect() {
    const url = `https://api.memorygraph.dev/api/v1/sync/stream?workspace_id=${this.workspaceId}`;
    this.eventSource = new EventSource(url, {
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });

    this.eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'connected':
          console.log('Connected to sync stream');
          break;
        case 'memory_created':
          this.onMemoryCreated(data.memory);
          break;
        case 'memory_updated':
          this.onMemoryUpdated(data.memory);
          break;
        case 'memory_deleted':
          this.onMemoryDeleted(data.memory_id);
          break;
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      // EventSource will auto-reconnect
    };
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
```

**Tasks**:
- [ ] Implement browser EventSource client
- [ ] Add automatic reconnection handling
- [ ] Integrate with React/Vue state management
- [ ] Add connection status indicator in UI

### 3.2 MCP Client Sync (Python)

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/sync/client.py`

```python
"""
Sync client for MCP (background thread).
"""
import sseclient
import requests
import threading
import queue
import time


class SyncClient:
    """
    Background sync client for MCP.

    Listens to SSE stream and updates local cache.
    """

    def __init__(self, workspace_id: str, api_key: str, cache):
        self.workspace_id = workspace_id
        self.api_key = api_key
        self.cache = cache
        self.running = False
        self.thread = None

    def start(self):
        """Start sync in background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop sync."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _sync_loop(self):
        """Main sync loop."""
        url = f"https://api.memorygraph.dev/api/v1/sync/stream?workspace_id={self.workspace_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        while self.running:
            try:
                response = requests.get(url, headers=headers, stream=True)
                client = sseclient.SSEClient(response)

                for event in client.events():
                    if not self.running:
                        break

                    data = json.loads(event.data)
                    self._handle_event(data)

            except Exception as e:
                logger.error(f"Sync error: {e}")
                time.sleep(5)  # Retry after 5 seconds

    def _handle_event(self, data: dict):
        """Handle sync event."""
        if data['type'] == 'memory_created':
            self.cache.add_memory(data['memory'])
        elif data['type'] == 'memory_updated':
            self.cache.update_memory(data['memory'])
        elif data['type'] == 'memory_deleted':
            self.cache.delete_memory(data['memory_id'])
```

**Tasks**:
- [ ] Implement background sync client for MCP
- [ ] Use sseclient library for SSE
- [ ] Update local cache on sync events
- [ ] Handle reconnection on errors
- [ ] Add sync status to MCP tools

---

## Section 4: Conflict Resolution

### 4.1 Last-Write-Wins Strategy

**Simple approach for v1**:
- Each memory has `updated_at` timestamp
- On conflict, most recent update wins
- No complex CRDTs needed initially

**Implementation**:
```python
def resolve_conflict(local: Memory, remote: Memory) -> Memory:
    """
    Resolve conflict using last-write-wins.

    Returns:
        The memory with the latest updated_at timestamp
    """
    if remote.updated_at > local.updated_at:
        return remote
    return local
```

**Tasks**:
- [ ] Implement last-write-wins conflict resolution
- [ ] Log all conflicts for monitoring
- [ ] Notify users when their changes are overwritten (optional)
- [ ] Document conflict resolution strategy

### 4.2 Optimistic Locking (Future Enhancement)

**For v1.2**:
- Add version field to memories
- Check version on update
- Reject updates if version mismatch
- Force client to fetch latest and re-apply changes

**Tasks**:
- [ ] Document optimistic locking design (for future)
- [ ] Don't implement in v1.1 (keep simple)

---

## Section 5: Team Activity Feed

### 5.1 Activity Stream

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/models/activity.py`

```python
class Activity(Base):
    """Team activity log."""
    __tablename__ = "activities"

    id = Column(String, primary_key=True)
    team_id = Column(String, ForeignKey('teams.id'), nullable=False)

    # What happened
    action = Column(String, nullable=False)  # 'created', 'updated', 'deleted'
    entity_type = Column(String, nullable=False)  # 'memory', 'relationship'
    entity_id = Column(String, nullable=False)

    # Who did it
    user_id = Column(String, ForeignKey('users.id'), nullable=False)

    # Metadata
    metadata = Column(String)  # JSON (title, tags, etc. for display)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Tasks**:
- [ ] Create activity model
- [ ] Log all team memory operations
- [ ] Implement activity feed API
- [ ] Add pagination to activity feed
- [ ] Display in dashboard UI

### 5.2 Activity Feed UI

**File**: `website/src/components/ActivityFeed.astro`

**Display**:
```
Recent Activity

🟢 Alice added "Fixed Redis timeout" (2 minutes ago)
🔵 Bob updated "API retry pattern" (10 minutes ago)
🟠 Alice created relationship: ErrorA SOLVES SolutionX (1 hour ago)
```

**Tasks**:
- [ ] Create activity feed component
- [ ] Show recent team activity (last 50 items)
- [ ] Add real-time updates (via SSE)
- [ ] Add filtering (by user, by action, by date)
- [ ] Link to memories from activity

---

## Section 6: Offline Support

### 6.1 Offline Detection

**File**: `website/src/lib/offline.ts`

```typescript
export class OfflineManager {
  private isOnline: boolean = navigator.onLine;
  private queue: Array<any> = [];

  constructor() {
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }

  handleOffline() {
    this.isOnline = false;
    console.log('Offline: queuing operations');
  }

  handleOnline() {
    this.isOnline = true;
    console.log('Online: syncing queued operations');
    this.syncQueue();
  }

  async syncQueue() {
    // Process queued operations
    for (const op of this.queue) {
      try {
        await this.executeOperation(op);
      } catch (error) {
        console.error('Sync failed:', error);
      }
    }
    this.queue = [];
  }
}
```

**Tasks**:
- [ ] Implement offline detection
- [ ] Queue operations when offline
- [ ] Sync queue when back online
- [ ] Show offline indicator in UI
- [ ] Store queued operations in IndexedDB (persist across page refreshes)

### 6.2 Local Storage Cache

**For MCP clients**:
- Use local SQLite as cache
- Sync to cloud when online
- Work offline with local cache
- Merge changes on reconnection

**Tasks**:
- [ ] Use existing SQLite backend as local cache
- [ ] Add sync status to memories (synced, pending, conflict)
- [ ] Implement merge logic on reconnect
- [ ] Test offline → online → offline cycles

---

## Section 7: Team Member Management

### 7.1 Invitation System

**Flow**:
1. Team owner invites user by email
2. Email sent with invitation link
3. User clicks link and joins team
4. User has access to team workspace

**API**:
```python
@router.post("/api/v1/teams/{team_id}/invite")
async def invite_user(
    team_id: str,
    email: str,
    role: str = "member",
    user: User = Depends(get_current_active_user)
):
    """Invite a user to join the team."""
    # Verify user is team owner/admin
    team = get_team(team_id)
    if user.id != team.owner_id:
        raise HTTPException(403, "Only team owners can invite")

    # Create invitation
    invitation = create_invitation(team_id, email, role)

    # Send email
    send_invitation_email(email, invitation.token)

    return {"invitation_id": invitation.id, "status": "sent"}


@router.post("/api/v1/invitations/{token}/accept")
async def accept_invitation(token: str, user: User = Depends(get_current_active_user)):
    """Accept team invitation."""
    invitation = get_invitation_by_token(token)

    if not invitation or invitation.email != user.email:
        raise HTTPException(404, "Invitation not found")

    # Add user to team
    add_team_member(invitation.team_id, user.id, invitation.role)

    # Mark invitation as accepted
    invitation.accepted_at = datetime.utcnow()
    db.commit()

    return {"team_id": invitation.team_id}
```

**Tasks**:
- [ ] Create invitation model and table
- [ ] Implement invite API endpoint
- [ ] Implement accept invitation endpoint
- [ ] Send invitation emails (via Supabase or SendGrid)
- [ ] Add invitation UI to dashboard

### 7.2 Member Management UI

**Dashboard page**: `/dashboard/teams/{team_id}/members`

**Features**:
- List all team members
- Show roles (owner, admin, member)
- Invite new members (owners/admins only)
- Remove members (owners/admins only)
- Change member roles (owners only)

**Tasks**:
- [ ] Create team members page
- [ ] Implement member list
- [ ] Add invite form
- [ ] Add remove member button
- [ ] Add role change dropdown

---

## Section 8: RBAC (Role-Based Access Control)

### 8.1 Permission Model

**Roles**:
- **Owner**: Full access, can delete team, manage billing
- **Admin**: Can invite/remove members, manage team settings
- **Member**: Can read/write memories, cannot manage team

**Permissions**:
```python
PERMISSIONS = {
    "owner": [
        "memory.read",
        "memory.write",
        "memory.delete",
        "team.read",
        "team.write",
        "team.delete",
        "member.invite",
        "member.remove",
        "member.change_role",
        "billing.manage"
    ],
    "admin": [
        "memory.read",
        "memory.write",
        "memory.delete",
        "team.read",
        "team.write",
        "member.invite",
        "member.remove"
    ],
    "member": [
        "memory.read",
        "memory.write",
        "team.read"
    ]
}
```

**Tasks**:
- [ ] Define permission model
- [ ] Implement permission checks in API
- [ ] Add middleware to enforce permissions
- [ ] Test permission enforcement
- [ ] Document permissions in API docs

### 8.2 Permission Middleware

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/auth/rbac.py`

```python
def require_permission(permission: str):
    """Decorator to check if user has required permission."""
    def decorator(func):
        async def wrapper(team_id: str, user: User = Depends(get_current_active_user), *args, **kwargs):
            # Get user's role in team
            member = get_team_member(team_id, user.id)
            if not member:
                raise HTTPException(403, "Not a team member")

            # Check permission
            if permission not in PERMISSIONS[member.role]:
                raise HTTPException(403, f"Missing permission: {permission}")

            return await func(team_id, user, *args, **kwargs)
        return wrapper
    return decorator


# Usage
@router.delete("/api/v1/teams/{team_id}/members/{user_id}")
@require_permission("member.remove")
async def remove_member(team_id: str, user_id: str, user: User = Depends(...)):
    """Remove a team member."""
    pass
```

**Tasks**:
- [ ] Implement permission decorator
- [ ] Add to all protected endpoints
- [ ] Test with different roles
- [ ] Return clear error messages

---

## Section 9: Testing

### 9.1 Sync Integration Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/sync/test_realtime.py`

**Tests**:
- [ ] Test SSE connection and disconnection
- [ ] Test message distribution to multiple clients
- [ ] Test offline queuing and sync
- [ ] Test conflict resolution
- [ ] Test team workspace isolation (messages don't leak between teams)

### 9.2 Team Management Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/teams/test_teams.py`

**Tests**:
- [ ] Test team creation
- [ ] Test member invitation and acceptance
- [ ] Test member removal
- [ ] Test role changes
- [ ] Test RBAC permission enforcement

### 9.3 Load Tests

**Scenarios**:
- 100 concurrent SSE connections
- 1000 messages per second distributed to clients
- Team with 50 members

**Tasks**:
- [ ] Create load test scenarios (Locust or k6)
- [ ] Test SSE scalability
- [ ] Test Redis pub/sub under load
- [ ] Identify bottlenecks
- [ ] Optimize as needed

---

## Section 10: Documentation

### 10.1 Team Sync Documentation

**File**: `/Users/gregorydickson/claude-code-memory/docs/team-sync.md`

**Content**:
- How real-time sync works
- How to create/manage teams
- How to invite members
- Offline behavior
- Conflict resolution

**Tasks**:
- [ ] Write comprehensive team sync guide
- [ ] Add architecture diagrams
- [ ] Document API endpoints
- [ ] Add troubleshooting section

### 10.2 API Documentation

**Update cloud API docs with**:
- Team endpoints
- Sync endpoints (SSE)
- Invitation endpoints
- Activity feed endpoints

**Tasks**:
- [ ] Document all new endpoints
- [ ] Add examples for each endpoint
- [ ] Update OpenAPI spec

---

## Acceptance Criteria Summary

### Functional
- [ ] Real-time sync working (SSE)
- [ ] Team workspaces working
- [ ] Member invitation working
- [ ] Activity feed showing updates
- [ ] Offline support working

### Performance
- [ ] Updates appear within 5 seconds
- [ ] SSE supports 100+ concurrent connections
- [ ] Low latency (<100ms to receive update)

### Quality
- [ ] 25+ tests passing
- [ ] Load tests passing
- [ ] No message loss
- [ ] Graceful degradation when offline

### Documentation
- [ ] Team sync guide published
- [ ] API docs updated
- [ ] Troubleshooting guide complete

---

## Notes for Coding Agent

**Critical Implementation Details**:

1. **SSE is simpler than WebSockets**: Start with SSE, add WebSockets only if needed.

2. **Redis pub/sub is key**: All sync messages go through Redis to support multiple API instances.

3. **Conflict resolution should be simple**: Last-write-wins for v1.1. Don't over-engineer CRDTs.

4. **Test offline scenarios**: Offline → online → offline is complex. Test thoroughly.

5. **Security**: Verify workspace access on every SSE connection. Don't leak data between teams.

---

## Dependencies

**External**:
- Redis (Upstash) for pub/sub
- SSE client libraries (sseclient for Python)
- WebSockets library (if needed later)

**Internal**:
- Team models (this workplan)
- Auth system (Workplan 15)
- Cloud API (Workplan 14)

---

## Estimated Timeline

| Section | Effort | Dependencies |
|---------|--------|--------------|
| Section 1: Team Model | 3-4 hours | Database ready |
| Section 2: SSE Sync | 4-5 hours | Redis set up |
| Section 3: Client Sync | 3-4 hours | SSE server done |
| Section 4: Conflict Resolution | 2 hours | Sync working |
| Section 5: Activity Feed | 2-3 hours | Team model done |
| Section 6: Offline Support | 3-4 hours | Sync working |
| Section 7: Member Management | 2-3 hours | Team model done |
| Section 8: RBAC | 2-3 hours | Team model done |
| Section 9: Testing | 3-4 hours | All impl done |
| Section 10: Documentation | 2-3 hours | All done |
| **Total** | **26-37 hours** | Sequential + parallel |

---

## References

- **PRODUCT_ROADMAP.md**: Phase 4 (Team Features)
- **Workplan 14**: Cloud infrastructure
- **Workplan 15**: Authentication
- **SSE MDN Docs**: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events

---

**Last Updated**: 2025-12-07
**Status**: ❌ DEPRECATED (moved to memorygraph.dev)
**Next Step**: See memorygraph.dev repository for team sync implementation
