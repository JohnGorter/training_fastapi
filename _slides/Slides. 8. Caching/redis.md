# Redis

---
### Redis

Redis (Remote Dictionary Server) is an in-memory, key-value data store that delivers sub-millisecond data access by maintaining datasets in RAM and processing commands using a single-threaded event loop

---
### Theoretical Background & Core Concepts

- Data Structures: Beyond key-value strings, Redis natively supports Hashes (field-value maps), Lists (linked lists), Sets (unique strings), Sorted Sets/ZSETs (leaderboards sorted by floating-point scores), and Bitmaps/HyperLogLogs
- Execution Model: Runs a single-threaded event loop using I/O multiplexing. Because operations run sequentially without thread lock contention, single operations execute with $O(1)$ or $O(\log N)$ time complexity
- Persistence Mechanics: RDB (Redis Database): Point-in-time snapshotting saved to disk at specified intervals
- AOF (Append-Only File): Logs every write operation sequentially. Replayed at startup for zero-data-loss durability.Hybrid: Uses AOF for durability alongside RDB for faster server restarts.
- Memory Eviction Policies:allkeys-lru / volatile-lru: Removes least recently used keys across the entire dataset or keys with an active TTL.
- allkeys-lfu / volatile-lfu: Removes least frequently used keys based on access counters.
- noeviction: Rejects write operations when allocated RAM (maxmemory) is exhausted

---
### Structured Object Storage

Redis Hashes store objects as field-value pairs directly inside memory, allowing mutation of individual fields without reading or serializing whole JSON strings

Real-World Use Case
- managing active user shopping carts, session preferences, or live status flags

Behavior
- fields can be set (hset), fetched individually (hget), or read completely (hgetall) with minimal memory overhead

---
### Structured Object Storage

```
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
import redis.asyncio as aioredis
from pydantic import BaseModel

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class CartItemUpdate(BaseModel):
    item_id: str
    quantity: int

@app.post("/cart/{user_id}/items")
async def update_cart_item(user_id: str, payload: CartItemUpdate):
    hash_key = f"cart:{user_id}"
    
    if payload.quantity <= 0:
        await redis_client.hdel(hash_key, payload.item_id)
        return {"status": "removed"}
        
    # Set field inside Hash map and extend session TTL
    await redis_client.hset(hash_key, payload.item_id, str(payload.quantity))
    await redis_client.expire(hash_key, 86400)  # 24-hour expiration
    
    return {"status": "updated", "cart": await redis_client.hgetall(hash_key)}
```

---
### API Rate Limiting via Atomic Fixed Windows 

Atomic counters track and restrict the number of HTTP requests a client IP or API key can make within a designated time window

Real-World Use Case
- protecting sensitive endpoints (e.g., login forms, payment gateways, LLM generation routes) from brute-force attacks or API quota exhaustion

Behavior
- redis.incr() atomically increments a counter. If the counter equals 1, redis.expire() sets the window reset clock. If the count exceeds the threshold, requests return HTTP 429 Too Many Requests

---
### API Rate Limiting via Atomic Fixed Windows 

```
from typing import Annotated
from fastapi import FastAPI, Depends, Request, HTTPException, status
import redis.asyncio as aioredis

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

async def rate_limiter(request: Request):
    client_ip = request.client.host
    rate_key = f"rate:{client_ip}:login"
    
    # Atomic increment
    current_requests = await redis_client.incr(rate_key)
    
    if current_requests == 1:
        await redis_client.expire(rate_key, 60)  # 60-second window
        
    if current_requests > 5:  # Max 5 requests per minute
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again in 60 seconds."
        )

@app.post("/login", dependencies=[Depends(rate_limiter)])
async def login_user():
    return {"message": "Authentication successful"}
```

3. Distributed Mutex Locking with Lua Scripting (SET ... NX PX)Distributed locks ensure that only one instance of a microservice executes a critical code block across a distributed cluster.Real-World Use Case: Preventing duplicate payment processing, coordinating scheduled background jobs, or reserving limited inventory seats.Behavior: Sets a lock using SET key token NX PX <ms>. Releases the lock using a Lua script to ensure workers only delete locks they currently own.Pythonimport uuid
import redis.asyncio as aioredis

# Lua script ensures atomic unlock (only delete if lock value matches token)
RELEASE_LOCK_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""

class RedisDistributedLock:
    def __init__(self, redis: aioredis.Redis, lock_key: str, ttl_ms: int = 5000):
        self.redis = redis
        self.lock_key = f"lock:{lock_key}"
        self.ttl_ms = ttl_ms
        self.token = str(uuid.uuid4())

    async def __aenter__(self):
        # NX: Only set if Not eXists | PX: Expiration in milliseconds
        acquired = await self.redis.set(self.lock_key, self.token, nx=True, px=self.ttl_ms)
        if not acquired:
            raise RuntimeError(f"Could not acquire lock for {self.lock_key}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Execute atomic Lua release
        await self.redis.eval(RELEASE_LOCK_LUA, 1, self.lock_key, self.token)
4. Event Messaging via Redis Pub/SubRedis Pub/Sub acts as a lightweight message broker, broadcasting published events instantly to all active channel subscribers.Real-World Use Case: Broadcasting real-time chat messages, system notifications, or streaming stock market updates to connected ASGI workers.Behavior: Publishers send messages with publish(); subscribers listen asynchronously via pubsub.listen().Pythonimport asyncio
from fastapi import FastAPI
import redis.asyncio as aioredis

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

@app.post("/broadcast")
async def broadcast_event(channel: str, message: str):
    # Publish message to channel
    listeners_count = await redis_client.publish(f"events:{channel}", message)
    return {"status": "dispatched", "active_listeners": listeners_count}

async def start_event_listener():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("events:orders")
    async for msg in pubsub.listen():
        if msg["type"] == "message":
            print(f"[EVENT RECEIVED] {msg['data']}")
Unified Enterprise Redis Infrastructure GatewayThis production pattern combines a FastAPI application using a Lifespan connection pool manager, Custom Redis Rate Limiting Dependency, Distributed Mutex Lock context manager, and Hash object persistence.Pythonfrom contextlib import asynccontextmanager
import time
from typing import Annotated, AsyncGenerator
import uuid
from fastapi import FastAPI, Depends, Request, HTTPException, status
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & LIFESPAN MANAGEMENT
# ---------------------------------------------------------------------
REDIS_URL = "redis://localhost:6379"

# Lua script for safe lock release
RELEASE_LOCK_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connection pool at startup
    app.state.redis = aioredis.from_url(
        REDIS_URL, 
        max_connections=20, 
        decode_responses=True
    )
    yield
    # Close pool on shutdown
    await app.state.redis.close()

app = FastAPI(title="Enterprise Redis Operations", lifespan=lifespan)

def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis

# ---------------------------------------------------------------------
# 2. DISTRIBUTED LOCK IMPLEMENTATION
# ---------------------------------------------------------------------
class DistributedLock:
    """Async Context Manager for distributed resource locking."""
    def __init__(self, redis: aioredis.Redis, resource_key: str, ttl_ms: int = 10000):
        self.redis = redis
        self.lock_key = f"lock:{resource_key}"
        self.ttl_ms = ttl_ms
        self.token = str(uuid.uuid4())

    async def __aenter__(self):
        acquired = await self.redis.set(self.lock_key, self.token, nx=True, px=self.ttl_ms)
        if not acquired:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resource is currently locked by another operation. Try again later."
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.redis.eval(RELEASE_LOCK_LUA, 1, self.lock_key, self.token)

# ---------------------------------------------------------------------
# 3. RATE LIMITER DEPENDENCY FACTORY
# ---------------------------------------------------------------------
class RateLimiter:
    """Fixed-window rate limiter dependency."""
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(
        self, 
        request: Request, 
        redis: Annotated[aioredis.Redis, Depends(get_redis)]
    ):
        client_ip = request.client.host
        route_path = request.url.path
        key = f"ratelimit:{client_ip}:{route_path}"

        current_count = await redis.incr(key)
        if current_count == 1:
            await redis.expire(key, self.window_seconds)

        if current_count > self.max_requests:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Window resets in {ttl} seconds.",
                headers={"Retry-After": str(ttl)}
            )

# Instantiate rate limiters
standard_limiter = RateLimiter(max_requests=10, window_seconds=60)
strict_limiter = RateLimiter(max_requests=2, window_seconds=60)

# ---------------------------------------------------------------------
# 4. SCHEMAS & PATH OPERATIONS
# ---------------------------------------------------------------------
class InventoryReservationRequest(BaseModel):
    item_sku: str
    quantity: int = Field(gt=0)
    user_id: str

@app.post(
    "/api/v1/inventory/reserve",
    dependencies=[Depends(strict_limiter)],
    status_code=status.HTTP_200_OK
)
async def reserve_inventory(
    payload: InventoryReservationRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    # Acquire lock specifically for the target SKU
    async with DistributedLock(redis, resource_key=f"inventory:{payload.item_sku}"):
        inventory_key = f"stock:{payload.item_sku}"
        
        # Read current stock level
        current_stock = await redis.get(inventory_key)
        
        # Initialize dummy inventory if missing
        if current_stock is None:
            current_stock = 50
            await redis.set(inventory_key, current_stock)
        else:
            current_stock = int(current_stock)

        if current_stock < payload.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient inventory. Requested: {payload.quantity}, Available: {current_stock}"
            )

        # Deduct stock atomically
        remaining_stock = await redis.decrby(inventory_key, payload.quantity)

        # Store user reservation details in a Redis Hash
        reservation_id = f"res_{uuid.uuid4().hex[:8]}"
        hash_key = f"reservation:{reservation_id}"
        await redis.hset(
            hash_key,
            mapping={
                "user_id": payload.user_id,
                "sku": payload.item_sku,
                "quantity": str(payload.quantity),
                "timestamp": str(time.time())
            }
        )
        await redis.expire(hash_key, 1800)  # 30-minute reservation window

        return {
            "status": "RESERVED",
            "reservation_id": reservation_id,
            "sku": payload.item_sku,
            "quantity_reserved": payload.quantity,
            "remaining_stock": remaining_stock
        }

@app.get(
    "/api/v1/reservations/{reservation_id}",
    dependencies=[Depends(standard_limiter)]
)
async def get_reservation_details(
    reservation_id: str,
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    hash_key = f"reservation:{reservation_id}"
    reservation = await redis.hgetall(hash_key)

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation #{reservation_id} not found or expired."
        )

    return {"reservation_id": reservation_id, "details": reservation}
Execution Pipeline Explanation:Connection Management: Uvicorn starts the application, triggering lifespan to establish an asynchronous Redis connection pool with a maximum connection threshold (max_connections=20) stored on app.state.redis.Rate Limiter Pipeline (strict_limiter): When POST /api/v1/inventory/reserve is invoked, RateLimiter increments ratelimit:<client_ip>:/api/v1/inventory/reserve via INCR. If request counts exceed 2 within a 60-second window, execution halts immediately with an HTTP 429 response.Distributed Lock Acquisition: The route handler enters async with DistributedLock(...), executing SET lock:inventory:<sku> <uuid_token> NX PX 10000. If another worker holds the lock, it raises an HTTP 409 Conflict error, preventing race conditions.Atomic Operations & Hash Storage: Stock is verified and decremented via DECRBY. Reservation details are mapped into a Redis Hash (HSET) and assigned a 30-minute expiration TTL (EXPIRE). Upon block exit, __aexit__ runs the Lua script to safely release the lock.



---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Redis

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Redis