# Data Architectures

---
### In this module
We examine
- changenotifier
- provider
- bloc pattern
- cubeit
- bloc package
- getx
- riverpod
- mvc


FastAPI testing relies on Starlette's TestClient (built on httpx) and Pytest to execute in-process ASGI HTTP requests, swap dependencies, and validate schemas without launching a live network server.

1. In-Process HTTP Testing (TestClient)
TestClient instantiates an in-memory HTTP client that sends requests directly to the FastAPI ASGI application layer, allowing rapid unit testing of endpoints without network overhead.

Real-World Use Case: Validating API routes, path parameters, status codes, and JSON response bodies in CI/CD pipelines.

Behavior: TestClient uses standard httpx syntax under the hood and executes synchronous requests against both def and async def endpoints.

Python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "1.0.0"}
2. Dependency Overriding (app.dependency_overrides)
FastAPI allows replacing production dependencies (database sessions, external API clients, authorization checks) with mock objects during testing by setting key-value pairs in app.dependency_overrides.

Real-World Use Case: Bypassing third-party authentication services (Auth0, Cognito) or preventing real payment processing calls during test suite execution.

Behavior: Maps original dependency callable signatures to test-specific replacement callables. Clearing app.dependency_overrides = {} restores original behavior.

Python
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()

def get_current_user():
    # Production dependency: raises error if unauthenticated
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/me")
async def read_user_me(user: Annotated[dict, Depends(get_current_user)]):
    return user

client = TestClient(app)

def test_read_user_me_override():
    # Override production auth dependency with mock user fixture
    app.dependency_overrides[get_current_user] = lambda: {"username": "test_admin", "role": "admin"}
    
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json()["username"] == "test_admin"
    
    # Reset overrides after test
    app.dependency_overrides = {}
3. Asynchronous HTTP Testing (httpx.AsyncClient)
For testing applications using native async database drivers (e.g., asyncpg, SQLModel async) or streaming endpoints, httpx.AsyncClient executes asynchronous HTTP requests over ASGITransport.

Real-World Use Case: Testing asynchronous event streams, background task dispatches, or concurrent database transactions.

Behavior: Integrates with pytest-asyncio using @pytest.mark.asyncio to allow await statements inside test functions.

Python
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

app = FastAPI()

@app.get("/async-data")
async def get_async_data():
    return {"data": "async_result"}

@pytest.mark.asyncio
async def test_async_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/async-data")
    assert response.status_code == 200
    assert response.json() == {"data": "async_result"}
4. WebSocket Endpoint Testing (websocket_connect)
TestClient provides a context manager websocket_connect() to initiate simulated WebSocket handshakes, send/receive text or JSON frames, and test close codes.

Real-World Use Case: Testing real-time notifications, chat message handling, or live telemetry stream behavior.

Behavior: Establishes an in-process WebSocket connection context. Raises WebSocketDisconnect on non-normal closures.

Python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

app = FastAPI()

@app.websocket("/ws/echo")
async def ws_echo(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_text()
    await websocket.send_text(f"ECHO: {data}")
    await websocket.close()

client = TestClient(app)

def test_websocket_echo():
    with client.websocket_connect("/ws/echo") as websocket:
        websocket.send_text("Hello FastAPI")
        data = websocket.receive_text()
        assert data == "ECHO: Hello FastAPI"
5. Test Isolation with Pytest Fixtures
Combining Pytest fixtures (@pytest.fixture) with yield statements manages setup and teardown tasks—such as initializing clean in-memory databases and purging overrides after every test case.

Real-World Use Case: Ensuring isolated state between automated test runs so database modifications in one test do not spill over into subsequent tests.

Behavior: Code preceding yield executes before the test; code following yield executes as cleanup after the test completes.

Python
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

app = FastAPI()

def get_db():
    return {"db": "production_postgresql"}

@app.get("/items")
def list_items(db: dict = Depends(get_db)):
    return db

@pytest.fixture
def client():
    # Setup: Override DB with in-memory test DB
    app.dependency_overrides[get_db] = lambda: {"db": "sqlite_in_memory"}
    yield TestClient(app)
    # Teardown: Clear dependency overrides
    app.dependency_overrides = {}

def test_list_items(client):
    response = client.get("/items")
    assert response.json() == {"db": "sqlite_in_memory"}
Unified Enterprise Test Suite Implementation

This production pattern demonstrates a complete Pytest test suite testing authenticated REST API routes, transactional database dependency overrides, Pydantic validation failures, and WebSocket event broadcasts within an enterprise order service.

main.py (FastAPI Application)

Python
from typing import Annotated
from fastapi import FastAPI, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

app = FastAPI()

class OrderCreate(BaseModel):
    item_name: str = Field(min_length=2)
    quantity: int = Field(gt=0)

class DatabaseSession:
    def add_order(self, item_name: str, quantity: int) -> dict:
        return {"id": 101, "item_name": item_name, "quantity": quantity}

def get_db():
    return DatabaseSession()

def get_current_user(x_api_key: Annotated[str, Header()]):
    if x_api_key != "live_prod_key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return {"user_id": "usr_99", "role": "admin"}

@app.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[DatabaseSession, Depends(get_db)]
):
    saved_order = db.add_order(order.item_name, order.quantity)
    return {"status": "created", "order": saved_order, "created_by": user["user_id"]}

@app.websocket("/ws/orders/stream")
async def order_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"event": "ORDER_BROADCAST", "payload": data})
    except WebSocketDisconnect:
        pass
test_suite.py (Pytest Test Suite)

Python
import pytest
from fastapi.testclient import TestClient
from main import app, get_db, get_current_user, DatabaseSession

# Mock Database Session for Testing
class MockTestDatabaseSession(DatabaseSession):
    def add_order(self, item_name: str, quantity: int) -> dict:
        # Returns mocked test database record
        return {"id": 999, "item_name": item_name, "quantity": quantity, "is_test": True}

# Pytest Fixture for TestClient setup & Dependency Overrides
@pytest.fixture
def test_client():
    # 1. Override Auth & DB Dependencies
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "usr_test_mock", "role": "admin"}
    app.dependency_overrides[get_db] = lambda: MockTestDatabaseSession()
    
    # 2. Yield initialized TestClient
    with TestClient(app) as client:
        yield client
        
    # 3. Teardown: Reset overrides after test run
    app.dependency_overrides = {}

# Test Case 1: Valid Authenticated REST Order Creation
def test_create_order_success(test_client):
    response = test_client.post(
        "/orders",
        json={"item_name": "Developer Monitor", "quantity": 2}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "created"
    assert data["order"]["id"] == 999
    assert data["order"]["is_test"] is True
    assert data["created_by"] == "usr_test_mock"

# Test Case 2: Pydantic Validation Failure (422 Unprocessable Entity)
def test_create_order_invalid_payload(test_client):
    # Sends invalid quantity (quantity must be > 0)
    response = test_client.post(
        "/orders",
        json={"item_name": "X", "quantity": 0}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # Confirm Pydantic validation targeted the specific error fields
    assert data["detail"][0]["loc"] == ["body", "item_name"] or data["detail"][1]["loc"] == ["body", "quantity"]

# Test Case 3: WebSocket Frame Transmission & Broadcast
def test_websocket_order_stream(test_client):
    with test_client.websocket_connect("/ws/orders/stream") as websocket:
        websocket.send_json({"order_id": 999, "status": "processing"})
        received = websocket.receive_json()
        assert received["event"] == "ORDER_BROADCAST"
        assert received["payload"] == {"order_id": 999, "status": "processing"}
Execution Pipeline Explanation:

Fixture Initialization (test_client): Before executing each test, Pytest invokes the test_client fixture. It populates app.dependency_overrides to swap get_current_user (bypassing real X-API-Key checks) and get_db (injecting MockTestDatabaseSession).

REST Test Execution (test_create_order_success): TestClient.post() dispatches an in-memory HTTP POST payload. FastAPI processes the request, executes the overridden dependencies, passes Pydantic validation, and returns an HTTP 201 Created JSON payload asserted by assert response.status_code == 201.

Validation Error Test (test_create_order_invalid_payload): Submitting invalid payload data (quantity=0) triggers Pydantic's internal validation engine, bypassing the endpoint logic entirely and returning an HTTP 422 Unprocessable Entity containing field location details.

WebSocket Stream Verification (test_websocket_order_stream): websocket_connect() performs an in-process HTTP 101 upgrade. websocket.send_json() pushes a frame down the socket, and websocket.receive_json() validates the server's immediate broadcast reply.

Teardown Cleanup: Following test completion, Pytest executes the post-yield statement block in the test_client fixture, resetting app.dependency_overrides = {} to maintain pure state for subsequent test modules.