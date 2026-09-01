# Dependency Injection

---
### What is "Dependency Injection"

*"Dependency Injection" means that there is a way for your code (in this case, your path operation functions) to declare things that it requires to work and use: "dependencies"*

*And then, that system (in this case FastAPI) will take care of doing whatever is needed to provide your code with those needed dependencies ("inject" the dependencies)*

---
### What brings dependency injection

- shared logic (the same code logic again and again)
    - Share database connections
- Enforce security, authentication, role requirements, etc.

And what about testabiliy..... 


---
### A simple example
Let's see a very simple example. It will be so simple that it is not very useful, for now.

Here is an example of a dependency that can take all the same parameters that a path operation function can take:

```
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

# define the dependant
async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]): # declare the dependant
    return commons


@app.get("/users/")
async def read_users(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

The same shape and structure that all your path operation functions have

---
### A simple example (2)

In this case, this dependency expects:

An optional query parameter q that is a str.
An optional query parameter skip that is an int, and by default is 0.
An optional query parameter limit that is an int, and by default is 100.
And then it just returns a dict containing those values.

---
### Declare the dependency, in the "dependant"¶
The same way you use Body, Query, etc. with your path operation function parameters, use Depends with a new parameter:


```
from typing import Annotated

from fastapi import Depends, FastAPI

app = FastAPI()


async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]): 
    return commons


```

--
### Rules of the Depends

- you only give Depends a single parameter
    - this parameter must be something like a function
- you don't call it directly, you just pass it as a parameter to Depends()
    - that function takes parameters in the same way that path operation functions do

Whenever a new request arrives, FastAPI will take care of:
- calling your dependency ("dependable") function with the correct parameters
- get the result from your function
- assign that result to the parameter in your path operation function

*Notice that you don't have to create a special class and pass it somewhere to FastAPI to "register" it or anything similar*


---
### Share Annotated dependencies

When you need to use the common_parameters() dependency:
```
commons: Annotated[dict, Depends(common_parameters)]
```

Because we are using Annotated, we can store that Annotated value in a variable and use it in multiple places:

```
CommonsDep = Annotated[dict, Depends(common_parameters)]

@app.get("/items/")
async def read_items(commons: CommonsDep):
    return commons

@app.get("/users/")
async def read_users(commons: CommonsDep):
    return commons
```

*This is just standard Python, it's called a "type alias", it's actually not specific to FastAPI*


---
### To async or not to async

As dependencies are called the same as your path operation functions, the same rules apply 
- you can use async def or normal def

You can declare dependencies with async def inside of normal def path operation functions
or def dependencies inside of async def path operation functions, etc.

**It doesn't matter. FastAPI will know what to do!**


---
### Integrated with OpenAPI

All the request declarations, validations and requirements of your dependencies (and sub-dependencies) will be integrated in the same OpenAPI schema!


---
### Simple usage
If you look at it, path operation functions are declared to be used whenever a path and operation matches, and then FastAPI takes care of calling the function with the correct parameters, extracting the data from the request.

Actually, all (or most) of the web frameworks work in this same way.

You never call those functions directly. They are called by your framework (in this case, FastAPI).

With the Dependency Injection system, you can also tell FastAPI that your path operation function also "depends" on something else that should be executed before your path operation function, and FastAPI will take care of executing it and "injecting" the results.

Other common terms for this same idea of "dependency injection" are:

resources
providers
services
injectables
components
FastAPI plug-ins¶
Integrations and "plug-ins" can be built using the Dependency Injection system. But in fact, there is actually no need to create "plug-ins", as by using dependencies it's possible to declare an infinite number of integrations and interactions that become available to your path operation functions.

And dependencies can be created in a very simple and intuitive way that allows you to just import the Python packages you need, and integrate them with your API functions in a couple of lines of code, literally.

You will see examples of this in the next chapters, about relational and NoSQL databases, security, etc.

FastAPI compatibility¶
The simplicity of the dependency injection system makes FastAPI compatible with:

all the relational databases
NoSQL databases
external packages
external APIs
authentication and authorization systems
API usage monitoring systems
response data injection systems
etc.
Simple and Powerful¶
Although the hierarchical dependency injection system is very simple to define and use, it's still very powerful.

You can define dependencies that in turn can define dependencies themselves.

In the end, a hierarchical tree of dependencies is built, and the Dependency Injection system takes care of solving all these dependencies for you (and their sub-dependencies) and providing (injecting) the results at each step.

For example, let's say you have 4 API endpoints (path operations):

/items/public/
/items/private/
/users/{user_id}/activate
/items/pro/
then you could add different permission requirements for each of them just with dependencies and sub-dependencies:

current_user

active_user

admin_user

paying_user

/items/public/

/items/private/

/users/{user_id}/activate

/items/pro/

Integrated with OpenAPI¶
All these dependencies, while declaring their requirements, also add parameters, validations, etc. to your path operations.

FastAPI will take care of adding it all to the OpenAPI schema, so that it is shown in the interactive documentation systems.