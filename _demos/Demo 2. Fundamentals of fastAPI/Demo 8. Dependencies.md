# Demo 8. Dependencies

### step 1. Create a new project
Create a new demo project and name it demo_dependencies. 
Be sure to add the packages fastapi[[standard]] and HTTPie.

### step 2. Demonstrate function based dependencies

Copy the following code into main.py, eplain the code and run the code
```
from fastapi import FastAPI, Depends, Query

app = FastAPI()

# notice the default value of the query parameter is set to "johndoe"
async def get_user(name:str = Query("johndoe", min_length=3, max_length=50)):
    return {"name": name}

@app.get("/")
async def read_root(user: dict = Depends(get_user)):
    return {"Hello": "World", "user": user["name"]}

```

Run the code and show that it works with:
```
http localhost:8000/ 
http localhost:8000/ name==test
```

### step 3. Demonstrate class based dependencies

Copy the following code into main.py,. explain the code and then run it

```
from fastapi import FastAPI, Depends, Query

app = FastAPI()


class User:
    def __init__(self, name:str = Query("johndoe", min_length=3, max_length=50)):
        self.name = name

@app.get("/")
async def read_root(user: User = Depends(User)):
    return {"Hello": "World", "user": user.name}

```
 
Run the code and show that it works with:
```
http localhost:8000/ 
http localhost:8000/ name==test
```
 
 You can also show that the User parameter to Depends is not necessary

### step 4. Demonstrate global dependencies

Copy the following code in main.py

```
from fastapi import FastAPI, Depends, Request

async def get_current_user(request:Request):
    # Simulate fetching the current user from a database or authentication system
    request.state.user = "johndoe"  # Store the user

app = FastAPI(dependencies=[Depends(get_current_user)])

@app.get("/")
async def root(request: Request):
    return {"message": "Hello World", "user": request.state.user}
```

Run the code and show and explain how it works

### step 5. Demonstrate class based dependencies

Copy the code in the snippet below and explain and run this code in the demo

```
from fastapi import FastAPI, Depends, Request, Query 
from typing import Annotated

app = FastAPI()

class SearchFilter:
    def __init__(
        self,
        q: Annotated[str | None, Query(description="Search string")] = None,
        category: Annotated[str | None, Query()] = None
    ):
        self.q = q
        self.category = category

@app.get("/products")
async def search_products(filters: Annotated[SearchFilter, Depends()]):
    return {"query": filters.q, "category": filters.category}

```

Run the code and show that it works with:
```
http localhost:8000/products q==test category==hardware
```

