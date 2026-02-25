from fastapi import APIRouter, HTTPException

from socialapi.database import comment_table, database, post_table
from socialapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostwithComments,
)

router = APIRouter()  # this is basicly a fastAPI app, but insted of runing on its own, in can be included into existing app


async def find_post(post_id: int):  # busca post por id en post_table
    query = post_table.select().where(
        post_table.c.id == post_id
    )  # sql query, without sql
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn,
):  # endporint, 1, fastAPI toma el JSON del body request y lo valida con Pydantic.
    data = post.model_dump()  # convierte el modelo de pydantic a dict
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


## get list of available post


@router.get("/post", response_model=list[UserPost])
async def get_all_post():  # enpoint
    query = post_table.select()
    return await database.fetch_all(query)


# Create a endpoint to create new comments:
@router.post("/comment", response_model=Comment)
async def create_comment(
    comment: CommentIn,
):
    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    data = comment.model_dump()
    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {
        **data,
        "id": last_record_id,
    }  ## **data, passses each of the values of data as key and values pairs, for the new dictonari we contructing


# endpoint to get post:
@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comment_on_post(post_id: int):
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    return await database.fetch_all(query)  # pydantic accesing the values we return.


# endpoint, get post with comments:
@router.get("/post/{post_id}", response_model=UserPostwithComments)
async def get_post_with_comments(post_id: int):
    post = await find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "post": post,
        "comments": await get_comment_on_post(
            post_id
        ),  # el await hacer que la funcion get_comment_on_post se ejecute antes de pasar a esta linea
    }
