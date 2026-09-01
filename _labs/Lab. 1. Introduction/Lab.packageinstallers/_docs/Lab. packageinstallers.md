## Lab 1. Basic Setup
In this lab you will install and create your first fastapi application
> duration: 30 minutes

### Step 1. Install uv package manager
Open a terminal to execute the following command: 
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Make sure the command executes succesfully. If it did, your installation was succesful.

Check the version of uv by issuing the following command: 
```
uv self version
```

Check to see if you have a correct output, anything greater than 0.12.3 is acceptable. 

### Step 2. Create a new project
Create a working directory named 'Labs" anywhere on your local file system if you not already have done so. Open a terminal into this directory and execute the following command: 
```
uv init Hello_FastAPI --no-package
```

If all went well, there should be a bunch of files in a subdirectory called 'Hello_FastAPI', one of them being main.py. 

Run the following command:
```
uv run main.py 
```

Notice that this step creates a .venv environment for this project and starts the code in the main.py file. If the result is "Hello from hello-fastapi!" then well done!

### Step 3. Make the project a FastAPI project
Add fastapi to the project by using uv as the package manager, executing the following code: 
```
uv add "fastapi[standard]"
```

Wait untill the installation has completed. 

Open the main.py file in the Hello-FastAPI folder and replace the code with the following  boilerplate hello world fast code:

```
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root(): 
  return "Hello world from FastAPI"

```

Save the file and when done, run the following command: 

```
uv run fastapi dev
```

If everything went well, fastapi should be up and running waiting for you to hit the endpoints at:
- http://127.0.0.1:8000        => for the api
- http://127.0.0.1:8000/docs   => for the openapi docs

Explore the running version of the application by using a browser to navigate to the endpoints, make sure everything works!

### Extra Exercise
There is no extra exercise in this lab

### Summary
We have installed and used uv package manager to create a new application for a bare minimum fastapi application. We have installed, implemented and run a first fastapi application. 

Congrats!

-= End of lab =-
  
