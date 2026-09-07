# OAuth2 

---
### Architecture & Password Flow Mechanics

OAuth2 is an authorization framework that decouples authentication from resource access by issuing signed tokens (typically JSON Web Tokens / JWTs)

Definitions:
- resource Owner => The user who owns the data
- client => The frontend application (React, iOS App) requesting access.
- authorization Server => The OAuth2 service validating credentials and issuing JWTs.
- resource Server => The FastAPI backend validating incoming JWTs and serving data.

---
### The OAuth2 Authorization Code Flow

The Authorization Code flow decouples authentication (verifying who the user is) from token issuance (granting access to resources) by introducing an intermediate step => a short-lived authorization code

- User Authorization Request (GET/POST /authorize):
    - the client application redirects the user's browser to the Authorization Server's /authorize endpoint with query parameters: 
     - client_id
     - redirect_uri
     - response_type="code"
     - scope
    - the user authenticates directly with the Authorization Server (e.g., login form or SSO provider)
- Upon successful authentication:
    - the Authorization Server generates a short-lived, single-use Authorization Code 
    - redirects the user's browser back to redirect_uri?code=TEMP_CODE

---
### The OAuth2 Authorization Code Flow (2)

Code-to-Token Exchange (POST /token):
- the client application:
    - extracts code from the redirect URL 
    - sends a back-channel (server-to-server) POST request to /token
        - parameters sent: grant_type="authorization_code", code, redirect_uri, client_id, and client_secret

- the Authorization Server:
    - verifies that the code is valid, unexpired, and matches the original client_id and redirect_uri
    - consumes (invalidates) the code 
    - responds with a JSON payload containing an access_token (JWT) and optionally a refresh_token

---
### The OAuth2 Authorization Code Flow (3)

Resource Access (GET /resources) require the client to send a header.

The client:
    - calls protected API endpoints by attaching the JWT in the Authorization header
    - Bearer TOKEN

---
### How does it work in FastAPI

FastAPI provides **OAuth2AuthorizationCodeBearer** to configure OpenAPI (Swagger UI) for this flow

It instructs Swagger UI to open an authorization window targeting authorizationUrl, retrieve the resulting code, and automatically POST it to tokenUrl

Python
from fastapi.security import OAuth2AuthorizationCodeBearer

# Tells Swagger UI where to redirect users for authorization and where to exchange codes
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/authorize",
    tokenUrl="/token",
    scopes={"read:profile": "Read user profile", "write:orders": "Create orders"}
)

OAuth2 scopes act as granular permissions that restrict access to specific parts of your API based on what the client application is allowed to do. In Swagger UI, declaring scopes displays checkboxes in the authorization modal so you can simulate requesting specific permissions during token retrieval.

Core Scope Concepts in FastAPI

Declaration: Available scopes are defined as a dictionary inside your OAuth2 security scheme so Swagger UI knows what choices to render in the popup.

Route Requirements: Endpoints are protected using Security() instead of Depends(), passing the exact array of scopes required to access that route.

Scope Extraction: FastAPI passes required route scopes into your authentication dependency using SecurityScopes, allowing you to compare required permissions against the scopes contained in the client's token.

Implementation Example for /users/me

Python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes

app = FastAPI()

# 1. Define available scopes in the OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/authorize",
    tokenUrl="/token",
    scopes={
        "me": "Read current user profile data.",
        "admin": "Full administrative access."
    }
)

# 2. Extract and validate scopes inside your dependency
async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    auth_header = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"

    # Decode JWT here and extract granted scopes (mocked for this example)
    granted_token_scopes = ["me"] 

    for scope in security_scopes.scopes:
        if scope not in granted_token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": auth_header},
            )
    return {"username": "johndoe"}

# 3. Require the "me" scope on the route
@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[dict, Security(get_current_user, scopes=["me"])]
):
    return current_user
Key Steps Explained

scopes={...}: Populates the checkboxes in the Swagger UI Authorize popup with human-readable descriptions.

Security(..., scopes=["me"]): Replaces standard Depends(). It registers in the OpenAPI spec that /users/me requires the "me" scope, making Swagger UI display it in the endpoint lock icon detail.

SecurityScopes: Injects an object into get_current_user containing .scopes (a list containing ["me"]) so you can programmatically block requests missing required permissions.


Unified Enterprise Authorization Code Flow Implementation

This production pattern demonstrates a complete Authorization Server and Resource Server workflow within FastAPI: handling /authorize credential verification and code issuance, single-use /token exchange, and JWT resource protection.

Python
from datetime import datetime, timedelta, timezone
import uuid
from typing import Annotated
import jwt
from fastapi import FastAPI, Depends, Form, Query, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from pydantic import BaseModel

SECRET_KEY = "enterprise-authorization-secret-key"
ALGORITHM = "HS256"

app = FastAPI()

# OpenAPI Security Scheme for Authorization Code Flow
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/authorize",
    tokenUrl="/token",
    scopes={"read:profile": "Read user profile data"}
)

# Transient Storage Simulations (Use Redis in Production)
CLIENT_DB = {"client_app_123": {"client_secret": "secret_abc", "redirect_uri": "https://client.app/callback"}}
USER_DB = {"alice": "password123"}
AUTHORIZATION_CODES: dict[str, dict] = {}  # Format: {code: {user, client_id, scope, expires_at}}


# Schema Definitions
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# =====================================================================
# STEP 1: AUTHORIZE ENDPOINT
# User authenticates and receives an Authorization Code via Redirect
# =====================================================================
@app.get("/authorize")
async def authorize_page(
    client_id: Annotated[str, Query()],
    redirect_uri: Annotated[str, Query()],
    response_type: Annotated[str, Query()],
    scope: Annotated[str, Query()] = "",
):
    """Validates client registration prior to rendering the login form."""
    if client_id not in CLIENT_DB or CLIENT_DB[client_id]["redirect_uri"] != redirect_uri:
        raise HTTPException(status_code=400, detail="Invalid client_id or redirect_uri")
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type. Must be 'code'")
    
    return {"message": "Render Authorization Login Form", "client_id": client_id, "scope": scope}


@app.post("/authorize")
async def process_authorization(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    scope: Annotated[str, Form()] = "",
):
    """Verifies user credentials and redirects back to client with temporary Auth Code."""
    # 1. Validate User Credentials
    if USER_DB.get(username) != password:
        raise HTTPException(status_code=401, detail="Invalid user credentials")

    # 2. Generate short-lived (60s), single-use Authorization Code
    auth_code = f"code_{uuid.uuid4().hex}"
    AUTHORIZATION_CODES[auth_code] = {
        "username": username,
        "client_id": client_id,
        "scope": scope.split(),
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=60),
    }

    # 3. Redirect user back to Client App with the Authorization Code
    redirect_target = f"{redirect_uri}?code={auth_code}"
    return RedirectResponse(url=redirect_target, status_code=status.HTTP_302_FOUND)


# =====================================================================
# STEP 2: TOKEN ENDPOINT
# Client App exchanges Authorization Code for JWT Access Token (Back-Channel)
# =====================================================================
@app.post("/token", response_model=TokenResponse)
async def exchange_code_for_token(
    grant_type: Annotated[str, Form()],
    code: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    client_secret: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form() | None] = None,
):
    """Exchanges a valid, unexpired Authorization Code for a Bearer JWT Token."""
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type. Must be 'authorization_code'")

    # 1. Verify Client Credentials
    client = CLIENT_DB.get(client_id)
    if not client or client["client_secret"] != client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    # 2. Retrieve & Validate Authorization Code
    code_data = AUTHORIZATION_CODES.get(code)
    if not code_data:
        raise HTTPException(status_code=400, detail="Invalid or spent authorization code")

    # 3. SINGLE-USE ENFORCEMENT: Delete code immediately upon access
    del AUTHORIZATION_CODES[code]

    if datetime.now(timezone.utc) > code_data["expires_at"]:
        raise HTTPException(status_code=400, detail="Authorization code has expired")

    if code_data["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Client ID mismatch")

    # 4. Issue JWT Access Token
    expires_delta = timedelta(minutes=15)
    jwt_payload = {
        "sub": code_data["username"],
        "client_id": client_id,
        "scopes": code_data["scope"],
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    
    access_token = jwt.encode(jwt_payload, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(access_token=access_token, expires_in=int(expires_delta.total_seconds()))


# =====================================================================
# STEP 3: PROTECTED RESOURCE ENDPOINT
# Validates Bearer Token and Scopes
# =====================================================================
async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token",
        headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])
        if not username:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Enforce endpoint scope requirements
    for required_scope in security_scopes.scopes:
        if required_scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: '{required_scope}'"
            )

    return {"username": username, "scopes": token_scopes}


@app.get("/users/me")
async def read_user_profile(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    return {
        "status": "authenticated",
        "user": current_user["username"],
        "granted_scopes": current_user["scopes"]
    }
The Authorization Code flow isolates credential entry to the /authorize endpoint, ensuring the client application never sees or stores user passwords. The short expiration window (e.g., 60 seconds) and immediate deletion of the authorization code upon exchange prevent replay attacks and token theft.


3. Authorization: Scopes vs. Role-Based Access Control (RBAC)

Authorization determines what an authenticated entity is permitted to execute. Enterprise systems generally mix or choose between two models:

OAuth2 Scopes (Delegated Permissions):

Focus: What authority has been granted to this specific token?

Scopes define permission flags encoded inside the token (e.g., read:users, write:orders). They are used when third-party applications or frontend clients operate on behalf of a user with restricted capabilities (e.g., "Allow this app to read your profile, but not delete your account").

In FastAPI, scopes are validated using Security and SecurityScopes.

Role-Based Access Control / RBAC (Organizational Permissions):

Focus: Who is this user inside the business organization?

RBAC assigns identity roles (admin, manager, customer) to users. System capabilities are mapped directly to these roles.

In FastAPI, RBAC is usually implemented via custom class dependencies that check user["role"].

Scopes vs. RBAC Key Differences

Feature	OAuth2 Scopes	Role-Based Access Control (RBAC)
Primary Target	Token capabilities (Delegation)	User identity & business function
Source of Truth	Encoded directly inside the JWT payload	Stored in Database / Identity Provider
Use Case	Third-party APIs, mobile/SPA client boundaries	Internal corporate apps, multi-tenant SaaS
FastAPI Tooling	Security(dep, scopes=["read"]), SecurityScopes	Custom Dependency Classes (Depends(RoleChecker(...)))
Python
# RBAC Dependency Example
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[dict, Depends(get_current_user)]):
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your assigned role"
            )
        return user
Unified Enterprise OAuth2, Scopes, and RBAC Request Flow

This complete production pattern illustrates how an enterprise API issues OAuth2 JWT tokens with scopes and validates incoming requests using both OAuth2 Scopes (via SecurityScopes) and RBAC Roles simultaneously.

Python
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import FastAPI, Depends, Security, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from pydantic import BaseModel, Field

SECRET_KEY = "enterprise-production-secret-key"
ALGORITHM = "HS256"

app = FastAPI()

# 1. Define OAuth2 Scheme with explicit OpenAPI Scope descriptions
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "reports:read": "Read financial analytics reports.",
        "reports:write": "Create or modify financial analytics reports.",
    }
)

# User Database Mock (Contains RBAC Roles)
USER_DB = {
    "alice_mgr": {
        "username": "alice_mgr",
        "password": "password123",
        "role": "finance_manager",  # RBAC Role
    },
    "bob_analyst": {
        "username": "bob_analyst",
        "password": "password123",
        "role": "analyst",          # RBAC Role
    }
}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scopes: list[str]

# 2. Token Generation Endpoint (Handles OAuth2 Authentication + Scope Assignment)
@app.post("/token", response_model=TokenResponse)
async def generate_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = USER_DB.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )
    
    # Requested scopes fallback to empty list if none provided by client
    requested_scopes = form_data.scopes if form_data.scopes else ["reports:read"]
    
    # Token Payload encoding Identity, Roles (RBAC), and Scopes
    jwt_claims = {
        "sub": user["username"],
        "role": user["role"],
        "scopes": requested_scopes,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    
    token = jwt.encode(jwt_claims, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(access_token=token, scopes=requested_scopes)

# 3. Security Dependency: Validates JWT and Checks Required OAuth2 Scopes
async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> dict:
    # Build WWW-Authenticate header with required scopes for 401 failures
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or scopes",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # SCOPE CHECK: Verify token contains ALL scopes declared on the target endpoint
    for required_scope in security_scopes.scopes:
        if required_scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Missing scope: '{required_scope}'",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return {"username": username, "role": role, "scopes": token_scopes}

# 4. Callable RBAC Checker Dependency
class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden for role '{user['role']}'. Required: {self.allowed_roles}"
            )
        return user

# 5. Protected Endpoint combining Scopes AND RBAC
@app.post(
    "/reports/financial",
    status_code=status.HTTP_201_CREATED,
    tags=["Financial Operations"]
)
async def create_financial_report(
    # Step A: Check OAuth2 Token Scope ('reports:write') via Security()
    # Step B: Check User RBAC Role ('finance_manager') via RequireRole dependency
    user: Annotated[dict, Security(RequireRole(["finance_manager"]), scopes=["reports:write"])]
):
    return {
        "status": "Report created successfully",
        "created_by": user["username"],
        "assigned_role": user["role"],
        "token_scopes_used": user["scopes"]
    }
Execution Pipeline Explanation:

Authentication (/token): The client POSTs username, password, and desired scopes. The endpoint validates credentials against USER_DB and returns a signed JWT containing both identity claims (sub, role) and authorization flags (scopes).

Scope Verification (Security(..., scopes=[...])): When accessing /reports/financial, FastAPI evaluates SecurityScopes. It checks whether the token contains the reports:write scope in payload["scopes"]. If missing, it returns HTTP 403 Forbidden detailing the missing scope.

RBAC Verification (RequireRole([...])): After scopes pass, the RequireRole callable dependency inspects user["role"]. If bob_analyst attempts access with a valid reports:write scope token, execution still halts with HTTP 403 because his role (analyst) is not in ["finance_manager"].

Endpoint Execution: Execution proceeds to the business logic only when both security criteria pass: the token is explicitly authorized to write reports (Scope Check) AND the user identity possesses managerial clearance (RBAC Check).