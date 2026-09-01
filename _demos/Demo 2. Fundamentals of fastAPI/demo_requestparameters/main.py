from typing import Annotated

from fastapi import FastAPI, Query, Body, Header, Cookie, Form, UploadFile, File
from pydantic import BaseModel, Field
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# request parameters demo
@app.get("/products/search")
async def search_catalog(
    q: Annotated[str, Query(min_length=3, description="Search string")] = "laptop",
    max_price: Annotated[float | None, Query(gt=0)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
):
    return {"q": q, "max_price": max_price, "page": page}


class PaymentItem(BaseModel):
    sku: str
    price: float = Field(gt=0)

# body parameters demo
@app.post("/checkout/pay")
async def process_payment(
    items: list[PaymentItem],
    idempotency_key: Annotated[str, Body(embed=True)],
):
    return {"processed_items": len(items), "key": idempotency_key}

# header parameters demo
@app.get("/analytics/metrics")
async def get_metrics(
    x_api_key: Annotated[str, Header(description="Service API authorization key")],
    user_agent: Annotated[str | None, Header()] = None,
):
    return {"authenticated": True, "agent": user_agent}

# cookie parameters demo
@app.get("/user/profile")
async def get_profile(
    session_id: Annotated[str, Cookie(description="HTTP-only session cookie")],
):
    return {"session_id": session_id}

# form parameters demo
@app.post("/auth/login")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    return {"user": username, "status": "authenticated"}

# file upload demo
@app.post("/documents/ocr")
async def process_document(
    document: Annotated[UploadFile, File(description="PDF or Image scan")],
):
    return {"filename": document.filename, "content_type": document.content_type}
