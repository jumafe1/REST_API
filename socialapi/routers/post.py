from fastapi import APIRouter, HTTPException

from socialapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostwithComments,
)

router = APIRouter()  # this is basicly a fastAPI app, but insted of runing on its own, in can be included into existing app


post_table = {}
comment_table = {}


def find_post(post_id: int):  # busca post por id en post_table
    return post_table.get(post_id)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn,
):  # endporint, 1, fastAPI toma el JSON del body request y lo valida con Pydantic.
    data = post.model_dump()  # convierte el modelo de pydantic a dict
    last_record_id = len(post_table)
    new_post = {**data, "id": last_record_id}  # se contruye el post y se guarda
    post_table[last_record_id] = new_post
    return new_post


## get list of available post


@router.get("/post", response_model=list[UserPost])
async def get_all_post():  # enpoint
    return list(post_table.values())


# Create a endpoint to create new comments:
@router.post("/comment", response_model=Comment)
async def create_comment(
    comment: CommentIn,
):
    post = find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    data = comment.model_dump()
    last_record_id = len(comment_table)
    new_comment = {**data, "id": last_record_id}
    comment_table[last_record_id] = new_comment
    return new_comment


# endpoint to get post:
@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comment_on_post(post_id: int):
    return [
        comment for comment in comment_table.values() if comment["post_id"] == post_id
    ]


# endpoint, get post with comments:
@router.get("/post/{post_id}", response_model=UserPostwithComments)
async def get_post_with_comments(post_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "post": post,
        "comments": await get_comment_on_post(
            post_id
        ),  # el await hacer que la funcion get_comment_on_post se ejecute antes de pasar a esta linea
    }
