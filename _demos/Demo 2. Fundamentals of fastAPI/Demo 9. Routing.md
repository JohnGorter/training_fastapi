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
