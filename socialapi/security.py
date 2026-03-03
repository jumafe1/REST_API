import datetime
import logging

import bcrypt
from fastapi import HTTPException, status
from jose import jwt

from socialapi.database import database, user_table

logger = logging.getLogger(__name__)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
)


# to simplyfy the test, because will we able to mock this function:
def access_token_expires_minutes() -> int:
    return 15


def create_access_token(email: str):
    logger.debug("Creating access token", extra={"email": email})
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        access_token_expires_minutes()
    )
    jwt_data = {
        "sub": email,
        "exp": expire,
    }
    jwt_encode = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return jwt_encode


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
        raise credentials_exception
    # the first es the plain password, the second is the hashed password.
    if not verify_password(password, user.password):
        raise credentials_exception
    # finally, if the user exists and the password is correct, return the user.
    return user


# raise the exeption above:
