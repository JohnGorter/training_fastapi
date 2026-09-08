

import asyncio
import time
import uuid
from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Global in-memory dictionary: session_id -> (expiration_timestamp, session_data)
class ThreadSafeSessionStore:
    def __init__(self):
        self._store: dict[str, tuple[float, dict]] = {}
        self._lock = asyncio.Lock()

    async def set(self, session_id: str, data: dict, ttl_seconds: int = 1800):
        expires_at = time.time() + ttl_seconds
        async with self._lock:
            self._store[session_id] = (expires_at, data)

    async def get(self, session_id: str) -> dict | None:
        async with self._lock:
            if session_id not in self._store:
                return None
            
            expires_at, data = self._store[session_id]
            if time.time() > expires_at:
                del self._store[session_id]  # Lazy eviction
                return None
            return data

session_store = ThreadSafeSessionStore()

class LoginPayload(BaseModel):
    user_id: int
    role: str

@app.post("/session")
async def create_session(payload: LoginPayload, response: Response):
    session_id = str(uuid.uuid4())
    expires_at = time.time() + 3600  # 1-hour expiration
    
    # Store directly in process memory
    await session_store.set(session_id, {"expire":expires_at, "data":payload.model_dump()})
    
    response.set_cookie(key="sid", value=session_id, httponly=True)
    return {"status": "session_created", "sid": session_id}



async def get_current_session(
    sid: Annotated[str | None, Cookie()] = None
) -> UserSession:
    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing session cookie"
        )
    
    session_data = await session_store.get(sid)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session invalid or expired"
        )
        
    return UserSession.model_validate(session_data)

@app.get("/api/v1/profile")
async def get_profile(user: Annotated[UserSession, Depends(get_current_session)]):
    return {"user_id": user.user_id, "email": user.email}