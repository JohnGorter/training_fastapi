# Deployment

---
### Deployment

FastAPI applications require an ASGI server (such as Uvicorn or Granian) to translate HTTP requests into asynchronous Python coroutines

In production, these ASGI servers run behind a reverse proxy (like Nginx, Traefik, or AWS ALB) inside containerized environments managed by Kubernetes, Docker Swarm, or Cloud Run

---
### Production ASGI Execution (Gunicorn + Uvicorn Workers)

Uvicorn runs single-process async loops during development 
Gunicorn spawns and manages multiple Uvicorn worker processes across CPU cores.

Real-World Use Case
- scaling API request handling horizontally across CPU cores on AWS EC2, bare-metal servers, or virtual machines

Behavior
- Gunicorn acts as the master process manager, monitoring worker health and restarting crashed processes, while each UvicornWorker runs an isolated asyncio event loop

```
# gunicorn.conf.py
import multiprocessing

# Worker Process Count: (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Bind address and port
bind = "0.0.0.0:8000"

# Timeouts & Keep-Alive
keepalive = 65
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

Execution Command
```
gunicorn -c gunicorn.conf.py app.main:app
```

---
### Reverse Proxying & Trusted Headers 

Production APIs sit behind reverse proxies (Nginx, Traefik, Cloudflare) that handle 
- TLS/SSL termination
- HTTP/2 multiplexing
- DDoS filtering

The proxy forwards client metadata to FastAPI via HTTP headers (X-Forwarded-For, X-Forwarded-Proto)

Real-World Use Case
- ensuring request.client.host and url_for() correctly reflect the end-user's real IP address and https:// scheme instead of the proxy's internal container IP (172.x.x.x)

Behavior
- proxyHeadersMiddleware inspects forwarding headers and updates the ASGI scope before request processing.

```
from fastapi import FastAPI, Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

app = FastAPI()

# Trust headers forwarded by reverse proxies (e.g., Nginx or AWS ALB)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["10.0.0.0/8", "172.16.0.0/12", "127.0.0.1"])

@app.get("/client-ip")
async def get_client_ip(request: Request):
    # Returns the actual client IP, not the reverse proxy IP
    return {
        "client_ip": request.client.host,
        "scheme": request.url.scheme
    }
```

---
### Multi-state Dockerfile

A multi-stage Dockerfile uses multiple FROM instructions within a single file to divide a container build into distinct stages, separating the build environment from the final execution environment

You compile dependencies or assets in an early build stage, then selectively copy only the required artifacts (COPY --from=<stage>) into a fresh, minimal runtime image

Key Advantages: 
- drastically Smaller Image Size
- single Source of Truth 

---
### Single-Stage vs. Multi-Stage 

|Feature| Single-Stage DockerfileM|ulti-Stage Dockerfile|
Final Image Size|Large (contains compilers, dev tools, build cache)|Minimal (contains only runtime binaries & dependencies)|
|Attack Surface|High (package managers and dev tools remain accessible)|Low (minimal binaries; can run as an unprivileged user)|
|Build Cleanup|Requires complex, error-prone && rm -rf cleanup chains|Automatic (discarded intermediate stages are purged)|

---
### Anatomy of a Multi-Stage BuildDockerfile

```
=====================================================================
# STAGE 1: Builder (Heavy build environment)
# =====================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install OS build tools required for compiling C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Compile and install Python dependencies to a separate directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# =====================================================================
# STAGE 2: Runtime (Minimal production environment)
# =====================================================================
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy ONLY the pre-compiled Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application code into the clean container
COPY ./app /app/app

# Run as a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

When Docker builds this image, it uses Stage 1 (builder) to download compilers and build native C extensions. Once complete, Docker discards the entire builder image layer and starts fresh with Stage 2 (runner), copying only the resulting /install folder into the final container

---
### Containerization Best Practices 

Multi stage Docker builds separate build-time dependencies (compilers, git, build toolchains) from the runtime environment. This produces minimal image sizes, reduces attack surface area, and enforces non-root execution security

Real-World Use Case
- package optimization for rapid CI/CD container registry pushes and Kubernetes pod deployments

Behavior
- build dependencies are compiled in a temporary builder image
- final artifacts are copied into a clean, unprivileged execution container


Dockerfile
```
# =====================================================================
# STAGE 1: Builder Image
# =====================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# =====================================================================
# STAGE 2: Final Runtime Image
# =====================================================================
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/install/bin:$PATH"

# Copy installed Python packages from builder
COPY --from=builder /install /install

# Copy application code
COPY ./app /app/app
COPY ./gunicorn.conf.py /app/gunicorn.conf.py

# Security Hardening: Create unprivileged non-root user
RUN useradd -m -u 10001 appuser && \
    chown -R appuser:appuser /app
USER 10001

EXPOSE 8000

# Exec form guarantees UNIX signals (SIGTERM/SIGINT) pass directly to Gunicorn
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
```

---
### Liveness & Readiness Health Probes

Orchestration platforms (Kubernetes, AWS ECS, Google Cloud Run) rely on HTTP health probes to determine when to route traffic to a container or restart a malfunctioning pod.

Liveness Probe (/healthz/live): Verifies the web server process is running. If it fails, the orchestrator kills and restarts the container.

Readiness Probe (/healthz/ready): Verifies backend dependencies (Database, Redis, external APIs) are connected. If it fails, the orchestrator removes the pod from service load balancers until connections recover.

Python
from typing import Annotated
from fastapi import FastAPI, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

app = FastAPI()

@app.get("/healthz/live", status_code=status.HTTP_200_OK, tags=["Probe"])
async def liveness_probe():
    """Basic process health check."""
    return {"status": "alive"}

@app.get("/healthz/ready", tags=["Probe"])
async def readiness_probe(response: Response, db: Annotated[AsyncSession, Depends(get_db)]):
    """Deep health check validating infrastructure connections."""
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "database": "disconnected"}
Unified Production FastAPI Deployment Suite

This complete suite provides a production-grade FastAPI web service featuring a Lifespan connection pool manager, Liveness/Readiness endpoints, Reverse Proxy header handling, Async Database & Redis integration, and a Gunicorn Process Configuration.

app/main.py

Python
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends, Response, status, Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import redis.asyncio as aioredis

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & LIFESPAN MANAGEMENT
# ---------------------------------------------------------------------
SQL_URL = "sqlite+aiosqlite:///production.db"
REDIS_URL = "redis://localhost:6379"

sql_engine = create_async_engine(SQL_URL, echo=False, pool_pre_ping=True)
session_factory = async_sessionmaker(sql_engine, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis Pool & Database Connection
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    yield
    # Graceful Shutdown: Drain and dispose connection pools
    await app.state.redis.close()
    await sql_engine.dispose()

app = FastAPI(title="Production Gateway API", lifespan=lifespan)

# Add Proxy Headers Middleware for reverse proxies (Nginx/Traefik/ALB)
app.add_middleware(
    ProxyHeadersMiddleware, 
    trusted_hosts=["10.0.0.0/8", "172.16.0.0/12", "127.0.0.1"]
)

# Database Session Dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ---------------------------------------------------------------------
# 2. HEALTH PROBES & METRICS
# ---------------------------------------------------------------------
@app.get("/healthz/live", status_code=status.HTTP_200_OK, tags=["Probes"])
async def liveness_check():
    """Liveness probe: Checks if container process is running."""
    return {"status": "UP"}

@app.get("/healthz/ready", tags=["Probes"])
async def readiness_check(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Readiness probe: Validates database and cache connectivity."""
    health_status = {"status": "UP", "checks": {}}
    is_healthy = True

    # 1. Verify SQL Database
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "OK"
    except Exception as exc:
        health_status["checks"]["database"] = f"UNHEALTHY: {str(exc)}"
        is_healthy = False

    # 2. Verify Redis Cache
    try:
        redis: aioredis.Redis = request.app.state.redis
        await redis.ping()
        health_status["checks"]["redis"] = "OK"
    except Exception as exc:
        health_status["checks"]["redis"] = f"UNHEALTHY: {str(exc)}"
        is_healthy = False

    if not is_healthy:
        health_status["status"] = "DOWN"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_status

# ---------------------------------------------------------------------
# 3. PRODUCTION BUSINESS ROUTE
# ---------------------------------------------------------------------
@app.get("/api/v1/data")
async def get_production_data(request: Request):
    return {
        "message": "Serving production workload",
        "client_ip": request.client.host,
        "scheme": request.url.scheme
    }
gunicorn.conf.py (Production Process Manager Config)

Python
import multiprocessing

# Worker Process Pool: 2 * Cores + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Socket Binding
bind = "0.0.0.0:8000"

# Process Naming
proc_name = "fastapi_production_gateway"

# Graceful Shutdown Timeout (Seconds allowed for background tasks/requests to finish)
graceful_timeout = 30
timeout = 60
keepalive = 65

# Log Management
accesslog = "-"
errorlog = "-"
loglevel = "info"
Execution Pipeline Explanation:

Deployment Initialization: The multi-stage Dockerfile compiles binary dependencies in a builder stage, discards build tools, copies runtime packages into a minimal Python environment, assigns ownership to an unprivileged appuser (UID 10001), and executes Gunicorn via JSON array syntax (CMD ["gunicorn", ...]).

Process Management: Gunicorn launches master process workers (UvicornWorker). Each worker initializes Python's asyncio event loop and invokes FastAPI's lifespan handler to open async connection pools for PostgreSQL/SQLite and Redis.

Reverse Proxy Ingestion: Incoming HTTPS requests terminate at Nginx or AWS ALB. The proxy injects X-Forwarded-For and X-Forwarded-Proto headers. ProxyHeadersMiddleware rewrites the ASGI scope so request.client.host reflects the actual remote client IP.

Orchestrator Probing: Kubernetes continuously monitors container lifecycle state:

Queries /healthz/live every 10 seconds. If workers freeze, Kubernetes restarts the pod.

Queries /healthz/ready. If Redis or PostgreSQL drops connections, the endpoint returns HTTP 503, causing the ingress controller to drop the container from active traffic routing until dependencies recover.