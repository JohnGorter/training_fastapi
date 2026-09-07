# SQLite

---
### SQLite

SQlite a self-contained, serverless, zero-configuration, transactional SQL database engine 
- built directly into Python via the standard sqlite3 module

Unlike MongoDB, SQLite stores the entire database—tables, indexes, triggers, and data—as a single cross-platform file 
- on disk 
- or in RAM as an in-memory database

---
### Key SQLite Concepts

- Database File: A single file on disk (e.g., app.db) or ":memory:" for ephemeral, ultra-fast temporary storage
- Connection (sqlite3.connect): Manages the communication session between Python and the database file
- Cursor (connection.cursor): An object used to execute SQL statements and fetch query results
- Dynamic Typing: SQLite uses manifest typing where column types (INTEGER, TEXT, REAL, BLOB, NULL) act as guidelines rather than strict constraints.

--- 
### Use Cases

- Local Application Storage: Desktop applications, mobile apps, and command-line tools
- Embedded & IoT Devices: Edge computing where running a database server process adds too much overhead
- Testing & Prototyping: In-memory databases (:memory:) allow unit test suites to run in milliseconds without cleaning up physical files
- Medium-Traffic Web Backends: Reading/writing local files when concurrency demands do not justify managing hosted database clusters

---
### Core Operations (CRUD) Explained
1. Connecting and Initializing
2. Creating Tables & Adding Data (Create)
3. Listing Data (Read)
4. Changing Data (Update)
5. Deleting Data (Delete)
6. Closing Connection


---
### Connecting and Initializing

Opening a connection creates the database file automatically if it does not already exist.

```
import sqlite3

# Connect to a disk file (or use ":memory:" for RAM-only)
conn = sqlite3.connect("store.db")
cursor = conn.cursor()

# Enable Foreign Key enforcement (disabled by default in SQLite)
cursor.execute("PRAGMA foreign_keys = ON;")
```

---
### Creating Tables & Adding Data (Create)

Execute DDL statements to define tables, then use parameterized queries (?) to prevent SQL injection vulnerabilities.

```
# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
    )
""")

# Insert single row using parameterized values (?)
cursor.execute(
    "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
    ("Wireless Mouse", 29.99, 150)
)
conn.commit()  # Write changes to disk

# Insert multiple rows
bulk_items = [
    ("Mechanical Keyboard", 89.99, 45),
    ("USB-C Hub", 19.99, 200)
]
cursor.executemany(
    "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
    bulk_items
)
conn.commit()
```

---
### Listing Data (Read)

Retrieve records using fetchone(), fetchall(), or by iterating directly over the cursor.

```
# Fetch single record
cursor.execute("SELECT * FROM products WHERE name = ?", ("Wireless Mouse",))
mouse = cursor.fetchone()

# Fetch all matching records
cursor.execute("SELECT name, price FROM products WHERE price > ?", (20.0,))
items = cursor.fetchall()
for name, price in items:
    print(name, price)
```

---
#### Changing Data (Update)

Modify existing rows using standard UPDATE statements inside a transaction block.

```
# Reduce stock by 1
cursor.execute(
    "UPDATE products SET stock = stock - 1 WHERE name = ?",
    ("Wireless Mouse",)
)

# Apply discount flag/price update
cursor.execute(
    "UPDATE products SET price = price * 0.9 WHERE price > ?",
    (50.0,)
)
conn.commit()
```

---
### Deleting Data (Delete)

Remove rows matching specific constraints.

```
# Delete single record
cursor.execute("DELETE FROM products WHERE name = ?", ("USB-C Hub",))

# Clear out-of-stock items
cursor.execute("DELETE FROM products WHERE stock = 0")
conn.commit()
```

---
### Closing Connection

Always close cursors and connection objects to release file locks

```
cursor.close()
conn.close()
```

---
### All-Encompassing Synchronous Example

This script runs through the full lifecycle of managing a warehouse inventory system using sqlite3, row factories for dictionary-like record access, parameterized security, transactions, and cleanup.

```
import sqlite3


def run_inventory_demo():
    # Step 1: Connect to SQLite File (or in-memory database)
    print("[1] Connecting to SQLite database...")
    conn = sqlite3.connect("warehouse.db")
    
    # Configure rows to behave like Python dictionaries instead of tuples
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Enable Foreign Keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Step 2: Initialize Schema
        print("\n[2] Setting up database schema...")
        cursor.execute("DROP TABLE IF EXISTS devices;")
        cursor.execute("""
            CREATE TABLE devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            );
        """)

        # Step 3: Add Records (Create)
        print("\n[3] Seeding inventory dataset...")
        inventory = [
            ("DEV-01", "Laptop Pro 15", "Computers", 1299.00, 12),
            ("DEV-02", "Monitor 27-inch", "Displays", 349.50, 25),
            ("DEV-03", "Ergonomic Chair", "Furniture", 450.00, 5),
            ("DEV-04", "4K Web Camera", "Peripherals", 89.99, 0)
        ]
        
        cursor.executemany("""
            INSERT INTO devices (sku, name, category, price, stock)
            VALUES (?, ?, ?, ?, ?)
        """, inventory)
        conn.commit()
        print(f"    Inserted {cursor.rowcount} seed records.")

        # Step 4: List Records (Read)
        print("\n[4] Querying in-stock items priced over $100:")
        cursor.execute("""
            SELECT sku, name, price, stock 
            FROM devices 
            WHERE stock > 0 AND price > ?
        """, (100.0,))
        
        for item in cursor.fetchall():
            print(f"    - [{item['sku']}] {item['name']}: ${item['price']} (In stock: {item['stock']})")

        # Step 5: Change Records (Update)
        print("\n[5] Updating stock levels and pricing...")
        # Restock camera
        cursor.execute("""
            UPDATE devices 
            SET stock = 15 
            WHERE sku = ?
        """, ("DEV-04",))

        # Bulk price adjustment on displays
        cursor.execute("""
            UPDATE devices 
            SET price = price + 20.00 
            WHERE category = ?
        """, ("Displays",))
        conn.commit()

        # Step 6: Delete Records (Delete)
        print("\n[6] Removing furniture items...")
        cursor.execute("DELETE FROM devices WHERE category = ?", ("Furniture",))
        conn.commit()
        print(f"    Deleted count: {cursor.rowcount}")

        # Verify final state
        print("\n[7] Final inventory state:")
        cursor.execute("SELECT sku, name, price, stock FROM devices")
        for row in cursor.fetchall():
            print(f"    [{row['sku']}] {row['name']} | ${row['price']} | Stock: {row['stock']}")

    except sqlite3.Error as err:
        print(f"SQLite Error: {err}")
        conn.rollback()  # Rollback on transaction failure
    finally:
        # Step 8: Close Connection
        cursor.close()
        conn.close()
        print("\n[8] Database connection closed successfully.")


if __name__ == "__main__":
    run_inventory_demo()
```

---
###  Asynchronous SQLite with aiosqlite

Because Python's standard sqlite3 module is blocking, web frameworks like FastAPI or async IO applications use aiosqlite to execute queries in an underlying thread pool while keeping the main asyncio event loop non-blocking.

---
### Install aiosqlite

Install first 
```
uv add aiosqlite
```

---
### Core Async Operations Explained

```
import asyncio
import aiosqlite

async def async_sqlite_demo():
    # Connect asynchronously
    async with aiosqlite.connect("async_store.db") as db:
        # Enable row factory for dictionary access
        db.row_factory = aiosqlite.Row
        
        # Create Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price REAL
            )
        """)
        
        # Insert Data
        await db.execute("INSERT INTO items (title, price) VALUES (?, ?)", ("Tablet", 299.99))
        await db.commit()
        
        # Query Data with async cursor
        async with db.execute("SELECT * FROM items WHERE price > ?", (100.0,)) as cursor:
            async for row in cursor:
                print(row["title"], row["price"])

asyncio.run(async_sqlite_demo())
```

---
### Real-Life FastAPI Integration with lifespan and aiosqlite

In FastAPI, opening an SQLite database context inside a lifespan event ensures 
- connection setup, 
- PRAGMA configuration, 
- schema migrations run once at server startup 
- close gracefully upon shutdown

---
### Example

```
import os
from contextlib import asynccontextmanager
import aiosqlite
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
import uvicorn

DB_FILE = "app_data.db"

# 1. Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[LIFESPAN] Connecting to SQLite database...")
    db = await aiosqlite.connect(DB_FILE)
    db.row_factory = aiosqlite.Row
    
    # Store reference on app.state
    app.state.db = db
    
    # Enable WAL mode for high concurrency & build table
    await db.execute("PRAGMA journal_mode = WAL;")
    await db.execute("PRAGMA foreign_keys = ON;")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        );
    """)
    await db.commit()
    print("[LIFESPAN] Database initialized with WAL mode.")

    yield  # Application handles requests

    print("[LIFESPAN] Closing database connection...")
    await app.state.db.close()
    print("[LIFESPAN] Database connection closed.")


# 2. Instantiate App
app = FastAPI(title="Async SQLite Task Manager", lifespan=lifespan)


# 3. Schemas
class TaskCreate(BaseModel):
    title: str

class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool


# 4. Endpoints
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, request: Request):
    db: aiosqlite.Connection = request.app.state.db
    
    cursor = await db.execute(
        "INSERT INTO tasks (title) VALUES (?)",
        (task.title,)
    )
    await db.commit()
    
    return {
        "id": cursor.lastrowid,
        "title": task.title,
        "completed": False
    }

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, request: Request):
    db: aiosqlite.Connection = request.app.state.db
    
    async with db.execute("SELECT id, title, completed FROM tasks WHERE id = ?", (task_id,)) as cursor:
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"])
        }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. SQLite

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
SQLite


---
### More SQLite

Lets explore:
- Parameterized Queries & SQL Injection Defense
- Row Factories for Dictionary Access (sqlite3.Row)
- Atomic Transaction Management 
- Extending SQLite with Custom Python Functions (create_function)

---
### Parameterized Queries & SQL Injection Defense

SQLite uses ? (positional) or :key (named) placeholders to separate SQL logic from raw data parameters

Real-World Use Case
- safely querying or inserting user-supplied search filters, authentication forms, or external API payloads

Behavior
- SQLite prepares the SQL query structure first and safely binds values as untrusted literals

---
### Parameterized Queries & SQL Injection Defense

```
import sqlite3

conn = sqlite3.connect("app_data.db")
cursor = conn.cursor()

# Untrusted user input
user_search = "admin' OR '1'='1"  # Malicious injection attempt

# INCORRECT (Vulnerable to SQL Injection)
# cursor.execute(f"SELECT * FROM users WHERE username = '{user_search}'")

# CORRECT: Positional Placeholders (?)
cursor.execute("SELECT * FROM system_logs WHERE service_name = ?", (user_search,))
results = cursor.fetchall()

# CORRECT: Named Placeholders (:name)
payload = {"service": "auth_service", "keyword": "%logged%"}
cursor.execute(
    "SELECT * FROM system_logs WHERE service_name = :service AND message LIKE :keyword", 
    payload
)
records = cursor.fetchall()
conn.close()
```

---
### Row Factories for Dictionary Access 

By default, SQLite returns query results as plain Python tuples ((1, 'auth_service', 'User logged in')), requiring index-based lookup 

Setting conn.row_factory = sqlite3.Row transforms query outputs into dictionary-like objects accessible by column names

Real-World Use Case
- mapping SQL query outputs directly to JSON endpoints or Pydantic models without manual index mapping

Behavior
- provides both index-based (row[0]) and key-based (row["service_name"]) access with minimal memory overhead

---
### Row Factories for Dictionary Access

```
import sqlite3

conn = sqlite3.connect("app_data.db")
# Enable dict-like column access
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("SELECT id, service_name, message FROM system_logs LIMIT 1")
row = cursor.fetchone()

if row:
    print(f"ID: {row['id']}")  # Access by column name
    print(f"Service: {row['service_name']}")
    
    # Convert sqlite3.Row directly to standard Python dictionary
    row_dict = dict(row)
    print("As Dictionary:", row_dict)

conn.close()
```

---
### Atomic Transaction Management 

Python's sqlite3.Connection acts as a context manager for handling transactions 

Using with conn: guarantees that a series of SQL statements execute atomically:
- if any statement raises an exception, all changes within the block are automatically rolled back

Real-World Use Case
- executing multi-table financial transfers or inventory deductions where partial updates must never occur

Behavior
- automatically calls conn.commit() on clean exit or conn.rollback() on unhandled exceptions

---
### Atomic Transaction Management 

```
import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

# Setup test accounts
cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, balance REAL)")
cursor.execute("INSERT OR REPLACE INTO accounts VALUES ('acc_1', 500.0), ('acc_2', 100.0)")
conn.commit()

# Transaction Context Manager
try:
    with conn:  # Begins transaction
        # Deduct from Account 1
        cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE id = ?", ("acc_1",))
        
        # Simulate business failure
        raise ValueError("Network error during transfer")
        
        # Credit Account 2 (Never reached)
        cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE id = ?", ("acc_2",))
except ValueError as e:
    print(f"Transaction aborted: {e}. Changes safely rolled back!")

# Verify balances remain unchanged
cursor.execute("SELECT * FROM accounts")
print("Post-rollback state:", cursor.fetchall())  # acc_1 is still 500.0
conn.close()
```

---
### Extending SQLite with Custom Python Functions

SQLite allows registering custom Python functions into the SQL engine using conn.create_function() 
- registered functions can then be invoked directly inside SQL queries

Real-World Use Case
- applying complex string transformations, regular expressions, or custom encryption/hashing directly inside SELECT or WHERE statements

Behavior
- executes the registered Python function synchronously for each evaluated row in the query pipeline

---
### Extending SQLite with Custom Python Functions

```
import hashlib
import re
import sqlite3

def hash_email(email: str) -> str:
    """Custom Python function to generate SHA-256 hashes."""
    return hashlib.sha256(email.lower().strip().encode('utf-8')).hexdigest()

def regex_match(pattern: str, text: str) -> bool:
    """Custom regex evaluation function."""
    return bool(re.search(pattern, text)) if text else False

conn = sqlite3.connect(":memory:")
# Register functions: name, num_params, callable
conn.create_function("sha256_email", 1, hash_email)
conn.create_function("REGEXP", 2, regex_match)

cursor = conn.cursor()
cursor.execute("CREATE TABLE users (email TEXT)")
cursor.execute("INSERT INTO users VALUES ('alice@example.com'), ('bob@domain.org')")

# Query using custom SHA-256 function in SQL SELECT
cursor.execute("SELECT email, sha256_email(email) FROM users")
for row in cursor.fetchall():
    print(f"Email: {row[0]} -> Hash: {row[1]}")

# Query using custom REGEXP function in SQL WHERE
cursor.execute("SELECT email FROM users WHERE REGEXP('\\.org$', email)")
print("Matched .org emails:", cursor.fetchall())
conn.close()
```

---
### Unified Enterprise SQLite Database Engine

This production pattern demonstrates a WAL-enabled (Write-Ahead Logging) SQLite database manager featuring connection configuration, custom function registration, parameterized CRUD operations, dict-like mapping, error handling, and atomic multi-statement transaction management

```
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
import sqlite3
from typing import Any, Generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseEngine")

# Custom Python function for SQLite registration
def generate_audit_hash(user_id: str, action: str, timestamp: str) -> str:
    payload = f"{user_id}:{action}:{timestamp}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class SQLiteEngine:
    """Robust SQLite Database Engine with WAL mode & transactional safety."""
    
    def __init__(self, db_path: Path | str = "production_audit.db"):
        self.db_path = str(db_path)
        self._initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """Configures connection options and row factory."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        
        # 1. Performance Optimization: WAL Mode (Concurrency enhancement)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # 2. Register Custom Extensions
        conn.create_function("audit_hash", 3, generate_audit_hash)
        return conn

    def _initialize_database(self) -> None:
        """Executes initial schema creation."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    integrity_hash TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS user_metrics (
                    user_id TEXT PRIMARY KEY,
                    total_actions INTEGER DEFAULT 0,
                    last_active TEXT NOT NULL
                );
            """)
        logger.info("Database schema initialized with WAL mode enabled.")

    def record_user_action(self, user_id: str, action: str) -> dict[str, Any]:
        """Atomically records an audit entry and updates aggregate user metrics."""
        now_utc = datetime.now(timezone.utc).isoformat()
        
        conn = self.get_connection()
        try:
            with conn:  # Transaction boundary (Commit on success, Rollback on error)
                cursor = conn.cursor()
                
                # Step A: Insert audit log entry using custom SQL function
                cursor.execute("""
                    INSERT INTO audit_logs (user_id, action, timestamp, integrity_hash)
                    VALUES (?, ?, ?, audit_hash(?, ?, ?))
                """, (user_id, action, now_utc, user_id, action, now_utc))
                
                log_id = cursor.lastrowid
                
                # Step B: Upsert user metrics aggregate
                cursor.execute("""
                    INSERT INTO user_metrics (user_id, total_actions, last_active)
                    VALUES (?, 1, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        total_actions = total_actions + 1,
                        last_active = excluded.last_active
                """, (user_id, now_utc))
                
                # Step C: Retrieve created record
                cursor.execute("SELECT * FROM audit_logs WHERE id = ?", (log_id,))
                record = cursor.fetchone()
                
                return dict(record) if record else {}
                
        except sqlite3.Error as e:
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            conn.close()

    def fetch_user_audit_history(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Queries parameterized records mapped to plain Python dictionaries."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, action, timestamp, integrity_hash
                FROM audit_logs
                WHERE user_id = :uid
                ORDER BY id DESC
                LIMIT :limit
            """, {"uid": user_id, "limit": limit})
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

# =====================================================================
# VERIFICATION & EXECUTION PIPELINE
# =====================================================================
if __name__ == "__main__":
    db = SQLiteEngine("enterprise_app.db")
    
    # 1. Execute atomic transactions
    record_1 = db.record_user_action(user_id="usr_1002", action="FILE_UPLOAD")
    record_2 = db.record_user_action(user_id="usr_1002", action="EXPORT_DATA")
    
    print("New Log Record:", record_1)
    
    # 2. Query history with dictionary formatting
    history = db.fetch_user_audit_history(user_id="usr_1002")
    print("\nAudit History:")
    for entry in history:
        print(f"[{entry['timestamp']}] Action: {entry['action']} | Hash: {entry['integrity_hash'][:16]}...")
```

---
### Execution Pipeline Explanation

- WAL Mode & Pragmas (PRAGMA journal_mode = WAL): Enables Write-Ahead Logging, allowing concurrent reader processes to read the database without being blocked by active writer processes
- Custom SQL Function Binding (conn.create_function): Registers generate_audit_hash under the name audit_hash. During INSERT INTO audit_logs, SQLite invokes this Python hashing function inline to generate cryptographically verified integrity hashes directly within the SQL pipeline.
- Atomic Transaction Unit (with conn:): Both INSERT INTO audit_logs and ON CONFLICT DO UPDATE on user_metrics run inside a single transaction block. If an error occurs on either table, the transaction aborts and rolls back completely.
-Dictionary Data Mapping (sqlite3.Row): Setting conn.row_factory = sqlite3.Row converts SQL output streams into structured objects that map cleanly into standard Python dict instances via dict(row).

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. SQLite Custom Functions

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
SQLite Custom Functions