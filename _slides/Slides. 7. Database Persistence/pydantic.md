
# Pydantic persistence

---
### Combine persistence with Pydantic

FastAPI decouples API contracts from database storage by pairing Pydantic models with async database ORMs or drivers

Pydantic:
- validates
- sanitizes
- serializes HTTP data

Database layers:
- persistence
- transactions
- caching

---
### Basic ORM-to-Schema Mapping (SQLAlchemy + Pydantic v2)

To bridge relational database tables with HTTP payloads, separate Pydantic models are used for input (write) and output (read). 

Model_config = ConfigDict(from_attributes=True) enables Pydantic to read raw SQLAlchemy ORM attributes directly!

Real-World Use Case:
- creating and reading simple user profile records in a relational database

Behavior
- input model validates incoming JSON
- output model reads ORM instances returned by AsyncSession and converts them to JSON

```
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select

# Database Infrastructure
engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_factory = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class UserTable(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column()

app = FastAPI()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr

@app.post("/users", response_model=UserResponse)
async def create_user(
    payload: UserCreate, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_db = UserTable(username=payload.username, email=payload.email)
    db.add(user_db)
    await db.commit()
    await db.refresh(user_db)
    return user_db  # Automatically converted via from_attributes=True
```

---
### Relational One-to-Many Nesting & Cascading Writes

Hierarchical Pydantic schemas validate complex incoming JSON trees 

example: 
- order containing multiple line items

The endpoint handler iterates through the validated Pydantic children, converts them into child ORM records, and commits them in a single database transaction.

Real-World Use Case
- submitting a shopping cart order containing an array of item records

Behavior
- if any nested item in the array fails Pydantic validation, no database transaction is opened

```
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

engine = create_async_engine("sqlite+aiosqlite:///:memory:")
session_factory = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class OrderTable(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column()
    items: Mapped[list["OrderItemTable"]] = relationship(back_populates="order", cascade="all, delete-orphan")

class OrderItemTable(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    sku: Mapped[str] = mapped_column()
    quantity: Mapped[int] = mapped_column()
    order: Mapped["OrderTable"] = relationship(back_populates="items")

app = FastAPI()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session

# Nested Pydantic Schemas
class OrderItemCreate(BaseModel):
    sku: str
    quantity: int = Field(gt=0)

class OrderCreate(BaseModel):
    customer_id: str
    items: list[OrderItemCreate] = Field(min_length=1)

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sku: str
    quantity: int

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: str
    items: list[OrderItemResponse]

@app.post("/orders", response_model=OrderResponse)
async def create_order(
    payload: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Map Pydantic trees to ORM Trees
    new_order = OrderTable(
        customer_id=payload.customer_id,
        items=[OrderItemTable(sku=i.sku, quantity=i.quantity) for i in payload.items]
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    return new_order
3. Custom Validation Rules & Document Stores (MongoDB / Motor)

Document databases store dynamic, unstructured JSON records. Pydantic models enforce application-level business rules (@field_validator and @model_validator) before sending clean Python dictionaries (.model_dump()) to driver collections.

Real-World Use Case: Inserting flexible device configuration documents into MongoDB while guaranteeing proper normalization and validation.

Behavior: MongoDB accepts arbitrary payloads, but Pydantic enforces strict runtime validation before writing to disk.

Python
from typing import Annotated, Self
from fastapi import FastAPI, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field, field_validator, model_validator

app = FastAPI()
mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")

def get_mongo_db() -> AsyncIOMotorDatabase:
    return mongo_client["telemetry_db"]

class DeviceConfig(BaseModel):
    device_id: str = Field(pattern=r"^DEV-\d{4}$")
    region: str
    min_threshold: float
    max_threshold: float

    @field_validator("region")
    @classmethod
    def force_uppercase(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def validate_thresholds(self) -> Self:
        if self.min_threshold >= self.max_threshold:
            raise ValueError("min_threshold must be strictly less than max_threshold")
        return self

@app.post("/devices")
async def register_device(
    config: DeviceConfig,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)]
):
    # Store validated document directly into MongoDB
    document = config.model_dump()
    result = await db["devices"].insert_one(document)
    return {"inserted_id": str(result.inserted_id), "status": "configured"}
4. Dynamic Response Calculation & In-Memory Caching (@computed_field + Redis)

Combining @computed_field with an in-memory Redis cache allows FastAPI to store raw validated payloads as JSON strings (.model_dump_json()) and rehydrate them instantly on reads (.model_validate_json()), avoiding database joins and custom serialization code.

Real-World Use Case: High-speed retrieval of inventory stock cards with automatic tax or margin calculations.

Behavior: Redis handles cached raw values, and Pydantic evaluates @computed_field during serialization on cache hits.

Python
from typing import Annotated
from fastapi import FastAPI, Depends
import redis.asyncio as aioredis
from pydantic import BaseModel, ConfigDict, computed_field

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

class ProductCacheModel(BaseModel):
    id: int
    name: str
    wholesale_cost: float
    margin_percent: float

    @computed_field
    @property
    def retail_price(self) -> float:
        return round(self.wholesale_cost * (1 + self.margin_percent / 100), 2)

@app.get("/products/{product_id}", response_model=ProductCacheModel)
async def get_product_details(product_id: int):
    cache_key = f"product:{product_id}"
    
    # 1. Check Redis Cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        # Rehydrate Pydantic model directly from JSON string
        return ProductCacheModel.model_validate_json(cached_data)

    # 2. Database Fallback (Simulated)
    product_obj = ProductCacheModel(
        id=product_id, name="Server Rack Unit", wholesale_cost=500.0, margin_percent=25.0
    )
    
    # 3. Save serialized Pydantic model into Redis with a 60-second TTL
    await redis_client.setex(cache_key, 60, product_obj.model_dump_json())
    return product_obj
Unified Enterprise Hybrid Database & Pydantic Pipeline

This production pattern demonstrates an e-commerce order entry and retrieval engine. It combines SQLAlchemy 2.0 (Async PostgreSQL/SQLite) for ACID storage, Redis for read-through caching, and Pydantic v2 for validation, nested schema parsing, field transformations, and computed metrics.