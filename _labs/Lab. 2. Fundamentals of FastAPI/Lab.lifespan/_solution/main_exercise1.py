from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    print("Server started")
    yield
    # Shutdown code here
    print("Server stopped")

app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}