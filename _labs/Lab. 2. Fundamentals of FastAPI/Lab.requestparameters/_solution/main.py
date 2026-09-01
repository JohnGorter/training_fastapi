from typing import Annotated
from fastapi import FastAPI, Query, Body, Header, Cookie, Form, UploadFile, File, Response
from pydantic import BaseModel, Field

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# - [POST] add users to a list of users using a form with firstname, lastname and password
# http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
@app.post("/users/add")
async def add_user(
    firstname: Annotated[str, Form()],
    lastname: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    return {"firstname": firstname, "lastname": lastname, "status": "added"}

# - [GET] get users with a query parameter that queries for a (part of a) name
# http localhost:8000/users/search name==john
@app.get("/users/search")
async def search_users(name: Annotated[str, Query(min_length=1, description="Search string")] = "John"):
    return {"name": name, "status": "found"}

# - [DELETE] delete users given his/her name in the querystring
# http DELETE localhost:8000/users/delete name==john
@app.delete("/users/delete")
async def delete_user(name: Annotated[str, Query(min_length=1, description="Name")]):
    return {"name": name, "status": "deleted"}

# - [POST] add profile photo to the user, given the username in the form that is POSTED
# http -f POST localhost:8000/users/profile/photo photo@main.py username=John
@app.post("/users/profile/photo")
async def add_profile_photo(
    username: Annotated[str, Form()],
    photo: Annotated[UploadFile, File(description="Profile photo")],
):
    return {"username": username, "photo_filename": photo.filename, "status": "added"}

# - [POST] let a user login using his firstname and password and setting a cookie on response
# http -f -v POST localhost:8000/users/login firstname=john password=test
@app.post("/users/login")
async def login_user(
    firstname: Annotated[str, Form()],
    password: Annotated[str, Form()],
    response: Response
):
    res = {"firstname": firstname, "status": "logged in"}
    # set a cookie on the response
    response.set_cookie(key="user", value=firstname, httponly=True)
    return res


# - [GET] get the user that is logged in using the cookie in the request
# http localhost:8000/users/me Cookie:user=mrGorter
@app.get("/users/me")
async def get_logged_in_user(user: Annotated[str, Cookie(description="username")]):
    return {"user": user, "status": "logged in"}