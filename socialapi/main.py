## This is how our Fast API goes
import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from socialapi.database import database
from socialapi.logging_conf import configure_logging
from socialapi.routers.post import router as post_router
from socialapi.routers.user import router as user_router  # add this router to our app

logger = logging.getLogger(__name__)


# connect to the database, and after any test
@asynccontextmanager  # context manager, function that does some setup
async def lifespan(app: FastAPI):
    configure_logging()

    await database.connect()
    yield  # stars runninr until FastAPI tell them to continue
    await database.disconnect()


app = FastAPI(lifespan=lifespan)  # the lifespan, is to use the above explanation
app.add_middleware(CorrelationIdMiddleware)


app.include_router(post_router)
app.include_router(user_router)


@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code}{exc.detail}")
    return await http_exception_handler(request, exc)
