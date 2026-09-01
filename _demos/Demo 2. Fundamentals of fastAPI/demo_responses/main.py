from fastapi import FastAPI, Response, status, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Generator, Union

app = FastAPI()

# demo 1. response header injection
# http -v localhost:8000/demo1
@app.get("/demo1")
async def main(response:Response):
    response.headers["header"] = "value"
    return "Hello World"

# demo 2. response class 
# http -v localhost:8000/demo2
@app.get("/demo2", response_class=PlainTextResponse)
async def main2():
    return "Hello World"

# @app.get("/")
# async def main():
#     return PlainTextResponse("Hello World")

# demo 3. redirect response
# http -v localhost:8000/demo3
@app.get("/demo3")
async def redirect_typer():
    return RedirectResponse("https://typer.tiangolo.com")

# demo 4. streaming response
# http -v localhost:8000/audit/export
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

# demo 5. status codes
# http POST localhost:8000/users/ username==john
@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(username: str):
    return {"username": username, "status": "created"}

# http DELETE localhost:8000/users/2
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    # Returns empty body with HTTP 204
    return None

# demo 6. dynamic status codes
# http POST localhost:8000/reports/generate is_large==true
# http POST localhost:8000/reports/generate is_large==false
@app.post("/reports/generate")
async def generate_report(is_large: bool, response: Response):
    if is_large:
        # Offload job and signal asynchronous processing
        response.status_code = status.HTTP_202_ACCEPTED
        return {"status": "queued", "job_id": "job_9921"}

    # Process inline
    response.status_code = status.HTTP_200_OK
    return {"status": "completed", "data": [1, 2, 3]}

# demo 7. Error status codes
# http localhost:8000/items/10
# http localhost:8000/items/1 
db = {"item_1": "Laptop"}

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    if item_id not in db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{item_id}' was not found in the catalog."
        )
    return {"item": db[item_id]}

# demo 8. Open API formalized status codes
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