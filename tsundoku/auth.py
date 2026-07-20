from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from tsundoku.responses import APIError
from tsundoku.user import User

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState

AUTH_COOKIE_NAME = "tsundoku_auth"
_AUTH_SALT = "tsundoku-auth"
# Tokens are always accepted for up to a year; the ``remember`` flag only
# controls whether the browser persists the cookie past the session.
_MAX_AGE_SECONDS = 60 * 60 * 24 * 365

_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class NotAuthenticatedError(Exception):
    """Raised when an unauthenticated request hits a login-required page.

    The UX exception handler turns this into a redirect to the login (or
    first-launch registration) page.
    """


def _serializer(state: TsundokuAppState) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(state.secret_key, salt=_AUTH_SALT)


def dump_auth_token(state: TsundokuAppState, user_id: int) -> str:
    return _serializer(state).dumps(user_id)


def load_auth_token(state: TsundokuAppState, token: str) -> int | None:
    try:
        user_id = _serializer(state).loads(token, max_age=_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None

    return user_id if isinstance(user_id, int) else None


def login_user(response: Response, state: TsundokuAppState, user: User, *, remember: bool = False) -> None:
    """Attach an authentication cookie for ``user`` to ``response``."""
    response.set_cookie(
        AUTH_COOKIE_NAME,
        dump_auth_token(state, user.id),
        max_age=_MAX_AGE_SECONDS if remember else None,
        httponly=True,
        samesite="lax",
        secure=False,
    )


def logout_user(response: Response) -> None:
    """Clear the authentication cookie from ``response``."""
    response.delete_cookie(AUTH_COOKIE_NAME)


def get_state(request: Request) -> TsundokuAppState:
    """Dependency returning the shared application state container."""
    return request.app.state.ctx


StateDep = Annotated["TsundokuAppState", Depends(get_state)]


async def load_current_user(request: Request, state: StateDep) -> User | None:
    """Resolve the requesting user from a bearer token or session cookie.

    Returns ``None`` when the request carries no valid credentials.
    """
    authorization = request.headers.get("Authorization")
    if authorization:
        if not authorization.startswith("Bearer "):
            raise APIError(401, "Invalid authorization header.")
        return await User.from_api_key(state, authorization[len("Bearer ") :])

    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return None

    user_id = load_auth_token(state, token)
    if user_id is None:
        return None

    return await User.from_id(state, user_id)


OptionalUserDep = Annotated[User | None, Depends(load_current_user)]


async def require_user(user: OptionalUserDep) -> User:
    """UX dependency: require an authenticated user or redirect to login."""
    if user is None:
        raise NotAuthenticatedError

    return user


RequireUserDep = Annotated[User, Depends(require_user)]


async def deny_readonly(user: RequireUserDep) -> User:
    """UX dependency: require an authenticated, non-readonly user."""
    if user.readonly:
        raise APIError(403, "You are forbidden from modifying this resource.")

    return user


DenyReadonlyDep = Annotated[User, Depends(deny_readonly)]


async def require_api_user(request: Request, user: OptionalUserDep) -> User:
    """API dependency: require authentication and block readonly writes.

    Mirrors the previous ``ensure_auth`` before-request hook: any
    unauthenticated request is rejected with 401, and a readonly user is
    forbidden from performing write-method requests.
    """
    if user is None:
        raise APIError(401, "You are not authorized to access this resource.")

    if user.readonly and request.method in _WRITE_METHODS:
        raise APIError(403, "You are forbidden from modifying this resource.")

    return user


ApiUserDep = Annotated[User, Depends(require_api_user)]
