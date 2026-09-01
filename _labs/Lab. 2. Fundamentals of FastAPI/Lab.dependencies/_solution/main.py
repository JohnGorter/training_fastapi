from typing import Annotated, Generator
from fastapi import FastAPI, Form, Request, Depends
import time 

# LogEnterAndExit is a dependency that logs the entry and exit of a request, along with the duration of the request.
def LogEnterAndExit(Request:Request) -> Generator[None, None, None]:
    start_time = time.perf_counter()
    print(f"Entering Request: {Request.method} {Request.url}")
    yield
    end_time = time.perf_counter() - start_time
    print(f"Exiting Request: {Request.method} {Request.url} duration: {end_time}")

# class LogToFile is a dependency that logs the request method and URL to a specified file.
class LogToFile:
    def __init__(self, filename:str):
        self.filename = filename

    async def __call__(self, request: Request):
        print(f"writing to {self.filename}, Request => {request.method} {request.url}")

# log is a dependency that logs the request method and URL to the console.
async def log(request: Request):
    print(f"Logging request...{request.method} {request.url}")

# instantiate the class to create an instance of LogToFile
log_to_file = LogToFile("log.txt")

# add global dependencies to the FastAPI app using the dependencies parameter
app = FastAPI(dependencies=[Depends(log_to_file), Depends(LogEnterAndExit)])

# - [POST] add users to a list of users using a form with firstname, lastname and password
# http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
@app.post("/users/add", dependencies=[Depends(log)])
async def add_user(user: Annotated[str, Form()]):
    return {"user":user, "status": "added"}