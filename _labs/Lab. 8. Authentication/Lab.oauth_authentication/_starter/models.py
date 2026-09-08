from pydantic import BaseModel

class UserOut(BaseModel):
    id:int 
    firstname:str

class User(BaseModel):
    id:int | None = None
    firstname:str
    lastname:str 