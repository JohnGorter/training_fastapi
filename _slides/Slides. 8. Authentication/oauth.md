# OAuth

---
### OAuth

The evolution of OAuth represents a fundamental shift in how applications handle identity, access control, and user trust across the internet.

---
### The Background 

The "Password Anti-Pattern" EraBefore OAuth:

*if a third-party application needed access to a user's data hosted on another service (for example, a print service wanting access to a user's photos stored on Yahoo! or Google), the only available mechanism was for the user to hand over their primary credentials directly to the third party*

Key Problems 
- Over-Privileged Access
- No Revocation Granularity
- Lack of Expiration
- Storage Hazard
- No Auditing or Visibility

The Need & Core Motivations for OAuthOAuth was created to establish a standardized protocol for delegated authorization—allowing a user to grant a third-party application limited, scoped access to their resources on a service without ever disclosing their master password to that application

---
### 

Schema
```
+-----------------------------------------------------------------------+
|                      THE OAUTH DELEGATION MODEL                       |
|                                                                       |
|  User  ──(Approves Request)──> Service Provider (Issues Token)         |
|                                         │                             |
|  Third-Party App <──(Scoped Token)──────┘                             |
|        │                                                              |
|        └────(Requests Resource + Token)─────────> Service Provider    |
+-----------------------------------------------------------------------+
```

---
### Core Architectural Motivations

- Credential Isolation
    - primary credentials (passwords, multi-factor tokens) stay strictly between the user and the identity provider
- Principle of Least Privilege (Scopes)
    - OAuth introduces explicitly defined scopes (e.g., read:photos instead of full:account) 
- Independent Revocation
    - users can view a dashboard on their provider's account (e.g., Google Account Permissions) and revoke access for a single compromised or unused app instantly without altering their master credentials
- Time-Bound Access
    - OAuth introduces short-lived access tokens alongside refresh tokens. If an access token leaks, its potential window of misuse is restricted (typically minutes to hours)
- Interoperability Standard
    - before OAuth, companies like Google, Yahoo!, and AOL created proprietary delegated authorization mechanisms (e.g., AuthSub, BBAuth)
    - OAuth unified the industry around a single, vendor-neutral standard
    
---
### The Historical Evolution 

OAuthOAuth evolved through distinct phases as web application architectures 
- shifted from simple server-rendered pages to modern Single-Page Applications (SPAs), native mobile apps, and microservice topologies

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ OAuth 1.0│ ───> │OAuth 1.0a│ ───> │ OAuth 2.0│ ───> │ OAuth 2.1│
│  (2007)  │      │  (2009)  │      │  (2012)  │      │ (Current)│
└──────────┘      └──────────┘      └──────────┘      └──────────┘
```

---
### Phase 3: The Modern Era 

Key Changes in Modern OAuth (OAuth 2.1 Consolidation)
- Mandatory PKCE (Proof Key for Code Exchange)
    originally designed for mobile apps, PKCE (RFC 7636) is now required across all authorization code flows to prevent authorization code interception attacks
- Deprecation of Insecure Flows
    - implicit Flow Deprecated: SPAs must no longer receive access tokens directly in URL fragments; they must use Authorization Code Flow with PKCE
- Resource Owner Password Credentials Deprecated
    - passing raw credentials to authorization endpoints is explicitly disallowed due to MFA limitations and credential exposure risks
- Strict Redirect URI Matching
    - eliminates wildcard and partial string matching on callback endpoints to prevent open-redirect state-injection attacks
- Identity Layering (OpenID Connect / OIDC) 
    While base OAuth 2.0 is strictly an authorization framework (what you can access), OpenID Connect was introduced as a standard identity layer on top of OAuth 2.0 to handle authentication (who you are) using standardized JSON Web Tokens (JWTs)

---
### Summary Timeline Comparison

|Milestone|Primary Focus|Signature Model|Key Advantage|Major Vulnerability / Downside|
|----|----|----|----|----|
|Pre-OAuth|Direct Credential Sharing|None (Plaintext/Basic Auth)|Simple to implement|Complete account compromise; over-privileged access|
|OAuth 1.0a|Delegated Authorization|Cryptographic (HMAC-SHA1 per request)|Security without mandatory HTTPS|Complex request signing; poor developer experience|
|OAuth 2.0|Flexible Grant Flows|Bearer Tokens over TLS|Simpler API calls; role-specific flows|Loose specification left room for insecure developer setups|
|OAuth 2.1|Security Hardening|Bearer / Sender-Constrained Tokens|Mandatory PKCE; eliminates unsafe grant types|Strict adherence required; legacy codebases require migration|


---
### Standard OAuth2 Implementation in FastAPI 


FastAPI provides native support for OAuth2 using the OAuth2PasswordBearer scheme

The flow involves exchanging user credentials for a signed JSON Web Token (JWT), which the client attaches to subsequent requests in the Authorization header

```
┌────────┐                   ┌─────────┐                 ┌──────────┐
│ Client │ ── POST /token ──>│ FastAPI │ ── Validates ──>│  Database│
│        │ <── JWT Token ─── │         │                 └──────────┘
│        │                   │         │
│        │ ─ GET /protected─>│         │ ── Decodes JWT ──> Decoded
│        │   (Bearer Token)  │         │                    User Data
└────────┘                   └─────────┘
```

---
### Steps & Code

1. Install Dependencies
```
uv add "fastapi[standard]" PyJWT "pwdlib[argon2]"
```
2. Code Implementation (main.py)

```
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel

# Security Configuration
SECRET_KEY = "your-super-secret-key-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Mock Database
fake_db = {
    "alice": {
        "username": "alice",
        "hashed_password": password_hash.hash("secret123"),
    }
}

class User(BaseModel):
    username: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in fake_db:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    return User(username=username)

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = fake_db.get(form_data.username)
    if not user or not password_hash.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. OAuth Authentication


---
### Scopes

In OAuth2, scopes are string identifiers that define specific permissions (such as me:read, items:write, or admin)
- they allow users to grant an application limited access to their account rather than full control

How to define, enforce, and integrate OAuth2 scopes in FastAPI? Good question, lets explore...

---
### Steps to implement scopes

We have to complete the following steps:
1. Define Security Scopes in FastAPI
2. Include Granted Scopes in the JWT
3. Enforce Scopes with Security Dependencies
4. Protect Endpoints with Specific Scopes


---
### Define security scopes

FastAPI provides SecurityScopes to read the scopes required by a route 
- OAuth2PasswordBearer accepts a scopes dictionary to populate the Swagger UI authorization modal

```
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from pydantic import BaseModel
import jwt

SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"

app = FastAPI()

# 1. Declare available scopes for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me:read": "Read basic profile details.",
        "items:read": "Read items from database.",
        "items:write": "Create or update items.",
        "admin": "Full administrative access.",
    },
)

class User(BaseModel):
    username: str
    disabled: bool = False
    scopes: list[str] = []
```

---
### Include Granted Scopes in the JWT

When a user logs in, determine their authorized permissions and encode them inside the scopes or scope claim of the JWT payload

```
@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # In a real app, authenticate against your database
    # Here we grant the scopes requested by the client if valid
    user_permissions = ["me:read", "items:read", "items:write"]
    
    # Filter requested scopes against granted permissions
    granted_scopes = [s for s in form_data.scopes if s in user_permissions]
    
    # Encode granted scopes into token
    token_data = {
        "sub": form_data.username,
        "scopes": granted_scopes
    }
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}
```

---
### Enforce Scopes with Security Dependencies

To check scopes on a route, use Security instead of Depends!
- security accepts a list of required scopes and passes them to SecurityScopes inside your dependency function.

```
def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Check if the token contains ALL required scopes for this endpoint
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scope: '{scope}'",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return User(username=username, scopes=token_scopes)
```

---
### Protect Endpoints with Specific Scopes
Pass the required scopes directly into Security() inside route parameters.

```
# Requires 'me:read' scope
@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Security(get_current_user, scopes=["me:read"])]
):
    return current_user

# Requires both 'items:read' and 'items:write' scopes
@app.post("/items/")
async def create_item(
    current_user: Annotated[
        User, Security(get_current_user, scopes=["items:read", "items:write"])
    ]
):
    return {"status": "Item created", "owner": current_user.username}

# Requires 'admin' scope
@app.get("/admin/dashboard")
async def admin_dashboard(
    current_user: Annotated[User, Security(get_current_user, scopes=["admin"])]
):
    return {"status": "Welcome to Admin Panel"}
```

---
### How It Works in Swagger UI

- Open http://localhost:8000/docs.
- Click the Authorize button at the top right.
- A modal opens with the prompt: "Select which ones you want to grant to Swagger UI."
- Check the checkboxes for the scopes you want to request (e.g., me:read, items:read).
- Enter credentials and submit.

Swagger UI sends the selected scopes to /token. FastApi verifies them, attaches them to the JWT, and enforces them on subsequent requests.

**If a user tries to access /admin/dashboard without checking the admin scope, FastAPI automatically returns a 403 Forbidden error with Not enough permissions**


---
### Social Login Implementations
Option A: Direct Google OAuth2 (Gmail Login)
Google OAuth2 uses Authorization Code Flow. The frontend redirects the user to Google, receives an authorization code on callback, and the FastAPI backend exchanges this code for Google tokens and profile data.

Steps
Google Cloud Setup:

Go to Google Cloud Console.

Create a project, setup the OAuth consent screen, and generate OAuth 2.0 Client Credentials.  
FutureSmart AI

Set Authorized Redirect URI: http://localhost:8000/auth/google/callback.

Install Dependencies:

Bash
pip install httpx authlib starlette
Implementation (google_auth.py):

Python
from fastapi import FastAPI, Request, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Required for Authlib state tracking
app.add_middleware(SessionMiddleware, secret_key="session-secret-key")

oauth = OAuth()
oauth.register(
    name="google",
    client_id="YOUR_GOOGLE_CLIENT_ID",
    client_secret="YOUR_GOOGLE_CLIENT_SECRET",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/auth/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")
        
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to parse Google profile")

    # user_info contains 'email', 'name', 'picture', 'sub'
    return {
        "status": "authenticated",
        "email": user_info["email"],
        "name": user_info["name"],
        "google_id": user_info["sub"]
    }
Option B: Firebase Authentication
Firebase delegates identity management to Google's infrastructure. The Client App logs in with Firebase SDKs (Web/Mobile) and sends a Firebase ID Token to FastAPI in the Authorization: Bearer <ID_TOKEN> header. FastAPI verifies the token via the firebase-admin SDK.

Steps
Firebase Console Setup:

Create a project in the Firebase Console.

Go to Project Settings > Service accounts and click Generate new private key. Save the JSON file locally.

Install Dependencies:

Bash
pip install firebase-admin
Implementation (firebase_auth.py):

Python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = FastAPI()
security = HTTPBearer()

def verify_firebase_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/protected-firebase")
async def protected_route(user_data: Annotated[dict, Depends(verify_firebase_token)]):
    # user_data contains 'uid', 'email', 'name', etc.
    return {
        "message": "Access granted via Firebase",
        "uid": user_data.get("uid"),
        "email": user_data.get("email")
    }
Summary Comparison
Approach	Client Handshake	FastAPI Role	Key Package
Direct OAuth2	Form submission to /token	Validates credentials, issues custom JWTs	PyJWT, pwdlib
Google OAuth2	Browser redirect loop	Exchanges auth code for Google profile data	authlib, httpx
Firebase Auth	Client SDK authenticates user	Verifies Firebase-issued ID tokens	firebase-admin
For a visual walkthrough of setting up Google OAuth2 with FastAPI routes and handling user profiles, see Python FastAPI Google Login Tutorial | OAuth2 Authentication. This video covers the full OAuth flow including redirect URIs, OAuth credentials setup, and token validation.

Here is a detailed breakdown of each implementation, covering the underlying mechanisms, execution flow, key security remarks, and critical configuration points.

1. FastAPI Standard OAuth2 with JWT (Password Flow)
This architecture uses the Resource Owner Password Credentials Grant alongside JSON Web Tokens (JWT). The application handles identity verification and issues cryptographic tokens directly.

┌────────┐                ┌───────────────────────────────┐
│ Client │ ── POST /token ──>│  FastAPI (PasswordHash / JWT) │
│        │ <── JWT Token ───│  Validates against Database   │
│        │                └───────────────────────────────┘
│        │                               │
│        │ ── GET /users/me ─────────────┘
│        │    Header: Authorization: Bearer <JWT>
└────────┘
Detailed Component Explanation
Token Generation & Verification Layer
OAuth2PasswordBearer:

Acts as a FastAPI dependency that inspects incoming requests for an Authorization: Bearer <token> header.

tokenUrl="token" specifies the endpoint where clients can obtain tokens. FastAPI uses this metadata to automatically populate its built-in Interactive API Docs (/docs) with an Authorize button.

PasswordHash.recommended() (pwdlib):

Hashes and verifies raw passwords using modern standards (Argon2 or bcrypt).

Raw passwords are never stored in databases; only cryptographic hashes are persisted.

jwt.encode() and jwt.decode():

Signing (encode): Creates a base64-encoded string containing user claims (e.g., sub for subject/username) and an expiration time (exp), signed using the server's SECRET_KEY.

Validation (decode): Ensures the incoming token was signed using the same SECRET_KEY and checks whether the current timestamp exceeds exp. If modified or expired, it raises jwt.InvalidTokenError.

Endpoint Execution Flow
POST /token:

Client sends a application/x-www-form-urlencoded body containing username and password.

FastAPI injects OAuth2PasswordRequestForm to parse these fields automatically.

Server queries the database for the user record.

Server verifies the password using password_hash.verify().

On success, an access token containing {"sub": username, "exp": expiration} is generated and returned as JSON: {"access_token": "...", "token_type": "bearer"}.

GET /users/me:

Client sends a request containing header: Authorization: Bearer <token>.

Dependency get_current_user calls oauth2_scheme, extracting the token string.

Token is decoded using SECRET_KEY and algorithm HS256.

The sub field is extracted and checked against the database to confirm the account still exists.

The resolved User object is injected directly into the route function parameter current_user.

Key Remarks & Security Requirements
Stateless vs. Revocation: JWTs are stateless—the server does not keep active sessions in memory or a database. Once issued, a JWT remains valid until it expires. To force logouts or invalidate tokens early, you must introduce a token blocklist in a fast store like Redis.

Secret Key Security: The SECRET_KEY string must be kept out of source control. Store it as an environment variable and generate it using a cryptographically secure method:

Bash
python -c "import secrets; print(secrets.token_hex(32))"
HTTPS Requirement: In standard OAuth2 password flow, raw credentials are transmitted in the request body to /token. Transport Layer Security (HTTPS) is mandatory in production to prevent interception.

2. Direct Google OAuth2 (Gmail Login)
This flow uses Authorization Code Flow with OpenID Connect (OIDC). FastAPI acts as an OAuth client relying on Google as the Identity Provider (IdP).

┌────────┐              ┌────────────────┐              ┌───────────────┐
│ Client │ ────────────>│  FastAPI App   │ ────────────>│ Google Auth   │
│        │  /auth/login │ (Authlib Setup)│ Redirect URI │ Server (IdP)  │
│        │              └────────────────┘              └───────────────┘
│        │                                                      │
│        │ <────── Returns User Data & Identity Credentials ─────┘
└────────┘   Callback to /auth/google/callback
Detailed Component Explanation
State & Redirect Management
SessionMiddleware:

Social login flows require protecting against Cross-Site Request Forgery (CSRF) attacks during OAuth redirects.

Authlib generates a unique temporary state token stored in an encrypted browser session cookie before redirecting to Google. When Google sends the response back, Authlib verifies that the state token returned matches the session cookie state.

OpenID Connect Discovery (server_metadata_url):

Instead of manually hardcoding endpoints for authorization, token retrieval, and user profiles, Authlib fetches configuration dynamically from [https://accounts.google.com/.well-known/openid-configuration](https://accounts.google.com/.well-known/openid-configuration).

Scopes (scope="openid email profile"):

openid: Instructs Google to process the request as an OpenID Connect identity transaction, returning an ID Token.

email: Grants access to the user's primary email address and verification status.

profile: Grants access to basic profile fields (display name, profile picture URL).

Endpoint Execution Flow
GET /auth/google/login:

User triggers login on client application.

oauth.google.authorize_redirect() builds a Google authorization URL containing client_id, requested scopes, and redirect_uri.

The route responds with a 302 Redirect to Google's sign-in page.

GET /auth/google/callback:

Google redirects the user back to /auth/google/callback?code=AUTH_CODE&state=STATE_TOKEN.

oauth.google.authorize_access_token(request) receives this authorization code and submits an asynchronous POST request behind the scenes to Google's token endpoint ([https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)).

Google validates the code and returns access tokens alongside an ID Token containing user profile metadata (userinfo).

FastAPI extracts identity attributes (email, sub, name) to create or log in the user within your application's database.

Key Remarks & Security Requirements
Redirect URIs Match: The callback path defined in code (request.url_for("google_callback")) must exactly match one of the URIs specified in the Google Cloud Console > Credentials > Authorized redirect URIs. A mismatch produces an invalid_grant or redirect_uri_mismatch error.

App-Specific Session Tokens: Google's OAuth tokens authenticate the user against Google, but should not serve as your API session directly. Once Google confirms identity:

Find or create the corresponding user in your database.

Issue your own application-specific JWT (as shown in Step 1) to pass back to your frontend client.

3. Firebase Authentication Integration
This pattern decouples authentication mechanics entirely from the API backend. The frontend (Web, iOS, Android) logs the user in using the Firebase Client SDK. The backend's sole responsibility is verifying identity assertions sent via Firebase ID tokens.

┌────────┐    1. Login via Client SDK     ┌──────────────────┐
│ Client │ ──────────────────────────────>│ Firebase Auth    │
│        │ <───────────────────────────── │ Services         │
│        │    2. Returns Firebase Token   └──────────────────┘
│        │
│        │    3. API Request with Bearer Token
│        │ ───────────────────────────────────┐
└────────┘                                    │
                                              ▼
                                   ┌────────────────────┐
                                   │  FastAPI Backend   │
                                   │  (firebase-admin)  │
                                   └────────────────────┘
Detailed Component Explanation
Service Account & Verification Layer
credentials.Certificate("serviceAccountKey.json"):

Authenticates your FastAPI backend to Firebase Admin infrastructure using asymmetric private keys.

firebase_admin.initialize_app():

Boots the Firebase SDK inside your application instance.

HTTPBearer():

A FastAPI security dependency that parses incoming headers, extracting the raw Bearer token string from Authorization: Bearer <TOKEN>.

auth.verify_id_token(token):

Performs cryptographic validation on the incoming JWT using Google's public key set (which firebase-admin automatically fetches and caches).

Validates token expiration, issuer ([https://securetoken.google.com/](https://securetoken.google.com/)<PROJECT-ID>), signature, and target audience (PROJECT-ID).

Endpoint Execution Flow
Client Handshake (Frontend):

Client app calls Firebase SDK methods (e.g., signInWithPopup(auth, googleProvider)).

Firebase issues a Firebase ID token.

Client attaches this ID token to API calls as a standard Bearer authorization header.

Backend Routing (GET /protected-firebase):

Request hits FastAPI endpoint guarded by Depends(verify_firebase_token).

Dependency runs auth.verify_id_token().

If valid, the decoded payload dictionary containing fields like uid (Firebase unique user ID), email, and email_verified is passed to your route handler.

If invalid or expired, HTTPException(status_code=401) is thrown automatically.

Key Remarks & Security Requirements
Key File Security: The service account JSON file contains high-privilege credentials capable of managing your entire Firebase infrastructure. Never check serviceAccountKey.json into source control. In production environments, use environment variables to load credentials instead:

Python
import os
import json
from firebase_admin import credentials

cred_dict = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"])
cred = credentials.Certificate(cred_dict)
Performance Considerations: firebase_admin handles cryptographic checks locally and caches Google's public key certs. It does not issue a remote network call to Firebase on every single API request, maintaining low latency.

Token Lifetime: Firebase ID tokens are short-lived (1 hour). Your frontend client must use the Firebase SDK's getIdToken() call before sending requests to automatically handle silent background token refresh.
Yes, you are completely correct.

In modern OAuth 2.0 and OAuth 2.1 specifications, the Resource Owner Password Credentials (ROPC) grant (commonly called the "Password Flow") is officially deprecated and explicitly disallowed in OAuth 2.1.

Here is a breakdown of why it was deprecated, why FastAPI documentation still references it, and what you should use instead.

Why the Password Flow Was Deprecated
Direct Exposure of Credentials: The client application must directly collect, handle, and process the user's plain-text password. This violates the primary objective of OAuth, which is to delegate authorization without sharing credentials with client applications.

No Support for Multi-Factor Authentication (MFA): Modern security demands MFA (SMS, TOTP, hardware keys). The simple username/password payload structure of the password grant makes implementing robust MFA mechanisms difficult and inconsistent.

Over-Privileged Access: Passing raw credentials to the application gives the client access to everything the user can do, rather than granting granular, scoped authorization.

Why FastAPI's Tutorial Still Uses It
FastAPI's security documentation heavily features OAuth2PasswordBearer and OAuth2PasswordRequestForm.

This is not because FastAPI encourages third-party OAuth password delegation, but because:

First-Party Login Convenience: For simple, single-service architectures where your frontend (e.g., React) and your backend (FastAPI) belong to the exact same system, OpenAPI (/docs) natively supports interactive login testing out-of-the-box using the password form wrapper.

Internal UI Support: The Swagger UI built into FastAPI natively integrates with the password flow specification to let developers test protected endpoints directly inside the browser docs.

Modern Alternatives & Recommended Flows
Depending on your application type, you should replace the Resource Owner Password Flow with one of the following standard patterns:

┌───────────────────────────────────┬─────────────────────────────────────────────────┐
│ Application Architecture          │ Recommended OAuth 2.1 / OIDC Flow               │
├───────────────────────────────────┼─────────────────────────────────────────────────┤
│ Single-Page Apps (React, Vue)     │ Authorization Code Flow with PKCE               │
│ Mobile Apps (iOS, Android)        │ Authorization Code Flow with PKCE               │
│ Traditional Web Apps (Jinja, SSR) │ Standard Authorization Code Flow                │
│ Third-Party / Social Auth         │ OpenID Connect (Google, GitHub, Firebase, etc.) │
└───────────────────────────────────┴─────────────────────────────────────────────────┘
What is PKCE (Proof Key for Code Exchange)?
PKCE (pronounced "pixie") extends the Authorization Code Flow for public clients (like browser or mobile apps) that cannot safely hold a client secret. Instead of sending a static secret, the client generates a dynamic secret key pair (code_verifier and code_challenge) for every single login request to prevent code interception attacks.

Updated Code Example: Session & Token Login (Without Password Flow)
If you want a standard, secure local authentication system without using the deprecated OAuth2 password grant structure, separate your login endpoint from the strict OAuth2PasswordRequestForm specification.

Python
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationHeader, HTTPBearer
from pwdlib import PasswordHash
from pydantic import BaseModel, EmailStr

SECRET_KEY = "your-super-secret-key"
ALGORITHM = "HS256"

app = FastAPI()
security = HTTPBearer()  # Uses standard HTTP Authorization: Bearer <token>
password_hash = PasswordHash.recommended()

# Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Helper to verify standard JWTs
def get_current_user(
    auth_header: Annotated[HTTPAuthorizationHeader, Depends(security)]
):
    token = auth_header.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token claims")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

# Standard Auth Endpoint (JSON body instead of form-data)
@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    # 1. Fetch user from database by credentials.email
    # 2. Verify password with password_hash.verify(credentials.password, db_user.password)
    
    # Example payload generation:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    token = jwt.encode(
        {"sub": "user_12345", "exp": expire}, SECRET_KEY, algorithm=ALGORITHM
    )
    return TokenResponse(access_token=token)

@app.get("/users/me")
async def get_me(current_user_id: Annotated[str, Depends(get_current_user)]):
    return {"user_id": current_user_id}