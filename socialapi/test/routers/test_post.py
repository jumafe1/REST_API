import pytest
from httpx import AsyncClient

from socialapi import security


# function that calls our API and create a post on our API
async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/post",
        json={"body": body},
        # this is hoe the token works, i dont send them in the token, i send them in the headers.
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )  # sumbit post request to the endpoint, and json equal the content type. Call to our API
    return response.json()  # json response that is the call for out API


# function for create comment, like the above but comments
async def create_comment(
    body: str, post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


# function to like a post
async def like_post(
    post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()  # use when testing requiererd post to already exist.
async def created_post(
    async_client: AsyncClient, logged_in_token: str
):  # this is fixture, use dependency injection. the value injecten dinamycally. see if theres a ficture async_client. Call it conftest
    return await create_post(
        "Test Post", async_client, logged_in_token
    )  # first interaction with out API.


@pytest.fixture()  # use when testing requiererd post to already exist.
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        "Test comment", created_post["id"], async_client, logged_in_token
    )


@pytest.mark.anyio  # para toda test toca decirle al test que se va a utilizar anyo
async def test_create_post(
    async_client: AsyncClient, logged_in_token: str, confirmed_user: dict
):
    body = "Test Post"

    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "user_id": confirmed_user["id"],
    }.items() <= response.json().items()  # this is expected in the response json


# test if we created a post but the token is experid


@pytest.mark.anyio
# the mocked allow us to modify the functionality of certain functions.
# this mocker is to modify acces token  minutes function 30 -> -1
async def test_create_post_expired_token(
    async_client: AsyncClient, confirmed_user: dict, mocker
):
    mocker.patch(
        "socialapi.security.access_token_expires_minutes", return_value=-1
    )  # full input path function
    token = security.create_access_token(confirmed_user["email"])
    response = await async_client.post(
        "/post",
        json={"body": "Test post"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_post_missing_data(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/post", json={}, headers={"Authorization": f"Bearer {logged_in_token}"}
    )  # whent we sent a empy json, means we need the 422, that means that the api works
    assert response.status_code == 422


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token
):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201


# test for getting all post
# if we have a error that inpedent us to call out Api, that error appeear in create post. If the API works as expected, we should get the JSON response.
@pytest.mark.anyio
async def test_get_all_post(
    async_client: AsyncClient, created_post: dict
):  # we use the dict post, because now we retrieven. how works pytest with fixture, frist, we put the fixture name and then pytest look in the current file for afixture name, and call it,
    response = await async_client.get("/post")
    assert response.status_code == 200
    assert created_post.items() <= response.json()[0].items()


@pytest.mark.anyio
# parametraicing
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
    ],
)
async def test_get_all_post_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    await create_post("Test post 1", async_client, logged_in_token)
    await create_post("Test post 2", async_client, logged_in_token)
    response = await async_client.get("/post", params={"sorting": sorting})
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_post_sort_likes(
    async_client: AsyncClient,
    logged_in_token: str,
):
    await create_post("Test post 1", async_client, logged_in_token)
    await create_post("Test post 2", async_client, logged_in_token)
    await like_post(1, async_client, logged_in_token)
    response = await async_client.get("/post", params={"sorting": "most_likes"})
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    expected_order = [1, 2]
    assert post_ids == expected_order


# test that we can create comment:
@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
    confirmed_user: dict,
):
    body = "Test comment"

    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 200
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"],
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
    assert response.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }


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
