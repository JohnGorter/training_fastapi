from typing import Annotated
from fastapi import FastAPI, Query, Body, Header, Cookie, Form, UploadFile, File, Response, status
from models import UserInput, UserResponse, UserResponseAction, UserProfilePhoto, UserProfilePhotoResult

app = FastAPI()


# - [POST] add users to a list of users using a form with firstname, lastname and password
# http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
@app.post("/users/add", status_code=status.HTTP_201_CREATED, response_model=UserResponseAction)
async def add_user(user: Annotated[UserInput, Form()]):
    return {**user.model_dump(), "status": "added"}

# - [GET] get users with a query parameter that queries for a (part of a) name
# http localhost:8000/users/search name==john
@app.get("/users/search", status_code=status.HTTP_200_OK, response_model=UserResponse)
async def search_users(name: Annotated[str, Query(min_length=1, description="Search string")] = "John"):
    return {"firstname": name, "lastname": "Gorter"} 


# - [POST] add profile photo to the user, given the username in the form that is POSTED
# http -f POST localhost:8000/users/profile/photo photo@main.py username=John
# http -f POST localhost:8000/users/profile/photo photo@main.jpg username=John
@app.post("/users/profile/photo", status_code=status.HTTP_201_CREATED, responses={400: {"description": "Invalid photo format"}}, response_model=UserProfilePhotoResult)
async def add_profile_photo(
    username: Annotated[str, Form()],
    photo: Annotated[UploadFile, File(description="Profile photo")], 
    response: Response
):
    user_profile_photo = UserProfilePhoto.validate({"username": username, "photo": photo})
    if (user_profile_photo.photo.content_type not in ["image/jpeg", "image/png"]):
        response.status_code=status.HTTP_400_BAD_REQUEST    
        return user_profile_photo.model_dump()
    return {**user_profile_photo.model_dump(), "filename": user_profile_photo.photo.filename}

