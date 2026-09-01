


class MyFramework:
    """
    This class represents a minimalistic web framework that adheres to the ASGI (Asynchronous Server Gateway Interface) specification. It is designed to handle HTTP requests and responses in an asynchronous manner, allowing for high concurrency and efficient resource usage.
    """
    async def __call__(self, scope, receive, send):
        
        """
        This signature defines a standard ASGI (Asynchronous Server Gateway Interface) application in Python, the low-level standard used by modern web frameworks like FastAPI, Starlette, and Django Channels.
        Core Parameters
        async def app(...): Declares the main callable as an asynchronous coroutine, allowing the web server to handle thousands of concurrent requests without blocking execution.
        scope: A Python dict containing metadata about the incoming connection. It holds information such as the connection type ("http" or "websocket"), HTTP method, URL path, headers, client IP address, and query string.
        receive: An awaitable async function used to fetch incoming event messages from the server (e.g., reading chunks of an incoming HTTP request body or incoming WebSocket messages).
        send: An awaitable async function used to send outgoing event messages back to the client (e.g., transmitting HTTP status codes, headers, and response body chunks).
        Minimal Working Example
        When an ASGI server like Uvicorn or Hypercorn accepts a connection, it prepares the connection context (scope) and provides two channel functions (receive and send) directly to this entry point to drive the request-response lifecycle.
        """
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", b"text/plain"],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b"Hello, world!!",
        })


app = MyFramework()



