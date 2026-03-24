import pytest
from jose import jwt

from socialapi import security

# test if the accesss token verification token returns 15:


@pytest.mark.anyio
async def test_access_token_expires_minutes():
    assert security.access_token_expires_minutes() == 15


@pytest.mark.anyio
async def test_create_access_token():
    token = security.create_access_token("123")
    # we cheking if the first dict items are in the second dict items:
    assert {"sub": "123"}.items() <= jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


# test if the password is hashed correctly:
@pytest.mark.anyio
async def test_password_hashed():
    password = "password"
    assert security.verify_password(password, security.get_password_hash(password))


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.com")
    assert user is None


# test for our auth user
@pytest.mark.anyio
async def test_authenticate_user_success(registered_user: dict):
    user = await security.authenticate_user(
        registered_user["email"], registered_user["password"]
    )
    assert user.email == registered_user["email"]


# auth user but the user does not exist:
@pytest.mark.anyio
async def test_authenticate_user_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.com", "1234")


@pytest.mark.anyio
async def test_authenticate_user_user_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user["email"], "Wrong Password")


# test if the token works to find the user
@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    # crear el token
    token = security.create_access_token(registered_user["email"])
    # obtener el usuario desde el token
    user = await security.get_current_user(token)
    # verificar
    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")
