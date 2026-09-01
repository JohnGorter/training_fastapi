# Demo 9. Routing

### step 1. Navigate to the main.py in the routing demo
Open the main.py in the routing demo and copy and paste this code into the file
```
from fastapi import FastAPI, APIRouter

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


# user endpoints
user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.get("/")
async def get_users():
    return {"message": "Get all users"}

# blog endpoints
blog_router = APIRouter(prefix="/blogs", tags=["blogs"])
@blog_router.get("/")
async def get_blogs():
    return {"message": "Get all blogs"}

app.include_router(user_router)
app.include_router(blog_router)
```

run the code using
```
uv run fastapi dev
```

open a new terminal in the root of the project and source the .venv
```
source .venv/bin/activate
```

Now run the following command to test the endpoints using routes
```
http localhost:8000/users/
http localhost:8000/blogs/
```

### step 2. Implement nested routing

Open main.py and copy in the following code

```
from fastapi import FastAPI, APIRouter

app = FastAPI()

@app.get("/")
async def root():
   return {"message": "Hello World"}


# user endpoints
user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.get("/")
async def get_users():
   return {"message": "Get all users"}

@user_router.get("/{user_id}")
async def get_user():
   return {"message": "Get a user"}

# blog endpoints
blog_router = APIRouter(prefix="/blogs", tags=["blogs"])

@blog_router.get("/")
async def get_blogs(user_id: int):
   return {"message": f"Get all blogs for user {user_id}"}

@blog_router.get("/{blog_id}")
async def get_blogs(user_id: int, blog_id: int):
   return {"message": f"Get blog {blog_id} for user {user_id}"}

app.include_router(user_router)
user_router.include_router(blog_router, prefix="/{user_id}", tags=["blogs"])

```

Save the file and now run the following commands from the client terminal
```
http localhost:8000/users/
http localhost:8000/users/4
http localhost:8000/users/4/blogs/
http localhost:8000/users/4/blogs/23
```

Explain the results

