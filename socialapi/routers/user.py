import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from socialapi import task
from socialapi.database import database, user_table
from socialapi.models.user import UserIn
from socialapi.security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
async def register(user: UserIn, request: Request, backgorund_tasks: BackgroundTasks):
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
    backgorund_tasks.add_task(
        task.send_user_registration_email(
            user.email,
            confirmation_url=request.url_for(
                "confirm_email", token=create_confirmation_token(user.email)
            ),
        )
    )
    return {"detail": "User created. Please confirm your email."}


# our login endpoint:
# userIn because we are going to receive the email and password.
@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(
        form_data.username, form_data.password
    )  # the function authenticate_user return the user record from our database if the user exists and the password is correct.
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )

    logger.debug(query)

    await database.execute(query)
    return {"detail": "User confirmed"}
