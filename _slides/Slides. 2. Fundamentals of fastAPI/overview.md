# Quick Overview

---
### Quick Overview

Lets look at the bare minimum:
```
from fastapi import FastAPI

app = FastAPI()


@app.get("/"). # <-- your first FastAPI endpoint 
async def root():
    return {"message": "Hello World"}

```
Run it:
```
uv run fastapi dev
```

---
### Overview (2)

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
That line shows the URL where your app is being served on your local machine.
``` 

If you visit that url, the following is the output:
```
{"message": "Hello World"}
```

---
### Tools for testing

To visit the API URL, you can use
- a normal webbrowser
- postman

But you can also use
- httpie text web client
- HTTPX sync/async web client package
- curl command line

---
### Tools for testing

Advantages of HTTPie over curl
- easier to use
- defaults to JSON encoding/decoding

example command line
```
http localhost:8000
```


---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. testing your first API using HTTPie


---
### Interactive API docs
For swaggerUI, visit:

```
http://127.0.0.1:8000/docs
```

For ReDoc, visit:
```
http://127.0.0.1:8000/redoc

```

---
### OpenAPI
FastAPI generates a "schema" with all your API using the OpenAPI standard for defining APIs

Schema
- an abstract description

API "schema"
- an abstract description of an API
- OpenAPI is a specification that dictates how to define a schema of your API

Data "schema"
- the shape of some data, like a JSON content
- the JSON attributes, and data types they have, etc

---
### OpenAPI and JSON Schema
OpenAPI defines an API schema for your API
- that schema includes definitions of the data sent and received using JSON Schema

Check the openapi.json at: 
```
http://127.0.0.1:8000/openapi.json
```

---
### What is OpenAPI for
The OpenAPI schema is used for:
- generate code automatically, for clients


---
### Configuration

You can configure where your app is located in a pyproject.toml file like:

```
[tool.fastapi]
entrypoint = "main:app"
```
That entrypoint will tell the fastapi command that it should import the app like:

```
from main import app
```

---
### Configuration (2)

If your code was structured like:

```
.
├── backend
│   ├── main.py
│   ├── __init__.py
```
Then you would set the entrypoint as:

```
[tool.fastapi]
entrypoint = "backend.main:app"
```

which would be equivalent to:
```
from backend.main import app
```


---
### Entrypoint argument

You can also pass the file path to the fastapi dev command
It will guess the FastAPI app object to use:

```
$ uv run fastapi dev main.py
```

---
### Entrypoint argument(2)

You can also pass the --entrypoint option to the fastapi dev command:

```
$ uv run fastapi dev --entrypoint main:app
```


Additionally, other tools might not be able to find it, for example the VS Code Extension or FastAPI Cloud, so it is recommended to use the entrypoint in pyproject.toml.

---
### Deploy your app

You can optionally deploy your FastAPI app to FastAPI Cloud with a single command:

```
uv run fastapi deploy

Deploying to FastAPI Cloud...

✅ Deployment successful!

🐔 Ready the chicken! Your app is ready at https://myapp.fastapicloud.dev
```


---
### Technical Details

FastAPI is a class that inherits directly from Starlette.
You can use all the Starlette functionality with FastAPI too.

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Install HTTPIE and test your endpoint(s)
