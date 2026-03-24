import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException

from socialapi.database import comment_table, database, like_table, post_table
from socialapi.models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostwithComments,
    UserPostwithLikes,
)
from socialapi.models.user import User
from socialapi.security import get_current_user

router = APIRouter()  # this is basicly a fastAPI app, but insted of runing on its own, in can be included into existing app

logger = logging.getLogger(__name__)

# query to re-use
select_post_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post(post_id: int):  # busca post por id en post_table
    logger.info(f"Fidding post with id {post_id}")
    query = post_table.select().where(
        post_table.c.id == post_id
    )  # sql query, without sql
    logger.debug(query)
    return await database.fetch_one(query)


# in order to create a post i need a access token. In orden to create a post i need to log in.
@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn, current_user: Annotated[User, Depends(get_current_user)]
):  # endporint, 1, fastAPI toma el JSON del body request y lo valida con Pydantic.
    logger.info("Create post")

    data = {
        **post.model_dump(),
        "user_id": current_user.id,
    }  # convierte el modelo de pydantic a dict
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)
    logger.debug(query)
    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


## get list of available post
@router.get("/post", response_model=list[UserPostwithLikes])
async def get_all_post(sorting: PostSorting = PostSorting.new):
    logger.info(
        "Getting all posts"
    )  # for more information about which logger is show in terminal

    if sorting == PostSorting.new:
        query = select_post_and_likes.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.old:
        query = select_post_and_likes.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.most_likes:
        query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.debug(
        query
    )  # something that i want to do. but in production, no, because it gonna be very expensive storage all these querys.

    return await database.fetch_all(query)


# Create a endpoint to create new comments:
@router.post("/comment", response_model=Comment)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):

    logger.info("Creating Comment")

    post = await find_post(comment.post_id)
    if not post:
        logger.error(
            f"logger with id {comment.post_id} not found"
        )  # when about its wrong.
        raise HTTPException(status_code=404, detail="Post not found")
    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comment_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)
    return {
        **data,
        "id": last_record_id,
    }  ## **data, passses each of the values of data as key and values pairs, for the new dictonari we contructing


# endpoint to get post:
@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comment_on_post(post_id: int):
    logger.info("Getting comments on post")

    query = comment_table.select().where(comment_table.c.post_id == post_id)

    logger.debug(query)
    return await database.fetch_all(query)  # pydantic accesing the values we return.


# endpoint, get post with comments:
@router.get("/post/{post_id}", response_model=UserPostwithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Getting post and its comments")

    # likes column
    query = select_post_and_likes.where(post_table.c.id == post_id)

    logger.debug(query)

    post = await database.fetch_one(query)
    if not post:
        logger.error(f"Post with post id {post_id} no found")
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "post": post,
        "comments": await get_comment_on_post(
            post_id
        ),  # el await hacer que la funcion get_comment_on_post se ejecute antes de pasar a esta linea
    }


# endpoint
@router.post("/like", response_model=PostLike, status_code=201)
async def like_post(
    like: PostLikeIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Linking info")

    # if the post does not exist we need to raise a error
    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not Found")
    data = {**like.model_dump(), "user_id": current_user.id}
    query = like_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}
