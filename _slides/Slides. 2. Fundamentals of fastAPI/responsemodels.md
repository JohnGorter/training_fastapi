# Response Models


---
### Response Models
In this lesson, we explore:
- response models

*Lets bring Pydantic into FastAPI!*

---
### Response models

FastAPI response models handle serialization, payload sanitization, HTTP status enforcement, and automatic OpenAPI documentation by projecting raw Python return values into explicit outgoing schemas

**It uses Pydantic for this!**

You can define different models/classes for the purpose of receiving and returning data and therefore exclude fields from the response

---
### Standard Response Filtering

Declaring a Pydantic model in response_model ensures internal entity attributes (like database primary keys, password hashes, or secret API keys) are safely stripped before JSON transmission

Real-World Use Case
- returning user profile data from a database object without exposing hashed credentials or internal salt values

Behavior
- FastAPI converts ORM instances or dictionaries into the specified response_model schema, omitting any fields not defined in that output model

---
### Standard Response Filtering
```
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class UserInDB(BaseModel):
    id: int
    username: str
    email: EmailStr
    hashed_password: str  # Secret internal field

class UserPublicResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

@app.post("/users/", response_model=UserPublicResponse)
async def create_user(user: UserInDB):
    # Returns UserInDB object, but FastAPI strips hashed_password automatically
    return user
```

---
### Dynamic Field Exclusion 

Field exclusion parameters allow route handlers to omit None values, default values, or uninitialized fields from the outgoing JSON string, drastically reducing network payload size

Real-World Use Case
- sparsely populated medical or telemetry records where transmitting null-value fields wastes bandwidth

Behavior
- flags like response_model_exclude_none=True strip attributes set to None prior to JSON serialization

---
### Dynamic Field Exclusion 

```
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PatientTelemetry(BaseModel):
    device_id: str
    heart_rate: int
    blood_oxygen: int | None = None
    alert_notes: str | None = None

@app.get("/telemetry/{device_id}", response_model=PatientTelemetry, response_model_exclude_none=True)
async def get_telemetry(device_id: str):
    # 'blood_oxygen' and 'alert_notes' are omitted from JSON payload because they evaluate to None
    return PatientTelemetry(device_id=device_id, heart_rate=72, blood_oxygen=None)
```

---
### Union & Polymorphic Responses

When an endpoint returns different object structures depending on user tier, state, or permissions, a Union type annotation ensures OpenAPI correctly documents all candidate schemas

Real-World Use Case
- an account endpoint returning basic user metrics for standard users versus extended system telemetry for administrative users

Behavior
- FastAPI matches the return dictionary/instance against candidate schemas in the Union list, serializing according to the first matching model.

---
### Union & Polymorphic Responses
```
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class StandardPlan(BaseModel):
    account_id: str
    max_projects: int = 5

class EnterprisePlan(BaseModel):
    account_id: str
    max_projects: int = 9999
    dedicated_support_email: str

@app.get("/accounts/{account_id}", response_model=Union[StandardPlan, EnterprisePlan])
async def get_account_plan(account_id: str):
    if account_id.startswith("ent_"):
        return EnterprisePlan(account_id=account_id, dedicated_support_email="vip@corp.com")
    return StandardPlan(account_id=account_id)
```

---
### Mixing Models with Status Codes 

The status_code decorator parameter sets default HTTP response codes (e.g., 201 Created), while declaring a Response argument allows dynamic injection of headers or cookies inside the handler

Real-World Use Case
- setting custom microservice tracking headers (X-Trace-ID) and returning HTTP 201 when persisting a newly created transaction

Behavior
- the Response parameter grants direct mutability over headers and cookies without breaking Pydantic's response_model serialization pipeline

---
### Explicit Status Codes & Dynamic Modification (Response)
```
from fastapi import FastAPI, Response, status
from pydantic import BaseModel

app = FastAPI()

class OrderCreatedResponse(BaseModel):
    order_id: str
    total_amount: float

@app.post("/orders/", response_model=OrderCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_order(response: Response):
    # Mutate response metadata dynamically
    response.headers["X-Order-Tracking-UUID"] = "ord_trk_99021a"
    response.set_cookie(key="cart_session", value="cleared")
    return {"order_id": "ord_8820", "total_amount": 299.95}
```

---
### Enable extra = "allow" 

Setting extra = "allow" in model_config instructs Pydantic to retain unmapped dictionary keys during serialization.

```
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

app = FastAPI()

class UserResponse(BaseModel):
    firstname: str
    lastname: str

    model_config = ConfigDict(extra="allow")

@app.post("/users/add", response_model=UserResponse)
async def add_user(user: UserResponse):
    # 'status' is preserved in the output JSON despite not being a defined field
    return {**user.model_dump(), "status": "added"}
```

---
### Modern approach and best practice

You don't have to use response_model in the last versions of FastAPI
- use typehints


---
###

```
The most simple and modern approach relies on pure Python return type annotations (-> Model) combined with Pydantic v2's built-in model features.

By letting type hints drive FastAPI's serialization and keeping configuration inside your Pydantic schemas, you eliminate redundant decorator parameters entirely while preserving total type safety, auto-generated OpenAPI documentation, and response filtering.

The Modern Standard Pattern
Python
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI()

# 1. Internal/Database Model (contains sensitive data)
class UserDB(BaseModel):
    id: int
    username: str
    hashed_password: str

# 2. Public API Schema (configures its own serialization rules)
class UserPublic(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None

    # Keep serialization rules (like excluding None values) inside the model
    model_config = ConfigDict(response_model_exclude_none=True)


# ------------------------------------------------------------------
# Route 1: Direct Return with Explicit Conversion
# ------------------------------------------------------------------
@app.get("/users/{user_id}")
def get_user(user_id: int) -> UserPublic:
    db_user = UserDB(id=user_id, username="alice", hashed_password="secret_hash")
    
    # Explicit conversion gives full IDE autocompletion & MyPy type safety
    return UserPublic.model_validate(db_user)


# ------------------------------------------------------------------
# Route 2: Returning Lists or Collections
# ------------------------------------------------------------------
@app.get("/users")
def list_users() -> list[UserPublic]:
    db_users = [
        UserDB(id=1, username="alice", hashed_password="hash1"),
        UserDB(id=2, username="bob", hashed_password="hash2"),
    ]
    
    return [UserPublic.model_validate(u) for u in db_users]
```

---
### Why This Is Preferred Today

- No Magic Decorator Parameters
    - no response_model, response_class, or response_model_exclude_none on @app.get(...).
- Strict Type Safety
    - Static type checkers (MyPy, Pyright, Pylance) verify that your function actually returns
- Decoupled Architecture
    - Route definitions stay minimal, while data validation and serialization behavior live inside the Pydantic schemas
- Auto-Generated Swagger/OpenAPI
    - FastAPI automatically generates full JSON schema models in /docs directl


---
### Unified Enterprise Response Workflow

This production pattern demonstrates how FastAPI processes response modeling, status code assignment, header mutability, field sanitization, and sparse payload filtering during an enterprise invoice generation request

```
from datetime import datetime
from typing import Annotated
from fastapi import FastAPI, Path, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# Internal Database Representation (Data Source)
class InvoiceInDB(BaseModel):
    invoice_id: str
    merchant_id: str
    internal_ledger_code: str  # Sensitive internal identifier
    amount: float
    tax_exempt: bool
    notes: str | None = None
    payment_processor_token: str  # Sensitive payment metadata
    created_at: datetime

# Public API Response Schema (Sanitized Output Contract)
class PublicInvoiceResponse(BaseModel):
    invoice_id: str
    amount: float = Field(gt=0)
    tax_exempt: bool
    notes: str | None = None
    created_at: datetime

@app.post(
    "/merchants/{merchant_id}/invoices/{invoice_id}/finalize",
    response_model=PublicInvoiceResponse,
    response_model_exclude_none=True,  # Omit optional 'notes' if None
    status_code=status.HTTP_201_CREATED,
    tags=["Billing Services"]
)
async def finalize_invoice(
    merchant_id: Annotated[str, Path()],
    invoice_id: Annotated[str, Path()],
    response: Response,
):
    # Simulate DB fetch of an internal record containing sensitive data
    db_record = InvoiceInDB(
        invoice_id=invoice_id,
        merchant_id=merchant_id,
        internal_ledger_code="LEDGER_SECRET_9021",
        amount=1250.00,
        tax_exempt=False,
        notes=None,  # Will be excluded due to response_model_exclude_none=True
        payment_processor_token="tok_live_sec_88291039120",
        created_at=datetime.now()
    )

    # Dynamic header/cookie manipulation on the outgoing HTTP envelope
    response.headers["X-Invoice-Status"] = "Finalized"
    response.headers["X-Audit-Trace-ID"] = "trc_inv_88290"

    # Return raw internal DB model; FastAPI sanitizes it against PublicInvoiceResponse
    return db_record
```

---
### Execution Pipeline Explanation

- Status Code Setup: FastAPI sets the HTTP status code to 201 Created prior to execution.
- Internal Processing
    - retrieve a raw InvoiceInDB model containing internal credentials (internal_ledger_code, payment_processor_token) and notes=None
- Envelope Mutation
    - the Response object injects runtime HTTP headers (X-Invoice-Status, X-Audit-Trace-ID) 
- Field Filtering & Sanitization
    - FastAPI passes db_record through PublicInvoiceResponse
    - sensitive fields (internal_ledger_code, payment_processor_token, merchant_id) are stripped automatically
- Sparse Serialization
    - because response_model_exclude_none=True, emitting a clean, minimal JSON payload directly to the caller


---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Response Models 

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Response Models
