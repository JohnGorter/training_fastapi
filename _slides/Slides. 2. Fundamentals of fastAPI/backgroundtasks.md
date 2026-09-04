
# Background tasks

---
### Background tasks

FastAPI’s BackgroundTasks allows you to schedule tasks to run after returning an HTTP response

**Because tasks execute after the HTTP payload is dispatched to the client, operations like sending emails, logging analytics, or triggering webhooks do not delay client response latency!**

---
### Basic Background Execution 

Adding BackgroundTasks as a route parameter gives access to .add_task():
- pass the function reference and its arguments
- FastAPI executes it after the HTTP response stream closes

Real-World Use Case
- sending welcome emails or dispatching push notifications without making the user wait for external SMTP or network latency

Behavior
- if the target function is defined as standard def, FastAPI runs it inside an internal thread pool
- if defined as async def, it runs directly on the asyncio event loop after the response is sent

---
### Basic Background Execution 

```
import time
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, EmailStr

app = FastAPI()

def send_welcome_email(email: str):
    # Simulate slow SMTP network transmission
    time.sleep(2.0)
    print(f"[BACKGROUND] Welcome email sent successfully to {email}")

class UserSignup(BaseModel):
    email: EmailStr

@app.post("/signup", status_code=202)
async def signup_user(
    payload: UserSignup, 
    background_tasks: BackgroundTasks
):
    # Schedule background execution
    background_tasks.add_task(send_welcome_email, email=payload.email)
    
    # Returns immediately to client while email sends in background
    return {"status": "accepted", "message": "Account created. Email processing."}
```

---
### Scoped Database Connection Management

Background tasks run outside the HTTP request-response lifecycle
- attempting to re-use request-scoped dependencies in a background task will fail because the session closes as soon as the HTTP response finishes

Real-World Use Case
- persisting audit logs or updating user usage metrics in the database asynchronously after an API call completes

Behavior
- background tasks must instantiate their own independent database sessions using the application's session factory

---
### Scoped Database Connection Management

```
from typing import Annotated
from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///app.db")
session_factory = async_sessionmaker(engine, expire_on_commit=False)

# Dedicated worker function creating its own session
async def log_audit_trail_task(user_id: str, action: str):
    async with session_factory() as session:
        # Perform independent DB write operation
        print(f"[AUDIT DB] Persisted action '{action}' for user {user_id}")

app = FastAPI()

@app.post("/action")
async def execute_action(
    user_id: str, 
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(log_audit_trail_task, user_id=user_id, action="FILE_DOWNLOAD")
    return {"status": "success"}
```

---
### Internal Exception Handling & Retries

Because background tasks execute after the HTTP response has been sent, exceptions raised inside background functions cannot be caught by HTTP exception handlers or return 500 status codes to the client

Real-World Use Case
- retrying failed external webhook deliveries without causing unhandled background worker crashes

Behavior
- all background functions must manage internal errors using explicit try...except blocks and internal retry loops or fallback logging

---
### Internal Exception Handling & Retries

```
import logging
import asyncio
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()
logger = logging.getLogger("BackgroundWorker")

async def dispatch_webhook_with_retry(url: str, payload: dict, retries: int = 3):
    for attempt in range(1, retries + 1):
        try:
            print(f"[WEBHOOK] Attempt {attempt}: Sending to {url}")
            # Simulate transient network failure
            if attempt < 3:
                raise ConnectionError("Network timeout")
            
            print(f"[WEBHOOK] Delivery successful to {url}")
            return
        except Exception as exc:
            logger.warning(f"[WEBHOOK ERROR] Attempt {attempt} failed: {exc}")
            await asyncio.sleep(1.0) # Wait before retry
            
    logger.error(f"[WEBHOOK FATAL] All {retries} delivery attempts failed for {url}")

@app.post("/trigger-webhook")
async def trigger_webhook(target_url: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        dispatch_webhook_with_retry, 
        url=target_url, 
        payload={"event": "ORDER_COMPLETED"}
    )
    return {"status": "webhook_queued"}
```

---
### Architecture

In-Process BackgroundTasks vs. External Distributed Queues

|Architectural Criteria|In-Process BackgroundTasks (FastAPI)|External Distributed Queue (Celery / ARQ / Dramatiq)|
|---|---|---|
|Execution Context|Runs inside the same Uvicorn/ASGI process worker|Runs in separate, dedicated worker processes/nodes|
|Infrastructure|Zero extra setup (Built into FastAPI/Starlette)|Requires message broker (Redis/RabbitMQ) + worker management|
|Persistence|In-memory|Persistent|
|Workload Suitability|Fast I/O tasks (< 5 sec) like emails, webhooks, or simple DB writes|Heavy CPU tasks (image processing, ML inference) or long jobs|

---
### Unified Enterprise Order Processing & Async Worker Pipeline

The following production pattern demonstrates an order ingestion service. The endpoint returns an immediate HTTP 202 Accepted response while delegating audit logging, external payment notification webhooks via httpx, and analytics metrics calculation to background tasks using an independent database session.

---
### Unified Enterprise Order Processing & Async Worker Pipeline

```
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel, EmailStr, Field
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EnterpriseWorker")

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & LIFESPAN MANAGEMENT
# ---------------------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///enterprise_tasks.db"

engine = create_async_engine(DATABASE_URL, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class OrderORM(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_email: Mapped[str] = mapped_column()
    amount: Mapped[float] = mapped_column()
    status: Mapped[str] = mapped_column(default="PROCESSING")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database Tables & Shared HTTP Client
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    
    yield
    
    # Cleanup resources on shutdown
    await app.state.http_client.aclose()
    await engine.dispose()

app = FastAPI(title="Order Ingestion Gateway", lifespan=lifespan)

# Database Session Dependency for Route Handlers
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ---------------------------------------------------------------------
# 2. PYDANTIC SCHEMAS
# ---------------------------------------------------------------------
class OrderRequest(BaseModel):
    customer_email: EmailStr
    amount: float = Field(gt=0.0)
    webhook_url: str

class OrderAcceptedResponse(BaseModel):
    order_id: int
    status: str
    message: str

# ---------------------------------------------------------------------
# 3. BACKGROUND WORKER ROUTINES
# ---------------------------------------------------------------------
async def process_post_order_tasks(
    order_id: int, 
    customer_email: str, 
    webhook_url: str, 
    http_client: httpx.AsyncClient
):
    """Executes asynchronous post-processing: DB updates and external webhooks."""
    logger.info(f"[TASK START] Processing order #{order_id}")

    # Task Component A: Database update using an independent worker session
    async with session_factory() as db_session:
        try:
            # Simulate secondary metric calculations
            order = await db_session.get(OrderORM, order_id)
            if order:
                order.status = "COMPLETED"
                await db_session.commit()
                logger.info(f"[TASK DB] Order #{order_id} status updated to COMPLETED")
        except Exception as exc:
            await db_session.rollback()
            logger.error(f"[TASK DB ERROR] Failed to update order #{order_id}: {exc}")
            return

    # Task Component B: External Webhook Notification with Error Handling
    try:
        payload = {"event": "ORDER_PROCESSED", "order_id": order_id, "email": customer_email}
        # In production: response = await http_client.post(webhook_url, json=payload)
        logger.info(f"[TASK WEBHOOK] Dispatched payment notification for order #{order_id} to {webhook_url}")
    except Exception as exc:
        logger.error(f"[TASK WEBHOOK ERROR] Failed to dispatch webhook for order #{order_id}: {exc}")

# ---------------------------------------------------------------------
# 4. PATH OPERATIONS
# ---------------------------------------------------------------------
@app.post(
    "/api/v1/orders",
    response_model=OrderAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def submit_order(
    payload: OrderRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # STEP 1: Fast synchronous write to record order in DB
    new_order = OrderORM(
        customer_email=payload.customer_email,
        amount=payload.amount,
        status="PROCESSING"
    )
    db.add(new_order)
    await db.flush()  # Populates new_order.id
    
    # STEP 2: Enqueue post-processing tasks to background pipeline
    background_tasks.add_task(
        process_post_order_tasks,
        order_id=new_order.id,
        customer_email=new_order.customer_email,
        webhook_url=payload.webhook_url,
        http_client=app.state.http_client
    )

    # STEP 3: Return immediate HTTP 202 Accepted response to client
    return OrderAcceptedResponse(
        order_id=new_order.id,
        status="ACCEPTED",
        message="Order accepted for processing. Notifications dispatched asynchronously."
    )
```

---
### Execution Pipeline Explanation

- Request Ingestion & Synchronous Persistence: An incoming POST request hits /api/v1/orders. The route opens an AsyncSession provided by get_db, inserts OrderORM with status="PROCESSING", and calls await db.flush() to obtain new_order.id.

- Background Task Registration: The endpoint calls background_tasks.add_task(), passing process_post_order_tasks alongside new_order.id, payload data, and the shared httpx.AsyncClient from app.state.http_client.

- Immediate Response Dispatch: The route handler finishes execution and dispatches an HTTP 202 Accepted JSON payload back to the calling client without waiting for notifications or external HTTP calls to finish.

- Asynchronous Background Execution: Once the HTTP response payload stream closes, FastAPI triggers process_post_order_tasks. The worker opens its own independent AsyncSession via session_factory() to update the database state to COMPLETED, handles any internal exceptions via try...except, and fires the outbound HTTP webhook asynchronously

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Background tasks

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Background tasks