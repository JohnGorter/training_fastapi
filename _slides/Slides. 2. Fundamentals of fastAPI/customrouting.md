# Custom APIRoute

---
### Custom APIRoute 

Custom APIRoute classes and ASGI middlewares allow you to 
- intercept
- profile
- transform HTTP requests and responses 

---
### Custom APIRoute Classes 

Subclassing APIRoute lets you override get_route_handler() to wrap route execution in custom logic

This logic applies specifically to endpoints mounted on that router rather than the entire global application

Real-World Use Case
- measuring execution latency for specific microservice endpoints or logging route-specific parameters without affecting static file routes or health checks

Behavior
- the custom handler wraps super().get_route_handler(), executing pre-processing before calling the route and post-processing after the response is returned

```
import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

class TimedAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            start_time = time.perf_counter()
            # Execute the actual endpoint & Pydantic validation
            response: Response = await original_handler(request)
            
            elapsed = time.perf_counter() - start_time
            response.headers["X-Response-Time-Sec"] = f"{elapsed:.4f}"
            return response

        return custom_handler
```

---
### Raw Request Payload Inspection in APIRoute

Standard middlewares can struggle to read request bodies because the HTTP byte stream can only be consumed once
- a custom APIRoute can safely read, log, and re-attach the raw body stream before Pydantic parsing runs

Real-World Use Case
- auditing raw incoming webhook signatures (e.g., Stripe or GitHub webhooks) 
- logging unparsed payload bodies for debugging

Behavior
- reading await request.body() caches the bytes in memory, allow to create a new receive stream so downstream route handlers can still parse the JSON body

```
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute

class AuditPayloadRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            # Read raw byte body without consuming it permanently
            body = await request.body()
            print(f"[AUDIT LOG] Incoming raw body ({len(body)} bytes): {body.decode('utf-8', errors='ignore')}")

            # Continue standard routing pipeline
            return await original_handler(request)

        return custom_handler
```

---
### Global ASGI Middleware (BaseHTTPMiddleware)

BaseHTTPMiddleware intercepts every HTTP request passing through the ASGI server, modifying headers, handling global CORS policies, or injecting correlation IDs before route matching occurs

Real-World Use Case
- injecting a unique trace/correlation ID (X-Correlation-ID) into every request to track logs across distributed microservices

Behavior
- wraps the entire application request/response lifecycle
- code before await call_next(request) runs on request entry
- code after runs before sending bytes to the client

```
import uuid
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Extract existing trace ID or generate a new UUID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # 2. Attach to request.state for access inside routes
        request.state.correlation_id = correlation_id

        # 3. Process request downstream
        response = await call_next(request)

        # 4. Inject trace header into outgoing response
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

---
### Centralized Exception Handlers 

Custom exception handlers can intercept specific Python domain exceptions thrown anywhere in the service layer, translating them into uniform, structured API error responses

Real-World Use Case
- catching internal business logic errors (e.g., InsufficientInventoryError) and mapping them to standardized JSON error models with explicit status codes

Behavior
- intercepts raised exceptions before they propagate to the ASGI server as generic 500 Internal Server Errors

```
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

class InventoryDepletedError(Exception):
    def __init__(self, sku: str, requested: int):
        self.sku = sku
        self.requested = requested

app = FastAPI()

# Register custom exception handler globally
@app.exception_handler(InventoryDepletedError)
async def inventory_exception_handler(request: Request, exc: InventoryDepletedError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error_code": "INVENTORY_DEPLETED",
            "message": f"Cannot fulfill request for item '{exc.sku}'. Requested: {exc.requested}.",
            "correlation_id": getattr(request.state, "correlation_id", "N/A")
        }
    )
```

---
### Unified Enterprise Middleware & Route Architecture

This complete pattern combines a global CorrelationIdMiddleware, a router-level TimedAPIRoute, and a centralized exception_handler to build a fully instrumented order processing service.

```
import time
import uuid
from typing import Annotated, Callable
from fastapi import FastAPI, APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

# =====================================================================
# 1. DOMAIN EXCEPTIONS & CENTRALIZED HANDLERS
# =====================================================================
class PaymentFailedError(Exception):
    def __init__(self, order_id: str, reason: str):
        self.order_id = order_id
        self.reason = reason

# =====================================================================
# 2. CUSTOM ROUTE & MIDDLEWARE INFRASTRUCTURE
# =====================================================================
class ProfilingAPIRoute(APIRoute):
    """Custom APIRoute to log route execution timing and correlation details."""
    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()

        async def custom_handler(request: Request) -> Response:
            start = time.perf_counter()
            
            # Execute endpoint handler
            response: Response = await original_handler(request)
            
            elapsed = time.perf_counter() - start
            correlation_id = getattr(request.state, "correlation_id", "UNKNOWN")
            
            # Inject performance header
            response.headers["X-Execution-Time-Ms"] = f"{elapsed * 1000:.2f}"
            print(f"[METRIC] Trace: {correlation_id} | Path: {request.url.path} | Time: {elapsed * 1000:.2f}ms")
            
            return response

        return custom_handler

class TelemetryMiddleware(BaseHTTPMiddleware):
    """Global ASGI Middleware for Correlation ID propagation."""
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", f"trace-{uuid.uuid4().hex[:8]}")
        request.state.correlation_id = correlation_id
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

# =====================================================================
# 3. FASTAPI CORE APP & ROUTER CONFIGURATION
# =====================================================================
app = FastAPI(title="Enterprise Telemetry Portal")

# Register Global Middleware
app.add_middleware(TelemetryMiddleware)

# Register Centralized Exception Handler
@app.exception_handler(PaymentFailedError)
async def handle_payment_failure(request: Request, exc: PaymentFailedError):
    return JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={
            "error_code": "PAYMENT_REJECTED",
            "order_id": exc.order_id,
            "reason": exc.reason,
            "trace_id": getattr(request.state, "correlation_id", None)
        }
    )

# Dedicated Router using Custom APIRoute Class
order_router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
    route_class=ProfilingAPIRoute  # Applies ProfilingAPIRoute to all routes in this router
)

# Schemas
class OrderRequest(BaseModel):
    item_sku: str
    amount: float = Field(gt=0.0)

class OrderResponse(BaseModel):
    order_id: str
    status: str
    trace_id: str

# Endpoints
@order_router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def submit_order(payload: OrderRequest, request: Request):
    # Simulate payment rejection business logic
    if payload.amount > 1000.0:
        raise PaymentFailedError(order_id="ORD-9901", reason="Transaction exceeds limit")
        
    return OrderResponse(
        order_id="ORD-9901",
        status="PROCESSED",
        trace_id=request.state.correlation_id
    )

app.include_router(order_router)
```

---
### Execution Pipeline Explanation

- Global Middleware Entry: An HTTP POST arrives at /api/v1/orders. TelemetryMiddleware intercepts the raw request, extracts or generates a trace ID (trace-a1b2c3d4), attaches it to request.state.correlation_id, and passes control downstream.

- Custom Route Profiling: order_router identifies that its endpoints use route_class=ProfilingAPIRoute. The custom_handler captures the high-resolution start time using time.perf_counter().

- Business Logic & Exception Handling:
    - If amount <= 1000.0, the route completes successfully.
    - If amount > 1000.0, the route raises PaymentFailedError. The handle_payment_failure exception handler intercepts this error, formats a structured JSON payload, includes request.state.correlation_id, and sets the status code to HTTP 402.

- Header Injection & Response Return: As the response exits back up through ProfilingAPIRoute, it injects X-Execution-Time-Ms. As it passes out through TelemetryMiddleware, it injects X-Correlation-ID into the final response headers before streaming to the client.