# FastAPI internals

---
### How FastAPI extends Starlette

Two main sources of information:
- FastAPI's source code (https://github.com/fastapi/fastapi)
- FastAPI's documentation

---
### FastAPI class
FastAPI's first entrypoint is FastAPI class => fastapi/applications.py

We can expect that FastAPI is a callable that receives scope, receive and send, like any other ASGI app:

```
async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if self.root_path:
        scope["root_path"] = self.root_path
    await super().__call__(scope, receive, send)
```

FastAPI has 
 - __call__ function 
 - delegates the request to Starlette

--- 
### Difference

FastAPI extends Starlette but adds some functionality during initialization

Look at FastAPI's __init__ function:
- it add routes to OpenAPI docs on setup function
- it sets the Router to APIRouter => this is where all your path operations live!

*Setup function will add one of the coolest features of FastAPI: It will add a free OpenAPI documentation to our project with Swagger and Redoc*

---
### How do requests work

In the previous slides, we talked about how a request are handled in Starlette

Chain of middlewares will be something like:
```
-> ServerErrorMiddleware
    -> Other Middlewares
        -> ExceptionMiddleware
            -> Router
```

FastAPI overrides Starlette's Router with it's own APIRouter

*FastAPI prefers to handle the requests its own way*

---
### How do requests work (2)

So with FastAPI:

```
-> FastAPI App
  -> Starlette's App
    -> Starlette's ServerErrorMiddleware
      -> Starlette's ExceptionMiddleware
        -> FastAPI's APIRouter (and Router, since it don't override Router's __call__)
```

---
### FastAPI routers and routes

There are two main ways to add a route:
- directly with FastAPI's instance:

```
app = FastAPI()

@app.get("/{name}")
async def hi(name: str):
    return {"hi": name}
```

- using APIRouter:

```
app = FastAPI()
router = APIRouter(prefix="/v1")

@router.get("/compliments/{name}")
async def hi1(name: str):
    return {"hi": name}

app.include_router(router)
```

---
### Decorator app verbs
Lets see what is happening when we use @app.{verb}:
```
    def get(
        self,
        path: Annotated[
            str,
            Doc("... # docs here"),
        ],
        *,
        ... # other args here
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.router.get(
            path,
            ... # code continues
        )
```

FastAPI.{get,put,post,etc} are simply decorators that will include the path to APIRouter

---
### What about FastAPI.include_router?

FastAPI's function include_router will simply call it's own APIRouter's include_router,

Basically iterates through all routes included in APIRouter and add the route

```
    # FastAPI include_router

    def include_router(
        self,
        router: Annotated[routing.APIRouter, Doc("The `APIRouter` to include.")],
        *,
        ... # other args
    ) -> None:
        self.router.include_router(
            router,
            ... # other args
        )

    # APIRouter include_router

    def include_router(
        self,
        router: Annotated["APIRouter", Doc("The `APIRouter` to include.")],
        ... # other args
    ) -> None:
        for route in router.routes:
            if isinstance(route, APIRoute):
                ... # some logic here

                self.add_api_route(
                    prefix + route.path,
                    route.endpoint,
                    ... # other args
                )
```

*Looking at APIRouter.include_router we can see that it handles other type of routes, like Starlette's routes, APIWebSocketRoute, etc*

---
### When are route function called?

When we receive a request, Starlette's Router will be called if it finds a matching route
- APIRouter don't override __call__ remember

Handle belongs to Route too, since it is not overwritten as well. 

What APIRoute does is setting Route's app to Starlette's function request_response, receiving APIRoute's get_route_handler as a parameter.
```
class APIRoute(routing.Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        ... # other args
    ) -> None:
        ... # some logic here
        self.app = request_response(self.get_route_handler())
```

---
### What is this request_response function?

In starlette.routing, the request_response function is an internal adapter that converts a high-level Python function (a endpoint handler taking a Request and returning a Response) into a low-level, standard ASGI application.

Primary Responsibilities
- ASGI Conversion: Transforms functions matching the endpoint signature func(request) -> response into an - ASGI callable matching async def app(scope, receive, send).

--
### Simplified Implementation

```
def request_response(
    func: Callable[[Request], Awaitable[Response] | Response],
) -> ASGIApp:
    # 1. Wrap synchronous handlers in run_in_threadpool
    f = func if is_async_callable(func) else functools.partial(run_in_threadpool, func)

    # 2. Return a standard ASGI app interface
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        response = await f(request)
        await response(scope, receive, send)

    return app
```

---
### Common Framework Usage

Starlette Route Instantiation: 
- When initializing a route like Route("/path", endpoint=my_func), Starlette calls self.app = request_response(endpoint) to turn the python function into a runnable ASGI app

FastAPI Endpoint Wrapper:
- FastAPI extends/overrides Starlette's request_response implementation in fastapi.routing 
- attaches dependency injection, parameter parsing, response validation, and AsyncExitStack resource management before running the route function

---
### So to summerize the code earlier

- get_route_handler returns the get_request_handler function
- here starts the "translation" of Starlette's request to a FastAPI route with dependants, pydantic models, etc.

Then it will run the run_endpoint_function function. And here is where our route function is being called with all the resolved dependencies, pydantic models, etc.

```
def get_request_handler(
    ... # args
) -> Callable[[Request], Coroutine[Any, Any, Response]]:
    # logic here

    async def app(request: Request) -> Response:
        response: Union[Response, None] = None
        async with AsyncExitStack() as file_stack:
            # logic here
            errors: List[Any] = []
            async with AsyncExitStack() as async_exit_stack:
                # logic here
                if not errors:
                    raw_response = await run_endpoint_function(
                        dependant=dependant, values=values, is_coroutine=is_coroutine
```
                    )
Pretty cool the see how the framework you are using handles your code right?

---
<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. FastAPI

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
FastAPI