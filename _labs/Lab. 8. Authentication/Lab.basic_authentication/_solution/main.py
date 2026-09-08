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