from datetime import UTC, datetime, timedelta
from time import timezone
from typing import Annotated

import jwt
from fastapi import FastAPI, Security, status, HTTPException
from pwdlib import PasswordHash
from typing import Dict
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from fastapi import Depends

app = FastAPI(title="johns api")

ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256" 

hashPassword = PasswordHash.recommended()
oauth2scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={"read": "Read access", "write": "Write access"})

async def generate_token(data:Dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(security_scopes: SecurityScopes = SecurityScopes(), token: str = Depends(oauth2scheme)):
    # Here you would normally decode the token and retrieve the user
    # For demonstration purposes, we'll just return a dummy user

    # test if the user has the required scopes
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    token_scopes = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM]).get("scopes", [])
    for scope in security_scopes.scopes:
        if scope not in token_scopes:  # Example check against allowed scopes
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough rights!!!",
            headers={"WWW-Authenticate": authenticate_value},
    )
    return {"username": "john"}

@app.get("/users/")
async def getUsers(user : Annotated[str, Security(get_current_user, scopes=["read"])]):
    return user   

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # Here you would normally verify the username and password
    # For demonstration purposes, we'll just return a dummy token
    user_permissions = ["read", "write"]  # Example permissions for the user
    granted_scopes = [scope for scope in form_data.scopes if scope in user_permissions]

    return {"access_token": await generate_token({"sub": form_data.username, "scopes": granted_scopes}), "token_type": "bearer"}