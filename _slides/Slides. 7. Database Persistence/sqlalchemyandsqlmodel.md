
# ORM

---
### ORM

Object-Relational Mapping (ORM) is a software design pattern that creates a virtual object database bridge between object-oriented programming languages (like Python) and relational databases (like SQLite, PostgreSQL, or MySQL)

---
### Key ORM Concepts

- Object-Relational Impedance Mismatch: The fundamental conceptual friction between object-oriented programming (classes, inheritance, objects with behaviors) and relational databases (tables, foreign keys, set theory, normalization).
- The Active Record Pattern: A pattern where a single class directly corresponds to a database table, and an instance of that class represents a single row (e.g., Django ORM, SQLModel).
- The Data Mapper Pattern: A pattern that decouples the in-memory domain representation from the database schema using a separate mapping layer and session manager (e.g., SQLAlchemy).
- Unit of Work: A mechanism that tracks changes made to in-memory domain objects during a business transaction and flushes all changes to the database in a single, optimized SQL batch.

---
### Use Cases

- Abstracting SQL Syntax: Writing database-agnostic code that seamlessly switches between SQLite during local development and PostgreSQL or MySQL in production.
- Eliminating Boilerplate: Avoiding manually written, repetitive SQL string concatenation (INSERT INTO..., UPDATE...) for standard CRUD operations.
- Type Safety & Data Validation: Ensuring database outputs convert automatically into strongly typed, auto-completable Python objects rather than un-typed raw tuples.
- Relationship Management: Traversing foreign key relationships using object attributes (e.g., user.orders) instead of explicitly authoring SQL JOIN clauses.

---
### The Fundamental Problem: Object-Relational Impedance Mismatch

Object-oriented programming and relational databases organize data around completely different paradigms

An ORM exists specifically to bridge these five core mismatches
-  Granularity Mismatch: Objects can represent complex composite types (e.g., an Address object nested inside a User object), whereas relational databases only support scalar primitives (integers, strings, booleans) across columns.
-  Subtype / Inheritance Mismatch: Object-oriented languages natively support inheritance (Admin extends User), but relational databases have no standard concept of class inheritance—only tables.
-  Identity Mismatch: Python compares objects by memory reference (a is b) or equality (a == b). Databases compare rows strictly by Primary Keys (PRIMARY KEY).
- Association Mismatch: Objects handle references as unidirectional pointers (user.order). Relational databases use bidirectional Foreign Keys (order.user_id = user.id).
- Navigation Mismatch: Objects navigate relationships by traversing pointers (user.orders[0].items), while databases require declarative set queries (SELECT ... JOIN ...).

---
### Core Mechanics Explained

Lets explore the mechanics:
1. Schema Mapping (Class-to-Table Definition)
2. Query Translation (Objects to SQL)
3. Identity Map & Dirty Tracking (Unit of Work)

---
### Schema Mapping  

The ORM maps Python classes to database tables and class attributes to database columns

```
# The Class represents the Table
# Class attributes represent Columns
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
```

---
### Query Translation 

Instead of string-concatenated SQL queries, the ORM constructs an Abstract Syntax Tree (AST) in Python and compiles it into database-specific SQL dialect.

```
Python Code:          select(User).where(User.username == "alice")
                            │
                            ▼ (ORM Compiler)
Generated SQL:        SELECT users.id, users.username, users.email 
                      FROM users 
                      WHERE users.username = 'alice';
```

---
### Identity Map & Dirty Tracking

The ORM tracks object modifications in memory. When attributes change, the session registers the object as "dirty" and generates the necessary UPDATE query only when committed

```
# 1. ORM fetches row and stores in Identity Map
user = session.get(User, 1)

# 2. Modify Python object in memory (No SQL executed yet)
user.email = "new_email@example.com"

# 3. Unit of Work detects dirty state and emits UPDATE statement
session.commit()
```

---
### ORM Frameworks

Lets explore two ORM frameworks
- SQLAlchemy
- SQLModel

---
### SQLAlchemy 

the standard Object-Relational Mapping (ORM) library for Python

---
### Key SQLAlchemy Concepts

- Engine (create_engine / create_async_engine): The core connection pool manager that handles network/file communication with the underlying database.
-  Declarative Base (DeclarativeBase): A base class used to define Python classes that map directly to database tables.
- Mapped & mapped_column: Type-hinted descriptors used in SQLAlchemy 2.0+ to define column names, data types, primary keys, and constraints.
- Session (Session / AsyncSession): The transactional workspace that tracks changes to Python objects and synchronizes them with the database (the Unit of Work pattern).

---
### Use Cases

- Enterprise Web APIs: Building structured REST or GraphQL backends with strongly-typed database models
- Complex Data Relationships: Managing one-to-many, many-to-many, and foreign key cascades without writing verbose JOIN queries manually
- Database Agnosticism: Writing application code that can run on SQLite during local testing and switch to PostgreSQL or MySQL in production with zero code changes

---
### Python Driver & Library Setup

Install SQLAlchemy 2.0+ with asynchronous support, Pydantic, and aiosqlite:

```
uv add "sqlalchemy>=2.0" pydantic fastapi uvicorn aiosqlite
```

---
### Core Operations (CRUD)

Lets explore the steps to get this to work:
1. Defining Models and Initializing Engine
2. Adding Data (Create)
3. Listing Data (Read)
4. Changing Data (Update)
5. Deleting Data (Delete)

---
### Defining Models

Create the declarative base and map a Python class to a database table.

```
import asyncio
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 1. Base class
class Base(AsyncAttrs, DeclarativeBase):
    pass

# 2. Database Model
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    stock: Mapped[int] = mapped_column(default=0)

# 3. Engine and Session factory
engine = create_async_engine("sqlite+aiosqlite:///store.db")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

---
### Adding Data (Create)

Instantiate Python objects and add them to the session, then call commit().

```
async def create_products():
    async with AsyncSessionLocal() as session:
        # Create single instance
        mouse = Product(name="Wireless Mouse", price=29.99, stock=150)
        session.add(mouse)

        # Create multiple instances
        bulk_items = [
            Product(name="Mechanical Keyboard", price=89.99, stock=45),
            Product(name="USB-C Hub", price=19.99, stock=200)
        ]
        session.add_all(bulk_items)
        
        await session.commit()
```

---
### Listing Data 

Execute select() statements using SQLAlchemy's modern 2.0 syntax.

```
async def read_products():
    async with AsyncSessionLocal() as session:
        # Fetch single record
        stmt = select(Product).where(Product.name == "Wireless Mouse")
        result = await session.execute(stmt)
        mouse = result.scalar_one_or_none()

        # Fetch multiple records
        stmt = select(Product).where(Product.price > 20.0)
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        for p in products:
            print(p.name, p.price)
```

---
### Changing Data (Update)

Fetch objects within a session, modify their Python attributes directly, and commit. SQLAlchemy automatically detects modifications (dirty checking).

```
async def update_products():
    async with AsyncSessionLocal() as session:
        stmt = select(Product).where(Product.name == "Wireless Mouse")
        result = await session.execute(stmt)
        mouse = result.scalar_one_or_none()
        
        if mouse:
            mouse.stock -= 1  # Modify attribute directly
            await session.commit()  # Generates UPDATE SQL statement
```

---
### Deleting Data 

Mark an object for deletion using session.delete()

```
async def delete_products():
    async with AsyncSessionLocal() as session:
        stmt = select(Product).where(Product.name == "USB-C Hub")
        result = await session.execute(stmt)
        hub = result.scalar_one_or_none()
        
        if hub:
            await session.delete(hub)
            await session.commit()
```

---
### SQLAlchemy + FastAPI + Pydantic Integration

When building APIs, responsibilities are split between two distinct model types:
- SQLAlchemy Models: Represent database tables, columns, and persistent storage mechanics.
- Pydantic Models (Schemas): Handle data validation, serializing response JSON, and parsing incoming request bodies.

Setting model_config = ConfigDict(from_attributes=True) inside a Pydantic model allows it to read data directly from SQLAlchemy ORM objects.

---
### SQLAlchemy + FastAPI + Pydantic Integration


```
Incoming HTTP Request (JSON) 
       │
       ▼
Pydantic Request Schema (Validation)
       │
       ▼
SQLAlchemy ORM Model (Database Logic)
       │
       ▼
Pydantic Response Schema (Serialization)
       │
       ▼
Outgoing HTTP Response (JSON)
```

---
### Real-Life FastAPI & Pydantic Application

This application demonstrates managing an inventory catalog using FastAPI, Pydantic v2, SQLAlchemy 2.0, and FastAPI Lifespan for connection management.

```
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncAttrs
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uvicorn

# -------------------------------------------------------------------
# 1. Database Setup & SQLAlchemy Models
# -------------------------------------------------------------------
DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///app_data.db")

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class ItemModel(Base):
    """SQLAlchemy ORM Model representing the database table."""
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    stock: Mapped[int] = mapped_column(default=0)


# -------------------------------------------------------------------
# 2. Pydantic Schemas (Request/Response Validation)
# -------------------------------------------------------------------
class ItemCreate(BaseModel):
    """Schema for incoming POST payload validation."""
    sku: str = Field(..., example="SKU-101")
    title: str = Field(..., example="Ergonomic Mouse")
    price: float = Field(..., gt=0, example=49.99)
    stock: int = Field(default=0, ge=0, example=100)


class ItemUpdate(BaseModel):
    """Schema for partial PUT/PATCH updates."""
    title: str | None = Field(default=None, example="Updated Mouse Title")
    price: float | None = Field(default=None, gt=0, example=39.99)
    stock: int | None = Field(default=None, ge=0, example=80)


class ItemResponse(BaseModel):
    """Schema for serializing outgoing HTTP response JSON."""
    id: int
    sku: str
    title: str
    price: float
    stock: int

    # Allows Pydantic to read SQLAlchemy ORM instances directly
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------
# 3. FastAPI Lifespan Manager
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[LIFESPAN] Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[LIFESPAN] Tables created successfully.")

    yield  # Application handles incoming HTTP requests

    print("[LIFESPAN] Disposing database engine...")
    await engine.dispose()
    print("[LIFESPAN] Engine disposed successfully.")


app = FastAPI(title="Inventory Management API", lifespan=lifespan)


# -------------------------------------------------------------------
# 4. Dependency Injection for DB Sessions
# -------------------------------------------------------------------
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# -------------------------------------------------------------------
# 5. API Endpoints
# -------------------------------------------------------------------
@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    # Check if SKU already exists
    stmt = select(ItemModel).where(ItemModel.sku == payload.sku)
    existing = await db.scalar(stmt)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Item with this SKU already exists."
        )

    # Convert Pydantic model to SQLAlchemy ORM model
    db_item = ItemModel(**payload.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    return db_item


@app.get("/items", response_model=list[ItemResponse])
async def list_items(
    skip: int = 0, 
    limit: int = 20, 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(ItemModel).offset(skip).limit(limit)
    result = await db.scalars(stmt)
    return result.all()


@app.get("/items/{sku}", response_model=ItemResponse)
async def get_item(
    sku: str, 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(ItemModel).where(ItemModel.sku == sku)
    item = await db.scalar(stmt)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found."
        )
    return item


@app.patch("/items/{sku}", response_model=ItemResponse)
async def update_item(
    sku: str, 
    payload: ItemUpdate, 
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(ItemModel).where(ItemModel.sku == sku)
    item = await db.scalar(stmt)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found."
        )

    # Update fields that were explicitly set in the payload
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item)
    return item


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```


---
### Modern syntax

THere are the three major modern shifts that streamline nowadays:
- Annotated Dependencies (Clean Injection)
- Pydantic v2 computed_field & Direct ORM Integration
- Asynchronous Context Manager for Sessions (async_sessionmaker)

---
### Annotated Dependencies (Clean Injection)
    
Rather than writing db: AsyncSession = Depends(get_db_session) in every single endpoint function signature
- use typing.Annotated to create reusable dependency types:

```
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Define a custom type alias
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]

# Usage inside endpoint parameters:
@app.get("/items")
async def list_items(db: DatabaseSession):
    # db is fully typed and injected automatically
    pass
```

---
### Pydantic v2 computed_field & Direct ORM Integration

Pydantic v2 allows you to compute fields on the fly without needing ORM hooks or methods, keeping schemas lean:

```
from pydantic import BaseModel, ConfigDict, computed_field

class ItemResponse(BaseModel):
    id: int
    sku: str
    price: float
    stock: int

    # Modern Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def is_in_stock(self) -> bool:
        return self.stock > 0
```

---
### Asynchronous Context Manager for Sessions 

Instead of writing a manual get_db generator function with try/finally logic, async_sessionmaker can be used directly as an asynchronous context manager:

```
# Direct, modern generator function
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

---
### SQLModel 

SQLModel is a library created by Tiangolo (the creator of FastAPI). It bridges the gap between SQLAlchemy and Pydantic by allowing a single Python class to act as both a database model and a validation schema

---
### Why SQLModel?

In standard FastAPI + SQLAlchemy applications, you maintain two separate definitions for every entity:
- a SQLAlchemy Model (e.g., ItemModel) for database table mappings.
- multiple Pydantic Schemas (e.g., ItemCreate, ItemResponse) for HTTP request validation and JSON serialization

SQLModel eliminates this duplication by making every model inherit from a unified base class that combines Pydantic's data validation with SQLAlchemy's ORM capabilities

---
### Why SQLModel?

```
Traditional Approach:
[SQLAlchemy Model] <---> [Pydantic Schema]

SQLModel Approach:
      ┌─────────────────────────┐
      │        SQLModel         │
      │ (SQLAlchemy + Pydantic) │
      └─────────────────────────┘
```

---
### Key Concepts

- table=True: Instructs SQLModel to generate an underlying SQLAlchemy database table for that class.
- Field(primary_key=True): Marks fields as database columns with specific constraints (e.g., primary keys, indexes, foreign keys).
- Class Inheritance for DTOs: Inherit from a base class without table=True to create request/response Data Transfer Objects (DTOs) without redefining common fields.

---
### Python Driver Setup

Install sqlmodel, fastapi, uvicorn, and aiosqlite:
```
uv add sqlmodel fastapi uvicorn aiosqlite
```

---
### Core Operations (CRUD) 

Lets explore the steps:
1. Defining Unified Models
2. Adding Data (Create)
3. Listing Data (Read)


---
### Defining Unified Models

Create a base model for shared fields, then extend it for table creation and API responses.

```
from typing import Optional
from sqlmodel import SQLModel, Field

# Shared fields base class (Pydantic validation, no table)
class ItemBase(SQLModel):
    title: str = Field(index=True)
    price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)

# Database Table Model (table=True)
class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# API Request Payload Schema
class ItemCreate(ItemBase):
    pass
```

---
### Adding Data (Create)

Instantiate the SQLModel class directly from validated request data.

```
from sqlmodel.ext.asyncio.session import AsyncSession

async def create_item_demo(session: AsyncSession, payload: ItemCreate):
    # Instantiate the database table model directly from payload
    db_item = Item.model_validate(payload)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item
```

---
### Listing Data (Read)

Query models using SQLModel's select() syntax, which wraps SQLAlchemy's underlying engine.

```
from sqlmodel import select

async def read_items_demo(session: AsyncSession):
    statement = select(Item).where(Item.price > 10.0)
    results = await session.exec(statement)
    return results.all()
```

---
### Complete Real-Life FastAPI + SQLModel Application

This standalone application demonstrates an asynchronous FastAPI service using SQLModel for unified schema/database definitions, FastAPI Lifespan for engine management, and Annotated dependencies.

```
import os
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
import uvicorn

# -------------------------------------------------------------------
# 1. Database Setup & Engine Initialization
# -------------------------------------------------------------------
DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///sqlmodel_app.db")

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


# -------------------------------------------------------------------
# 2. Unified SQLModel Definitions
# -------------------------------------------------------------------
class ItemBase(SQLModel):
    """Shared attributes between request schemas and DB models."""
    sku: str = Field(index=True, unique=True, min_length=3, max_length=50)
    title: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)


class Item(ItemBase, table=True):
    """Actual Database Table Model."""
    id: Optional[int] = Field(default=None, primary_key=True)


class ItemCreate(ItemBase):
    """Payload for POST /items endpoints."""
    pass


class ItemUpdate(SQLModel):
    """Payload for PATCH /items endpoints (all fields optional)."""
    title: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None


# -------------------------------------------------------------------
# 3. Dependency Injection Setup
# -------------------------------------------------------------------
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


# -------------------------------------------------------------------
# 4. Lifespan Manager
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB Tables asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Unified FastAPI + SQLModel API", lifespan=lifespan)


# -------------------------------------------------------------------
# 5. API Endpoints
# -------------------------------------------------------------------
@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(payload: ItemCreate, db: DatabaseSession):
    # Check for existing SKU
    statement = select(Item).where(Item.sku == payload.sku)
    result = await db.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item with this SKU already exists."
        )

    # Convert Pydantic payload directly to SQLModel DB Instance
    db_item = Item.model_validate(payload)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@app.get("/items", response_model=list[Item])
async def list_items(db: DatabaseSession, skip: int = 0, limit: int = 20):
    statement = select(Item).offset(skip).limit(limit)
    results = await db.exec(statement)
    return results.all()


@app.get("/items/{sku}", response_model=Item)
async def get_item(sku: str, db: DatabaseSession):
    statement = select(Item).where(Item.sku == sku)
    result = await db.exec(statement)
    item = result.first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found."
        )
    return item


@app.patch("/items/{sku}", response_model=Item)
async def update_item(sku: str, payload: ItemUpdate, db: DatabaseSession):
    statement = select(Item).where(Item.sku == sku)
    result = await db.exec(statement)
    item = result.first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found."
        )

    # Update fields that were explicitly sent
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---
### SqlAlchemy cs SQLModel


While SQLModel offers an elegant developer experience by unifying Pydantic and SQLAlchemy, choosing between pure SQLAlchemy 2.0+ and SQLModel for production depends on your project's complexity, team structure, and maintenance requirements.

---
### SqlAlchemy cs SQLModel


Trade-Off Comparison
|Feature / Metric|Pure SQLAlchemy 2.0+|SQLModel|
|---|---|---|
|Data Definition|Two separate classes (SQLAlchemy Model + Pydantic Schema)|Single unified class hierarchy (table=True)|
|Pydantic v2 Alignment|Native support via ConfigDict(from_attributes=True)|Built on top of Pydantic, but can lag behind major Pydantic/SQLAlchemy core updates|
|Complex Relationships|Native, mature support for circular, self-referential, and multi-join relationships|Works well for simple Relationship(), but edge cases can require falling back to pure SQLAlchemy syntax|
|Alembic Migrations|Native industry standard; auto-generates clean migration scripts seamlessly|Uses Alembic under the hood, but complex type changes sometimes require custom handling|
|Ecosystem & Community|Decades of battle-tested documentation, production post-mortems, and StackOverflow answers|Smaller ecosystem; heavily relies on Tiangolo and community maintainers for updates|
|Type Safety & IDE Support|Excellent static typing via Mapped[...] and mapped_column(...)|Excellent autocompletion for basic CRUD; occasionally tricky typing with optional primary keys (id: Optional[int])|


---
### When to Choose Pure SQLAlchemy 2.0+Enterprise 

- Complex Domain Models: If your database schema involves multi-table inheritance, composite primary keys, complex many-to-many relationship cascades, or heavy query optimizations
- Strict Separation of Concerns: When your database schema needs to stay decoupled from your API layer (e.g., your database representation shouldn't change just because an external API contract changes)
- Large Teams & Legacy Codebases: Teams that already know standard SQLAlchemy and Alembic inside-out benefit from keeping the traditional, explicit boundaries

---
### When to Choose SQLModel
- Rapid Prototyping & MVPs: When building new microservices or greenfield projects where speed of development is the top priority.Standard REST APIs: 
- When your database models directly mirror your API endpoints with minimal custom transformation logic
- Small to Medium Codebases: Eliminating duplicate model files drastically reduces code volume and maintenance overhead.


---
### Architectural Decision Strategy

```
                                  ┌────────────────────────┐
                                  │ Is your DB schema or   │
                                  │ query logic complex?   │
                                  └───────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
                   [ YES ]                                         [ NO ]
                      │                                               │
                      ▼                                               ▼
         ┌────────────────────────┐                     ┌────────────────────────┐
         │ Use Pure SQLAlchemy 2  │                     │     Use SQLModel       │
         │  - Clean separation    │                     │  - Unified models      │
         │  - Full Alembic power  │                     │  - Fast development    │
         └────────────────────────┘                     └────────────────────────┘
```

---
### The N+1 query problem 

This problem is the most common performance trap when working with ORMs!

It occurs when code executes 1 query to fetch a list of parent records, followed by N additional queries to fetch related child records for each individual parent in a loop

Instead of retrieving all data in 1 or 2 optimized database round-trips, the application makes $1 + N$ separate network calls to the database

---
### Concepts

- Lazy Loading (Default Behavior): Related models are not fetched from the database until you explicitly access their attribute on a parent instance in Python
- Eager Loading: Tells the ORM in advance to load parent records and their related children in a single, batched operation.
- Joined Eager Loading (joinedload / JOIN): Uses a single SQL LEFT OUTER JOIN statement to pull both parents and children in a single query. Best for 1-to-1 or Many-to-1 relationships.
- Selectin Eager Loading (selectinload / IN (...)): Emits two queries—one for the parents, and a second SELECT ... WHERE id IN (...) query for the children. Best for 1-to-Many or Many-to-Many relationships.

---
### How the N+1 Query Problem Occurs

Consider a database with Department (parent) and Employee (child) tables. If you have 100 departments, lazy loading generates 101 SQL queries:

```
# 1. The initial query fetches 100 departments (1 query)
departments = await db.scalars(select(Department))

# 2. Iterating triggers lazy loading for EACH department's employees
for dept in departments.all():
    # ❌ Triggers 1 hidden SELECT query PER iteration (N queries)
    print(f"Department {dept.name} has {len(dept.employees)} employees")

# Total queries executed: 1 + 100 = 101 queries!
```

```
Database Round-Trips:
Query 1:   SELECT * FROM departments;
Query 2:   SELECT * FROM employees WHERE department_id = 1;
Query 3:   SELECT * FROM employees WHERE department_id = 2;
...
Query 101: SELECT * FROM employees WHERE department_id = 100;
```

---
### Solution Strategies 

- Eager Loading
    - SQLAlchemy provides two primary functions in sqlalchemy.orm to eliminate N+1 queries
        - selectinload 
        - joinedload
        
---
### selectinload 

Recommended for 1-to-Many & Many-to-Many

- emits two separate, optimized queries: one for parents, and one using an IN clause for all children

```
from sqlalchemy.orm import selectinload
from sqlalchemy import select

# Fetches departments and employees in exactly 2 queries
stmt = select(Department).options(selectinload(Department.employees))
departments = (await db.scalars(stmt)).all()

for dept in departments:
    # ✅ Employees are already loaded in memory - 0 additional queries!
    print(dept.name, len(dept.employees))
```

```
Database Round-Trips (Always 2 queries, regardless of N):
Query 1: SELECT * FROM departments;
Query 2: SELECT * FROM employees WHERE department_id IN (1, 2, 3, ..., 100);
```

---
### joinedload 

Recommended for Many-to-1 & 1-to-1
- combines tables into a single query using a SQL LEFT OUTER JOIN.

```
from sqlalchemy.orm import joinedload

# Fetches employee and their single department in 1 query
stmt = select(Employee).options(joinedload(Employee.department))
employees = (await db.scalars(stmt)).all()
```

```
Database Round-Trips (Always 1 query):
Query 1: SELECT employees.*, departments.* 
         FROM employees 
         LEFT OUTER JOIN departments ON departments.id = employees.department_id;
```

---
### How SQLModel Handles Relationships

In SQLModel, defining a relationship field using Relationship() defaults to **lazy** loading when accessed on an active session.

```
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Lazily loaded by default
    heroes: List["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    team: Optional[Team] = Relationship(back_populates="heroes")
```

---
### The N+1 Problem in SQLModel

If you retrieve a list of teams and then iterate over their heroes collection inside an active session, SQLModel executes an additional SQL query for every single team in the list:

```
from sqlmodel import select

# ❌ Query 1: Fetch all teams (100 teams returned)
statement = select(Team)
teams = (await session.exec(statement)).all()

for team in teams:
    # ❌ Queries 2 to 101: Lazy loading triggers a new SELECT for EACH team
    print(team.name, len(team.heroes))
```

---
### Async Caveat

Accessing a lazy-loaded relationship that wasn't eagerly loaded does not silently run N+1 queries.

Instead, it raises an error:Plaintextsqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; 

---
### Solving N+1 in SQLModel

SQLModel exposes SQLAlchemy's eager loading options via selectinload and joinedload through sqlalchemy.orm.1. 
- selectinload (Best for 1-to-Many / Many-to-Many)
    - loads parents first, then fetches all child relationships using an IN clause in a single batch query (2 total queries)
- joinedload (Best for Many-to-1 / 1-to-1)

---
### selectinload

```
from sqlalchemy.orm import selectinload
from sqlmodel import select

# ✅ Executes exactly 2 queries regardless of table size
statement = select(Team).options(selectinload(Team.heroes))
teams = (await session.exec(statement)).all()

for team in teams:
    # Read directly from memory
    print(team.name, len(team.heroes))
```

---
### joinedload 

```
from sqlalchemy.orm import joinedload
from sqlmodel import select

# ✅ Executes exactly 1 query with a JOIN
statement = select(Hero).options(joinedload(Hero.team))
heroes = (await session.exec(statement)).all()

for hero in heroes:
    if hero.team:
        print(hero.name, hero.team.name)
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. SqlModel

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
SqlModel