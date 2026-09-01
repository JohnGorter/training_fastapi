# End to end FastAPI

The end-to-end FastAPI request pipeline moves data through five distinct stages: 
- HTTP payload ingestion
- Pydantic input validation
- SQLAlchemy 2.0 ORM mapping
- SQLite disk persistence
- Pydantic output serialization

---
### Inbound Ingestion & Validation (HTTP JSON -> Pydantic Input)

Raw JSON payloads sent via HTTP POST or PUT enter FastAPI and are parsed into Pydantic input schemas 

Before any business logic or database code executes, Pydantic validates:
- data types
- string patterns
- value ranges 

Behavior
- if payload attributes fail validation, FastAPI aborts the pipeline and returns HTTP 422 error

```
class AccountCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    initial_deposit: float = Field(gt=0.0)

# HTTP Request: {"username": "alice", "email": "alice@site.com", "initial_deposit": 150.0}
# Pydantic validates input attributes synchronously before route handler execution.
```

---
### Data Handoff & ORM Ingestion (Pydantic Input -> SQLAlchemy 2.0 ORM)

Once the input Pydantic model validates the payload, the route handler converts the Pydantic dictionary (payload.model_dump()) into a SQLAlchemy 2.0 ORM model instance

Behavior
- the ORM entity binds validated values to typed database columns (Mapped[T]) defined in the declarative schema

```
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class AccountORM(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column()
    balance: Mapped[float] = mapped_column()

# Route Conversion Step:
# account_db = AccountORM(**payload.model_dump())
```

---
### Async Database Persistence (SQLAlchemy ORM -> SQLite File)

An injected AsyncSession dependency receives the ORM instance, adds it to the transaction pipeline, and flushes/commits the changes to disk via the non-blocking aiosqlite driver

Behavior
- db.flush() forces SQLite to generate primary keys (e.g., id) inside the active transaction
- db.commit() saves the record permanently

```
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///bank.db")
session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
        await session.commit()

# Route Persistence Execution:
# db.add(account_db)
# await db.flush()  # Primary Key 'id' is generated here
```

---
### Outbound Mapping & Computed Response (SQLite -> Pydantic Response)

After database operations complete, the resulting SQLAlchemy ORM entity is passed to an output Pydantic model configured with ConfigDict(from_attributes=True)

Behavior
- Pydantic reads attributes directly from the ORM object and evaluates any @computed_field methods for the outgoing payload

```
from pydantic import BaseModel, ConfigDict, computed_field

class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    balance: float

    @computed_field
    @property
    def account_tier(self) -> str:
        return "Gold" if self.balance >= 100.0 else "Standard"

# Conversion: AccountResponse.model_validate(account_db)
```

---
### Outbound Payload Streaming (Pydantic Response -> HTTP JSON)

FastAPI serializes the output Pydantic model into a clean JSON string, sets HTTP headers (such as Content-Type: application/json), and streams the HTTP 200/201 response back to the client

Unified End-to-End Enterprise Request-to-Response Pipeline

```
ximport asyncio
from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator, Self
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, select
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
    computed_field,
)

# =====================================================================
# STAGE 1: DATABASE ENGINE & ORM SETUP (SQLAlchemy 2.0 + SQLite)
# =====================================================================
DATABASE_URL = "sqlite+aiosqlite:///enterprise_store.db"

engine = create_async_engine(DATABASE_URL, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class OrderORM(Base):
    __tablename__ = "store_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_email: Mapped[str] = mapped_column()
    currency: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(default="CONFIRMED")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    items: Mapped[list["OrderItemORM"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )

class OrderItemORM(Base):
    __tablename__ = "store_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("store_orders.id"))
    sku: Mapped[str] = mapped_column()
    unit_price: Mapped[float] = mapped_column()
    quantity: Mapped[int] = mapped_column()

    order: Mapped["OrderORM"] = relationship(back_populates="items")

# Dependency: Database Session Provider
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# =====================================================================
# STAGE 2: PYDANTIC SCHEMAS (Input Validation & Output Formatting)
# =====================================================================

# --- INBOUND REQUEST SCHEMAS ---
class ItemCreateRequest(BaseModel):
    sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$", description="Format: ABC-1234")
    unit_price: float = Field(gt=0.0)
    quantity: int = Field(gt=0, le=100)

class OrderCreateRequest(BaseModel):
    customer_email: EmailStr
    currency: str = Field(min_length=3, max_length=3)
    items: list[ItemCreateRequest] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def force_uppercase_currency(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def validate_minimum_order_total(self) -> Self:
        total = sum(item.unit_price * item.quantity for item in self.items)
        if total < 10.0:
            raise ValueError("Minimum order value must be at least 10.00 currency units.")
        return self

# --- OUTBOUND RESPONSE SCHEMAS ---
class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    unit_price: float
    quantity: int

    @computed_field
    @property
    def line_subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_email: str
    currency: str
    status: str
    created_at: datetime
    items: list[ItemResponse]

    @computed_field
    @property
    def subtotal(self) -> float:
        return round(sum(item.line_subtotal for item in self.items), 2)

    @computed_field
    @property
    def estimated_tax(self) -> float:
        return round(self.subtotal * 0.10, 2)  # 10% tax calculation

    @computed_field
    @property
    def grand_total(self) -> float:
        return round(self.subtotal + self.estimated_tax, 2)

# =====================================================================
# STAGE 3: FASTAPI APPLICATION & ROUTE PIPELINE
# =====================================================================
app = FastAPI(title="Full-Pipeline Store API")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post(
    "/api/v1/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Orders"]
)
async def create_order(
    payload: OrderCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    # 1. Pydantic validated input: email syntax, SKU pattern, uppercase currency, min $10 total.
    
    # 2. Convert Pydantic models to SQLAlchemy ORM Entities
    order_orm = OrderORM(
        customer_email=payload.customer_email,
        currency=payload.currency,
        items=[
            OrderItemORM(
                sku=item.sku,
                unit_price=item.unit_price,
                quantity=item.quantity
            )
            for item in payload.items
        ]
    )

    # 3. Persist asynchronously in SQLite
    db.add(order_orm)
    await db.flush()     # Forces database to populate order_orm.id
    await db.refresh(order_orm)

    # 4. Return ORM instance; FastAPI automatically maps it to OrderResponse
    return order_orm

@app.get(
    "/api/v1/orders/{order_id}",
    response_model=OrderResponse,
    tags=["Orders"]
)
async def get_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    # Fetch ORM record from SQLite database
    stmt = select(OrderORM).where(OrderORM.id == order_id)
    result = await db.execute(stmt)
    order_orm = result.scalar_one_or_none()

    if not order_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order #{order_id} not found."
        )

    return order_orm
```

---
### Execution Pipeline Explanation

- HTTP Request Ingestion: The client dispatches a POST request to /api/v1/orders containing a JSON payload with customer email, currency code, and an array of items.

- Pydantic Input Validation: FastAPI passes the raw JSON to OrderCreateRequest. Pydantic validates customer_email, verifies SKU syntax against ^[A-Z]{3}-\d{4}$, normalizes "usd" to "USD", and confirms the minimum order total reaches $10.00.

- ORM Transformation: Inside create_order, the application instantiates OrderORM and OrderItemORM entities from the validated Pydantic model attributes.

- Async SQLite Storage: db.add(order_orm) registers the objects with the SQLAlchemy session. await db.flush() issues non-blocking SQL INSERT statements via aiosqlite, generating primary keys (id) without closing the active transaction.

- ORM-to-Pydantic Response Serialization: The endpoint returns order_orm. FastAPI uses OrderResponse (ConfigDict(from_attributes=True)) to extract values from ORM properties, compute dynamic fields (line_subtotal, subtotal, estimated_tax, and grand_total), and serialize the structured output into a standard HTTP 201 JSON response stream.
