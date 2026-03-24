# file to configure test
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

os.environ["ENV_STATE"] = "test"
from socialapi.database import database, user_table  # noqa: E402
from socialapi.main import app


#
@pytest.fixture(scope="session")  # only runs once
def anyio_backend():
    return "asyncio"


# test client, who gonna interact with
@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


# clear the tables, before run any test.
@pytest.fixture(autouse=True)  # to run on nay test
async def db() -> AsyncGenerator:  # the async function it is for database
    await database.connect()
    yield
    await database.disconnect()  # autmatic rollback


# make request to our API while test runing


@pytest.fixture()
async def async_client(client: TestClient) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url=str(client.base_url),  # importante: que sea string
    ) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def logged_in_token(
    async_client: AsyncClient, registered_user: dict
) -> str:
    response = await async_client.post("/token", json=registered_user)
    return response.json()["access_token"]
