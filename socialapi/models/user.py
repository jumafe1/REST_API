from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    email: str


# we do not want to return the password.
class UserIn(User):
    password: str
