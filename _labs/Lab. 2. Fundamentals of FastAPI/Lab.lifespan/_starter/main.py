from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

# your code here

app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}