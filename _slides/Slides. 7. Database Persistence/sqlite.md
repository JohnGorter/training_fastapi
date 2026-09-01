# Sqlite 

---
### Sqlite 

Python’s built-in sqlite3 module provides a lightweight, zero-configuration SQL database engine embedded directly into application process memory or local file systems

---
### Basic Connection, Table Creation, & Statements (execute, commit)

Connecting to SQLite opens a file path (or :memory: for ephemeral storage) and instantiates a Cursor object to issue SQL commands

Real-World Use Case
- local desktop tools, single-user CLI utilities, or persistent embedded system configurations

Behavior
- data-modifying statements (INSERT, UPDATE, DELETE) require an explicit .commit() call on the connection object to persist changes

```
import sqlite3

# 1. Connect to file database (creates file if missing)
conn = sqlite3.connect("app_data.db")
cursor = conn.cursor()

# 2. Execute DDL Schema Creation
cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# 3. Execute DML Insert & Commit Transaction
cursor.execute(
    "INSERT INTO system_logs (service_name, message) VALUES ('auth_service', 'User logged in')"
)
conn.commit()
conn.close()
```

---
### Parameterized Queries & SQL Injection Defense

SQLite uses ? (positional) or :key (named) placeholders to separate SQL logic from raw data parameters

Real-World Use Case
- safely querying or inserting user-supplied search filters, authentication forms, or external API payloads

Behavior
- SQLite prepares the SQL query structure first and safely binds values as untrusted literals

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
### Row Factories for Dictionary Access (sqlite3.Row)

By default, SQLite returns query results as plain Python tuples ((1, 'auth_service', 'User logged in')), requiring index-based lookup 

Setting conn.row_factory = sqlite3.Row transforms query outputs into dictionary-like objects accessible by column names

Real-World Use Case
- mapping SQL query outputs directly to JSON endpoints or Pydantic models without manual index mapping

Behavior
- provides both index-based (row[0]) and key-based (row["service_name"]) access with minimal memory overhead

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
### Extending SQLite with Custom Python Functions (create_function)

SQLite allows registering custom Python functions into the SQL engine using conn.create_function() 
- registered functions can then be invoked directly inside SQL queries

Real-World Use Case
- applying complex string transformations, regular expressions, or custom encryption/hashing directly inside SELECT or WHERE statements

Behavior
- executes the registered Python function synchronously for each evaluated row in the query pipeline

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
