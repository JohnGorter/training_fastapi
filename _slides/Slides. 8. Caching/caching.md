# Caching

---
### Caching

Caching in FastAPI operates at two primary levels
- HTTP-level client/proxy caching (browser/CDN headers and ETags) 
- application-level response/service caching (storing serialized Pydantic or ORM outputs in fast memory)

---
### Theoretical Background & Key Strategies

- HTTP/Browser Caching (Cache-Control, ETag)
    - Cache-Control: Dictates how browsers, reverse proxies (Nginx), and CDNs (Cloudflare) cache responses (e.g., max-age=3600, public, s-maxage=86400)
- ETag (Entity Tag) & 304 Not Modified
    - server generates a unique cryptographic hash of the response payload. On subsequent requests, the client sends If-None-Match: "<hash>". If the hash matches, the server returns an empty HTTP 304 Not Modified response, saving bandwidth
- Application & Service-Layer Caching
    - Cache-Aside Pattern: The route handler checks memory/Redis for a pre-computed response string. On a miss, it computes the data, populates the cache with a Time-To-Live (TTL), and returns the payload
- Stale-While-Revalidate
    - returns a cached (possibly stale) value immediately to the client while asynchronously firing a background task to fetch fresh data and update the cache
- Cache Invalidation
    - TTL Expiration: Automatic deletion after a set duration
- Explicit Purging
    - direct removal of cache keys during data-modifying HTTP operations (POST, PUT, PATCH, DELETE).
    
---
### HTTP Header Caching & Conditional Requests

Generating an ETag hash of the response body allows clients to issue conditional GET requests using If-None-Match. 

If data hasn't changed, FastAPI returns HTTP 304 Not Modified with zero response body payload

Real-World Use Case
- serving static catalog endpoints or configuration models to mobile apps to eliminate redundant JSON payload downloads

Behavior
- reduces egress bandwidth and client rendering latency while keeping data strictly up to date

---
### HTTP Header Caching & Conditional Requests

```
import hashlib
from typing import Annotated
from fastapi import FastAPI, Header, Response, status
from pydantic import BaseModel

app = FastAPI()

class AppSettings(BaseModel):
    version: str
    feature_flags: dict[str, bool]

SETTINGS_DATA = AppSettings(
    version="2.4.0",
    feature_flags={"dark_mode": True, "beta_checkout": False}
)

@app.get("/api/v1/config", response_model=AppSettings)
async def get_app_config(
    response: Response,
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None
):
    json_payload = SETTINGS_DATA.model_dump_json()
    # Generate cryptographic hash of payload
    etag = f'"{hashlib.md5(json_payload.encode()).hexdigest()}"'
    
    # Check conditional client header
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=3600"
    return SETTINGS_DATA
```


---
### In-Memory Service Caching (functools.lru_cache)

Python’s functools.lru_cache memoizes synchronous, CPU-bound computations or immutable configuration loading directly in process RAM

Real-World Use Case
- caching parsed application settings (Pydantic BaseSettings), machine learning models, or static cryptographic key sets

Behavior
- executes the function logic once on first call and returns the cached result instantaneously on subsequent calls with zero I/O overhead

---
### In-Memory Service Caching (functools.lru_cache)

```
from functools import lru_cache
from fastapi import FastAPI, Depends
from pydantic_settings import BaseSettings

class SystemConfig(BaseSettings):
    app_name: str = "Enterprise Gateway"
    max_workers: int = 8

# Singleton cached instance initialized on first access
@lru_cache
def get_system_config() -> SystemConfig:
    print("[INIT] Parsing configuration settings...")
    return SystemConfig()

app = FastAPI()

@app.get("/info")
async def get_info(config: SystemConfig = Depends(get_system_config)):
    return {"app": config.app_name, "workers": config.max_workers}
```

---
### Custom Parameterized Route Caching Decorator

A custom asynchronous decorator can intercept path calls, construct cache keys from route arguments, and return pre-serialized JSON payloads on cache hits

Real-World Use Case
- caching expensive database aggregation queries or report generation routes based on URL query parameters

Behavior
- bypasses path operation logic and database execution entirely when a valid cached string exists for the generated key


---
### Custom Parameterized Route Caching Decorator

```
import asyncio

from functools import wraps
import json
from typing import Callable
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()
LOCAL_CACHE: dict[str, tuple[float, str]] = {}  # key -> (expiration_timestamp, json_data)

def cache_response(ttl_seconds: int = 60):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract Request object from kwargs or positional args
            request: Request = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            cache_key = f"route:{request.url.path}:{sorted(request.query_params.items())}" if request else None

            now = asyncio.get_event_loop().time()
            if cache_key and cache_key in LOCAL_CACHE:
                expires_at, data = LOCAL_CACHE[cache_key]
                if now < expires_at:
                    return json.loads(data)

            # Compute route response
            result = await func(*args, **kwargs)
            
            if cache_key and result:
                payload = result.model_dump_json() if isinstance(result, BaseModel) else json.dumps(result)
                LOCAL_CACHE[cache_key] = (now + ttl_seconds, payload)

            return result
        return wrapper
    return decorator

@app.get("/reports/analytics")
@cache_response(ttl_seconds=120)
async def get_analytics_report(request: Request, region: str = "US"):
    await asyncio.sleep(1.0)  # Simulate heavy DB query
    return {"region": region, "active_users": 14200, "status": "computed"}
```

---
### Explicit Cache Invalidation on Mutations

To avoid serving stale data after POST, PUT, or DELETE mutations, route handlers must explicitly purge or update specific cached entries

Real-World Use Case
- evicting cached user profile data or inventory levels immediately after an administrative update

Behavior
- deletes matching keys from the cache store so subsequent reads trigger a fresh database query

---
### Explicit Cache Invalidation on Mutations

```
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()
CACHE_STORE: dict[str, str] = {}  # In-memory key-value cache store

class InventoryItem(BaseModel):
    name: str
    quantity: int

@app.put("/inventory/{item_id}")
async def update_inventory_item(item_id: str, payload: InventoryItem):
    # 1. Update Database (Simulated)
    # await db.execute(...)

    # 2. Invalidate Cache Entry
    cache_key = f"inventory:{item_id}"
    if cache_key in CACHE_STORE:
        del CACHE_STORE[cache_key]
        print(f"[CACHE PURGE] Evicted key: {cache_key}")

    return {"status": "success", "updated_id": item_id}
```

---
### Unified Enterprise FastAPI Caching & ETag Pipeline

This production pattern demonstrates an end-to-end e-commerce catalog API featuring Lifespan cache store initialization, Cache-Aside Async Decorator with TTL Jitter, HTTP ETag & 304 Not Modified validation, Explicit Cache Invalidation, and SQLAlchemy 2.0 Async database integration

---
### Unified Enterprise FastAPI Caching & ETag Pipeline

```
import asyncio
from contextlib import asynccontextmanager
import hashlib

from functools import wraps
import json
import random
import time
from typing import Annotated, AsyncGenerator, Callable
from fastapi import FastAPI, Depends, Header, Request, Response, status, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, update
from pydantic import BaseModel, Field, ConfigDict

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & DATABASE SETUP
# ---------------------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///enterprise_caching.db"

engine = create_async_engine(DATABASE_URL, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class ProductORM(Base):
    __tablename__ = "catalog_products"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()

# Centralized In-Memory Async Cache Engine
class AsyncMemoryCache:
    def __init__(self):
        self._store: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> str | None:
        if key not in self._store:
            return None
        expires_at, payload = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return payload

    async def set(self, key: str, payload: str, ttl_seconds: int):
        expires_at = time.time() + ttl_seconds
        self._store[key] = (expires_at, payload)

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def clear(self):
        self._store.clear()

cache_engine = AsyncMemoryCache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup
    await cache_engine.clear()
    await engine.dispose()

app = FastAPI(title="Enterprise Caching Gateway", lifespan=lifespan)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ---------------------------------------------------------------------
# 2. PYDANTIC CONTRACTS & DECORATOR HELPERS
# ---------------------------------------------------------------------
class ProductUpdateSchema(BaseModel):
    title: str = Field(min_length=2)
    price: float = Field(gt=0.0)

class ProductResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    title: str
    price: float

def async_cache(base_ttl: int = 60, jitter_max: int = 15):
    """Async route decorator with Cache-Aside pattern & TTL Jitter."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            
            if not request:
                return await func(*args, **kwargs)

            cache_key = f"cache:{request.url.path}"
            
            # 1. Read from Cache
            cached_data = await cache_engine.get(cache_key)
            if cached_data:
                return ProductResponseSchema.model_validate_json(cached_data)

            # 2. Execute Handler on Cache Miss
            result = await func(*args, **kwargs)

            # 3. Write Back with TTL Jitter (Prevents Cache Avalanche)
            if result:
                jitter = random.randint(0, jitter_max)
                payload = result.model_dump_json() if isinstance(result, BaseModel) else json.dumps(result)
                await cache_engine.set(cache_key, payload, base_ttl + jitter)

            return result
        return wrapper
    return decorator

# ---------------------------------------------------------------------
# 3. PATH OPERATIONS (Cache-Aside + ETags + Invalidation)
# ---------------------------------------------------------------------

@app.get(
    "/api/v1/products/{product_id}",
    response_model=ProductResponseSchema,
    status_code=status.HTTP_200_OK
)
@async_cache(base_ttl=120, jitter_max=10)
async def get_product(
    product_id: int,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None
):
    # Fetch from SQLite Database
    stmt = select(ProductORM).where(ProductORM.id == product_id)
    result = await db.execute(stmt)
    product_orm = result.scalar_one_or_none()

    if not product_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product #{product_id} not found"
        )

    product_schema = ProductResponseSchema.model_validate(product_orm)
    json_bytes = product_schema.model_dump_json().encode("utf-8")

    # Generate ETag
    etag = f'"{hashlib.md5(json_bytes).hexdigest()}"'
    
    # Conditional HTTP Request Handling
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60"
    return product_schema

@app.put(
    "/api/v1/products/{product_id}",
    response_model=ProductResponseSchema,
    status_code=status.HTTP_200_OK
)
async def update_product(
    product_id: int,
    payload: ProductUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Update Database Record
    stmt = (
        update(ProductORM)
        .where(ProductORM.id == product_id)
        .values(title=payload.title, price=payload.price)
    )
    result = await db.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product #{product_id} not found"
        )

    updated_orm = (await db.execute(
        select(ProductORM).where(ProductORM.id == product_id)
    )).scalar_one()

    # 2. Invalidate Cached Route Endpoint
    cache_key = f"cache:/api/v1/products/{product_id}"
    await cache_engine.delete(cache_key)

    return ProductResponseSchema.model_validate(updated_orm)
```

---
### Execution Pipeline Explanation

- Request Ingestion & Cache Check (GET /api/v1/products/101)
    - The client invokes the GET endpoint. @async_cache constructs the cache key cache:/api/v1/products/101 and queries AsyncMemoryCache. On a hit, ProductResponseSchema.model_validate_json() deserializes the string and returns immediately
- Database Execution & TTL Jitter
    - on a cache miss, the handler queries SQLite for ProductORM, converts it to a Pydantic schema, and generates a random TTL ($120 + \text{jitter}$ seconds) before writing the payload back to memory
- HTTP ETag Validation
    - the endpoint calculates an MD5 digest hash of the JSON response payload. If the client includes If-None-Match: "<hash>", FastAPI returns an empty HTTP 304 Not Modified response
- Targeted Cache Invalidation (PUT)
    - when product data is updated via update_product, SQLAlchemy updates SQLite, and cache_engine.delete("cache:/api/v1/products/101") purges the stale cache entry, guaranteeing that subsequent reads fetch the newly updated database state



---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Caching

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Caching