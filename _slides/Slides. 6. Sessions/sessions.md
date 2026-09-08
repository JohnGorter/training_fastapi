# Sessions

---
### Sessions

Sessions persist client state across stateless HTTP requests

In web architectures, session management is implemented either as 
- client-side signed cookie state 
- server-side session stores mapped to an opaque session identifier token

---
### Theoretical Background & Architecture Options

|Criteria|Client-Side Signed Cookies (SessionMiddleware)|Server-Side Session Store (Redis + Session ID Cookie)|
|----|----|----|
|State Storage|Encrypted/signed payload stored inside browser cookie|Payload stored in server RAM (Redis); client holds 36-char UUID|
|Payload Capacity|Max 4KB per domain (browser cookie spec limit)|Arbitrary size (megabytes of user state/cart data)|
|Revocation Control|Hard to invalidate before cookie expiration without blacklist|Instant global revocation via server key deletion (redis.delete())|
|Security Risk|Payload visible/decryptable if secret leaks|Low payload exposure; client holds only an opaque reference token|
|Backend Overhead|Zero server RAM/DB overhead per active user|Requires fast, persistent key-value store (Redis/Memcached)|

---
### Sessions in fastAPI

To implement sessions, we have the following high level steps to take
- enable session middleware
- Session Management => takes care of creating a random session string and validates sessions
- Creating a Session Validation Dependency => a dependency that validates the expiration of sessions
- Handling Token Expiry
- Manage login and logout functionality

---
### Enable session middleware

First we 
```
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
```
 enables HTTP session management in a Starlette or FastAPI application
- intercepts every incoming HTTP request, reads or creates a signed session cookie
- attaches a dictionary-like object to request.session that persists data across multiple HTTP requests for the same user

---
### How It Works

1. Cookie Reading: When a client sends a request, SessionMiddleware looks for a cookie named session
2. Cryptographic Unpacking: It uses the secret_key to verify the signature and decode the payload stored inside the cookie
3. Data Access: It makes the session data available inside your endpoint via request.session
4. Cookie Writing: When the response is sent back to the client, any modifications made to request.session are serialized, cryptographically signed with secret_key, and sent back in a updated Set-Cookie header


---
### How It Works

```
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Add the session middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

@app.post("/login")
async def login(request: Request):
    # Write to session (stored in the signed cookie)
    request.session["user_id"] = 42
    return {"message": "Logged in"}

@app.get("/profile")
async def profile(request: Request):
    # Read from session
    user_id = request.session.get("user_id")
    if not user_id:
        return {"error": "Not authenticated"}, 401
    return {"user_id": user_id}

@app.post("/logout")
async def logout(request: Request):
    # Clear session
    request.session.clear()
    return {"message": "Logged out"}
```

---
### Important Considerations

- Client-Side Storage
    - Starlette's SessionMiddleware stores the actual session payload directly inside the cookie on the user's browser—not on the server!
- Security
    - because data is stored on the client, it is signed (to prevent tampering) but not encrypted by default!
    - do not store sensitive secrets (like raw passwords or credit card numbers) inside request.session
- Cookie Size Limit
    - browsers cap cookies at ~4 KB, so request.session should only store small amounts of state, such as a user ID or temporary authentication flag
- Secret Key Safety
    - always load secret_key from an environment variable in production (e.g., os.getenv("SECRET_KEY"))
    - never hardcode values like "your-secret-key"

---
### Essential Security Controls 

For session cookies there are some security controls:
- HttpOnly = True
    - prevents client-side JavaScript (document.cookie) from accessing the cookie, mitigating Cross-Site Scripting (XSS) token theft.
- SameSite = "Lax" / "Strict"
    - restricts cookie transmission on cross-site requests, mitigating Cross-Site Request Forgery (CSRF) attacks.
- Secure = True
    - enforces cookie transmission exclusively over encrypted HTTPS connections.
- Session Fixation Defense
    - regenerates new session UUID tokens upon authentication state changes (e.g., login or privilege escalation)

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Sessions

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Sessions
