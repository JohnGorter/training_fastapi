# Request Parameters


---
### What are Request Parameters 

A special parameter in a function decorated by path operations that allows you to get data from a request

Request parameters are resolved by dependency injection!

---
### Example of a Request Parameter

The endpoint below has two query strings: skip and limit:

```
http://127.0.0.1:8000/items/?skip=0&limit=103
```

```
@app.get("/items/")
async def read_items(
        skip: int = Query(default=0, lt=0), 
        limit: int = Query(default=100, gt=100)):
```

As you can see
- the request parameters declared in a function are typed with Query object 
- the Query is instantiated with three parameters: default, gt and lt

---
### Simple Query Parameters 

There is no need for Query() when you only need a basic query parameter
There is no:
- extra validation
- default overrides
- OpenAPI metadata

Any function parameter that isn't part of the path and isn't a Pydantic model is automatically parsed as a query parameter!

```
@app.get("/items/")
async def read_items(q: str | None = None):
    return {"q": q}
```

---
### Path Parameters
Path parameters are a value attached to a URL path that identifies a specific resource or collection of resources in a server, such as a user identified by ID:

```
@app.get("/blog/{id}")
async def read_item(
    id: int = Path(gt=0, 
                   title="Blog ID", 
                   description="Blog resource identifier"),):
    return {"id": id}

https://example.com/blog/123. # /blog/123 is the path 123 is the path parameter
```

---
### Query Parameters

Query parameters, also known as query strings, are a value attached to the end of a URL followed by a question mark (?) 

```
class BlogOrder(str, Enum):
    age = "age"
    title = "title"
    created_at = "created_at"

@app.get("/blog/")
async def read_items(order_by: BlogOrder = Query(default=BlogOrder.created_at)):
    return {"order_by": order_by}

http://example.com/users/?page=2&sort=age # https://example.com is a base URL, /users/ is the path, page=2&sort=age are the query parameters
```

Example:
```
```
https://example.com: is a base URL.
/users/: is the path.
page=2&sort=age: are the query parameters to represent paging and sorting operations.
Query parameters serve various purposes, including SEO strategies.

Let's see an example:

FastAPI code

from fastapi import Query, FastAPI
from enum import Enum


app = FastAPI()


class BlogOrder(str, Enum):
    age = "age"
    title = "title"
    created_at = "created_at"


@app.get("/blog/")
async def read_items(order_by: BlogOrder = Query(default=BlogOrder.created_at)):
    return {"order_by": order_by}
Testing

curl -X 'GET' \
  'http://127.0.0.1:8000/blog/?order_by=title' \
  -H 'accept: application/json'
Header Parameters
Header parameters are values used to provide additional information between the client and server during an HTTP request and response transaction. An HTTP header consists of key-value pairs separated by colons (:).

Header parameters do not appear in the URL request as query or path parameters. They are generally processed or logged only by the server or client application.

The most common API request headers are: Accept, Authorization, Content Type, Cache Control, and User Agent.

Get Johni Douglas Marangon’s stories in your inbox
Join Medium for free to get updates from this writer.

Enter your email
Subscribe

Remember me for faster sign in

The code below is used to set a custom HTTP header used by the client to tell the server application which time zone the user is using.

Let’s see an example:

FastAPI code

from fastapi import FastAPI, Header


app = FastAPI()


REGEX_TZ = r"^GMT[+-]((0?[0-9]|1[0-1]):([0-5][0-9])|12:00)$"


@app.get("/blog/")
async def read_items(client_tz: str = Header(pattern=REGEX_TZ)):
    return {"Client-TZ": client_tz}
Testing

curl -X 'GET' \
  'http://127.0.0.1:8000/blog/' \
  -H 'accept: application/json' \
  -H 'client-tz: GMT+5:30'
Cookie Parameters
Cookies parameters (aka web cookie, HTTP cookies, or browser cookie) are a piece of data stored by a specific website in a browser and used to identify and improve your web browsing experience or used to send useful data to a server.

Cookies in general are used for general client-side storage like: session management (login, shopping card, or anything else), personalization (user preferences, and settings) or tracking (user behavior).

See an example on how to read a country value store in a cookie to customize API behavior.

Let’s see an example:

FastAPI code

from fastapi import Cookie, FastAPI

app = FastAPI()


@app.get("/blog/")
async def read_items(country: str = Cookie(default=None)):
    return {"Country": country}
Testing

Open the URL in a web browser and open the console (Ctrl + ) and execute the line below:

document.cookie='country=Brazil'
It isn't possible to use curl to test this feature because cookie is a browser-feature. Open the endpoint in a browser URL http://127.0.0.1:8000/blog/ and see the result using a cookie value.

Body Parameters
Body parameters, sometimes referred to as a payload, are used when the client needs to send data to a server to create or update resources, POST, PUT, or PATCH requests. The body of a request can be in a variety of formats, including JSON, XML, and plain text, the most commonly used is to send a JSON.

In the example below, you can see an endpoint that receives a body field called content in plain text format.

Let’s see an example:

FastAPI code

from fastapi import Body, FastAPI


app = FastAPI()

@app.post("/blog/")
async def read_items(content: str = Body(...)):
    return {"Content": content}
Testing

curl -X 'POST' \
  'http://127.0.0.1:8000/blog/' \
  -H 'accept: application/json' \
  -H 'Content-Type: text/plain' \
  -d 'Ireland is known for its wide expanses of lush, green fields.'
Form Parameters
Form parameters refer to data that is submitted through an HTML form and sent to a server using the HTTP POST or GET method. Using GET method is not secure or a recommended practice, especially for sensitive information like passwords.

The values are sent as key-value pairs, where the key corresponds to the name of the form field, and the value is the data entered by the user.

The Content-Type header in the HTTP request is set to application/x-www-form-urlencoded when form parameters are used or multipart/form-data when the form is used to upload files.

As you can see below, we are using a form to send an username and password to a server. A common approach to authenticating users.

Let’s see an example:

FastAPI code

from fastapi import Form, FastAPI


app = FastAPI()


@app.post("/blog/")
async def read_items(user: str = Form(...), password: str = Form(...)):
    return {"user": user, "password": password}
Testing

curl -X 'POST' \
  'http://127.0.0.1:8000/blog/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'user=admin&password=wewqe'
File Parameters
File parameters allow you to send a file as part of the request to a server. The content type of a request is multipart/form-data.

File uploads are one thing that is complicated to develop in an API. Fortunately in FastAPI this task is really easy.

Let see an example of how easy it is to do this in FastAPI:

FastAPI code

from fastapi import File, FastAPI, UploadFile
import uuid


app = FastAPI()


@app.post("/blog/")
async def read_items(photo: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}-{photo.filename}"

    with open(filename, "wb") as f:
        while contents := photo.file.read(1024 * 1024):
            f.write(contents)

    return {"Photo": filename}
Testing

curl -X 'POST' \
  'http://127.0.0.1:8000/blog/' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'photo=@screenshot.png;type=image/png'
Final thoughts
We have seen all the steps on how to send data to a server using request parameters in FastAPI. This is an important topic for using advanced features when building an API.

This is all for this article, hope you enjoy reading it.