# Context managers 

---
### Context managers

Context managers manage resource allocation and cleanup around code blocks using Python’s with and async with statements

- they guarantee that setup tasks execute before block execution and teardown tasks execute upon exit—even if runtime exceptions occur

---
### Class-Based Synchronous Context Managers 

Class-based context managers implement the __enter__ and __exit__ protocol methods.
- __enter__ returns an object assigned to the as variable
- __exit__ handles cleanup and exception suppression

Real-World Use Case
- measuring execution time for CPU-bound routines or acquiring file-system locks

Behavior
- if an exception occurs inside the with block, Python passes its type, value, and traceback to __exit__
- returning True from __exit__ suppresses the exception
- returning False re-raises it

---
### Class-Based Synchronous Context Managers 

```
import time

class ExecutionTimer:
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self  # Value assigned to the 'as' target variable

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start_time
        print(f"Block execution completed in {self.elapsed:.4f} seconds.")
        return False  # Do not suppress exceptions

# Usage:
with ExecutionTimer() as timer:
    time.sleep(0.1)
    print("Work completed inside block.")
```

---
### Generator-Based Synchronous Context Managers 

The @contextlib.contextmanager decorator converts a Python generator function into a context manager

- code before the yield statement acts as __enter__
- code inside a finally block post-yield acts as __exit__

Real-World Use Case
- temporarily mutating environment variables, switching active working directories, or opening local file streams

Behavior
- the value passed to yield is assigned to the as variable
- exceptions raised inside the with block are re-thrown at the yield statement site inside the generator

---
### Generator-Based Synchronous Context Managers 
```
import os
from contextlib import contextmanager

@contextmanager
def temporary_env_var(key: str, value: str):
    old_value = os.environ.get(key)
    os.environ[key] = value  # Setup
    try:
        yield value  # Yield control to the 'with' block
    finally:
        # Cleanup guarantees restoration
        if old_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old_value

# Usage:
with temporary_env_var("APP_ENV", "testing") as env:
    print(f"Current APP_ENV: {os.environ['APP_ENV']}")  # Outputs: testing

print(f"Restored APP_ENV: {os.environ.get('APP_ENV')}")  # Restores original state
```


---
### Class-Based Asynchronous Context Managers 

Asynchronous context managers use async with and implement __aenter__ and __aexit__

- both lifecycle methods are async def coroutines capable of awaiting asynchronous operations during setup and teardown

Real-World Use Case
- acquiring distributed locks in Redis or opening non-blocking socket connections

Behavior
- both await lock.__aenter__() and await lock.__aexit__() run on Python's async event loop without blocking concurrent tasks

---
### Class-Based Asynchronous Context Managers 

```
import asyncio

class AsyncDistributedLock:
    def __init__(self, resource_name: str):
        self.resource_name = resource_name

    async def __aenter__(self):
        print(f"Awaiting lock acquisition for resource '{self.resource_name}'...")
        await asyncio.sleep(0.05)  # Simulate async network call to lock manager
        print(f"Lock acquired for '{self.resource_name}'.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"Releasing lock for resource '{self.resource_name}'...")
        await asyncio.sleep(0.02)  # Simulate async network release
        print(f"Lock released for '{self.resource_name}'.")
        return False

# Usage:
async def main():
    async with AsyncDistributedLock("payment_gateway_user_101"):
        print("Executing critical payment processing operations...")

asyncio.run(main())
```

---
### Generator-Based Asynchronous Context Managers 

The @contextlib.asynccontextmanager decorator wraps an async def generator coroutine. 

- this creates lightweight asynchronous resource scopes without needing to write full class boilerplate

Real-World Use Case
- managing asynchronous database transaction scopes (BEGIN, COMMIT, ROLLBACK) or non-blocking HTTP connection pools

Behavior
- pauses execution at yield when entering the async with block and resumes execution in the finally block upon exit


---
### Generator-Based Asynchronous Context Managers 
```
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_transaction_scope(db_connection):
    print("[TX] Beginning async transaction...")
    await asyncio.sleep(0.01)
    try:
        yield db_connection
        print("[TX] Committing async transaction...")
        await asyncio.sleep(0.01)
    except Exception:
        print("[TX] Rolling back async transaction...")
        await asyncio.sleep(0.01)
        raise

# Usage
async def run_db_task():
    async with async_transaction_scope("fake_db_conn") as conn:
        print("Writing records to database...")

asyncio.run(run_db_task())
```

---
#### Unified Python Data Processing Pipeline

This script demonstrates a batch data processor using pure Python standard library modules. It combines synchronous profiling and safe file cleanup with asynchronous locking and transactional work.

```
import asyncio
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path
import time

# 1. Sync Profiling Class
class OperationProfiler:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start
        print(f"[METRIC] {self.name} executed in {elapsed:.4f}s")
        return False

# 2. Sync Generator File Cleanup
@contextmanager
def temporary_scratchpad(filename: str):
    filepath = Path(f"./tmp_{filename}")
    try:
        yield filepath
    finally:
        if filepath.exists():
            filepath.unlink()
            print(f"[CLEANUP] Removed temporary file: {filepath}")

# 3. Async Class Mutex
class AsyncMutex:
    def __init__(self, key: str):
        self.key = key

    async def __aenter__(self):
        print(f"[MUTEX] Locking key: {self.key}")
        await asyncio.sleep(0.02)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"[MUTEX] Unlocking key: {self.key}")
        await asyncio.sleep(0.01)
        return False

# 4. Async Generator Connection Pool Scope
@asynccontextmanager
async def get_async_connection():
    print("[CONN] Opening async database connection...")
    await asyncio.sleep(0.03)
    conn = {"session_id": "sess_8832", "status": "active"}
    try:
        yield conn
    finally:
        print("[CONN] Closing async database connection...")
        await asyncio.sleep(0.01)

# 5. Pipeline Orchestrator
async def process_data_batch(batch_id: str):
    # Layer 1: Sync Timing Profiler
    with OperationProfiler(f"Batch Processing {batch_id}"):
        
        # Layer 2: Async Mutex Lock
        async with AsyncMutex(f"batch_lock_{batch_id}"):
            
            # Layer 3: Async Connection Scope
            async with get_async_connection() as conn:
                print(f"[WORK] Executing batch inside session {conn['session_id']}")
                
                # Layer 4: Sync File Scratchpad
                with temporary_scratchpad(f"{batch_id}.txt") as scratch_path:
                    scratch_path.write_text("Row1,Row2,Row3")
                    content = scratch_path.read_text()
                    print(f"[WORK] Read from temp file: {content}")

if __name__ == "__main__":
    asyncio.run(process_data_batch("batch_9021"))

```

---
### Execution Pipeline Explanation

- OperationProfiler (with): Captures start time on __enter__ and logs execution elapsed time on __exit__.
- AsyncMutex (async with): Awaits __aenter__ to simulate non-blocking lock acquisition across asynchronous tasks.
    - get_async_connection (async with): Opens an async session resource, yields it to the inner block, and automatically triggers connection teardown post-yield.
    - temporary_scratchpad (with): Creates a local scratch file, yields the path for read/write operations, and guarantees file unlinking inside the finally block when exiting scope.

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Context Managers

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Context Managers