from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    print("Starting up...")
    app.state.something = "Initialized"
    yield
    # Shutdown code here
    print("Shutting down...")
    app.state.something = None

app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root(request:Request):
    return {"Hello": "World", "something": request.app.state.something}