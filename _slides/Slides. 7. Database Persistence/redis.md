# Redis and Caching 

---
### Caching

stores high-frequency read data in fast, volatile memory to decrease database CPU load and reduce network latency. Selecting the right pattern balances read/write throughput against data freshness guarantees.

Caching Strategy Theory

Strategy	Read Path	Write Path	Strengths	Weaknesses
Cache-Aside (Lazy Loading)	Read Cache → On miss, Read DB → Write Cache	Write DB directly	Contains only requested data; system remains resilient if cache fails.	Initial read penalty on cache misses; risk of serving stale data if not invalidated.
Write-Through	Read Cache → On miss, Read DB	Write Cache → Write DB synchronously	Cache is always in sync with DB; zero stale reads.	Higher write latency due to dual-writes; populates unrequested data.
Write-Back (Write-Behind)	Read Cache	Write Cache immediately → Async queue writes to DB	Extremely low write latency; absorbs high write traffic spikes.	Risk of data loss if memory store crashes before async DB flush completes.
Common Failure Modes & Mitigations

Cache Avalanche: Thousands of cached keys expire simultaneously, causing a massive surge of database queries.

Mitigation: Add random time-to-live (TTL) jitter (e.g., 300±45 seconds) to desynchronize key expiration times.

Cache Stampede (Thundering Herd): A high-traffic key expires, triggering hundreds of concurrent requests to query the database and regenerate the same key simultaneously.

Mitigation: Use distributed locks (Redis Mutex) so only one worker queries the database while others wait for the refreshed cache.

Cache Penetration: Requests continuously query non-existent primary keys, completely bypassing the cache every time.

Mitigation: Cache null or empty indicator strings with a short TTL, or pre-filter queries using a Bloom filter.

Redis Fundamentals & Python Usage

Redis (Remote Dictionary Server) is an in-memory data structure store used as a database, cache, message broker, and streaming engine. Because it holds datasets in RAM and executes commands via an event loop, reads and writes complete in sub-millisecond speeds.

1. Basic String Key-Value Operations (set, get, setex)
Strings are the foundational data type in Redis. They hold text, serialized JSON, or raw binary payloads up to 512MB.

Python
import redis

# Connect to Redis instance
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Set key with value
r.set("user:101:name", "Alice")

# Read value
name = r.get("user:101:name")
print(f"User Name: {name}")

# Set key with Time-To-Live (TTL) in seconds
r.setex("session:token_99", 60, "active_session_data")
2. Native Data Structures (Hashes & Lists)
Redis supports complex in-memory types like Hashes (field-value maps), Lists (ordered string sequences), Sets, and Sorted Sets.

Python
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# 1. Hashes (Ideal for objects without full JSON string overhead)
r.hset("user:101", mapping={"name": "Alice", "role": "admin", "visits": "5"})
user_role = r.hget("user:101", "role")
full_object = r.hgetall("user:101")
print(f"Hash Object: {full_object}")

# 2. Lists (Ideal for queues or activity feeds)
r.rpush("queue:tasks", "job_1", "job_2", "job_3")
next_job = r.lpop("queue:tasks")
print(f"Processed Job: {next_job}")
3. Key Expiration & Memory Eviction
When Redis reaches its allocated memory limit (maxmemory), it enforces an eviction policy to free space for new writes.

Volatile-LRU: Evicts the least recently used keys among those with an explicit TTL set.

Allkeys-LRU: Evicts the least recently used keys across the entire dataset (standard cache mode).

Noeviction: Returns an error on write attempts when memory is full (standard database mode).

Python
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

r.set("temp_key", "value")
r.expire("temp_key", 30)  # Sets TTL to 30 seconds

time_remaining = r.ttl("temp_key")
print(f"TTL remaining: {time_remaining} seconds")
4. Asynchronous Redis in Python (redis.asyncio)
The redis.asyncio module integrates non-blocking I/O operations into Python's asyncio event loop.

Python
import asyncio
import redis.asyncio as aioredis

async def main():
    # Asynchronous Redis client
    client = aioredis.from_url("redis://localhost:6379", decode_responses=True)
    
    await client.set("async_key", "async_value")
    val = await client.get("async_key")
    print(f"Async Redis Read: {val}")
    
    await client.close()

asyncio.run(main())
FastAPI Caching Integration with Redis

Integrating Redis caching into FastAPI route lifecycles involves managing connection pools inside the lifespan handler and executing non-blocking read/write patterns inside path operations.

1. Cache-Aside Implementation in FastAPI
Routes attempt to read from Redis first. On a cache miss, the route queries the database, serializes the Pydantic schema into JSON, stores it in Redis with a TTL, and returns the response.

Python
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException
import redis.asyncio as aioredis
from pydantic import BaseModel

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class UserProfile(BaseModel):
    user_id: int
    email: str

@app.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: int):
    cache_key = f"cache:users:{user_id}"

    # 1. Read from Redis Cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return UserProfile.model_validate_json(cached_data)

    # 2. Cache Miss: Query Database (Simulated)
    if user_id != 42:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = UserProfile(user_id=42, email="alex@enterprise.com")

    # 3. Write back to Redis with a 300-second TTL
    await redis_client.setex(cache_key, 300, user.model_dump_json())
    return user
2. Mutation-Based Cache Invalidation
When data is updated or deleted in the database, the handler purges the corresponding Redis key (redis.delete()), forcing subsequent reads to load fresh data.

Python
from fastapi import FastAPI, HTTPException
import redis.asyncio as aioredis
from pydantic import BaseModel, EmailStr

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class UserUpdate(BaseModel):
    email: EmailStr

@app.put("/users/{user_id}")
async def update_user_profile(user_id: int, payload: UserUpdate):
    # 1. Update Database Record (Simulated)
    # await db.execute(update(UserORM)...)

    # 2. Invalidate Cache Key
    cache_key = f"cache:users:{user_id}"
    await redis_client.delete(cache_key)

    return {"status": "updated", "invalidated": cache_key}
3. Cache Avalanche Mitigation via TTL Jitter
Adding random seconds to base TTL values prevents synchronized expirations across bulk datasets.

Python
import random
import redis.asyncio as aioredis
from pydantic import BaseModel

async def set_cache_with_jitter(
    redis: aioredis.Redis, 
    key: str, 
    model: BaseModel, 
    base_ttl: int = 300
):
    jitter = random.randint(0, 45)  # Add between 0 and 45 seconds
    await redis.setex(key, base_ttl + jitter, model.model_dump_json())
Unified Enterprise Redis Caching Gateway

This production pattern demonstrates a full FastAPI application incorporating Lifespan resource management, SQLAlchemy 2.0 Async database persistence, Redis Cache-Aside reading with TTL jitter, Cache Invalidation on mutation, and Pydantic serialization.

Python
from contextlib import asynccontextmanager
import random
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, update
from pydantic import BaseModel, Field, ConfigDict
import redis.asyncio as aioredis

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & LIFESPAN MANAGEMENT
# ---------------------------------------------------------------------
SQL_URL = "sqlite+aiosqlite:///enterprise_cache.db"
REDIS_URL = "redis://localhost:6379"

sql_engine = create_async_engine(SQL_URL, echo=False)
session_factory = async_sessionmaker(sql_engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class ProductORM(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables & Redis Connection Pool
    async with sql_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    yield
    # Shutdown: Cleanly close Redis & Database pools
    await app.state.redis.close()
    await sql_engine.dispose()

app = FastAPI(title="Enterprise Product Gateway", lifespan=lifespan)

# Dependencies
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_redis(app_ref: FastAPI) -> aioredis.Redis:
    return app_ref.state.redis

async def redis_dep() -> aioredis.Redis:
    return get_redis(app)

# ---------------------------------------------------------------------
# 2. PYDANTIC SCHEMAS
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

# ---------------------------------------------------------------------
# 3. PATH OPERATIONS
# ---------------------------------------------------------------------
@app.get(
    "/api/v1/products/{product_id}",
    response_model=ProductResponseSchema,
    status_code=status.HTTP_200_OK
)
async def read_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(redis_dep)]
):
    cache_key = f"catalog:products:{product_id}"

    # STEP 1: Check Redis Cache (Fast Path)
    cached_json = await redis.get(cache_key)
    if cached_json:
        return ProductResponseSchema.model_validate_json(cached_json)

    # STEP 2: Cache Miss -> Query Async Database
    stmt = select(ProductORM).where(ProductORM.id == product_id)
    result = await db.execute(stmt)
    product_orm = result.scalar_one_or_none()

    if not product_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product #{product_id} not found"
        )

    response_model = ProductResponseSchema.model_validate(product_orm)

    # STEP 3: Write to Redis with Jitter (Base 300s + Jitter 0-60s)
    base_ttl = 300
    jitter = random.randint(0, 60)
    await redis.setex(cache_key, base_ttl + jitter, response_model.model_dump_json())

    return response_model

@app.put(
    "/api/v1/products/{product_id}",
    response_model=ProductResponseSchema,
    status_code=status.HTTP_200_OK
)
async def update_product(
    product_id: int,
    payload: ProductUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(redis_dep)]
):
    # STEP 1: Update Database Entity
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

    # STEP 2: Retrieve Fresh State
    updated_orm = (await db.execute(
        select(ProductORM).where(ProductORM.id == product_id)
    )).scalar_one()

    # STEP 3: Invalidate Cache Entry
    cache_key = f"catalog:products:{product_id}"
    await redis.delete(cache_key)

    return ProductResponseSchema.model_validate(updated_orm)
Execution Pipeline Explanation:

Lifespan Management: At server startup, lifespan creates the database tables and initializes an asynchronous Redis connection pool attached to app.state.redis.

Cache-Aside Execution (GET): Reads the key catalog:products:{id} from Redis. On a hit, model_validate_json parses the cached JSON payload directly into ProductResponseSchema. On a miss, SQLAlchemy loads the record from SQLite, populates Redis using setex with randomized TTL jitter (300+jitter seconds), and streams the response.

Cache Invalidation Execution (PUT): When product data is updated, SQLAlchemy commits changes to SQLite, and redis.delete() instantly purges the corresponding cache key, preventing stale reads on future queries.