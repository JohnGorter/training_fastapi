from typing import List
from fastapi import FastAPI, HTTPException, status
from bson import ObjectId
from database import lifespan, db_context
from models import ItemModel, ItemResponse, ItemUpdate

app = FastAPI(title="FastAPI with PyMongo AsyncMongoClient", lifespan=lifespan)

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemModel):
    # 1 your code here 
    return created_doc

@app.get("/items/", response_model=List[ItemResponse])
async def get_all_items():
    items = []
    # 2 your code here
    return items

@app.get("/items/{name}", response_model=ItemResponse)
async def get_item(name: str):
    # 3 your code here
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    return doc

@app.patch("/items/{name}", response_model=ItemResponse)
async def update_item(name: str, patch: ItemUpdate):
    update_data = {k: v for k, v in patch.model_dump(exclude_unset=True).items()}
    if update_data:
       # 4 your code here

    updated_doc = await db_context.db.items.find_one({"name": name})
    if not updated_doc:
        raise HTTPException(status_code=404, detail="Item not found")

    return updated_doc

@app.delete("/items/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(name: str):
    # 5 your code here
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")