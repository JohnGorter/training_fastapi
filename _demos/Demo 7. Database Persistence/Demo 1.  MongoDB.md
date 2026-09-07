# Demo MongoDB

### Step 0. Install and demonstrate the installation steps for mongodb locally

Install mongodb
```
brew tap mongodb/brew
brew install mongodb-community
mongod --dbpath=/data/db
```
use mongodb
```
mongo
```
frequent commands
```
show dbs
use <db>
show collections
db.items.insertOne({})
```

Verify that it is running.

### Step 1. Open the demo project
Open the demo project and open the main.py. 

Make sure the following packages are added
```
uv add "fastapi[standard]"
uv add HTTPie
uv add pydantic
uv add pydantic[email]
uv add pydantic-settings
```

create an .env file with the following
```
# "mongodb+srv://johngorter_db_user:ouq62yRHTAKnTYmp@cluster0.ut813ql.mongodb.net/?appName=Cluster0"
MONGODB_URI = "mongodb://127.0.0.1:27017/"
DB_NAME = "fastapi_db"
```

then, create a settings.py with the following code

```
from pydantic_settings import SettingsConfigDict, BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    db_name: str = "fastapi_db"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

Explain the code. 

### Step 2. Create the database logic

Create a database.py file with the following code

```
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from settings import settings

class Database:
    client: AsyncMongoClient | None = None
    db: AsyncDatabase |  None = None

db_context = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open async MongoDB client
    db_context.client = AsyncMongoClient(settings.mongodb_uri)
    db_context.db = db_context.client[settings.db_name]
    yield
    # Shutdown: Close client
    await db_context.client.close()
```

Explain the code

### Step 3. Create the models for the database

Create a file called models.py and copy in the following code: 
```
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ItemModel(BaseModel):
    name: str
    description: str | None = None
    price: float
    in_stock: bool = True

class ItemResponse(ItemModel):
    model_config = ConfigDict(populate_by_name=True)

class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: str | None = None
    in_stock: str | None = None
```

### Step 4. Create the code that uses the database to insert

Copy over the code below
```
from typing import List
from fastapi import FastAPI, HTTPException, status
from database import lifespan, db_context
from models import ItemModel, ItemResponse, ItemUpdate

app = FastAPI(title="FastAPI with PyMongo AsyncMongoClient", lifespan=lifespan)

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemModel):
    result = await db_context.db.items.insert_one(item.model_dump())
    created_doc = await db_context.db.items.find_one({"_id": result.inserted_id})
    return created_doc

```

Explain the code.

### Step 5. Run the demo

use HTTPie to execute a request
```
http POST localhost:8000/items/ name=john price=10
```

Show that it was inserted using a terminal.


### Step 6. Complete example

Open main.py and copy over the following code
```
from typing import List
from fastapi import FastAPI, HTTPException, status
from bson import ObjectId
from database import lifespan, db_context
from models import ItemModel, ItemResponse, ItemUpdate

app = FastAPI(title="FastAPI with PyMongo AsyncMongoClient", lifespan=lifespan)

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemModel):
    result = await db_context.db.items.insert_one(item.model_dump())
    created_doc = await db_context.db.items.find_one({"_id": result.inserted_id})
    return created_doc

@app.get("/items/", response_model=List[ItemResponse])
async def get_all_items():
    items = []
    async for doc in db_context.db.items.find():
        items.append(doc)
    return items

@app.get("/items/{name}", response_model=ItemResponse)
async def get_item(name: str):
    doc = await db_context.db.items.find_one({"name": name})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    return doc

@app.patch("/items/{name}", response_model=ItemResponse)
async def update_item(name: str, patch: ItemUpdate):
    update_data = {k: v for k, v in patch.model_dump(exclude_unset=True).items()}
    if update_data:
        doc = await db_context.db.items.find_one({"name": name})
        if not doc:
            raise HTTPException(status_code=404, detail="Item not found")
        await db_context.db.items.update_one(
            {"_id": str(doc["_id"])},
            {"$set": update_data}
        )

    updated_doc = await db_context.db.items.find_one({"name": name})
    if not updated_doc:
        raise HTTPException(status_code=404, detail="Item not found")

    return updated_doc

@app.delete("/items/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(name: str):
    result = await db_context.db.items.delete_one({"name": name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
```


Walk through the code and run all endpoints and show the results in the terminal


-= end of demo =-