from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import aiosqlite
from models import User, UserOut
from database import connect, disconnect, create
from typing import List


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await connect()
    await create(app.state.db)
    yield
    await disconnect(app.state.db)

app = FastAPI(lifespan=lifespan)

@app.get("/users/{id}")
async def get_user(id:int) -> UserOut:
    # 3. your code here
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/")
async def get_users() -> List[User]:
    users = []
    # 2. your code here
    return users


@app.post("/users/")
async def post_users(user:User) -> UserOut:
    cursor = # 1. your code here 
    await app.state.db.commit()
    return UserOut(**{"id" : cursor.lastrowid, "firstname" : user.firstname})