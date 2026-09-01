## Lab HTTPIE
In this lab you will add the package HTTPie to your first demo project and use it to make requests
> duration: 15 minutes

### Step 1. Add HTTPie package
Navigate to your lab folder and make a new folder called helloworld

Open a terminal to execute the following command: 
```
uv init --no-package hello_fastapi
```

*note: If you are in a vpn with restricted access, use the following command to skip the certification check:*
```
uv add --allow-insecure-host pypi.org --allow-insecure-host files.pythonhosted.org "fastapi[standard]"
```

Open a terminal to execute the following command: 
```
uv add "fastapi[standard]"
uv add HTTPie
```

Make sure the command executes succesfully. If it did, your installation was succesful.

Copy in this code in main.py in your root folder
```
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World!!"}
```

Save the file

### Step 2. Use HTTPie

From a fresh terminal in the current working folder (root of the hello world project), issue the following command to start the fastAPI server
```
uv run fastAPI dev
```

Make sure it runs and wait for it to start. 

Inside another terminal, activate the virtual environment by using the command
```
source .venv/bin/activate
```

If the command executed succesfully, the prompt changes to reflect the change in environment. 

Test the HTTPie command by issuing the command
```
HTTPie
```

If you see the usage description of the HTTPie package, then it worked. 

### Step 3. Execute commands using HTTPie

In the terminal that has the virtual environment activated, issue the following command
```
http localhost:8000/
```

If all went wel, you see something similar to the following output, of course with different datetimes :D

```
HTTP/1.1 200 OK
content-length: 25
content-type: application/json
date: Sun, 30 Aug 2026 13:37:52 GMT
server: uvicorn

{
    "message": "Hello World"
}
```

Read the details here and ask questions when you dont understand the output. 

### Extra Exercise
With the knowledge gained, try to use curl to execute a request and compare the difference in usage

Also try the request package that is default available from Python using an interactive prompt.
Use this as inspiration:
```
>>> import requests
>>> r = requests.get("http://localhost:8000/")
>>> r.json()
{'message': 'Hello World'}
>>> 
```


### Summary
We have installed and tested the HTTPie package and executed a GET request to a boilerplate fastAPI project. 

Congrats!

-= End of lab =-
  
