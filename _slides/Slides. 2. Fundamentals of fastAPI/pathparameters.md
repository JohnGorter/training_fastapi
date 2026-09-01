# Path Parameters

---
### Path Parameters

Declare them using the same syntax used by Python format strings:

```
@app.get("/items/{item_id}") # <- notice the curly braces here
async def read_item(item_id: int):  # <-- notice the type here 
    return {"item_id": item_id}
```

- in this case, item_id is declared to be an int
- with type declaration, FastAPI gives you automatic request "parsing"

http://127.0.0.1:8000/items/1, you will see a response of {"item_id":1}

---
### Data validation

If you go to the browser at http://127.0.0.1:8000/items/foo, there is an error:

```
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": [
        "path",
        "item_id"
      ],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "foo"
    }
  ]
}
```

---
### Documentation

When you open your browser at http://127.0.0.1:8000/docs, you will see an automatic, interactive, API documentation 

If you prefer Redoc:  http://127.0.0.1:8000/redoc


---
### Order matters
When creating path operations, you can find situations where you have a fixed path
let's say that it's to get data about the current user:
```
/users/me
``` 
and then you can also have a path to get data about a specific user by some user ID:
```
/users/{user_id} 
```

Path operations are evaluated in order! 
- make sure that the path for /users/me is declared before the one for /users/{user_id}

---
### Order mattters(2)
Similarly, you cannot redefine a path operation:

```
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
async def read_users():
    return ["Rick", "Morty"]

@app.get("/users")
async def read_users2():
    return ["Bean", "Elfo"]
```

The first one will always be used since the path matches first!

---
### Predefined values
You can use a standard Python Enum:

```
from enum import Enum
from fastapi import FastAPI

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

app = FastAPI()

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}
```

The interactive docs show them nicely!

---
### Return enumeration members

Return enum members from path operation, even nested in a JSON body (e.g. a dict)

```
from enum import Enum
from fastapi import FastAPI

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

app = FastAPI()

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}
```
In your client you will get a JSON response like
```
{
  "model_name": "alexnet",
  "message": "Deep Learning FTW!"
}
```

---
### Path parameters containing paths

Let's say you have a path operation with a path /files/{file_path}.

But you need file_path itself to contain a path,
```
home/johndoe/myfile.txt
```

So, the URL for that file would be 
```
/files/home/johndoe/myfile.txt
```

Now with default str, you get a 404 not found, of course!

---
### Use the Path convertor

Using an option directly from Starlette :
```
/files/{file_path:path}
```

- the name of the parameter is file_path
- the last part, :path should match any path

Example:
```
from fastapi import FastAPI
app = FastAPI()

@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
```

The URL would be: 
```
/files//home/johndoe/myfile.txt
```

Notice the double slash (//) between files and home

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Path Parameters

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Path Parameters
