FastAPI manages user session state using either client-side signed cookies (SessionMiddleware) or server-side session stores (e.g., Redis) where a client holds only a secure, unique session ID cookie.

1. Signed Cookie Sessions (SessionMiddleware)
Starlette’s built-in SessionMiddleware stores session data directly inside an encrypted HTTP cookie signed with a secret key.

Real-World Use Case: Storing lightweight user state (e.g., user IDs, flash notifications, theme preferences) without setting up a backend database table.

Behavior: The client holds the signed payload. On every request, FastAPI verifies the cryptographic signature and populates request.session as a standard Python dictionary.

Python
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Cryptographically signs cookies to prevent client tampering
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-change-in-prod")

@app.post("/session/theme")
async def set_theme(theme: str, request: Request):
    # Mutate session dict directly
    request.session["theme"] = theme
    return {"message": f"Theme set to {theme}"}

@app.get("/session/theme")
async def get_theme(request: Request):
    # Read from verified cookie payload
    user_theme = request.session.get("theme", "light")
    return {"theme": user_theme}
2. Server-Side Sessions with Redis (Session ID Pattern)
Storing large or sensitive session data inside client-side cookies can breach the 4KB browser cookie size limit or expose state. A server-side pattern stores session objects in Redis and issues a random UUID session_id cookie to the browser.

Real-World Use Case: Managing high-security authentication states, active shopping carts, or multi-tenant permissions.

Behavior: The browser stores only a 36-character UUID string. The server fetches the JSON session payload asynchronously from Redis on each request.

Python
import uuid
from fastapi import FastAPI, Response
import redis.asyncio as aioredis
from pydantic import BaseModel

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class SessionPayload(BaseModel):
    user_id: int
    role: str

@app.post("/login")
async def login(payload: SessionPayload, response: Response):
    session_id = str(uuid.uuid4())
    
    # Store session data in Redis with a 1-hour expiration (TTL)
    await redis_client.setex(
        f"session:{session_id}",
        3600,
        payload.model_dump_json()
    )
    
    # Send only the session_id to the client
    response.set_cookie(key="session_id", value=session_id)
    return {"status": "logged_in"}
3. Custom Session Dependency Injection (Depends)
Extracting session verification into a custom FastAPI dependency (Depends(get_current_session)) decouples cookie reading and storage lookup logic from your route handlers.

Real-World Use Case: Enforcing mandatory session authentication across protected routes while injecting a strongly typed session object into handlers.

Behavior: Reads the session_id cookie, queries Redis, validates expiration, and raises an HTTP 401 Unauthorized exception if the session is invalid or expired.

Python
from typing import Annotated
from fastapi import FastAPI, Depends, Cookie, HTTPException, status
import redis.asyncio as aioredis
from pydantic import BaseModel

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class UserSession(BaseModel):
    user_id: int
    email: str

async def get_current_session(
    session_id: Annotated[str | None, Cookie()] = None
) -> UserSession:
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session cookie")
    
    raw_session = await redis_client.get(f"session:{session_id}")
    if not raw_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
        
    return UserSession.model_validate_json(raw_session)

@app.get("/me")
async def get_profile(session: Annotated[UserSession, Depends(get_current_session)]):
    return {"user_id": session.user_id, "email": session.email}
4. Cookie Security Hardening (HttpOnly, SameSite, Secure)
Production session cookies must be protected against Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF) attacks using explicit cookie security flags.

Real-World Use Case: Securing authentication session tokens against browser token theft and cross-site request vulnerabilities.

Behavior: httponly=True blocks JavaScript document.cookie access; samesite="lax" prevents cross-site request sending; secure=True restricts cookie transmission to HTTPS connections.

Python
from fastapi import Response

def set_secure_session_cookie(response: Response, session_id: str):
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=3600,             # Expires in 1 hour
        httponly=True,            # Prevents JavaScript theft (XSS protection)
        samesite="lax",           # Mitigates CSRF attacks
        secure=True,              # Transmits over HTTPS only
        path="/"                  # Available across whole domain
    )
Unified Enterprise Server-Side Session System

This complete implementation combines a FastAPI application using a lifespan context manager, Redis session persistence, Pydantic data schemas, dependency-based session validation, and hardened HTTP cookie handling.

Python
from contextlib import asynccontextmanager
import uuid
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends, Cookie, Response, HTTPException, status
from pydantic import BaseModel, EmailStr
import redis.asyncio as aioredis

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & LIFESPAN MANAGEMENT
# ---------------------------------------------------------------------
REDIS_URL = "redis://localhost:6379"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Establish Redis connection pool on startup
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    yield
    # Close connection pool on shutdown
    await app.state.redis.close()

app = FastAPI(title="Enterprise Session Service", lifespan=lifespan)

# ---------------------------------------------------------------------
# 2. PYDANTIC SCHEMAS
# ---------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserSessionData(BaseModel):
    user_id: int
    email: EmailStr
    role: str

# ---------------------------------------------------------------------
# 3. SESSION DEPENDENCY INJECTION
# ---------------------------------------------------------------------
async def get_active_session(
    request_app: FastAPI,
    session_id: Annotated[str | None, Cookie()] = None
) -> UserSessionData:
    """Dependency that extracts, validates, and rehydrates session state from Redis."""
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No session cookie present."
        )

    redis: aioredis.Redis = request_app.state.redis
    raw_data = await redis.get(f"session:{session_id}")

    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid."
        )

    return UserSessionData.model_validate_json(raw_data)

# Helper Dependency wrapper to supply app state to dependency
async def get_session(
    session_id: Annotated[str | None, Cookie()] = None
) -> UserSessionData:
    # Resolves dependency in route handlers
    return await get_active_session(app, session_id)

# ---------------------------------------------------------------------
# 4. PATH OPERATIONS (Login, Session Inspection, Logout)
# ---------------------------------------------------------------------
@app.post("/api/auth/login", status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest, response: Response):
    # 1. Authenticate credentials (simulated)
    if credentials.email != "admin@enterprise.com" or credentials.password != "secret123":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password."
        )

    # 2. Construct session payload
    session_data = UserSessionData(
        user_id=8842,
        email=credentials.email,
        role="administrator"
    )

    # 3. Save session in Redis with 30-minute TTL (1800 seconds)
    session_id = str(uuid.uuid4())
    redis: aioredis.Redis = app.state.redis
    await redis.setex(
        f"session:{session_id}",
        1800,
        session_data.model_dump_json()
    )

    # 4. Set Hardened Cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=1800,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production environments
        path="/"
    )

    return {"message": "Login successful", "user_id": session_data.user_id}

@app.get("/api/auth/me", response_model=UserSessionData)
async def get_current_user_profile(
    session: Annotated[UserSessionData, Depends(get_session)]
):
    # Route is protected; automatically receives valid session payload
    return session

@app.post("/api/auth/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    session_id: Annotated[str | None, Cookie()] = None
):
    if session_id:
        # 1. Delete session record from Redis
        redis: aioredis.Redis = app.state.redis
        await redis.delete(f"session:{session_id}")

    # 2. Instruct browser to clear session cookie
    response.delete_cookie(key="session_id", path="/")
    return {"message": "Logged out successfully"}
Execution Pipeline Explanation:

Session Creation (/api/auth/login): Upon successful authentication, the server generates a UUID session_id. It stores the serialized UserSessionData object in Redis under the key session:<uuid> with a 30-minute Time-To-Live (setex), and writes the UUID string to a secure, HttpOnly client cookie.

Session Verification (/api/auth/me): When the browser accesses a protected route, it transmits the session_id cookie automatically. The get_session dependency extracts the cookie value, reads the JSON payload from Redis, parses it into a UserSessionData object, and injects it directly into the route handler.

Session Destruction (/api/auth/logout): The logout endpoint reads the session_id cookie, issues a DELETE command to Redis to purge the server-side state immediately, and calls response.delete_cookie() to clear the client browser cookie.