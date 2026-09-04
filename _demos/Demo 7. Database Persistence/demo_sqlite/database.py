from contextlib import asynccontextmanager
import aiosqlite


async def connect():
    db = await aiosqlite.connect("./database.db")
    db.row_factory = aiosqlite.Row
    return db;

async def create(db):
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL
        )
    """)
    await db.commit()

async def disconnect(db):
    await db.close()