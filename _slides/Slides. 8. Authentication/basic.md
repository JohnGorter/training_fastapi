# Basic Authentication

FastAPI provides native security utilities built on top of Starlette and OpenAPI standards to implement authentication (who you are) and authorization (what you are allowed to do).

---
### HTTP Basic Authentication (HTTPBasic)

HTTP Basic authentication transmits credentials as a Base64-encoded username:password string in the Authorization request header (Authorization: Basic dXNlcjpwYXNz)

Real-World Use Case
- protecting simple internal administration dashboards, status pages, or legacy service-to-service calls

Behavior 
- browsers automatically display a native credential popup when a route protected by HTTPBasic returns an HTTP 401 response with the WWW-Authenticate: Basic header

```
import secrets
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()
security = HTTPBasic()

def authenticate_admin(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_user = secrets.compare_digest(credentials.username, "admin")
    correct_pass = secrets.compare_digest(credentials.password, "secret123")
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/admin/system-status")
async def get_system_status(user: Annotated[str, Depends(authenticate_admin)]):
    return {"status": "ok", "authenticated_as": user}
```

---
### Secrets.compare_digest

This function performs a constant-time string comparison between credentials.password and "secret123" to prevent side-channel timing attacks

Why Regular == Is Vulnerable:
- Short-Circuit Evaluation: Standard Python equality checks (a == b) compare characters sequentially and stop the moment they encounter a mismatch
- Timing Attacks: 
    - if an attacker sends "sXXXXX", the comparison fails on index 1. If they send "seXXXX", it fails on index 2, taking a fraction of a nanosecond longer 
    - by measuring microscopic response-time differences across thousands of requests, an attacker can guess a password one character at a time

---
### secrets.compare_digest (2) 

How compare_digest Fixes It?

- constant Execution Time: secrets.compare_digest() iterates through the entire length of both strings regardless of where mismatches occur
- Identical Latency: Whether 0 characters match or all characters match, the function takes the exact same amount of time to execute, erasing the timing signal required for side-channel exploits.

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Basic Authentication

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Basic Authentication
