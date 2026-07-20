from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Form, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from tsundoku.auth import DenyReadonlyDep, OptionalUserDep, RequireUserDep, StateDep, login_user, logout_user
from tsundoku.blueprints.api.response import Success
from tsundoku.blueprints.api.schemas import IssueRequest
from tsundoku.constants import DATA_DIR, LOGGING_FILE_NAME
from tsundoku.ratelimit import limiter
from tsundoku.templating import flash, render
from tsundoku.user import User

from .issues import get_issue_url

ux_router = APIRouter()
hasher = PasswordHasher()


@ux_router.post("/issue")
async def issue(_guard: DenyReadonlyDep, body: IssueRequest) -> Success[str]:
    return Success(result=get_issue_url(body.issue_type or "", body.user_agent or ""))


@ux_router.get("/", response_class=HTMLResponse)
@ux_router.get("/nyaa", response_class=HTMLResponse)
@ux_router.get("/webhooks", response_class=HTMLResponse)
@ux_router.get("/config", response_class=HTMLResponse)
async def index(state: StateDep, request: Request, _guard: RequireUserDep) -> HTMLResponse:
    if state.flags.DL_CLIENT_CONNECTION_ERROR:
        flash(request, state.get_fluent()._("dl-client-connection-error"), "error")

    return render(state, request, "index.html")


@ux_router.get("/logs")
async def logs(state: StateDep, request: Request, _guard: RequireUserDep, dl: str | None = None) -> Response:
    if dl:
        return FileResponse(str(DATA_DIR / LOGGING_FILE_NAME), filename=LOGGING_FILE_NAME)

    if state.flags.DL_CLIENT_CONNECTION_ERROR:
        flash(request, state.get_fluent()._("dl-client-connection-error"), "error")

    return render(state, request, "index.html")


def _guard_registration(state: StateDep, user: User | None) -> Response | None:
    """Shared guard for the registration routes.

    Raises 403 for readonly users, returns a redirect for anyone who
    cannot register, or ``None`` if registration may proceed.
    """
    if user is not None and user.readonly:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    if not state.flags.IS_FIRST_LAUNCH or user is not None:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    return None


@ux_router.get("/register")
async def register_get(state: StateDep, request: Request, user: OptionalUserDep) -> Response:
    redirect = _guard_registration(state, user)
    if redirect is not None:
        return redirect

    return render(state, request, "register.html")


@ux_router.post("/register")
async def register_post(
    state: StateDep,
    request: Request,
    user: OptionalUserDep,
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    confirm_password: Annotated[str, Form(alias="confirmPassword")] = "",
) -> Response:
    redirect = _guard_registration(state, user)
    if redirect is not None:
        return redirect

    fluent = state.get_fluent()

    def fail(key: str, args: dict[str, str] | None = None) -> RedirectResponse:
        flash(request, fluent._(key, args), "error")
        return RedirectResponse("/register", status_code=status.HTTP_302_FOUND)

    if not username:
        return fail("form-register-missing-data", {"field": "username"})
    if not password:
        return fail("form-register-missing-data", {"field": "password"})
    if len(password) < 8:
        return fail("form-password-characters")
    if password != confirm_password:
        return fail("form-password-mismatch")

    async with state.acquire_db() as con:
        existing_id = await con.fetchval(
            """
            SELECT id FROM users WHERE LOWER(username) = LOWER(?);
            """,
            username,
        )

    if existing_id is not None:
        return fail("form-username-taken")

    pw_hash = hasher.hash(password)
    async with state.acquire_db() as con:
        await con.execute(
            """
            INSERT INTO
                users
                (username, password_hash, api_key)
            VALUES
                (?, ?, ?);
            """,
            username,
            pw_hash,
            str(uuid4()),
        )

    state.flags.IS_FIRST_LAUNCH = False

    flash(request, fluent._("form-register-success"), "success")
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@ux_router.get("/login")
async def login_get(state: StateDep, request: Request, user: OptionalUserDep) -> Response:
    if user is not None:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    return render(state, request, "login.html")


@ux_router.post("/login")
@limiter.limit("1/2 seconds;10/minute;20/hour")
async def login_post(
    state: StateDep,
    request: Request,
    user: OptionalUserDep,
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    remember: Annotated[bool, Form()] = False,
) -> Response:
    if user is not None:
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

    fluent = state.get_fluent()

    if not username or not password:
        flash(request, fluent._("form-missing-data"), "error")
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    async with state.acquire_db() as con:
        user_data = await con.fetchone(
            """
            SELECT id, password_hash FROM users WHERE LOWER(username) = ?;
            """,
            username.lower(),
        )

    if not user_data:
        flash(request, fluent._("invalid-credentials"), "error")
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    try:
        hasher.verify(user_data["password_hash"], password)
    except VerifyMismatchError:
        flash(request, fluent._("invalid-credentials"), "error")
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    if hasher.check_needs_rehash(user_data["password_hash"]):
        async with state.acquire_db() as con:
            await con.execute(
                """
                UPDATE users SET password_hash=? WHERE LOWER(username)=?;
                """,
                hasher.hash(password),
                username.lower(),
            )

    resolved = await User.from_id(state, user_data["id"])
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    if resolved is not None:
        login_user(response, state, resolved, remember=remember)

    return response


@ux_router.get("/logout")
async def logout(_guard: RequireUserDep) -> Response:
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    logout_user(response)
    return response


@ux_router.websocket("/ws/logs")
async def logs_ws(websocket: WebSocket) -> None:
    state = websocket.app.state.ctx
    await websocket.accept()

    queue: asyncio.Queue[str] = asyncio.Queue()
    state.connected_websockets.add(queue)
    try:
        await websocket.send_text("ACCEPT")
        while True:
            record = await queue.get()
            await websocket.send_text(record)
    except WebSocketDisconnect:
        pass
    finally:
        state.connected_websockets.discard(queue)
