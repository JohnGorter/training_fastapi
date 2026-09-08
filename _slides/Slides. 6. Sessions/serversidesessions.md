# Serverside sessions

---
### Serverside sessions

Ok, so now we know how to implement client (Cookie based) sessions. 
But what if we want to store more data, more securely?

Lets implement serverside sessions!

---
### Benefits of inmem sessions

In-memory session management stores user session state directly in the Python process memory (RAM)
- sub-microsecond access speeds 
- no external infrastructure like Redis or database queries needed


---
### Considerations

We can store session information in memory, but take these considerations:
- We still need cookies to store the correctation token for the serverside sessions
- when implementing serverside memory sessions, we potentially create server affinity requirements
- we have to think about memory pressure, how long do we keep sessions alive in memory?

---
### Alternative consideration

We can also use a state server (like Redis) to store sessions for us
- no server affinity
- but slower
- persistent data

---
### Comparison

|Metric / Aspect|Pure In-Memory Sessions|Server-Side External Store (Redis/DB)|
|----|----|
|Lookup Latency|Nanosecond / Sub-microsecond (RAM lookup)|Sub-millisecond (Network I/O over socket)|
|Infrastructure Overhead|Zero (Built directly into Python standard library)|Requires managing external Redis or DB cluster|
|Multi-Worker Scaling|Isolated per process (Requires single-worker or sticky sessions)|Shared globally across all API worker instances|
|Persistence / Restarts|Volatile (Process restarts purge all active sessions)|Persistent (Sessions survive process restarts)|
|Memory Management|Requires explicit periodic TTL purging to prevent RAM leaks|Managed automatically via engine eviction (e.g., Redis TTL)|


---
### Basic Dictionary Session Storage 

A basic in-memory store maps a generated UUID session token to a session object and an absolute epoch timestamp

Real-World Use Case
- single-process internal dashboards, CLI admin panels, or lightweight single-instance microservices

Behavior
- stores session data directly in process memory. The browser holds only an opaque session token in an HttpOnly cookie

---
### Basic Dictionary Session Storage 
```
import time
import uuid
from fastapi import FastAPI, Response
from pydantic import BaseModel

app = FastAPI()

# Global in-memory dictionary: session_id -> (expiration_timestamp, session_data)
SESSION_STORE: dict[str, tuple[float, dict]] = {}

class LoginPayload(BaseModel):
    user_id: int
    role: str

@app.post("/session")
async def create_session(payload: LoginPayload, response: Response):
    session_id = str(uuid.uuid4())
    expires_at = time.time() + 3600  # 1-hour expiration
    
    # Store directly in process memory
    SESSION_STORE[session_id] = (expires_at, payload.model_dump())
    
    response.set_cookie(key="sid", value=session_id, httponly=True)
    return {"status": "session_created", "sid": session_id}
```

---
### Asynchronous Thread Safety (asyncio.Lock)

When multiple async requests modify or delete session keys simultaneously, wrapping storage mutations inside an asyncio.Lock context prevents race conditions

Real-World Use Case
- High-concurrency applications where concurrent background tasks or requests modify shared session state 

Behavior
- guarantees atomic dictionary reads, writes, and deletions across asynchronous event loop tasks


---
### Asynchronous Thread Safety (asyncio.Lock)

```
import asyncio
import time

class ThreadSafeSessionStore:
    def __init__(self):
        self._store: dict[str, tuple[float, dict]] = {}
        self._lock = asyncio.Lock()

    async def set(self, session_id: str, data: dict, ttl_seconds: int = 1800):
        expires_at = time.time() + ttl_seconds
        async with self._lock:
            self._store[session_id] = (expires_at, data)

    async def get(self, session_id: str) -> dict | None:
        async with self._lock:
            if session_id not in self._store:
                return None
            
            expires_at, data = self._store[session_id]
            if time.time() > expires_at:
                del self._store[session_id]  # Lazy eviction
                return None
            return data

session_store = ThreadSafeSessionStore()
```

---
### Automatic Background Memory Sweeper (TTL Purging)

To prevent expired sessions from permanently occupying RAM, a background task periodically scans the session store and unlinks stale entries

Real-World Use Case
- long-running web services that must manage RAM footprint over time without relying on an external database or Redis engine

Behavior
- a background asyncio task runs in a loop, acquiring the memory lock to purge expired keys at set intervals


---
### Automatic Background Memory Sweeper (TTL Purging)

```
import asyncio
import time

async def start_memory_sweeper(store: ThreadSafeSessionStore, interval_seconds: int = 300):
    """Background task purging expired keys every 5 minutes."""
    while True:
        await asyncio.sleep(interval_seconds)
        now = time.time()
        async with store._lock:
            expired_keys = [
                sid for sid, (expires_at, _) in store._store.items() 
                if now > expires_at
            ]
            for sid in expired_keys:
                del store._store[sid]
            if expired_keys:
                print(f"[MEMORY SWEEPER] Purged {len(expired_keys)} expired sessions.")
```


---
### Strongly Typed Session Dependency Injection (Depends)

Injecting an in-memory session dependency into route handlers validates incoming cookies, checks expiration times, and transforms raw state into typed Pydantic models

Real-World Use Case
- securing private API routes by injecting a pre-validated UserSession model into endpoint functions

Behavior
- intercepts incoming HTTP requests, extracts the session ID cookie, retrieves the in-memory object, and raises an HTTP 401 Unauthorized exception if the session token is missing or expired

---
### Strongly Typed Session Dependency Injection (Depends)

```
from typing import Annotated
from fastapi import FastAPI, Depends, Cookie, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

class UserSession(BaseModel):
    user_id: int
    email: str

async def get_current_session(
    sid: Annotated[str | None, Cookie()] = None
) -> UserSession:
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing session cookie"
        )
    
    session_data = await session_store.get(sid)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session invalid or expired"
        )
        
    return UserSession.model_validate(session_data)

@app.get("/api/v1/profile")
async def get_profile(user: Annotated[UserSession, Depends(get_current_session)]):
    return {"user_id": user.user_id, "email": user.email}
```

---
### Unified Enterprise In-Memory Session Architecture

This complete pattern demonstrates a self-contained, in-memory session engine built for single-instance or sticky-session deployments. It features Lifespan background memory sweeper management, Async thread safety via asyncio.Lock, Pydantic schema validation, Sliding expiration windows, and Hardened Cookie security

---
### Unified Enterprise In-Memory Session Architecture

```
import asyncio
from contextlib import asynccontextmanager
import time
from typing import Annotated
import uuid
from fastapi import FastAPI, Depends, Cookie, Request, Response, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict

# ---------------------------------------------------------------------
# 1. THREAD-SAFE IN-MEMORY SESSION ENGINE
# ---------------------------------------------------------------------
class UserSessionModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    email: EmailStr
    role: str

class InMemorySessionEngine:
    """Thread-safe, process-local session store with automatic TTL management."""
    def __init__(self):
        # Key: session_id -> Value: (expiration_epoch, UserSessionModel)
        self._store: dict[str, tuple[float, UserSessionModel]] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, session_data: UserSessionModel, ttl_seconds: int = 1800) -> str:
        session_id = str(uuid.uuid4())
        expires_at = time.time() + ttl_seconds
        async with self._lock:
            self._store[session_id] = (expires_at, session_data)
        return session_id

    async def get_session(self, session_id: str, sliding_ttl: int = 1800) -> UserSessionModel | None:
        async with self._lock:
            if session_id not in self._store:
                return None
            
            expires_at, session_data = self._store[session_id]
            now = time.time()
            
            if now > expires_at:
                del self._store[session_id]  # Lazy eviction
                return None

            # Sliding Expiration: Refresh TTL on active read
            self._store[session_id] = (now + sliding_ttl, session_data)
            return session_data

    async def delete_session(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._store:
                del self._store[session_id]
                return True
            return False

    async def purge_expired_sessions(self) -> int:
        """Sweeper method to evict expired tokens from memory."""
        now = time.time()
        async with self._lock:
            expired_ids = [
                sid for sid, (expires_at, _) in self._store.items() 
                if now > expires_at
            ]
            for sid in expired_ids:
                del self._store[sid]
            return len(expired_ids)

session_engine = InMemorySessionEngine()

# ---------------------------------------------------------------------
# 2. LIFESPAN MANAGEMENT & BACKGROUND SWEEPER
# ---------------------------------------------------------------------
async def background_memory_sweeper(engine: InMemorySessionEngine, interval_seconds: int = 60):
    """Background task running continuously to clean memory leaks."""
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            purged_count = await engine.purge_expired_sessions()
            if purged_count > 0:
                print(f"[MEMORY SWEEPER] Cleaned {purged_count} expired session(s) from RAM.")
    except asyncio.CancelledError:
        print("[MEMORY SWEEPER] Background task gracefully stopped.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch background memory sweeper
    sweeper_task = asyncio.create_task(background_memory_sweeper(session_engine, interval_seconds=60))
    yield
    # Shutdown: Cancel background task
    sweeper_task.cancel()
    await asyncio.gather(sweeper_task, return_exceptions=True)

app = FastAPI(title="Enterprise In-Memory Session Service", lifespan=lifespan)

# ---------------------------------------------------------------------
# 3. PYDANTIC SCHEMAS & DEPENDENCIES
# ---------------------------------------------------------------------
class LoginCredentials(BaseModel):
    email: EmailStr
    password: str

class ProfileResponse(BaseModel):
    user_id: int
    email: str
    role: str

async def get_active_session(
    sid: Annotated[str | None, Cookie()] = None
) -> UserSessionModel:
    """Dependency validating in-memory session token from client cookie."""
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Missing session token."
        )

    session_data = await session_engine.get_session(sid, sliding_ttl=1800)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or been revoked."
        )

    return session_data

# ---------------------------------------------------------------------
# 4. PATH OPERATIONS (Login, Session Inspection, Logout)
# ---------------------------------------------------------------------

@app.post("/api/v1/auth/login", status_code=status.HTTP_200_OK)
async def login(credentials: LoginCredentials, response: Response):
    # STEP 1: Verify Credentials (Simulated)
    if credentials.email != "admin@enterprise.io" or credentials.password != "SecretPass123!":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # STEP 2: Construct Immutable Session State Model
    session_data = UserSessionModel(
        user_id=10042,
        email=credentials.email,
        role="ADMINISTRATOR"
    )

    # STEP 3: Store in Thread-Safe In-Memory Engine with 30-Minute Expiration
    session_id = await session_engine.create_session(session_data, ttl_seconds=1800)

    # STEP 4: Set Hardened Security Cookie
    response.set_cookie(
        key="sid",
        value=session_id,
        max_age=1800,
        httponly=True,   # Mitigates XSS attack vectors
        samesite="lax",   # Mitigates CSRF attack vectors
        secure=False,     # Set to True in HTTPS production environments
        path="/"
    )

    return {"status": "SUCCESS", "user_id": session_data.user_id}

@app.get(
    "/api/v1/auth/me",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK
)
async def get_current_user_profile(
    session: Annotated[UserSessionModel, Depends(get_active_session)]
):
    # Route protected by dependency; returns active session state
    return ProfileResponse(
        user_id=session.user_id,
        email=session.email,
        role=session.role
    )

@app.post("/api/v1/auth/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    sid: Annotated[str | None, Cookie()] = None
):
    if sid:
        # STEP 1: Explicit In-Memory Revocation
        await session_engine.delete_session(sid)

    # STEP 2: Clear Client Cookie Storage
    response.delete_cookie(key="sid", path="/")
    
    return {"status": "SUCCESS", "message": "Session revoked from memory."}
```

---
### Execution Pipeline Explanation

- Application Lifespan & Background Sweeper Setup
    - when Uvicorn boots, lifespan starts background_memory_sweeper as a non-blocking asyncio.Task
    - every 60 seconds, it calls purge_expired_sessions(), acquiring _lock to delete stale entries and prevent RAM leaks
- Authentication & Session Storage (POST /login)
    - validates incoming JSON against LoginCredentials
    - creates a UserSessionModel and passes it to session_engine.create_session()
    - generates a unique UUID, acquires _lock, writes (expires_at, session_data) into the _store dictionary, and sets an HttpOnly client cookie
- Dependency Session Extraction (GET /me)
    - the browser transmits the sid cookie.get_active_session calls session_engine.get_session().The engine acquires _lock, verifies that now < expires_at, updates the expiration time to implement sliding expiration, and returns the typed UserSessionModel
- In-Memory Revocation (POST /logout)
    - the endpoint calls session_engine.delete_session(sid), removing the key from process memory instantly, and clears the client browser cookie via response.delete_cookie()

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Sessions


---
### Server-Side Sessions with Redis (Opaque UUID Token Pattern)

Instead of storing payload bytes inside RAM, thethe user session schema is written into Redis with a Time-To-Live (TTL), and only the UUID string is sent to the browser

Real-World Use Case
- high-security enterprise web applications managing user authentication, multi-tenant roles, and dynamic permissions.

Behavior
- keeps client cookies lightweight while enabling instant server-side session revocation and central session tracking across multiple API nodes.

---
### Server-Side Sessions with Redis (Opaque UUID Token Pattern)

```
import uuid
from fastapi import FastAPI, Response
import redis.asyncio as aioredis
from pydantic import BaseModel

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class UserSessionData(BaseModel):
    user_id: int
    role: str

@app.post("/auth/session")
async def create_server_session(payload: UserSessionData, response: Response):
    # 1. Generate opaque UUID token
    session_id = str(uuid.uuid4())
    
    # 2. Persist session payload in Redis with 30-minute TTL (1800 seconds)
    redis_key = f"session:{session_id}"
    await redis_client.setex(
        redis_key, 
        1800, 
        payload.model_dump_json()
    )
    
    # 3. Transmit opaque token in cookie
    response.set_cookie(key="sid", value=session_id, httponly=True)
    return {"status": "session_created", "sid": session_id}
```

---
### Strongly Typed Session Dependency Injection (Depends)

Creating a custom FastAPI dependency decouples cookie parsing, Redis retrieval, and authorization validation from route handler code.

Real-World Use Case
- protecting private API endpoints by injecting a validated, strongly typed user session object directly into route handlers.

Behavior
- intercepts incoming requests, reads the session cookie, queries Redis, validates schema compliance via Pydantic, and raises an HTTP 401 Unauthorized exception on cache misses or invalid tokens


---
### Strongly Typed Session Dependency Injection (Depends)

```
from typing import Annotated
from fastapi import FastAPI, Depends, Cookie, HTTPException, status
import redis.asyncio as aioredis
from pydantic import BaseModel

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class AuthenticatedUser(BaseModel):
    user_id: int
    email: str

async def get_current_user_session(
    sid: Annotated[str | None, Cookie()] = None
) -> AuthenticatedUser:
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing session cookie"
        )
    
    raw_payload = await redis_client.get(f"session:{sid}")
    if not raw_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session invalid or expired"
        )
        
    return AuthenticatedUser.model_validate_json(raw_payload)

@app.get("/api/v1/profile")
async def get_user_profile(
    user: Annotated[AuthenticatedUser, Depends(get_current_user_session)]
):
    return {"user_id": user.user_id, "email": user.email}
```

---
### Explicit Session Revocation & Cookie Security Hardening

Terminating active user sessions requires deleting the key from Redis and issuing a matching delete_cookie() command to clear client storage.

Real-World Use Case
- implementing secure user logouts, "Log out of all devices" actions, or administrative user suspension.

Behavior
- purging the Redis key invalidates all subsequent API calls immediately, even if the client retains the original cookie value

---
### Explicit Session Revocation & Cookie Security Hardening

```
from typing import Annotated
from fastapi import FastAPI, Cookie, Response, status
import redis.asyncio as aioredis

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

@app.post("/auth/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    response: Response, 
    sid: Annotated[str | None, Cookie()] = None
):
    if sid:
        # 1. Server-side revocation: Purge key from Redis
        await redis_client.delete(f"session:{sid}")

    # 2. Client-side revocation: Clear client cookie
    response.delete_cookie(
        key="sid",
        path="/",
        httponly=True,
        samesite="lax",
        secure=True
    )
    return {"message": "Session terminated successfully"}
```

---
### Unified Enterprise Server-Side Session Engine

This production pattern demonstrates a complete authentication session management service. It incorporates Lifespan Redis connection pooling, Pydantic schema validation, Hardened Cookie configuration, Session Fixation protection, Dependency-driven session extraction, and Server-side session revocation.

---
### Unified Enterprise Server-Side Session Engine

```
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
import uuid
from fastapi import FastAPI, Depends, Cookie, Request, Response, HTTPException, status
from pydantic import BaseModel, EmailStr, ConfigDict
import redis.asyncio as aioredis

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & LIFESPAN MANAGEMENT
# ---------------------------------------------------------------------
REDIS_URL = "redis://localhost:6379"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis Async Client
    app.state.redis = aioredis.from_url(
        REDIS_URL, 
        max_connections=20, 
        decode_responses=True
    )
    yield
    # Shutdown: Close Connection Pool
    await app.state.redis.close()

app = FastAPI(title="Enterprise Session Gateway", lifespan=lifespan)

def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis

# ---------------------------------------------------------------------
# 2. PYDANTIC SCHEMAS
# ---------------------------------------------------------------------
class LoginCredentials(BaseModel):
    email: EmailStr
    password: str

class UserSessionModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    email: EmailStr
    role: str
    tenant_id: str

class ProfileResponse(BaseModel):
    user_id: int
    email: str
    role: str

# ---------------------------------------------------------------------
# 3. SESSION DEPENDENCY INJECTION
# ---------------------------------------------------------------------
async def get_active_session(
    request: Request,
    sid: Annotated[str | None, Cookie()] = None
) -> UserSessionModel:
    """Dependency validating active session token against Redis."""
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Missing session token."
        )

    redis: aioredis.Redis = get_redis(request)
    raw_payload = await redis.get(f"session:{sid}")

    if not raw_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or been revoked."
        )

    # Refresh session TTL on active request (Sliding Expiration)
    await redis.expire(f"session:{sid}", 1800)  # Reset 30-minute window

    return UserSessionModel.model_validate_json(raw_payload)

# ---------------------------------------------------------------------
# 4. PATH OPERATIONS (Login, Session Inspection, Logout)
# ---------------------------------------------------------------------

@app.post("/api/v1/auth/login", status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginCredentials,
    response: Response,
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    # STEP 1: Verify User Credentials (Simulated)
    if credentials.email != "admin@enterprise.io" or credentials.password != "SecretPass123!":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # STEP 2: Construct Immutable Session State Model
    session_data = UserSessionModel(
        user_id=10042,
        email=credentials.email,
        role="ADMINISTRATOR",
        tenant_id="tenant_alpha"
    )

    # STEP 3: Generate New Token (Defends against Session Fixation)
    new_sid = str(uuid.uuid4())
    session_key = f"session:{new_sid}"

    # STEP 4: Store in Redis with 30-Minute Expiration (1800s)
    await redis.setex(session_key, 1800, session_data.model_dump_json())

    # STEP 5: Set Hardened Security Cookie
    response.set_cookie(
        key="sid",
        value=new_sid,
        max_age=1800,
        httponly=True,   # Protects against XSS script access
        samesite="lax",   # Protects against CSRF
        secure=False,     # Set to True in HTTPS production environments
        path="/"
    )

    return {"status": "SUCCESS", "user_id": session_data.user_id}

@app.get(
    "/api/v1/auth/me",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK
)
async def get_current_user_profile(
    session: Annotated[UserSessionModel, Depends(get_active_session)]
):
    # Route protected by dependency; executes only if session is active
    return ProfileResponse(
        user_id=session.user_id,
        email=session.email,
        role=session.role
    )

@app.post("/api/v1/auth/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    sid: Annotated[str | None, Cookie()] = None
):
    if sid:
        # STEP 1: Explicit Server-Side Revocation
        await redis.delete(f"session:{sid}")

    # STEP 2: Clear Client Cookie Storage
    response.delete_cookie(key="sid", path="/")
    
    return {"status": "SUCCESS", "message": "Logged out and session revoked."}
```

---
### Execution Pipeline Explanation

- Application Lifespan Setup
    - as Uvicorn boots up, lifespan creates a pool of asynchronous Redis connections (redis.asyncio) attached to app.state.redis.

- Authentication & Token Generation (POST /login):
    - validates incoming JSON against LoginCredentials.
    - Constructs a typed UserSessionModel payload
    - Generates a cryptographically secure UUID (new_sid), saving the serialized JSON payload to Redis via SETEX with a 1800-second (30-minute) TTL
    - Writes sid=<uuid> to response cookies with httponly=True and samesite="lax".
- Dependency Session Extraction (GET /me):
    - the client transmits the sid cookie automatically
    - get_active_session extracts sid, queries Redis for session:<sid>, and parses raw JSON back into UserSessionModel. 
    - resets the 30-minute Redis TTL (redis.expire), implementing a sliding expiration window for active users.
- Session Revocation (POST /logout)
    - the endpoint reads sid, issues an explicit DEL session:<sid> to Redis to purge server state, and instructs the browser to delete the client cookie via response.delete_cookie()

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Serverside sessions with Redis

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Serverside sessions