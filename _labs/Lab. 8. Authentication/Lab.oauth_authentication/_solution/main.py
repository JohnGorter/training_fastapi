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
    async with app.state.db.execute("SELECT id, firstname, lastname FROM users WHERE id=?", [id]) as cursor:
        row = await cursor.fetchone()
        return UserOut(**row)
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/")
async def get_users() -> List[User]:
    users = []
    async with app.state.db.execute("SELECT id, firstname, lastname FROM users") as cursor:
        rows = await cursor.fetchall()
        for row in rows:
            users.append(User(**row))
    return users


@app.post("/users/")
async def post_users(user:User) -> UserOut:
    cursor = await app.state.db.execute("INSERT INTO users(firstname, lastname) VALUES (?, ?)", [user.firstname, user.lastname])
    await app.state.db.commit()
    return UserOut(**{"id" : cursor.lastrowid, "firstname" : user.firstname})