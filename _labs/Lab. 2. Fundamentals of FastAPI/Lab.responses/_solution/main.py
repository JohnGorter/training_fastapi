from typing import Annotated
from fastapi import FastAPI, Query, Body, Header, Cookie, Form, UploadFile, File, Response, status


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# - [POST] add users to a list of users using a form with firstname, lastname and password
# http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
@app.post("/users/add", status_code=status.HTTP_201_CREATED)
async def add_user(
    firstname: Annotated[str, Form()],
    lastname: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    return {"firstname": firstname, "lastname": lastname, "status": "added"}

# - [GET] get users with a query parameter that queries for a (part of a) name
# http localhost:8000/users/search name==john
@app.get("/users/search", status_code=status.HTTP_200_OK)
async def search_users(name: Annotated[str, Query(min_length=1, description="Search string")] = "John"):
    return {"name": name, "status": "found"}

# - [DELETE] delete users given his/her name in the querystring
# http DELETE localhost:8000/users/delete name==john
# http DELETE localhost:8000/users/delete name==nobody
@app.delete("/users/delete", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"description": "User not found"}})
async def delete_user(name: Annotated[str, Query(min_length=1, description="Name")], response: Response):
    if (name == "nobody"):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"name": name, "status": "not found"}
    return {"name": name, "status": "deleted"}

# - [POST] add profile photo to the user, given the username in the form that is POSTED
# http -f POST localhost:8000/users/profile/photo photo@main.py username=John
# http -f POST localhost:8000/users/profile/photo photo@main.jpg username=John
@app.post("/users/profile/photo", status_code=status.HTTP_201_CREATED, responses={400: {"description": "Invalid photo format"}})
async def add_profile_photo(
    username: Annotated[str, Form()],
    photo: Annotated[UploadFile, File(description="Profile photo")], 
    response: Response
):
    if (photo.content_type not in ["image/jpeg", "image/png"]):
        response.status_code=status.HTTP_400_BAD_REQUEST    
        return {"status": "invalid photo format"}
    return {"username": username, "photo_filename": photo.filename, "status": "added"}

# - [POST] let a user login using his firstname and password and setting a cookie on response
# http -f -v POST localhost:8000/users/login firstname=john password=test
@app.post("/users/login", status_code=status.HTTP_200_OK)
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
# http localhost:8000/users/me 
@app.get("/users/me", status_code=status.HTTP_200_OK, responses={401: {"description": "User not logged in"}})
async def get_logged_in_user(response: Response, user: Annotated[str | None, Cookie(description="username")] = None):
    if (user is None):
        response.status_code=status.HTTP_401_UNAUTHORIZED
        return {"status": "not logged in"}
    return {"user": user, "status": "logged in"}