from fastapi import FastAPI
from blogs import blog_router
from users import user_router

app = FastAPI()

app.include_router(user_router)
app.include_router(blog_router)