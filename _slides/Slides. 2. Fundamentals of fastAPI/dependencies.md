# Dependencies

---
### Dependencies

*FastAPI's dependency injection system (Depends) resolves and injects shared logic—such as database sessions, security checks, and query parameters—by evaluating a Directed Acyclic Graph (DAG) of callable objects before executing your route logic.*

Lets look at: 
- Standard Function Dependencies
- Class-Based Dependencies
- Sub-dependencies
- Yield Dependencies (Resource Cleanup & Context Managers)

---
### Standard Function Dependencies

Any standard function or async callable can act as a dependency!

FastAPI inspects its parameters (path, query, body, or other dependencies), extracts them from the request, executes the function, and passes the return value to your path operation

Real-World Use Case
- shared pagination logic across multiple GET endpoints

Behavior
- reusable logic is extracted out of path functions to keep controller endpoints lean

---
### Standard Function Dependencies

```
def pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> dict[str, int]:
    return {"skip": (page - 1) * limit, "limit": limit}

@app.get("/items")
async def list_items(pagination: Annotated[dict, Depends(pagination_params)]):
    return {"skip": pagination["skip"], "limit": pagination["limit"]}
```

---
### Class-Based Dependencies 

Classes can be used directly as dependencies 

FastAPI 
- evaluates the class's __init__ signature
- extracts required request parameters to instantiate the class,
- injects the resulting object instance

Real-World Use Case
- complex multi-field search and filtering objects in administrative dashboards.

Behavior
- passing Depends() without arguments instructs FastAPI to infer the target dependency directly from the parameter's type annotation, in this case SearchFilter

---
### Class-Based Dependencies

```
class SearchFilter:
    def __init__(
        self,
        q: Annotated[str | None, Query(description="Search string")] = None,
        category: Annotated[str | None, Query()] = None
    ):
        self.q = q
        self.category = category

@app.get("/products")
async def search_products(filters: Annotated[SearchFilter, Depends()]):
    return {"query": filters.q, "category": filters.category}
```

We have seen this pattern before, remember ;-)

---
### Callable dependencies

You can reuse a created dependency by inplementing the __call__ patterm

__init__ vs. __call__ Pattern
- __init__ => FastAPI creates a new instance of dependency on every request
- __call__ => allows you to pass configuration options at app startup and execute request checks 

---
### Callable dependencies

```
class ValidateToken:
    def __init__(self, expected_token: str):
        # Configured once on app startup
        self.expected_token = expected_token

    def __call__(self, admin_token: str = Header(...)):
        # Executed on every request
        if admin_token != self.expected_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")

# Instantiate reusable instance with environment config
admin_guard = ValidateToken(expected_token="secret_admin_token")

@app.get("/admin/users", dependencies=[Depends(admin_guard)])
async def get_admin_users():
    return [{"user": "Alice"}]

```

---
### Decorator dependencies

Decorator dependencies are registered on the decorator, not on a parameter in the path function.

These dependencies uns before the path operation function executes
- if the dependency raises an exception (e.g., HTTPException), the route handler will not run
- the dependency function itself can still inject other dependencies

Router-level reuse: You can pass the same dependencies=[Depends(...)] parameter to an APIRouter() instance to apply non-bound side effects across a specific group of routes, more on this later!

---
### Decorator dependencies

```
import logging
from fastapi import FastAPI, Depends, Request

app = FastAPI()

def log_endpoint_access(request: Request):
    logging.info(f"Accessed endpoint: {request.url.path}")

@app.get("/items", dependencies=[Depends(log_endpoint_access)])
def read_items():
    return [{"name": "Item A"}]
```


---
### Sub-dependencies (Nested Dependencies)

Dependencies can depend on other dependencies to build multi-layered processing chains

Real-World Use Case
- reading a bearer token from headers → validating token & retrieving user → verifying admin permissions.

Behavior
- If any sub-dependency in the chain raises an HTTPException, processing halts immediately and skips down-stream functions

---
### Sub-dependencies (Nested Dependencies)

```
def get_auth_token(x_token: Annotated[str, Header()]) -> str:
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing X-Token header")
    return x_token

def get_current_user(token: Annotated[str, Depends(get_auth_token)]) -> dict:
    # Simulate DB lookup from token
    return {"user_id": 101, "role": "admin", "token": token}

@app.get("/admin/dashboard")
async def get_dashboard(user: Annotated[dict, Depends(get_current_user)]):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"status": "Welcome Admin", "user_id": user["user_id"]}
```

---
### Yield Dependencies

Dependencies containing a yield statement act as setup/teardown execution blocks
- code before yield runs before the request
- code after yield runs after the response has been delivered to the client

Real-World Use Case
- managing relational database sessions or temporary network connections safely

Behavior
- guarantees teardown execution (e.g., db.close()) even if exceptions occur during request handling

---
### Yield Dependencies

```
class FakeDBSession:
    def close(self):
        print("Database connection closed cleanly.")

def get_db() -> Generator[FakeDBSession, None, None]:
    db = FakeDBSession()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/me")
async def read_user_me(db: Annotated[FakeDBSession, Depends(get_db)]):
    return {"status": "Database session active during execution"}
```

---
### Global & Router-Level Dependencies

Dependencies declared inside route decorators (@app.get(..., dependencies=[...])) or on an APIRouter run automatically for all matching routes

Real-World Use Case
- enforcing rate limiting, feature flag checks, or global maintenance windows across an entire route group

Behavior
- prevents boilerplate by removing the need to add parameters to every single path function signature

---
### Global & Router-Level Dependencies

```
from typing import Annotated
from fastapi import FastAPI, APIRouter, Depends, Header, HTTPException, status

# =====================================================================
# 1. GLOBAL DEPENDENCY
# Application-wide execution (e.g., Distributed Request Tracing)
# =====================================================================
async def enforce_tracing_header(
    x_correlation_id: Annotated[str | None, Header(alias="X-Correlation-ID")] = None
):
    """Enforces that every incoming request to the API includes a tracing ID."""
    if not x_correlation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required 'X-Correlation-ID' header."
        )

# Attached at app instantiation: applies to ALL endpoints globally
app = FastAPI(dependencies=[Depends(enforce_tracing_header)])

# =====================================================================
# 2. ROUTER-LEVEL DEPENDENCY
# Group-level execution (e.g., Role-Based Access Control)
# =====================================================================
async def verify_admin_role(
    x_user_role: Annotated[str, Header(alias="X-User-Role")] = "guest"
):
    """Guards an entire router slice against non-admin traffic."""
    if x_user_role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Endpoint requires admin privileges."
        )

# Attached at router instantiation: applies to ALL routes in this router
admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin Portal"],
    dependencies=[Depends(verify_admin_role)]
)

@admin_router.get("/users")
async def list_users():
    # Automatically protected by verify_admin_role AND enforce_tracing_header
    return [{"id": 1, "username": "alice"}, {"id": 2, "username": "bob"}]

@admin_router.delete("/cache")
async def purge_cache():
    # Also protected automatically without repeating parameters
    return {"status": "cache_purged"}

# =====================================================================
# PUBLIC ROUTES (Inherit Global Dependencies Only)
# =====================================================================
@app.get("/health")
async def health_check():
    # Only evaluates enforce_tracing_header
    return {"status": "healthy"}

app.include_router(admin_router)
```

---
### Global state dependency state transfer

You van transfer state to your path function using to following construct

```
from fastapi import FastAPI, Depends, Request

def global_auth_dependency(request: Request):
    # Perform authentication or setup logic
    user_context = {"user_id": 42, "role": "admin"}
    request.state.user = user_context

# Registered globally
app = FastAPI(dependencies=[Depends(global_auth_dependency)])

@app.get("/dashboard")
def get_dashboard(request: Request):
    # Access the value populated by the global dependency
    current_user = request.state.user
    return {"message": f"Hello {current_user['user_id']}"}
```

---
### Dependency Caching Control

By default (use_cache=True)
- if multiple parameters or sub-dependencies call the exact same dependency within a single request execution, FastAPI evaluates it once and reuses the cached return value
- very good practice to open database connections but sometimes not desired

Real-World Use Case
- generating distinct unique request trace IDs or execution timers at different pipeline stages

Behavior
- setting use_cache=False forces FastAPI to execute the dependency function anew every time it is referenced

---
### Dependency Caching Control

```
import uuid
from typing import Annotated
from fastapi import FastAPI, Depends

app = FastAPI()

def generate_request_id() -> str:
    return str(uuid.uuid4())

@app.get("/trace")
async def trace_request(
    id_a: Annotated[str, Depends(generate_request_id, use_cache=False)],
    id_b: Annotated[str, Depends(generate_request_id, use_cache=False)],
):
    return {"trace_a": id_a, "trace_b": id_b}  # Evaluates to two distinct UUIDs
```

---
### Unified Enterprise Request Flow Implementation

This production pattern demonstrates how FastAPI resolves router guards, nested authentication, database context managers, class filters, and teardown logic within a financial refund execution pipeline.

```
from typing import Annotated, Generator
from fastapi import FastAPI, APIRouter, Depends, Header, Path, Query, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI()

# 1. Yield Dependency: DB Session Context
class DBSession:
    def execute_refund(self, order_id: int, amount: float):
        return f"Refund #{order_id} processed for ${amount}"
    def close(self):
        pass

def get_db_session() -> Generator[DBSession, None, None]:
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

# 2. Sub-dependencies: Auth Pipeline
def get_auth_header(authorization: Annotated[str, Header()]) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid Authorization scheme")
    return authorization.split(" ")[1]

def get_authorized_staff(token: Annotated[str, Depends(get_auth_header)]) -> dict:
    if token != "valid-staff-token":
        raise HTTPException(status_code=401, detail="Unauthorized staff account")
    return {"staff_id": "usr_99", "role": "finance_manager"}

# 3. Class-Based Dependency: Request Context Payload
class RefundContext:
    def __init__(
        self,
        reason: Annotated[str, Query(description="Audit trail reason")] = "Customer Request",
        force_override: Annotated[bool, Query()] = False,
    ):
        self.reason = reason
        self.force_override = force_override

# 4. Global Router Dependency: System Maintenance Check
def verify_system_online():
    system_maintenance = False
    if system_maintenance:
        raise HTTPException(status_code=533, detail="System under maintenance")

# Attach Global Guard to Router
finance_router = APIRouter(
    prefix="/finance",
    dependencies=[Depends(verify_system_online)]
)

class RefundRequest(BaseModel):
    amount: float = Field(gt=0)

@finance_router.post("/orders/{order_id}/refund")
async def execute_refund_route(
    order_id: Annotated[int, Path(ge=1)],
    payload: RefundRequest,
    db: Annotated[DBSession, Depends(get_db_session)],
    staff: Annotated[dict, Depends(get_authorized_staff)],
    context: Annotated[RefundContext, Depends()],
):
    result = db.execute_refund(order_id, payload.amount)
    return {
        "status": "success",
        "order_id": order_id,
        "processed_by": staff["staff_id"],
        "reason": context.reason,
        "audit_override": context.force_override,
        "detail": result
    }

app.include_router(finance_router)
```
---
### Execution Pipeline Explanation

- Router Guard Check: FastAPI evaluates verify_system_online(). If it fails, execution halts before parsing any request bodies or acquiring database connections.

- Request Parameter Extraction: order_id is extracted from the URL path, payload is parsed from JSON, and RefundContext instantiates query parameters (reason, force_override).

- Sub-dependency Resolution: FastAPI resolves get_authorized_staff(), identifying its dependency on get_auth_header(). get_auth_header() extracts the Authorization HTTP header first, passes the extracted token string to get_authorized_staff(), and attaches the resulting staff object.

---
### Execution Pipeline Explanation (2)

- Yield Setup: get_db_session() runs up to the yield statement, instantiating the database handle and passing it into db.

- Route Execution: The route function completes using all fully validated dependencies.

- Yield Teardown: After the HTTP response is formulated and dispatched to the user, FastAPI re-enters get_db_session() right after the yield statement to execute db.close(), preventing resource leaks.

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Dependencies

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Dependencies