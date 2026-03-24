import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from socialapi.database import database, user_table
from socialapi.models.user import UserIn
from socialapi.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
async def register(user: UserIn):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exist",
        )
    # if not the exception, insert the user data in database
    # i NEVER store user password in database just as is(plain text).
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)
    logger.debug(query)

    await database.execute(query)
    return {"detail": "User created"}


# our login endpoint:
# userIn because we are going to receive the email and password.
@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(
        form_data.username, form_data.password
    )  # the function authenticate_user return the user record from our database if the user exists and the password is correct.
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}
