FastAPI executes database interactions asynchronously through dependency injection, mapping relational ORM entities and NoSQL documents directly to Pydantic schemas without blocking the ASGI event loop.

1. Relational SQL Database Access (SQLAlchemy 2.0 / SQLModel)
Relational databases enforce fixed schemas, table joins, and ACID compliance. SQLAlchemy 2.0 and SQLModel use create_async_engine and AsyncSession to perform non-blocking database queries over drivers like asyncpg or aiosqlite.

Real-World Use Case: Financial ledgers, user management, and order processing systems requiring strict relational constraints and transactional rollback guarantees.

Behavior: Database models inherit from declarative ORM bases, while Pydantic schemas validate input/output payloads.

Python
from typing import Annotated
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select

# 1. Engine & Session Setup
engine = create_async_engine("sqlite+aiosqlite:///:memory:")
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# 2. ORM Model
class Base(DeclarativeBase):
    pass

class UserTable(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)

app = FastAPI()

# 3. Session Dependency
async def get_db_session():
    async with async_session_factory() as session:
        yield session

@app.get("/users/{user_id}")
async def get_user(
    user_id: int, 
    session: Annotated[AsyncSession, Depends(get_db_session)]
):
    result = await session.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalar_one_or_none()
    return {"id": user.id, "email": user.email} if user else {"error": "Not found"}
2. Session Lifecycle & Yield Dependencies (get_db)
A yield dependency manages the operational lifecycle of a database connection per HTTP request. Code before yield initializes the connection; code after yield closes or releases the connection back to the connection pool.

Real-World Use Case: Preventing database pool exhaustion by ensuring open transactions roll back safely on exceptions and close after the response is dispatched.

Behavior: The context block ensures teardown logic (session.close()) executes even if an unhandled exception occurs inside the path operation.

Python
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on clean completion
        except Exception:
            await session.rollback()  # Auto-rollback on route failure
            raise
3. Document NoSQL Database Access (MongoDB / Motor)
Document-oriented NoSQL databases store flexible, hierarchical JSON/BSON records. Drivers like Motor provide native async/await bindings for MongoDB operations.

Real-World Use Case: Product catalog management, variable user settings, or content management systems (CMS) with unpredictable document fields.

Behavior: Pydantic models convert raw BSON dictionaries returned by Motor into strongly typed Python objects.

Python
from typing import Annotated
from fastapi import FastAPI, Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field

app = FastAPI()

# MongoDB Client Setup
mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")

def get_mongo_db() -> AsyncIOMotorDatabase:
    return mongo_client["inventory_db"]

class ProductDocument(BaseModel):
    name: str
    attributes: dict  # Dynamic nested key-value pairs

@app.post("/products")
async def create_product(
    product: ProductDocument,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)]
):
    result = await db["products"].insert_one(product.model_dump())
    return {"inserted_id": str(result.inserted_id), "name": product.name}
4. Key-Value & Cache Stores (Redis)
Key-value NoSQL stores operate in memory to provide sub-millisecond data reads, publish-subscribe messaging, and automatic key expiration times (TTL).

Real-World Use Case: Rate limiting, session token storage, and caching expensive database query outputs.

Behavior: Interacts with async clients (redis.asyncio) to fetch cached byte strings and deserialize them into Pydantic models.

Python
from typing import Annotated
from fastapi import FastAPI, Depends
import redis.asyncio as aioredis

app = FastAPI()
redis_pool = aioredis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)

async def get_redis():
    return redis_pool

@app.get("/cache/{key}")
async def get_cached_value(
    key: str, 
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    val = await redis.get(key)
    return {"key": key, "value": val, "hit": val is not None}
Architectural Framework: SQL vs. NoSQL

Choosing between SQL and NoSQL depends on data relationships, transactional guarantees, and schema flexibility.

Evaluation Metric	Relational SQL (PostgreSQL, MySQL)	Document NoSQL (MongoDB)	Key-Value NoSQL (Redis)
Data Structure	Strict Tables, Columns, Foreign Keys	Flexible JSON / BSON Documents	Key-Value Strings, Hashes, Sets
Transactions	Full ACID (Atomicity, Isolation)	Single-Document ACID (Multi-doc supported)	Atomic operations per command
Query Mechanism	Structured SQL, Relational Joins	Document Query APIs, Aggregations	Direct Key Lookups, Range Queries
Scaling Pattern	Vertical (Scale Up) / Read Replicas	Horizontal Sharding (Scale Out)	In-memory Horizontal Cluster
Primary Use Case	Financials, Core Orders, Users	Catalogs, Unstructured Telemetry	Caching, Rate Limits, Sessions
Decision Rules:

Use SQL when: Data integrity is critical, entities are highly interconnected (e.g., Users → Orders → Payments), and schema modifications must be controlled via migrations.

Use Document NoSQL when: Data structures change frequently, payloads contain deeply nested lists/objects, or horizontal read/write throughput requires distributed sharding.

Use Key-Value NoSQL when: Data requires temporary lifetimes (TTL), sub-millisecond response latency is needed, or access patterns rely purely on primary key identifiers.

Unified Enterprise Hybrid Database Request Flow

This production pattern demonstrates a hybrid architecture using PostgreSQL (via SQLAlchemy 2.0 Async Session) for transactional order processing alongside Redis for high-speed rate-limiting and query caching.

Python
from datetime import datetime, timezone
import json
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

# =====================================================================
# 1. DATABASE SETUP & INFRASTRUCTURE
# =====================================================================
SQL_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # Swap with postgresql+asyncpg in prod
REDIS_URL = "redis://localhost:6379"

sql_engine = create_async_engine(SQL_DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(sql_engine, expire_on_commit=False)
redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

# SQL Declarative Models
class Base(DeclarativeBase):
    pass

class OrderRecord(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column()
    quantity: Mapped[int] = mapped_column()
    total_price: Mapped[float] = mapped_column()

# Pydantic Input/Output Schemas
class OrderCreateSchema(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)

class OrderResponseSchema(BaseModel):
    id: int
    sku: str
    quantity: int
    total_price: float

app = FastAPI()

# Create Tables on Startup
@app.on_event("startup")
async def startup_event():
    async with sql_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# =====================================================================
# 2. DEPENDENCY INJECTION PIPELINE
# =====================================================================
async def get_sql_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional AsyncSession with automatic cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def verify_rate_limit(
    x_client_id: Annotated[str, Header()],
):
    """NoSQL Rate Limiting Guard using Redis TTL counters."""
    rate_key = f"rate:{x_client_id}"
    requests = await redis_client.incr(rate_key)
    if requests == 1:
        await redis_client.expire(rate_key, 60)  # 60-second window
    
    if requests > 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 10 requests per minute."
        )

# =====================================================================
# 3. HYBRID PATH OPERATIONS
# =====================================================================
@app.post(
    "/orders",
    response_model=OrderResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_rate_limit)]
)
async def place_order(
    payload: OrderCreateSchema,
    db: Annotated[AsyncSession, Depends(get_sql_db)]
):
    # 1. ACID Transaction in Relational SQL Store
    total = payload.quantity * payload.unit_price
    db_order = OrderRecord(sku=payload.sku, quantity=payload.quantity, total_price=total)
    db.add(db_order)
    await db.flush()  # Populates db_order.id within transaction boundary

    # 2. Invalidate NoSQL Redis Cache for catalog updates
    await redis_client.delete(f"cache:orders:{db_order.id}")

    return OrderResponseSchema(
        id=db_order.id,
        sku=db_order.sku,
        quantity=db_order.quantity,
        total_price=db_order.total_price
    )

@app.get(
    "/orders/{order_id}",
    response_model=OrderResponseSchema,
    dependencies=[Depends(verify_rate_limit)]
)
async def get_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_sql_db)]
):
    cache_key = f"cache:orders:{order_id}"

    # Step A: Check NoSQL Redis Cache (Sub-millisecond read)
    cached_order = await redis_client.get(cache_key)
    if cached_order:
        return OrderResponseSchema.model_validate_json(cached_order)

    # Step B: Cache Miss -> Fallback to Relational SQL Query
    result = await db.execute(select(OrderRecord).where(OrderRecord.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order record not found")

    response_data = OrderResponseSchema(
        id=order.id,
        sku=order.sku,
        quantity=order.quantity,
        total_price=order.total_price
    )

    # Step C: Populate NoSQL Redis Cache with 5-minute TTL
    await redis_client.setex(
        cache_key,
        300,
        response_data.model_dump_json()
    )

    return response_data
Execution Pipeline Explanation:

Rate Limiting Guard: Requests hitting /orders evaluate verify_rate_limit. Redis increments the rate:client_id key using an atomic INCR operation. If execution exceeds 10 calls per minute, execution halts with an HTTP 429 error.

ACID Transactional Writes: place_order instantiates OrderRecord within a SQL transaction managed by the get_sql_db yield generator. Calling await db.flush() writes the record and generates a primary key (id). When the function returns, get_sql_db executes await session.commit().

Read-Through Cache Pattern: get_order queries the Redis cache using cache:orders:{order_id}. On a cache hit, it parses the JSON string directly into a Pydantic model (model_validate_json), skipping the SQL database. On a cache miss, it queries PostgreSQL via SQLAlchemy, populates the Redis cache with a 300-second Time-To-Live (setex), and returns the payload.