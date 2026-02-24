## This is how our Fast API goes
from contextlib import asynccontextmanager

from fastapi import FastAPI

from socialapi.database import database
from socialapi.routers.post import router as post_router


# connect to the database, and after any test
@asynccontextmanager  # context manager, function that does some setup
async def lifespan(app: FastAPI):
    await database.connect()
    yield  # stars runninr until FastAPI tell them to continue
    await database.disconnect()


app = FastAPI(lifespan=lifespan)  # the lifespan, is to use the above explanation


app.include_router(post_router)
