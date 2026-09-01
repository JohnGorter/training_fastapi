# FastApi's dependency injection internals
Exploring how FastAPI's dependency injection works under the hood

---
### Dependency Injection demystified

Here’s a simple example taken from FastApi’s Dependencies documentation.
```
async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

How is a type annotation able to execute a callable and inject arguments into the scope of a path function?

---
### The route decorator

Now, as we know, a decorator is a wrapper function that:
- takes another function as an argument, in this case the path function read_items
- performs some logic, if necessary
- returns the original function back

In this case, the logic that is performed is to create a new api route by calling fastapi/routing.py::APIRouter.add_api_route and append it to the routes of object
```
self.routes.append(route)
```

---
### Dependency discovery (at import time)

- dependencies are passed all the way down to the route class

```
class APIRoute(routing.Route):
    def __init__(
        self,
        path: str,
        ...
        dependencies: Optional[Sequence[params.Depends]] = None,
        ...
    )
```

Upon initialization of the router class, a loop over the dependencies occurs an assigns the dependency callables in the route object:

```
for depends in self.dependencies[::-1]:
    self.dependant.dependencies.insert(
        0,
        get_parameterless_sub_dependant(depends=depends, path=self.path_format),
    )
```

The logic is fairly complicated, but the key function I was looking for was the fastapi/dependencies/utils.py::get_typed_signature.

```
def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    signature = inspect.signature(call)
    globalns = getattr(call, "__globals__", {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=get_typed_annotation(param.annotation, globalns),
        )
        for param in signature.parameters.values()
    ]
    typed_signature = inspect.Signature(typed_params)
    return typed_signature
```

This is exactly the point where FastAPI is interpreting the type annotations from the signature of the read_items function, using Python’s standard inspect library



Bear in mind, however, that all this is happening at import time.. Thus, there was a final step to investigate.

---
### Where are the dependency callables actually executed?

this is happening at runtime in fastapi/routing.py::get_request_handler, presumably when a new request is made to the “/items/” endpoint:

Somewhere in there, the dependency callables that have already been assigned to the route object are executed (solve_dependencies) and their results are passed down to the read_items function as arguments (run_endpoint_function):

```
solved_result = await solve_dependencies(
    request=request,
    dependant=dependant,
    body=body,
    dependency_overrides_provider=dependency_overrides_provider,
    async_exit_stack=async_exit_stack,
    embed_body_fields=embed_body_fields,
)
errors = solved_result.errors
if not errors:
    raw_response = await run_endpoint_function(
        dependant=dependant,
        values=solved_result.values,
        is_coroutine=is_coroutine,
    )
```

---
### Getting rid of all the noise
Here is a simplified example to demonstrate how it works under the hood:

```
import functools
import inspect
from typing import Annotated, Any, Callable, Optional
from typing_extensions import Annotated, get_args


class Depends:
    def __init__(self, dependency: Callable[..., Any]):
        self.dependency = dependency


def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    """Returns the Signature of a callable"""
    return inspect.signature(call)


def analyze_param(param: inspect.Parameter) -> Depends:
    """Extracts the dependency object from the parameter annotation"""
    annotated_args = get_args(param.annotation)
    return [
        arg
        for arg in annotated_args[1:]
        if isinstance(arg, Depends)
    ][-1]


def solve_dependencies(dependency: Depends) -> Any:
    """Executes the dependency function"""
    return dependency.dependency()


def get(path):
    def api_route(func: Callable) -> Callable:
        @functools.wraps(func)
        def decorator(*args, **kwargs) -> Any:
            signature = get_typed_signature(func)

            dependency_kwargs = {}
            for param_name, param in signature.parameters.items():
                dependency = analyze_param(param)
                dependency_results = solve_dependencies(dependency)
                dependency_kwargs[param_name] = dependency_results

            kwargs.update(dependency_kwargs)

            return func(*args, **kwargs)
        return decorator
    return api_route


def common_parameters(q: Optional[str] = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


@get("/items/")
def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons


if __name__ == "__main__":
    print(read_items())
```

In a nutshell, it is just a decorator that uses the inspect library to extract the callable from the annotation.

If we execute the script above, we get the expected result.

```
{'q': None, 'skip': 0, 'limit': 100}
```

---
### Conclusion
The FastAPI dependency injection 
- relies on type annotations

The source code of FastAPI can be found in the fastapi github repo!

