# SQLAlchemy

---
### SQLAlchemy

SQLAlchemy unifies Core and ORM components into a type-safe API


---
### Declarative Mapping 

SQLAlchemy 2.0 uses type annotations and mapped_column(). This provides static type checking in IDEs and enforces database column constraints directly inside class definitions

Real-World Use Case
- defining typed relational database models (e.g., users, orders) with automatic IDE auto-completion and type checking

Behavior
- mapped[int] implicitly marks the column as non-nullable unless wrapped in Mapped[int | None]

```
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(String(500))  # Nullable column
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )
```

---
### Modern Querying Syntax 

SQLAlchemy Queries are constructed using explicit select(Model) and executed via session.execute() - calling .scalars() extracts the ORM model instances from the result tuples

Real-World Use Case
- fetching filtered, sorted, or paginated database records 

Behavior
- session.execute(select(...)) returns Result row tuples. 
- .scalars() extracts single ORM entities
- .scalar_one_or_none() safely returns one record or None

```
from sqlalchemy import select
from sqlalchemy.orm import Session

def get_active_user(session: Session, username: str) -> User | None:
    # 1. Construct explicit SELECT statement
    stmt = select(User).where(User.username == username)
    
    # 2. Execute statement and extract scalar ORM object
    result = session.execute(stmt)
    user = result.scalars().scalar_one_or_none()
    return user
```

---
### Relationship Mapping & Eager Loading

Relationships use Mapped[list["Child"]] and relationship() 

*To avoid the N+1 query performance bug, queries must explicitly specify loading strategies like selectinload (for 1-to-Many) or joinedload (for Many-to-1)*

Real-World Use Case
- fetching a user and all their associated blog posts in optimized database round-trips.

Behavior
- in async SQLAlchemy, accessing un-loaded relationship attributes triggers an MissingGreenlet error. Eager loading strategies prevent this by fetching related entities upfront

```
from sqlalchemy import select, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped[User] = relationship(back_populates="posts")

# Eager Loading Execution (Prevents N+1 Queries)
def get_user_with_posts(session, user_id: int):
    stmt = select(User).options(selectinload(User.posts)).where(User.id == user_id)
    return session.execute(stmt).scalars().scalar_one_or_none()
```

---
### Async Engine & Session Execution 

SQLAlchemy 2.0 natively supports async database drivers via create_async_engine and async_sessionmaker:
- asyncpg for PostgreSQL 
- aiosqlite for SQLite

Real-World Use Case
- running non-blocking database queries inside FastAPI request handlers to maintain high concurrency

Behavior
- database operations (execute(), commit(), refresh()) must be explicitly awaited

```
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Async Engine Initialization
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def fetch_all_users() -> list[User]:
    async with async_session_factory() as session:
        stmt = select(User).order_by(User.id.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
```

---
### High-Performance Bulk Operations

SQLAlchemy allows executing bulk update() and delete() statements directly on the database without loading entities into Python memory first

Real-World Use Case
- deactivating expired user accounts or updating pricing across thousands of inventory items at once

Behavior
- bypasses individual ORM instance loading, executing a single SQL UPDATE or DELETE query directly on the database engine

```
from sqlalchemy import update, delete

async def deactivate_inactive_users(session: AsyncSession, days_inactive: int):
    # Executes direct SQL: UPDATE users SET is_active = False WHERE ...
    stmt = (
        update(User)
        .where(User.bio == None)
        .values(bio="No bio provided.")
    )
    await session.execute(stmt)
    await session.commit()
```

---
### Unified Enterprise SQLAlchemy 

This production pattern demonstrates an asynchronous content publishing engine built with SQLAlchemy 2.0, featuring type-annotated models, 1-to-Many relationships, eager loading, transactional units of work, and bulk mutations.

```
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy import String, Text, ForeignKey, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload

# ---------------------------------------------------------------------
# 1. BASE & MODEL DEFINITIONS
# ---------------------------------------------------------------------
class Base(DeclarativeBase):
    pass

class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    
    # 1-to-Many Relationship
    articles: Mapped[list["Article"]] = relationship(
        back_populates="author", 
        cascade="all, delete-orphan",
        lazy="raise"  # Enforces explicit eager loading
    )

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    published_at: Mapped[datetime | None] = mapped_column(default=None)
    
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), index=True)
    author: Mapped[Author] = relationship(back_populates="articles")

# ---------------------------------------------------------------------
# 2. ASYNC DATABASE ENGINE SETUP
# ---------------------------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---------------------------------------------------------------------
# 3. REPOSITORY & TRANSACTIONAL SERVICES
# ---------------------------------------------------------------------
class ContentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_author_with_articles(
        self, name: str, email: str, articles_data: list[dict[str, str]]
    ) -> Author:
        """Creates an author and nested articles in a single atomic transaction."""
        author = Author(
            name=name,
            email=email,
            articles=[Article(title=a["title"], content=a["content"]) for a in articles_data]
        )
        self.session.add(author)
        await self.session.flush()  # Flushes to get DB-generated IDs
        return author

    async def get_author_feed(self, author_id: int) -> Author | None:
        """Queries author with eager-loaded articles to prevent N+1 queries."""
        stmt = (
            select(Author)
            .options(selectinload(Author.articles))
            .where(Author.id == author_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().scalar_one_or_none()

    async def bulk_publish_drafts(self, author_id: int) -> int:
        """Executes direct bulk UPDATE statement without loading ORM models into memory."""
        now_utc = datetime.now(timezone.utc)
        stmt = (
            update(Article)
            .where(Article.author_id == author_id, Article.status == "DRAFT")
            .values(status="PUBLISHED", published_at=now_utc)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

# ---------------------------------------------------------------------
# 4. EXECUTION PIPELINE
# ---------------------------------------------------------------------
async def main():
    await init_db()

    async with AsyncSessionFactory() as session:
        async with session.begin():  # Manages transaction commit/rollback block automatically
            repo = ContentRepository(session)
            
            # Step A: Atomic Insert of Parent + Children
            author = await repo.create_author_with_articles(
                name="Jane Doe",
                email="jane@example.com",
                articles_data=[
                    {"title": "SQLAlchemy 2.0 Overview", "content": "Modern ORM practices..."},
                    {"title": "Async Python Guide", "content": "Concurrency patterns..."}
                ]
            )
            print(f"Created Author ID: {author.id}")

    # Step B: Eager Querying Execution
    async with AsyncSessionFactory() as session:
        repo = ContentRepository(session)
        fetched_author = await repo.get_author_feed(author_id=1)
        
        if fetched_author:
            print(f"\nAuthor: {fetched_author.name}")
            for article in fetched_author.articles:
                print(f" - Article: '{article.title}' | Status: {article.status}")

    # Step C: Bulk Status Update Execution
    async with AsyncSessionFactory() as session:
        async with session.begin():
            repo = ContentRepository(session)
            updated_count = await repo.bulk_publish_drafts(author_id=1)
            print(f"\nBulk Published {updated_count} articles.")

    # Step D: Verify Update State
    async with AsyncSessionFactory() as session:
        repo = ContentRepository(session)
        updated_author = await repo.get_author_feed(author_id=1)
        if updated_author:
            print("\nUpdated Article Feed:")
            for article in updated_author.articles:
                print(f" - '{article.title}' | Status: {article.status} | Published: {article.published_at}")

if __name__ == "__main__":
    asyncio.run(main())
```

---
### Execution Pipeline Explanation

- Schema Generation: init_db() runs Base.metadata.create_all asynchronously, instantiating the authors and articles tables in memory.

- Parent-Child Atomic Insertion: create_author_with_articles() instantiates an Author with a list of Article child models. Calling session.flush() assigns primary keys across both tables within an active transaction block (async with session.begin()).

- Eager Loading Resolution: get_author_feed() executes select(Author).options(selectinload(Author.articles)). SQLAlchemy executes a two-stage query (SELECT * FROM authors WHERE id = 1 followed by SELECT * FROM articles WHERE author_id IN (1)), loading the articles relationship list safely without relying on synchronous lazy loading.

- Bulk Mutation: bulk_publish_drafts() constructs an update(Article) statement. It issues a direct SQL update to set status = "PUBLISHED" for all matching rows in SQLite without pulling the records into Python memory.

