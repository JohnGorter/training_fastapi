# Demo 11. Lifespan

### step 1. Open the project

Open the project demo_lifespan and open main.py

Copy over the following code: 
```
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
```

Explain how the ligespan function is a generator function, because of the yield.
also explain that this generate can be used as a contextmanager, everything before the 
yield is done at the start, after the yield is in the stopping state of the server shutdown. 

Also explain the way to add data to the app.state and how to get it from the request, which is
better then getting it from the global variable!


