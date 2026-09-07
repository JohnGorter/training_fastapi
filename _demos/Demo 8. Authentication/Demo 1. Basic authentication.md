# Demo 1. Basic Authentication

### step 1. Open the main.py file in the demo folder

Open the main.py in the routing demo and copy and paste this code into the file
```
from fastapi import FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, Response, HTTPException, status
from typing import Annotated
import secrets

app = FastAPI()
security = HTTPBasic()

@app.get("/")
async def read_root(response: Response, credentials: HTTPBasicCredentials = Depends(security)):
    if (credentials.username != "admin" or credentials.password != "secret"):
        response.status_code = 401
        response.headers["WWW-Authenticate"] = 'Basic realm="My Realm"'
        return
    return credentials
```

Explain this non dependency version of the basic authentication demo. Also explain the text comparison that is done and the potential hack.

run the code using
```
uv run fastapi dev
```

open chrome and navigate to the docs
```
http://localhost:8000/docs
```

Show the login that pops up when you try to execute the endpoint

### Step 2. Use a security dependency

Open the main.py and paste in the following code: 
```
from fastapi import FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, Response, HTTPException, status
from typing import Annotated
import secrets

app = FastAPI()
security = HTTPBasic()

def authenticate_admin(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_user = secrets.compare_digest(credentials.username, "admin")
    correct_pass = secrets.compare_digest(credentials.password, "secret123")
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/admin/system-status")
async def get_system_status(user: Annotated[str, Depends(authenticate_admin)]):
    return {"status": "ok", "authenticated_as": user}
```

Explain the secrets.compare_digest/ 

run the code using
```
uv run fastapi dev
```

open chrome and navigate to the docs
```
http://localhost:8000/docs
```

Show the login that pops up when you try to execute the endpoint


-= End of Demo =-
