# Server Sent Events

---
### Server-Sent Events (SSE) 

Server sent events provide a lightweight, unidirectional HTTP streaming standard (text/event-stream) for pushing real-time updates from server to client over a single long-lived TCP connection

---
### Theoretical Background

Real-Time Communication in SSE works entirely over standard HTTP/1.1 or HTTP/2

- the client initiates an event listener using the browser's native EventSource API
- the server keeps the connection open indefinitely to push UTF-8 encoded text streams

---
### Theoretical Background

| Feature|Short Polling|Long Polling|WebSockets|Server-Sent Events (SSE)|
|----|----|----|----|----|
|Direction|Client -> Server|Client -> Server|Bidirectional (<-->)|Unidirectional (Server -> Client)|
|Protocol|Standard HTTP|Standard HTTP|WS / WSS (Custom TCP)|Standard HTTP (text/event-stream)|
|Connection|Repeated short requests|Held open until data arrives|Single persistent connection|Single persistent HTTP connection|
|Overhead|High (HTTP headers per request)|Medium (re-established often)|Very Low (after handshake)|Low (uses native HTTP multiplexing)|
|Auto-Reconnect|Manual (Application logic)|Manual (Application logic)|Manual (Requires JS library)|Native browser automatic retry|
|Firewall/Proxy|Seamless|Seamless|Requires WS proxy support|Seamless (Standard HTTP/2 friendly)|


---
### SSE Protocol Data Specification

An SSE stream is a continuous plain-text stream formatted with key-value pairs separated by colons (:), terminated by a double newline (\n\n)

- data: <content> — The message payload (can span multiple lines)
- event: <name> — Custom event type name (defaults to message if omitted)
- id: <value> — Unique event identifier used for stream tracking
- retry: <milliseconds> — Instructs the browser how long to wait before attempting reconnection after a drop
- : <comment> — Lines starting with a colon are ignored by EventSource (commonly used as keep-alive heartbeats to prevent proxy timeouts)

---
### SSE Protocol Data Specification

```
event: price_update
id: 10045
retry: 5000
data: {"sku": "GPU-4090", "price": 1599.99}

: heartbeat ping (prevents proxy timeout)
```

---
### State Recovery via Last-Event-ID

- When an SSE connection drops (due to network failure or server restarts), the browser's native EventSource automatically attempts reconnection

- Upon reconnecting, the client automatically attaches the Last-Event-ID HTTP header containing the last received id: value, allowing the server to replay missed events from an event log 

---
### Basic Unidirectional Streaming in fastAPI

In FastAPI, SSE streams are implemented by returning an async generator wrapped inside a StreamingResponse configured with media_type="text/event-stream"

Real-World Use Case: Streaming live progress updates for long-running server tasks (e.g., AI document processing or video rendering)

Behavior
- the connection remains open while the generator yields formatted event strings, streaming data directly to the client without buffering

---
### Basic Unidirectional Streaming in fastAPI

```
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def generate_task_progress():
    for step in range(1, 6):
        await asyncio.sleep(1.0)  # Simulate processing step
        percent = step * 20
        # Format string following SSE spec (must end in \n\n)
        yield f"data: {{\"progress\": {percent}}}\n\n"
    
    yield "data: {\"status\": \"completed\"}\n\n"

@app.get("/api/v1/task-status")
async def get_task_status():
    return StreamingResponse(
        generate_task_progress(),
        media_type="text/event-stream"
    )
```

---
### Custom Event Names & Client Retry Directives

By yielding fields like below, you can route messages to specific Javascript event listeners on the client side
- event: event-name
- retry: retry-policy, reconnection interval

```
eventSource.addEventListener("event_name", ...)
```

Real-World Use Case
- a multi-channel monitoring system broadcasting separate metrics (e.g., cpu_spike, memory_warning) to distinct dashboard components

Behavior
- the browser routes events matching the named event field directly to dedicated client handlers instead of the default onmessage callback

---
### Custom Event Names & Client Retry Directives

```
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def system_metrics_stream():
    # Instruct browser to retry every 3000ms if connection drops
    yield "retry: 3000\n\n"
    
    count = 0
    while True:
        await asyncio.sleep(2.0)
        count += 1
        
        # Yield named event 'cpu_metric'
        cpu_data = json.dumps({"cpu_load": 45.2 + count})
        yield f"event: cpu_metric\ndata: {cpu_data}\n\n"
        
        # Yield named event 'memory_metric'
        mem_data = json.dumps({"ram_usage_mb": 2048 + (count * 10)})
        yield f"event: memory_metric\ndata: {mem_data}\n\n"

@app.get("/api/v1/metrics")
async def stream_metrics():
    return StreamingResponse(
        system_metrics_stream(),
        media_type="text/event-stream"
    )
```

---
### Connection Resiliency & Last-Event-ID Recovery

Reading the Last-Event-ID HTTP header allows the server to detect where a client left off after a dropped connection and re-transmit missed events from a buffer or log

Real-World Use Case
- unreliable mobile connections receiving real-time notifications without losing messages during transient disconnects

Behavior
- if Last-Event-ID is present in incoming headers, the route replays missed events prior to streaming live updates


---
### Connection Resiliency & Last-Event-ID Recovery

```
import asyncio
from typing import Annotated
from fastapi import FastAPI, Header
from fastapi.responses import StreamingResponse

app = FastAPI()

# Simulated event ledger
EVENT_HISTORY = [
    {"id": 1, "msg": "System initialized"},
    {"id": 2, "msg": "Database connected"},
    {"id": 3, "msg": "Cache warmed"},
]

async def resilient_event_stream(last_event_id: int):
    # 1. Replay missed events if client reconnected with Last-Event-ID
    for event in EVENT_HISTORY:
        if event["id"] > last_event_id:
            yield f"id: {event['id']}\ndata: {event['msg']}\n\n"
            await asyncio.sleep(0.1)

    # 2. Continue streaming live events
    next_id = len(EVENT_HISTORY) + 1
    while True:
        await asyncio.sleep(2.0)
        yield f"id: {next_id}\ndata: Live update {next_id}\n\n"
        next_id += 1

@app.get("/api/v1/notifications")
async def stream_notifications(
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None
):
    parsed_id = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
    return StreamingResponse(
        resilient_event_stream(last_event_id=parsed_id),
        media_type="text/event-stream"
    )
```

---
### Multi-Client Broadcast via Redis Pub/Sub

You can combine Redis Pub/Sub with FastAPI SSE to enable horizontally scaled event broadcasting across multiple API worker nodes

Real-World Use Case
- live financial ticker dashboards or chat rooms where one server-side event must fan out to thousands of connected browser streams

Behavior
- the API worker subscribes to a Redis channel upon client connection and streams incoming published messages directly to the client's HTTP response stream

---
### Multi-Client Broadcast via Redis Pub/Sub

```
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis

app = FastAPI()
redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)

async def redis_event_stream(channel_name: str):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel_name)
    try:
        while True:
            # Non-blocking check for new pub/sub messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                payload = message["data"]
                yield f"data: {payload}\n\n"
            else:
                # Periodic keep-alive comment to keep connection alive
                yield ": keep-alive\n\n"
            await asyncio.sleep(0.5)
    finally:
        await pubsub.unsubscribe(channel_name)

@app.get("/api/v1/live-feed/{channel}")
async def stream_channel_feed(channel: str):
    return StreamingResponse(
        redis_event_stream(channel_name=channel),
        media_type="text/event-stream"
    )
```

---
### Unified Enterprise SSE Broadcast & Resilience Pipeline

This complete implementation features a production-ready SSE broadcast hub combining Lifespan Redis connection pooling, Pydantic schema validation, Keep-alive heartbeats to prevent Nginx/Cloudflare timeouts, Event ID tracking, and Broadcast fan-out via Redis Pub/Sub


---
### Unified Enterprise SSE Broadcast & Resilience Pipeline

```
from contextlib import asynccontextmanager
import json
import logging
from typing import Annotated, AsyncGenerator
from fastapi import FastAPI, Depends, Header, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SSEGateway")

# ---------------------------------------------------------------------
# 1. INFRASTRUCTURE & LIFESPAN MANAGEMENT
# ---------------------------------------------------------------------
REDIS_URL = "redis://localhost:6379"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis Client Pool
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Connected to Redis event bus.")
    yield
    # Shutdown: Close Connection Pool
    await app.state.redis.close()
    logger.info("Disconnected from Redis event bus.")

app = FastAPI(title="Enterprise SSE Hub", lifespan=lifespan)

def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis

# ---------------------------------------------------------------------
# 2. SCHEMAS & SSE FORMATTING HELPERS
# ---------------------------------------------------------------------
class SystemAlertSchema(BaseModel):
    event_id: int
    severity: str = Field(description="INFO, WARNING, or CRITICAL")
    message: str

class PublishAlertRequest(BaseModel):
    severity: str
    message: str

def format_sse_message(
    data: str, 
    event: str | None = None, 
    event_id: int | None = None, 
    retry: int = 5000
) -> str:
    """Helper formatting string according to standard SSE specifications."""
    buffer = [f"retry: {retry}"]
    if event:
        buffer.append(f"event: {event}")
    if event_id is not None:
        buffer.append(f"id: {event_id}")
    
    # Handle multi-line data payloads cleanly
    for line in data.splitlines():
        buffer.append(f"data: {line}")
        
    return "\n".join(buffer) + "\n\n"

# ---------------------------------------------------------------------
# 3. STREAM GENERATOR WITH HEARTBEATS
# ---------------------------------------------------------------------
async def sse_channel_listener(
    channel_name: str, 
    redis: aioredis.Redis, 
    last_event_id: int
) -> AsyncGenerator[str, None]:
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel_name)
    
    try:
        # A. Optionally notify client of successful subscription
        yield format_sse_message(
            data=json.dumps({"status": "subscribed", "channel": channel_name}),
            event="system_status"
        )

        while True:
            # Check for Redis messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
            
            if message:
                raw_payload = message["data"]
                # Parse payload to extract event ID for SSE metadata
                try:
                    alert = SystemAlertSchema.model_validate_json(raw_payload)
                    yield format_sse_message(
                        data=alert.model_dump_json(),
                        event="alert",
                        event_id=alert.event_id
                    )
                except Exception:
                    # Fallback for plain unformatted string payloads
                    yield format_sse_message(data=raw_payload, event="raw_message")
            else:
                # B. Heartbeat comment line every 15s to keep connection alive through proxies
                yield ": keepalive ping\n\n"
                
    except Exception as exc:
        logger.error(f"Error in SSE stream for channel '{channel_name}': {exc}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()

# ---------------------------------------------------------------------
# 4. PATH OPERATIONS
# ---------------------------------------------------------------------
@app.get("/api/v1/sse/alerts/{channel}")
async def stream_system_alerts(
    channel: str,
    request: Request,
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None
):
    parsed_id = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
    
    return StreamingResponse(
        sse_channel_listener(channel_name=f"alerts:{channel}", redis=redis, last_event_id=parsed_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disables response buffering in Nginx
        }
    )

@app.post("/api/v1/sse/alerts/{channel}", status_code=status.HTTP_202_ACCEPTED)
async def publish_system_alert(
    channel: str,
    payload: PublishAlertRequest,
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    # Increment atomic counter for event ID generation
    next_id = await redis.incr(f"global:event_id:{channel}")
    
    alert = SystemAlertSchema(
        event_id=next_id,
        severity=payload.severity.upper(),
        message=payload.message
    )
    
    # Publish serialized alert to Redis Pub/Sub channel
    subscribers = await redis.publish(f"alerts:{channel}", alert.model_dump_json())
    
    return {
        "status": "published", 
        "event_id": next_id, 
        "active_listeners": subscribers
    }
```

---
###  Execution Pipeline Explanation

- Client Connection Initiation
    - a browser initializes new EventSource('/api/v1/sse/alerts/production'). The request hits stream_system_alerts, disabling HTTP caching and buffer delays via response headers (X-Accel-Buffering: no)
- Redis Pub/Sub Subscription
    - sse_channel_listener creates an async Pub/Sub context subscribing to alerts:production
- Event Ingestion & Format Generation
    - when an administrator publishes an alert via POST /api/v1/sse/alerts/production, the endpoint increments a Redis sequence counter (INCR), constructs a SystemAlertSchema, and publishes it
- Real-Time Fan-Out & Keep-Alive
    - every connected worker receives the Redis message, formats it into standard id:, event:, retry:, and data: strings via format_sse_message(), and flushes the data stream down the StreamingResponse. Every 15 seconds of inactivity triggers a : keepalive ping comment to keep idle connections open across proxy boundaries

    