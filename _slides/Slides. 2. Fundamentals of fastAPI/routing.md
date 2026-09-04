# Routing

---
### Routing

FastAPI routing maps incoming HTTP verbs and URL paths to Python coroutines

---
### Basic Path Operations 

Path parameters capture variable segments directly from the URL path (/items/{item_id})
- non-path function arguments automatically map to URL query parameters (/items?limit=10&page=1)

Real-World Use Case
- fetching a specific resource by ID while applying pagination and search filters

Behavior
- type hints (int, str, bool) enforce automatic casting and validation. Invalid parameter types immediately trigger an HTTP 422 error

---
### Basic Path Operations 

```
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/products/{product_id}")
async def get_product(
    product_id: int,  # Path parameter (validated as integer)
    is_active: bool = True,  # Query parameter with default
    search: str | None = Query(default=None, max_length=50)  # Optional query parameter
):
    return {
        "product_id": product_id,
        "is_active": is_active,
        "search_term": search
    }
```

---
### Modular Route Organization

APIRouter separates endpoints into distinct files or feature modules

Routers define:
- shared URL prefixes
- OpenAPI documentation tags
- common response headers
- shared dependencies
    
Real-World Use Case
- splitting an e-commerce API into isolated domain files 

Behavior
- mounting an APIRouter onto the main FastAPI() app automatically prefixes paths 
- groups operations under OpenAPI tags

---
### Modular Route Organization

```
# routers/users.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)

@router.get("/")
async def list_users():
    return [{"id": 1, "username": "alex"}]

@router.get("/{user_id}")
async def get_user_by_id(user_id: int):
    return {"id": user_id, "username": "alex"}
```

```
# main.py
from fastapi import FastAPI
# from routers.users import router as user_router

app = FastAPI()
app.include_router(user_router)  # Routes now accessible at /users/ and /users/{user_id}
```

---
### Router-Level & Endpoint Dependencies 

Dependencies can be attached at the router or path-operation level via the dependencies parameter

Real-World Use Case
- securing an entire administrative sub-router with JWT authorization or rate-limiting guards

Behavior
- dependencies declared in APIRouter(dependencies=[...]) execute sequentially before any route handler in that router runs

---
### Router-Level & Endpoint Dependencies 

```
from typing import Annotated
from fastapi import FastAPI, APIRouter, Header, HTTPException, status

async def verify_admin_token(x_admin_token: Annotated[str, Header()]):
    if x_admin_token != "super-secret-admin-key":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required"
        )

# Router-level security dependency applied to all routes in this router
admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin Area"],
    dependencies=[Depends(verify_admin_token)]
)

@admin_router.get("/metrics")
async def get_system_metrics():
    return {"cpu_usage": "12%", "memory_usage": "45%"}
```


---
### Nest Routers with dynamic parts

You can nest routers with dynamic path segments in the call to include_router

```
from fastapi import FastAPI, APIRouter

app = FastAPI()

# 1. Child Router (Blogs)
blogs_router = APIRouter(tags=["Blogs"])

@blogs_router.get("/{blog_id}")
async def get_user_blog(user_id: int, blog_id: int):
    # 'user_id' comes from the parent router prefix
    # 'blog_id' comes from this route's path
    return {"user_id": user_id, "blog_id": blog_id, "content": "Blog contents..."}

# 2. Parent Router (Users)
users_router = APIRouter(prefix="/users", tags=["Users"])

# Nest the child router with the dynamic parameter in the prefix
users_router.include_router(blogs_router, prefix="/{user_id}/blogs")

# 3. Mount Parent Router to App
app.include_router(users_router)
```

---
### Question?

**Is the previous approach the best? What is the problem?**

---
### Answer

That approach is not ideal
- Coupling Child to Parent Prefixes
    - the child route relies directly on user_id being provided in the parent router's prefix
    - if the child router is later included under a different prefix (or reused independently), the parameter signatures break
- OpenAPI Schema / Docs Fragmentation
    - passing prefix="/{user_id}/blogs" during include_router puts path parameters into the routing registration step rather than declaring them inside the endpoint/router file itself
    - this makes reading and maintaining isolated router files confusing for larger codebases

---
### The Recommended Standard Pattern

**Keep child routers complete and explicit in their own modules, declaring full resource paths natively in the child router file**

```
from fastapi import APIRouter, FastAPI

# ---------------------------------------------------------
# 1. Child Router (blogs.py)
# ---------------------------------------------------------
# Declare the full functional prefix inside the child router.
blogs_router = APIRouter(
    prefix="/users/{user_id}/blogs",
    tags=["Blogs"]
)

@blogs_router.get("/{blog_id}")
async def get_user_blog(user_id: int, blog_id: int):
    return {"user_id": user_id, "blog_id": blog_id, "content": "Blog contents..."}


# ---------------------------------------------------------
# 2. Parent Router (users.py)
# ---------------------------------------------------------
users_router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@users_router.get("/")
async def get_users():
    return [{"user_id": 1, "name": "Alice"}]


# ---------------------------------------------------------
# 3. Main App Setup (main.py)
# ---------------------------------------------------------
app = FastAPI()

# Include each router directly into the main app (or aggregate via a master api_router)
app.include_router(users_router)
app.include_router(blogs_router)
```

---
### Why This Modern Pattern Is preferred

- Self-Contained Submodules
    - the child router defines its full prefix /users/{user_id}/blogs
    - anyone opening blogs.py instantly knows the full URL structure without hunting down parent include_router calls
- Clean Separation
    - decouples blogs_router from users_router
    - in large applications, main.py simply imports and registers all feature routers flatly:

```
app.include_router(users_router)
app.include_router(blogs_router)
app.include_router(comments_router)
```

- Type Hint Safety & Tools
    - keeping path parameters matching function arguments explicitly in the same router reduces IDE and schema mismatch warnings.

---
### Nest Routers with dynamic parts

Key Patterns to Keep in Mind
- parameter name alignment
    - the parameter name defined in the prefix (e.g., {user_id}) must match the parameter name expected in the child route function signature (user_id: int)
- clean modular file structure
    - if split across files, blogs_router can be defined in routers/blogs.py without needing to import or know about users_router
    - the parent prefix relationship is established entirely when you call users_router.include_router(...)
- deep nesting
    - you can chain this pattern further down 
    - e.g., /users/{user_id}/blogs/{blog_id}/comments/{comment_id}

---
### Unified Enterprise Routing Architecture

This production pattern demonstrates a modular FastAPI routing layout with multi-router inclusion (v1 API group), path versioning, router-level security dependencies, enum path parameters, query filters, and response model serialization

Project Directory Structure
```
Plaintextapp/
├── api/
│   └── v1/
│       ├── auth.py
│       └── inventory.py
├── main.py
```

app/api/v1/inventory.py (Domain Sub-Router)
```
from enum import Enum
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field

class CategoryEnum(str, Enum):
    ELECTRONICS = "electronics"
    HARDWARE = "hardware"
    SOFTWARE = "software"

class ItemResponse(BaseModel):
    id: int
    name: str
    category: CategoryEnum
    price: float

router = APIRouter(prefix="/inventory", tags=["Inventory Operations"])

# Mock Database
INVENTORY_DB = [
    {"id": 101, "name": "4K Monitor", "category": CategoryEnum.ELECTRONICS, "price": 399.99},
    {"id": 102, "name": "NVMe SSD 2TB", "category": CategoryEnum.HARDWARE, "price": 149.50},
]

@router.get("", response_model=list[ItemResponse])
async def list_inventory(
    category: CategoryEnum | None = None,
    min_price: float = Query(default=0.0, ge=0.0),
    limit: int = Query(default=10, le=50)
):
    results = INVENTORY_DB
    if category:
        results = [i for i in results if i["category"] == category]
    results = [i for i in results if i["price"] >= min_price]
    return results[:limit]

@router.get("/{item_id}", response_model=ItemResponse)
async def get_inventory_item(item_id: int):
    item = next((i for i in INVENTORY_DB if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item
```

app/main.py (Core Router Assembly)
```
from typing import Annotated
from fastapi import FastAPI, APIRouter, Depends, Header, HTTPException, status
from app.api.v1.inventory import router as inventory_router

# Common Guard Dependency
async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None):
    if x_api_key != "valid-enterprise-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header"
        )

app = FastAPI(
    title="Enterprise Core API",
    version="1.0.0",
    docs_url="/docs"
)

# Version 1 Master Router Grouping
v1_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(verify_api_key)]  # Protects all V1 sub-routers
)

# Include Domain Routers under V1
v1_router.include_router(inventory_router)

# Mount Master Router to Core FastAPI Application
app.include_router(v1_router)

@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {"status": "healthy", "api_version": "v1"}
```

---
### Execution Pipeline Explanation
- Request Dispatch
    - client dispatches an HTTP GET request to /api/v1/inventory?category=electronics&min_price=100.0 with header X-API-Key: valid-enterprise-key.Path Resolution & Middleware
    - FastAPI resolves the URL tree (app -> v1_router [/api/v1] -> inventory_router [/inventory])
- Router Dependency Execution
    - before reaching the route handler, v1_router executes verify_api_key. If the header is missing or incorrect, it raises an HTTP 401 error
- Parameter Extraction & Enum Parsing
    - FastAPI parses category=electronics into CategoryEnum.ELECTRONICS and checks min_price against Pydantic's ge=0.0 constraint
- Serialization:
    - the handler filters INVENTORY_DB and returns matching dict items
    - FastAPI converts the raw dictionaries into ItemResponse Pydantic models and streams the final JSON payload

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Routing

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Routing