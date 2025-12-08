# Workplan 14: Cloud Infrastructure - LOW COST (v1.0.0)

> ## ⚠️ DEPRECATED - DO NOT USE
>
> **Status**: DEPRECATED (2025-12-06)
> **Reason**: Superseded by memorygraph.dev project workplans
>
> **The cloud infrastructure is being built in the separate `memorygraph.dev` repository.**
>
> ### What to Use Instead
>
> See `/Users/gregorydickson/memorygraph.dev/docs/planning/`:
> - **Workplan 1**: Infrastructure (✅ COMPLETE) - GCP, Cloud SQL, FalkorDB
> - **Workplan 2**: Auth Service (✅ COMPLETE) - FastAPI, JWT, API Keys
> - **Workplan 3**: Marketing Site (✅ COMPLETE) - Astro, Cloudflare Pages
> - **Workplan 4**: Graph Service (🚧 75% COMPLETE) - FastAPI, FalkorDB
> - **Workplan 6**: User Dashboard (✅ COMPLETE) - Next.js, Cloud Run
> - **Workplan 7**: Operations - Monitoring, logging, security
>
> ### Key Architecture Decisions (memorygraph.dev)
>
> | Component | memorygraph.dev Decision | This Workplan Proposed |
> |-----------|-------------------------|----------------------|
> | Auth | FastAPI + PostgreSQL + JWT | Supabase Auth |
> | Storage | FalkorDB Cloud + Cloud SQL | Turso + Supabase |
> | API | FastAPI on Cloud Run | FastAPI on Cloud Run ✅ |
> | Website | Cloudflare Pages | Cloudflare Pages ✅ |
> | Dashboard | Next.js on Cloud Run | Astro static |
>
> **The memorygraph.dev decisions prevail.** This workplan is kept for historical reference only.

---

## ~~Overview~~ (DEPRECATED)

~~Deploy memorygraph.dev cloud platform using cost-effective managed services. Prioritize free tiers and pay-per-use over fixed infrastructure costs. Target: <$50/month for first 1000 users.~~

**Cost Philosophy**: Bootstrap-friendly. Use free tiers and serverless where possible. Avoid Kubernetes complexity and fixed compute costs.

**Reference**: PRODUCT_ROADMAP.md Phase 3 (Cloud Launch)

---

## Goal

Launch memorygraph.dev with:
- Free tier for individual users
- Pro tier ($8/month) for persistent cloud storage
- Team tier ($12/user/month) for collaboration
- Total infrastructure cost <$50/month initially

---

## Success Criteria

- [ ] memorygraph.dev website live and fast (<2s load time)
- [ ] User authentication working (email + OAuth)
- [ ] API endpoints deployed and accessible
- [ ] Free tier available (SQLite or limited Turso)
- [ ] Paid tiers configured with Stripe
- [ ] Total monthly cost <$50 for 0-1000 users
- [ ] 99.5%+ uptime target

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     memorygraph.dev                         │
│                   (Cloudflare Pages)                        │
│                        FREE                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 API Gateway + Auth                          │
│              (Cloud Run - serverless)                       │
│              $0.40 per 1M requests                          │
└──────┬──────────────────────────┬───────────────────────────┘
       │                          │
       ▼                          ▼
┌──────────────┐          ┌──────────────────┐
│   Free Tier  │          │    Paid Tiers    │
│    Storage   │          │     Storage      │
│    (Turso)   │          │  (PlanetScale)   │
│     FREE     │          │   $29/month      │
│  3 DBs/user  │          │   or Supabase    │
│              │          │   FREE tier      │
└──────────────┘          └──────────────────┘
```

**Cost Breakdown (Monthly)**:
- Cloudflare Pages: $0 (unlimited bandwidth, static hosting)
- Cloud Run: ~$5-10 (pay per request, 1M free requests)
- Turso Free: $0 (3 databases, 500MB each)
- PlanetScale or Supabase: $0-29 (free tier → paid as needed)
- Domain: $1/month (amortized)
- **Total: $6-40/month**

---

## Section 1: Domain and DNS

### 1.1 Domain Setup

**Tasks**:
- [ ] Register memorygraph.dev (if not done)
- [ ] Transfer DNS to Cloudflare (for free CDN + SSL)
- [ ] Configure Cloudflare DNS records
- [ ] Enable DNSSEC
- [ ] Set up email forwarding (Cloudflare Email Routing - FREE)

**Files**: No code, DNS configuration only

### 1.2 SSL Certificates

**Tasks**:
- [ ] Enable Cloudflare Universal SSL (FREE, automatic)
- [ ] Set SSL mode to "Full (strict)"
- [ ] Enable Always Use HTTPS
- [ ] Enable HSTS (HTTP Strict Transport Security)

---

## Section 2: Static Website (Cloudflare Pages)

### 2.1 Website Deployment

**Framework**: Astro (fast, static, great DX)
**Hosting**: Cloudflare Pages (FREE)

**File Structure**:
```
website/
├── src/
│   ├── pages/
│   │   ├── index.astro           # Landing page
│   │   ├── docs/                 # Documentation
│   │   ├── pricing.astro         # Pricing page
│   │   └── login.astro           # Login page
│   ├── components/
│   └── layouts/
├── public/
├── package.json
└── astro.config.mjs
```

**Tasks**:
- [ ] Create `/Users/gregorydickson/claude-code-memory/website/` directory
- [ ] Initialize Astro project: `npm create astro@latest`
- [ ] Set up Tailwind CSS for styling
- [ ] Create landing page (see 7-WEBSITE-WORKPLAN for design)
- [ ] Create pricing page
- [ ] Create docs integration (link to existing docs)
- [ ] Build for production
- [ ] Deploy to Cloudflare Pages

### 2.2 Cloudflare Pages Configuration

**File**: `website/wrangler.toml` (or Cloudflare dashboard config)

```toml
name = "memorygraph"
type = "javascript"

[site]
bucket = "./dist"

[env.production]
name = "memorygraph"
route = "memorygraph.dev/*"
```

**Tasks**:
- [ ] Connect GitHub repo to Cloudflare Pages
- [ ] Configure build command: `npm run build`
- [ ] Set publish directory: `dist/`
- [ ] Enable automatic deployments on push to main
- [ ] Test deployment

**Cost**: $0/month (unlimited bandwidth on free tier)

---

## Section 3: Authentication (Supabase Auth)

**Choice**: Supabase Auth (FREE tier, 50,000 MAU)
**Alternative**: Clerk ($25/month for 10k users) - only if Supabase limits hit

### 3.1 Supabase Setup

**Tasks**:
- [ ] Create Supabase account
- [ ] Create new project: `memorygraph-prod`
- [ ] Enable email + password authentication
- [ ] Enable OAuth providers (GitHub, Google)
- [ ] Configure JWT secret
- [ ] Set up email templates (welcome, password reset)
- [ ] Configure redirect URLs (memorygraph.dev/auth/callback)

**Cost**: $0/month (free tier includes 50,000 monthly active users)

### 3.2 Auth Backend Implementation

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/auth.py`

```python
"""
Authentication using Supabase Auth.
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_jwt(token: str) -> dict:
    """Verify Supabase JWT token."""
    user = supabase.auth.get_user(token)
    return user

def create_api_key(user_id: str) -> str:
    """Generate API key for user."""
    # Generate secure random key
    # Store in database with user_id
    pass
```

**Tasks**:
- [ ] Create `src/memorygraph_cloud/` package
- [ ] Implement JWT verification
- [ ] Implement API key generation
- [ ] Implement API key validation middleware
- [ ] Add rate limiting per API key
- [ ] Add tests for auth functions

### 3.3 Frontend Auth Integration

**File**: `website/src/lib/auth.ts`

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.PUBLIC_SUPABASE_URL,
  import.meta.env.PUBLIC_SUPABASE_ANON_KEY
)

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

export async function signUp(email: string, password: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })
  return { data, error }
}

export async function signOut() {
  await supabase.auth.signOut()
}

export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}
```

**Tasks**:
- [ ] Create auth utility module
- [ ] Implement sign in/up/out functions
- [ ] Create login page UI
- [ ] Create signup page UI
- [ ] Add "forgot password" flow
- [ ] Test OAuth flows (GitHub, Google)

---

## Section 4: API Backend (Cloud Run)

**Choice**: Google Cloud Run (serverless, pay-per-request)
**Alternative**: Cloudflare Workers (more limited, but cheaper)

### 4.1 API Service Setup

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/api.py`

```python
"""
FastAPI service for memorygraph.dev API.
Deployed on Cloud Run (serverless).
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .auth import verify_jwt
from .storage import get_user_backend

app = FastAPI(title="MemoryGraph Cloud API")

# CORS for website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://memorygraph.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/memories")
async def create_memory(
    memory: dict,
    user_id: str = Depends(get_current_user)
):
    backend = get_user_backend(user_id)
    result = backend.create_memory(**memory)
    return result

@app.get("/api/v1/memories")
async def list_memories(
    user_id: str = Depends(get_current_user)
):
    backend = get_user_backend(user_id)
    memories = backend.search_memories()
    return memories
```

**Tasks**:
- [ ] Create FastAPI application
- [ ] Implement authentication middleware
- [ ] Implement memory CRUD endpoints
- [ ] Implement search endpoint
- [ ] Implement relationship endpoints
- [ ] Add request validation (Pydantic models)
- [ ] Add error handling
- [ ] Add logging (structured JSON logs)

### 4.2 Dockerfile for Cloud Run

**File**: `/Users/gregorydickson/claude-code-memory/Dockerfile.cloud`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy application
COPY src/ ./src/

# Run as non-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run expects PORT env var
ENV PORT 8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

CMD ["uvicorn", "memorygraph_cloud.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Tasks**:
- [ ] Create Dockerfile optimized for Cloud Run
- [ ] Minimize image size (multi-stage build if needed)
- [ ] Add health check endpoint
- [ ] Test locally: `docker build -f Dockerfile.cloud .`
- [ ] Test locally: `docker run -p 8080:8080 <image>`

### 4.3 Deploy to Cloud Run

**Tasks**:
- [ ] Create Google Cloud project: `memorygraph-prod`
- [ ] Enable Cloud Run API
- [ ] Enable Artifact Registry (container registry)
- [ ] Build and push image:
  ```bash
  gcloud builds submit --tag gcr.io/memorygraph-prod/api
  ```
- [ ] Deploy to Cloud Run:
  ```bash
  gcloud run deploy memorygraph-api \
    --image gcr.io/memorygraph-prod/api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60s
  ```
- [ ] Configure custom domain: api.memorygraph.dev
- [ ] Set environment variables (SUPABASE_URL, etc.)

**Cost**: ~$5-10/month (1M free requests, then $0.40 per 1M)
- Min instances = 0 (scale to zero when idle = $0)
- Cold starts ~1-2 seconds (acceptable for API)

---

## Section 5: Storage Backend

### 5.1 Free Tier: Turso (SQLite Cloud)

**Why Turso**:
- Free tier: 3 databases per user, 500MB each
- SQLite compatibility (reuse existing backend)
- Low latency (edge deployment)
- No cold starts

**Tasks**:
- [ ] Verify Turso backend works (from Workplan 8)
- [ ] Create free tier provisioning logic
- [ ] Implement database creation per user
- [ ] Add database limits (500MB, rate limits)
- [ ] Monitor usage per user

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/storage.py`

```python
def provision_free_tier(user_id: str) -> dict:
    """
    Provision Turso database for free tier user.
    Returns connection details.
    """
    # Create Turso database via API
    db_name = f"memorygraph-{user_id}"
    turso_client.create_database(db_name)

    # Get connection details
    url = f"libsql://{db_name}.turso.io"
    token = turso_client.create_token(db_name)

    return {"url": url, "token": token}
```

**Cost**: $0/month (free tier for first 3 databases per user)

### 5.2 Paid Tiers: PlanetScale or Supabase PostgreSQL

**Option A: Supabase PostgreSQL** (RECOMMENDED)
- Free tier: 500MB database, 2GB bandwidth
- Paid: $25/month for 8GB database, 50GB bandwidth
- Already using Supabase for auth (simplify stack)

**Option B: PlanetScale**
- Free tier: 1 database, 5GB storage, 1 billion row reads
- Paid: $29/month for 3 databases, 10GB storage
- MySQL-compatible, excellent DX

**Recommendation**: Start with Supabase PostgreSQL (reuse auth infrastructure)

**Tasks**:
- [ ] Set up Supabase PostgreSQL for paid tiers
- [ ] Create PostgreSQL backend (adapt from existing or create new)
- [ ] Implement automatic provisioning for paid users
- [ ] Add migration path: Turso (free) → PostgreSQL (paid)
- [ ] Test backend with PostgreSQL

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph/backends/postgres_backend.py`

```python
"""
PostgreSQL backend for paid tiers.
"""
import psycopg2
from .base import Backend

class PostgresBackend(Backend):
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self._init_schema()

    def _init_schema(self):
        # Reuse SQLite schema with PostgreSQL types
        pass
```

**Cost**:
- Free tier: $0 (Supabase free tier)
- Paid tiers: $25-29/month (when users exceed free tier)

---

## Section 6: Payment Processing (Stripe)

### 6.1 Stripe Setup

**Tasks**:
- [ ] Create Stripe account
- [ ] Set up products:
  - Free tier (no charge)
  - Pro tier: $8/month
  - Team tier: $12/user/month
- [ ] Create price IDs for each tier
- [ ] Enable Stripe Checkout
- [ ] Set up webhooks (payment success, subscription changes)
- [ ] Test with Stripe test mode

### 6.2 Stripe Integration

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/billing.py`

```python
"""
Stripe billing integration.
"""
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(user_id: str, price_id: str) -> str:
    """Create Stripe checkout session."""
    session = stripe.checkout.Session.create(
        customer_email=user_email,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url='https://memorygraph.dev/success',
        cancel_url='https://memorygraph.dev/pricing',
        metadata={'user_id': user_id}
    )
    return session.url

def handle_webhook(payload: bytes, sig_header: str):
    """Handle Stripe webhook events."""
    event = stripe.Webhook.construct_event(
        payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
    )

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        # Upgrade user to paid tier
        provision_paid_tier(user_id)

    elif event['type'] == 'customer.subscription.deleted':
        # Downgrade user to free tier
        pass
```

**Tasks**:
- [ ] Implement checkout session creation
- [ ] Implement webhook handler
- [ ] Add webhook endpoint: `/api/v1/webhooks/stripe`
- [ ] Test checkout flow end-to-end
- [ ] Implement subscription management (upgrade/downgrade)

**Cost**: Stripe fees: 2.9% + $0.30 per transaction
- $8 subscription = $0.53 fee = $7.47 net

---

## Section 7: User Dashboard

### 7.1 Dashboard Pages

**File**: `website/src/pages/dashboard/index.astro`

**Pages**:
- `/dashboard` - Overview (usage stats, recent memories)
- `/dashboard/api-keys` - API key management
- `/dashboard/usage` - Usage metrics
- `/dashboard/settings` - Account settings
- `/dashboard/billing` - Subscription management

**Tasks**:
- [ ] Create dashboard layout component
- [ ] Implement API key display (masked)
- [ ] Implement API key regeneration
- [ ] Show usage metrics (API calls, storage used)
- [ ] Show subscription status
- [ ] Add "Upgrade" CTA for free users
- [ ] Add "Manage subscription" link (Stripe portal)

### 7.2 Dashboard API Endpoints

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/api.py`

**Endpoints**:
```python
@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(user_id: str = Depends(get_current_user)):
    """Get user's usage statistics."""
    return {
        "memory_count": ...,
        "api_calls_this_month": ...,
        "storage_used_mb": ...,
        "subscription_tier": "free|pro|team"
    }

@app.post("/api/v1/api-keys")
async def create_api_key(user_id: str = Depends(get_current_user)):
    """Generate new API key for user."""
    key = generate_api_key(user_id)
    return {"api_key": key}

@app.delete("/api/v1/api-keys/{key_id}")
async def revoke_api_key(key_id: str, user_id: str = Depends(get_current_user)):
    """Revoke an API key."""
    revoke_key(key_id, user_id)
    return {"status": "revoked"}
```

**Tasks**:
- [ ] Implement dashboard stats endpoint
- [ ] Implement API key CRUD endpoints
- [ ] Add usage tracking (count API calls)
- [ ] Store usage in database (daily aggregates)
- [ ] Implement rate limiting by tier

---

## Section 8: Rate Limiting and Quotas

### 8.1 Rate Limits by Tier

**Limits**:
- **Free**: 1000 API calls/day, 100 memories, 500MB storage
- **Pro**: 100,000 API calls/day, 10,000 memories, 5GB storage
- **Team**: 1M API calls/day, unlimited memories, 50GB storage

**Implementation**:

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/rate_limit.py`

```python
"""
Rate limiting using Redis (Upstash free tier).
"""
import redis
import os

redis_client = redis.from_url(os.getenv("UPSTASH_REDIS_URL"))

def check_rate_limit(user_id: str, tier: str) -> bool:
    """Check if user has exceeded rate limit."""
    key = f"rate:{user_id}:{date.today()}"
    count = redis_client.incr(key)
    redis_client.expire(key, 86400)  # 24 hours

    limits = {
        "free": 1000,
        "pro": 100000,
        "team": 1000000
    }

    return count <= limits[tier]
```

**Tasks**:
- [ ] Set up Upstash Redis (free tier: 10k commands/day)
- [ ] Implement rate limiting middleware
- [ ] Return 429 Too Many Requests when limit exceeded
- [ ] Add rate limit headers (X-RateLimit-Remaining, etc.)
- [ ] Test rate limiting

**Cost**: $0/month (Upstash free tier sufficient for initial scale)

### 8.2 Storage Quotas

**Tasks**:
- [ ] Track storage per user
- [ ] Block new memories when quota exceeded
- [ ] Show storage usage in dashboard
- [ ] Send email when approaching quota
- [ ] Implement quota upgrade flow

---

## Section 9: Monitoring and Logging

### 9.1 Monitoring Setup

**Choice**: Google Cloud Monitoring (included with Cloud Run)
**Alternative**: Uptime Robot (free, external monitoring)

**Tasks**:
- [ ] Enable Cloud Run metrics
- [ ] Set up uptime monitoring (health check)
- [ ] Set up error rate alerts (>5% errors)
- [ ] Set up latency alerts (p95 >500ms)
- [ ] Create dashboard in Cloud Console

**Cost**: Included with Cloud Run (no extra cost)

### 9.2 Logging

**Tasks**:
- [ ] Use structured logging (JSON format)
- [ ] Log all API requests (user_id, endpoint, status, latency)
- [ ] Log errors with stack traces
- [ ] Set log retention: 30 days
- [ ] Create log-based metrics for business KPIs

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/logging.py`

```python
import logging
import json

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        return json.dumps(log_data)
```

### 9.3 Error Tracking

**Choice**: Sentry (free tier: 5k errors/month)

**Tasks**:
- [ ] Create Sentry account
- [ ] Add Sentry SDK to API
- [ ] Configure error sampling (100% for now)
- [ ] Set up error alerts (email)
- [ ] Test error reporting

**Cost**: $0/month (free tier)

---

## Section 10: CI/CD Pipeline

### 10.1 GitHub Actions for Website

**File**: `.github/workflows/deploy-website.yml`

```yaml
name: Deploy Website

on:
  push:
    branches: [main]
    paths:
      - 'website/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd website && npm ci
      - name: Build
        run: cd website && npm run build
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: memorygraph
          directory: website/dist
```

**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Add Cloudflare API token to secrets
- [ ] Test deployment on push
- [ ] Add build caching for speed

### 10.2 GitHub Actions for API

**File**: `.github/workflows/deploy-api.yml`

```yaml
name: Deploy API

on:
  push:
    branches: [main]
    paths:
      - 'src/memorygraph_cloud/**'
      - 'Dockerfile.cloud'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - name: Build and push
        run: |
          gcloud builds submit --tag gcr.io/memorygraph-prod/api
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy memorygraph-api \
            --image gcr.io/memorygraph-prod/api \
            --region us-central1
```

**Tasks**:
- [ ] Create GCP service account for CI/CD
- [ ] Add service account key to GitHub secrets
- [ ] Test deployment pipeline
- [ ] Add rollback capability

---

## Section 11: Security Hardening

### 11.1 API Security

**Tasks**:
- [ ] Add rate limiting (implemented in Section 8)
- [ ] Validate all inputs (Pydantic models)
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Implement CORS properly (whitelist only memorygraph.dev)
- [ ] Add CSRF protection for state-changing operations
- [ ] Use HTTPS only (enforce in Cloudflare)
- [ ] Set security headers (CSP, X-Frame-Options, etc.)

### 11.2 Secret Management

**Tasks**:
- [ ] Store secrets in Google Secret Manager
- [ ] Never commit secrets to git
- [ ] Rotate API keys regularly (document process)
- [ ] Use environment variables for all credentials
- [ ] Audit access to secrets

### 11.3 Database Security

**Tasks**:
- [ ] Use least-privilege database users
- [ ] Encrypt data at rest (enabled by default on Supabase/PlanetScale)
- [ ] Encrypt data in transit (TLS required)
- [ ] Regular backups (daily, 30-day retention)
- [ ] Test backup restoration

---

## Section 12: Documentation

### 12.1 Cloud API Documentation

**File**: `/Users/gregorydickson/claude-code-memory/docs/cloud-api.md`

**Content**:
```markdown
# MemoryGraph Cloud API

## Authentication
All requests require an API key:
```
Authorization: Bearer <your-api-key>
```

## Endpoints

### Create Memory
`POST /api/v1/memories`

### Search Memories
`GET /api/v1/memories?query=...`

[Document all endpoints with examples]
```

**Tasks**:
- [ ] Document all API endpoints
- [ ] Include request/response examples
- [ ] Add error codes and meanings
- [ ] Document rate limits
- [ ] Add quickstart guide

### 12.2 Getting Started Guide

**File**: `/Users/gregorydickson/claude-code-memory/docs/guides/cloud-setup.md`

**Tasks**:
- [ ] Write signup flow documentation
- [ ] Document API key generation
- [ ] Show how to configure MCP client for cloud
- [ ] Document migration from local to cloud
- [ ] Add troubleshooting section

### 12.3 Update Main Docs

**Tasks**:
- [ ] Add "Cloud Hosting" section to README
- [ ] Link to pricing page
- [ ] Add cloud setup to quickstart
- [ ] Update architecture diagrams

---

## Section 13: Testing

### 13.1 API Integration Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/cloud/test_api.py`

**Tests**:
- [ ] Test authentication (valid/invalid tokens)
- [ ] Test CRUD operations for memories
- [ ] Test rate limiting
- [ ] Test quota enforcement
- [ ] Test error handling

**Tasks**:
- [ ] Create cloud test suite
- [ ] Use pytest fixtures for test data
- [ ] Mock Stripe webhooks
- [ ] Test against staging environment

### 13.2 Load Testing

**Tool**: Locust or k6 (both free)

**Tasks**:
- [ ] Create load test scenarios
- [ ] Test with 100 concurrent users
- [ ] Measure p95 latency under load
- [ ] Identify bottlenecks
- [ ] Document performance characteristics

### 13.3 End-to-End Tests

**Tasks**:
- [ ] Test full user journey: signup → create memory → query
- [ ] Test upgrade flow: free → pro
- [ ] Test payment flow (Stripe test mode)
- [ ] Test API key generation and usage
- [ ] Run E2E tests in CI

---

## Section 14: Launch Preparation

### 14.1 Pre-Launch Checklist

**Infrastructure**:
- [ ] All services deployed and healthy
- [ ] DNS configured correctly
- [ ] SSL certificates active
- [ ] Monitoring and alerts set up
- [ ] Backups configured

**Security**:
- [ ] Security headers configured
- [ ] Rate limiting active
- [ ] Secrets stored securely
- [ ] GDPR compliance reviewed

**Product**:
- [ ] Free tier works end-to-end
- [ ] Paid tiers work end-to-end
- [ ] Documentation complete
- [ ] Pricing page live
- [ ] Terms of Service and Privacy Policy published

### 14.2 Soft Launch

**Tasks**:
- [ ] Launch to small group (10-20 beta users)
- [ ] Collect feedback
- [ ] Fix critical issues
- [ ] Monitor infrastructure costs
- [ ] Optimize based on usage patterns

### 14.3 Public Launch

**Tasks**:
- [ ] Announce on HN, Reddit, Twitter
- [ ] Submit to MCP servers list
- [ ] Update all documentation
- [ ] Monitor for issues
- [ ] Prepare for increased traffic

---

## Acceptance Criteria Summary

### Infrastructure
- [ ] memorygraph.dev resolves correctly
- [ ] Website loads in <2 seconds
- [ ] API responds in <200ms p95
- [ ] 99.5%+ uptime

### Features
- [ ] User signup and login working
- [ ] API key generation working
- [ ] Memory CRUD operations working
- [ ] Free tier provisioning automatic
- [ ] Paid tier upgrades working

### Cost
- [ ] Monthly cost <$50 for 0-1000 users
- [ ] All free tiers utilized where possible
- [ ] No fixed compute costs (serverless only)

### Documentation
- [ ] Cloud API documented
- [ ] Setup guide published
- [ ] Pricing page live
- [ ] Terms of Service and Privacy Policy published

---

## Monthly Cost Breakdown (Detailed)

| Service | Free Tier | Paid Tier | Expected Cost (0-1k users) |
|---------|-----------|-----------|---------------------------|
| Domain | N/A | $12/year | $1/month |
| Cloudflare Pages | Unlimited | N/A | $0 |
| Cloudflare DNS | Unlimited | N/A | $0 |
| Google Cloud Run | 1M requests | $0.40/1M | $5-10 (estimate 10-25M requests) |
| Supabase Auth | 50k MAU | $25/month | $0 (under limit) |
| Supabase DB | 500MB | $25/month | $0-25 (as needed) |
| Turso | 3 DBs/user | N/A | $0 (free for all free tier users) |
| Upstash Redis | 10k commands/day | $0.20/10k | $0 (under limit initially) |
| Stripe | N/A | 2.9% + $0.30 | $0 (pass-through) |
| Sentry | 5k errors/month | $26/month | $0 (under limit) |
| **TOTAL** | | | **$6-36/month** |

**Scaling costs**:
- 1k users: ~$30/month
- 5k users: ~$80/month (Supabase paid tier kicks in)
- 10k users: ~$150/month
- Revenue at 10k users (10% conversion to $8 plan): $8,000/month
- **Margin**: ~98% at scale

---

## Notes for Coding Agent

**Critical Implementation Notes**:

1. **Always use free tiers first**:
   - Don't provision paid services until necessary
   - Monitor usage closely
   - Set up billing alerts

2. **Serverless everything**:
   - Cloud Run scales to zero (no idle costs)
   - No always-on servers
   - Pay only for actual usage

3. **Security cannot be an afterthought**:
   - Implement rate limiting from day one
   - Validate all inputs
   - Use parameterized queries
   - Enable HTTPS only

4. **Environment variables**:
   - Never hardcode credentials
   - Use `.env.example` for documentation
   - Store secrets in Secret Manager

5. **Test before deploying**:
   - Test locally with Docker
   - Test in staging environment
   - Run E2E tests in CI

---

## Dependencies

**External Services**:
- Cloudflare (DNS, Pages)
- Google Cloud (Cloud Run)
- Supabase (Auth, PostgreSQL)
- Turso (SQLite cloud)
- Stripe (payments)
- Upstash (Redis for rate limiting)
- Sentry (error tracking)

**Internal**:
- Existing backends (SQLite, PostgreSQL)
- MCP server code
- Documentation

---

## Estimated Timeline

| Section | Effort | Dependencies |
|---------|--------|--------------|
| Section 1: Domain/DNS | 1 hour | None |
| Section 2: Website | 4-6 hours | None |
| Section 3: Authentication | 3-4 hours | Website done |
| Section 4: API Backend | 4-6 hours | Auth done |
| Section 5: Storage | 2-3 hours | API done |
| Section 6: Payments | 2-3 hours | API done |
| Section 7: Dashboard | 3-4 hours | API + payments done |
| Section 8: Rate Limiting | 2 hours | API done |
| Section 9: Monitoring | 2 hours | API deployed |
| Section 10: CI/CD | 2-3 hours | All services ready |
| Section 11: Security | 2-3 hours | All services ready |
| Section 12: Documentation | 3-4 hours | All done |
| Section 13: Testing | 3-4 hours | All done |
| Section 14: Launch | 2-3 hours | All tested |
| **Total** | **35-50 hours** | Sequential + parallel |

---

## References

- **7-WEBSITE-WORKPLAN.md**: Website design (merge into workplan 17)
- **PRODUCT_ROADMAP.md**: Phase 3 (Cloud Launch)
- **Workplan 15**: Authentication details
- **Cloudflare Pages Docs**: https://developers.cloudflare.com/pages/
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Supabase Docs**: https://supabase.com/docs

---

**Last Updated**: 2025-12-05
**Status**: NOT STARTED
**Next Step**: Register domain, set up DNS
