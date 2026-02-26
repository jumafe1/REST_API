## This is how our Fast API goes
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from socialapi.database import database
from socialapi.logging_conf import configure_logging
from socialapi.routers.post import router as post_router

logger = logging.getLogger(__name__)


# connect to the database, and after any test
@asynccontextmanager  # context manager, function that does some setup
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("HOLALALALAL")
    await database.connect()
    yield  # stars runninr until FastAPI tell them to continue
    await database.disconnect()


app = FastAPI(lifespan=lifespan)  # the lifespan, is to use the above explanation


app.include_router(post_router)
