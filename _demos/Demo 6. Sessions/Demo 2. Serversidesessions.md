# Demo 1. Sessions

### step 1. create project
Create a new project with uv --no-package 
Make sure to add fastapi[standard] packages to the project. 


### step 2. copy the following code
Open ./main.py in the project folder and add the following code:
```
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Add the session middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

@app.post("/login")
async def login(request: Request):
    # Write to session (stored in the signed cookie)
    request.session["user_id"] = 42
    return {"message": "Logged in"}

@app.get("/profile")
async def profile(request: Request):
    # Read from session
    user_id = request.session.get("user_id")
    if not user_id:
        return {"error": "Not authenticated"}, 401
    return {"user_id": user_id}

@app.post("/logout")
async def logout(request: Request):
    # Clear session
    request.session.clear()
    return {"message": "Logged out"}
```

run this code using the command
```
uv run ./main.py
```
and explain the details the code

navigate to the docs
```
http://localhost:8000/docs
```

Run the login, profile logout profile endpoints and show the details in the request and response..

You can also use the following httpie commands: 
```
http -v post localhost:8000/login
http -v localhost:8000/profile   
http -v localhost:8000/profile Cookie:session=eyJ1c2VyX2lkIjogNDJ9.ap_axA.YKBqBiQbhs1YUglYFlZhWDLkoDs
http -v post localhost:8000/logout
```


-= end of demo =-