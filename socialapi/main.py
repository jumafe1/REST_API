## This is how our Fast API goes
from fastapi import FastAPI

from socialapi.routers.post import router as post_router

app = FastAPI()

app.include_router(post_router)
