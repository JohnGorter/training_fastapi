from fastapi import FastAPI, Depends, Query

app = FastAPI()

async def get_user(name:str = Query("johndoe", min_length=3, max_length=50)):
    return {"username": name}

class User:
    def __init__(self, name:str = Query("johndoe", min_length=3, max_length=50)):
        self.name = name

# @app.get("/")
# async def read_root(user: dict = Depends(get_user)):
#     return {"Hello": "World", "user": user}

@app.get("/")
async def read_root(user: User = Depends(User)):
    return {"Hello": "World", "user": user}

# note that user dict and user class are different, the first one is a dictionary and the second one is a class instance. The first one is returned by the get_user function and the second one is returned by the User class.
# but they both are serialised to JSON and returned to the client as a JSON object. The difference is that the first one is a dictionary and the second one is a class instance. The first one is returned by the get_user function and the second one is returned by the User class.