from fastapi import APIRouter
from typing import List

# your code here

@user_router.get("/")
async def return_users() -> List[str]:
   return ["user1", "user2"]

@user_router.get("/{user_id}")
async def return_user(user_id:int) -> str:
   return "user1"