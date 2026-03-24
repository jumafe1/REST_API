import datetime
import logging
from typing import Annotated

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

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
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


# funtcion that takes a token, do some work, and return the user.


# first we decode the token, if the token is experid we return a 401 exepction. If there was other erro like jwt malfornation, also raise a 401 exception
# Then we try to get the email from the payload and then, if there was no email from the payload, we reaise a 401. Same with the user
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except JWTError as e:
        raise credentials_exception from e
    # user weight
    user = await get_user(email=email)
    # if user is None means that was not found in the database, otherwise, return the user
    if user is None:
        raise credentials_exception
    return user
