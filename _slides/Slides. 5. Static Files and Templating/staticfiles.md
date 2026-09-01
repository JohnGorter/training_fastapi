# Static files

---
### Static files

Static assets (CSS, JavaScript, images) are served directly from the filesystem but: 
**you have to mount a directory**

---
### Mounting static files

Mounting binds an isolated directory on disk to an HTTP route prefix (e.g., /static)

Real-World Use Case
- serving client-side assets like stylesheets, JavaScript libraries, logos, or public PDF downloads

Behavior
- staticFiles bypasses FastAPI route parsing entirely, handling GET requests, HTTP caching headers (ETag, Cache-Control), and byte ranges directly from disk

```
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mounts the local 'static' folder to the '/static' URL route
app.mount("/static", StaticFiles(directory="static"), name="static")
```

---
### Using the API from static files

FastAPI serves vanilla JavaScript files directly through StaticFiles middleware

Client-side JavaScript running in the browser interacts with FastAPI backend endpoints using browser-native APIs like fetch() and WebSocket

---
### Serving Client-Side Scripts (StaticFiles)

Mounting a static directory exposes JavaScript assets to the browser. The frontend links scripts using path relative URLs or Jinja2's url_for('static', path='...')

Real-World Use Case
- loading modular UI logic, form validators, or WebSocket client drivers without needing a Node.js build pipeline or bundler

Behavior
- the browser downloads .js files via HTTP GET, executing them inside the document object model (DOM) context

```
# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
```

```
<!-- templates/index.html -->
<script src="{{ url_for('static', path='js/main.js') }}" defer></script>
```

---
### Query & Path Parameters in fetch() Requests

Vanilla JS constructs dynamic URLs containing Path variables (/api/items/101) and Query strings (?search=laptop&page=1) to consume FastAPI endpoints

Real-World Use Case
- live autocomplete search bars or paginated data tables

Behavior
- URLSearchParams formats key-value pairs into valid query strings that map directly to FastAPI's scalar function parameters.

```
// static/js/search.js
async function searchProducts(query, page = 1) {
    const params = new URLSearchParams({ q: query, page: page });
    
    // Calls @app.get("/api/products/search") with Query parameters
    const response = await fetch(`/api/products/search?${params.toString()}`);
    const data = await response.json();
    console.log("Found products:", data);
}
```

---
### Sending JSON Bodies & Consuming Response Models

JavaScript serializes client object states using JSON.stringify() and dispatches them via HTTP POST/PUT 

FastAPI decodes the JSON payload into Pydantic models and returns filtered response_model outputs

Real-World Use Case
- submitting user forms, shopping cart updates, or settings payloads

Behavior
- requiring headers: { 'Content-Type': 'application/json' } tells FastAPI's request body parser to process the body into a Pydantic BaseModel

```
// static/js/checkout.js
async function submitOrder(cartItems) {
    const response = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: cartItems })
    });

    // Parsed response strictly conforms to FastAPI's response_model
    const orderConfirmation = await response.json();
    return orderConfirmation;
}
```

---
### Error Handling (HTTPException & Status Codes)

Browsers do not automatically throw errors on HTTP 4xx or 5xx responses. JavaScript inspects response.ok and reads FastAPI's standard detail JSON error structure

Real-World Use Case
- displaying contextual error messages (e.g., "404 Not Found" or Pydantic "422 Unprocessable Entity" field failures) in the browser UI

Behavior
- when FastAPI raises HTTPException(status_code=400, detail="..."), the payload is exposed on await response.json()

```
// static/js/api_client.js
async function fetchUser(userId) {
    const response = await fetch(`/api/users/${userId}`);

    if (!response.ok) {
        // Reads FastAPI HTTPException output: {"detail": "User not found"}
        const errorData = await response.json();
        throw new Error(`Error ${response.status}: ${errorData.detail}`);
    }

    return await response.json();
}
```

---
### OAuth2 Bearer Token Authentication Lifecycle

Client JS handles the full authentication loop
- POSTing credentials as application/x-www-form-urlencoded data to /authorize
- Exchanging the returned CODE for an access and id token (JWT)
- storing the returned JWT
- injecting Authorization: Bearer token into future API calls

Real-World Use Case 
- single-page frontend interactions on protected routes without full page reloads

Behavior
- standardizes client-side security headers across all state-modifying requests.

```
// static/js/pkce_auth.js

// 1. Step 1: Request Authorization Code
async function initiateOAuthLogin() {

    // Redirect or fetch authorization code
    const params = new URLSearchParams({
        response_type: "code",
        client_id: "vanilla_js_client",
        redirect_uri: `${window.location.origin}/`
    });
    
    window.location.href = `/authorize?${params.toString()}`;
}

// 2. Step 2: Exchange Auth Code for Bearer Token
async function handleCodeExchange(authCode) {
    const payload = new URLSearchParams({
        grant_type: "authorization_code",
        code: authCode,
        client_id: "vanilla_js_client"
    });

    const response = await fetch("/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: payload
    });

    const data = await response.json();
    sessionStorage.setItem("access_token", data.access_token);
}
```

---
###  Proof Key for Code Exchange 

PKCE stands for Proof Key for Code Exchange (pronounced "pixie").

It is a security extension for the OAuth 2.0 Authorization Code Flow designed to prevent authorization code interception attacks, especially in public clients like mobile applications and browser-based single-page apps (SPAs) where client secrets cannot be securely hidden

Real-World Use Case
- securing browser-initiated single-page applications against code-interception attacks without storing hardcoded client secrets

Behavior
- the server verifies that the SHA-256 hash of the incoming code_verifier matches the code_challenge registered during the initial authorization request

```
// static/js/pkce_auth.js

// 1. Generate PKCE Verifier and SHA-256 Challenge
function generateRandomString(length) {
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    return Array.from(array, b => b.toString(16).padStart(2, '0')).join('');
}

async function sha256(plain) {
    const encoder = new TextEncoder();
    const data = encoder.encode(plain);
    const hash = await window.crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode(...new Uint8Array(hash)))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// 2. Step 1: Request Authorization Code
async function initiateOAuthLogin() {
    const codeVerifier = generateRandomString(32);
    sessionStorage.setItem("pkce_verifier", codeVerifier);
    const codeChallenge = await sha256(codeVerifier);

    // Redirect or fetch authorization code
    const params = new URLSearchParams({
        response_type: "code",
        client_id: "vanilla_js_client",
        redirect_uri: `${window.location.origin}/`,
        code_challenge: codeChallenge,
        code_challenge_method: "S256"
    });
    
    window.location.href = `/authorize?${params.toString()}`;
}

// 3. Step 2: Exchange Auth Code for Bearer Token
async function handleCodeExchange(authCode) {
    const codeVerifier = sessionStorage.getItem("pkce_verifier");

    const payload = new URLSearchParams({
        grant_type: "authorization_code",
        code: authCode,
        client_id: "vanilla_js_client",
        code_verifier: codeVerifier
    });

    const response = await fetch("/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: payload
    });

    const data = await response.json();
    sessionStorage.setItem("access_token", data.access_token);
    sessionStorage.removeItem("pkce_verifier");
}
```

---
### Native WebSocket Integration

Browser-native WebSocket objects establish persistent, full-duplex channels with FastAPI @app.websocket endpoints, handling JSON encoding and connection events.

Real-World Use Case: Live chat feeds, stock tickers, or push notification toasts.

Behavior: Passes authentication tokens via query parameters during connection instantiation (new WebSocket("ws://...?token=XYZ")).

JavaScript
// static/js/stream.js
function connectToLiveStream(roomId, token) {
    const ws = new WebSocket(`ws://${location.host}/ws/rooms/${roomId}?token=${token}`);

    ws.onopen = () => console.log("Connected to live stream");
    
    ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        console.log("Server update:", payload);
    };

    ws.onclose = () => console.log("Connection closed");
    
    return ws;
}
Unified Full-Stack Implementation

This production pattern combines FastAPI static file serving, Jinja2 rendering, OAuth2 token authentication, Pydantic validation, status handling, and WebSocket streaming with a vanilla JavaScript frontend client.

Directory Structure:

Plaintext
project/
├── static/
│   └── js/
│       └── app.js
├── templates/
│   └── dashboard.html
└── main.py
main.py (FastAPI Application Server)

Python
from datetime import datetime, timezone
from typing import Annotated
import jwt
from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

SECRET_KEY = "enterprise-secret-key"
ALGORITHM = "HS256"

app = FastAPI()

# 1. Mount Static Files & Config Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Pydantic Schemas
class TaskCreate(BaseModel):
    title: str = Field(min_length=3)
    priority: str = "medium"

class TaskResponse(BaseModel):
    id: int
    title: str
    priority: str
    created_at: str

# In-Memory DB & WS Pool
TASKS_DB = []
ACTIVE_WEBSOCKETS: list[WebSocket] = []

# Auth Helper
def create_jwt(subject: str) -> str:
    return jwt.encode({"sub": subject, "exp": datetime.now(timezone.utc).timestamp() + 3600}, SECRET_KEY, algorithm=ALGORITHM)

# 2. Page Route
@app.get("/")
async def render_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})

# 3. Authentication Endpoint
@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if form_data.username != "admin" or form_data.password != "secret":
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"access_token": create_jwt(form_data.username), "token_type": "bearer"}

# 4. JSON REST Endpoint
@app.post("/api/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    token: Annotated[str, Depends(oauth2_scheme)]
):
    new_task = {
        "id": len(TASKS_DB) + 1,
        "title": task.title,
        "priority": task.priority,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    TASKS_DB.append(new_task)
    
    # Broadcast event to WebSockets
    for ws in ACTIVE_WEBSOCKETS:
        await ws.send_json({"event": "TASK_CREATED", "data": new_task})

    return new_task

# 5. WebSocket Real-Time Endpoint
@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket, token: Annotated[str | None, Query()] = None):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await websocket.accept()
    ACTIVE_WEBSOCKETS.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        ACTIVE_WEBSOCKETS.remove(websocket)
templates/dashboard.html (Jinja2 HTML Container)

HTML
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Task Board</title>
    <!-- Load Static JavaScript Client -->
    <script src="{{ url_for('static', path='js/app.js') }}" defer></script>
</head>
<body>
    <h1>Task Operations Board</h1>
    
    <!-- Login Section -->
    <section id="login-section">
        <h3>Authentication</h3>
        <input type="text" id="username" placeholder="Username (admin)">
        <input type="password" id="password" placeholder="Password (secret)">
        <button id="login-btn">Login</button>
        <p id="auth-status" style="color: gray;"></p>
    </section>

    <hr>

    <!-- Protected Task Form -->
    <section id="task-section" style="display: none;">
        <h3>Create Task</h3>
        <input type="text" id="task-title" placeholder="Task Title (min 3 chars)">
        <select id="task-priority">
            <option value="low">Low</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High</option>
        </select>
        <button id="create-task-btn">Submit Task</button>
        <p id="error-output" style="color: red;"></p>

        <h3>Live Activity Feed</h3>
        <ul id="events-list"></ul>
    </section>
</body>
</html>
static/js/app.js (Vanilla Client Application)

JavaScript
// Application State
let authToken = sessionStorage.getItem("access_token") || null;
let socket = null;

// DOM Elements
const loginSection = document.getElementById("login-section");
const taskSection = document.getElementById("task-section");
const authStatus = document.getElementById("auth-status");
const errorOutput = document.getElementById("error-output");
const eventsList = document.getElementById("events-list");

// 1. Authentication Handler
document.getElementById("login-btn").addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const payload = new URLSearchParams();
    payload.append("username", username);
    payload.append("password", password);

    try {
        const response = await fetch("/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: payload
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail);
        }

        const data = await response.json();
        authToken = data.access_token;
        sessionStorage.setItem("access_token", authToken);
        
        authStatus.innerText = "Authenticated successfully!";
        initializeDashboard();
    } catch (err) {
        authStatus.innerText = `Auth Error: ${err.message}`;
    }
});

// 2. Protected REST Request Handler
document.getElementById("create-task-btn").addEventListener("click", async () => {
    errorOutput.innerText = "";
    const title = document.getElementById("task-title").value;
    const priority = document.getElementById("task-priority").value;

    try {
        const response = await fetch("/api/tasks", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify({ title, priority })
        });

        // Handle Status Codes and Pydantic 422 Errors
        if (!response.ok) {
            const errorData = await response.json();
            if (response.status === 422) {
                // Pydantic validation failures
                throw new Error(`Validation Error: ${errorData.detail[0].msg}`);
            }
            throw new Error(errorData.detail || "Failed to create task");
        }

        document.getElementById("task-title").value = "";
    } catch (err) {
        errorOutput.innerText = err.message;
    }
});

// 3. WebSocket Real-Time Connection Setup
function connectWebSocket() {
    socket = new WebSocket(`ws://${location.host}/ws/events?token=${authToken}`);

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.event === "TASK_CREATED") {
            const li = document.createElement("li");
            li.innerText = `[${message.data.priority.toUpperCase()}] ${message.data.title} - ${message.data.created_at}`;
            eventsList.prepend(li);
        }
    };

    socket.onclose = () => console.log("WebSocket disconnected.");
}

// 4. Initialization Logic
function initializeDashboard() {
    if (authToken) {
        loginSection.style.display = "none";
        taskSection.style.display = "block";
        connectWebSocket();
    }
}

// Auto-boot on page load if token exists
initializeDashboard();
Execution Pipeline Explanation:

Static JS Ingestion: The browser fetches /static/js/app.js via the StaticFiles engine mounted at /static.

Authentication & Storage: The user clicks Login. app.js posts form data to /token. Upon success, the returned JWT is saved into sessionStorage.

Authenticated REST Execution: Submitting a task sends a JSON POST request to /api/tasks with the Authorization: Bearer <token> header attached. If the title is under 3 characters, FastAPI returns HTTP 422, which app.js catches and renders in red.

Real-Time Broadcast Push: When a valid task is created, FastAPI iterates through ACTIVE_WEBSOCKETS and broadcasts a JSON payload. The open WebSocket connection in app.js receives onmessage, dynamically appending the new item to the DOM without requiring a page reload.

<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Static files

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Static Files