from fastapi import FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, Response, HTTPException, status
from typing import Annotated
import secrets

app = FastAPI()
security = HTTPBasic()

@app.get("/")
async def read_root(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    if (credentials.username != "admin" or credentials.password != "secret"):
        response.status_code = 401
        response.headers["WWW-Authenticate"] = 'Basic realm="My Realm"'
        return
    return credentials

def authenticate_admin(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_user = secrets.compare_digest(credentials.username, "admin")
    correct_pass = secrets.compare_digest(credentials.password, "secret123")
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/admin/system-status")
async def get_system_status(user: Annotated[str, Depends(authenticate_admin)]):
    return {"status": "ok", "authenticated_as": user}