# Starlette internals

---
### Starlette internals

Is an ASGI implementation

FastAPI is based on Starlette

---
### Hello world Starlette
Let's recreate that simple hello world from the previous post using Starlette:

```
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

async def hello(request):
    return PlainTextResponse("Hello, World!")

app = Starlette(routes=[
    Route('/', hello),
])
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Starlette

---
### Earlier implementation

Remember this: 

```
class MyFramework:
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

app = MyFramework()
```

It looks very different but there are similarities
---
### Similarities

In both cases:
 - we have a class (MyFramework or Starlette)
 - we create an instance of this class and pass it to the ASGI server to deal with it

*According with ASGI's specification, an ASGI must expose a a single, asynchronous callable who receives a dictionary named scope and two other async callables named receive and send as parameters*

---
### Lets look at Starlette code
If we are passing a Starlette object to the ASGI server 
it MUST be a class that has a __call__ method implemented: 

@starlette/applications.py:

https://github.com/Kludex/starlette

```
async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    scope["app"] = self
    if self.middleware_stack is None:
        self.middleware_stack = self.build_middleware_stack()
    await self.middleware_stack(scope, receive, send)
```

*So we can see here that Starlette is a "callable" class, and apparently has a list of middlewares that will be executed each request*

---
### Middleware stack
What is a middleware_stack?

```
...
self.middleware_stack: ASGIApp | None = None
```

middleware_stack is an ASGIApp
- ASGIApp is just an ASGI callable:
    - ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]

So Starlette chains ASGIApps

---
### Lets look a little bit closer

If we take a look at Starlette.build_middleware_stack, we'll se a strange piece of code:

```
middleware = (
    [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
    + self.user_middleware
    + [
        Middleware(
            ExceptionMiddleware, handlers=exception_handlers, debug=debug
        )
    ]
)

app = self.router
for cls, args, kwargs in reversed(middleware):
    app = cls(app=app, *args, **kwargs)
return app
```

Starlette is creating sort of a chain of responsability of middlewares
- lastly our router / endpoint

Things will work like:
```
-> ServerErrorMiddleware
    -> Other Middlewares
        -> ExceptionMiddleware
            -> Router
```

---
### Explanation

Each ASGIApp will receive another ASGIApp as a dependency
Each one will call the next app when it gets called, till we reach ExceptionMiddleware
This will wrap our Router to deal with our exceptions

---
### The Router
The Router
- implements it's own app function (ASGI app) to match a route and execute path operation function:

```
async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
    # ... previous code

    for route in self.routes:
        # Determine if any route matches the incoming scope,
        # and hand over to the matching route if found.
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            scope.update(child_scope)
            await route.handle(scope, receive, send)
            return

    # ... code continues
```

--- 
### Lets use Starlette
Now we can create a simple middleware to log the request's path, and another one that logs that everything went ok after the response is sent:

```
class LogRequestMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        logging.info(f"-> received a request @ {scope['path']}")
        await self.app(scope, receive, send)

class LogResponseMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        await self.app(scope, receive, send)
        logging.info("-> wow, we did it")

async def hello(request):
    logging.info("Great news, we got a request!")
    return PlainTextResponse("Hello, World!")

app = Starlette(
    routes=[
        Route('/', hello),
    ],
    middleware=[
        Middleware(LogRequestMiddleware),
        Middleware(LogResponseMiddleware)
    ]
)
```

And we'll get:
```
INFO:root:-> received a request @ /
INFO:root:Great news, we got a request!
INFO:     127.0.0.1:51770 - "GET / HTTP/1.1" 200 OK
INFO:root:-> wow, we did it
```

---
### Routes and Router
And last but not least, after all the chain of middlewares, we'll get our Router beeing executed wrapped in an ExceptionMiddleware, so it can deal with our exceptions. Router will have a list of routes to deal with.

If the router finds a matching route, it will call the route's handle function. The handle function will call our endpoint, that is basically the function or class that you passed while creating the Starlette app:

app = Starlette(
    routes=[
        Route('/', hello), # -> hello is the function that will be handled by Router's handle
    ],
Infact, a Router is an ASGIApp too, and you can dismiss all Starlette's middlewares by creating only a Router:

app = Router(routes=[
    Route('/', hello)
])

---
### What about FastAPI?

FastAPI is Starlette
- it's a framework built on top of Starllete

if you go to FastAPI's source code, you'll find this:

```
class FastAPI(Starlette):

    def __init__(
    # ... code continues
```

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Starlette Middleware


---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Starlette