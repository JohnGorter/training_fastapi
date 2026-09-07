from fastapi import APIRouter
from typing import List

# your code here

async def return_one_blog(blogid:int, userid:int | None = None):
   return f"returning blog {blogid} for user {userid}" if userid else f"returning blogs {blogid}!"
   
async def return_all_blogs(userid:int | None = None):
   return f"returning all blogs for user {userid}" if userid else "returning all blogs!"


@_blog_router.get("/")
async def return_blogs() -> str:
   return await return_all_blogs()

@_blog_router.get("/{blog_id}")
async def return_blog(blog_id:int) -> str:
   return await return_one_blog(blog_id)


@_blog_user_router.get("/")
async def return_user_blogs(user_id:int) -> str:
   return await return_all_blogs(user_id)

@_blog_user_router.get("/{blog_id}")
async def return_user_blog(user_id:int, blog_id:int) -> str:
   return await return_one_blog(blog_id, user_id)
