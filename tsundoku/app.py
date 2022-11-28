from __future__ import annotations

import asyncio
from asyncio.queues import Queue
from contextlib import _AsyncGeneratorContextManager
import logging
import os
from pathlib import Path
import secrets
from typing import Any, Tuple, MutableSet, List
from uuid import uuid4

import aiofiles
import aiohttp
from argon2 import PasswordHasher
from quart import Quart, redirect, url_for
from quart_auth import AuthManager, Unauthorized
from werkzeug import Response

import tsundoku.asqlite
from tsundoku.blueprints.api import api_blueprint
from tsundoku.blueprints.ux import ux_blueprint
from tsundoku.config import GeneralConfig
from tsundoku.database import acquire, migrate, sync_acquire
from tsundoku.dl_client import Manager
from tsundoku.feeds import Downloader, Encoder, Poller
from tsundoku.log import setup_logging
from tsundoku.parsers import load_parsers, ParserStub
from tsundoku.user import User

hasher = PasswordHasher()

auth = AuthManager()
auth.user_class = User


class TsundokuApp(Quart):
    seen_titles: MutableSet[str] = set()
    connected_websockets: MutableSet[Queue[str]] = set()
    logging_queue: Queue[str]
    session: aiohttp.ClientSession
    dl_client: Manager

    rss_parsers: List[ParserStub]
    parser_lock: asyncio.Lock

    poller: Poller
    downloader: Downloader
    encoder: Encoder

    acquire_db: Any
    sync_acquire_db: Any

    _tasks: List[asyncio.Task] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


app: TsundokuApp = TsundokuApp("Tsundoku", static_folder=None)

logger = logging.getLogger("tsundoku")


class QuartConfig:
    SECRET_KEY = "1"  # secrets.token_urlsafe(16)
    QUART_AUTH_COOKIE_SECURE = False


app.config.from_object(QuartConfig())
setup_logging(app)


async def insert_user(username: str, password: str) -> None:
    await migrate()

    if os.getenv("IS_DOCKER"):
        fp = "data/tsundoku.db"
    else:
        fp = "tsundoku.db"

    pw_hash = hasher.hash(password)
    async with tsundoku.asqlite.connect(fp) as con:
        await con.execute("""
            INSERT INTO
                users
                (username, password_hash, api_key)
            VALUES
                (?, ?, ?);
        """, username, pw_hash, str(uuid4()))


@app.errorhandler(Unauthorized)
async def redirect_to_login(*_: Any) -> Response:
    return redirect(url_for("ux.login"))


@app.before_serving
async def setup_db() -> None:
    """
    Creates a database pool for PostgreSQL interaction.
    """
    await migrate()
    app.acquire_db = acquire
    app.sync_acquire_db = sync_acquire  # type: ignore

    async with app.acquire_db() as con:
        await con.execute("""
            SELECT
                COUNT(*)
            FROM
                users;
        """)
        users = await con.fetchval()

    if not users:
        logger.error("No existing users! Run `tsundoku --create-user` to create a new user.")


@app.before_serving
async def setup_session() -> None:
    """
    Creates an aiohttp ClientSession on startup using Quart's event loop.
    """
    loop = asyncio.get_event_loop()

    jar = aiohttp.CookieJar(unsafe=True)  # unsafe has to be True to store cookies from non-DNS URLs, i.e local IPs.

    app.session = aiohttp.ClientSession(
        loop=loop,
        cookie_jar=jar,
        timeout=aiohttp.ClientTimeout(total=15.0)
    )
    app.dl_client = Manager(app.session)


@app.before_serving
async def setup_parsers() -> None:
    """
    Load all of the custom RSS parsers into the app.
    """
    if os.getenv("IS_DOCKER"):
        parser_path = Path.cwd() / "data" / "parsers"
        spec_root = "data.parsers"
    else:
        parser_path = Path.cwd() / "parsers"
        spec_root = "parsers"

    parser_path.mkdir(exist_ok=True, parents=True)
    if not (parser_path / "COPIED").exists():
        default_parsers = ("subsplease", "nyaa")
        for parser in default_parsers:
            if not (parser_path / f"{parser}.py").exists():
                async with aiofiles.open(parser_path / f"{parser}.py", "wb") as fp:
                    async with aiofiles.open(Path.cwd() / "default_parsers" / f"{parser}.py", "rb") as default_fp:
                        await fp.write(await default_fp.read())

        async with aiofiles.open(parser_path / "COPIED", "wb") as fp:
            await fp.write(b"")

    parsers = [f"{spec_root}.{p.stem}" for p in parser_path.glob("*.py")]

    # It's okay if we're blocking here.
    # The webserver isn't intended to
    # be serving at this point in time.
    app.parser_lock = asyncio.Lock()
    async with app.parser_lock:
        load_parsers(parsers)


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

    await app.run_task(
        host=host,
        port=port
    )
