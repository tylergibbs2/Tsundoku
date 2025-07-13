from asyncio import Queue
from datetime import timedelta
from functools import wraps
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from quart import Blueprint
from quart import Response as QuartResponse
from quart_rate_limiter import RateLimitExceeded, rate_limit
from werkzeug import Response

if TYPE_CHECKING:
    import tsundoku.app

    app = tsundoku.app.TsundokuApp()
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
from quart_auth import (
    Unauthorized,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from tsundoku import __version__ as version
from tsundoku.blueprints.api import APIResponse
from tsundoku.constants import DATA_DIR
from tsundoku.decorators import deny_readonly
from tsundoku.user import User

from .issues import get_issue_url

ux_blueprint = Blueprint(
    "ux",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/ux/static",
)
hasher = PasswordHasher()


@ux_blueprint.errorhandler(Unauthorized)
async def redirect_to_login(_: Any) -> Response:  # noqa: RUF029
    if app.flags.IS_FIRST_LAUNCH:
        return redirect(url_for("ux.register"))

    return redirect(url_for("ux.login"))


@ux_blueprint.errorhandler(429)
async def err_429(e: Exception) -> Response:
    error = "Too many requests."
    if isinstance(e, RateLimitExceeded):
        error += f" Try again in {e.retry_after} seconds."

    await flash(error, category="error")
    return redirect(request.url)


@ux_blueprint.context_processor
async def update_context() -> dict:  # noqa: RUF029
    fluent = app.get_fluent()
    stats = {"version": version}

    return {
        "stats": stats,
        "docker": app.flags.IS_DOCKER,
        "update_info": app.flags.UPDATE_INFO,
        "_": fluent.format_value,
    }


@ux_blueprint.route("/issue", methods=["POST"])
@login_required
@deny_readonly
async def issue() -> APIResponse:
    data = await request.get_json()

    issue_type = data.get("issue_type")
    user_agent = data.get("user_agent")

    return APIResponse(result=get_issue_url(issue_type, user_agent))


@ux_blueprint.route("/", methods=["GET"])
@ux_blueprint.route("/nyaa", methods=["GET"])
@ux_blueprint.route("/webhooks", methods=["GET"])
@ux_blueprint.route("/config", methods=["GET"])
@login_required
async def index() -> str:
    fluent = app.get_fluent()
    if app.flags.DL_CLIENT_CONNECTION_ERROR:
        await flash(fluent._("dl-client-connection-error"), category="error")

    return await render_template("index.html")


@ux_blueprint.route("/logs", methods=["GET"])
@login_required
async def logs() -> str | QuartResponse:
    if request.args.get("dl"):
        return await send_file(f"{DATA_DIR / 'tsundoku.log'}", as_attachment=True)

    fluent = app.get_fluent()
    if app.flags.DL_CLIENT_CONNECTION_ERROR:
        await flash(fluent._("dl-client-connection-error"), category="error")

    return await render_template("index.html")


@ux_blueprint.route("/register", methods=["GET", "POST"])
@deny_readonly
async def register() -> Any:
    if not app.flags.IS_FIRST_LAUNCH or await current_user.is_authenticated:
        return redirect("/")

    if request.method == "GET":
        return await render_template("register.html")
    fluent = app.get_fluent()
    form = await request.form

    username = form.get("username")
    password = form.get("password")
    password_confirm = form.get("confirmPassword")
    if not username:
        await flash(
            fluent._("form-register-missing-data", {"field": "username"}),
            category="error",
        )
        return redirect(url_for("ux.register"))
    if not password:
        await flash(
            fluent._("form-register-missing-data", {"field": "password"}),
            category="error",
        )
        return redirect(url_for("ux.register"))
    if len(password) < 8:
        await flash(fluent._("form-password-characters"), category="error")
        return redirect(url_for("ux.register"))
    if password != password_confirm:
        await flash(fluent._("form-password-mismatch"), category="error")
        return redirect(url_for("ux.register"))

    async with app.acquire_db() as con:
        existing_id = await con.fetchval(
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


@ux_blueprint.route("/login", methods=["GET"])
async def login() -> Response | str:
    if await current_user.is_authenticated:
        return redirect("/")

    return await render_template("login.html")


@ux_blueprint.route("/login", methods=["POST"])
@rate_limit(1, timedelta(seconds=2))
@rate_limit(10, timedelta(minutes=1))
@rate_limit(20, timedelta(hours=1))
async def login_post() -> Any:
    if await current_user.is_authenticated:
        return redirect("/")

    fluent = app.get_fluent()
    form = await request.form

    username = form.get("username")
    password = form.get("password")
    if not username or not password:
        await flash(fluent._("form-missing-data"), category="error")
        return redirect(url_for("ux.login"))

    async with app.acquire_db() as con:
        user_data = await con.fetchone(
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

    return redirect("/")


@ux_blueprint.route("/logout", methods=["GET"])
@login_required
async def logout() -> Any:  # noqa: RUF029
    logout_user()
    return redirect("/")


def collect_websocket(func: Any) -> Any:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        queue = Queue()
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
