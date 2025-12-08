# Workplan 15: Authentication & API Keys (v1.0.0)

> ## ❌ DEPRECATED (2025-12-06)
>
> **This workplan has been superseded by the memorygraph.dev repository.**
>
> ### What Happened
> - Auth service was implemented in `/Users/gregorydickson/memorygraph.dev/`
> - Different architecture chosen: FastAPI + PostgreSQL + JWT (not Supabase)
> - Auth service already deployed to Cloud Run
>
> ### Where to Find the Active Work
> - **Replacement**: `memorygraph.dev/docs/planning/2-WORKPLAN-auth-service.md`
> - **Live Service**: https://auth-service-793446666872.us-central1.run.app
> - **Status**: PoC Complete (95 tests, 80%+ coverage)
>
> ### Do NOT use this workplan for implementation.
>
> ---

**Version Target**: v1.0.0
**Priority**: ~~HIGH~~ DEPRECATED
**Prerequisites**:
- ~~Workplan 14 Section 3 (Auth infrastructure) complete~~
- See memorygraph.dev workplans instead
**Estimated Effort**: ~~8-12 hours~~ N/A (already implemented elsewhere)
**Status**: ❌ DEPRECATED

---

## Overview

~~Implement comprehensive authentication and API key management system for memorygraph.dev. Support email/password, OAuth (GitHub, Google), and long-lived API keys for MCP clients.~~

**This work was completed in the memorygraph.dev repository with a different architecture.**

**Security First**: Follow OWASP guidelines, use proven libraries, implement rate limiting, enable 2FA.

---

## Goal

Secure authentication system that supports:
- Email/password signup and login
- OAuth (GitHub, Google)
- API key generation and management
- Rate limiting and abuse prevention
- 2FA (optional, future enhancement)

---

## Success Criteria

- [ ] Users can sign up with email/password
- [ ] Users can sign in with GitHub/Google OAuth
- [ ] API keys can be generated and revoked
- [ ] API keys work with MCP clients
- [ ] Rate limiting prevents abuse
- [ ] Password reset flow works
- [ ] Email verification works
- [ ] 15+ tests passing for auth

---

## Section 1: User Authentication Models

### 1.1 Database Schema

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/models/user.py`

```python
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"

class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # UUID
    email = Column(String, unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)

    # Managed by Supabase Auth
    supabase_id = Column(String, unique=True, nullable=False, index=True)

    # Subscription
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)


class APIKey(Base):
    """API key model for MCP clients."""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, nullable=False, index=True)  # Foreign key to users.id

    name = Column(String, nullable=False)  # User-provided name (e.g., "My MacBook")
    key_hash = Column(String, nullable=False, unique=True)  # SHA256 hash of key
    key_prefix = Column(String, nullable=False)  # First 8 chars for display

    # Permissions (future: scope API keys)
    scopes = Column(String, default="read,write")  # Comma-separated

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)

    # Lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    revoked_at = Column(DateTime, nullable=True)
```

**Tasks**:
- [ ] Create models/user.py with SQLAlchemy models
- [ ] Add Alembic migration for user and api_keys tables
- [ ] Create indexes for performance (email, supabase_id, key_hash)
- [ ] Add unique constraints where needed

### 1.2 User CRUD Operations

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/db/users.py`

```python
from sqlalchemy.orm import Session
from .models import User, SubscriptionTier
from typing import Optional

def create_user(
    db: Session,
    email: str,
    supabase_id: str,
    tier: SubscriptionTier = SubscriptionTier.FREE
) -> User:
    """Create a new user."""
    user = User(
        id=generate_uuid(),
        email=email,
        supabase_id=supabase_id,
        subscription_tier=tier
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

def get_user_by_supabase_id(db: Session, supabase_id: str) -> Optional[User]:
    """Get user by Supabase ID."""
    return db.query(User).filter(User.supabase_id == supabase_id, User.deleted_at.is_(None)).first()

def update_last_login(db: Session, user_id: str):
    """Update last login timestamp."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_login_at = datetime.utcnow()
        db.commit()
```

**Tasks**:
- [ ] Implement user CRUD operations
- [ ] Add proper error handling
- [ ] Add input validation
- [ ] Add tests for all operations

---

## Section 2: Supabase Authentication Integration

### 2.1 Auth Service

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/auth/supabase.py`

```python
"""
Supabase authentication integration.
"""
import os
from supabase import create_client, Client
from typing import Optional, Dict

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Client for public operations (signup, login)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Admin client for user management
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def sign_up(email: str, password: str) -> Dict:
    """Sign up a new user."""
    response = supabase.auth.sign_up({
        "email": email,
        "password": password,
    })

    if response.user:
        # Create user in our database
        create_user_from_supabase(response.user)

    return response


def sign_in(email: str, password: str) -> Dict:
    """Sign in existing user."""
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })

    if response.user:
        update_last_login(response.user.id)

    return response


def sign_in_with_oauth(provider: str, redirect_url: str) -> Dict:
    """
    Initiate OAuth flow.

    Args:
        provider: "github" or "google"
        redirect_url: Where to redirect after auth
    """
    response = supabase.auth.sign_in_with_oauth({
        "provider": provider,
        "options": {
            "redirect_to": redirect_url
        }
    })
    return response


def verify_jwt(token: str) -> Optional[Dict]:
    """
    Verify JWT token from request headers.

    Returns:
        User data if valid, None if invalid
    """
    try:
        user = supabase.auth.get_user(token)
        return user
    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
        return None


def send_password_reset(email: str) -> Dict:
    """Send password reset email."""
    response = supabase.auth.reset_password_for_email(email)
    return response


def update_password(token: str, new_password: str) -> Dict:
    """Update user password (from reset flow)."""
    response = supabase.auth.update_user(token, {
        "password": new_password
    })
    return response
```

**Tasks**:
- [ ] Implement Supabase auth wrapper functions
- [ ] Add proper error handling and logging
- [ ] Implement JWT verification middleware
- [ ] Test all auth flows (signup, login, password reset)
- [ ] Handle OAuth callback

### 2.2 FastAPI Auth Middleware

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/auth/middleware.py`

```python
"""
FastAPI authentication middleware.
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .supabase import verify_jwt
from .api_keys import verify_api_key

security = HTTPBearer()


async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency for routes that require authentication.

    Accepts either:
    - JWT token (from Supabase Auth)
    - API key (for MCP clients)

    Returns:
        user_id if authenticated
    """
    token = credentials.credentials

    # Try JWT first
    user = verify_jwt(token)
    if user:
        return user.id

    # Try API key
    api_key_user = verify_api_key(token)
    if api_key_user:
        return api_key_user.user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(user_id: str = Depends(get_current_user)) -> User:
    """
    Get the full user object for authenticated requests.
    """
    user = get_user_by_id(db, user_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Tasks**:
- [ ] Implement auth middleware
- [ ] Support both JWT and API key auth
- [ ] Add dependency injection for protected routes
- [ ] Add tests for middleware

---

## Section 3: API Key Management

### 3.1 API Key Generation

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/auth/api_keys.py`

```python
"""
API key generation and management.
"""
import secrets
import hashlib
from sqlalchemy.orm import Session
from .models import APIKey
from typing import Optional

API_KEY_LENGTH = 32  # bytes (64 hex chars)
PREFIX_LENGTH = 8    # chars to show in UI


def generate_api_key(db: Session, user_id: str, name: str) -> tuple[str, APIKey]:
    """
    Generate a new API key for user.

    Returns:
        (plaintext_key, api_key_record)

    Important: The plaintext key is only returned once!
    """
    # Generate secure random key
    plaintext_key = secrets.token_urlsafe(API_KEY_LENGTH)

    # Hash for storage
    key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()

    # Extract prefix for display
    key_prefix = plaintext_key[:PREFIX_LENGTH]

    # Create database record
    api_key = APIKey(
        id=generate_uuid(),
        user_id=user_id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes="read,write"  # Default scopes
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return plaintext_key, api_key


def verify_api_key(db: Session, plaintext_key: str) -> Optional[APIKey]:
    """
    Verify API key and return the key record if valid.
    """
    key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()

    api_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.revoked_at.is_(None)
    ).first()

    if api_key:
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None

        # Update usage tracking
        api_key.last_used_at = datetime.utcnow()
        api_key.usage_count += 1
        db.commit()

    return api_key


def revoke_api_key(db: Session, key_id: str, user_id: str):
    """
    Revoke an API key.
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == user_id
    ).first()

    if api_key:
        api_key.revoked_at = datetime.utcnow()
        db.commit()


def list_user_api_keys(db: Session, user_id: str) -> list[APIKey]:
    """
    List all API keys for a user (excluding revoked).
    """
    return db.query(APIKey).filter(
        APIKey.user_id == user_id,
        APIKey.revoked_at.is_(None)
    ).order_by(APIKey.created_at.desc()).all()
```

**Tasks**:
- [ ] Implement API key generation with cryptographically secure random
- [ ] Use SHA256 for hashing (keys never stored plaintext)
- [ ] Implement verification with timing-safe comparison
- [ ] Implement revocation
- [ ] Add usage tracking (last_used_at, usage_count)
- [ ] Add tests for all operations

### 3.2 API Key Endpoints

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/api/keys.py`

```python
"""
API endpoints for API key management.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..auth.middleware import get_current_active_user
from ..auth.api_keys import generate_api_key, revoke_api_key, list_user_api_keys

router = APIRouter(prefix="/api/v1/keys", tags=["api-keys"])


class CreateAPIKeyRequest(BaseModel):
    name: str  # User-friendly name like "MacBook Pro"


class CreateAPIKeyResponse(BaseModel):
    api_key: str  # Plaintext key (only shown once!)
    key_id: str
    name: str
    prefix: str
    created_at: str


@router.post("/", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user: User = Depends(get_current_active_user)
):
    """Generate a new API key."""
    plaintext_key, api_key_record = generate_api_key(
        db, user.id, request.name
    )

    return CreateAPIKeyResponse(
        api_key=plaintext_key,
        key_id=api_key_record.id,
        name=api_key_record.name,
        prefix=api_key_record.key_prefix,
        created_at=api_key_record.created_at.isoformat()
    )


@router.get("/")
async def list_api_keys(user: User = Depends(get_current_active_user)):
    """List user's API keys (excluding revoked)."""
    keys = list_user_api_keys(db, user.id)

    return {
        "api_keys": [
            {
                "key_id": k.id,
                "name": k.name,
                "prefix": k.key_prefix + "...",  # Show prefix only
                "created_at": k.created_at.isoformat(),
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "usage_count": k.usage_count
            }
            for k in keys
        ]
    }


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    user: User = Depends(get_current_active_user)
):
    """Revoke an API key."""
    revoke_api_key(db, key_id, user.id)
    return {"status": "revoked", "key_id": key_id}
```

**Tasks**:
- [ ] Implement API key CRUD endpoints
- [ ] Add rate limiting (5 key generations per hour)
- [ ] Validate key names (max length, allowed chars)
- [ ] Add tests for all endpoints
- [ ] Test with MCP client

---

## Section 4: Rate Limiting

### 4.1 Rate Limiter Implementation

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/auth/rate_limit.py`

```python
"""
Rate limiting using Redis (Upstash).
"""
import redis
import os
from datetime import date, datetime
from typing import Optional

redis_client = redis.from_url(
    os.getenv("UPSTASH_REDIS_URL"),
    decode_responses=True
)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, redis_client):
        self.redis = redis_client

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (user_id or API key)
            max_requests: Maximum requests in window
            window_seconds: Time window in seconds

        Returns:
            (allowed, remaining_requests)
        """
        current = datetime.utcnow()
        window_key = f"rate:{key}:{current.minute // (window_seconds // 60)}"

        # Increment counter
        count = self.redis.incr(window_key)

        # Set expiration on first request
        if count == 1:
            self.redis.expire(window_key, window_seconds)

        allowed = count <= max_requests
        remaining = max(0, max_requests - count)

        return allowed, remaining


# Rate limits by tier
RATE_LIMITS = {
    "free": {
        "requests_per_minute": 10,
        "requests_per_day": 1000
    },
    "pro": {
        "requests_per_minute": 100,
        "requests_per_day": 100000
    },
    "team": {
        "requests_per_minute": 1000,
        "requests_per_day": 1000000
    }
}


rate_limiter = RateLimiter(redis_client)


def check_user_rate_limit(user_id: str, tier: str) -> bool:
    """Check if user has exceeded rate limit."""
    limits = RATE_LIMITS[tier]

    # Per-minute check
    allowed_minute, remaining_minute = rate_limiter.check_rate_limit(
        f"{user_id}:minute",
        limits["requests_per_minute"],
        60
    )

    if not allowed_minute:
        return False

    # Per-day check
    allowed_day, remaining_day = rate_limiter.check_rate_limit(
        f"{user_id}:day",
        limits["requests_per_day"],
        86400
    )

    return allowed_day
```

**Tasks**:
- [ ] Implement token bucket rate limiter
- [ ] Use Redis for distributed rate limiting
- [ ] Implement per-minute and per-day limits
- [ ] Add rate limit headers to responses
- [ ] Test rate limiting under load

### 4.2 Rate Limiting Middleware

**File**: `/Users/gregorydickson/claude-code-memory/src/memorygraph_cloud/auth/middleware.py`

```python
async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for all API requests.
    """
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)

    # Get user from auth (JWT or API key)
    try:
        user = await get_current_active_user(request)
    except HTTPException:
        # Allow unauthenticated requests to auth endpoints
        if request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)
        raise

    # Check rate limit
    if not check_user_rate_limit(user.id, user.subscription_tier):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Upgrade your plan for higher limits.",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(RATE_LIMITS[user.subscription_tier]["requests_per_minute"]),
                "X-RateLimit-Remaining": "0"
            }
        )

    # Process request
    response = await call_next(request)

    # Add rate limit headers
    limits = RATE_LIMITS[user.subscription_tier]
    response.headers["X-RateLimit-Limit"] = str(limits["requests_per_minute"])
    # TODO: Add remaining count

    return response
```

**Tasks**:
- [ ] Add rate limiting middleware to FastAPI app
- [ ] Add rate limit headers to all responses
- [ ] Return 429 Too Many Requests when limit exceeded
- [ ] Test middleware

---

## Section 5: Password Security

### 5.1 Password Policy

**Enforced by Supabase Auth**, but document requirements:

**Policy**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Optional: Special characters

**Tasks**:
- [ ] Document password requirements
- [ ] Configure in Supabase dashboard
- [ ] Add client-side validation
- [ ] Add server-side validation (defense in depth)

### 5.2 Password Reset Flow

**File**: `website/src/pages/auth/reset-password.astro`

**Flow**:
1. User enters email on /auth/forgot-password
2. Backend calls Supabase `reset_password_for_email`
3. Supabase sends email with magic link
4. User clicks link → redirected to /auth/reset-password?token=...
5. User enters new password
6. Backend calls Supabase `update_password`

**Tasks**:
- [ ] Create forgot password page
- [ ] Create reset password page
- [ ] Implement email sending (via Supabase)
- [ ] Customize email templates in Supabase
- [ ] Test full flow

---

## Section 6: Email Verification

### 6.1 Verification Flow

**Flow** (managed by Supabase):
1. User signs up
2. Supabase sends verification email
3. User clicks link
4. Email marked as verified
5. Redirect to dashboard

**Tasks**:
- [ ] Enable email verification in Supabase
- [ ] Customize verification email template
- [ ] Set up redirect after verification
- [ ] Block unverified users from certain actions (optional)
- [ ] Test verification flow

### 6.2 Resend Verification Email

**Endpoint**:
```python
@router.post("/resend-verification")
async def resend_verification_email(user: User = Depends(get_current_active_user)):
    """Resend email verification."""
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    supabase.auth.resend_verification_email(user.email)
    return {"status": "sent"}
```

**Tasks**:
- [ ] Implement resend endpoint
- [ ] Add rate limiting (1 per 5 minutes)
- [ ] Add UI button on dashboard
- [ ] Test resend flow

---

## Section 7: OAuth Integration

### 7.1 GitHub OAuth

**Configuration** (in Supabase dashboard):
1. Create GitHub OAuth app
2. Set callback URL: `https://<supabase-project>.supabase.co/auth/v1/callback`
3. Add Client ID and Secret to Supabase

**Tasks**:
- [ ] Create GitHub OAuth app
- [ ] Configure in Supabase
- [ ] Add "Sign in with GitHub" button
- [ ] Test OAuth flow
- [ ] Handle new user creation from OAuth

### 7.2 Google OAuth

**Configuration**:
1. Create Google Cloud project
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Add to Supabase

**Tasks**:
- [ ] Create Google OAuth credentials
- [ ] Configure in Supabase
- [ ] Add "Sign in with Google" button
- [ ] Test OAuth flow
- [ ] Handle new user creation from OAuth

### 7.3 OAuth Callback Handling

**File**: `website/src/pages/auth/callback.astro`

```astro
---
// Handle OAuth callback
import { supabase } from '@/lib/auth'

const { data: { session }, error } = await supabase.auth.getSession()

if (error) {
  return Astro.redirect('/auth/error?message=' + encodeURIComponent(error.message))
}

if (session) {
  // Create user in our database if new
  // Redirect to dashboard
  return Astro.redirect('/dashboard')
}
---
```

**Tasks**:
- [ ] Create OAuth callback page
- [ ] Handle session creation
- [ ] Create user record if new OAuth user
- [ ] Redirect to appropriate page
- [ ] Handle errors gracefully

---

## Section 8: Testing

### 8.1 Unit Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/auth/test_api_keys.py`

**Tests**:
- [ ] Test API key generation
- [ ] Test API key verification
- [ ] Test API key revocation
- [ ] Test expired key rejection
- [ ] Test usage tracking

**File**: `/Users/gregorydickson/claude-code-memory/tests/auth/test_rate_limit.py`

**Tests**:
- [ ] Test rate limit enforcement
- [ ] Test rate limit headers
- [ ] Test tier-based limits
- [ ] Test rate limit reset

### 8.2 Integration Tests

**File**: `/Users/gregorydickson/claude-code-memory/tests/auth/test_auth_flow.py`

**Tests**:
- [ ] Test signup flow
- [ ] Test login flow
- [ ] Test password reset flow
- [ ] Test email verification flow
- [ ] Test OAuth flow (mocked)
- [ ] Test API key authentication

### 8.3 Security Tests

**Tests**:
- [ ] Test invalid JWT rejection
- [ ] Test expired API key rejection
- [ ] Test revoked API key rejection
- [ ] Test rate limit bypass attempts
- [ ] Test SQL injection in auth endpoints
- [ ] Test XSS in auth forms

---

## Section 9: Documentation

### 9.1 API Documentation

**File**: `/Users/gregorydickson/claude-code-memory/docs/cloud-api.md`

**Content**:
```markdown
# Authentication

## API Keys

Generate an API key from your dashboard:
1. Go to https://memorygraph.dev/dashboard/api-keys
2. Click "Generate New Key"
3. Give it a name (e.g., "MacBook Pro")
4. Copy the key (shown only once!)

## Using API Keys

Include in Authorization header:
```
Authorization: Bearer mgraph_...your-key...
```

## Rate Limits

| Tier | Per Minute | Per Day |
|------|------------|---------|
| Free | 10 | 1,000 |
| Pro | 100 | 100,000 |
| Team | 1,000 | 1,000,000 |
```

**Tasks**:
- [ ] Document authentication methods
- [ ] Document API key usage
- [ ] Document rate limits
- [ ] Add code examples for each language

### 9.2 User Guide

**File**: `/Users/gregorydickson/claude-code-memory/docs/guides/authentication.md`

**Content**:
- How to sign up
- How to generate API keys
- How to use API keys with MCP
- Troubleshooting auth issues

**Tasks**:
- [ ] Write user-facing authentication guide
- [ ] Include screenshots
- [ ] Add troubleshooting section

---

## Acceptance Criteria Summary

### Functional
- [ ] Email/password signup and login working
- [ ] OAuth (GitHub, Google) working
- [ ] API keys can be generated and used
- [ ] Password reset working
- [ ] Email verification working

### Security
- [ ] Passwords hashed (by Supabase)
- [ ] API keys hashed (SHA256)
- [ ] Rate limiting active
- [ ] JWT verification working
- [ ] No secrets in code or logs

### Testing
- [ ] 15+ tests passing
- [ ] Security tests passing
- [ ] Integration tests passing

### Documentation
- [ ] API documentation complete
- [ ] User guide complete
- [ ] Rate limits documented

---

## Notes for Coding Agent

**Security Critical**:

1. **Never store plaintext keys or passwords**
2. **Use timing-safe comparison for key verification**
3. **Rate limit all auth endpoints**
4. **Log auth failures for security monitoring**
5. **Use HTTPS only (enforce at load balancer)**

**Supabase Integration**:
- Supabase handles password hashing, JWT generation
- We store user records in our database for subscription/usage tracking
- Sync on every login (update last_login_at)

**API Key Format**:
- Use URL-safe base64 encoding
- Prefix keys with `mgraph_` for easy identification
- Never log full keys, only prefix

---

## Dependencies

**External**:
- Supabase Auth
- Upstash Redis (rate limiting)
- SMTP for emails (via Supabase)

**Internal**:
- User models
- Database migrations
- FastAPI application

---

## Estimated Timeline

| Section | Effort | Dependencies |
|---------|--------|--------------|
| Section 1: Models | 2 hours | None |
| Section 2: Supabase Integration | 2-3 hours | Models done |
| Section 3: API Keys | 2-3 hours | Models done |
| Section 4: Rate Limiting | 2 hours | Redis set up |
| Section 5: Password Security | 1 hour | Supabase done |
| Section 6: Email Verification | 1 hour | Supabase done |
| Section 7: OAuth | 2-3 hours | Supabase done |
| Section 8: Testing | 3-4 hours | All impl done |
| Section 9: Documentation | 2 hours | All done |
| **Total** | **17-23 hours** | Sequential + parallel |

---

## References

- **Workplan 14**: Cloud infrastructure (Section 3)
- **Supabase Auth Docs**: https://supabase.com/docs/guides/auth
- **OWASP Auth Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

---

**Last Updated**: 2025-12-05
**Status**: NOT STARTED
**Next Step**: Section 1 (Models)
