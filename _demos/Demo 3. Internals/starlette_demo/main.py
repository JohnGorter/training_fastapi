from starlette.routing import Route
from starlette.responses import PlainTextResponse
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class LogRequest(BaseHTTPMiddleware): 

    async def dispatch(self, request, call_next):
        print(f"Request: {request.scope['method']} {request.scope['path']}")
        return await call_next(request)

class LogResponse(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        print(f"Response: {request.scope['method']} {request.scope['path']}")
        return response


async def HelloWorld(request):
    return PlainTextResponse('Hello, World!')

app = Starlette(routes=[
        Route('/', HelloWorld),
    ], middleware=[
        Middleware(LogRequest),
        Middleware(LogResponse)
    ])
