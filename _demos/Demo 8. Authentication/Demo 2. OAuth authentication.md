# Demo 2. OAuth Authentication

### step 1. Navigate to the main.py in the oath authentication demo

In this demo you are going to show how to implement the basic OAuth flow. Even though it is a password grant flow, it is still the way to work in fastAPI.

Open the main.py in the oauth authentication demo and copy and paste this code into the file:
```
from datetime import UTC, datetime, timedelta
from time import timezone
from typing import Annotated

import jwt
from fastapi import FastAPI
from pwdlib import PasswordHash
from typing import Dict
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends

app = FastAPI(title="johns api")

ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256" 

hashPassword = PasswordHash.recommended()
oauth2scheme = OAuth2PasswordBearer(tokenUrl="token")

async def generate_token(data:Dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2scheme)):
    # Here you would normally decode the token and retrieve the user
    # For demonstration purposes, we'll just return a dummy user
    return {"username": "john"}

@app.get("/users/")
async def getUsers(user = Depends(get_current_user)):
    return user   

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # Here you would normally verify the username and password
    # For demonstration purposes, we'll just return a dummy token
    return {"access_token": await generate_token({"sub": form_data.username}), "token_type": "bearer"}
```

run the code using
```
uv run fastapi dev
```

open a chrome and go to the docs:
```
http://localhost:8000/docs
```

From the docs, call the api that is available also show the lock icon in the /users/ endpoint and login with fake data and see that
authentication works


### step 2. Implement scopes

In this demo we are going to look at scopes, which effectively add groupings of permissions a user can grant upon loggin in and creating a token. 
the token holds all the granted scopes and upon accessing an enpoint, we can validate if the scope needed is in the JWT. 

4 steps to point out: 
- scheme defines the scopes that are possible to grand (for the form to show)
- endpoint defines the required scopes, only the ones needed are clickable in the form
- upon submission of the form, serialize the granted scopes to the token using scopes as a name
- upon the get_current_user, we have to check if the required scope is in the list of granted scopes 

Open main.py and copy in the following code

```
ffrom datetime import UTC, datetime, timedelta
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
```

Save the file and go to the docs, show these two scenarios

- first, login to the /users/ endpoint and dont grant the scope permission, show the token in jwt.ms
- try to execute the enpoint, see the result fail.
- logout and now do give permission to the scope and show the token in jwt.ms
- execute the endpoint and see that it works!

Explain the results

### step 3. Implement routing the correct way

Copy over this code and explain the differences

- in the main.py file
```
from fastapi import FastAPI
from blogs import blog_router
from users import user_router

app = FastAPI()

app.include_router(user_router)
app.include_router(blog_router)
```

- in the user.py file
```
from fastapi import APIRouter
from typing import List

user_router = APIRouter(prefix="/users")

@user_router.get("/")
async def return_users() -> List[str]:
   return ["user1", "user2"]

@user_router.get("/{user_id}")
async def return_user(user_id:int) -> str:
   return "user1"
```

- in the blog.py file
```
from fastapi import APIRouter
from typing import List

_blog_router      = APIRouter(prefix="/blogs")
_blog_user_router = APIRouter(prefix="/users/{user_id}/blogs")
blog_router       = APIRouter()

blog_router.include_router(_blog_router)
blog_router.include_router(_blog_user_router)

async def return_one_blog(blogid:int, userid:int | None = None):
   return f"returning blog {blogid} for user {userid}" if userid else f"returning blogs {blogid}!"
   
async def return_all_blogs(userid:int | None = None):
   return f"returning all blogs for user {userid}" if userid else "returning all blogs!"


@_blog_router.get("/")
async def return_blogs() -> str:
   return await return_all_blogs()

@_blog_router.get("/{blog_id}")
async def return_blog(blog_id:int) -> str:
   return await return_one_blog(blog_id)


@_blog_user_router.get("/")
async def return_user_blogs(user_id:int) -> str:
   return await return_all_blogs(user_id)

@_blog_user_router.get("/{blog_id}")
async def return_user_blog(user_id:int, blog_id:int) -> str:
   return await return_one_blog(blog_id, user_id)

```

explain the best practices here:
- isolated modules
- little code reuse
- OpenAPI documentation is correct (no userid parameters mentions in the openAPI docs)

-= End of Demo =-
