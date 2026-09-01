# Lifespan

---
### Lifespan 

FastAPI’s lifespan context manager handles application startup and shutdown operations using Python's contextlib.asynccontextmanager

- it replaces legacy @app.on_event decorators with an asynchronous generator 
    - code preceding yield executes on application startup 
    - code following yield executes during graceful shutdown

---
### Basic Lifespan Anatomy 

A lifespan function wraps the application lifecycle
- the yield keyword splits the function into startup execution (before yield) and shutdown execution (after yield)

Real-World Use Case:
- initializing local configuration settings or printing deployment environment diagnostics when the ASGI server boots

Behavior
- the ASGI server (e.g., Uvicorn) blocks incoming HTTP requests until code prior to yield completes successfully. When the server receives a shutdown signal (SIGTERM or SIGINT), code after yield executes before the process terminates

---
### Basic Lifespan Anatomy 

```
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print("Application booting up: Warming caches...")
    
    yield  # Application handles incoming HTTP requests here
    
    # --- SHUTDOWN LOGIC ---
    print("Application stopping: Releasing resources...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "online"}
```

---
### Shared State & Dependency Storage 

The lifespan function receives the app instance, allowing startup tasks to attach shared resources directly to app.state. 

- routes access these resources via request.state

Real-World Use Case
- instantiating a single HTTP client (httpx.AsyncClient) at startup to reuse TCP connections across out-of-process API requests

Behavior
- eliminates fragile global variables by binding long-lived client instances directly to the application context

---
### Shared State & Dependency Storage 

```
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Instantiate single persistent HTTP client on startup
    app.state.http_client = httpx.AsyncClient(timeout=5.0)
    
    yield
    
    # Close HTTP connection pool cleanly on shutdown
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/external-data")
async def get_data(request: Request):
    # Retrieve the shared client instance from request.state
    client: httpx.AsyncClient = request.state.http_client
    response = await client.get("https://api.github.com")
    return {"status_code": response.status_code}
```

---
### Exception Safety & Teardown Guarantees 

Wrapping lifespan operations in a try...finally block ensures that cleanup tasks run even if an unhandled exception occurs while running the application or processing startup procedures

Real-World Use Case
- If an application component crashes, safely close
- file handles
- temporary socket connections
- background workers 

Behavior
- i an error occurs after startup, execution jumps directly to the finally block, executing cleanup logic before process termination

---
### Exception Safety & Teardown Guarantees 

```
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing system locks...")
    try:
        # Simulate startup step
        yield
    finally:
        # Guaranteed teardown execution regardless of errors
        print("Cleaning up system locks and flushing logs.")

app = FastAPI(lifespan=lifespan)
```

---
### Async Database Engines & Cache Pool Lifecycles

Lifespan manages the startup and teardown of asynchronous database connection pools (SQLAlchemy create_async_engine) and cache clients (redis.asyncio)

Real-World Use Case
- opening a database connection pool when the web server starts up and closing all connections on shutdown to prevent leaked database sockets

Behavior
- connects to infrastructure resources before accepting traffic and drains active connection pools cleanly during rolling deployments

---
### Async Database Engines & Cache Pool Lifecycles

```
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///app.db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Async Database Engine & Session Factory
    engine = create_async_engine(DATABASE_URL, echo=False)
    app.state.db_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    yield
    
    # 2. Dispose database engine connection pool on shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

---
### Unified Enterprise Lifespan Infrastructure

This production pattern demonstrates a complete lifespan manager handling machine learning model weights, an asynchronous database connection pool, a shared httpx HTTP client, and an in-memory Redis connection pool attached to app.state

```
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select
from pydantic import BaseModel
import httpx
import redis.asyncio as aioredis

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & ORM MODELS
# ---------------------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///enterprise_lifespan.db"
REDIS_URL = "redis://localhost:6379"

class Base(DeclarativeBase):
    pass

class UserAuditORM(Base):
    __tablename__ = "user_audits"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column()
    action: Mapped[str] = mapped_column()

# Dummy Machine Learning Model
class PredictionModel:
    def load_weights(self):
        self.is_ready = True
    def predict(self, text: str) -> float:
        return 0.95 if "good" in text.lower() else 0.10

# ---------------------------------------------------------------------
# 2. LIFESPAN MANAGER
# ---------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # === STARTUP PHASE ===
    print("Starting Enterprise Services...")
    
    # A. Initialize Database Engine & Schema
    db_engine = create_async_engine(DATABASE_URL, echo=False)
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.db_session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    app.state.db_engine = db_engine

    # B. Initialize Shared HTTP Client
    app.state.http_client = httpx.AsyncClient(timeout=10.0)

    # C. Initialize Redis Connection Pool
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    # D. Load Machine Learning Model Weights
    ml_model = PredictionModel()
    ml_model.load_weights()
    app.state.ml_model = ml_model

    print("All enterprise infrastructure online. Accepting requests.")
    
    try:
        yield  # Server serves requests
    finally:
        # === SHUTDOWN PHASE ===
        print("Shutting down Enterprise Services...")
        
        # Close HTTP Client
        await app.state.http_client.aclose()
        
        # Close Redis Client
        await app.state.redis.close()
        
        # Dispose Database Connection Pool
        await app.state.db_engine.dispose()
        
        print("Cleanup complete. Server stopped.")

app = FastAPI(title="Enterprise Lifespan App", lifespan=lifespan)

# ---------------------------------------------------------------------
# 3. DEPENDENCY INJECTION HELPERS
# ---------------------------------------------------------------------
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_factory: async_sessionmaker = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_ml_model(request: Request) -> PredictionModel:
    return request.app.state.ml_model

def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

# ---------------------------------------------------------------------
# 4. PATH OPERATIONS CONSUMING LIFESPAN RESOURCES
# ---------------------------------------------------------------------
class PredictRequest(BaseModel):
    text: str
    username: str

@app.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_sentiment(
    payload: PredictRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    model: Annotated[PredictionModel, Depends(get_ml_model)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
):
    # 1. Run inference using ML Model loaded at startup
    score = model.predict(payload.text)

    # 2. Log audit record in Database using pool created at startup
    audit_entry = UserAuditORM(username=payload.username, action=f"ANALYZE_SCORE_{score}")
    db.add(audit_entry)

    return {
        "text": payload.text,
        "sentiment_score": score,
        "model_status": "ready" if model.is_ready else "not_loaded"
    }
```

---
### Execution Pipeline Explanation

- Startup Sequence Execution: When Uvicorn boots the app, the code prior to yield inside lifespan executes sequentially:
    - Creates database tables and attaches the SQLAlchemy AsyncEngine and session factory to app.state
    - Instantiates an httpx.AsyncClient session pool and attaches it to app.state.http_client
    - Establishes an async Redis connection pool and stores it in app.state.redis
    - Loads heavy ML model weights in memory and stores the instance in app.state.ml_model
- Request Handling: When /analyze receives a request, dependency providers (get_db, get_ml_model, get_http_client) extract the pre-initialized instances directly from request.app.state
- Zero-Allocation Endpoint Execution: The endpoint runs inference using the pre-loaded ML model and queries the database via the existing connection pool without re-instantiating engines or reloading weights per request
- Graceful Shutdown Sequence: When the server receives a termination signal, execution jumps to the finally block post-yield. It closes http_client, closes the redis connection, and disposes of the db_engine connection pool before the Python process terminates

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Lifespan

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Lifespan