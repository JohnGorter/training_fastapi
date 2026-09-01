from enum import Enum

from fastapi import FastAPI

app = FastAPI()


# - [GET] (users/me) => get and return response showing "current_user" as a response Make sure the ordering is correct
# http localhost:8000/users/me
@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}

# - [GET] (users/{userid}) => get the user given its userid, it must be a string!
# http localhost:8000/users/john
@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}

# - [GET] (users/{userid}/profile/{photo}) where the photo parameter is the name of a file that should be returned to the client
# http localhost:8000/users/john/profile//path/to/photo.jpg
@app.get("/users/{user_id}/profile/{photo:path}")
async def read_user_profile_photo(user_id: str, photo: str):
    return {"user_id": user_id, "photo": photo}

# - [GET] (currentenvironment) => get and return one of the values "PROD", "TEST", "DEV" as an Enum
# http localhost:8000/currentenvironment
class Environment(str, Enum):
    PROD = "PROD"
    TEST = "TEST"
    DEV = "DEV"

environment = Environment.DEV  # Set the current environment here

@app.get("/currentenvironment")
async def get_current_environment():
    return {"environment": environment}