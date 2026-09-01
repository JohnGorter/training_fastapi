from enum import Enum

from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}") # <- notice the curly braces here
async def read_item(item_id: int):  # <-- notice the type here 
    return {"item_id": item_id}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}

# wrong order here, this will never be called because the previous path will match first
@app.get("users/me")
async def read_user_me():
    return {"user_id": "the current user"}

# check the documentation and see the enum shine!
class ModelName(str, Enum): # MRO Multuple Inheritance => Mtehod Resolution Order
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/files/{file_path:path}") # <- notice the :path here
async def read_file(file_path: str):
    return {"file_path": file_path}
