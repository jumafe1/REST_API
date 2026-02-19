# file to configure test
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from socialapi.main import app
from socialapi.routers.post import comment_table, post_table


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
    post_table.clear()
    comment_table.clear()
    yield


# make request to our API while test runing


@pytest.fixture()
async def async_client(client: TestClient) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url=str(client.base_url),  # importante: que sea string
    ) as ac:
        yield ac


# @pytest.fixture()
# async def async_client(
#     client,
# ) -> AsyncGenerator:  # parameter is the name of the fixture. dependency injection
#     async with AsyncClient(
#         app=app, base_url=client.base_url
#     ) as ac:  # connect with out test cliente, vealo desde test/routers/test_post
#         yield ac
