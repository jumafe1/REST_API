import pytest
from httpx import AsyncClient


# function that calls our API and create a post on our API
async def create_post(body: str, async_client: AsyncClient) -> dict:
    response = await async_client.post(
        "/post", json={"body": body}
    )  # sumbit post request to the endpoint, and json equal the content type. Call to our API
    return response.json()  # json response that is the call for out API


# function for create comment, like the above but comments


async def create_comment(body: str, post_id: int, async_client: AsyncClient) -> dict:
    response = await async_client.post(
        "/comment", json={"body": body, "post_id": post_id}
    )
    return response.json()


@pytest.fixture()  # use when testing requiererd post to already exist.
async def created_post(
    async_client: AsyncClient,
):  # this is fixture, use dependency injection. the value injecten dinamycally. see if theres a ficture async_client. Call it conftest
    return await create_post(
        "Test Post", async_client
    )  # first interaction with out API.


@pytest.fixture()  # use when testing requiererd post to already exist.
async def created_comment(async_client: AsyncClient, created_post: dict):
    return await create_comment("Test comment", created_post["id"], async_client)


@pytest.mark.anyio  # para toda test toca decirle al test que se va a utilizar anyo
async def test_create_post(async_client: AsyncClient):
    body = "Test Post"

    response = await async_client.post("/post", json={"body": body})

    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
    }.items() <= response.json().items()  # this is expected in the response json


@pytest.mark.anyio
async def test_create_post_missing_data(async_client: AsyncClient):
    response = await async_client.post(
        "/post", json={}
    )  # whent we sent a empy json, means we need the 422, that means that the api works
    assert response.status_code == 422


# test for getting all post
# if we have a error that inpedent us to call out Api, that error appeear in create post. If the API works as expected, we should get the JSON response.
@pytest.mark.anyio
async def test_get_all_post(
    async_client: AsyncClient, created_post: dict
):  # we use the dict post, because now we retrieven. how works pytest with fixture, frist, we put the fixture name and then pytest look in the current file for afixture name, and call it,
    response = await async_client.get("/post")
    assert response.status_code == 200
    assert response.json() == [created_post]


# test that we can create comment:


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):
    body = "Test comment"

    response = await async_client.post(
        "/comment", json={"body": body, "post_id": created_post["id"]}
    )

    assert response.status_code == 200
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(
    async_client: AsyncClient, created_post: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == []


# test and the comments with the last endpoint


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):

    # create our request:
    response = await async_client.get(f"/post/{created_post['id']}")

    assert response.status_code == 200
    assert response.json() == {"post": created_post, "comments": [created_comment]}


# get the post with comments when the post does not exist:


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient,
    created_comment: dict,
    created_post: dict,  ## this function has 2 fixtures
):

    response = await async_client.get("/post/2")
    assert response.status_code == 404


# lo que hicimos se puedes hacer en insomia/postman, pero aca es mas facil llevar un path
