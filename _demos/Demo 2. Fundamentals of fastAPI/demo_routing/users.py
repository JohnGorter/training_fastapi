from fastapi import APIRouter
from typing import List

user_router = APIRouter(prefix="/users")

@user_router.get("/")
async def return_users() -> List[str]:
   return ["user1", "user2"]

@user_router.get("/{user_id}")
async def return_user(user_id:int) -> str:
   return "user1"