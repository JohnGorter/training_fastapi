# NoSQL

---
### NoSQL

NoSQL database systems were designed to address the physical limitations of traditional relational databases (SQL) when handling modern web-scale, high-velocity, and unstructured data.

---
### Scalability Paradigm (Vertical vs. Horizontal)

SQL (Vertical Scaling / Scale-Up): Relational databases depend on structured schemas and complex relations (joins), making them hard to distribute across multiple machines 
- scalability is achieved primarily by adding more CPU, RAM, and SSD power to a single server instance.

NoSQL (Horizontal Scaling / Scale-Out)
- designed from the ground up to operate across distributed hardware clusters
- data is automatically partitioned across many commodity nodes using sharding, allowing data throughput and storage capacity to scale linearly by adding more nodes.

---
### Consistency Models (ACID vs. BASE)

SQL (ACID Compliance)
- focuses on strict data integrity, ensuring every transaction satisfies Atomicity, Consistency, Isolation, and Durability.

- Atomicity: All operations in a transaction succeed, or the entire transaction fails.
- Consistency: Data must validly follow all defined schema rules and constraints.
- Isolation: Concurrent transactions do not affect or see each other's uncommitted state.
- Durability: Once committed, changes survive system failures.

---
### Consistency Models (ACID vs. BASE)

NoSQL (BASE Compliance)
- prioritizes high availability and performance over instantaneous consistency.

- Basically Available: The database prioritizes responding to read/write requests, even during node failures or network partitions.
- Soft-state: System state can change over time due to asynchronous background replication, even without active user input.
- Eventual consistency: Data updates replicate across all cluster nodes eventually, guaranteeing that reads across nodes will match given enough time.

---
### CAP Theorem Trade-Offs

The Constraint: In any distributed data store, you can simultaneously guarantee at most two out of three properties:
- Consistency (all nodes see the same data at the same time)
- Availability (every non-failing node returns a non-error response)
- Partition Tolerance (the system continues operating despite network disruptions between nodes).

SQL Positioning (CA)
- single-node or tightly coupled SQL databases guarantee strong Consistency and Availability but sacrifice Partition Tolerance when split across distinct network nodes

NoSQL Positioning (CP or AP): Because distributed networks always experience latency or network partitions (making Partition Tolerance mandatory), NoSQL systems choose between:
- CP (Consistency & Partition Tolerance): Block read/write access to nodes that cannot confirm state synchronization (e.g., MongoDB primary election mechanics).
- AP (Availability & Partition Tolerance): Allow nodes to write independently during a network split, accepting temporary data drift (e.g., Apache Cassandra).

---
### Schema Design & Data Modeling Flexibility

SQL (Rigid / Schema-on-Write)
- requires a predefined, strict tabular structure with fixed data types before data entry
- structural changes require schema migrations (ALTER TABLE).

NoSQL (Flexible / Schema-on-Read)
- stores unstructured or semi-structured data (JSON/BSON documents, key-value pairs, wide-columns, graphs)
- fields can be added dynamically per document without migration downtime

---
### MongoDB

MongoDB is the first NoSQL implementation we are going to implement
- Async of course!

**AsyncMongoClient is available in PyMongo 4.9+ (replacing the legacy Motor library). It provides native async/await syntax using Python’s built-in asyncio loop.**

---
### Installation

You can download and run mongodb server locally

```
brew tap mongodb/brew
brew trust mongodb/brew
brew install mongodb-community
brew services start mongodb-community
mongosh
```

or use a cloud free cluster (MongoDB Atlas)
https://cloud.mongodb.com/

---
### MongoDB Async

Key Async Differences
- await keyword: Network calls (insert_one, find, update_one, delete_one, etc.) must be awaited.

Cursors
- queries returning multiple documents require asynchronous iteration using async for or fetching with to_list()
Context Management
- connection setup and teardown are best handled using async with AsyncMongoClient(...) to ensure sockets close properly.

---
### Installation

Python Driver Setup
Install pymongo (version 4.9 or higher) 

```
pip install "pymongo>=4.9" 
```

---
### Core Async Operations 

Let's examine:
- Connecting and Initializing
- Adding Data (Create)
- Listing Data (Read)
- Changing Data (Update)
- Deleting Data (Delete)
- Closing the Connection

---
### Connecting

Import AsyncMongoClient directly from pymongo

```
import asyncio
from pymongo import AsyncMongoClient

async def connect_example():
    uri = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"
    
    # Connection initialized asynchronously
    async with AsyncMongoClient(uri) as client:
        db = client["store_db"]
        products = db["products"]
        print("Connected asynchronously!")

asyncio.run(connect_example())
```

---
### Adding Data (Create)

Await single or bulk insertions to ensure write concerns are acknowledged before proceeding

```
# Insert single document
new_item = {"name": "Wireless Mouse", "price": 29.99, "stock": 150}
result = await products.insert_one(new_item)
print(f"Inserted ID: {result.inserted_id}")

# Insert multiple documents
bulk_items = [
    {"name": "Mechanical Keyboard", "price": 89.99, "stock": 45},
    {"name": "USB-C Hub", "price": 19.99, "stock": 200}
]
await products.insert_many(bulk_items)
```

---
### Listing Data (Read)

Use async for to stream results from an async cursor without blocking the event loop, or use to_list() to collect all results into memory

```
# Single document search
mouse = await products.find_one({"name": "Wireless Mouse"})

# Stream documents asynchronously with 'async for'
cursor = products.find({"price": {"$gt": 20}})
async for item in cursor:
    print(item["name"], item["price"])

# Or fetch a limited batch directly as a list
items_list = await products.find({"price": {"$gt": 20}}).to_list(length=100)
```

---
### Changing Data (Update)

Modify existing documents using standard operators ($set, $inc, $push) with await.

```
# Update single item
await products.update_one(
    {"name": "Wireless Mouse"},
    {"$inc": {"stock": -1}}
)

# Update multiple items
await products.update_many(
    {"price": {"$gt": 50}},
    {"$set": {"discounted": True}}
)
```

---
### Deleting Data (Delete)

Remove records asynchronously

```
# Delete one
await products.delete_one({"name": "USB-C Hub"})

# Delete many
await products.delete_many({"stock": 0})
```

---
### Closing the Connection

When using async with AsyncMongoClient(...), connection teardown is handled automatically when leaving the context block
- if managing the instance manually, call await client.close().

```
client = AsyncMongoClient(uri)
# ... perform operations ...
await client.close()
```

---
### All-Encompassing Async Example

This asynchronous script manages an enterprise asset inventory using AsyncMongoClient, handling connections, error catching, dynamic updates, cursor streaming, and clean context closing inside an asyncio event loop

```
import asyncio
import os
from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

async def run_async_inventory_demo():
    # Retrieve connection string from environment
    uri = os.getenv(
        "MONGO_URI",
        "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"
    )

    try:
        # Step 1: Connect asynchronously using context manager
        print("[1] Connecting to MongoDB Atlas asynchronously...")
        async with AsyncMongoClient(uri, serverSelectionTimeoutMS=5000) as client:
            
            # Ping database to confirm connection
            await client.admin.command('ping')
            print("    Connection successful!")

            db = client["async_warehouse_db"]
            devices = db["devices"]

            # Clear collection for demonstration rerun
            await devices.delete_many({})

            # Step 2: Add Documents (Create)
            print("\n[2] Seeding devices dataset asynchronously...")
            inventory = [
                {"sku": "DEV-01", "name": "Laptop Pro 15", "category": "Computers", "price": 1299.00, "stock": 12, "tags": ["work", "portable"]},
                {"sku": "DEV-02", "name": "Monitor 27-inch", "category": "Displays", "price": 349.50, "stock": 25, "tags": ["office"]},
                {"sku": "DEV-03", "name": "Ergonomic Chair", "category": "Furniture", "price": 450.00, "stock": 5, "tags": ["office", "furniture"]},
                {"sku": "DEV-04", "name": "4K Web Camera", "category": "Peripherals", "price": 89.99, "stock": 0, "tags": ["video", "accessory"]}
            ]
            
            insert_result = await devices.insert_many(inventory)
            print(f"    Inserted {len(insert_result.inserted_ids)} records.")

            # Step 3: List Documents (Read via async cursor)
            print("\n[3] Querying in-stock items with price > $100:")
            query_filter = {"stock": {"$gt": 0}, "price": {"$gt": 100}}
            projection = {"_id": 0, "sku": 1, "name": 1, "price": 1, "stock": 1}
            
            cursor = devices.find(query_filter, projection)
            async for item in cursor:
                print(f"    - [{item['sku']}] {item['name']}: ${item['price']} (In stock: {item['stock']})")

            # Step 4: Change Documents (Update)
            print("\n[4] Updating inventory and tags asynchronously...")
            update_result = await devices.update_one(
                {"sku": "DEV-04"},
                {
                    "$set": {"stock": 15},
                    "$push": {"tags": "restocked"}
                }
            )
            print(f"    Matched: {update_result.matched_count}, Modified: {update_result.modified_count}")

            # Bulk price update
            await devices.update_many(
                {"category": "Displays"},
                {"$inc": {"price": 20.00}}
            )

            # Step 5: Delete Documents (Delete)
            print("\n[5] Removing furniture category items...")
            delete_result = await devices.delete_many({"category": "Furniture"})
            print(f"    Deleted count: {delete_result.deleted_count}")

            # Verify final state using to_list()
            print("\n[6] Final inventory state:")
            final_docs = await devices.find({}, {"_id": 0, "sku": 1, "name": 1, "price": 1, "stock": 1, "tags": 1}).to_list(length=10)
            for doc in final_docs:
                print(f"    {doc}")

        # Client connection automatically closed here via async context manager
        print("\n[7] Connection closed automatically upon exiting context.")

    except ConnectionFailure:
        print("Failed to connect to server. Verify network rules and connection URI.")
    except PyMongoError as err:
        print(f"A MongoDB error occurred: {err}")


if __name__ == "__main__":
    # Execute async main loop
    asyncio.run(run_async_inventory_demo())
```

---
### MongoDB and FastAPI

In web applications like FastAPI opening and closing a database connection for every single HTTP request adds unnecessary overhead and network latency 
- use Lifespan Context Managers
    - allows you to open a single connection pool when the application starts up and cleanly close it when the application shuts down

---
### Core Concept: FastAPI Lifespan

The lifespan parameter in FastAPI accepts an asynccontextmanager:
- anything before the yield statement executes before the app starts serving requests (startup)
- anything after yield executes after the app finishes processing requests (shutdown)

---
### FastAPI Lifespan

Here is an implementation

```
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # Create the client and attach it to app.state
    app.state.mongo_client = AsyncMongoClient(MONGO_URI)
    app.state.db = app.state.mongo_client["production_db"]
    
    yield  # Application runs and serves requests here
    
    # --- SHUTDOWN ---
    # Clean up and close connection pool
    await app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)
```

---
### Real-Life Use Case 1 

**E-Commerce Order Service with Transactions**

In an e-commerce backend, creating an order requires deducting stock and generating an invoice atomically using MongoDB transactions

Transactions require an active database session (start_session()) tied to the shared AsyncMongoClient.


---
### Implementation

```
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from pymongo import AsyncMongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize shared connection pool
    client = AsyncMongoClient(MONGO_URI)
    app.state.mongo_client = client
    app.state.db = client["ecommerce_db"]
    print("Database connection pool initialized.")
    
    yield
    
    # Shutdown: Flush operations and close sockets
    await app.state.mongo_client.close()
    print("Database connection pool closed.")

app = FastAPI(title="Order Service", lifespan=lifespan)

class OrderRequest(BaseModel):
    user_id: str
    item_sku: str
    quantity: int
    price: float

@app.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderRequest, request: Request):
    client: AsyncMongoClient = request.app.state.mongo_client
    db = request.app.state.db
    
    # Use MongoDB ACID session/transaction across multiple collections
    async with await client.start_session() as session:
        async with session.start_transaction():
            # 1. Check & Update Inventory
            inventory_res = await db.products.update_one(
                {"sku": order.item_sku, "stock": {"$gte": order.quantity}},
                {"$inc": {"stock": -order.quantity}},
                session=session
            )
            
            if inventory_res.modified_count == 0:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient stock or item not found."
                )
            
            # 2. Insert Order Record
            new_order = {
                "user_id": order.user_id,
                "item_sku": order.item_sku,
                "quantity": order.quantity,
                "total": order.quantity * order.price,
                "status": "PAID"
            }
            order_res = await db.orders.insert_one(new_order, session=session)
            
            return {
                "message": "Order processed successfully", 
                "order_id": str(order_res.inserted_id)
            }
```

---
### Real-Life Use Case 2

**Multi-Tenant SaaS with Dynamic Index Creation**

In multi-tenant or analytics applications, you often need to ensure database indexes exist before receiving traffic (so queries don't trigger full collection scans). 

Managing index builds inside the lifespan startup phase ensures the database is optimized before serving traffic.

---
### Implementation

```
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, Request
from pymongo import AsyncMongoClient, ASCENDING, DESCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://<username>:<password>@cluster0.mongodb.net/")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    client = AsyncMongoClient(MONGO_URI)
    db = client["saas_logs_db"]
    
    # Pre-build indexes asynchronously on application startup
    print("Building collection indexes...")
    await db.user_logs.create_index([("tenant_id", ASCENDING), ("timestamp", DESCENDING)])
    await db.user_logs.create_index([("action", ASCENDING)])
    
    app.state.mongo_client = client
    app.state.db = db
    
    yield
    
    # Shutdown
    await app.state.mongo_client.close()

app = FastAPI(title="Log Ingestion Service", lifespan=lifespan)

# Dependency to inject DB collection into path operations
def get_log_collection(request: Request):
    return request.app.state.db["user_logs"]

@app.get("/logs/{tenant_id}")
async def get_tenant_logs(
    tenant_id: str, 
    action: Optional[str] = None,
    logs_col = Depends(get_log_collection)
):
    query = {"tenant_id": tenant_id}
    if action:
        query["action"] = action
        
    # Query uses the pre-built compound index created in lifespan startup
    cursor = logs_col.find(query, {"_id": 0}).sort("timestamp", -1).limit(50)
    results = await cursor.to_list(length=50)
    
    return {"tenant_id": tenant_id, "count": len(results), "logs": results}
```


---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. NoSQL

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
NoSQL