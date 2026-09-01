
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator
from fastapi import Form, UploadFile, File
from typing import Annotated, Generator, Union


class UserInput(BaseModel):
    firstname:str
    lastname: str
    password: str

class UserResponse(BaseModel):
    firstname:str
    lastname: str

class UserResponseAction(UserResponse):
    status: str

class UserProfilePhoto(BaseModel):
    username: str
    photo: UploadFile | None = None

class UserProfilePhotoResult(BaseModel):
    username: str
    filename: str | None = None


class ChangePassword(BaseModel):
    user: EmailStr
    password: str
    new_password: str
    repeat_new_password: str

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.new_password != self.repeat_new_password:
            raise ValueError("New password has to be the same as the repeat password")
        return self

class ChangePasswordResponse(BaseModel):
    user: EmailStr
    status: str
