import datetime
import logging
from typing import Annotated, Literal

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt

from socialapi.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# the endpoint that the user send the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ALGORITHM = "HS256"


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# to simplyfy the test, because will we able to mock this function:
def access_token_expires_minutes() -> int:
    return 15


def confirm_token_expires_minutes() -> int:
    return 1440  # 24h


def create_access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        access_token_expires_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    jwt_encode = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return jwt_encode


def create_confirmation_token(email: str):
    logger.debug("Creating confirmation token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expires_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    jwt_encode = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return jwt_encode


def get_subject_for_token_type(
    token: str, type: Literal["access", "confirmation"]
) -> str:
    try:  # get email
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e

    except JWTError as e:
        raise create_credentials_exception("invalid token") from e

    email = payload.get("sub")
    if email is None:
        raise create_credentials_exception("token is missing 'sub' field")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{type}'"
        )

    return email


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


async def get_user(email: str):
    logger.debug("Fetching user from the database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)
    if result:
        return result


# function for authentication::


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user(email)
    if not user:
        raise create_credentials_exception("Invalid email or password")
    # the first es the plain password, the second is the hashed password.
    if not verify_password(password, user.password):
        raise create_credentials_exception("Invalid email or password")
    # finally, if the user exists and the password is correct, return the user.
    if not user.confirmed:
        raise create_credentials_exception("User has not confirmed email")
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = get_subject_for_token_type(token, "access")
    user = await get_user(email=email)
    if user is None:
        raise create_credentials_exception("could not find user for this token")
    return user
