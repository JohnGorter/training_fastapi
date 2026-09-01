## Lab. PathParameters
In this lab you will make a set of API endpoints with arguments that actually resemble a real life implementation. This time we use path parameters to actually carry over data from the path to your code
> duration: 15 minutes

### Step 1. Create a new project in a working folder for your labs
Navigate to your lab folder and create a new project with uv, name it lab_pathparameters. 
Dont forget to add packages HTTPie, Pydantic and fastapi[standard] to your project using uv add. 
Make sure the project is created without package (--no-package) and the main.py is empty. 

These are the commands
```
uv init --no-package lab_pathparameters
uv add "fastapi[standard]"
uv add Pydantic
uv add HTTPie
```

*note: If you are in a vpn with restricted access, use the following command to skip the certification check:*
```
uv add --allow-insecure-host pypi.org --allow-insecure-host files.pythonhosted.org "fastapi[standard]"
uv add --allow-insecure-host pypi.org --allow-insecure-host files.pythonhosted.org Pydantic
uv add --allow-insecure-host pypi.org --allow-insecure-host files.pythonhosted.org HTTPie
```

### Step 2. Write the fastAPI boilerplate code
Open the main.py and write the boilerplate code to generate a fastAPI server. 

Here is the code:
```
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World!!"}
```

Try to run the server using
```
uv run fastapi dev
```

Let the server start and reload whenever you write code. 

### Step 3. Add user endpoints

Define async methods to:
- [GET] (users/{userid}) => get the user given its userid, it must be a string!
- [GET] (users/{userid}/profile/{photo}) where the photo parameter is the name of a file that should be returned to the client
- [GET] (users/me) => get and return response showing "current_user" as a response
Make sure the ordering is correct
- [GET] (currentenvironment) => get and return one of the values "PROD", "TEST", "DEV" as an Enum

### Step 3. Execute commands using HTTPie

Use HTTPie to test each individual API Call with the correct syntax.

Here are the HTTPie commands for you to test:
```
- http localhost:8000/users/me
- http localhost:8000/users/john
- http localhost:8000/users/john/profile//path/to/photo.jpg
- http localhost:8000/currentenvironment
```

Make sure they are all working correctly.

If you get errors and need inspiration, you can always peek at the solution file
<a href="../_solution/main.py"> here </a>

### Extra Exercise
Try to implement the business logic using regular Python syntax and utillities like in-memory dicts and lists. 

### Summary
We have defined and run multiple different API endpoints with different paths and options to have dynamic content!

Congrats!

-= End of lab =-
  
