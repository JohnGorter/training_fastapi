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