# Request Parameters

---
### Request Parameters explained

FastAPI extracts HTTP request parameters by inspecting parameter locations, Python type hints, and marker functions (Path, Query, Header, etc.)

Lets look at: 
- Path Parameters
- Query Parameters
- Request Body Parameters
- Header Parameters
- Cookie Parameters
- Form Body Parameters
- File upload Parameters

And a complete practical example!


---
### Path Parameters (Path)

Path parameters are hardcoded into URL route (e.g., /orders/{order_id}). 

They identify specific resources in a REST API and are **strictly required**.

Real-World Use Case
- Locating a specific tenant's order record in a multi-tenant database.

Behavior
- FastApi raises an automatic HTTP 422 error if the path segment cannot be converted to the declared type (e.g., non-integer string where int is required).

```
@app.get("/tenants/{tenant_id}/orders/{order_id}")
async def get_tenant_order(
    tenant_id: Annotated[str, Path(description="Organization string ID")],
    order_id: Annotated[int, Path(ge=1, description="Database integer ID (>= 1)")],
):
    return {"tenant_id": tenant_id, "order_id": order_id}
```

---
### Query Parameters (Query)

Query parameters appear after ? in the URL (/products?q=tech&page=2)

Function arguments that are scalar types (str, int, bool) and not present in the path string default to query parameters

Real-World Use Case
- Filtering, searching, sorting, and paginating long lists of items in an e-commerce catalog

Behavior
- Can be mandatory, optional, or have default fallback values

```
@app.get("/products/search")
async def search_catalog(
    q: Annotated[str, Query(min_length=3, description="Search string")] = "laptop",
    max_price: Annotated[float | None, Query(gt=0)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
):
    return {"q": q, "max_price": max_price, "page": page}
```

---
### Request Body (Body & Pydantic Models)

Data sent via HTTP POST, PUT, or PATCH payloads

Setting the type annotation to a Pydantic BaseModel instructs FastAPI to parse, validate, and serialize JSON payloads

Real-World Use Case
- Submitting complex data structures like a payment transaction payload with nested items

Behavior
- Pydantic models parse the raw JSON stream into typed Python objects.
- to receive isolated JSON fields outside a model, wrapper parameters with Body(embed=True).

---
### Request Body (Body & Pydantic Models)

```
class PaymentItem(BaseModel):
    sku: str
    price: float = Field(gt=0)

@app.post("/checkout/pay")
async def process_payment(
    items: list[PaymentItem],
    idempotency_key: Annotated[str, Body(embed=True)],
):
    return {"processed_items": len(items), "key": idempotency_key}
```

---
### Header Parameters (Header)
HTTP headers carry request metadata like API authorization tokens, client IDs, or client user-agents

Real-World Use Case
- Verifying API keys passed by microservices or third-party webhooks

Behavior
- HTTP header keys are case-insensitive and standardly use hyphens (X-API-Key)
- FastAPI automatically converts Python snake_case variable names (e.g., x_api_key) to hyphenated headers (X-API-Key).

---
### Header Parameters (Header)

```
@app.get("/analytics/metrics")
async def get_metrics(
    x_api_key: Annotated[str, Header(description="Service API authorization key")],
    user_agent: Annotated[str | None, Header()] = None,
):
    return {"authenticated": True, "agent": user_agent}
```

---
### Cookie Parameters (Cookie)
Extracted directly from the Cookie header sent automatically by browsers

Real-World Use Case
- validating server-side browser sessions
- reading state-tracking cookies for Web applications

Behavior
- decodes cookie string keys cleanly without manually parsing the HTTP Cookie header string.

```
@app.get("/user/profile")
async def get_profile(
    session_id: Annotated[str, Cookie(description="HTTP-only session cookie")],
):
    return {"session_id": session_id}
```

---
### Form Parameters (Form)
Extracts parameters sent via application/x-www-form-urlencoded

Real-World Use Case
- handling traditional HTML <form> submissions 
- or complying with the OAuth2 Password Specification (username and password credentials)

Behavior
- unlike standard JSON endpoint models, Form() fields read URL-encoded form bodies.

```
@app.post("/auth/login")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    return {"user": username, "status": "authenticated"}
```

---
### Class based form parameters

You can also use your own classes to retrieve the data from the form

```
from typing import Annotated
from fastapi import Depends, FastAPI, Form

app = FastAPI()

class User:
    def __init__(
        self,
        firstname: Annotated[str, Form()],
        lastname: Annotated[str, Form()],
    ):
        self.firstname = firstname
        self.lastname = lastname

@app.post("/users/add", status_code=status.HTTP_201_CREATED)
async def add_user(user_data: Annotated[User, Depends()]): # <- more on this later..
    return {
        "firstname": user_data.firstname,
        "filename": user_data.photo.filename
    }
```

---
### File Upload Parameters (File & UploadFile)
Handles binary inputs sent via multipart/form-data

Real-World Use Case
- user profile image uploads or processing uploaded PDF invoices

Behavior
- using UploadFile utilizes Python's SpooledTemporaryFile
- it streams files on disk once memory thresholds are hit, preventing server crashes when receiving gigabyte-scale uploads (unlike raw bytes with File()).

```
@app.post("/documents/ocr")
async def process_document(
    document: Annotated[UploadFile, File(description="PDF or Image scan")],
):
    return {"filename": document.filename, "content_type": document.content_type}
```

---
### Unified Real-World Request Flow

This production-grade example illustrates how FastAPI orchestrates these parameters simultaneously during a high-security KYC (Know Your Customer) merchant document submission workflow:

```
from typing import Annotated
from fastapi import FastAPI, Path, Query, Header, Cookie, Form, File, UploadFile
from pydantic import BaseModel, EmailStr

app = FastAPI()

@app.post("/merchants/{merchant_id}/documents/upload")
async def upload_merchant_kyc_document(
    # 1. Path: Locates the exact merchant account entity
    merchant_id: Annotated[int, Path(ge=1000, description="Merchant account ID")],
    
    # 2. Query: Sets operational control flags
    async_processing: Annotated[bool, Query(description="Offload OCR to background queue")] = True,
    
    # 3. Headers: Infrastructure routing & microservice API security
    x_client_id: Annotated[str, Header(description="Originating API Gateway client identifier")] = ...,
    
    # 4. Cookies: Authenticated Web Portal Operator session
    operator_session: Annotated[str, Cookie(description="Operator auth token")] = ...,
    
    # 5. Form Fields: Non-JSON metadata accompanying file stream
    document_type: Annotated[str, Form(description="e.g., passport, tax_return, business_license")] = ...,
    contact_email: Annotated[EmailStr, Form()] = ...,
    
    # 6. File Stream: Binary file object sent via multipart/form-data
    kyc_file: UploadFile = File(description="Scanned document file stream")
):
    return {
        "merchant_id": merchant_id,
        "async_processing": async_processing,
        "x_client_id": x_client_id,
        "operator_session": operator_session,
        "document_type": document_type,
        "contact_email": contact_email,
        "filename": kyc_file.filename
    }
```

---
### Execution Pipeline Explanation:

- URL Template Matching: /merchants/5021/documents/upload maps 5021 directly to merchant_id as a Path parameter
- URL Query Parsing: Any string after ? (e.g., ?async_processing=false) is evaluated by the Query engine. Missing optional values fallback to defaults
- HTTP Request Headers & Cookies: FastAPI retrieves request headers (x-client-id) and cookies (operator_session) directly from the HTTP transport layer, converting naming conventions automatically
- Payload Processing (multipart/form-data constraint)
    - HTTP protocol specifications prevent combining application/json and multipart/form-data within a single payload stream. When uploading files (UploadFile), payload fields must use Form() parameters instead of Pydantic models (Body())
- Type Validation Engine
    - Prior to entering the function execution block, Pydantic parses every parameter (int, bool, EmailStr). If any field fails type assertions (e.g., merchant_id set to "abc"), execution halts immediately and returns a standardized JSON 422 Unprocessable Entity response detailing the exact failure

<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Request Parameters

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Request Parameters