from fastapi import FastAPI, Response, status, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Generator, Union

app = FastAPI()

# demo 1. standard response filtering
# http POST localhost:8000/users/ id=1 username=john email=john@test.nl hashed_password=tetete
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

# demo 2. dynmic field exclusion
# http localhost:8000/telemetry/10
class PatientTelemetry(BaseModel):
    device_id: str
    heart_rate: int
    blood_oxygen: int | None = None
    alert_notes: str | None = None

@app.get("/telemetry/{device_id}", response_model=PatientTelemetry, response_model_exclude_none=True)
async def get_telemetry(device_id: str):
    # 'blood_oxygen' and 'alert_notes' are omitted from JSON payload because they evaluate to None
    return PatientTelemetry(device_id=device_id, heart_rate=72, blood_oxygen=None)


# demo 3. Union response models
# http localhost:8000/accounts/ent_123
# http localhost:8000/accounts/st 
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


# demo 4. explicit status code and dynamic response modification
# http -v POST localhost:8000/orders/
class OrderCreatedResponse(BaseModel):
    order_id: str
    total_amount: float

@app.post("/orders/", response_model=OrderCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_order(response: Response):
    # Mutate response metadata dynamically
    response.headers["X-Order-Tracking-UUID"] = "ord_trk_99021a"
    response.set_cookie(key="cart_session", value="cleared")
    return {"order_id": "ord_8820", "total_amount": 299.95}

