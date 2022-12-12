from __future__ import annotations

import asyncio
from asyncio.queues import Queue
import logging
from pathlib import Path
import secrets
import sqlite3
from typing import (
    Any,
    Optional,
    Tuple,
    MutableSet,
    List,
    Callable,
    AsyncContextManager,
    ContextManager,
)
from uuid import uuid4

import aiohttp
from argon2 import PasswordHasher
from quart import Quart, redirect, url_for
from quart_auth import AuthManager, Unauthorized
from werkzeug import Response

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import tsundoku.asqlite
from tsundoku.blueprints.api import api_blueprint
from tsundoku.blueprints.ux import ux_blueprint
from tsundoku.config import GeneralConfig
from tsundoku.database import acquire, migrate, sync_acquire
from tsundoku.dl_client import Manager
from tsundoku.feeds import Downloader, Encoder, Poller
from tsundoku.flags import Flags
from tsundoku.log import setup_logging
from tsundoku.user import User

auth = AuthManager()
auth.user_class = User


class TsundokuApp(Quart):
    session: aiohttp.ClientSession
    dl_client: Manager

    connected_websockets: MutableSet[Queue[str]]
    logging_queue: Queue[str]

    source_lock: asyncio.Lock

    poller: Poller
    downloader: Downloader
    encoder: Encoder

    acquire_db: Callable[..., AsyncContextManager[tsundoku.asqlite.Cursor]]
    sync_acquire_db: Callable[..., ContextManager[sqlite3.Connection]]

    flags: Flags

    cached_bundle_hash: Optional[str] = None
    _tasks: List[asyncio.Task] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.connected_websockets = set()
        self.flags = Flags()


app: TsundokuApp = TsundokuApp("Tsundoku", static_folder=None)

logger = logging.getLogger("tsundoku")


class QuartConfig:
    SECRET_KEY = secrets.token_urlsafe(16) if not app.flags.IS_DEBUG else "debug"
    QUART_AUTH_COOKIE_SECURE = False


app.config.from_object(QuartConfig())
setup_logging(app)


async def insert_user(username: str, password: str) -> None:
    await migrate()

    if app.flags.IS_DOCKER:
        fp = "data/tsundoku.db"
    else:
        fp = "tsundoku.db"

    pw_hash = PasswordHasher().hash(password)
    async with tsundoku.asqlite.connect(fp) as con:
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


@app.errorhandler(Unauthorized)
async def redirect_to_login(*_: Any) -> Response:
    if app.flags.IS_FIRST_LAUNCH:
        return redirect(url_for("ux.register"))

    return redirect(url_for("ux.login"))


@app.url_defaults
def add_hash_for_webpack_bundle(endpoint: str, values: dict) -> None:
    filename = values.get("filename")
    if endpoint != "ux.static" or filename != "js/root.js":
        return

    if app.cached_bundle_hash is not None and not app.flags.IS_DEBUG:
        values["filename"] = f"js/root.{app.cached_bundle_hash}.js"
        return

    js_folder = Path("tsundoku", "blueprints", "ux", "static", "js")
    if not js_folder.exists():
        logger.error("Could not find static JS folder!")
        return

    for file in js_folder.glob("*.js"):
        if file.name.startswith("root."):
            split = file.name.split(".")
            if len(split) == 2:
                return

            app.cached_bundle_hash = split[1]
            values["filename"] = f"js/root.{app.cached_bundle_hash}.js"
            return


@app.before_serving
async def setup_db() -> None:
    """
    Creates a database pool for database interaction.
    """
    await migrate()
    app.acquire_db = acquire
    app.sync_acquire_db = sync_acquire

    async with app.acquire_db() as con:
        await con.execute(
            """
            SELECT
                COUNT(*)
            FROM
                users;
        """
        )
        users = await con.fetchval()

    if not users:
        logger.warn(
            "No existing users! Opening the app will result in a one-time registration page. Alternatively, you can create a user with the `tsundoku --create-user` command."
        )
        app.flags.IS_FIRST_LAUNCH = True


@app.before_serving
async def setup_session() -> None:
    """
    Creates an aiohttp ClientSession on startup using Quart's event loop.
    """
    loop = asyncio.get_event_loop()

    jar = aiohttp.CookieJar(
        unsafe=True
    )  # unsafe has to be True to store cookies from non-DNS URLs, i.e local IPs.

    app.session = aiohttp.ClientSession(
        loop=loop, cookie_jar=jar, timeout=aiohttp.ClientTimeout(total=15.0)
    )
    app.dl_client = Manager(app.session)


@app.before_serving
async def setup_tasks() -> None:
    """
    Creates the instances for the following tasks:
    poller, downloader, encoder

    These tasks are added to the app's global task list.
    """

    async def poller() -> None:
        app.poller = Poller(app.app_context())
        await app.poller.start()

    async def downloader() -> None:
        app.downloader = Downloader(app.app_context())
        await app.downloader.start()

    async def encoder() -> None:
        app.encoder = Encoder(app.app_context())
        await app.encoder.resume()

    app._tasks.append(asyncio.create_task(poller()))
    app._tasks.append(asyncio.create_task(downloader()))
    app._tasks.append(asyncio.create_task(encoder()))

    app.logging_queue = Queue(maxsize=50)


@app.after_serving
async def cleanup() -> None:
    """
    Closes the database pool and the
    aiohttp ClientSession on script closure.

    Also tries to cancel running tasks (downloader and poller).
    """
    for task in app._tasks:
        try:
            task.cancel()
        except Exception:
            pass

    try:
        await app.session.close()
    except Exception:
        pass


@ux_blueprint.context_processor
async def insert_locale() -> dict:
    # Inserts the user's locale into jinja2 variables.
    cfg = await GeneralConfig.retrieve()

    return {"LOCALE": cfg["locale"]}


app.register_blueprint(api_blueprint)
app.register_blueprint(ux_blueprint)


def get_bind() -> Tuple[str, int]:
    """
    Returns the host and port bindings
    to run the app on.

    Returns
    -------
    Tuple[str, int]
        Address and port
    """
    cfg = GeneralConfig.sync_retrieve(ensure_exists=True)
    return cfg["host"], cfg["port"]


async def run() -> None:
    await migrate()

    host, port = get_bind()

    auth.init_app(app)

    await app.run_task(host=host, port=port)
