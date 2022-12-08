from __future__ import annotations

from asyncio import Queue
from functools import wraps
from typing import TYPE_CHECKING, Any, Union
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from quart import Blueprint, Response

if TYPE_CHECKING:
    import tsundoku.app

    app: tsundoku.app.TsundokuApp
else:
    from quart import current_app as app

from quart import (
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    websocket,
)
from quart_auth import current_user, login_required, login_user, logout_user

from tsundoku import __version__ as version
from tsundoku.blueprints.api import APIResponse
from tsundoku.fluent import get_injector
from tsundoku.user import User
from tsundoku.webhooks import WebhookBase

from .issues import get_issue_url

ux_blueprint = Blueprint(
    "ux",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/ux/static",
)
hasher = PasswordHasher()


@ux_blueprint.context_processor
async def update_context() -> dict:
    async with app.acquire_db() as con:
        await con.execute(
            """
            SELECT
                COUNT(*)
            FROM
                shows;
        """
        )
        shows = await con.fetchval()
        await con.execute(
            """
            SELECT
                COUNT(*)
            FROM
                show_entry;
        """
        )
        entries = await con.fetchval()

    stats = {
        "shows": shows,
        "entries": entries,
        "seen": len(app.seen_titles),
        "version": version,
    }

    return {"stats": stats, "docker": app.flags.IS_DOCKER}


@ux_blueprint.route("/issue", methods=["POST"])
@login_required
async def issue() -> APIResponse:
    data = await request.get_json()

    issue_type = data.get("issue_type")
    user_agent = data.get("user_agent")

    return APIResponse(result=get_issue_url(issue_type, user_agent))


@ux_blueprint.route("/", methods=["GET"])
@login_required
async def index() -> str:
    ctx = {}

    resources = ["base", "errors", "index"]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    if not len(app.rss_parsers):
        await flash(fluent._("no-rss-parsers"), category="error")
    elif not len(app.seen_titles):
        await flash(fluent._("no-shows-found"), category="error")
    elif app.flags.DL_CLIENT_CONNECTION_ERROR:
        await flash(fluent._("dl-client-connection-error"), category="error")

    return await render_template("index.html", **ctx)


@ux_blueprint.route("/nyaa", methods=["GET"])
@login_required
async def nyaa_search() -> str:
    ctx = {}

    resources = ["base"]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    if app.flags.DL_CLIENT_CONNECTION_ERROR:
        await flash(fluent._("dl-client-connection-error"), category="error")

    async with app.acquire_db() as con:
        await con.execute(
            """
            SELECT
                id,
                title
            FROM
                shows
            ORDER BY title;
        """
        )
        shows = await con.fetchall()
        ctx["shows"] = [dict(s) for s in shows]

    ctx["seen_titles"] = list(app.seen_titles)

    return await render_template("index.html", **ctx)


@ux_blueprint.route("/webhooks", methods=["GET"])
@login_required
async def webhooks() -> str:
    ctx = {}

    resources = ["base"]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    if app.flags.DL_CLIENT_CONNECTION_ERROR:
        await flash(fluent._("dl-client-connection-error"), category="error")

    return await render_template("index.html", **ctx)


@ux_blueprint.route("/config", methods=["GET"])
@login_required
async def config() -> str:
    ctx = {}

    resources = ["base"]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    if app.flags.DL_CLIENT_CONNECTION_ERROR:
        await flash(fluent._("dl-client-connection-error"), category="error")

    return await render_template("index.html", **ctx)


@ux_blueprint.route("/logs", methods=["GET"])
@login_required
async def logs() -> Union[str, Response]:
    if request.args.get("dl"):
        return await send_file("tsundoku.log", as_attachment=True)

    ctx = {}

    resources = ["base"]

    fluent = get_injector(resources)
    ctx["_"] = fluent.format_value

    return await render_template("index.html", **ctx)


@ux_blueprint.route("/register", methods=["GET", "POST"])
async def register() -> Any:
    if await current_user.is_authenticated or not app.flags.IS_FIRST_LAUNCH:
        return redirect(url_for("ux.index"))

    if request.method == "GET":
        fluent = get_injector(["register"])
        return await render_template("register.html", **{"_": fluent.format_value})
    else:
        resources = ["register"]
        fluent = get_injector(resources)

        form = await request.form

        username = form.get("username")
        password = form.get("password")
        password_confirm = form.get("confirmPassword")
        if not username:
            await flash(
                fluent._("form-missing-data", {"field": "username"}), category="error"
            )
            return redirect(url_for("ux.register"))
        elif not password:
            await flash(
                fluent._("form-missing-data", {"field": "password"}), category="error"
            )
            return redirect(url_for("ux.register"))
        elif len(password) < 8:
            await flash(fluent._("form-password-characters"), category="error")
            return redirect(url_for("ux.register"))
        elif password != password_confirm:
            await flash(fluent._("form-password-mismatch"), category="error")
            return redirect(url_for("ux.register"))

        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    id
                FROM
                    users
                WHERE
                    LOWER(username) = LOWER(?);
            """,
                username,
            )
            existing_id = await con.fetchval()

        # technically not possible to get to this page if there are
        # any other users at all
        if existing_id is not None:
            await flash(fluent._("form-username-taken"), category="error")
            return redirect(url_for("ux.register"))

        pw_hash = PasswordHasher().hash(password)
        async with app.acquire_db() as con:
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

        if app.flags.IS_FIRST_LAUNCH:
            app.flags.IS_FIRST_LAUNCH = False

        await flash(fluent._("form-register-success"), category="success")
        return redirect(url_for("ux.login"))


@ux_blueprint.route("/login", methods=["GET", "POST"])
async def login() -> Any:
    if await current_user.is_authenticated:
        return redirect(url_for("ux.index"))

    if request.method == "GET":
        fluent = get_injector(["login"])
        return await render_template("login.html", **{"_": fluent.format_value})
    else:
        resources = ["login"]
        fluent = get_injector(resources)

        form = await request.form

        username = form.get("username")
        password = form.get("password")
        if not username or not password:
            await flash(fluent._("form-missing-data"), category="error")
            return redirect(url_for("ux.login"))

        async with app.acquire_db() as con:
            await con.execute(
                """
                SELECT
                    id,
                    password_hash
                FROM
                    users
                WHERE LOWER(username) = ?;
            """,
                username.lower(),
            )
            user_data = await con.fetchone()

        if not user_data:
            await flash(fluent._("invalid-credentials"), category="error")
            return redirect(url_for("ux.login"))

        try:
            hasher.verify(user_data["password_hash"], password)
        except VerifyMismatchError:
            await flash(fluent._("invalid-credentials"), category="error")
            return redirect(url_for("ux.login"))

        if hasher.check_needs_rehash(user_data["password_hash"]):
            async with app.acquire_db() as con:
                await con.execute(
                    """
                    UPDATE
                        users
                    SET
                        password_hash=?
                    WHERE username=?;
                """,
                    hasher.hash(password),
                    username,
                )

        remember = form.get("remember", False)

        login_user(User(user_data["id"]), remember=remember)

        return redirect(url_for("ux.index"))


@ux_blueprint.route("/logout", methods=["GET"])
@login_required
async def logout() -> Any:
    logout_user()
    return redirect(url_for("ux.index"))


def collect_websocket(func):  # type: ignore
    @wraps(func)
    async def wrapper(*args, **kwargs):  # type: ignore
        queue = Queue()  # type: ignore
        app.connected_websockets.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            app.connected_websockets.remove(queue)

    return wrapper


@ux_blueprint.websocket("/ws/logs")
@collect_websocket
async def logs_ws(queue: Queue[str]) -> None:
    await websocket.send("ACCEPT")
    while True:
        record = await queue.get()
        await websocket.send(record)
