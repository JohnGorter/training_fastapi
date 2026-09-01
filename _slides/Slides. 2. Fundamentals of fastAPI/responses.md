# Responses


---
### Responses

In this lesson, we explore:
- response headers
- response types
- response status codes

---
### Response headers

You can inject response headers, you dont need to return them

```
@app.get("/header/{name}/{value}")
async def header(name:str, value:str, response:Response):
    response.headers[name] = value
    return "normal body"
```

---
### Response Types

You can specify the following response types
- JSONResponse (default)
- HTMLResponse
- PlainTextResponse
- RedirectResponse
- FileResponse
- StreamingResponse

---
### PlainTextResponse as an example

To return plain/text, you can use the PlainTextRespone

Recommended version, this also updates swagger generaated docs to have content-type text/plain!
```
@app.get("/", response_class=PlainTextResponse)
async def main():
    return "Hello World"
```

Alternative version
```
@app.get("/")
async def main():
    return PlainTextResponse("Hello World")
```
---
### RedirectResponse as a second example

Another example is the redirectresponse.

To redirect, use a redirectresponse :D

```
@app.get("/typer")
async def redirect_typer():
    return RedirectResponse("https://typer.tiangolo.com")
```

---
### StreamingResponse
For high-throughput JSON microservices or binary streaming, custom response classes bypass standard Pydantic JSON encoding to maximize raw throughput or handle huge datasets

Real-World Use Case
- exporting high-volume audit logs directly to client browsers as CSV file downloads without causing server memory spikes.

Behavior
- bypasses default JSON encoders, writing raw memory chunks directly to the HTTP socket stream.

---
### StreamingResponse model

```
from collections.abc import Generator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

def stream_csv_export() -> Generator[str, None, None]:
    yield "timestamp,event_type,user_id\n"
    yield "2026-08-21T10:00:00Z,LOGIN,usr_101\n"
    yield "2026-08-21T10:05:00Z,PURCHASE,usr_102\n"

@app.get("/audit/export", response_class=StreamingResponse)
async def export_audit_logs():
    return StreamingResponse(
        stream_csv_export(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_export.csv"}
    )
```

---
### Response status codes

FastAPI controls HTTP response status codes via:
- route decorator parameters
- runtime Response object mutation
- short-circuiting HTTPException raises

---
### Static Status Codes 

Declaring status_code in the route decorator sets the default HTTP status code returned upon successful completion of the endpoint logic

Real-World Use Cases
- explicitly signaling resource creation (201 Created) 
- successful deletion with no body content (204 No Content)

Behavior
- replaces the implicit default 200 OK status code for successful endpoint executions

---
### Static Status Codes 

```
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(username: str):
    return {"username": username, "status": "created"}

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    # Returns empty body with HTTP 204
    return None
```

---
### Dynamic Status Code Mutation

Injecting the Response object into your handler allows you to alter the returned status code conditionally at runtime based on business logic

Real-World Use Case
- returning 200 OK for immediate synchronous execution versus 202 Accepted when work is offloaded to a background queue

Behavior
- overrides the decorator's static status_code value before the HTTP frame is sent to the client

---
### Dynamic Status Code Mutation

```
from fastapi import FastAPI, Response, status

app = FastAPI()

@app.post("/reports/generate")
async def generate_report(is_large: bool, response: Response):
    if is_large:
        # Offload job and signal asynchronous processing
        response.status_code = status.HTTP_202_ACCEPTED
        return {"status": "queued", "job_id": "job_9921"}
    
    # Process inline
    response.status_code = status.HTTP_200_OK
    return {"status": "completed", "data": [1, 2, 3]}
```

---
### Error Status Codes (HTTPException)

Raising HTTPException halts endpoint execution immediately and serializes an error payload directly into an HTTP response with the designated error status code

Real-World Use Case
- returning 404 Not Found for missing resources
- returning 409 Conflict for duplicate entries
- returning 401 Unauthorized for failed token validation

Behavior
- bypasses normal route return values and jump straight to FastAPI's global error handling middleware

---
### Error Status Codes (HTTPException)

```
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

db = {"item_1": "Laptop"}

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    if item_id not in db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{item_id}' was not found in the catalog."
        )
    return {"item": db[item_id]}
```

---
### The status Module Convenience Constants

FastAPI provides the status module (an alias for Starlette's status module) containing human-readable constants for all valid HTTP status codes

Real-World Use Case
- replacing ambiguous "magic numbers" (201, 403, 422) with self-documenting code constants

Behavior
- prevents typos and improves static analysis checks across large codebases

---
### The status Module Convenience Constants

```
from fastapi import FastAPI, status

app = FastAPI()

@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "healthy"}
```

---
### OpenAPI Multi-Status Documentation

Passing a dictionary to the responses parameter in the decorator documents custom status codes and schemas in the auto-generated Swagger UI (/docs)

Real-World Use Case
- formally specifying OpenAPI documentation for expected failure modes (400 Bad Request, 409 Conflict) alongside success payloads

Behavior
- modifies the generated OpenAPI JSON schema without altering runtime code execution

---
### OpenAPI Multi-Status Documentation

```
from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()

class ErrorDetail(BaseModel):
    message: str

@app.post(
    "/payments",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetail, "description": "Invalid Payment Payload"},
        409: {"model": ErrorDetail, "description": "Duplicate Transaction Detected"},
    }
)
async def process_payment():
    return {"payment_id": "pay_9021"}
```
---
### Unified Enterprise Response Status Flow

This production pattern demonstrates static default status codes, runtime mutation, explicit exception raising, and multi-status OpenAPI declarations during a subscription upgrade operation.

```
from typing import Annotated
from fastapi import FastAPI, Path, Query, Response, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

# Standardized Error Schema for Documentation
class ErrorResponse(BaseModel):
    detail: str

# Database simulation
subscriptions_db = {
    "sub_100": {"tier": "free", "active": True},
    "sub_200": {"tier": "pro", "active": False},
}

@app.post(
    "/subscriptions/{sub_id}/upgrade",
    status_code=status.HTTP_200_OK,  # Default status for sync completion
    responses={
        status.HTTP_200_OK: {"description": "Upgrade processed immediately."},
        status.HTTP_202_ACCEPTED: {"description": "Upgrade offloaded to async queue."},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Account inactive."},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Subscription ID not found."},
    },
    tags=["Subscriptions"]
)
async def upgrade_subscription(
    sub_id: Annotated[str, Path(description="Subscription identifier")],
    async_queue: Annotated[bool, Query(description="Force asynchronous worker pipeline")] = False,
    response: Response = None,
):
    # 1. Resource existence check (404 Not Found)
    if sub_id not in subscriptions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{sub_id}' does not exist."
        )

    sub_data = subscriptions_db[sub_id]

    # 2. Business constraint validation (400 Bad Request)
    if not sub_data["active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upgrade an inactive subscription. Reactivate account first."
        )

    # 3. Dynamic status modification (202 Accepted vs 200 OK)
    if async_queue:
        response.status_code = status.HTTP_202_ACCEPTED
        return {
            "subscription_id": sub_id,
            "status": "processing",
            "message": "Upgrade request queued for asynchronous execution."
        }

    # Synchronous processing (Default 200 OK)
    sub_data["tier"] = "enterprise"
    return {
        "subscription_id": sub_id,
        "status": "completed",
        "new_tier": sub_data["tier"]
    }
```

---
### Execution Pipeline Explanation:

- OpenAPI Schema Binding: The responses dictionary binds custom error models and human-readable descriptions to status codes 200, 202, 400, and 404 inside the OpenAPI UI.

- Early Exception Halting: If sub_id is invalid or inactive, HTTPException raises immediately, terminating execution and returning an explicit status code (404 or 400) alongside structured JSON detail.

- Runtime Mutation: If validation passes and async_queue=True is provided via URL query, the endpoint mutates response.status_code to 202 Accepted dynamically before returning the payload. Otherwise, it completes normally using the default 200 OK code.

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Response Status Codes

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Response Status Codes
