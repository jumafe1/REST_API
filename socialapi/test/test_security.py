import pytest
from jose import jwt

from socialapi import security


@pytest.mark.anyio
@pytest.mark.parametrize(
    "fn, expected",
    [
        (security.access_token_expires_minutes, 15),
        (security.confirm_token_expires_minutes, 1440),
    ],
)
async def test_token_expires_minutes(fn, expected):
    assert fn() == expected


@pytest.mark.anyio
@pytest.mark.parametrize(
    "email, token_type, create_fn",
    [
        ("123", "access", security.create_access_token),
        ("123", "confirmation", security.create_confirmation_token),
    ],
)
async def test_create_token(email, token_type, create_fn):
    token = create_fn(email)
    assert {"sub": email, "type": token_type}.items() <= security.jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_confirmation():
    email = "test@example.com"
    token = security.create_confirmation_token(email)
    assert email == security.get_subject_for_token_type(token, "confirmation")


@pytest.mark.anyio
async def test_get_subject_for_token_type_valid_access():
    email = "test@example.com"
    token = security.create_access_token(email)
    assert email == security.get_subject_for_token_type(token, "access")


def get_subject_for_token_type_expired(mocker):
    mocker.patch("socialapi.security.access_token_expire_minutes", return_value=-1)
    email = "test@example.com"
    token = security.create_access_token(email)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Token has expired" == exc_info.value.detail


def get_subject_for_token_type_invalid_token():
    token = "invalid token"
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Invalid token" == exc_info.value.detail


@pytest.mark.anyio
async def test_get_subject_token_type_missing_sub():
    email = "test@example.com"
    token = security.create_access_token(email)
    payload = jwt.decode(token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM])
    del payload["sub"]
    token = jwt.encode(payload, key=security.SECRET_KEY, algorithm=security.ALGORITHM)

    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "token is missing 'sub' field" == exc_info.value.detail


@pytest.mark.anyio
async def test_get_subject_for_token_type_wrong_type():
    email = "test@example.com"
    token = security.create_confirmation_token(email)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Token has incorrect type, expected 'access'" == exc_info.value.detail


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
async def test_authenticate_user_success(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"], confirmed_user["password"]
    )
    assert user.email == confirmed_user["email"]


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


@pytest.mark.anyio
async def test_get_current_user_wrong_type_token(registered_user: dict):
    token = security.create_confirmation_token(registered_user["email"])

    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)
