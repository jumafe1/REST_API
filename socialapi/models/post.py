from pydantic import BaseModel


class UserPostIn(
    BaseModel
):  ## this two models is for validate the incoming and out coming data, only validates what the user can send
    body: str


class UserPost(
    UserPostIn
):  # Como Hereda UserpostIn, ya tiene body:str. modelo de salida
    id: int


class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    id: int


class UserPostwithComments(
    BaseModel
):  # modelo de devolver el post con todos los comentarios.
    post: UserPost
    comments: list[Comment] = []
