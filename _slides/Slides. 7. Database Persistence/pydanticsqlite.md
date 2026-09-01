# Integrated Pipeline

---
### Integrated Pipeline

FastAPI processes data by passing HTTP request payloads through Pydantic models for validation, writing them to an underlying persistence layer like SQLite, and re-serializing database outputs back through Pydantic response models into JSON streams

---
### Basic Pipeline

Request → Validation → SQLite → Response

An incoming HTTP JSON payload is parsed into an input Pydantic model. The route handler writes the validated fields to SQLite using parameterized SQL, queries the saved record, and serializes it through an output Pydantic model

Real-World Use Case
- simple user creation or system registration endpoints

Behavior
- invalid request payloads return an HTTP 422 error immediately, preventing unvalidated writes from reaching the database cursor.

```
import sqlite3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr

app = FastAPI()

def get_db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

# 1. Request Input Schema
class UserCreate(BaseModel):
    username: str
    email: EmailStr

# 2. Response Output Schema
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Write to SQLite persistence layer
    try:
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)", 
            (payload.username, payload.email)
        )
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    # Read back from SQLite
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    # Convert SQLite row to dict and validate against output schema
    return UserResponse(**dict(row))
```

---
### Inbound Data Sanitization & Business Rules

Before touching the database, Pydantic @field_validator and @model_validator functions validate constraints (e.g., regex patterns, range checks, matching fields) to ensure database constraints are never violated

Real-World Use Case
- enforcing formatted hardware serial numbers or verifying password matching prior to database execution

Behavior
- runs synchronously during payload ingestion before the route function executes

```
from typing import Self
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator, model_validator

app = FastAPI()

class InventoryItemCreate(BaseModel):
    sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$")
    cost_price: float = Field(gt=0.0)
    selling_price: float = Field(gt=0.0)

    @field_validator("sku")
    @classmethod
    def force_uppercase(cls, v: str) -> str:
        return v.upper()

    # Validate cross-field relationships
    @model_validator(mode="after")
    def check_profit_margin(self) -> Self:
        if self.selling_price <= self.cost_price:
            raise ValueError("selling_price must be greater than cost_price")
        return self

# Incoming JSON: {"sku": "abc-1234", "cost_price": 10.0, "selling_price": 15.0}
# Pydantic normalizes SKU to "ABC-1234" and verifies selling_price > cost_price
```

---
### Outbound Mapping & Computed Response Fields 

Output models:
- use ConfigDict(from_attributes=True) to map database objects/dictionaries into response attributes 
- @computed_field dynamically generates calculated fields during JSON serialization

Real-World Use Case
- returning database records with dynamically calculated totals without storing redundant calculated values in SQLite

Behavior
- @computed_field attributes evaluate automatically upon serialization

```
from pydantic import BaseModel, ConfigDict, computed_field

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    tax_rate: float = 0.20

    # Dynamically calculated during JSON response output
    @computed_field
    @property
    def total_price(self) -> float:
        return round(self.price * (1 + self.tax_rate), 2)

```
--- 
### Async Database Persistence 

Standard sqlite3 blocks Python's single-threaded event loop during disk reads/writes
- using an asynchronous driver keeps the ASGI loop unblocked during database I/O

Real-World Use Case
- high-throughput API services requiring concurrent database processing under heavy traffic load

Behavior
- database operations use await statements, allowing FastAPI to process other HTTP requests 

```
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Async Engine targeting SQLite file via aiosqlite
engine = create_async_engine("sqlite+aiosqlite:///app_async.db")
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

# Usage in route:
# async def my_route(db: Annotated[AsyncSession, Depends(get_db_session)]): ...
```

---
### Unified Enterprise Request-to-Response Pipeline

This production pattern demonstrates an end-to-end e-commerce invoice management system. It accepts raw JSON, validates business rules in Pydantic, persists records in SQLite asynchronously, reads the ORM entity back, and formats calculated output attributes in the final HTTP JSON response

```
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

# ---------------------------------------------------------------------
# 1. DATABASE SETUP (SQLite + aiosqlite Async Driver)
# ---------------------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///invoices.db"

engine = create_async_engine(DATABASE_URL, echo=False)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Relational ORM Entities
class InvoiceORM(Base):
    __tablename__ = "invoices"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_email: Mapped[str] = mapped_column()
    currency: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    items: Mapped[list["InvoiceItemORM"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", lazy="selectin"
    )

class InvoiceItemORM(Base):
    __tablename__ = "invoice_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    description: Mapped[str] = mapped_column()
    unit_price: Mapped[float] = mapped_column()
    quantity: Mapped[int] = mapped_column()

    invoice: Mapped["InvoiceORM"] = relationship(back_populates="items")

app = FastAPI(title="Enterprise Invoice Engine")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# ---------------------------------------------------------------------
# 2. PYDANTIC MODEL CONTRACTS
# ---------------------------------------------------------------------

# Input Item Payload Schema
class InvoiceItemCreate(BaseModel):
    description: str = Field(min_length=2)
    unit_price: float = Field(gt=0.0)
    quantity: int = Field(gt=0, le=500)

# Input Invoice Payload Schema
class InvoiceCreate(BaseModel):
    client_email: EmailStr
    currency: str = Field(min_length=3, max_length=3)
    items: list[InvoiceItemCreate] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def force_uppercase_currency(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode="after")
    def validate_minimum_invoice_value(self) -> Self:
        estimated_total = sum(i.unit_price * i.quantity for i in self.items)
        if estimated_total < 5.0:
            raise ValueError("Total invoice value must be at least 5.00 currency units.")
        return self

# Output Item Serialization Schema
class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    description: str
    unit_price: float
    quantity: int

    @computed_field
    @property
    def line_total(self) -> float:
        return round(self.unit_price * self.quantity, 2)

# Output Invoice Serialization Schema
class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_email: str
    currency: str
    created_at: datetime
    items: list[InvoiceItemResponse]

    @computed_field
    @property
    def subtotal(self) -> float:
        return round(sum(item.line_total for item in self.items), 2)

    @computed_field
    @property
    def sales_tax(self) -> float:
        return round(self.subtotal * 0.15, 2)  # 15% Tax

    @computed_field
    @property
    def total_due(self) -> float:
        return round(self.subtotal + self.sales_tax, 2)

# ---------------------------------------------------------------------
# 3. FASTAPI ROUTE PIPELINE EXECUTION
# ---------------------------------------------------------------------

@app.post(
    "/api/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Invoices"]
)
async def create_invoice(
    payload: InvoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # STEP 1: Incoming JSON is validated by Pydantic:
    #         - Email syntax verified
    #         - Currency transformed to uppercase ("usd" -> "USD")
    #         - Minimum value check performed ($5.00 threshold)
    
    # STEP 2: Map validated Pydantic models to SQLAlchemy ORM Entities
    invoice_orm = InvoiceORM(
        client_email=payload.client_email,
        currency=payload.currency,
        items=[
            InvoiceItemORM(
                description=item.description,
                unit_price=item.unit_price,
                quantity=item.quantity
            )
            for item in payload.items
        ]
    )

    # STEP 3: Persist asynchronously into SQLite database file
    db.add(invoice_orm)
    await db.flush()  # Generates primary key 'id' inside transaction
    await db.refresh(invoice_orm)

    # STEP 4: FastAPI maps InvoiceORM into InvoiceResponse:
    #         - from_attributes=True reads ORM fields directly
    #         - Evaluates line_total for each item
    #         - Evaluates subtotal, sales_tax, and total_due
    #         - Returns final JSON stream to client
    return invoice_orm

@app.get(
    "/api/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    tags=["Invoices"]
)
async def get_invoice(
    invoice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Fetch record asynchronously from SQLite
    result = await db.execute(
        select(InvoiceORM).where(InvoiceORM.id == invoice_id)
    )
    invoice_orm = result.scalar_one_or_none()

    if not invoice_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )

    return invoice_orm
```

---
### Execution Pipeline Lifecycle:

- Request Ingestion & Validation: A client submits a POST request to /api/invoices. FastAPI passes the payload to InvoiceCreate. If validation fails (e.g., negative price or total under 5.00), Pydantic raises a ValidationError, halting execution and returning an HTTP 422 JSON response.

- ORM Mapping: The route handler maps validated InvoiceCreate fields into an InvoiceORM entity tree containing child InvoiceItemORM records.

- Non-Blocking Persistence: db.add(invoice_orm) and await db.flush() asynchronously insert records into invoices and invoice_items tables in SQLite without blocking the main event loop.

- Response Transformation: The route handler returns invoice_orm. FastAPI converts the ORM instance using InvoiceResponse (ConfigDict(from_attributes=True)). During serialization, Pydantic calculates line_total, subtotal, sales_tax, and total_due dynamically before emitting the final HTTP 201 JSON payload.