## Lab Dependencies
In this lab you try out dependencies for a variety of use cases. We can use dependencies to validate request but also to inject caching, database access, logging etc etc.
> duration: 30 minutes

### Step 1. Copy over the previous exercise 
Navigate to your lab folder and create a new project with uv, name it lab_dependencies.
Dont forget to add packages HTTPie, Pydantic and fastapi[standard] to your project using uv add. 
Make sure the project is created without package (--no-package) and the main.py is empty. 

These are the commands
```
uv init --no-package lab_requestparameters
uv add "fastapi[standard]"
uv add Pydantic
uv add HTTPie
```

Make sure that all dependencies are installed correctly.

Copy over the main.py from the _starter folder in this lab into the root of this project, effetively replacing the existing main.py file.

You should be able to read the code understand it. There is only one enpoint!

Try to test it out using the command
```
http --form POST localhost:8000/users/add user=john  
```

This should work perfectly.

### Step 2. Implement logging dependency

Open the file ./main.py and add add a function based dependency for the "/users/add" API endpoint
that outputs the request as logging to the terminal.

The logging function should look like this
```
async def log(request: Request):
    print(f"Logging request...{request.method} {request.url}")
```

Connect this function as a decorator dependency to the API endpoint. 

Here is the code:
```
@app.post("/users/add", dependencies=[Depends(log)])
```

If you are done, run the project using
```
uv run fastapi dev
```

Test the code using the following command
```
http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
```

Did it work?

**Note: You have to inspect the server logs, not the client terminal that executes the HTTPie command**

### Step 3. Implement class based callable dependency 

In the main.py file, create a class that has the __init__ and the __call__ methods. 

Create the class so you can provide a filename on construction and implement the call
that does the logging to the configured file. 

For testing purposes, you dont have to write to the actual file but print the intention to the terminal. 

The output could be someting like: 
```
writing to log.txt, request => POST http://localhost:8000/users/add
```

Instantiate the class and register the dependency in the global app dependencies.

Here is the code for inspiration:
```
# class LogToFile is a dependency that logs the request method and URL to a specified file.
class LogToFile:
    def __init__(self, filename:str):
        self.filename = filename

    async def __call__(self, request: Request):
        print(f"writing to {self.filename}, Request => {request.method} {request.url}")

# instantiate the class to create an instance of LogToFile
log_to_file = LogToFile("log.txt")

# add global dependencies to the FastAPI app using the dependencies parameter
app = FastAPI(dependencies=[Depends(log_to_file)])
```

If you are done, run the project if you did not do that already, using
```
uv run fastapi dev
```

Test the code using the following command
```
http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
```

Did it work? Check the server output to see the result!

### Extra Exercise
Try to implement a yield dependency that logs the entry and the exit of each request in a global dependency. 

It should also record the duration of the request and log that to the terminal as well. 

If you dont know the code to do timings, it is simple, here is the complete code for the yield dependency for inspiration:

```
def LogEnterAndExit(Request:Request) -> Generator[None, None, None]:
    start_time = time.perf_counter()
    print(f"Entering Request: {Request.method} {Request.url}")
    yield
    end_time = time.perf_counter() - start_time
    print(f"Exiting Request: {Request.method} {Request.url} duration: {end_time}")
```

Hook up this function as a global dependency to the fastAPI app as before, a.k.a add it to the list.

Test the code using the following command
```
http --form POST localhost:8000/users/add firstname=john lastname=gorter password=jojo
```

Check the server logs to see the ouput of the logs.

### Summary
We have experimented with dependencies on different levels of the application. You are now a dependency master!

Congrats!

-= End of lab =-
  
