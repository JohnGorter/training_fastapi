from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes

# Tells Swagger UI where to redirect users for authorization and where to exchange codes
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="/authorize",
    tokenUrl="/token",
    scopes={"read:profile": "Read user profile", "write:orders": "Create orders"})


async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    # Here you would validate the token and extract user information
    # For demonstration, we will just return a mock user
    if token == "valid_token":
        return {"username": "johndoe", "scopes": security_scopes.scopes}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
app = FastAPI()
@app.get("/users/me")
async def read_users_me(current_user: Annotated[dict, Security(get_current_user, scopes=["read:profile"])]):
    # Here you would validate the token and extract user information
    return {"current_user": current_user}