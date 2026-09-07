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