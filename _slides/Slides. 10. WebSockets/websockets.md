# Websockets

---
### Websockets 

WebSockets (RFC 6455) provide full-duplex, bi-directional, persistent communication over a single long-lived TCP connection
 
 Differences:
 - traditional HTTP operates on a stateless, half-duplex request-response model where the client must initiate every interaction 
 - WebSockets allow both client and server to send text or binary payloads asynchronously at any time without the overhead of HTTP headers on every transmission

---
### Mechanics

The HTTP-to-WebSocket Protocol Upgrade Mechanics
= a WebSocket connection begins as a standard HTTP/1.1 request and performs a protocol transition known as the HTTP Handshake:

Client Upgrade Request:

```
HTTP
GET /ws/live HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

Server Handshake Response:

```
HTTP
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

---
### Socket Persistence & Framing
 
The underlying TCP connection remains open, but the HTTP protocol engine detaches. 
- the connection shifts to a framing protocol.
- each frame carries a lightweight 2-to-10-byte header (specifying frame type, payload length, and optional masking key) instead of kilobytes of HTTP header metadata

---
### FastAPI and WebSockets

FastAPI implements WebSockets over Starlette’s ASGI interface, enabling:
- full-duplex
- bi-directional communication between clients and servers 
- over a single persistent TCP connection

---
### Connection Lifecycle 

The mechanics:
- WebSocket.accept()
- send_text(),
- receive_text()

The WebSocket object controls the connection handshake, frame ingestion, frame transmission, and termination lifecycle

Real-World Use Case 
- streaming live log outputs from a deployment pipeline directly to a browser console

Behavior
- await websocket.accept() completes the HTTP-to-WebSocket upgrade handshake
- WebSocketDisconnect is raised when the client closes the TCP connection or loses network connectivity

```
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws/logs")
async def stream_logs(websocket: WebSocket):
    await websocket.accept()  # Complete HTTP -> WS upgrade handshake
    try:
        while True:
            data = await websocket.receive_text()  # Wait for client frames
            await websocket.send_text(f"ACK: Log line received -> '{data}'")
    except WebSocketDisconnect:
        print("Client cleanly disconnected from log stream.")
```

---
### Structured JSON Data Handling & Pydantic Validation

FastAPI provides native methods to (de)serialize JSON payloads directly over WebSocket:
- receive_json() 
- send_json()) 

Real-World Use Case
- receiving user interaction events (like cursor positions or canvas drawing operations) from a browser client

Behavior
- receive_json() parses incoming text frames as dictionaries
- passing the dictionary to a Pydantic model provides standard schema validation

```
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

app = FastAPI()

class CanvasEvent(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    action: str

@app.websocket("/ws/draw")
async def draw_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw_json = await websocket.receive_json()
            event = CanvasEvent.model_validate(raw_json)  # Validate schema
            await websocket.send_json({"status": "rendered", "x": event.x, "y": event.y})
    except WebSocketDisconnect:
        pass
```

---
### Connection Management & Broadcasting

An in-memory manager class tracks active WebSocket connections, enabling server-initiated broadcasts to single clients, groups, or channels

Real-World Use Case
- a multi-user chat application or collaborative document editing suite.

Behavior
- maintains an active pool 
- iterates through connected sockets to dispatch messages concurrently

```
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            await manager.broadcast(f"Broadcast: {msg}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---
### Authentication & Security 

Standard browser WebSocket APIs do not support custom HTTP headers during connection initialization. **Authentication tokens are typically passed via URL query parameters (ws://host/path?token=XYZ)**

Real-World Use Case
- restricting live notification channels to authorized platform subscribers

Behavior
- validate credentials before calling await websocket.accept(). Rejection sends an explicit WebSocket close code (e.g., 1008 Policy Violation) and terminates the handshake attempt

```
from typing import Annotated
from fastapi import FastAPI, WebSocket, Query, status
import jwt

app = FastAPI()
SECRET_KEY = "production-secret"

async def authenticate_ws(websocket: WebSocket, token: str | None) -> str:
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise Exception("Missing token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise Exception("Invalid token")

@app.websocket("/ws/notifications")
async def notifications(
    websocket: WebSocket,
    token: Annotated[str | None, Query()] = None
):
    user_id = await authenticate_ws(websocket, token)
    await websocket.accept()  # Only accept if authentication succeeds
    await websocket.send_text(f"Welcome user {user_id}")
```

---
#### Full-Duplex Concurrent Processing

FastAPI endpoints can decouple reading incoming frames and sending outgoing streams into separate async tasks running concurrently over the same socket

Real-World Use Case
- high-frequency stock market tickers where the server continuously streams live price updates while simultaneously receiving client commands (e.g., pause, resume, subscribe).

Behavior
- uses asyncio.create_task or asyncio.gather to manage simultaneous send and receive loops without blocking execution.

```
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

async def outgoing_ticker(websocket: WebSocket):
    """Continuously pushes updates to the client."""
    count = 0
    while True:
        await asyncio.sleep(1)
        count += 1
        await websocket.send_text(f"Market Tick #{count}")

async def incoming_listener(websocket: WebSocket):
    """Listens for client control commands."""
    while True:
        cmd = await websocket.receive_text()
        print(f"Client command received: {cmd}")

@app.websocket("/ws/market")
async def market_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Run reader and writer concurrently on the single connection
    producer = asyncio.create_task(outgoing_ticker(websocket))
    consumer = asyncio.create_task(incoming_listener(websocket))
    
    try:
        await asyncio.gather(producer, consumer)
    except WebSocketDisconnect:
        producer.cancel()
        consumer.cancel()
```

---
### Unified Enterprise WebSocket Request Flow

This production pattern demonstrates room-based routing, JWT authentication via query parameters, Pydantic validation of incoming frames, and connection lifecycle management in a multi-channel trading desk environment

```
from datetime import datetime, timezone
from typing import Annotated
import jwt
from fastapi import FastAPI, WebSocket, Query, status, WebSocketDisconnect
from pydantic import BaseModel, Field

SECRET_KEY = "enterprise-trading-secret-key"
ALGORITHM = "HS256"

app = FastAPI()

# 1. Incoming Frame Schema
class TradeOrderFrame(BaseModel):
    symbol: str
    amount: float = Field(gt=0)
    action: str  # "BUY" or "SELL"

# 2. Channel-Based Connection Manager
class TradingRoomManager:
    def __init__(self):
        # Maps room_id -> list of active WebSocket connections
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.rooms:
            self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast_to_room(self, room_id: str, message: dict):
        if room_id in self.rooms:
            for connection in self.rooms[room_id]:
                await connection.send_json(message)

trading_manager = TradingRoomManager()

# 3. Authentication Helper
def verify_ws_jwt(token: str | None) -> str:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

# 4. Multi-Room WebSocket Endpoint
@app.websocket("/ws/trading/{room_id}")
async def trading_room_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: Annotated[str | None, Query()] = None,
):
    # Step A: Pre-Handshake Authentication Check
    username = verify_ws_jwt(token)
    if not username:
        # Reject connection attempt before completing handshake
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Step B: Register and Accept Connection
    await trading_manager.connect(room_id, websocket)
    
    # Announce user arrival to room members
    await trading_manager.broadcast_to_room(
        room_id,
        {
            "event": "USER_JOINED",
            "user": username,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    # Step C: Full-Duplex Processing Loop
    try:
        while True:
            # Read incoming JSON frame from client
            raw_data = await websocket.receive_json()
            
            # Validate frame structure via Pydantic
            order = TradeOrderFrame.model_validate(raw_data)
            
            # Broadcast formatted order payload to the room channel
            await trading_manager.broadcast_to_room(
                room_id,
                {
                    "event": "ORDER_PLACED",
                    "trader": username,
                    "symbol": order.symbol,
                    "amount": order.amount,
                    "action": order.action,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
    except (WebSocketDisconnect, Exception):
        # Step D: Cleanup on disconnect or network fault
        trading_manager.disconnect(room_id, websocket)
        await trading_manager.broadcast_to_room(
            room_id,
            {
                "event": "USER_LEFT",
                "user": username,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
```

---
### Execution Pipeline Explanation

- Pre-Handshake Auth Check: The client initiates a connection to /ws/trading/forex?token=JWT_STRING. verify_ws_jwt() decodes the token from websocket.query_params. If missing or invalid, await websocket.close(code=1008) terminates the handshake prior to acceptance.

- Room Assignment & Handshake: Once authenticated, trading_manager.connect() invokes await websocket.accept(), completes the HTTP upgrade, and registers the socket in the rooms["forex"] array.

- Frame Ingestion & Validation: Inside the while True loop, receive_json() blocks until a frame arrives. TradeOrderFrame.model_validate() validates fields (amount > 0, required string properties) before processing continues.

- Channel Broadcasting: broadcast_to_room() iterates over every socket registered inside rooms["forex"] and calls send_json() to push the event payload across all active client connections concurrently.

- Graceful Disconnection Cleanup: If a client closes their browser tab or experiences network degradation, receive_json() raises WebSocketDisconnect. The except block catches the event, removes the socket from rooms["forex"], deletes empty room arrays, and notifies remaining room participants.


<!-- .slide: data-background="url('images/demo.jpg')" --> 
<!-- .slide: class="lab" -->
## Demo time!
Demo. Websockets

---
<!-- .slide: data-background="url('images/lab2.jpg')" --> 
<!-- .slide: class="lab" -->
## Lab time!
Websockets