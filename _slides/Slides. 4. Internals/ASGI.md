# ASGI

---
### ASGI 

ASGI => Asynchronous Server Gateway Interface
WSGI => Web Server Gateway Interface

Specifications of server implementations

---
### Let's start from the beginning

What is FastAPI?
As the docs says:

*FastAPI is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints*

FastAPI => A web framework for building APIs.


---
### Starlette

FastAPI is a framework that was built on top of another framework: Starlette.

*Starlette is a lightweight ASGI framework/toolkit, which is ideal for building async web services in Python*

And what is ASGI?

---
### Now we are back at ASGI

ASGI is a specification that proposes an interface between web servers and applications

*When we are running our fastapi application, we're using an ASGI server that will forward the request to our app*

---
### Now we are back at ASGI
Some of the most well-known asgi servers are:
- Uvicorn
- Hypercorn
- Daphne

*FastAPI is a modern webframework written in python that is built on top Starlette, which in turn is a lightweight ASGI framework that needs an ASGI server to run*


---
### Let's create a basic ASGI application
Lets build a simple ASGI application:

```
async def app(scope, receive, send):
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            [b"content-type", b"text/plain"],
        ],
    })
    await send({
        "type": "http.response.body",
        "body": b"Hello, World!",
    })
```

FastAPI offers all middlewares and error handling, OpenAPI docs, etc. and starts from this

---
### ASGI 

And ASGI application:
- a single asynchronous callable that takes a dict and two asynchronous callables as parameters


---
### Run this appplication
First, install an ASGI server

with uv
```
uv add uvicorn
```
or use pip
```
pip install uvicorn
```

---
### Run this application (2)

Run uvicorn
```
uvicorn app:app
```

Now enter http://localhost:8000 in your browser:

```
INFO:     Started server process [4808]
INFO:     Waiting for application startup.
INFO:     ASGI 'lifespan' protocol appears unsupported.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:64045 - "GET / HTTP/1.1" 200 OK
```

---
### Creating the simplest FastAPI clone ever

Now that we know what's beneath FastAPI, lets create the smallest, simpler ASGI framework ever:

```

class SimplestFrameworkEver:
    async def __call__(self, scope, receive, send):
        await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            [b"content-type", b"text/plain"],
        ],

        })
        await send({
            "type": "http.response.body",
            "body": b"Hello, World!",
        })


app = SimplestFrameworkEver()
```

And you can still run it like before, with:

```
uvicorn app:app
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. ASGI

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
ASGI

