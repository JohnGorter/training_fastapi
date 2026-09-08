from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from settings import settings

class Database:
    client: AsyncMongoClient | None = None
    db: AsyncDatabase |  None = None

db_context = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open async MongoDB client
    db_context.client = AsyncMongoClient(settings.mongodb_uri)
    db_context.db = db_context.client[settings.db_name]
    yield
    # Shutdown: Close client
    await db_context.client.close()