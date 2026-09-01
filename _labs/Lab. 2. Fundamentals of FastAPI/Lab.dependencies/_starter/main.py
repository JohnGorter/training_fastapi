from typing import Annotated
from fastapi import FastAPI, Form

app = FastAPI()

# - [POST] add users to a list of users using a form with firstname, lastname and password
# http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
@app.post("/users/add")
async def add_user(user: Annotated[str, Form()]):
    return {"user":user, "status": "added"}