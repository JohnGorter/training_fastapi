from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field
from pymongo import AsyncMongoClient

# Client & Database initialization
client = AsyncMongoClient("mongodb://localhost:27017")
db = client["blog_db"]

# Write Operations
async def create_user(user: User) -> None:
    await db.users.insert_one(user.model_dump(by_alias=True))

async def create_post(post: Post) -> None:
    await db.posts.insert_one(post.model_dump(by_alias=True))

async def add_comment_to_post(post_id: str, comment: Comment) -> None:
    await db.posts.update_one(
        {"_id": post_id},
        {"$push": {"comments": comment.model_dump(by_alias=True)}}
    )

# Read Operations
async def get_user(user_id: str) -> User | None:
    doc = await db.users.find_one({"_id": user_id})
    return User.model_validate(doc) if doc else None

async def get_post_with_comments(post_id: str) -> Post | None:
    doc = await db.posts.find_one({"_id": post_id})
    return Post.model_validate(doc) if doc else None

async def get_user_posts(author_id: str) -> list[Post]:
    cursor = db.posts.find({"author_id": author_id})
    docs = await cursor.to_list(length=100)
    return [Post.model_validate(doc) for doc in docs]